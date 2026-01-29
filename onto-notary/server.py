"""
ONTO Notary Server - Production
Validates and signs Merkle roots for permanent certification.

Environment variables:
- PORT: Server port (default: 8082)
- DATABASE_URL: PostgreSQL connection string
- NOTARY_SECRET: HMAC signing secret
- SIGNAL_URL: Signal server URL
"""

import os
import json
import time
import hmac
import hashlib
import secrets
from datetime import datetime, timezone
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# ============================================================
# Configuration
# ============================================================

PORT = int(os.getenv("PORT", "8082"))
DATABASE_URL = os.getenv("DATABASE_URL")
NOTARY_SECRET = os.getenv("NOTARY_SECRET", "dev-secret-change-in-prod")
SIGNAL_URL = os.getenv("SIGNAL_URL", "https://signal.ontostandard.org")

# PostgreSQL setup
import asyncpg
db_pool = None

# ============================================================
# Database
# ============================================================

async def init_db():
    """Initialize database connection and tables"""
    global db_pool
    
    if not DATABASE_URL:
        print("[NOTARY] WARNING: No DATABASE_URL - using in-memory storage")
        return
    
    try:
        db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
        
        # Create tables - using notary_certificates to avoid conflict with backend
        async with db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS notary_certificates (
                    certificate_id VARCHAR(64) PRIMARY KEY,
                    merkle_root VARCHAR(64) NOT NULL,
                    sigma_id VARCHAR(32) NOT NULL,
                    model_id VARCHAR(128) NOT NULL,
                    batch_size INTEGER NOT NULL,
                    metrics_summary JSONB,
                    client_id VARCHAR(64) NOT NULL,
                    issued_at TIMESTAMPTZ NOT NULL,
                    expires_at TIMESTAMPTZ NOT NULL,
                    signature VARCHAR(128) NOT NULL,
                    status VARCHAR(16) NOT NULL DEFAULT 'CERTIFIED',
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS idx_notary_certificates_client 
                ON notary_certificates(client_id);
                
                CREATE INDEX IF NOT EXISTS idx_notary_certificates_model 
                ON notary_certificates(model_id);
                
                CREATE INDEX IF NOT EXISTS idx_notary_certificates_status 
                ON notary_certificates(status);
            """)
        
        print(f"[NOTARY] Database connected: PostgreSQL (table: notary_certificates)")
    except Exception as e:
        print(f"[NOTARY] Database error: {e}")
        print("[NOTARY] Falling back to in-memory storage")

async def close_db():
    """Close database connection"""
    global db_pool
    if db_pool:
        await db_pool.close()

# In-memory fallback
certificates_memory: dict = {}

# ============================================================
# Lifespan
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()

# ============================================================
# App
# ============================================================

app = FastAPI(
    title="ONTO Notary",
    description="Certificate Authority for AI Reliability Proofs",
    version="1.1.0",
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
# Data Models
# ============================================================

class SignRequest(BaseModel):
    merkle_root: str
    sigma_id: str
    model_id: str
    batch_size: int
    metrics_summary: dict
    client_id: str
    timestamp: int

class Certificate(BaseModel):
    certificate_id: str
    merkle_root: str
    sigma_id: str
    model_id: str
    batch_size: int
    metrics_summary: dict
    client_id: str
    issued_at: str
    expires_at: str
    signature: str
    status: str

class VerifyResponse(BaseModel):
    valid: bool
    certificate_id: str
    status: str
    issued_at: str
    merkle_root: str
    message: str

# ============================================================
# Helpers
# ============================================================

def generate_certificate_id() -> str:
    timestamp = int(time.time())
    random_part = secrets.token_hex(8)
    return f"ONTO-{timestamp}-{random_part}"

def sign_data(data: bytes) -> str:
    signature = hmac.new(
        NOTARY_SECRET.encode(),
        data,
        hashlib.sha256
    ).hexdigest()
    return signature

def verify_signature(data: bytes, signature: str) -> bool:
    expected = sign_data(data)
    return hmac.compare_digest(expected, signature)

def validate_api_key(x_api_key: str = Header(...)) -> str:
    if not x_api_key or len(x_api_key) < 8:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key[:16]

# ============================================================
# Database Operations
# ============================================================

async def save_certificate(cert: Certificate):
    """Save certificate to database or memory"""
    if db_pool:
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO notary_certificates (
                    certificate_id, merkle_root, sigma_id, model_id,
                    batch_size, metrics_summary, client_id,
                    issued_at, expires_at, signature, status
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """,
                cert.certificate_id,
                cert.merkle_root,
                cert.sigma_id,
                cert.model_id,
                cert.batch_size,
                json.dumps(cert.metrics_summary),
                cert.client_id,
                datetime.fromisoformat(cert.issued_at),
                datetime.fromisoformat(cert.expires_at),
                cert.signature,
                cert.status
            )
    else:
        certificates_memory[cert.certificate_id] = cert

