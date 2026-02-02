const { Client } = require('pg');

const client = new Client({
  connectionString: 'postgresql://postgres:wmTlABjoAdpPKgwWtBDLkQoZvXvjkDcv@shortline.proxy.rlwy.net:52797/railway'
});

const sql = `
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS is_banned BOOLEAN DEFAULT false;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS banned_at TIMESTAMP;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS ban_reason TEXT;

CREATE TABLE IF NOT EXISTS rate_limit_violations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id),
    api_key_id UUID,
    ip_address VARCHAR(50),
    violation_type VARCHAR(50) NOT NULL,
    request_count INT,
    limit_value INT,
    endpoint VARCHAR(255),
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_violations_org ON rate_limit_violations(organization_id);
CREATE INDEX IF NOT EXISTS idx_violations_created ON rate_limit_violations(created_at DESC);

CREATE TABLE IF NOT EXISTS system_settings (
    key VARCHAR(100) PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW(),
    updated_by UUID
);

INSERT INTO system_settings (key, value) VALUES 
    ('broadcast_enabled', 'true'::jsonb),
    ('maintenance_mode', 'false'::jsonb)
ON CONFLICT (key) DO NOTHING;
`;

async function run() {
  await client.connect();
  console.log('Connected to database');
  
  await client.query(sql);
  console.log('Migration completed!');
  
  const res = await client.query('SELECT * FROM system_settings');
  console.log('System settings:', res.rows);
  
  await client.end();
}

run().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});