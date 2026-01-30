"""
ONTO API - Unified Backend
Epistemic Calibration Infrastructure

Endpoints:
  /health                    - Health check
  /docs                      - Swagger UI
  
  # Auth
  POST /v1/auth/register     - Register organization
  POST /v1/auth/login        - Login (get JWT)
  POST /v1/auth/api-keys     - Create API key
  
  # Evaluations  
  POST /v1/evaluate          - Submit evaluation
  GET  /v1/evaluations       - List evaluations
  GET  /v1/evaluations/{id}  - Get evaluation
  
  # Certificates
  GET  /v1/certificates      - List certificates
  GET  /v1/certificates/{id} - Get certificate
  
  # Billing (Stripe)
  POST /v1/billing/checkout  - Create checkout session
  POST /v1/billing/portal    - Create customer portal session
  GET  /v1/billing/status    - Get subscription status
  POST /v1/webhooks/stripe   - Stripe webhook handler
  
  # Admin
  GET  /v1/admin/stats       - System stats
"""

import os
import hashlib
import secrets
import json
import time
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Header, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
import asyncpg
import uvicorn

# ============================================================
# CONFIG
# ============================================================

DATABASE_URL = os.getenv("DATABASE_URL")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-jwt-secret-change-in-prod")
SIGNAL_URL = os.getenv("SIGNAL_URL", "https://signal.ontostandard.org")
NOTARY_URL = os.getenv("NOTARY_URL", "https://notary.ontostandard.org")

# Stripe
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
STRIPE_SUCCESS_URL = os.getenv("STRIPE_SUCCESS_URL", "https://ontostandard.org/billing/success")
STRIPE_CANCEL_URL = os.getenv("STRIPE_CANCEL_URL", "https://ontostandard.org/billing/cancel")

# Initialize Stripe
stripe = None
if STRIPE_SECRET_KEY:
    try:
        import stripe as stripe_module
        stripe_module.api_key = STRIPE_SECRET_KEY
        stripe = stripe_module
        print("[API] Stripe initialized")
    except ImportError:
        print("[API] WARNING: stripe package not installed")

# Protocol Layers (NOT Tiers!)
# See ONTO_PROTOCOL_MASTER.md Section 3
LAYERS = {
    "open": {
        "certificates_per_month": 100,
        "signal_delay_hours": 1,  # +1 hour delay for fraud prevention
        "price": 0,
        "watermark": True,
        "attribution_required": True
    },
    "standard": {
        "certificates_per_year": 10000,
        "signal_delay_hours": 0,  # Real-time
        "price": 15000,
        "watermark": False,
        "attribution_required": False
    },
    "critical": {
        "certificates_per_year": -1,  # Unlimited
        "signal_delay_hours": 0,  # Real-time
        "price": 100000,
        "watermark": False,
        "attribution_required": False,
        "audit_trail_months": 24
    }
}

# Stripe Price IDs (set in Railway env vars)
# OPEN = free, no Stripe
STRIPE_PRICE_IDS = {
    "standard": os.getenv("STRIPE_PRICE_STANDARD"),
    "critical": os.getenv("STRIPE_PRICE_CRITICAL"),
}

# Rate limits per layer (requests per minute)
RATE_LIMITS = {
    "open": 30,
    "standard": 500,
    "critical": 2000,
    "public": 10,  # Unauthenticated requests
}

# ============================================================
# RATE LIMITER (In-Memory)
# ============================================================

class RateLimiter:
    """Simple in-memory rate limiter using sliding window"""
    
    def __init__(self):
        # {key: [(timestamp, count), ...]}
        self.requests = defaultdict(list)
        self.window_seconds = 60
    
    def _cleanup(self, key: str):
        """Remove old entries outside the window"""
        cutoff = time.time() - self.window_seconds
        self.requests[key] = [
            (ts, count) for ts, count in self.requests[key] 
            if ts > cutoff
        ]
    
    def is_allowed(self, key: str, limit: int) -> tuple[bool, int]:
        """
        Check if request is allowed.
        Returns (allowed, remaining_requests)
        """
        now = time.time()
        self._cleanup(key)
        
        # Count requests in current window
        total = sum(count for _, count in self.requests[key])
        
        if total >= limit:
            return False, 0
        
        # Add this request
        self.requests[key].append((now, 1))
        remaining = limit - total - 1
        
        return True, max(0, remaining)
    
    def get_reset_time(self, key: str) -> int:
        """Get seconds until rate limit resets"""
        if not self.requests[key]:
            return 0
        oldest = min(ts for ts, _ in self.requests[key])
        reset = int(oldest + self.window_seconds - time.time())
        return max(0, reset)

