/**
 * ONTO Admin Panel Patch Script
 * Applies admin endpoints to app.py
 */

const fs = require('fs');
const path = require('path');

// Read original file
const appPath = path.join(__dirname, 'backend', 'app.py');
let content = fs.readFileSync(appPath, 'utf8');

console.log('Patching app.py for Admin Panel...\n');

// ============================================================
// PATCH 1: Add role to login response
// ============================================================

const oldLogin = `        row = await conn.fetchrow("""
            SELECT u.id, u.name, u.organization_id, o.name as org_name, o.tier
            FROM users u
            JOIN organizations o ON u.organization_id = o.id
            WHERE u.email = $1 AND u.password_hash = $2 AND u.is_active = true
        """, request.email, password_hash)`;

const newLogin = `        row = await conn.fetchrow("""
            SELECT u.id, u.name, u.organization_id, u.role, o.name as org_name, o.tier
            FROM users u
            JOIN organizations o ON u.organization_id = o.id
            WHERE u.email = $1 AND u.password_hash = $2 AND u.is_active = true
        """, request.email, password_hash)`;

if (content.includes(oldLogin)) {
    content = content.replace(oldLogin, newLogin);
    console.log('✓ Patch 1: Added role to login SELECT');
} else {
    console.log('⚠ Patch 1: Already applied or not found');
}

// ============================================================
// PATCH 2: Add role to login return
// ============================================================

const oldReturn = `        return {
            "user_id": str(row['id']),
            "name": row['name'],
            "organization_id": str(row['organization_id']),
            "organization_name": row['org_name'],
            "layer": row['tier'],
            "token": token,
            "message": "Login successful"
        }`;

const newReturn = `        return {
            "user_id": str(row['id']),
            "name": row['name'],
            "organization_id": str(row['organization_id']),
            "organization_name": row['org_name'],
            "layer": row['tier'],
            "role": row['role'],
            "token": token,
            "message": "Login successful"
        }`;

if (content.includes(oldReturn)) {
    content = content.replace(oldReturn, newReturn);
    console.log('✓ Patch 2: Added role to login response');
} else {
    console.log('⚠ Patch 2: Already applied or not found');
}

// ============================================================
// PATCH 3: Add superadmin validation helper after validate_api_key
// ============================================================

const afterValidateApiKey = `            "slug": row['slug'],
            "stripe_customer_id": row['stripe_customer_id']
        }`;

const withSuperadminHelper = `            "slug": row['slug'],
            "stripe_customer_id": row['stripe_customer_id']
        }

async def validate_superadmin(x_api_key: str = Header(...)) -> dict:
    """Validate API key and check superadmin role"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    key_hash = hash_api_key(x_api_key)
    
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT ak.id, ak.organization_id, ak.is_active,
                   u.id as user_id, u.role,
                   o.name, o.tier, o.slug
            FROM api_keys ak
            JOIN organizations o ON ak.organization_id = o.id
            JOIN users u ON u.organization_id = o.id
            WHERE ak.key_hash = $1
        """, key_hash)
        
        if not row:
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        if not row['is_active']:
            raise HTTPException(status_code=401, detail="API key revoked")
        
        if row['role'] != 'superadmin':
            raise HTTPException(status_code=403, detail="Superadmin access required")
        
        return {
            "api_key_id": str(row['id']),
            "organization_id": str(row['organization_id']),
            "user_id": str(row['user_id']),
            "organization_name": row['name'],
            "layer": row['tier'],
            "role": row['role']
        }`;

if (content.includes(afterValidateApiKey) && !content.includes('validate_superadmin')) {
    content = content.replace(afterValidateApiKey, withSuperadminHelper);
    console.log('✓ Patch 3: Added validate_superadmin helper');
} else {
    console.log('⚠ Patch 3: Already applied or not found');
}

// ============================================================
// PATCH 4: Replace ADMIN ENDPOINTS section
// ============================================================

const oldAdminSection = `# ============================================================
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
        
        return stats`;

