const { Client } = require('pg');
const crypto = require('crypto');

const client = new Client({
  connectionString: 'postgresql://postgres:wmTlABjoAdpPKgwWtBDLkQoZvXvjkDcv@shortline.proxy.rlwy.net:52797/railway'
});

async function run() {
  await client.connect();
  
  const user = await client.query(
    "SELECT organization_id FROM users WHERE role = 'superadmin' LIMIT 1"
  );
  
  if (user.rows.length === 0) {
    console.log('No superadmin found');
    return;
  }
  
  const orgId = user.rows[0].organization_id;
  
  const randomPart = crypto.randomBytes(24).toString('hex');
  const fullKey = `onto_${randomPart}`;
  const prefix = `onto_${randomPart.slice(0, 4)}`;
  const keyHash = crypto.createHash('sha256').update(fullKey).digest('hex');
  
  await client.query(`
    INSERT INTO api_keys (organization_id, name, key_hash, key_prefix, scopes, is_active)
    VALUES ($1, 'Admin Key', $2, $3, '{"read", "write", "admin"}', true)
  `, [orgId, keyHash, prefix]);
  
  console.log('\n=== ADMIN API KEY ===');
  console.log(fullKey);
  console.log('=====================\n');
  
  await client.end();
}

run().catch(console.error);