rate_limiter = RateLimiter()

# ============================================================
# DATABASE
# ============================================================

db_pool = None

async def init_db():
    global db_pool
    if not DATABASE_URL:
        print("[API] WARNING: No DATABASE_URL - some features disabled")
        return
    
    try:
        db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
        print("[API] Database connected")
    except Exception as e:
        print(f"[API] Database error: {e}")

async def close_db():
    global db_pool
    if db_pool:
        await db_pool.close()

# ============================================================
# MODELS
# ============================================================

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    company: str
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class CreateApiKeyRequest(BaseModel):
    name: str

class EvaluationRequest(BaseModel):
    model_name: str
    model_version: Optional[str] = None
    predictions: List[dict]  # [{id, prediction, confidence}, ...]

class OrganizationResponse(BaseModel):
    id: str
    name: str
    email: str
    company: str
    layer: str
    created_at: str

class ApiKeyResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    created_at: str
    last_used_at: Optional[str]

class CheckoutRequest(BaseModel):
    layer: str  # standard, critical

class PortalRequest(BaseModel):
    return_url: Optional[str] = None

# ============================================================
# AUTH HELPERS
# ============================================================

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()

def generate_api_key() -> tuple[str, str]:
    """Returns (full_key, prefix)"""
    random_part = secrets.token_hex(24)
    full_key = f"onto_{random_part}"
    prefix = f"onto_{random_part[:4]}"
    return full_key, prefix