const newAdminSection = `# ============================================================
# ADMIN ENDPOINTS (Superadmin only)
# ============================================================

@app.get("/v1/admin/stats")
async def get_admin_stats(admin: dict = Depends(validate_superadmin)):
    """Get system stats (superadmin only)"""
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
        
        # By layer
        tier_counts = await conn.fetch("""
            SELECT tier, COUNT(*) as count 
            FROM organizations 
            GROUP BY tier
        """)
        stats['by_layer'] = {r['tier']: r['count'] for r in tier_counts}
        
        # Violations count
        stats['violations_today'] = await conn.fetchval("""
            SELECT COUNT(*) FROM rate_limit_violations 
            WHERE created_at > NOW() - INTERVAL '24 hours'
        """)
        
        # Banned orgs
        stats['banned_organizations'] = await conn.fetchval(
            "SELECT COUNT(*) FROM organizations WHERE is_banned = true"
        )
        
        return stats

@app.get("/v1/admin/users")
async def admin_list_users(
    admin: dict = Depends(validate_superadmin),
    limit: int = 50,
    offset: int = 0,
    search: Optional[str] = None
):
    """List all users (superadmin only)"""
    if not db_pool:
        return {"error": "Database not available"}
    
    async with db_pool.acquire() as conn:
        if search:
            rows = await conn.fetch("""
                SELECT u.id, u.email, u.name, u.role, u.is_active, u.created_at, u.last_login_at,
                       o.id as org_id, o.name as org_name, o.tier, o.is_banned
                FROM users u
                JOIN organizations o ON u.organization_id = o.id
                WHERE u.email ILIKE $1 OR u.name ILIKE $1 OR o.name ILIKE $1
                ORDER BY u.created_at DESC
                LIMIT $2 OFFSET $3
            """, f"%{search}%", limit, offset)
        else:
            rows = await conn.fetch("""
                SELECT u.id, u.email, u.name, u.role, u.is_active, u.created_at, u.last_login_at,
                       o.id as org_id, o.name as org_name, o.tier, o.is_banned
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
                    "created_at": r['created_at'].isoformat() if r['created_at'] else None,
                    "last_login_at": r['last_login_at'].isoformat() if r['last_login_at'] else None,
                    "organization": {
                        "id": str(r['org_id']),
                        "name": r['org_name'],
                        "tier": r['tier'],
                        "is_banned": r['is_banned']
                    }
                }
                for r in rows
            ],
            "total": total,
            "limit": limit,
            "offset": offset
        }

@app.get("/v1/admin/users/{user_id}")
async def admin_get_user(user_id: str, admin: dict = Depends(validate_superadmin)):
    """Get user details (superadmin only)"""
    if not db_pool:
        return {"error": "Database not available"}
    
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT u.*, o.name as org_name, o.tier, o.is_banned, o.slug,
                   o.stripe_customer_id, o.profile_data
            FROM users u
            JOIN organizations o ON u.organization_id = o.id
            WHERE u.id = $1
        """, user_id)
        
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user's API keys
        keys = await conn.fetch("""
            SELECT id, name, key_prefix, is_active, created_at, last_used_at
            FROM api_keys WHERE organization_id = $1
        """, row['organization_id'])
        
        # Get recent evaluations
        evals = await conn.fetch("""
            SELECT id, model_name, status, created_at
            FROM evaluations WHERE organization_id = $1
            ORDER BY created_at DESC LIMIT 10
        """, row['organization_id'])
        
        return {
            "user": {
                "id": str(row['id']),
                "email": row['email'],
                "name": row['name'],
                "role": row['role'],
                "is_active": row['is_active'],
                "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                "last_login_at": row['last_login_at'].isoformat() if row['last_login_at'] else None
            },
            "organization": {
                "id": str(row['organization_id']),
                "name": row['org_name'],
                "slug": row['slug'],
                "tier": row['tier'],
                "is_banned": row['is_banned'],
                "stripe_customer_id": row['stripe_customer_id'],
                "profile_data": json.loads(row['profile_data']) if row['profile_data'] else {}
            },
            "api_keys": [
                {
                    "id": str(k['id']),
                    "name": k['name'],
                    "key_prefix": k['key_prefix'],
                    "is_active": k['is_active'],
                    "created_at": k['created_at'].isoformat() if k['created_at'] else None,
                    "last_used_at": k['last_used_at'].isoformat() if k['last_used_at'] else None
                }
                for k in keys
            ],
            "recent_evaluations": [
                {
                    "id": str(e['id']),
                    "model_name": e['model_name'],
                    "status": e['status'],
                    "created_at": e['created_at'].isoformat() if e['created_at'] else None
                }
                for e in evals
            ]
        }

@app.post("/v1/admin/users/{user_id}/ban")
async def admin_ban_user(user_id: str, admin: dict = Depends(validate_superadmin)):
    """Ban user's organization (superadmin only)"""
    if not db_pool:
        return {"error": "Database not available"}
    
    async with db_pool.acquire() as conn:
        # Get user's org
        row = await conn.fetchrow("SELECT organization_id FROM users WHERE id = $1", user_id)
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Ban organization
        await conn.execute("""
            UPDATE organizations 
            SET is_banned = true, banned_at = NOW(), ban_reason = 'Banned by admin'
            WHERE id = $1
        """, row['organization_id'])
        
        # Deactivate all API keys
        await conn.execute(
            "UPDATE api_keys SET is_active = false WHERE organization_id = $1",
            row['organization_id']
        )
        
        # Log
        await conn.execute("""
            INSERT INTO audit_log (organization_id, user_id, action, resource_type, details)
            VALUES ($1, $2, 'ban', 'organization', $3)
        """, row['organization_id'], admin['user_id'], json.dumps({"banned_user_id": user_id}))
        
        return {"status": "banned", "organization_id": str(row['organization_id'])}

@app.post("/v1/admin/users/{user_id}/unban")
async def admin_unban_user(user_id: str, admin: dict = Depends(validate_superadmin)):
    """Unban user's organization (superadmin only)"""
    if not db_pool:
        return {"error": "Database not available"}
    
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT organization_id FROM users WHERE id = $1", user_id)
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        
        await conn.execute("""
            UPDATE organizations 
            SET is_banned = false, banned_at = NULL, ban_reason = NULL
            WHERE id = $1
        """, row['organization_id'])
        
        # Reactivate API keys
        await conn.execute(
            "UPDATE api_keys SET is_active = true WHERE organization_id = $1",
            row['organization_id']
        )
        
        await conn.execute("""
            INSERT INTO audit_log (organization_id, user_id, action, resource_type, details)
            VALUES ($1, $2, 'unban', 'organization', $3)
        """, row['organization_id'], admin['user_id'], json.dumps({"unbanned_user_id": user_id}))
        
        return {"status": "unbanned", "organization_id": str(row['organization_id'])}

@app.get("/v1/admin/violations")
async def admin_list_violations(
    admin: dict = Depends(validate_superadmin),
    limit: int = 100,
    offset: int = 0
):
    """List rate limit violations (superadmin only)"""
    if not db_pool:
        return {"error": "Database not available"}
    
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT v.*, o.name as org_name, o.tier
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
                    "organization_name": r['org_name'],
                    "ip_address": r['ip_address'],
                    "violation_type": r['violation_type'],
                    "request_count": r['request_count'],
                    "limit_value": r['limit_value'],
                    "endpoint": r['endpoint'],
                    "details": r['details'],
                    "created_at": r['created_at'].isoformat() if r['created_at'] else None
                }
                for r in rows
            ],
            "total": total,
            "limit": limit,
            "offset": offset
        }

@app.get("/v1/admin/broadcast")
async def admin_get_broadcast(admin: dict = Depends(validate_superadmin)):
    """Get broadcast status (superadmin only)"""
    if not db_pool:
        return {"error": "Database not available"}
    
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT value FROM system_settings WHERE key = 'broadcast_enabled'"
        )
        return {"broadcast_enabled": row['value'] if row else True}

@app.post("/v1/admin/broadcast")
async def admin_toggle_broadcast(
    admin: dict = Depends(validate_superadmin),
    enabled: bool = True
):
    """Toggle broadcast (superadmin only)"""
    if not db_pool:
        return {"error": "Database not available"}
    
    async with db_pool.acquire() as conn:
        await conn.execute("""
            UPDATE system_settings 
            SET value = $1::jsonb, updated_at = NOW(), updated_by = $2
            WHERE key = 'broadcast_enabled'
        """, json.dumps(enabled), admin['user_id'])
        
        return {"broadcast_enabled": enabled, "updated": True}

@app.get("/v1/admin/export/{org_id}")
async def admin_export_org(org_id: str, admin: dict = Depends(validate_superadmin)):
    """Export organization data as JSON (superadmin only)"""
    if not db_pool:
        return {"error": "Database not available"}
    
    async with db_pool.acquire() as conn:
        # Organization
        org = await conn.fetchrow("SELECT * FROM organizations WHERE id = $1", org_id)
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        # Users
        users = await conn.fetch("SELECT * FROM users WHERE organization_id = $1", org_id)
        
        # API Keys (without hashes)
        keys = await conn.fetch("""
            SELECT id, name, key_prefix, is_active, created_at, last_used_at 
            FROM api_keys WHERE organization_id = $1
        """, org_id)
        
        # Evaluations
        evals = await conn.fetch("SELECT * FROM evaluations WHERE organization_id = $1", org_id)
        
        # Certificates
        certs = await conn.fetch("SELECT * FROM certificates WHERE organization_id = $1", org_id)
        
        # Audit log
        audit = await conn.fetch("""
            SELECT * FROM audit_log WHERE organization_id = $1 ORDER BY created_at DESC LIMIT 1000
        """, org_id)
        
        def serialize_row(r):
            d = dict(r)
            for k, v in d.items():
                if hasattr(v, 'isoformat'):
                    d[k] = v.isoformat()
                elif isinstance(v, uuid.UUID):
                    d[k] = str(v)
            return d
        
        return {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "organization": serialize_row(org),
            "users": [serialize_row(u) for u in users],
            "api_keys": [serialize_row(k) for k in keys],
            "evaluations": [serialize_row(e) for e in evals],
            "certificates": [serialize_row(c) for c in certs],
            "audit_log": [serialize_row(a) for a in audit]
        }`;

