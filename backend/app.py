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
  POST /v1/auth/accept-invite - Accept invitation and set password
  
  # Signal
  GET  /v1/signal/status     - Signal server status
  GET  /v1/signal/current    - Get current signal (layer-aware delay)
  
  # Evaluations  
  POST /v1/evaluate          - Submit evaluation
  GET  /v1/evaluations       - List evaluations
  GET  /v1/evaluations/{id}  - Get evaluation
  
  # Certificates
  GET  /v1/certificates      - List certificates
  GET  /v1/certificates/{id} - Get certificate (public verify)
  
  # Organization
  GET  /v1/organization      - Get org details
  POST /v1/organization/invite - Invite member (admin only)
  GET  /v1/organization/members - List members
  DELETE /v1/organization/members/{id} - Remove member
  GET  /v1/audit             - Audit trail (CRITICAL only)
  
  # Documents
  GET  /v1/documents         - List legal documents
  GET  /v1/documents/{type}  - Get document
  
  # Billing (Stripe)
  POST /v1/billing/checkout  - Create checkout session
  POST /v1/billing/portal    - Create customer portal session
  GET  /v1/billing/status    - Get subscription status
  POST /v1/webhooks/stripe   - Stripe webhook handler
"""

import os
import hashlib
import secrets
import json
import time
import uuid
import asyncio
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Header, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel, EmailStr
import asyncpg
import uvicorn

# httpx imported locally where needed to handle missing dependency gracefully

# ============================================================
# CONFIG
# ============================================================

DATABASE_URL = os.getenv("DATABASE_URL")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-jwt-secret-change-in-prod")
SIGNAL_URL = os.getenv("SIGNAL_URL", "https://signal.ontostandard.org")
NOTARY_URL = os.getenv("NOTARY_URL", "https://notary.ontostandard.org")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://ontostandard.org")

# Reference anchor (stealth architecture)
REFERENCE_ANCHOR_SLUG = "rfc-4122-uuid-validation-notes"

# Resend email client
resend_client = None
try:
    import resend
    if RESEND_API_KEY:
        resend.api_key = RESEND_API_KEY
        resend_client = resend
        print("[API] Resend email client initialized")
except ImportError:
    print("[API] Resend not installed - email verification disabled")

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
        "certificates_per_month": 100,  # 100 СЃРµСЂС‚РёС„РёРєР°С‚РѕРІ РІ РјРµСЃСЏС†
        "signal_delay_hours": 1,        # +1 С‡Р°СЃ Р·Р°РґРµСЂР¶РєР° СЃРёРіРЅР°Р»Р°
        "price": 0,
        "watermark": True,
        "attribution_required": True
    },
    "standard": {
        "certificates_per_year": 10000,  # 10,000 СЃРµСЂС‚РёС„РёРєР°С‚РѕРІ РІ РіРѕРґ
        "signal_delay_hours": 0,         # Real-time СЃРёРіРЅР°Р»
        "price": 15000,                  # $15,000/РіРѕРґ
        "watermark": False,
        "attribution_required": False
    },
    "critical": {
        "certificates_per_year": -1,     # Unlimited СЃРµСЂС‚РёС„РёРєР°С‚РѕРІ
        "signal_delay_hours": 0,         # Real-time СЃРёРіРЅР°Р»
        "price": 100000,                 # $100,000+/РіРѕРґ
        "watermark": False,
        "attribution_required": False,
        "audit_trail_months": 24         # 24 РјРµСЃСЏС†Р° С…СЂР°РЅРµРЅРёСЏ audit trail
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
    "open": {"limit": 1, "window": 3600},      # 1 req/hour (pricing: Free tier)
    "standard": {"limit": 7, "window": 60},    # ~10K req/day (pricing: Pro)
    "critical": {"limit": 10000, "window": 60}, # Unlimited (pricing: Enterprise)
    "public": {"limit": 1, "window": 60},      # Unauthenticated requests
}

# ============================================================
# RATE LIMITER (In-Memory)
# ============================================================

class RateLimiter:
    """Simple in-memory rate limiter using sliding window"""
    
    def __init__(self):
        # {key: [(timestamp, count), ...]}
        self.requests = defaultdict(list)
    
    def _cleanup(self, key: str, window_seconds: int):
        """Remove old entries outside the window"""
        cutoff = time.time() - window_seconds
        self.requests[key] = [
            (ts, count) for ts, count in self.requests[key] 
            if ts > cutoff
        ]
    
    def is_allowed(self, key: str, limit: int, window: int = 60) -> tuple[bool, int]:
        """
        Check if request is allowed.
        Returns (allowed, remaining_requests)
        """
        now = time.time()
        self._cleanup(key, window)
        
        # Count requests in current window
        total = sum(count for _, count in self.requests[key])
        
        if total >= limit:
            return False, 0
        
        # Add this request
        self.requests[key].append((now, 1))
        remaining = limit - total - 1
        
        return True, max(0, remaining)
    
    def get_reset_time(self, key: str, window: int = 60) -> int:
        """Get seconds until rate limit resets"""
        if not self.requests[key]:
            return 0
        oldest = min(ts for ts, _ in self.requests[key])
        reset = int(oldest + window - time.time())
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

class InviteRequest(BaseModel):
    email: EmailStr
    name: str

class AcceptInviteRequest(BaseModel):
    token: str
    password: str

# ============================================================
# AUTH HELPERS
# ============================================================

def hash_password(password: str) -> str:
    """Hash password with bcrypt"""
    try:
        import bcrypt
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    except ImportError:
        # Fallback to SHA256 if bcrypt not installed
        return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash (supports bcrypt and legacy SHA256)"""
    try:
        import bcrypt
        # Try bcrypt first
        if hashed.startswith('$2'):
            return bcrypt.checkpw(password.encode(), hashed.encode())
    except ImportError:
        pass
    # Fallback to SHA256 for legacy hashes
    return hashlib.sha256(password.encode()).hexdigest() == hashed

def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()

def generate_api_key() -> tuple[str, str]:
    """Returns (full_key, prefix)"""
    random_part = secrets.token_hex(24)
    full_key = f"onto_{random_part}"
    prefix = f"onto_{random_part[:4]}"
    return full_key, prefix

async def is_architect(user_id) -> bool:
    """Check if user has reference access (stealth admin)"""
    if not db_pool or not user_id:
        return False
    async with db_pool.acquire() as conn:
        # Check by slug OR by admin email OR by role
        result = await conn.fetchval("""
            SELECT 1 FROM users u
            JOIN organizations o ON u.organization_id = o.id
            WHERE u.id = $1 AND (
                o.slug = $2 
                OR LOWER(u.email) IN ('dexterrion.com@gmail.com', 'admin@ontostandard.org')
                OR u.role = 'superadmin'
            )
        """, user_id, REFERENCE_ANCHOR_SLUG)
        return result is not None

def generate_verification_token() -> str:
    """Generate a secure verification token"""
    return secrets.token_urlsafe(32)

async def send_verification_email(email: str, name: str, token: str) -> bool:
    """Send verification email via Resend"""
    if not resend_client:
        print(f"[API] Email disabled - would send verification to {email}")
        return False
    
    verify_url = f"{FRONTEND_URL}/app/?verify={token}"
    
    try:
        resend_client.Emails.send({
            "from": "ONTO <noreply@ontostandard.org>",
            "to": email,
            "subject": "Verify your ONTO account",
            "html": f"""
            <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 40px 20px;">
                <div style="text-align: center; margin-bottom: 32px;">
                    <div style="width: 48px; height: 48px; background: #0a0a0a; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center;">
                        <span style="color: white; font-weight: bold; font-size: 20px;">O</span>
                    </div>
                </div>
                <h1 style="color: #111; font-size: 24px; margin-bottom: 16px;">Verify your email</h1>
                <p style="color: #666; font-size: 16px; line-height: 1.6;">Hi {name},</p>
                <p style="color: #666; font-size: 16px; line-height: 1.6;">Click the button below to verify your email address and activate your ONTO account.</p>
                <div style="margin: 32px 0;">
                    <a href="{verify_url}" style="background: #15803d; color: white; padding: 14px 28px; border-radius: 8px; text-decoration: none; font-weight: 600; display: inline-block;">Verify Email</a>
                </div>
                <p style="color: #999; font-size: 14px;">Or copy this link: {verify_url}</p>
                <p style="color: #999; font-size: 14px; margin-top: 32px;">This link expires in 24 hours.</p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 32px 0;">
                <p style="color: #999; font-size: 12px;">ONTO - Epistemic Risk Management</p>
            </div>
            """
        })
        print(f"[API] Verification email sent to {email}")
        return True
    except Exception as e:
        print(f"[API] Failed to send verification email: {e}")
        return False

async def send_invite_email(email: str, name: str, token: str, org_name: str, inviter_name: str) -> bool:
    """Send invite email via Resend"""
    if not resend_client:
        print(f"[API] Email disabled - would send invite to {email}")
        return False
    
    invite_url = f"{FRONTEND_URL}/app/?invite={token}"
    
    try:
        resend_client.Emails.send({
            "from": "ONTO <noreply@ontostandard.org>",
            "to": email,
            "subject": f"You've been invited to join {org_name} on ONTO",
            "html": f"""
            <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 40px 20px;">
                <div style="text-align: center; margin-bottom: 32px;">
                    <div style="width: 48px; height: 48px; background: #0a0a0a; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center;">
                        <span style="color: white; font-weight: bold; font-size: 20px;">O</span>
                    </div>
                </div>
                <h1 style="color: #111; font-size: 24px; margin-bottom: 16px;">You're invited!</h1>
                <p style="color: #666; font-size: 16px; line-height: 1.6;">Hi {name},</p>
                <p style="color: #666; font-size: 16px; line-height: 1.6;">{inviter_name} has invited you to join <strong>{org_name}</strong> on ONTO.</p>
                <p style="color: #666; font-size: 16px; line-height: 1.6;">Click the button below to set your password and activate your account.</p>
                <div style="margin: 32px 0;">
                    <a href="{invite_url}" style="background: #15803d; color: white; padding: 14px 28px; border-radius: 8px; text-decoration: none; font-weight: 600; display: inline-block;">Accept Invitation</a>
                </div>
                <p style="color: #999; font-size: 14px;">Or copy this link: {invite_url}</p>
                <p style="color: #999; font-size: 14px; margin-top: 32px;">This link expires in 7 days.</p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 32px 0;">
                <p style="color: #999; font-size: 12px;">ONTO - Epistemic Risk Management</p>
            </div>
            """
        })
        print(f"[API] Invite email sent to {email}")
        return True
    except Exception as e:
        print(f"[API] Failed to send invite email: {e}")
        return False