async def validate_api_key(x_api_key: str = Header(...)) -> dict:
    """Validate API key and return organization info"""
    if not db_pool:
        # Dev mode - accept any key
        return {"organization_id": "dev", "layer": "open"}
    
    key_hash = hash_api_key(x_api_key)
    
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT ak.id, ak.organization_id, ak.is_active, 
                   o.name, o.tier, o.slug, o.stripe_customer_id
            FROM api_keys ak
            JOIN organizations o ON ak.organization_id = o.id
            WHERE ak.key_hash = $1
        """, key_hash)
        
        if not row:
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        if not row['is_active']:
            raise HTTPException(status_code=401, detail="API key revoked")
        
        # Update last_used_at
        await conn.execute(
            "UPDATE api_keys SET last_used_at = NOW() WHERE id = $1",
            row['id']
        )
        
        return {
            "api_key_id": str(row['id']),
            "organization_id": str(row['organization_id']),
            "organization_name": row['name'],
            "layer": row['tier'],
            "slug": row['slug'],
            "stripe_customer_id": row['stripe_customer_id']
        }

# ============================================================
# RATE LIMITING MIDDLEWARE
# ============================================================

async def check_rate_limit(request: Request, layer: str = "public") -> None:
    """Check rate limit for a request"""
    # Get client identifier
    client_ip = request.client.host if request.client else "unknown"
    api_key = request.headers.get("x-api-key", "")
    
    # Use API key if present, otherwise IP
    if api_key:
        key = f"api:{hash_api_key(api_key)[:16]}"
    else:
        key = f"ip:{client_ip}"
    
    limit = RATE_LIMITS.get(layer, RATE_LIMITS["public"])
    allowed, remaining = rate_limiter.is_allowed(key, limit)
    
    if not allowed:
        reset_time = rate_limiter.get_reset_time(key)
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset_time),
                "Retry-After": str(reset_time)
            }
        )

# ============================================================
# LIFESPAN
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()

# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="ONTO API",
    description="Epistemic Calibration Infrastructure for Enterprise AI",
    version="1.2.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# RATE LIMIT MIDDLEWARE
# ============================================================

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Apply rate limiting to all requests"""
    # Skip rate limiting for health checks and docs
    if request.url.path in ["/health", "/docs", "/openapi.json", "/", "/v1/webhooks/stripe"]:
        return await call_next(request)
    
    # Get client identifier
    client_ip = request.client.host if request.client else "unknown"
    api_key = request.headers.get("x-api-key", "")
    
    # Determine layer (DB column is 'tier' for backward compatibility)
    layer = "public"
    if api_key and db_pool:
        key_hash = hash_api_key(api_key)
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT o.tier FROM api_keys ak
                JOIN organizations o ON ak.organization_id = o.id
                WHERE ak.key_hash = $1 AND ak.is_active = true
            """, key_hash)
            if row:
                layer = row['tier']  # DB column name
    
    # Check rate limit
    if api_key:
        key = f"api:{hash_api_key(api_key)[:16]}"
    else:
        key = f"ip:{client_ip}"
    
    limit = RATE_LIMITS.get(layer, RATE_LIMITS["public"])
    allowed, remaining = rate_limiter.is_allowed(key, limit)
    allowed, remaining = rate_limiter.is_allowed(key, limit)
    
    if not allowed:
        reset_time = rate_limiter.get_reset_time(key)
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded", "retry_after": reset_time},
            headers={
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset_time),
                "Retry-After": str(reset_time)
            }
        )
    
    # Process request
    response = await call_next(request)
    
    # Add rate limit headers
    response.headers["X-RateLimit-Limit"] = str(limit)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    
    return response

# ============================================================
# PUBLIC ENDPOINTS
# ============================================================

@app.get("/")
async def root():
    return {
        "name": "ONTO API",
        "version": "1.2.0",
        "docs": "https://api.ontostandard.org/docs",
        "status": "operational",
        "rate_limits": RATE_LIMITS,
        "stripe_enabled": stripe is not None
    }

@app.get("/health")
async def health():
    db_status = "connected" if db_pool else "disconnected"
    return {
        "status": "healthy",
        "database": db_status,
        "stripe": "enabled" if stripe else "disabled",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/v1/pricing")
async def get_pricing():
    return {
        "layers": LAYERS,
        "rate_limits": RATE_LIMITS,
        "currency": "USD",
        "billing": "annual",
        "contact": "sales@ontostandard.org"
    }

@app.get("/v1/signal/status")
async def get_signal_status():
    """Proxy to Signal Server status"""
    import httpx
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{SIGNAL_URL}/signal/status", timeout=5)
            return resp.json()
    except Exception as e:
        return {"error": str(e), "signal_url": SIGNAL_URL}


@app.get("/v1/signal/current")
async def get_current_signal(org: dict = Depends(validate_api_key)):
    """
    Get current signal for evaluation.
    OPEN layer: +1 hour delay (cannot use for real-time production)
    STANDARD/CRITICAL: real-time signal
    """
    import httpx
    
    # Get layer info
    layer = org.get('tier', 'open')  # DB column is 'tier'
    layer_info = LAYERS.get(layer, LAYERS['open'])
    delay_hours = layer_info.get('signal_delay_hours', 1)
    
    try:
        async with httpx.AsyncClient() as client:
            if delay_hours > 0:
                # OPEN layer: get delayed signal
                resp = await client.get(
                    f"{SIGNAL_URL}/signal/delayed",
                    params={"hours": delay_hours},
                    timeout=5
                )
            else:
                # STANDARD/CRITICAL: real-time signal
                resp = await client.get(f"{SIGNAL_URL}/signal/current", timeout=5)
            
            data = resp.json()
            
            # Add layer info to response
            data["layer"] = layer
            data["delay_hours"] = delay_hours
            if delay_hours > 0:
                data["warning"] = "OPEN layer signal is delayed by 1 hour. Not suitable for real-time production."
            
            return data
            
    except Exception as e:
        return {
            "error": str(e), 
            "signal_url": SIGNAL_URL,
            "layer": layer,
            "delay_hours": delay_hours
        }

# ============================================================
# AUTH ENDPOINTS
# ============================================================

@app.post("/v1/auth/register")
async def register(request: RegisterRequest, req: Request):
    """Register a new organization"""
    # Rate limit registration (stricter)
    client_ip = req.client.host if req.client else "unknown"
    key = f"register:{client_ip}"
    allowed, _ = rate_limiter.is_allowed(key, 5)  # 5 registrations per minute per IP
    if not allowed:
        raise HTTPException(status_code=429, detail="Too many registration attempts")
    
    if not db_pool:
        return {"message": "Registration disabled (no database)", "status": "demo_mode"}
    
    async with db_pool.acquire() as conn:
        # Check if email exists
        existing = await conn.fetchval(
            "SELECT id FROM users WHERE email = $1", 
            request.email
        )
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create Stripe customer if Stripe is enabled
        stripe_customer_id = None
        if stripe:
            try:
                customer = stripe.Customer.create(
                    email=request.email,
                    name=request.company,
                    metadata={"company": request.company}
                )
                stripe_customer_id = customer.id
            except Exception as e:
                print(f"[API] Stripe customer creation failed: {e}")
        
        # Create organization
        slug = request.company.lower().replace(" ", "-")[:50]
        org_id = await conn.fetchval("""
            INSERT INTO organizations (name, slug, tier, stripe_customer_id)
            VALUES ($1, $2, 'pilot', $3)
            RETURNING id
        """, request.company, slug, stripe_customer_id)
        
        # Create user
        password_hash = hash_password(request.password)
        user_id = await conn.fetchval("""
            INSERT INTO users (email, name, password_hash, organization_id, role)
            VALUES ($1, $2, $3, $4, 'admin')
            RETURNING id
        """, request.email, request.name, password_hash, org_id)
        
        # Create initial API key
        full_key, prefix = generate_api_key()
        key_hash = hash_api_key(full_key)
        await conn.execute("""
            INSERT INTO api_keys (organization_id, name, key_hash, key_prefix, scopes)
            VALUES ($1, 'Default Key', $2, $3, '["read", "write"]')
        """, org_id, key_hash, prefix)
        
        # Log event
        await conn.execute("""
            INSERT INTO audit_log (organization_id, user_id, action, resource_type, details)
            VALUES ($1, $2, 'register', 'organization', $3)
        """, org_id, user_id, json.dumps({"company": request.company}))
        
        return {
            "organization_id": str(org_id),
            "user_id": str(user_id),
            "api_key": full_key,  # Only shown once!
            "layer": "open",
            "stripe_customer_id": stripe_customer_id,
            "message": "Registration successful. Save your API key - it won't be shown again."
        }

@app.post("/v1/auth/login")
async def login(request: LoginRequest):
    """Login and get JWT token"""
    if not db_pool:
        return {"message": "Login disabled (no database)", "status": "demo_mode"}
    
    async with db_pool.acquire() as conn:
        password_hash = hash_password(request.password)
        row = await conn.fetchrow("""
            SELECT u.id, u.name, u.organization_id, o.name as org_name, o.tier
            FROM users u
            JOIN organizations o ON u.organization_id = o.id
            WHERE u.email = $1 AND u.password_hash = $2 AND u.is_active = true
        """, request.email, password_hash)
        
        if not row:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Update last login
        await conn.execute(
            "UPDATE users SET last_login_at = NOW() WHERE id = $1",
            row['id']
        )
        
        # Generate simple token (in production use proper JWT)
        token = secrets.token_urlsafe(32)
        
        return {
            "user_id": str(row['id']),
            "name": row['name'],
            "organization_id": str(row['organization_id']),
            "organization_name": row['org_name'],
            "layer": row['tier'],
            "token": token,
            "message": "Login successful"
        }

@app.post("/v1/auth/api-keys")
async def create_api_key(
    request: CreateApiKeyRequest,
    org: dict = Depends(validate_api_key)
):
    """Create a new API key"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    full_key, prefix = generate_api_key()
    key_hash = hash_api_key(full_key)
    
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO api_keys (organization_id, name, key_hash, key_prefix, scopes)
            VALUES ($1, $2, $3, $4, '["read", "write"]')
        """, org['organization_id'], request.name, key_hash, prefix)
        
        return {
            "api_key": full_key,
            "prefix": prefix,
            "name": request.name,
            "message": "API key created. Save it - it won't be shown again."
        }

@app.get("/v1/auth/api-keys")
async def list_api_keys(org: dict = Depends(validate_api_key)):
    """List API keys for organization"""
    if not db_pool:
        return {"api_keys": []}
    
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, name, key_prefix, created_at, last_used_at, is_active
            FROM api_keys
            WHERE organization_id = $1
            ORDER BY created_at DESC
        """, org['organization_id'])
        
        return {
            "api_keys": [
                {
                    "id": str(r['id']),
                    "name": r['name'],
                    "key_prefix": r['key_prefix'],
                    "is_active": r['is_active'],
                    "created_at": r['created_at'].isoformat() if r['created_at'] else None,
                    "last_used_at": r['last_used_at'].isoformat() if r['last_used_at'] else None
                }
                for r in rows
            ]
        }

