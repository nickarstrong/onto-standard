/**
 * ONTO Admin Panel Patch for Client Portal
 * Adds admin section to onto-client-portal
 */

const fs = require('fs');
const path = require('path');

const portalPath = path.join(__dirname, 'docs', 'app', 'index.html');
let content = fs.readFileSync(portalPath, 'utf8');

console.log('Patching portal for Admin Panel...\n');

// ============================================================
// PATCH 1: Add Admin nav item after Settings
// ============================================================

const oldNav = `            <div class="nav-item" onclick="showPage('settings', this)">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/></svg>
                Account
            </div>
        </nav>`;

const newNav = `            <div class="nav-item" onclick="showPage('settings', this)">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/></svg>
                Account
            </div>
            <div class="nav-item admin-nav-item" onclick="showPage('admin', this)" style="display: none;">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/><circle cx="12" cy="12" r="2" fill="currentColor"/></svg>
                Admin Panel
            </div>
        </nav>`;

if (content.includes(oldNav)) {
    content = content.replace(oldNav, newNav);
    console.log('✓ Patch 1: Added Admin nav item');
} else {
    console.log('⚠ Patch 1: Nav not found or already patched');
}

// ============================================================
// PATCH 2: Add Admin page before closing </main>
// ============================================================

const adminPageHTML = `
        <!-- ADMIN PAGE (superadmin only) -->
        <div class="page" id="page-admin">
            <div class="page-header">
                <h1>Admin Panel</h1>
                <p class="page-subtitle">System administration (superadmin only)</p>
            </div>
            
            <!-- Admin Stats -->
            <div class="admin-stats-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 16px; margin-bottom: 24px;">
                <div class="stat-card" style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 16px;">
                    <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 4px;">Organizations</div>
                    <div id="admin-stat-orgs" style="font-size: 24px; font-weight: 700;">-</div>
                </div>
                <div class="stat-card" style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 16px;">
                    <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 4px;">Users</div>
                    <div id="admin-stat-users" style="font-size: 24px; font-weight: 700;">-</div>
                </div>
                <div class="stat-card" style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 16px;">
                    <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 4px;">API Keys</div>
                    <div id="admin-stat-keys" style="font-size: 24px; font-weight: 700;">-</div>
                </div>
                <div class="stat-card" style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 16px;">
                    <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 4px;">Violations (24h)</div>
                    <div id="admin-stat-violations" style="font-size: 24px; font-weight: 700; color: var(--danger);">-</div>
                </div>
                <div class="stat-card" style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 16px;">
                    <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 4px;">Banned</div>
                    <div id="admin-stat-banned" style="font-size: 24px; font-weight: 700; color: var(--danger);">-</div>
                </div>
            </div>
            
            <!-- Broadcast Toggle -->
            <div class="admin-section" style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 24px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h3 style="font-size: 16px; font-weight: 600; margin-bottom: 4px;">Signal Broadcast</h3>
                        <p style="font-size: 13px; color: var(--text-secondary);">Enable or disable global signal broadcasting</p>
                    </div>
                    <label class="toggle-switch" style="position: relative; display: inline-block; width: 50px; height: 26px;">
                        <input type="checkbox" id="broadcast-toggle" onchange="toggleBroadcast(this.checked)" style="opacity: 0; width: 0; height: 0;">
                        <span class="toggle-slider" style="position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: var(--border); transition: .3s; border-radius: 26px;"></span>
                    </label>
                </div>
            </div>
            
            <!-- Users Table -->
            <div class="admin-section" style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 24px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                    <h3 style="font-size: 16px; font-weight: 600;">Users</h3>
                    <input type="text" id="admin-user-search" placeholder="Search users..." oninput="searchAdminUsers(this.value)" style="padding: 8px 12px; border: 1px solid var(--border); border-radius: 6px; font-size: 13px; background: var(--bg); color: var(--text); width: 200px;">
                </div>
                <div style="overflow-x: auto;">
                    <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                        <thead>
                            <tr style="border-bottom: 1px solid var(--border);">
                                <th style="text-align: left; padding: 10px 8px; color: var(--text-muted); font-weight: 500;">Email</th>
                                <th style="text-align: left; padding: 10px 8px; color: var(--text-muted); font-weight: 500;">Name</th>
                                <th style="text-align: left; padding: 10px 8px; color: var(--text-muted); font-weight: 500;">Organization</th>
                                <th style="text-align: left; padding: 10px 8px; color: var(--text-muted); font-weight: 500;">Layer</th>
                                <th style="text-align: left; padding: 10px 8px; color: var(--text-muted); font-weight: 500;">Status</th>
                                <th style="text-align: right; padding: 10px 8px; color: var(--text-muted); font-weight: 500;">Actions</th>
                            </tr>
                        </thead>
                        <tbody id="admin-users-table">
                            <tr><td colspan="6" style="padding: 20px; text-align: center; color: var(--text-muted);">Loading...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
            
            <!-- Violations Log -->
            <div class="admin-section" style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 20px;">
                <h3 style="font-size: 16px; font-weight: 600; margin-bottom: 16px;">Rate Limit Violations</h3>
                <div style="overflow-x: auto;">
                    <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                        <thead>
                            <tr style="border-bottom: 1px solid var(--border);">
                                <th style="text-align: left; padding: 10px 8px; color: var(--text-muted); font-weight: 500;">Time</th>
                                <th style="text-align: left; padding: 10px 8px; color: var(--text-muted); font-weight: 500;">Organization</th>
                                <th style="text-align: left; padding: 10px 8px; color: var(--text-muted); font-weight: 500;">IP</th>
                                <th style="text-align: left; padding: 10px 8px; color: var(--text-muted); font-weight: 500;">Type</th>
                                <th style="text-align: left; padding: 10px 8px; color: var(--text-muted); font-weight: 500;">Endpoint</th>
                            </tr>
                        </thead>
                        <tbody id="admin-violations-table">
                            <tr><td colspan="5" style="padding: 20px; text-align: center; color: var(--text-muted);">No violations</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

    </main>`;