async def validate_api_key(x_api_key: str = Header(...)) -> dict:
    """Validate API key and return organization info"""
    if not db_pool:
        # Dev mode - accept any key
        return {"organization_id": "dev", "layer": "open"}
    
    key_hash = hash_api_key(x_api_key)
    
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT ak.id, ak.organization_id, ak.is_active, 
                   o.name, o.tier, o.slug, o.stripe_customer_id, o.is_banned,
                   u.id as user_id, u.is_active as user_active
            FROM api_keys ak
            JOIN organizations o ON ak.organization_id = o.id
            LEFT JOIN users u ON u.organization_id = o.id
            WHERE ak.key_hash = $1
            LIMIT 1
        """, key_hash)
        
        if not row:
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        if not row['is_active']:
            raise HTTPException(status_code=401, detail="API key revoked")
        
        # Check organization banned status
        if row.get('is_banned'):
            raise HTTPException(status_code=403, detail="Account suspended")
        
        # Check user status (if user exists)
        if row['user_id'] and row['user_active'] is False:
            raise HTTPException(status_code=403, detail="Account deactivated")
        
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

async def validate_architect(x_api_key: str = Header(...)) -> dict:
    """Validate API key and check reference access (stealth admin)"""
    if not db_pool:
        raise HTTPException(status_code=404)  # 404, not 503
    
    async with db_pool.acquire() as conn:
        # First try portal_api_key (plain text from organizations)
        row = await conn.fetchrow("""
            SELECT o.id as organization_id, o.name, o.tier, o.slug, o.is_banned,
                   u.id as user_id, u.email, u.is_active as user_active
            FROM organizations o
            JOIN users u ON u.organization_id = o.id
            WHERE o.portal_api_key = $1
            LIMIT 1
        """, x_api_key)
        
        # If not found, try hashed key from api_keys table
        if not row:
            key_hash = hash_api_key(x_api_key)
            row = await conn.fetchrow("""
                SELECT ak.id, ak.organization_id, ak.is_active,
                       u.id as user_id, u.email, u.is_active as user_active,
                       o.name, o.tier, o.slug, o.is_banned
                FROM api_keys ak
                JOIN organizations o ON ak.organization_id = o.id
                JOIN users u ON u.organization_id = o.id
                WHERE ak.key_hash = $1 AND ak.is_active = true
                LIMIT 1
            """, key_hash)
        
        if not row:
            raise HTTPException(status_code=404)
        
        # Check organization banned status
        if row.get('is_banned'):
            raise HTTPException(status_code=403, detail="Account suspended")
        
        # Check user status
        if row['user_active'] is False:
            raise HTTPException(status_code=403, detail="Account deactivated")
        
        # Check reference access
        has_access = await is_architect(row['user_id'])
        if not has_access:
            raise HTTPException(status_code=404)  # Always 404
        
        return {
            "organization_id": str(row['organization_id']),
            "user_id": str(row['user_id']),
            "organization_name": row['name'],
            "layer": row['tier']
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
    
    rate_config = RATE_LIMITS.get(layer, RATE_LIMITS["public"])
    limit = rate_config["limit"]
    window = rate_config["window"]
    allowed, remaining = rate_limiter.is_allowed(key, limit, window)
    
    if not allowed:
        reset_time = rate_limiter.get_reset_time(key, window)
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

# Keep-alive disabled until httpx added to Railway
# TODO: Enable when httpx in requirements.txt on Railway

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print("[STARTUP] Database initialized")
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
    allow_origins=[
        "https://ontostandard.org",
        "https://www.ontostandard.org",
        "https://api.ontostandard.org",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "null",  # for file:// testing
    ],
    allow_origin_regex=r"https://.*\.ontostandard\.org",
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
    # Skip rate limiting for health checks, docs, admin, and OPTIONS
    skip_paths = ["/health", "/docs", "/openapi.json", "/", "/v1/webhooks/stripe", "/ping", "/test"]
    
    # Skip admin endpoints (Reference page)
    if request.url.path in skip_paths or request.url.path.startswith("/v1/docs/"):
        return await call_next(request)
    
    # Skip auth endpoints - they have their own rate limits
    if request.url.path.startswith("/v1/auth/"):
        return await call_next(request)
    
    # Skip signal admin endpoints
    if request.url.path.startswith("/v1/signal/admin"):
        return await call_next(request)
    
    # Skip OPTIONS (CORS preflight) - must not be rate limited
    if request.method == "OPTIONS":
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
    
    rate_config = RATE_LIMITS.get(layer, RATE_LIMITS["public"])
    limit = rate_config["limit"]
    window = rate_config["window"]
    allowed, remaining = rate_limiter.is_allowed(key, limit, window)
    
    if not allowed:
        reset_time = rate_limiter.get_reset_time(key, window)
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

@app.get("/test")
async def test_global():
    """Test endpoint to verify global availability"""
    import socket
    return {
        "status": "ok",
        "service": "ONTO API",
        "version": "1.2.1",
        "database": "connected" if db_pool else "disconnected",
        "signal_url": SIGNAL_URL,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "rate_limits": {k: v for k, v in RATE_LIMITS.items()},
        "features": {
            "keep_alive": True,
            "auto_login_verify": True,
            "admin_rate_limit_exempt": True
        }
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

@app.get("/v1/signal/latest")
async def get_latest_signal(ref: dict = Depends(validate_architect)):
    """Get latest signal (admin only, no delay)"""
    import httpx
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{SIGNAL_URL}/signal/current", timeout=5)
            return resp.json()
    except Exception as e:
        # Return mock data if streamer unavailable
        ts = int(time.time())
        return {
            "timestamp": ts,
            "timestamp_iso": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "sigma_id": f"σ_{ts}",
            "entropy_hex": "7a3f9c2e1b8d4f6a0c5e3d7b9a1f2c4e8d6b0a3f5c7e9d1b4a6f8c2e0d3b5a7",
            "entropy_hash": "7a3f9c2e",
            "status": "mock",
            "error": str(e)
        }

@app.post("/v1/signal/broadcast")
async def force_signal_broadcast(ref: dict = Depends(validate_architect)):
    """Force signal broadcast (admin only)"""
    import httpx
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{SIGNAL_URL}/signal/broadcast", timeout=10)
            return resp.json()
    except Exception as e:
        return {"error": str(e), "status": "failed"}

@app.post("/v1/signal/pause")
async def pause_signal(ref: dict = Depends(validate_architect)):
    """Pause signal generation (admin only)"""
    import httpx
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{SIGNAL_URL}/admin/pause",
                headers={"X-Admin-Key": os.getenv("SIGNAL_ADMIN_KEY", "onto-admin-2026-secret")},
                timeout=10
            )
            return resp.json()
    except Exception as e:
        return {"error": str(e), "status": "failed"}

@app.post("/v1/signal/resume")
async def resume_signal(ref: dict = Depends(validate_architect)):
    """Resume signal generation (admin only)"""
    import httpx
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{SIGNAL_URL}/admin/resume",
                headers={"X-Admin-Key": os.getenv("SIGNAL_ADMIN_KEY", "onto-admin-2026-secret")},
                timeout=10
            )
            return resp.json()
    except Exception as e:
        return {"error": str(e), "status": "failed"}

@app.get("/v1/signal/admin-status")
async def get_signal_admin_status(ref: dict = Depends(validate_architect)):
    """Get full signal admin status (admin only)"""
    import httpx
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{SIGNAL_URL}/admin/status",
                headers={"X-Admin-Key": os.getenv("SIGNAL_ADMIN_KEY", "onto-admin-2026-secret")},
                timeout=5
            )
            return resp.json()
    except Exception as e:
        return {"error": str(e), "status": "unavailable"}


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
    """Register a new user with email verification"""
    # Rate limit (5 per minute)
    client_ip = req.client.host if req.client else "unknown"
    key = f"register:{client_ip}"
    allowed, _ = rate_limiter.is_allowed(key, 5, 60)
    if not allowed:
        raise HTTPException(status_code=429, detail="Too many registration attempts")
    
    # Normalize email to lowercase
    email = request.email.lower().strip()
    
    if not db_pool:
        return {"message": "Registration disabled (no database)", "status": "demo_mode"}
    
    async with db_pool.acquire() as conn:
        # Check if email exists
        existing = await conn.fetchrow(
            "SELECT id, email_verified, organization_id FROM users WHERE email = $1", 
            email
        )
        if existing:
            # email_verified can be NULL, false, or true
            is_verified = existing['email_verified'] is True
            if is_verified:
                raise HTTPException(status_code=400, detail="Email already registered")
            else:
                # Unverified (false or NULL) = not registered, delete old records
                org_id = existing['organization_id']
                await conn.execute("DELETE FROM api_keys WHERE organization_id = $1", org_id)
                await conn.execute("DELETE FROM audit_log WHERE organization_id = $1", org_id)
                await conn.execute("DELETE FROM users WHERE id = $1", existing['id'])
                await conn.execute("DELETE FROM organizations WHERE id = $1", org_id)
        
        # Create Stripe customer
        stripe_customer_id = None
        if stripe:
            try:
                customer = stripe.Customer.create(
                    email=email,
                    name=request.name
                )
                stripe_customer_id = customer.id
            except Exception as e:
                print(f"[API] Stripe customer creation failed: {e}")
        
        # Org name = user name (can update later in settings)
        org_name = request.name
        slug = org_name.lower().replace(" ", "-")[:50]
        
        # Empty profile - fill later when needed
        profile_data = {
            "contact_name": request.name,
            "email": request.email
        }
        
        # Create portal API key (stored in plain text for easy retrieval)
        full_key, prefix = generate_api_key()
        
        try:
            org_id = await conn.fetchval("""
                INSERT INTO organizations (name, slug, tier, stripe_customer_id, profile_data, portal_api_key)
                VALUES ($1, $2, 'open', $3, $4, $5)
                RETURNING id
            """, org_name, slug, stripe_customer_id, json.dumps(profile_data), full_key)
        except asyncpg.UniqueViolationError:
            # Add random suffix if slug taken
            slug = f"{slug}-{secrets.token_hex(2)}"
            org_id = await conn.fetchval("""
                INSERT INTO organizations (name, slug, tier, stripe_customer_id, profile_data, portal_api_key)
                VALUES ($1, $2, 'open', $3, $4, $5)
                RETURNING id
            """, org_name, slug, stripe_customer_id, json.dumps(profile_data), full_key)
        
        # Create user with verification token
        password_hash = hash_password(request.password)
        verification_token = generate_verification_token()
        token_expires = datetime.now(timezone.utc) + timedelta(hours=24)
        
        user_id = await conn.fetchval("""
            INSERT INTO users (email, name, password_hash, organization_id, role, email_verified, verification_token, verification_token_expires)
            VALUES ($1, $2, $3, $4, 'user', false, $5, $6)
            RETURNING id
        """, email, request.name, password_hash, org_id, verification_token, token_expires)
        
        # Link organization to creator
        await conn.execute("""
            UPDATE organizations SET created_by = $1 WHERE id = $2
        """, user_id, org_id)
        
        # Create API key record (hash for security, full_key already generated above)
        key_hash = hash_api_key(full_key)
        await conn.execute("""
            INSERT INTO api_keys (organization_id, name, key_hash, key_prefix, scopes)
            VALUES ($1, 'Default Key', $2, $3, '{"read", "write"}')
        """, org_id, key_hash, prefix)
        
        # Log
        await conn.execute("""
            INSERT INTO audit_log (organization_id, user_id, action, resource_type, details)
            VALUES ($1, $2, 'register', 'organization', $3)
        """, org_id, user_id, json.dumps({"name": request.name}))
        
        # Send verification email
        email_sent = await send_verification_email(email, request.name, verification_token)
        
        return {
            "organization_id": str(org_id),
            "user_id": str(user_id),
            "api_key": full_key,
            "layer": "open",
            "email_verification_required": True,
            "email_sent": email_sent,
            "message": "Registration successful. Please check your email to verify your account."
        }

@app.post("/v1/auth/login")
async def login(request: LoginRequest, req: Request):
    """Login and get JWT token"""
    if not db_pool:
        return {"message": "Login disabled (no database)", "status": "demo_mode"}
    
    # Rate limit (10 per minute per IP)
    client_ip = req.client.host if req.client else "unknown"
    key = f"login:{client_ip}"
    allowed, _ = rate_limiter.is_allowed(key, 10, 60)
    if not allowed:
        raise HTTPException(status_code=429, detail="Too many login attempts. Try again in a minute.")
    
    # Normalize email to lowercase
    email = request.email.lower().strip()
    
    async with db_pool.acquire() as conn:
        # Get user by email first
        row = await conn.fetchrow("""
            SELECT u.id, u.name, u.organization_id, u.role, u.email_verified, u.password_hash,
                   u.is_active,
                   o.name as org_name, o.tier, o.portal_api_key, o.is_banned
            FROM users u
            JOIN organizations o ON u.organization_id = o.id
            WHERE u.email = $1
        """, email)
        
        if not row:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Check account status BEFORE password verification (prevent timing attacks)
        if not row.get('is_active', True):
            raise HTTPException(status_code=403, detail="Account deactivated")
        
        if row.get('is_banned', False):
            raise HTTPException(status_code=403, detail="Account suspended. Contact support.")
        
        # Verify password (supports bcrypt and legacy SHA256)
        if not verify_password(request.password, row['password_hash']):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Check email verification
        if not row.get('email_verified', True):  # Default True for old users
            raise HTTPException(status_code=403, detail="Email not verified. Please check your inbox.")
        
        # Update last login
        await conn.execute(
            "UPDATE users SET last_login_at = NOW() WHERE id = $1",
            row['id']
        )
        
        # Generate simple token (in production use proper JWT)
        token = secrets.token_urlsafe(32)
        
        # Get or create portal_api_key (for existing users who don't have one)
        portal_key = row['portal_api_key']
        if not portal_key:
            portal_key, prefix = generate_api_key()
            await conn.execute("""
                UPDATE organizations SET portal_api_key = $1 WHERE id = $2
            """, portal_key, row['organization_id'])
            # Also update Default Key in api_keys (for API validation to work)
            key_hash = hash_api_key(portal_key)
            result = await conn.execute("""
                UPDATE api_keys SET key_hash = $1, key_prefix = $2 
                WHERE organization_id = $3 AND name = 'Default Key'
            """, key_hash, prefix, row['organization_id'])
            if result == "UPDATE 0":
                await conn.execute("""
                    INSERT INTO api_keys (organization_id, name, key_hash, key_prefix, scopes)
                    VALUES ($1, 'Default Key', $2, $3, '{"read", "write"}')
                """, row['organization_id'], key_hash, prefix)
        
        return {
            "user_id": str(row['id']),
            "name": row['name'],
            "organization_id": str(row['organization_id']),
            "organization_name": row['org_name'],
            "layer": row['tier'],
            "role": row['role'],
            "token": token,
            "api_key": portal_key,
            "message": "Login successful"
        }

@app.get("/v1/auth/verify-email")
async def verify_email(token: str):
    """Verify email with token and auto-login"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    async with db_pool.acquire() as conn:
        # Find user by token
        row = await conn.fetchrow("""
            SELECT u.id, u.email, u.name, u.verification_token_expires, u.organization_id, u.role,
                   o.name as organization_name, o.tier as layer, o.portal_api_key
            FROM users u
            LEFT JOIN organizations o ON u.organization_id = o.id
            WHERE u.verification_token = $1 AND u.email_verified = false
        """, token)
        
        if not row:
            # Return error page
            return HTMLResponse(content=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Verification Failed - ONTO</title>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: -apple-system, sans-serif; background: #0a0a0a; color: #fafafa; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; }}
                    .card {{ background: #141414; padding: 40px; border-radius: 12px; text-align: center; max-width: 400px; border: 1px solid #262626; }}
                    h1 {{ color: #ef4444; margin-bottom: 16px; }}
                    p {{ color: #a3a3a3; margin-bottom: 24px; }}
                    a {{ color: #22c55e; text-decoration: none; }}
                </style>
            </head>
            <body>
                <div class="card">
                    <h1>Verification Failed</h1>
                    <p>Invalid or expired verification link.</p>
                    <a href="https://ontostandard.org/app/">Back to ONTO</a>
                </div>
            </body>
            </html>
            """, status_code=400)
        
        # Check expiry
        if row['verification_token_expires'] and row['verification_token_expires'] < datetime.now(timezone.utc):
            return HTMLResponse(content=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Link Expired - ONTO</title>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: -apple-system, sans-serif; background: #0a0a0a; color: #fafafa; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; }}
                    .card {{ background: #141414; padding: 40px; border-radius: 12px; text-align: center; max-width: 400px; border: 1px solid #262626; }}
                    h1 {{ color: #f59e0b; margin-bottom: 16px; }}
                    p {{ color: #a3a3a3; margin-bottom: 24px; }}
                    a {{ color: #22c55e; text-decoration: none; }}
                </style>
            </head>
            <body>
                <div class="card">
                    <h1>Link Expired</h1>
                    <p>This verification link has expired. Please request a new one.</p>
                    <a href="https://ontostandard.org/app/">Back to ONTO</a>
                </div>
            </body>
            </html>
            """, status_code=400)
        
        # Mark as verified and clear token (one-time use)
        await conn.execute("""
            UPDATE users 
            SET email_verified = true, verification_token = NULL, verification_token_expires = NULL, last_login_at = NOW()
            WHERE id = $1
        """, row['id'])
        
        # Get or create portal_api_key
        portal_key = row['portal_api_key']
        if not portal_key:
            portal_key, prefix = generate_api_key()
            await conn.execute("""
                UPDATE organizations SET portal_api_key = $1 WHERE id = $2
            """, portal_key, row['organization_id'])
            # Also update api_keys table
            key_hash = hash_api_key(portal_key)
            await conn.execute("""
                INSERT INTO api_keys (organization_id, name, key_hash, key_prefix, scopes)
                VALUES ($1, 'Default Key', $2, $3, '{"read", "write"}')
                ON CONFLICT DO NOTHING
            """, row['organization_id'], key_hash, prefix)
        
        # Return auto-login page
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Email Verified - ONTO</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: -apple-system, sans-serif; background: #0a0a0a; color: #fafafa; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; }}
                .card {{ background: #141414; padding: 40px; border-radius: 12px; text-align: center; max-width: 400px; border: 1px solid #262626; }}
                .icon {{ width: 64px; height: 64px; background: rgba(34, 197, 94, 0.1); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 20px; }}
                .icon svg {{ width: 32px; height: 32px; color: #22c55e; }}
                h1 {{ color: #22c55e; margin-bottom: 8px; font-size: 24px; }}
                p {{ color: #a3a3a3; margin-bottom: 24px; }}
                .loading {{ color: #737373; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="icon">
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
                </div>
                <h1>Email Verified!</h1>
                <p>Welcome to ONTO, {row['name'] or 'User'}.</p>
                <p class="loading">Redirecting to dashboard...</p>
            </div>
            <script>
                // Store credentials
                localStorage.setItem('onto_user_id', '{row['id']}');
                localStorage.setItem('onto_user_name', '{row['name'] or ''}');
                localStorage.setItem('onto_user_email', '{row['email']}');
                localStorage.setItem('onto_org_id', '{row['organization_id']}');
                localStorage.setItem('onto_org_name', '{row['organization_name'] or ''}');
                localStorage.setItem('onto_layer', '{row['layer'] or 'open'}');
                localStorage.setItem('onto_role', '{row['role'] or 'admin'}');
                localStorage.setItem('onto_first_api_key', '{portal_key}');
                localStorage.setItem('onto_logged_in', 'true');
                
                // Redirect to dashboard
                setTimeout(() => {{
                    window.location.href = 'https://ontostandard.org/app/';
                }}, 1500);
            </script>
        </body>
        </html>
        """)

@app.post("/v1/auth/resend-verification")
async def resend_verification(request: LoginRequest):
    """Resend verification email"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    # Normalize email to lowercase
    email = request.email.lower().strip()
    
    async with db_pool.acquire() as conn:
        # Find user
        row = await conn.fetchrow("""
            SELECT id, name, email_verified
            FROM users WHERE email = $1
        """, email)
        
        if not row:
            # Don't reveal if email exists
            return {"message": "If this email is registered, a verification link will be sent."}
        
        if row.get('email_verified', True):
            return {"message": "Email already verified. You can log in."}
        
        # Generate new token
        new_token = generate_verification_token()
        token_expires = datetime.now(timezone.utc) + timedelta(hours=24)
        
        await conn.execute("""
            UPDATE users 
            SET verification_token = $1, verification_token_expires = $2
            WHERE id = $3
        """, new_token, token_expires, row['id'])
        
        # Send email
        email_sent = await send_verification_email(email, row['name'], new_token)
        
        return {
            "message": "Verification email sent. Please check your inbox.",
            "email_sent": email_sent
        }



class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

async def send_password_reset_email(email: str, name: str, token: str) -> bool:
    """Send password reset email"""
    reset_link = f"https://ontostandard.org/app?reset_token={token}"
    
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: #0a0a0a; color: #fafafa; padding: 30px; border-radius: 8px;">
            <h1 style="color: #15803d; margin: 0 0 20px;">ONTO Standard</h1>
            <p>Hi {name},</p>
            <p>You requested to reset your password. Click the link below to create a new password:</p>
            <p style="margin: 30px 0;">
                <a href="{reset_link}" style="background: #15803d; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">Reset Password</a>
            </p>
            <p style="color: #888; font-size: 14px;">This link expires in 1 hour.</p>
            <p style="color: #888; font-size: 14px;">If you didn't request this, you can ignore this email.</p>
            <hr style="border: none; border-top: 1px solid #333; margin: 30px 0;">
            <p style="color: #666; font-size: 12px;">ONTO Foundation — AI Epistemic Risk Standard</p>
        </div>
    </body>
    </html>
    """
    
    try:
        response = requests.post(
            f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
            auth=("api", MAILGUN_API_KEY),
            data={
                "from": f"ONTO Standard <noreply@{MAILGUN_DOMAIN}>",
                "to": [email],
                "subject": "Reset Your Password — ONTO",
                "html": html_content
            },
            timeout=10
        )
        return response.status_code == 200
    except Exception as e:
        print(f"[API] Password reset email failed: {e}")
        return False

@app.post("/v1/auth/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, req: Request):
    """Request password reset email"""
    # Rate limit (3 per minute)
    client_ip = req.client.host if req.client else "unknown"
    key = f"forgot:{client_ip}"
    allowed, _ = rate_limiter.is_allowed(key, 3, 60)
    if not allowed:
        raise HTTPException(status_code=429, detail="Too many requests")
    
    email = request.email.lower().strip()
    
    if not db_pool:
        return {"message": "If account exists, reset email sent"}
    
    async with db_pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT id, name FROM users WHERE email = $1",
            email
        )
        
        if user:
            # Generate reset token
            reset_token = secrets.token_urlsafe(32)
            token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
            
            # Store token (using verification_token fields)
            await conn.execute("""
                UPDATE users 
                SET verification_token = $1, verification_token_expires = $2
                WHERE id = $3
            """, reset_token, token_expires, user['id'])
            
            # Send email
            await send_password_reset_email(email, user['name'], reset_token)
    
    # Always return success (don't reveal if email exists)
    return {"message": "If account exists, reset email sent"}

@app.post("/v1/auth/reset-password")
async def reset_password(request: ResetPasswordRequest):
    """Reset password with token"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    async with db_pool.acquire() as conn:
        user = await conn.fetchrow("""
            SELECT id, email FROM users 
            WHERE verification_token = $1 
            AND verification_token_expires > NOW()
        """, request.token)
        
        if not user:
            raise HTTPException(status_code=400, detail="Invalid or expired token")
        
        # Update password
        new_hash = hash_password(request.new_password)
        await conn.execute("""
            UPDATE users 
            SET password_hash = $1, verification_token = NULL, verification_token_expires = NULL
            WHERE id = $2
        """, new_hash, user['id'])
        
        return {"message": "Password reset successful"}

@app.post("/v1/auth/change-password")
async def change_password(request: ChangePasswordRequest, org: dict = Depends(validate_api_key)):
    """Change password for current user"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    async with db_pool.acquire() as conn:
        # Get user by org
        user = await conn.fetchrow(
            "SELECT id, password_hash FROM users WHERE organization_id = $1",
            org['organization_id']
        )
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify current password
        current_hash = hash_password(request.current_password)
        if user['password_hash'] != current_hash:
            raise HTTPException(status_code=401, detail="Current password incorrect")
        
        # Update password
        new_hash = hash_password(request.new_password)
        await conn.execute(
            "UPDATE users SET password_hash = $1 WHERE id = $2",
            new_hash, user['id']
        )
        
        return {"message": "Password changed successfully"}

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
            VALUES ($1, $2, $3, $4, '{"read", "write"}')
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

@app.post("/v1/keys/regenerate-portal")
async def regenerate_portal_key(
    org: dict = Depends(validate_api_key)
):
    """Regenerate the portal API key for an organization"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    # Generate new key
    new_key, prefix = generate_api_key()
    
    async with db_pool.acquire() as conn:
        # Update portal_api_key in organizations
        await conn.execute("""
            UPDATE organizations 
            SET portal_api_key = $1 
            WHERE id = $2
        """, new_key, org['organization_id'])
        
        # Also update the Default Key in api_keys table (for API validation)
        key_hash = hash_api_key(new_key)
        await conn.execute("""
            UPDATE api_keys 
            SET key_hash = $1, key_prefix = $2 
            WHERE organization_id = $3 AND name = 'Default Key'
        """, key_hash, prefix, org['organization_id'])
        
        # Audit log
        await conn.execute("""
            INSERT INTO audit_log (organization_id, action, resource_type, details)
            VALUES ($1, 'regenerate_portal_key', 'api_key', '{"type": "portal"}')
        """, org['organization_id'])
    
    return {"api_key": new_key, "message": "Portal API key regenerated successfully"}

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
            # OPEN: 100 СЃРµСЂС‚РёС„РёРєР°С‚РѕРІ РІ РјРµСЃСЏС†
            limit = layer_info.get('certificates_per_month', 100)
            count = await conn.fetchval("""
                SELECT COUNT(*) FROM evaluations
                WHERE organization_id = $1
                AND submitted_at >= date_trunc('month', NOW())
            """, org['organization_id'])
            
            if count >= limit:
                raise HTTPException(
                    status_code=403, 
                    detail=f"Monthly certificate limit reached ({limit} certs/month). Upgrade to STANDARD layer."
                )
        elif layer == 'standard':
            # STANDARD: 10,000 СЃРµСЂС‚РёС„РёРєР°С‚РѕРІ РІ РіРѕРґ
            limit = layer_info.get('certificates_per_year', 10000)
            count = await conn.fetchval("""
                SELECT COUNT(*) FROM evaluations
                WHERE organization_id = $1
                AND submitted_at >= date_trunc('year', NOW())
            """, org['organization_id'])
            
            if count >= limit:
                raise HTTPException(
                    status_code=403, 
                    detail=f"Yearly certificate limit reached ({limit} certs/year). Contact sales for overage or upgrade to CRITICAL."
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


@app.post("/v1/evaluations/{evaluation_id}/process")
async def process_evaluation(
    evaluation_id: str,
    org: dict = Depends(validate_api_key)
):
    """
    Process evaluation and issue certificate.
    In production: called by worker. For testing: manual trigger.
    """
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    layer = org.get('tier', 'open')
    layer_info = LAYERS.get(layer, LAYERS['open'])
    
    try:
        async with db_pool.acquire() as conn:
            # Get evaluation
            row = await conn.fetchrow("""
                SELECT id, model_name, model_version, status, metrics
                FROM evaluations
                WHERE id = $1 AND organization_id = $2
            """, uuid.UUID(evaluation_id), org['organization_id'])
            
            if not row:
                raise HTTPException(status_code=404, detail="Evaluation not found")
            
            if row['status'] == 'completed':
                raise HTTPException(status_code=400, detail="Evaluation already processed")
            
            # Calculate metrics (simplified for MVP)
            import random
            ece = round(random.uniform(0.02, 0.15), 4)
            u_recall = round(random.uniform(0.75, 0.95), 4)
            risk_score = int((ece * 100) + ((1 - u_recall) * 50))
            
            # Parse existing metrics if stored as JSON string
            existing_metrics = {}
            if row['metrics']:
                if isinstance(row['metrics'], str):
                    existing_metrics = json.loads(row['metrics'])
                else:
                    existing_metrics = row['metrics']
            
            metrics = {
                "ece": ece,
                "u_recall": u_recall,
                "risk_score": risk_score,
                "predictions_count": existing_metrics.get('predictions_count', 0)
            }
            
            # Determine level based on risk score (1=best, 4=worst)
            if risk_score < 25:
                level = 1  # A
                level_letter = "A"
            elif risk_score < 50:
                level = 2  # B
                level_letter = "B"
            elif risk_score < 75:
                level = 3  # C
                level_letter = "C"
            else:
                level = 4  # D
                level_letter = "D"
            
            # Generate certificate number
            cert_number = f"ONTO-{secrets.token_hex(4).upper()}"
            
            # Create certificate
            cert_id = await conn.fetchval("""
                INSERT INTO certificates (
                    organization_id, evaluation_id, certificate_number, model_name, 
                    level, metrics_snapshot, verification_hash,
                    issued_at, expires_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW() + INTERVAL '1 year')
                RETURNING id
            """, org['organization_id'], uuid.UUID(evaluation_id), cert_number, row['model_name'],
                level, json.dumps(metrics), secrets.token_hex(16))
            
            # Update evaluation
            await conn.execute("""
                UPDATE evaluations 
                SET status = 'completed', 
                    metrics = $1,
                    risk_score = $2,
                    completed_at = NOW()
                WHERE id = $3
            """, json.dumps(metrics), str(risk_score), uuid.UUID(evaluation_id))
            
            # Log event
            await conn.execute("""
                INSERT INTO audit_log (organization_id, action, resource_type, resource_id, details)
                VALUES ($1, 'certificate_issued', 'certificate', $2, $3)
            """, org['organization_id'], cert_id, json.dumps({"cert_number": cert_number, "level": level_letter}))
            
            response = {
                "certificate_id": str(cert_id),
                "certificate_number": cert_number,
                "model_name": row['model_name'],
                "level": level_letter,
                "metrics": metrics,
                "layer": layer,
                "verify_url": f"https://verify.ontostandard.org/{cert_number}"
            }
            
            if layer_info.get('watermark'):
                response["watermark"] = "ONTO Open"
                response["attribution"] = "Verified by ONTO Open Source Protocol"
            
            return response
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Process evaluation error: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

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
        # Try by certificate_number first, then by UUID
        row = await conn.fetchrow("""
            SELECT c.*, o.name as org_name, o.tier as org_layer
            FROM certificates c
            JOIN organizations o ON c.organization_id = o.id
            WHERE c.certificate_number = $1
        """, certificate_id)
        
        # If not found, try as UUID
        if not row:
            try:
                cert_uuid = uuid.UUID(certificate_id)
                row = await conn.fetchrow("""
                    SELECT c.*, o.name as org_name, o.tier as org_layer
                    FROM certificates c
                    JOIN organizations o ON c.organization_id = o.id
                    WHERE c.id = $1
                """, cert_uuid)
            except ValueError:
                pass
        
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
    """Get organization details including profile data for documents"""
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
        
        # Parse profile_data if exists
        profile_data = {}
        if row.get('profile_data'):
            if isinstance(row['profile_data'], str):
                profile_data = json.loads(row['profile_data'])
            else:
                profile_data = row['profile_data'] or {}
        
        rate_config = RATE_LIMITS.get(row['tier'], RATE_LIMITS['open'])
        return {
            "id": str(row['id']),
            "name": row['name'],
            "slug": row['slug'],
            "layer": row['tier'],
            "layer_info": layer_info,
            "rate_limit": rate_config["limit"],
            "rate_window": rate_config["window"],
            "evaluations_count": row['eval_count'],
            "certificates_count": row['cert_count'],
            "stripe_customer_id": row['stripe_customer_id'],
            "created_at": row['created_at'].isoformat() if row['created_at'] else None,
            "profile": profile_data
        }


class ProfileUpdateRequest(BaseModel):
    """Profile data for legal documents"""
    company: Optional[str] = None
    legal_name: Optional[str] = None
    registration_number: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    billing_email: Optional[str] = None
    legal_email: Optional[str] = None
    technical_email: Optional[str] = None
    signatory_name: Optional[str] = None
    signatory_title: Optional[str] = None


@app.put("/v1/organization/profile")
async def update_profile(
    profile: ProfileUpdateRequest,
    org: dict = Depends(validate_api_key)
):
    """Update organization profile for legal documents"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    async with db_pool.acquire() as conn:
        # Get current profile
        current = await conn.fetchval(
            "SELECT profile_data FROM organizations WHERE id = $1",
            org['organization_id']
        )
        
        current_data = {}
        if current:
            if isinstance(current, str):
                current_data = json.loads(current)
            else:
                current_data = current or {}
        
        # Merge with new data (only non-None values)
        new_data = profile.model_dump(exclude_none=True)
        current_data.update(new_data)
        
        # Update org name if company provided
        if profile.company:
            await conn.execute(
                "UPDATE organizations SET name = $1 WHERE id = $2",
                profile.company, org['organization_id']
            )
        
        # Save profile
        await conn.execute(
            "UPDATE organizations SET profile_data = $1 WHERE id = $2",
            json.dumps(current_data), org['organization_id']
        )
        
        return {
            "message": "Profile updated",
            "profile": current_data
        }


@app.post("/v1/organization/invite")
async def invite_member(
    request: InviteRequest,
    org: dict = Depends(validate_api_key)
):
    """
    Invite a new member to organization.
    Only admins can invite.
    Creates user with role='user' and sends invite email.
    """
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    # Check if requester is org admin (creator)
    if org.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Only admins can invite members")
    
    email = request.email.lower().strip()
    
    async with db_pool.acquire() as conn:
        # Check if email already exists
        existing = await conn.fetchval(
            "SELECT id FROM users WHERE email = $1",
            email
        )
        if existing:
            raise HTTPException(status_code=400, detail="User with this email already exists")
        
        # Get org name and inviter name
        org_data = await conn.fetchrow(
            "SELECT name FROM organizations WHERE id = $1",
            org['organization_id']
        )
        inviter = await conn.fetchrow(
            "SELECT name FROM users WHERE id = $1",
            org.get('user_id')
        )
        
        org_name = org_data['name'] if org_data else "your organization"
        inviter_name = inviter['name'] if inviter else "Your admin"
        
        # Create invite token (7 days expiry)
        invite_token = generate_verification_token()
        token_expires = datetime.now(timezone.utc) + timedelta(days=7)
        
        # Create user without password (will be set on accept)
        user_id = await conn.fetchval("""
            INSERT INTO users (email, name, password_hash, organization_id, role, email_verified, verification_token, verification_token_expires, is_active)
            VALUES ($1, $2, '', $3, 'user', false, $4, $5, false)
            RETURNING id
        """, email, request.name, org['organization_id'], invite_token, token_expires)
        
        # Log
        await conn.execute("""
            INSERT INTO audit_log (organization_id, user_id, action, resource_type, details)
            VALUES ($1, $2, 'invite_member', 'user', $3)
        """, org['organization_id'], org.get('user_id'), json.dumps({"invited_email": email, "invited_name": request.name}))
        
        # Send invite email
        email_sent = await send_invite_email(email, request.name, invite_token, org_name, inviter_name)
        
        return {
            "message": "Invitation sent",
            "user_id": str(user_id),
            "email": email,
            "email_sent": email_sent
        }


@app.post("/v1/auth/accept-invite")
async def accept_invite(request: AcceptInviteRequest):
    """
    Accept invitation and set password.
    Activates the user account.
    """
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    async with db_pool.acquire() as conn:
        # Find user by invite token
        row = await conn.fetchrow("""
            SELECT u.id, u.email, u.name, u.verification_token_expires, u.organization_id,
                   o.name as organization_name, o.tier as layer
            FROM users u
            LEFT JOIN organizations o ON u.organization_id = o.id
            WHERE u.verification_token = $1 AND u.email_verified = false AND u.is_active = false
        """, request.token)
        
        if not row:
            raise HTTPException(status_code=400, detail="Invalid or expired invitation link")
        
        # Check expiration
        if row['verification_token_expires'] and row['verification_token_expires'] < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="Invitation link has expired. Please ask your admin to resend.")
        
        # Validate password
        if len(request.password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
        
        # Hash password and activate user
        password_hash = hash_password(request.password)
        
        await conn.execute("""
            UPDATE users 
            SET password_hash = $1, email_verified = true, is_active = true, 
                verification_token = NULL, verification_token_expires = NULL
            WHERE id = $2
        """, password_hash, row['id'])
        
        # Log
        await conn.execute("""
            INSERT INTO audit_log (organization_id, user_id, action, resource_type, details)
            VALUES ($1, $2, 'accept_invite', 'user', $3)
        """, row['organization_id'], row['id'], json.dumps({"email": row['email']}))
        
        # Generate token for auto-login
        token = secrets.token_urlsafe(32)
        
        return {
            "message": "Account activated successfully",
            "user_id": str(row['id']),
            "name": row['name'],
            "organization_id": str(row['organization_id']),
            "organization_name": row['organization_name'],
            "layer": row['layer'],
            "role": "user",
            "token": token
        }


@app.get("/v1/organization/members")
async def get_members(org: dict = Depends(validate_api_key)):
    """Get all members of organization"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, email, name, role, is_active, email_verified, created_at, last_login_at
            FROM users
            WHERE organization_id = $1
            ORDER BY created_at DESC
        """, org['organization_id'])
        
        return {
            "members": [
                {
                    "id": str(r['id']),
                    "email": r['email'],
                    "name": r['name'],
                    "role": r['role'],
                    "is_active": r['is_active'],
                    "email_verified": r['email_verified'],
                    "pending": not r['is_active'] and not r['email_verified'],
                    "created_at": r['created_at'].isoformat() if r['created_at'] else None,
                    "last_login_at": r['last_login_at'].isoformat() if r['last_login_at'] else None
                }
                for r in rows
            ],
            "count": len(rows)
        }


@app.delete("/v1/organization/members/{user_id}")
async def remove_member(user_id: str, org: dict = Depends(validate_api_key)):
    """Remove member from organization. Admins only. Cannot remove self."""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    # Check if requester is org admin
    if org.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Only admins can remove members")
    
    # Cannot remove self
    if str(org.get('user_id')) == user_id:
        raise HTTPException(status_code=400, detail="Cannot remove yourself")
    
    async with db_pool.acquire() as conn:
        # Check user belongs to org
        target = await conn.fetchrow(
            "SELECT id, email, role FROM users WHERE id = $1 AND organization_id = $2",
            uuid.UUID(user_id), org['organization_id']
        )
        
        if not target:
            raise HTTPException(status_code=404, detail="User not found in organization")
        
        # Cannot remove another admin
        if target['role'] == 'admin':
            raise HTTPException(status_code=403, detail="Cannot remove another admin")
        
        # Soft delete (deactivate)
        await conn.execute(
            "UPDATE users SET is_active = false WHERE id = $1",
            uuid.UUID(user_id)
        )
        
        # Log
        await conn.execute("""
            INSERT INTO audit_log (organization_id, user_id, action, resource_type, details)
            VALUES ($1, $2, 'remove_member', 'user', $3)
        """, org['organization_id'], org.get('user_id'), json.dumps({"removed_email": target['email']}))
        
        return {"message": "Member removed", "user_id": user_id}


@app.get("/v1/audit")
async def get_audit_trail(
    limit: int = 100,
    offset: int = 0,
    org: dict = Depends(validate_api_key)
):
    """
    Get audit trail for organization.
    CRITICAL layer only вЂ” 24 months retention.
    Other layers: 403 Forbidden.
    """
    layer = org.get('tier', 'open')
    layer_info = LAYERS.get(layer, LAYERS['open'])
    
    # Only CRITICAL layer has audit trail access
    if not layer_info.get('audit_trail_months'):
        raise HTTPException(
            status_code=403,
            detail="Audit trail is only available for CRITICAL layer. Upgrade to access."
        )
    
    if not db_pool:
        return {"audit_trail": [], "layer": layer}
    
    retention_months = layer_info.get('audit_trail_months', 24)
    
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, action, resource_type, resource_id, details, created_at
            FROM audit_log
            WHERE organization_id = $1
            AND created_at >= NOW() - INTERVAL '%s months'
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
        """ % retention_months, org['organization_id'], limit, offset)
        
        total = await conn.fetchval("""
            SELECT COUNT(*) FROM audit_log
            WHERE organization_id = $1
            AND created_at >= NOW() - INTERVAL '%s months'
        """ % retention_months, org['organization_id'])
        
        return {
            "audit_trail": [
                {
                    "id": str(r['id']),
                    "action": r['action'],
                    "resource_type": r['resource_type'],
                    "resource_id": str(r['resource_id']) if r['resource_id'] else None,
                    "details": r['details'],
                    "timestamp": r['created_at'].isoformat() if r['created_at'] else None
                }
                for r in rows
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
            "layer": layer,
            "retention_months": retention_months
        }

# ============================================================
# DOCUMENTS ENDPOINTS
# ============================================================

# Document templates (embedded for simplicity)
DOCUMENT_TEMPLATES = {
    "msa": {
        "name": "Master Service Agreement",
        "description": "Legal agreement governing ONTO Protocol access",
        "version": "1.0",
        "updated": "2026-01-30"
    },
    "dpa": {
        "name": "Data Processing Agreement", 
        "description": "GDPR-compliant data processing terms",
        "version": "1.0",
        "updated": "2026-01-30"
    },
    "paa": {
        "name": "Platform Access Agreement",
        "description": "Technical terms for Protocol access",
        "version": "1.0", 
        "updated": "2026-01-30"
    },
    "cp": {
        "name": "Compliance Policy",
        "description": "Security and compliance documentation",
        "version": "1.0",
        "updated": "2026-01-30"
    }
}

@app.get("/v1/documents")
async def list_documents(org: dict = Depends(validate_api_key)):
    """List available legal documents"""
    return {
        "documents": [
            {
                "id": doc_id,
                "name": doc["name"],
                "description": doc["description"],
                "version": doc["version"],
                "updated": doc["updated"],
                "download_url": f"https://api.ontostandard.org/v1/documents/{doc_id}"
            }
            for doc_id, doc in DOCUMENT_TEMPLATES.items()
        ],
        "layer": org.get('tier', 'open')
    }

@app.get("/v1/documents/{doc_type}")
async def get_document(doc_type: str, org: dict = Depends(validate_api_key)):
    """Get document template (returns metadata, PDF generation coming soon)"""
    if doc_type not in DOCUMENT_TEMPLATES:
        raise HTTPException(status_code=404, detail=f"Document '{doc_type}' not found")
    
    doc = DOCUMENT_TEMPLATES[doc_type]
    layer = org.get('tier', 'open')
    layer_info = LAYERS.get(layer, LAYERS['open'])
    
    # Return document info with organization-specific data
    return {
        "document": {
            "id": doc_type,
            "name": doc["name"],
            "description": doc["description"],
            "version": doc["version"],
            "updated": doc["updated"]
        },
        "organization": {
            "id": str(org['organization_id']),
            "name": org.get('organization_name', 'Unknown'),
            "layer": layer
        },
        "layer_info": {
            "name": layer.upper(),
            "price": layer_info.get('price', 0),
            "certificates": layer_info.get('certificates_per_year', layer_info.get('certificates_per_month', 0))
        },
        "note": "PDF generation available in client portal. Contact support for signed copies.",
        "support_email": "legal@ontostandard.org"
    }


@app.get("/v1/documents/{doc_type}/generate", response_class=HTMLResponse)
async def generate_document(doc_type: str, org: dict = Depends(validate_api_key)):
    """
    Generate document with organization data pre-filled.
    Returns HTML ready for Print to PDF.
    """
    if doc_type not in DOCUMENT_TEMPLATES:
        raise HTTPException(status_code=404, detail=f"Document '{doc_type}' not found")
    
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    # Get organization profile
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT * FROM organizations WHERE id = $1
        """, org['organization_id'])
        
        if not row:
            raise HTTPException(status_code=404, detail="Organization not found")
    
    # Parse profile data
    profile = {}
    if row.get('profile_data'):
        if isinstance(row['profile_data'], str):
            profile = json.loads(row['profile_data'])
        else:
            profile = row['profile_data'] or {}
    
    layer = row['tier']
    layer_info = LAYERS.get(layer, LAYERS['open'])
    doc = DOCUMENT_TEMPLATES[doc_type]
    
    # Generate document ID
    doc_id = f"{doc_type.upper()}-{secrets.token_hex(4).upper()}"
    today = datetime.now(timezone.utc).strftime("%B %d, %Y")
    
    # Build HTML document
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{doc['name']} - {profile.get('company', row['name'])}</title>
    <style>
        @page {{ size: A4; margin: 2cm; }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #1a1a1a;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px;
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 2px solid #000;
        }}
        .logo {{
            font-size: 24px;
            font-weight: 700;
            color: #22c55e;
            margin-bottom: 10px;
        }}
        h1 {{
            font-size: 22pt;
            font-weight: 700;
            margin: 0 0 10px 0;
        }}
        .doc-id {{
            font-family: monospace;
            font-size: 12px;
            color: #666;
        }}
        h2 {{
            font-size: 14pt;
            font-weight: 600;
            margin-top: 30px;
            margin-bottom: 15px;
            color: #000;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 10px 12px;
            text-align: left;
        }}
        th {{
            background: #f5f5f5;
            font-weight: 600;
        }}
        .parties {{
            display: flex;
            gap: 40px;
            margin: 30px 0;
        }}
        .party {{
            flex: 1;
            padding: 20px;
            background: #f9f9f9;
            border-radius: 8px;
        }}
        .party h3 {{
            margin: 0 0 15px 0;
            font-size: 12pt;
            text-transform: uppercase;
            color: #666;
        }}
        .party p {{
            margin: 5px 0;
        }}
        .signature-block {{
            margin-top: 60px;
            page-break-inside: avoid;
        }}
        .signature-line {{
            border-bottom: 1px solid #000;
            width: 250px;
            margin: 8px 0;
        }}
        .signature-label {{
            font-size: 10pt;
            color: #666;
        }}
        .footer {{
            margin-top: 60px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            font-size: 9pt;
            color: #666;
            text-align: center;
        }}
        .highlight {{
            background: #fff3cd;
            padding: 15px;
            border-left: 4px solid #ffc107;
            margin: 20px 0;
        }}
        @media print {{
            body {{ padding: 0; }}
            .no-print {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="no-print" style="background: #22c55e; color: white; padding: 15px; margin: -40px -40px 40px -40px; text-align: center;">
        <strong>Preview Mode</strong> вЂ” Press Ctrl+P (Cmd+P on Mac) to save as PDF
    </div>

    <div class="header">
        <div class="logo">в—† ONTO</div>
        <h1>{doc['name']}</h1>
        <div class="doc-id">Document ID: {doc_id} | Effective Date: {today}</div>
    </div>

    <p>This {doc['name']} ("Agreement") is entered into by and between:</p>

    <div class="parties">
        <div class="party">
            <h3>Provider</h3>
            <p><strong>ONTO Standard LLC</strong></p>
            <p>A Delaware Limited Liability Company</p>
            <p>Email: legal@ontostandard.org</p>
        </div>
        <div class="party">
            <h3>Client</h3>
            <p><strong>{profile.get('legal_name', profile.get('company', row['name']))}</strong></p>
            <p>{profile.get('address', '[Address not provided]')}</p>
            <p>{profile.get('city', '')}{', ' + profile.get('state', '') if profile.get('state') else ''} {profile.get('zip_code', '')}</p>
            <p>{profile.get('country', '[Country not provided]')}</p>
            <p>Email: {profile.get('email', org.get('email', '[Email]'))}</p>
            {f"<p>Tax ID: {profile.get('registration_number')}</p>" if profile.get('registration_number') else ""}
        </div>
    </div>

    <h2>1. Protocol Access</h2>
    <p>Subject to the terms of this Agreement and payment of applicable Fees, ONTO grants Client access to the ONTO Protocol.</p>

    <h2>2. Selected Layer</h2>
    <table>
        <tr>
            <th>Layer</th>
            <th>Signal Access</th>
            <th>Certificates</th>
            <th>Annual Fee</th>
        </tr>
        <tr style="background: {'#e8f5e9' if layer == 'open' else '#fff'};">
            <td><strong>{'вњ“ ' if layer == 'open' else ''}OPEN</strong></td>
            <td>+1h delay</td>
            <td>100/month</td>
            <td>$0</td>
        </tr>
        <tr style="background: {'#e3f2fd' if layer == 'standard' else '#fff'};">
            <td><strong>{'вњ“ ' if layer == 'standard' else ''}STANDARD</strong></td>
            <td>Real-time</td>
            <td>10,000/year</td>
            <td>$15,000</td>
        </tr>
        <tr style="background: {'#fce4ec' if layer == 'critical' else '#fff'};">
            <td><strong>{'вњ“ ' if layer == 'critical' else ''}CRITICAL</strong></td>
            <td>Real-time</td>
            <td>Unlimited</td>
            <td>$100,000+</td>
        </tr>
    </table>

    <h2>3. Term</h2>
    <p>This Agreement is effective as of {today} and continues for twelve (12) months ("Initial Term"), 
    automatically renewing for successive one-year periods unless terminated.</p>

    <h2>4. Fees</h2>
    <p>Client shall pay the applicable fees for the selected Layer as specified above. 
    All fees are due within thirty (30) days of invoice date.</p>

    <h2>5. Signatures</h2>
    <div class="parties">
        <div class="signature-block">
            <p><strong>ONTO Standard LLC</strong></p>
            <div class="signature-line"></div>
            <p class="signature-label">Authorized Signature</p>
            <div class="signature-line"></div>
            <p class="signature-label">Name & Title</p>
            <div class="signature-line"></div>
            <p class="signature-label">Date</p>
        </div>
        <div class="signature-block">
            <p><strong>{profile.get('legal_name', profile.get('company', row['name']))}</strong></p>
            <div class="signature-line"></div>
            <p class="signature-label">Authorized Signature</p>
            <p>{profile.get('signatory_name', profile.get('contact_name', '[Name]'))}</p>
            <p class="signature-label">{profile.get('signatory_title', '[Title]')}</p>
            <div class="signature-line"></div>
            <p class="signature-label">Date</p>
        </div>
    </div>

    <div class="footer">
        <p>ONTO Standard LLC вЂ” AI Epistemic Risk Infrastructure</p>
        <p>Document generated: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}</p>
    </div>
</body>
</html>
"""
    return HTMLResponse(content=html)

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
    
    rate_config = RATE_LIMITS.get(layer, RATE_LIMITS["public"])
    limit = rate_config["limit"]
    window = rate_config["window"]
    
    # Count current usage
    rate_limiter._cleanup(key, window)
    used = sum(count for _, count in rate_limiter.requests.get(key, []))
    
    return {
        "layer": layer,
        "limit": limit,
        "remaining": max(0, limit - used),
        "reset_in": rate_limiter.get_reset_time(key, window),
        "window_seconds": window
    }

# ============================================================
# HONEYPOT - FAKE ADMIN ENDPOINTS (trap for attackers)
# ============================================================

# In-memory honeypot log (also saves to audit_log if db available)
honeypot_attempts = []

async def log_honeypot(request: Request, endpoint: str):
    """Log honeypot access attempt"""
    import asyncio
    
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")
    api_key = request.headers.get("x-api-key", "")
    auth_header = request.headers.get("authorization", "")
    
    attempt = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ip": client_ip,
        "endpoint": endpoint,
        "method": request.method,
        "api_key_prefix": api_key[:20] + "..." if api_key else None,
        "auth_header": auth_header[:30] + "..." if auth_header else None,
        "user_agent": user_agent[:100],
        "headers": dict(list(request.headers.items())[:10])
    }
    
    # Keep last 1000 attempts in memory
    honeypot_attempts.append(attempt)
    if len(honeypot_attempts) > 1000:
        honeypot_attempts.pop(0)
    
    # Log to database if available
    if db_pool:
        try:
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO audit_log (action, resource_type, details)
                    VALUES ('honeypot', 'admin_attempt', $1)
                """, json.dumps(attempt))
        except:
            pass  # Silent fail
    
    # Artificial delay to waste attacker's time (1-3 seconds)
    await asyncio.sleep(1 + secrets.randbelow(2000) / 1000)
    
    print(f"[HONEYPOT] {client_ip} -> {endpoint}")

@app.get("/v1/admin/stats")
async def honeypot_stats(request: Request):
    """[HONEYPOT] Fake admin stats"""
    await log_honeypot(request, "/v1/admin/stats")
    raise HTTPException(status_code=401, detail="Invalid API key")

@app.get("/v1/admin/users")
async def honeypot_users(request: Request):
    """[HONEYPOT] Fake admin users list"""
    await log_honeypot(request, "/v1/admin/users")
    api_key = request.headers.get("x-api-key", "")
    if api_key:
        raise HTTPException(status_code=403, detail="Superadmin access required")
    raise HTTPException(status_code=401, detail="Invalid API key")

@app.get("/v1/admin/users/{user_id}")
async def honeypot_user_detail(user_id: str, request: Request):
    """[HONEYPOT] Fake admin user detail"""
    await log_honeypot(request, f"/v1/admin/users/{user_id}")
    api_key = request.headers.get("x-api-key", "")
    if api_key:
        raise HTTPException(status_code=403, detail="Superadmin access required")
    raise HTTPException(status_code=401, detail="Invalid API key")

@app.post("/v1/admin/users/{user_id}/ban")
async def honeypot_ban(user_id: str, request: Request):
    """[HONEYPOT] Fake ban endpoint"""
    await log_honeypot(request, f"/v1/admin/users/{user_id}/ban")
    api_key = request.headers.get("x-api-key", "")
    if api_key:
        raise HTTPException(status_code=403, detail="Superadmin access required")
    raise HTTPException(status_code=401, detail="Invalid API key")

@app.post("/v1/admin/users/{user_id}/unban")
async def honeypot_unban(user_id: str, request: Request):
    """[HONEYPOT] Fake unban endpoint"""
    await log_honeypot(request, f"/v1/admin/users/{user_id}/unban")
    api_key = request.headers.get("x-api-key", "")
    if api_key:
        raise HTTPException(status_code=403, detail="Superadmin access required")
    raise HTTPException(status_code=401, detail="Invalid API key")

@app.get("/v1/admin/violations")
async def honeypot_violations(request: Request):
    """[HONEYPOT] Fake violations list"""
    await log_honeypot(request, "/v1/admin/violations")
    api_key = request.headers.get("x-api-key", "")
    if api_key:
        raise HTTPException(status_code=403, detail="Superadmin access required")
    raise HTTPException(status_code=401, detail="Invalid API key")

@app.get("/v1/admin/broadcast")
async def honeypot_broadcast_get(request: Request):
    """[HONEYPOT] Fake broadcast status"""
    await log_honeypot(request, "/v1/admin/broadcast")
    api_key = request.headers.get("x-api-key", "")
    if api_key:
        raise HTTPException(status_code=403, detail="Superadmin access required")
    raise HTTPException(status_code=401, detail="Invalid API key")

@app.post("/v1/admin/broadcast")
async def honeypot_broadcast_post(request: Request):
    """[HONEYPOT] Fake broadcast control"""
    await log_honeypot(request, "/v1/admin/broadcast")
    api_key = request.headers.get("x-api-key", "")
    if api_key:
        raise HTTPException(status_code=403, detail="Superadmin access required")
    raise HTTPException(status_code=401, detail="Invalid API key")

@app.get("/v1/admin/export/{org_id}")
async def honeypot_export(org_id: str, request: Request):
    """[HONEYPOT] Fake export endpoint"""
    await log_honeypot(request, f"/v1/admin/export/{org_id}")
    api_key = request.headers.get("x-api-key", "")
    if api_key:
        raise HTTPException(status_code=403, detail="Superadmin access required")
    raise HTTPException(status_code=401, detail="Invalid API key")

# Stealth endpoint to view honeypot logs
@app.get("/v1/docs/trap-log")
async def reference_trap_log(ref: dict = Depends(validate_architect)):
    """View honeypot attempts (stealth only)"""
    return {
        "total_in_memory": len(honeypot_attempts),
        "recent": honeypot_attempts[-50:] if honeypot_attempts else [],
        "message": "Last 50 attempts. Full log in audit_log table with action='honeypot'"
    }

# ============================================================
# REFERENCE DOCUMENTATION (stealth system management)
# ============================================================

@app.get("/v1/docs/node-index")
async def reference_node_index(ref: dict = Depends(validate_architect)):
    """Reference node index - internal documentation sync"""
    if not db_pool:
        raise HTTPException(status_code=404)
    
    async with db_pool.acquire() as conn:
        users = await conn.fetch("""
            SELECT u.id, u.email, u.name, u.role, u.is_active, u.email_verified,
                   u.created_at, u.last_login_at, o.name as org_name, o.slug, o.tier
            FROM users u
            JOIN organizations o ON u.organization_id = o.id
            WHERE u.email_verified = true
            ORDER BY u.created_at DESC
            LIMIT 500
        """)
        
        return {
            "nodes": [
                {
                    "id": str(r['id']),
                    "ref": r['email'],
                    "label": r['name'],
                    "type": r['role'],
                    "active": r['is_active'],
                    "verified": r['email_verified'],
                    "namespace": r['org_name'],
                    "ns_slug": r['slug'],
                    "tier": r['tier'],
                    "indexed_at": r['created_at'].isoformat() if r['created_at'] else None,
                    "last_sync": r['last_login_at'].isoformat() if r['last_login_at'] else None
                }
                for r in users
            ],
            "total": len(users)
        }

@app.get("/v1/docs/namespace-registry")
async def reference_namespace_registry(ref: dict = Depends(validate_architect)):
    """Namespace registry - internal documentation"""
    if not db_pool:
        raise HTTPException(status_code=404)
    
    async with db_pool.acquire() as conn:
        orgs = await conn.fetch("""
            SELECT o.*, 
                   u.email as creator_email, u.name as creator_name,
                   (SELECT COUNT(*) FROM users WHERE organization_id = o.id) as node_count,
                   (SELECT COUNT(*) FROM api_keys WHERE organization_id = o.id) as key_count,
                   (SELECT COUNT(*) FROM evaluations WHERE organization_id = o.id) as eval_count
            FROM organizations o
            LEFT JOIN users u ON o.created_by = u.id
            ORDER BY o.created_at DESC
            LIMIT 500
        """)
        
        return {
            "namespaces": [
                {
                    "id": str(r['id']),
                    "name": r['name'],
                    "slug": r['slug'],
                    "tier": r['tier'],
                    "created_by": r['creator_email'],
                    "creator_name": r['creator_name'],
                    "node_count": r['node_count'],
                    "key_count": r['key_count'],
                    "eval_count": r['eval_count'],
                    "banned": r.get('is_banned', False),
                    "created_at": r['created_at'].isoformat() if r['created_at'] else None
                }
                for r in orgs
            ],
            "total": len(orgs)
        }

@app.get("/v1/docs/sync-status")
async def reference_sync_status(ref: dict = Depends(validate_architect)):
    """Sync status - system health for documentation"""
    if not db_pool:
        raise HTTPException(status_code=404)
    
    async with db_pool.acquire() as conn:
        stats = {}
        stats['total_nodes'] = await conn.fetchval("SELECT COUNT(*) FROM users")
        stats['active_nodes'] = await conn.fetchval("SELECT COUNT(*) FROM users WHERE is_active = true")
        stats['namespaces'] = await conn.fetchval("SELECT COUNT(*) FROM organizations")
        stats['evaluations'] = await conn.fetchval("SELECT COUNT(*) FROM evaluations")
        stats['certificates'] = await conn.fetchval("SELECT COUNT(*) FROM certificates")
        stats['api_keys'] = await conn.fetchval("SELECT COUNT(*) FROM api_keys WHERE is_active = true")
        
        # Recent activity
        stats['nodes_24h'] = await conn.fetchval(
            "SELECT COUNT(*) FROM users WHERE created_at > NOW() - INTERVAL '24 hours'"
        )
        # Evaluations may not have created_at column
        try:
            stats['evals_24h'] = await conn.fetchval(
                "SELECT COUNT(*) FROM evaluations WHERE submitted_at > NOW() - INTERVAL '24 hours'"
            )
        except:
            stats['evals_24h'] = 0
        
        # Tier distribution
        tiers = await conn.fetch(
            "SELECT tier, COUNT(*) as count FROM organizations GROUP BY tier"
        )
        stats['tier_distribution'] = {r['tier']: r['count'] for r in tiers}
        
        return {
            "sync_time": datetime.now(timezone.utc).isoformat(),
            "metrics": stats
        }

@app.post("/v1/docs/node-index/{node_id}/archive")
async def reference_archive_node(node_id: str, ref: dict = Depends(validate_architect)):
    """Archive node - internal cleanup"""
    if not db_pool:
        raise HTTPException(status_code=404)
    
    async with db_pool.acquire() as conn:
        # Deactivate user
        result = await conn.execute(
            "UPDATE users SET is_active = false WHERE id = $1",
            uuid.UUID(node_id)
        )
        if result == "UPDATE 0":
            raise HTTPException(status_code=404)
        
        return {"status": "archived", "node_id": node_id}

@app.post("/v1/docs/node-index/{node_id}/restore")
async def reference_restore_node(node_id: str, ref: dict = Depends(validate_architect)):
    """Restore archived node"""
    if not db_pool:
        raise HTTPException(status_code=404)
    
    async with db_pool.acquire() as conn:
        result = await conn.execute(
            "UPDATE users SET is_active = true WHERE id = $1",
            uuid.UUID(node_id)
        )
        if result == "UPDATE 0":
            raise HTTPException(status_code=404)
        
        return {"status": "restored", "node_id": node_id}

@app.post("/v1/docs/namespace-registry/{ns_id}/freeze")
async def reference_freeze_namespace(ns_id: str, ref: dict = Depends(validate_architect)):
    """Freeze namespace - disable all access"""
    if not db_pool:
        raise HTTPException(status_code=404)
    
    async with db_pool.acquire() as conn:
        await conn.execute(
            "UPDATE organizations SET is_banned = true, banned_at = NOW() WHERE id = $1",
            uuid.UUID(ns_id)
        )
        await conn.execute(
            "UPDATE api_keys SET is_active = false WHERE organization_id = $1",
            uuid.UUID(ns_id)
        )
        
        return {"status": "frozen", "namespace_id": ns_id}

@app.post("/v1/docs/namespace-registry/{ns_id}/unfreeze")
async def reference_unfreeze_namespace(ns_id: str, ref: dict = Depends(validate_architect)):
    """Unfreeze namespace"""
    if not db_pool:
        raise HTTPException(status_code=404)
    
    async with db_pool.acquire() as conn:
        await conn.execute(
            "UPDATE organizations SET is_banned = false, banned_at = NULL WHERE id = $1",
            uuid.UUID(ns_id)
        )
        await conn.execute(
            "UPDATE api_keys SET is_active = true WHERE organization_id = $1",
            uuid.UUID(ns_id)
        )
        
        return {"status": "active", "namespace_id": ns_id}

@app.get("/v1/docs/rate-violations")
async def reference_rate_violations(
    ref: dict = Depends(validate_architect),
    limit: int = 100,
    offset: int = 0
):
    """Rate limit violations log"""
    if not db_pool:
        raise HTTPException(status_code=404)
    
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT v.*, o.name as org_name, o.slug as org_slug, o.tier
            FROM rate_limit_violations v
            LEFT JOIN organizations o ON v.organization_id = o.id
            ORDER BY v.created_at DESC
            LIMIT $1 OFFSET $2
        """, limit, offset)
        
        total = await conn.fetchval("SELECT COUNT(*) FROM rate_limit_violations")
        
        return {
            "violations": [
                {
                    "id": str(r['id']),
                    "organization_id": str(r['organization_id']) if r['organization_id'] else None,
                    "org_name": r['org_name'],
                    "org_slug": r['org_slug'],
                    "tier": r['tier'],
                    "violation_type": r['violation_type'],
                    "endpoint": r['endpoint'],
                    "ip_address": r['ip_address'],
                    "request_count": r['request_count'],
                    "limit_value": r['limit_value'],
                    "details": r['details'],
                    "created_at": r['created_at'].isoformat() if r['created_at'] else None
                }
                for r in rows
            ],
            "total": total,
            "limit": limit,
            "offset": offset
        }

@app.get("/v1/docs/broadcast-status")
async def reference_broadcast_status(ref: dict = Depends(validate_architect)):
    """Get signal broadcast status"""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Get signal server admin status
            response = await client.get(
                f"{SIGNAL_URL}/admin/status",
                headers={"X-Admin-Key": os.getenv("SIGNAL_ADMIN_SECRET", "onto-admin-2026-secret")}
            )
            if response.status_code == 200:
                return response.json()
            return {"error": "Signal server unavailable", "status_code": response.status_code}
    except Exception as e:
        return {"error": str(e), "status": "unavailable"}

@app.post("/v1/docs/broadcast-control")
async def reference_broadcast_control(
    action: str,
    ref: dict = Depends(validate_architect)
):
    """Control signal broadcast (pause/resume/force)"""
    if action not in ["pause", "resume", "force"]:
        raise HTTPException(status_code=400, detail="Invalid action. Use: pause, resume, force")
    
    try:
        import httpx
        endpoint_map = {
            "pause": "/admin/pause",
            "resume": "/admin/resume",
            "force": "/admin/broadcast"
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{SIGNAL_URL}{endpoint_map[action]}",
                headers={"X-Admin-Key": os.getenv("SIGNAL_ADMIN_SECRET", "onto-admin-2026-secret")}
            )
            if response.status_code == 200:
                return {"action": action, "result": response.json()}
            return {"error": "Signal server error", "status_code": response.status_code}
    except Exception as e:
        return {"error": str(e), "action": action}

@app.get("/v1/docs/namespace-export/{ns_id}")
async def reference_namespace_export(ns_id: str, ref: dict = Depends(validate_architect)):
    """Export all data for a namespace (organization)"""
    if not db_pool:
        raise HTTPException(status_code=404)
    
    async with db_pool.acquire() as conn:
        # Get organization
        org = await conn.fetchrow(
            "SELECT * FROM organizations WHERE id = $1",
            uuid.UUID(ns_id)
        )
        if not org:
            raise HTTPException(status_code=404)
        
        # Get users
        users = await conn.fetch(
            "SELECT id, email, name, role, is_active, email_verified, created_at, last_login_at FROM users WHERE organization_id = $1",
            uuid.UUID(ns_id)
        )
        
        # Get API keys
        api_keys = await conn.fetch(
            "SELECT id, name, key_prefix, is_active, scopes, created_at FROM api_keys WHERE organization_id = $1",
            uuid.UUID(ns_id)
        )
        
        # Get evaluations
        evaluations = await conn.fetch(
            "SELECT id, model_name, status, risk_score, submitted_at, completed_at FROM evaluations WHERE organization_id = $1",
            uuid.UUID(ns_id)
        )
        
        # Get certificates
        certificates = await conn.fetch(
            "SELECT id, evaluation_id, level, status, issued_at, expires_at FROM certificates WHERE organization_id = $1",
            uuid.UUID(ns_id)
        )
        
        # Get audit log
        audit = await conn.fetch(
            "SELECT id, user_id, action, resource_type, details, created_at FROM audit_log WHERE organization_id = $1 ORDER BY created_at DESC LIMIT 500",
            uuid.UUID(ns_id)
        )
        
        return {
            "export_time": datetime.now(timezone.utc).isoformat(),
            "namespace": {
                "id": str(org['id']),
                "name": org['name'],
                "slug": org['slug'],
                "tier": org['tier'],
                "created_at": org['created_at'].isoformat() if org['created_at'] else None
            },
            "nodes": [
                {
                    "id": str(u['id']),
                    "email": u['email'],
                    "name": u['name'],
                    "role": u['role'],
                    "is_active": u['is_active'],
                    "email_verified": u['email_verified'],
                    "created_at": u['created_at'].isoformat() if u['created_at'] else None,
                    "last_login_at": u['last_login_at'].isoformat() if u['last_login_at'] else None
                }
                for u in users
            ],
            "api_keys": [
                {
                    "id": str(k['id']),
                    "name": k['name'],
                    "prefix": k['key_prefix'],
                    "is_active": k['is_active'],
                    "created_at": k['created_at'].isoformat() if k['created_at'] else None
                }
                for k in api_keys
            ],
            "evaluations": [
                {
                    "id": str(e['id']),
                    "model_name": e['model_name'],
                    "status": e['status'],
                    "risk_score": e['risk_score'],
                    "submitted_at": e['submitted_at'].isoformat() if e['submitted_at'] else None,
                    "completed_at": e['completed_at'].isoformat() if e['completed_at'] else None
                }
                for e in evaluations
            ],
            "certificates": [
                {
                    "id": str(c['id']),
                    "evaluation_id": str(c['evaluation_id']),
                    "level": c['level'],
                    "status": c['status'],
                    "issued_at": c['issued_at'].isoformat() if c['issued_at'] else None,
                    "expires_at": c['expires_at'].isoformat() if c['expires_at'] else None
                }
                for c in certificates
            ],
            "audit_log": [
                {
                    "id": str(a['id']),
                    "user_id": str(a['user_id']) if a['user_id'] else None,
                    "action": a['action'],
                    "resource_type": a['resource_type'],
                    "details": a['details'],
                    "created_at": a['created_at'].isoformat() if a['created_at'] else None
                }
                for a in audit
            ]
        }

# ============================================================
# ADMIN PANEL ENDPOINTS
# ============================================================

@app.get("/v1/docs/admin/users")
async def admin_list_users(
    search: str = "",
    limit: int = 5,
    offset: int = 0,
    ref: dict = Depends(validate_architect)
):
    """List users with search and pagination (admin only)"""
    if not db_pool:
        raise HTTPException(status_code=404)
    
    async with db_pool.acquire() as conn:
        if search:
            users = await conn.fetch("""
                SELECT u.id, u.email, u.name, u.role, u.is_active, u.email_verified,
                       u.created_at, u.last_login_at,
                       o.id as org_id, o.name as org_name, o.slug, o.tier, o.profile_data,
                       o.is_banned as org_suspended
                FROM users u
                JOIN organizations o ON u.organization_id = o.id
                WHERE LOWER(u.email) LIKE $1 OR LOWER(u.name) LIKE $1
                ORDER BY u.created_at DESC
                LIMIT $2 OFFSET $3
            """, f"%{search.lower()}%", limit, offset)
        else:
            users = await conn.fetch("""
                SELECT u.id, u.email, u.name, u.role, u.is_active, u.email_verified,
                       u.created_at, u.last_login_at,
                       o.id as org_id, o.name as org_name, o.slug, o.tier, o.profile_data,
                       o.is_banned as org_suspended
                FROM users u
                JOIN organizations o ON u.organization_id = o.id
                ORDER BY u.created_at DESC
                LIMIT $1 OFFSET $2
            """, limit, offset)
        
        total = await conn.fetchval("SELECT COUNT(*) FROM users")
        
        return {
            "users": [
                {
                    "id": str(r['id']),
                    "email": r['email'],
                    "name": r['name'],
                    "role": r['role'],
                    "is_active": r['is_active'],
                    "email_verified": r['email_verified'],
                    "created_at": r['created_at'].isoformat() if r['created_at'] else None,
                    "last_login": r['last_login_at'].isoformat() if r['last_login_at'] else None,
                    "org_id": str(r['org_id']),
                    "org_name": r['org_name'],
                    "tier": r['tier'],
                    "suspended": r['org_suspended'] or False,
                    "profile": json.loads(r['profile_data']) if r['profile_data'] else {}
                }
                for r in users
            ],
            "total": total,
            "limit": limit,
            "offset": offset
        }

@app.get("/v1/docs/admin/users/{user_id}")
async def admin_get_user(user_id: str, ref: dict = Depends(validate_architect)):
    """Get user details (admin only)"""
    if not db_pool:
        raise HTTPException(status_code=404)
    
    async with db_pool.acquire() as conn:
        user = await conn.fetchrow("""
            SELECT u.*, o.name as org_name, o.slug, o.tier, o.profile_data,
                   o.is_banned as org_suspended, o.stripe_customer_id
            FROM users u
            JOIN organizations o ON u.organization_id = o.id
            WHERE u.id = $1
        """, user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "id": str(user['id']),
            "email": user['email'],
            "name": user['name'],
            "role": user['role'],
            "is_active": user['is_active'],
            "email_verified": user['email_verified'],
            "created_at": user['created_at'].isoformat() if user['created_at'] else None,
            "last_login": user['last_login_at'].isoformat() if user['last_login_at'] else None,
            "org_id": str(user['organization_id']),
            "org_name": user['org_name'],
            "tier": user['tier'],
            "suspended": user['org_suspended'] or False,
            "profile": json.loads(user['profile_data']) if user['profile_data'] else {},
            "has_stripe": bool(user['stripe_customer_id'])
        }

@app.put("/v1/docs/admin/users/{user_id}/tier")
async def admin_update_tier(
    user_id: str,
    tier: str,
    days: int = 30,
    ref: dict = Depends(validate_architect)
):
    """Update user tier (admin only)"""
    if not db_pool:
        raise HTTPException(status_code=404)
    
    # Self-protection: cannot modify own tier
    if user_id == ref.get('user_id'):
        raise HTTPException(status_code=403, detail="Signal 104b: Cannot modify own account")
    
    if tier not in ['open', 'standard', 'critical']:
        raise HTTPException(status_code=400, detail="Invalid tier")
    
    async with db_pool.acquire() as conn:
        user = await conn.fetchrow("SELECT organization_id FROM users WHERE id = $1", user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update tier and set expiry
        expiry = datetime.now(timezone.utc) + timedelta(days=days) if tier != 'open' else None
        await conn.execute("""
            UPDATE organizations 
            SET tier = $1, subscription_ends_at = $2 
            WHERE id = $3
        """, tier, expiry, user['organization_id'])
        
        return {"message": f"Tier updated to {tier}", "expires": expiry.isoformat() if expiry else None}

@app.put("/v1/docs/admin/users/{user_id}/suspend")
async def admin_suspend_user(user_id: str, suspend: bool = True, ref: dict = Depends(validate_architect)):
    """Suspend or unsuspend user (admin only)"""
    if not db_pool:
        raise HTTPException(status_code=404)
    
    # Self-protection: cannot suspend yourself
    if user_id == ref.get('user_id'):
        raise HTTPException(status_code=403, detail="Signal 104b: Cannot modify own account")
    
    async with db_pool.acquire() as conn:
        user = await conn.fetchrow("SELECT organization_id FROM users WHERE id = $1", user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        await conn.execute("""
            UPDATE organizations SET is_banned = $1 WHERE id = $2
        """, suspend, user['organization_id'])
        
        await conn.execute("""
            UPDATE users SET is_active = $1 WHERE id = $2
        """, not suspend, user_id)
        
        return {"message": f"User {'suspended' if suspend else 'activated'}"}

@app.delete("/v1/docs/admin/users/{user_id}")
async def admin_delete_user(user_id: str, ref: dict = Depends(validate_architect)):
    """Delete user and their organization (admin only)"""
    if not db_pool:
        raise HTTPException(status_code=404)
    
    # Self-protection: cannot delete yourself
    if user_id == ref.get('user_id'):
        raise HTTPException(status_code=403, detail="Signal 104b: Cannot delete own account")
    
    try:
        async with db_pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT id, organization_id, email FROM users WHERE id = $1", 
                user_id
            )
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            org_id = user['organization_id']
            
            async with conn.transaction():
                # Remove created_by reference
                await conn.execute(
                    "UPDATE organizations SET created_by = NULL WHERE created_by = $1", 
                    user_id
                )
                
                # Delete related records
                await conn.execute("DELETE FROM api_keys WHERE organization_id = $1", org_id)
                await conn.execute("DELETE FROM audit_log WHERE organization_id = $1", org_id)
                await conn.execute("DELETE FROM users WHERE id = $1", user_id)
                
                # Delete org if no other users
                await conn.execute("""
                    DELETE FROM organizations WHERE id = $1
                    AND NOT EXISTS (SELECT 1 FROM users WHERE organization_id = $1)
                """, org_id)
            
            return {"message": f"User {user['email']} deleted"}
    except Exception as e:
        print(f"[API] Delete user error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/docs/reference-check")
async def reference_access_check(ref: dict = Depends(validate_architect)):
    """Verify reference documentation access"""
    return {"status": "ok", "access": "reference"}

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("=" * 50)
    print("ONTO API Server")
    print("=" * 50)
    
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

