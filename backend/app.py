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
  
  # Admin
  GET  /v1/admin/stats       - System stats
"""

import os
import hashlib
import secrets
import json
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

# Pricing tiers
TIERS = {
    "pilot": {"slots": 1, "evaluations_per_month": 10, "price": 0},
    "l1": {"slots": 3, "evaluations_per_month": 100, "price": 15000},
    "l2": {"slots": 10, "evaluations_per_month": 1000, "price": 60000},
    "l3": {"slots": 50, "evaluations_per_month": -1, "price": 250000},  # -1 = unlimited
}

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
    tier: str
    created_at: str

class ApiKeyResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    created_at: str
    last_used_at: Optional[str]

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
        return {"organization_id": "dev", "tier": "pilot"}
    
    key_hash = hash_api_key(x_api_key)
    
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT ak.id, ak.organization_id, ak.is_active, 
                   o.name, o.tier, o.slug
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
            "tier": row['tier'],
            "slug": row['slug']
        }

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
    version="1.0.0",
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
# PUBLIC ENDPOINTS
# ============================================================

@app.get("/")
async def root():
    return {
        "name": "ONTO API",
        "version": "1.0.0",
        "docs": "https://api.ontostandard.org/docs",
        "status": "operational"
    }

@app.get("/health")
async def health():
    db_status = "connected" if db_pool else "disconnected"
    return {
        "status": "healthy",
        "database": db_status,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/v1/pricing")
async def get_pricing():
    return {
        "tiers": TIERS,
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
        return {"status": "unavailable", "error": str(e)}

# ============================================================
# AUTH ENDPOINTS
# ============================================================

@app.post("/v1/auth/register")
async def register(request: RegisterRequest):
    """Register new organization"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    slug = request.company.lower().replace(" ", "-")[:50]
    password_hash = hash_password(request.password)
    
    async with db_pool.acquire() as conn:
        # Check if email exists
        existing = await conn.fetchval(
            "SELECT id FROM users WHERE email = $1", request.email
        )
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create organization
        org_id = await conn.fetchval("""
            INSERT INTO organizations (name, slug, tier)
            VALUES ($1, $2, 'pilot')
            RETURNING id
        """, request.company, slug)
        
        # Create user
        user_id = await conn.fetchval("""
            INSERT INTO users (email, name, password_hash, organization_id, role)
            VALUES ($1, $2, $3, $4, 'admin')
            RETURNING id
        """, request.email, request.name, password_hash, org_id)
        
        # Create initial API key
        full_key, prefix = generate_api_key()
        key_hash = hash_api_key(full_key)
        
        await conn.execute("""
            INSERT INTO api_keys (organization_id, name, key_hash, key_prefix, created_by)
            VALUES ($1, 'Default Key', $2, $3, $4)
        """, org_id, key_hash, prefix, user_id)
        
        return {
            "status": "created",
            "organization_id": str(org_id),
            "user_id": str(user_id),
            "api_key": full_key,
            "message": "Save your API key - it won't be shown again!"
        }

@app.post("/v1/auth/login")
async def login(request: LoginRequest):
    """Login and get session info"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    password_hash = hash_password(request.password)
    
    async with db_pool.acquire() as conn:
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
        
        return {
            "status": "authenticated",
            "user_id": str(row['id']),
            "user_name": row['name'],
            "organization_id": str(row['organization_id']),
            "organization_name": row['org_name'],
            "tier": row['tier']
        }

@app.post("/v1/auth/api-keys")
async def create_api_key(
    request: CreateApiKeyRequest,
    org: dict = Depends(validate_api_key)
):
    """Create new API key"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    full_key, prefix = generate_api_key()
    key_hash = hash_api_key(full_key)
    
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO api_keys (organization_id, name, key_hash, key_prefix)
            VALUES ($1, $2, $3, $4)
        """, org['organization_id'], request.name, key_hash, prefix)
        
        return {
            "api_key": full_key,
            "prefix": prefix,
            "name": request.name,
            "message": "Save your API key - it won't be shown again!"
        }

@app.get("/v1/auth/api-keys")
async def list_api_keys(org: dict = Depends(validate_api_key)):
    """List API keys for organization"""
    if not db_pool:
        return {"keys": []}
    
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, name, key_prefix, is_active, created_at, last_used_at
            FROM api_keys
            WHERE organization_id = $1
            ORDER BY created_at DESC
        """, org['organization_id'])
        
        return {
            "keys": [
                {
                    "id": str(r['id']),
                    "name": r['name'],
                    "prefix": r['key_prefix'],
                    "active": r['is_active'],
                    "created_at": r['created_at'].isoformat() if r['created_at'] else None,
                    "last_used_at": r['last_used_at'].isoformat() if r['last_used_at'] else None
                }
                for r in rows
            ]
        }

