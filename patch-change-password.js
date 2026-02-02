const fs = require('fs');
const path = require('path');

const appPath = path.join(__dirname, 'backend', 'app.py');
let content = fs.readFileSync(appPath, 'utf8');

const newEndpoint = `

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

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
`;

// Insert after ChangePasswordRequest or after login endpoint
const insertPoint = `@app.post("/v1/auth/api-keys")`;

if (content.includes(insertPoint) && !content.includes('change-password')) {
    content = content.replace(insertPoint, newEndpoint + '\n' + insertPoint);
    fs.writeFileSync(appPath, content);
    console.log('✓ Added /v1/auth/change-password endpoint');
} else {
    console.log('⚠ Already exists or insert point not found');
}