@app.delete("/v1/auth/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    org: dict = Depends(validate_api_key)
):
    """Revoke an API key"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    async with db_pool.acquire() as conn:
        result = await conn.execute("""
            UPDATE api_keys 
            SET is_active = false 
            WHERE id = $1 AND organization_id = $2
        """, key_id, org['organization_id'])
        
        if result == "UPDATE 0":
            raise HTTPException(status_code=404, detail="API key not found")
        
        return {"status": "revoked", "key_id": key_id}

# ============================================================
# BILLING ENDPOINTS (Stripe)
# ============================================================

@app.post("/v1/billing/checkout")
async def create_checkout_session(
    request: CheckoutRequest,
    org: dict = Depends(validate_api_key)
):
    """Create a Stripe checkout session for upgrading layer"""
    if not stripe:
        raise HTTPException(status_code=503, detail="Billing not available")
    
    if request.layer not in STRIPE_PRICE_IDS:
        raise HTTPException(status_code=400, detail=f"Invalid layer: {request.layer}")
    
    price_id = STRIPE_PRICE_IDS.get(request.layer)
    if not price_id:
        raise HTTPException(status_code=400, detail=f"Price not configured for layer: {request.layer}")
    
    # Get or create Stripe customer
    stripe_customer_id = org.get('stripe_customer_id')
    
    if not stripe_customer_id and db_pool:
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT name, stripe_customer_id FROM organizations WHERE id = $1",
                org['organization_id']
            )
            if row:
                stripe_customer_id = row['stripe_customer_id']
                
                # Create customer if not exists
                if not stripe_customer_id:
                    try:
                        customer = stripe.Customer.create(
                            name=row['name'],
                            metadata={"organization_id": org['organization_id']}
                        )
                        stripe_customer_id = customer.id
                        await conn.execute(
                            "UPDATE organizations SET stripe_customer_id = $1 WHERE id = $2",
                            stripe_customer_id, org['organization_id']
                        )
                    except Exception as e:
                        raise HTTPException(status_code=500, detail=f"Failed to create customer: {e}")
    
    try:
        session = stripe.checkout.Session.create(
            customer=stripe_customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=f"{STRIPE_SUCCESS_URL}?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=STRIPE_CANCEL_URL,
            metadata={
                "organization_id": org['organization_id'],
                "layer": request.layer
            }
        )
        
        return {
            "checkout_url": session.url,
            "session_id": session.id,
            "layer": request.layer,
            "price": LAYERS[request.layer]['price']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create checkout session: {e}")

@app.post("/v1/billing/portal")
async def create_portal_session(
    request: PortalRequest,
    org: dict = Depends(validate_api_key)
):
    """Create a Stripe customer portal session for managing subscription"""
    if not stripe:
        raise HTTPException(status_code=503, detail="Billing not available")
    
    stripe_customer_id = org.get('stripe_customer_id')
    
    if not stripe_customer_id and db_pool:
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT stripe_customer_id FROM organizations WHERE id = $1",
                org['organization_id']
            )
            if row:
                stripe_customer_id = row['stripe_customer_id']
    
    if not stripe_customer_id:
        raise HTTPException(status_code=400, detail="No billing account found. Please upgrade first.")
    
    try:
        return_url = request.return_url or "https://ontostandard.org/dashboard"
        session = stripe.billing_portal.Session.create(
            customer=stripe_customer_id,
            return_url=return_url
        )
        
        return {
            "portal_url": session.url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create portal session: {e}")

@app.get("/v1/billing/status")
async def get_billing_status(org: dict = Depends(validate_api_key)):
    """Get current subscription status"""
    if not db_pool:
        return {"status": "no_database"}
    
    async with db_pool.acquire() as conn:
        # Get organization with subscription info
        row = await conn.fetchrow("""
            SELECT o.tier, o.stripe_customer_id, s.stripe_subscription_id, s.status,
                   s.current_period_start, s.current_period_end, s.evaluations_used
            FROM organizations o
            LEFT JOIN subscriptions s ON o.id = s.organization_id AND s.status = 'active'
            WHERE o.id = $1
        """, org['organization_id'])
        
        if not row:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        layer_info = LAYERS.get(row['tier'], LAYERS['open'])
        
        return {
            "layer": row['tier'],
            "layer_info": layer_info,
            "stripe_customer_id": row['stripe_customer_id'],
            "subscription": {
                "id": row['stripe_subscription_id'],
                "status": row['status'] or "none",
                "current_period_start": row['current_period_start'].isoformat() if row['current_period_start'] else None,
                "current_period_end": row['current_period_end'].isoformat() if row['current_period_end'] else None,
                "evaluations_used": row['evaluations_used'] or 0
            } if row['stripe_subscription_id'] else None
        }

# ============================================================
# STRIPE WEBHOOK
# ============================================================

@app.post("/v1/webhooks/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events"""
    if not stripe:
        raise HTTPException(status_code=503, detail="Stripe not configured")
    
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    try:
        if STRIPE_WEBHOOK_SECRET:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
        else:
            # Dev mode - parse without verification
            event = json.loads(payload)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    event_type = event.get('type') if isinstance(event, dict) else event.type
    data = event.get('data', {}).get('object', {}) if isinstance(event, dict) else event.data.object
    
    print(f"[Stripe] Webhook: {event_type}")
    
    if not db_pool:
        return {"status": "received", "warning": "no database"}
    
    async with db_pool.acquire() as conn:
        # Handle different event types
        if event_type == 'checkout.session.completed':
            # Checkout completed - activate subscription
            org_id = data.get('metadata', {}).get('organization_id')
            layer = data.get('metadata', {}).get('layer')  # Layer from checkout metadata
            subscription_id = data.get('subscription')
            customer_id = data.get('customer')
            
            if org_id and layer:
                # Update organization layer (DB column is 'tier')
                await conn.execute("""
                    UPDATE organizations 
                    SET tier = $1, stripe_customer_id = $2, updated_at = NOW()
                    WHERE id = $3
                """, layer, customer_id, org_id)
                
                # Create subscription record
                await conn.execute("""
                    INSERT INTO subscriptions (organization_id, tier, stripe_subscription_id, status)
                    VALUES ($1, $2, $3, 'active')
                    ON CONFLICT (organization_id) 
                    DO UPDATE SET tier = $2, stripe_subscription_id = $3, status = 'active', updated_at = NOW()
                """, org_id, layer, subscription_id)
                
                # Log event
                await conn.execute("""
                    INSERT INTO audit_log (organization_id, action, resource_type, details)
                    VALUES ($1, 'subscription_created', 'subscription', $2)
                """, org_id, json.dumps({"layer": layer, "subscription_id": subscription_id}))
                
                print(f"[Stripe] Org {org_id} upgraded to {layer}")
        
        elif event_type == 'customer.subscription.updated':
            subscription_id = data.get('id')
            status = data.get('status')
            current_period_end = data.get('current_period_end')
            
            if subscription_id:
                await conn.execute("""
                    UPDATE subscriptions 
                    SET status = $1, 
                        current_period_end = to_timestamp($2),
                        updated_at = NOW()
                    WHERE stripe_subscription_id = $3
                """, status, current_period_end, subscription_id)
        
        elif event_type == 'customer.subscription.deleted':
            subscription_id = data.get('id')
            
            if subscription_id:
                # Downgrade to pilot
                row = await conn.fetchrow(
                    "SELECT organization_id FROM subscriptions WHERE stripe_subscription_id = $1",
                    subscription_id
                )
                if row:
                    await conn.execute(
                        "UPDATE organizations SET tier = 'open', updated_at = NOW() WHERE id = $1",
                        row['organization_id']
                    )
                    await conn.execute(
                        "UPDATE subscriptions SET status = 'canceled', updated_at = NOW() WHERE stripe_subscription_id = $1",
                        subscription_id
                    )
                    print(f"[Stripe] Org {row['organization_id']} downgraded to pilot")
        
        elif event_type == 'invoice.payment_failed':
            subscription_id = data.get('subscription')
            
            if subscription_id:
                await conn.execute("""
                    UPDATE subscriptions 
                    SET status = 'past_due', updated_at = NOW()
                    WHERE stripe_subscription_id = $1
                """, subscription_id)
    
    return {"status": "received", "event": event_type}

