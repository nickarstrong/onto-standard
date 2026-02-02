const { Client } = require('pg');

const client = new Client({
  connectionString: 'postgresql://postgres:wmTlABjoAdpPKgwWtBDLkQoZvXvjkDcv@shortline.proxy.rlwy.net:52797/railway'
});

async function run() {
  await client.connect();
  
  const res = await client.query('SELECT id, email, name, role FROM users');
  console.log('Users in database:', res.rows);
  
  await client.end();
}

run().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});