const oldMainClose = `    </main>`;

if (content.includes(oldMainClose) && !content.includes('page-admin')) {
    content = content.replace(oldMainClose, adminPageHTML);
    console.log('✓ Patch 2: Added Admin page HTML');
} else {
    console.log('⚠ Patch 2: Already patched or structure changed');
}

// ============================================================
// PATCH 3: Add toggle switch CSS
// ============================================================

const toggleCSS = `
/* Toggle Switch */
.toggle-switch input:checked + .toggle-slider { background-color: var(--accent); }
.toggle-slider:before { position: absolute; content: ""; height: 20px; width: 20px; left: 3px; bottom: 3px; background-color: white; transition: .3s; border-radius: 50%; }
.toggle-switch input:checked + .toggle-slider:before { transform: translateX(24px); }
`;

const cssInsertPoint = `*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }`;

if (content.includes(cssInsertPoint) && !content.includes('.toggle-switch input:checked')) {
    content = content.replace(cssInsertPoint, cssInsertPoint + toggleCSS);
    console.log('✓ Patch 3: Added toggle switch CSS');
} else {
    console.log('⚠ Patch 3: Already patched');
}

// ============================================================
// PATCH 4: Add Admin JavaScript functions before closing </script>
// ============================================================

const adminJS = `

// ============================================================
// ADMIN PANEL FUNCTIONS
// ============================================================

const API_BASE = 'https://api.ontostandard.org';
let adminApiKey = null;

async function loadAdminData() {
    if (!adminApiKey) {
        adminApiKey = prompt('Enter your Admin API Key:');
        if (!adminApiKey) return;
        localStorage.setItem('onto_admin_key', adminApiKey);
    }
    
    try {
        // Load stats
        const statsRes = await fetch(API_BASE + '/v1/admin/stats', {
            headers: { 'x-api-key': adminApiKey }
        });
        
        if (statsRes.status === 403) {
            showToast('Access denied. Superadmin required.', 'error');
            adminApiKey = null;
            localStorage.removeItem('onto_admin_key');
            return;
        }
        
        const stats = await statsRes.json();
        document.getElementById('admin-stat-orgs').textContent = stats.organizations || 0;
        document.getElementById('admin-stat-users').textContent = stats.users || 0;
        document.getElementById('admin-stat-keys').textContent = stats.api_keys || 0;
        document.getElementById('admin-stat-violations').textContent = stats.violations_today || 0;
        document.getElementById('admin-stat-banned').textContent = stats.banned_organizations || 0;
        
        // Load broadcast status
        const broadcastRes = await fetch(API_BASE + '/v1/admin/broadcast', {
            headers: { 'x-api-key': adminApiKey }
        });
        const broadcast = await broadcastRes.json();
        document.getElementById('broadcast-toggle').checked = broadcast.broadcast_enabled;
        
        // Load users
        await loadAdminUsers();
        
        // Load violations
        await loadAdminViolations();
        
    } catch (err) {
        console.error('Admin load error:', err);
        showToast('Failed to load admin data', 'error');
    }
}

async function loadAdminUsers(search = '') {
    try {
        const url = search 
            ? API_BASE + '/v1/admin/users?search=' + encodeURIComponent(search)
            : API_BASE + '/v1/admin/users';
            
        const res = await fetch(url, {
            headers: { 'x-api-key': adminApiKey }
        });
        const data = await res.json();
        
        const tbody = document.getElementById('admin-users-table');
        if (!data.users || data.users.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="padding: 20px; text-align: center; color: var(--text-muted);">No users found</td></tr>';
            return;
        }
        
        tbody.innerHTML = data.users.map(u => \`
            <tr style="border-bottom: 1px solid var(--border);">
                <td style="padding: 10px 8px;">\${u.email}</td>
                <td style="padding: 10px 8px;">\${u.name}</td>
                <td style="padding: 10px 8px;">\${u.organization?.name || '-'}</td>
                <td style="padding: 10px 8px;">
                    <span style="padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 500; background: \${u.organization?.tier === 'critical' ? 'var(--danger-subtle)' : u.organization?.tier === 'standard' ? 'var(--blue-subtle)' : 'var(--bg-elevated)'}; color: \${u.organization?.tier === 'critical' ? 'var(--danger)' : u.organization?.tier === 'standard' ? 'var(--blue)' : 'var(--text-secondary)'};">
                        \${(u.organization?.tier || 'open').toUpperCase()}
                    </span>
                </td>
                <td style="padding: 10px 8px;">
                    \${u.organization?.is_banned 
                        ? '<span style="color: var(--danger);">Banned</span>' 
                        : '<span style="color: var(--accent);">Active</span>'}
                </td>
                <td style="padding: 10px 8px; text-align: right;">
                    \${u.organization?.is_banned
                        ? \`<button onclick="adminUnbanUser('\${u.id}')" style="padding: 4px 10px; font-size: 12px; border: 1px solid var(--accent); background: transparent; color: var(--accent); border-radius: 4px; cursor: pointer;">Unban</button>\`
                        : \`<button onclick="adminBanUser('\${u.id}')" style="padding: 4px 10px; font-size: 12px; border: 1px solid var(--danger); background: transparent; color: var(--danger); border-radius: 4px; cursor: pointer;">Ban</button>\`}
                    <button onclick="adminExportOrg('\${u.organization?.id}')" style="padding: 4px 10px; font-size: 12px; border: 1px solid var(--border); background: transparent; color: var(--text-secondary); border-radius: 4px; cursor: pointer; margin-left: 4px;">Export</button>
                </td>
            </tr>
        \`).join('');
        
    } catch (err) {
        console.error('Load users error:', err);
    }
}

async function loadAdminViolations() {
    try {
        const res = await fetch(API_BASE + '/v1/admin/violations?limit=50', {
            headers: { 'x-api-key': adminApiKey }
        });
        const data = await res.json();
        
        const tbody = document.getElementById('admin-violations-table');
        if (!data.violations || data.violations.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="padding: 20px; text-align: center; color: var(--text-muted);">No violations</td></tr>';
            return;
        }
        
        tbody.innerHTML = data.violations.map(v => \`
            <tr style="border-bottom: 1px solid var(--border);">
                <td style="padding: 10px 8px; font-size: 12px;">\${new Date(v.created_at).toLocaleString()}</td>
                <td style="padding: 10px 8px;">\${v.organization_name || '-'}</td>
                <td style="padding: 10px 8px; font-family: monospace; font-size: 12px;">\${v.ip_address || '-'}</td>
                <td style="padding: 10px 8px;">\${v.violation_type}</td>
                <td style="padding: 10px 8px; font-family: monospace; font-size: 12px;">\${v.endpoint || '-'}</td>
            </tr>
        \`).join('');
        
    } catch (err) {
        console.error('Load violations error:', err);
    }
}

function searchAdminUsers(query) {
    clearTimeout(window.adminSearchTimeout);
    window.adminSearchTimeout = setTimeout(() => {
        loadAdminUsers(query);
    }, 300);
}

async function toggleBroadcast(enabled) {
    try {
        await fetch(API_BASE + '/v1/admin/broadcast?enabled=' + enabled, {
            method: 'POST',
            headers: { 'x-api-key': adminApiKey }
        });
        showToast('Broadcast ' + (enabled ? 'enabled' : 'disabled'), 'success');
    } catch (err) {
        showToast('Failed to toggle broadcast', 'error');
    }
}

async function adminBanUser(userId) {
    if (!confirm('Ban this user\\'s organization?')) return;
    
    try {
        await fetch(API_BASE + '/v1/admin/users/' + userId + '/ban', {
            method: 'POST',
            headers: { 'x-api-key': adminApiKey }
        });
        showToast('User banned', 'success');
        loadAdminUsers();
        loadAdminData();
    } catch (err) {
        showToast('Failed to ban user', 'error');
    }
}

async function adminUnbanUser(userId) {
    if (!confirm('Unban this user\\'s organization?')) return;
    
    try {
        await fetch(API_BASE + '/v1/admin/users/' + userId + '/unban', {
            method: 'POST',
            headers: { 'x-api-key': adminApiKey }
        });
        showToast('User unbanned', 'success');
        loadAdminUsers();
        loadAdminData();
    } catch (err) {
        showToast('Failed to unban user', 'error');
    }
}

async function adminExportOrg(orgId) {
    if (!orgId) {
        showToast('No organization ID', 'error');
        return;
    }
    
    try {
        const res = await fetch(API_BASE + '/v1/admin/export/' + orgId, {
            headers: { 'x-api-key': adminApiKey }
        });
        const data = await res.json();
        
        // Download as JSON
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'org-export-' + orgId + '.json';
        a.click();
        URL.revokeObjectURL(url);
        
        showToast('Export downloaded', 'success');
    } catch (err) {
        showToast('Failed to export', 'error');
    }
}

// Show admin nav if superadmin
function checkAdminAccess() {
    const savedKey = localStorage.getItem('onto_admin_key');
    if (savedKey) {
        adminApiKey = savedKey;
        document.querySelector('.admin-nav-item').style.display = 'flex';
    }
}

// Override showPage to load admin data
const originalShowPage = showPage;
showPage = function(page, el) {
    originalShowPage(page, el);
    if (page === 'admin') {
        loadAdminData();
    }
};

// Check admin on load
document.addEventListener('DOMContentLoaded', checkAdminAccess);
`;

const scriptCloseTag = `</script>
</body>`;

if (content.includes(scriptCloseTag) && !content.includes('loadAdminData')) {
    content = content.replace(scriptCloseTag, adminJS + '\n</script>\n</body>');
    console.log('✓ Patch 4: Added Admin JavaScript');
} else {
    console.log('⚠ Patch 4: Already patched');
}

// ============================================================
// Save patched file
// ============================================================

fs.writeFileSync(portalPath, content);
console.log('\n✅ Portal patched with Admin Panel!\n');
console.log('Next steps:');
console.log('1. cd C:\\ONTO');
console.log('2. git add docs/app/index.html');
console.log('3. git commit -m "Add Admin Panel to portal"');
console.log('4. git push origin main');
console.log('\nTo access Admin Panel:');
console.log('1. Login to portal');
console.log('2. Click Admin Panel in sidebar');
console.log('3. Enter your admin API key when prompted');