# ============================================================
# EVALUATION ENDPOINTS
# ============================================================

@app.post("/v1/evaluate")
async def submit_evaluation(
    request: EvaluationRequest,
    org: dict = Depends(validate_api_key)
):
    """Submit model predictions for evaluation"""
    if not db_pool:
        # Demo mode
        return {
            "evaluation_id": "demo-" + secrets.token_hex(8),
            "status": "demo_mode",
            "predictions_received": len(request.predictions)
        }
    
    layer = org.get('tier', 'open')  # DB column is 'tier'
    layer_info = LAYERS.get(layer, LAYERS['open'])
    
    async with db_pool.acquire() as conn:
        # Check certificate/evaluation limits based on layer
        if layer == 'open':
            # OPEN: 100 certificates per month
            limit = layer_info.get('certificates_per_month', 100)
            count = await conn.fetchval("""
                SELECT COUNT(*) FROM evaluations
                WHERE organization_id = $1
                AND submitted_at >= date_trunc('month', NOW())
            """, org['organization_id'])
            
            if count >= limit:
                raise HTTPException(
                    status_code=403, 
                    detail=f"Monthly certificate limit reached ({limit}). Upgrade to STANDARD layer."
                )
        elif layer == 'standard':
            # STANDARD: 10,000 certificates per year
            limit = layer_info.get('certificates_per_year', 10000)
            count = await conn.fetchval("""
                SELECT COUNT(*) FROM evaluations
                WHERE organization_id = $1
                AND submitted_at >= date_trunc('year', NOW())
            """, org['organization_id'])
            
            if count >= limit:
                raise HTTPException(
                    status_code=403, 
                    detail=f"Yearly certificate limit reached ({limit}). Contact sales for overage or upgrade to CRITICAL."
                )
        # CRITICAL: unlimited (-1)
        
        # Create evaluation
        eval_id = await conn.fetchval("""
            INSERT INTO evaluations (organization_id, model_name, model_version, status, metrics)
            VALUES ($1, $2, $3, 'pending', $4)
            RETURNING id
        """, org['organization_id'], request.model_name, request.model_version,
            json.dumps({
                "predictions_count": len(request.predictions),
                "layer": layer,
                "watermark": layer_info.get('watermark', False)
            }))
        
        # Log usage
        await conn.execute("""
            INSERT INTO usage_events (organization_id, event_type, resource_id, event_metadata)
            VALUES ($1, 'evaluation_submitted', $2, $3)
        """, org['organization_id'], eval_id, 
            json.dumps({"model": request.model_name, "predictions": len(request.predictions), "layer": layer}))
        
        # Update subscription usage counter
        await conn.execute("""
            UPDATE subscriptions 
            SET evaluations_used = COALESCE(evaluations_used, 0) + 1
            WHERE organization_id = $1 AND status = 'active'
        """, org['organization_id'])
        
        response = {
            "evaluation_id": str(eval_id),
            "status": "pending",
            "model_name": request.model_name,
            "predictions_received": len(request.predictions),
            "layer": layer,
            "message": "Evaluation queued for processing"
        }
        
        # Add watermark warning for OPEN layer
        if layer_info.get('watermark'):
            response["watermark"] = "ONTO Open"
            response["attribution_required"] = True
        
        return response