if (content.includes(oldAdminSection)) {
    content = content.replace(oldAdminSection, newAdminSection);
    console.log('✓ Patch 4: Replaced ADMIN ENDPOINTS section');
} else {
    console.log('⚠ Patch 4: Admin section not found or already modified');
}

// ============================================================
// PATCH 5: Add ban check to rate limit middleware
// ============================================================

const oldMiddlewareCheck = `            if row:
                layer = row['tier']  # DB column name
    
    # Check rate limit`;

const newMiddlewareCheck = `            if row:
                layer = row['tier']  # DB column name
                
                # Check if organization is banned
                ban_check = await conn.fetchrow("""
                    SELECT is_banned FROM organizations o
                    JOIN api_keys ak ON ak.organization_id = o.id
                    WHERE ak.key_hash = $1
                """, key_hash)
                if ban_check and ban_check['is_banned']:
                    return JSONResponse(
                        status_code=403,
                        content={"detail": "Organization is banned", "code": "ORG_BANNED"}
                    )
    
    # Check rate limit`;

if (content.includes(oldMiddlewareCheck) && !content.includes('is_banned')) {
    content = content.replace(oldMiddlewareCheck, newMiddlewareCheck);
    console.log('✓ Patch 5: Added ban check to middleware');
} else {
    console.log('⚠ Patch 5: Already applied or not found');
}

// ============================================================
// Save patched file
// ============================================================

fs.writeFileSync(appPath, content);
console.log('\n✅ app.py patched successfully!');
console.log('\nNext steps:');
console.log('1. git add backend/app.py');
console.log('2. git commit -m "Add admin panel endpoints"');
console.log('3. git push origin main');
console.log('4. Railway will auto-deploy');