async def get_certificate(cert_id: str) -> Optional[Certificate]:
    """Get certificate from database or memory"""
    if db_pool:
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM notary_certificates WHERE certificate_id = $1",
                cert_id
            )
            if row:
                return Certificate(
                    certificate_id=row['certificate_id'],
                    merkle_root=row['merkle_root'],
                    sigma_id=row['sigma_id'],
                    model_id=row['model_id'],
                    batch_size=row['batch_size'],
                    metrics_summary=json.loads(row['metrics_summary']) if isinstance(row['metrics_summary'], str) else row['metrics_summary'],
                    client_id=row['client_id'],
                    issued_at=row['issued_at'].isoformat(),
                    expires_at=row['expires_at'].isoformat(),
                    signature=row['signature'],
                    status=row['status']
                )
    else:
        return certificates_memory.get(cert_id)
    return None

async def update_certificate_status(cert_id: str, status: str):
    """Update certificate status"""
    if db_pool:
        async with db_pool.acquire() as conn:
            await conn.execute(
                "UPDATE notary_certificates SET status = $1 WHERE certificate_id = $2",
                status, cert_id
            )
    else:
        if cert_id in certificates_memory:
            cert = certificates_memory[cert_id]
            certificates_memory[cert_id] = Certificate(
                certificate_id=cert.certificate_id,
                merkle_root=cert.merkle_root,
                sigma_id=cert.sigma_id,
                model_id=cert.model_id,
                batch_size=cert.batch_size,
                metrics_summary=cert.metrics_summary,
                client_id=cert.client_id,
                issued_at=cert.issued_at,
                expires_at=cert.expires_at,
                signature=cert.signature,
                status=status
            )

async def list_client_certificates(client_id: str, limit: int = 100):
    """List all certificates for a client"""
    if db_pool:
        async with db_pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT * FROM notary_certificates 
                   WHERE client_id = $1 
                   ORDER BY created_at DESC 
                   LIMIT $2""",
                client_id, limit
            )
            return [
                {
                    "certificate_id": row['certificate_id'],
                    "model_id": row['model_id'],
                    "status": row['status'],
                    "issued_at": row['issued_at'].isoformat(),
                    "batch_size": row['batch_size']
                }
                for row in rows
            ]
    else:
        return [
            {
                "certificate_id": cert.certificate_id,
                "model_id": cert.model_id,
                "status": cert.status,
                "issued_at": cert.issued_at,
                "batch_size": cert.batch_size
            }
            for cert in certificates_memory.values()
            if cert.client_id == client_id
        ][:limit]

# ============================================================
# Endpoints
# ============================================================

@app.get("/")
async def root():
    return {
        "service": "ONTO Notary",
        "version": "1.1.0",
        "status": "operational",
        "database": "PostgreSQL" if db_pool else "in-memory",
        "table": "notary_certificates",
        "endpoints": {
            "sign": "POST /v1/sign-root",
            "certificate": "GET /v1/certificate/{id}",
            "verify": "GET /v1/verify/{id}"
        }
    }

@app.get("/health")
async def health():
    db_status = "connected" if db_pool else "in-memory"
    
    # Test actual DB connection
    if db_pool:
        try:
            async with db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            db_status = "connected"
        except Exception as e:
            db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "database": db_status,
        "table": "notary_certificates",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.post("/v1/sign-root", response_model=Certificate)
async def sign_root(
    request: SignRequest,
    client_id: str = Depends(validate_api_key)
):
    """Sign a Merkle root and issue a certificate"""
    
    # Validate merkle_root format
    if len(request.merkle_root) != 64:
        raise HTTPException(status_code=400, detail="Invalid merkle_root: must be 64 hex chars")
    
    try:
        bytes.fromhex(request.merkle_root)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid merkle_root: not valid hex")
    
    # Validate timestamp
    now = int(time.time())
    if abs(now - request.timestamp) > 300:
        raise HTTPException(status_code=400, detail="Timestamp too old or in future")
    
    # Generate certificate
    cert_id = generate_certificate_id()
    issued_at = datetime.now(timezone.utc)
    expires_at = datetime.fromtimestamp(issued_at.timestamp() + 365 * 24 * 3600, tz=timezone.utc)
    
    # Create signable payload
    payload = json.dumps({
        "certificate_id": cert_id,
        "merkle_root": request.merkle_root,
        "sigma_id": request.sigma_id,
        "model_id": request.model_id,
        "batch_size": request.batch_size,
        "client_id": client_id,
        "issued_at": issued_at.isoformat()
    }, sort_keys=True).encode()
    
    signature = sign_data(payload)
    
    certificate = Certificate(
        certificate_id=cert_id,
        merkle_root=request.merkle_root,
        sigma_id=request.sigma_id,
        model_id=request.model_id,
        batch_size=request.batch_size,
        metrics_summary=request.metrics_summary,
        client_id=client_id,
        issued_at=issued_at.isoformat(),
        expires_at=expires_at.isoformat(),
        signature=signature,
        status="CERTIFIED"
    )
    
    await save_certificate(certificate)
    
    print(f"[NOTARY] Certificate issued: {cert_id}")
    print(f"         Model: {request.model_id} | Batch: {request.batch_size}")
    
    return certificate

@app.get("/v1/certificate/{certificate_id}", response_model=Certificate)
async def get_certificate_endpoint(certificate_id: str):
    """Retrieve a certificate by ID"""
    cert = await get_certificate(certificate_id)
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    return cert

@app.get("/v1/verify/{certificate_id}", response_model=VerifyResponse)
async def verify_certificate(certificate_id: str):
    """Verify a certificate's validity"""
    cert = await get_certificate(certificate_id)
    
    if not cert:
        return VerifyResponse(
            valid=False,
            certificate_id=certificate_id,
            status="NOT_FOUND",
            issued_at="",
            merkle_root="",
            message="Certificate not found"
        )
    
    # Check expiration
    expires_at = datetime.fromisoformat(cert.expires_at)
    if datetime.now(timezone.utc) > expires_at:
        return VerifyResponse(
            valid=False,
            certificate_id=certificate_id,
            status="EXPIRED",
            issued_at=cert.issued_at,
            merkle_root=cert.merkle_root,
            message="Certificate has expired"
        )
    
    # Check revocation
    if cert.status == "REVOKED":
        return VerifyResponse(
            valid=False,
            certificate_id=certificate_id,
            status="REVOKED",
            issued_at=cert.issued_at,
            merkle_root=cert.merkle_root,
            message="Certificate has been revoked"
        )
    
    # Verify signature
    payload = json.dumps({
        "certificate_id": cert.certificate_id,
        "merkle_root": cert.merkle_root,
        "sigma_id": cert.sigma_id,
        "model_id": cert.model_id,
        "batch_size": cert.batch_size,
        "client_id": cert.client_id,
        "issued_at": cert.issued_at
    }, sort_keys=True).encode()
    
    if not verify_signature(payload, cert.signature):
        return VerifyResponse(
            valid=False,
            certificate_id=certificate_id,
            status="INVALID_SIGNATURE",
            issued_at=cert.issued_at,
            merkle_root=cert.merkle_root,
            message="Signature verification failed"
        )
    
    return VerifyResponse(
        valid=True,
        certificate_id=certificate_id,
        status="CERTIFIED",
        issued_at=cert.issued_at,
        merkle_root=cert.merkle_root,
        message="Certificate is valid"
    )