@app.get("/v1/evaluations")
async def list_evaluations(
    limit: int = 20,
    org: dict = Depends(validate_api_key)
):
    """List evaluations for organization"""
    if not db_pool:
        return {"evaluations": []}
    
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, model_name, model_version, status, risk_score, 
                   submitted_at, completed_at
            FROM evaluations
            WHERE organization_id = $1
            ORDER BY submitted_at DESC
            LIMIT $2
        """, org['organization_id'], limit)
        
        return {
            "evaluations": [
                {
                    "id": str(r['id']),
                    "model_name": r['model_name'],
                    "model_version": r['model_version'],
                    "status": r['status'],
                    "risk_score": r['risk_score'],
                    "submitted_at": r['submitted_at'].isoformat() if r['submitted_at'] else None,
                    "completed_at": r['completed_at'].isoformat() if r['completed_at'] else None
                }
                for r in rows
            ]
        }

@app.get("/v1/evaluations/{evaluation_id}")
async def get_evaluation(
    evaluation_id: str,
    org: dict = Depends(validate_api_key)
):
    """Get evaluation details"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT * FROM evaluations
            WHERE id = $1 AND organization_id = $2
        """, evaluation_id, org['organization_id'])
        
        if not row:
            raise HTTPException(status_code=404, detail="Evaluation not found")
        
        return {
            "id": str(row['id']),
            "model_name": row['model_name'],
            "model_version": row['model_version'],
            "status": row['status'],
            "metrics": row['metrics'],
            "risk_score": row['risk_score'],
            "recommendations": row['recommendations'],
            "submitted_at": row['submitted_at'].isoformat() if row['submitted_at'] else None,
            "completed_at": row['completed_at'].isoformat() if row['completed_at'] else None
        }

# ============================================================
# CERTIFICATE ENDPOINTS
# ============================================================

@app.get("/v1/certificates")
async def list_certificates(
    limit: int = 20,
    org: dict = Depends(validate_api_key)
):
    """List certificates for organization"""
    if not db_pool:
        return {"certificates": []}
    
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, certificate_number, model_name, level, 
                   issued_at, expires_at, revoked_at
            FROM certificates
            WHERE organization_id = $1
            ORDER BY issued_at DESC
            LIMIT $2
        """, org['organization_id'], limit)
        
        return {
            "certificates": [
                {
                    "id": str(r['id']),
                    "certificate_number": r['certificate_number'],
                    "model_name": r['model_name'],
                    "level": r['level'],
                    "status": "revoked" if r['revoked_at'] else "valid",
                    "issued_at": r['issued_at'].isoformat() if r['issued_at'] else None,
                    "expires_at": r['expires_at'].isoformat() if r['expires_at'] else None
                }
                for r in rows
            ]
        }

