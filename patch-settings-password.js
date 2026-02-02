const fs = require('fs');
const path = require('path');

const portalPath = path.join(__dirname, 'docs', 'app', 'index.html');
let content = fs.readFileSync(portalPath, 'utf8');

// Find settings page and add password change section
const settingsSection = `<div class="page" id="page-settings">`;

const passwordHTML = `<div class="page" id="page-settings">
            <!-- Change Password Section -->
            <div class="settings-section" style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 24px;">
                <h3 style="font-size: 16px; font-weight: 600; margin-bottom: 16px;">Change Password</h3>
                <div style="max-width: 400px;">
                    <div class="form-group" style="margin-bottom: 12px;">
                        <label class="form-label" style="font-size: 13px;">Current Password</label>
                        <input type="password" id="current-password" class="form-input" placeholder="Enter current password">
                    </div>
                    <div class="form-group" style="margin-bottom: 12px;">
                        <label class="form-label" style="font-size: 13px;">New Password</label>
                        <input type="password" id="new-password" class="form-input" placeholder="Enter new password">
                    </div>
                    <div class="form-group" style="margin-bottom: 16px;">
                        <label class="form-label" style="font-size: 13px;">Confirm New Password</label>
                        <input type="password" id="confirm-password" class="form-input" placeholder="Confirm new password">
                    </div>
                    <button class="btn btn-primary" style="width: auto; padding: 10px 20px;" onclick="changePassword(this)">Change Password</button>
                </div>
            </div>`;

if (content.includes(settingsSection) && !content.includes('current-password')) {
    content = content.replace(settingsSection, passwordHTML);
    console.log('✓ Added password change UI to Settings');
} else {
    console.log('⚠ Already exists or not found');
}

// Add JS function
const changePasswordJS = `
async function changePassword(btn) {
    const currentPwd = document.getElementById('current-password').value;
    const newPwd = document.getElementById('new-password').value;
    const confirmPwd = document.getElementById('confirm-password').value;
    
    if (!currentPwd || !newPwd || !confirmPwd) {
        showToast('Please fill in all fields', 'error');
        return;
    }
    
    if (newPwd !== confirmPwd) {
        showToast('New passwords do not match', 'error');
        return;
    }
    
    if (newPwd.length < 8) {
        showToast('Password must be at least 8 characters', 'error');
        return;
    }
    
    const apiKey = localStorage.getItem('onto_api_key');
    if (!apiKey) {
        showToast('No API key found. Please re-login.', 'error');
        return;
    }
    
    setLoading(btn, true);
    
    try {
        const res = await fetch('https://api.ontostandard.org/v1/auth/change-password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'x-api-key': apiKey
            },
            body: JSON.stringify({
                current_password: currentPwd,
                new_password: newPwd
            })
        });
        
        const data = await res.json();
        
        if (!res.ok) {
            throw new Error(data.detail || 'Failed to change password');
        }
        
        showToast('Password changed successfully', 'success');
        document.getElementById('current-password').value = '';
        document.getElementById('new-password').value = '';
        document.getElementById('confirm-password').value = '';
        
    } catch (err) {
        showToast(err.message, 'error');
    }
    
    setLoading(btn, false);
}
`;

const scriptClose = '</script>\n</body>';
if (!content.includes('changePassword(btn)')) {
    content = content.replace(scriptClose, changePasswordJS + '\n</script>\n</body>');
    console.log('✓ Added changePassword JS function');
}

fs.writeFileSync(portalPath, content);
console.log('✅ Portal patched with password change!');
