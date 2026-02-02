const { Client } = require('pg');
const crypto = require('crypto');

const client = new Client({
  connectionString: 'postgresql://postgres:wmTlABjoAdpPKgwWtBDLkQoZvXvjkDcv@shortline.proxy.rlwy.net:52797/railway'
});

async function run() {
  await client.connect();
  
  const newPassword = 'onaknhgaekniomevto';
  const hash = crypto.createHash('sha256').update(newPassword).digest('hex');
  
  await client.query(
    "UPDATE users SET password_hash = $1 WHERE email = 'aristokratrom@gmail.com'",
    [hash]
  );
  
  console.log('Password changed!');
  await client.end();
}

run().catch(console.error);