@app.get("/v1/certificates/{certificate_id}")
async def get_certificate(certificate_id: str):
    """Get certificate (public endpoint for verification)"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT c.*, o.name as org_name, o.tier as org_layer
            FROM certificates c
            JOIN organizations o ON c.organization_id = o.id
            WHERE c.id = $1 OR c.certificate_number = $1
        """, certificate_id)
        
        if not row:
            raise HTTPException(status_code=404, detail="Certificate not found")
        
        # Get layer info for watermark
        layer = row.get('org_layer', 'open')
        layer_info = LAYERS.get(layer, LAYERS['open'])
        
        response = {
            "certificate_number": row['certificate_number'],
            "organization": row['org_name'],
            "model_name": row['model_name'],
            "level": row['level'],
            "layer": layer,
            "metrics": row['metrics_snapshot'],
            "verification_hash": row['verification_hash'],
            "status": "revoked" if row['revoked_at'] else "valid",
            "issued_at": row['issued_at'].isoformat() if row['issued_at'] else None,
            "expires_at": row['expires_at'].isoformat() if row['expires_at'] else None,
            "verify_url": f"https://verify.ontostandard.org/{row['certificate_number']}"
        }
        
        # Add watermark for OPEN layer
        if layer_info.get('watermark'):
            response["watermark"] = "ONTO Open"
            response["attribution"] = "Verified by ONTO Open Source Protocol"
            response["attribution_required"] = True
        
        return response