@app.get("/v1/certificates")
async def list_certificates(
    client_id: str = Depends(validate_api_key),
    limit: int = 100
):
    """List certificates for a client"""
    certs = await list_client_certificates(client_id, limit)
    return {"certificates": certs, "total": len(certs)}

@app.post("/v1/revoke/{certificate_id}")
async def revoke_certificate(
    certificate_id: str,
    client_id: str = Depends(validate_api_key)
):
    """Revoke a certificate"""
    cert = await get_certificate(certificate_id)
    
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    
    if cert.client_id != client_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await update_certificate_status(certificate_id, "REVOKED")
    
    print(f"[NOTARY] Certificate revoked: {certificate_id}")
    
    return {"status": "revoked", "certificate_id": certificate_id}

# Public Registry
@app.get("/registry/{certificate_id}")
async def public_verify(certificate_id: str):
    """Public verification endpoint"""
    result = await verify_certificate(certificate_id)
    
    if result.valid:
        cert = await get_certificate(certificate_id)
        return {
            "verified": True,
            "certificate_id": certificate_id,
            "model_id": cert.model_id,
            "issued_at": cert.issued_at,
            "merkle_root_preview": cert.merkle_root[:16] + "...",
            "batch_size": cert.batch_size,
            "metrics": cert.metrics_summary,
            "verify_url": f"https://notary.ontostandard.org/registry/{certificate_id}"
        }
    else:
        return {
            "verified": False,
            "certificate_id": certificate_id,
            "reason": result.message
        }

# Stats
@app.get("/v1/stats")
async def get_stats():
    """Get notary statistics"""
    if db_pool:
        async with db_pool.acquire() as conn:
            total = await conn.fetchval("SELECT COUNT(*) FROM notary_certificates")
            certified = await conn.fetchval("SELECT COUNT(*) FROM notary_certificates WHERE status = 'CERTIFIED'")
            revoked = await conn.fetchval("SELECT COUNT(*) FROM notary_certificates WHERE status = 'REVOKED'")
            return {
                "total_certificates": total,
                "certified": certified,
                "revoked": revoked,
                "database": "PostgreSQL",
                "table": "notary_certificates"
            }
    else:
        total = len(certificates_memory)
        return {
            "total_certificates": total,
            "database": "in-memory"
        }

# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    print("=" * 50)
    print("ONTO Notary Server - Production v1.1.0")
    print("=" * 50)
    print(f"Port: {PORT}")
    print(f"Signal URL: {SIGNAL_URL}")
    print(f"Database: {'PostgreSQL' if DATABASE_URL else 'in-memory'}")
    print(f"Table: notary_certificates")
    print("=" * 50)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        log_level="info"
    )