@app.delete("/v1/auth/api-keys/{key_id}")
async def revoke_api_key(key_id: str, org: dict = Depends(validate_api_key)):
    """Revoke API key"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    async with db_pool.acquire() as conn:
        result = await conn.execute("""
            UPDATE api_keys SET is_active = false
            WHERE id = $1 AND organization_id = $2
        """, key_id, org['organization_id'])
        
        if result == "UPDATE 0":
            raise HTTPException(status_code=404, detail="API key not found")
        
        return {"status": "revoked", "key_id": key_id}

# ============================================================
# EVALUATION ENDPOINTS
# ============================================================

@app.post("/v1/evaluate")
async def submit_evaluation(
    request: EvaluationRequest,
    org: dict = Depends(validate_api_key)
):
    """Submit model for evaluation"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    async with db_pool.acquire() as conn:
        # Check tier limits
        tier_info = TIERS.get(org['tier'], TIERS['pilot'])
        
        if tier_info['evaluations_per_month'] != -1:
            # Count this month's evaluations
            count = await conn.fetchval("""
                SELECT COUNT(*) FROM evaluations
                WHERE organization_id = $1
                AND submitted_at > date_trunc('month', NOW())
            """, org['organization_id'])
            
            if count >= tier_info['evaluations_per_month']:
                raise HTTPException(
                    status_code=403, 
                    detail=f"Monthly evaluation limit reached ({tier_info['evaluations_per_month']})"
                )
        
        # Create evaluation
        eval_id = await conn.fetchval("""
            INSERT INTO evaluations (organization_id, model_name, model_version, status, metrics)
            VALUES ($1, $2, $3, 'pending', $4)
            RETURNING id
        """, org['organization_id'], request.model_name, request.model_version,
            json.dumps({"predictions_count": len(request.predictions)}))
        
        # Log usage
        await conn.execute("""
            INSERT INTO usage_events (organization_id, event_type, resource_id, event_metadata)
            VALUES ($1, 'evaluation_submitted', $2, $3)
        """, org['organization_id'], eval_id, 
            json.dumps({"model": request.model_name, "predictions": len(request.predictions)}))
        
        return {
            "evaluation_id": str(eval_id),
            "status": "pending",
            "model_name": request.model_name,
            "predictions_received": len(request.predictions),
            "message": "Evaluation queued for processing"
        }

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
            SELECT c.*, o.name as org_name
            FROM certificates c
            JOIN organizations o ON c.organization_id = o.id
            WHERE c.id = $1 OR c.certificate_number = $1
        """, certificate_id)
        
        if not row:
            raise HTTPException(status_code=404, detail="Certificate not found")
        
        return {
            "certificate_number": row['certificate_number'],
            "organization": row['org_name'],
            "model_name": row['model_name'],
            "level": row['level'],
            "metrics": row['metrics_snapshot'],
            "verification_hash": row['verification_hash'],
            "status": "revoked" if row['revoked_at'] else "valid",
            "issued_at": row['issued_at'].isoformat() if row['issued_at'] else None,
            "expires_at": row['expires_at'].isoformat() if row['expires_at'] else None,
            "verify_url": f"https://api.ontostandard.org/v1/certificates/{row['certificate_number']}"
        }

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
        
        tier_info = TIERS.get(row['tier'], TIERS['pilot'])
        
        return {
            "id": str(row['id']),
            "name": row['name'],
            "slug": row['slug'],
            "tier": row['tier'],
            "tier_info": tier_info,
            "evaluations_count": row['eval_count'],
            "certificates_count": row['cert_count'],
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
        
        # By tier
        tier_counts = await conn.fetch("""
            SELECT tier, COUNT(*) as count 
            FROM organizations 
            GROUP BY tier
        """)
        stats['by_tier'] = {r['tier']: r['count'] for r in tier_counts}
        
        return stats

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("=" * 50)
    print("ONTO API Server")
    print("=" * 50)
    
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