# ============================================================
# ORGANIZATION ENDPOINTS
# ============================================================

@app.get("/v1/organization")
async def get_organization(org: dict = Depends(validate_api_key)):
    """Get organization details"""
    if not db_pool:
        return {"organization": org}
    
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT o.*, 
                   (SELECT COUNT(*) FROM evaluations WHERE organization_id = o.id) as eval_count,
                   (SELECT COUNT(*) FROM certificates WHERE organization_id = o.id) as cert_count
            FROM organizations o
            WHERE o.id = $1
        """, org['organization_id'])
        
        if not row:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        layer_info = LAYERS.get(row['tier'], LAYERS['open'])
        
        return {
            "id": str(row['id']),
            "name": row['name'],
            "slug": row['slug'],
            "layer": row['tier'],
            "layer_info": layer_info,
            "rate_limit": RATE_LIMITS.get(row['tier'], RATE_LIMITS['open']),
            "evaluations_count": row['eval_count'],
            "certificates_count": row['cert_count'],
            "stripe_customer_id": row['stripe_customer_id'],
            "created_at": row['created_at'].isoformat() if row['created_at'] else None
        }

# ============================================================
# ADMIN ENDPOINTS
# ============================================================

@app.get("/v1/admin/stats")
async def get_admin_stats(org: dict = Depends(validate_api_key)):
    """Get system stats (admin only)"""
    # TODO: Add admin role check
    if not db_pool:
        return {"error": "Database not available"}
    
    async with db_pool.acquire() as conn:
        stats = {}
        
        stats['organizations'] = await conn.fetchval("SELECT COUNT(*) FROM organizations")
        stats['users'] = await conn.fetchval("SELECT COUNT(*) FROM users")
        stats['api_keys'] = await conn.fetchval("SELECT COUNT(*) FROM api_keys WHERE is_active = true")
        stats['evaluations'] = await conn.fetchval("SELECT COUNT(*) FROM evaluations")
        stats['certificates'] = await conn.fetchval("SELECT COUNT(*) FROM certificates")
        
        # Active subscriptions
        stats['active_subscriptions'] = await conn.fetchval(
            "SELECT COUNT(*) FROM subscriptions WHERE status = 'active'"
        )
        
        # By tier
        tier_counts = await conn.fetch("""
            SELECT tier, COUNT(*) as count 
            FROM organizations 
            GROUP BY tier
        """)
        stats['by_layer'] = {r['tier']: r['count'] for r in tier_counts}
        
        return stats

# ============================================================
# RATE LIMIT INFO ENDPOINT
# ============================================================

@app.get("/v1/rate-limit")
async def get_rate_limit_info(request: Request):
    """Get current rate limit status"""
    client_ip = request.client.host if request.client else "unknown"
    api_key = request.headers.get("x-api-key", "")
    
    layer = "public"
    if api_key:
        key = f"api:{hash_api_key(api_key)[:16]}"
        if db_pool:
            async with db_pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT o.tier FROM api_keys ak
                    JOIN organizations o ON ak.organization_id = o.id
                    WHERE ak.key_hash = $1 AND ak.is_active = true
                """, hash_api_key(api_key))
                if row:
                    layer = row['tier']  # DB column name
    else:
        key = f"ip:{client_ip}"
    
    limit = RATE_LIMITS.get(layer, RATE_LIMITS["public"])
    
    # Count current usage
    rate_limiter._cleanup(key)
    used = sum(count for _, count in rate_limiter.requests.get(key, []))
    
    return {
        "layer": layer,
        "limit": limit,
        "remaining": max(0, limit - used),
        "reset_in": rate_limiter.get_reset_time(key),
        "window": "60 seconds"
    }

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("=" * 50)
    print("ONTO API Server")
    print("=" * 50)
    
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
