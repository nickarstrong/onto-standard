const { Client } = require('pg');

const client = new Client({
  connectionString: 'postgresql://postgres:wmTlABjoAdpPKgwWtBDLkQoZvXvjkDcv@shortline.proxy.rlwy.net:52797/railway'
});

async function run() {
  await client.connect();
  console.log('Connected to database');
  
  const res = await client.query(
    "UPDATE users SET role = 'superadmin' WHERE email = 'aristokratrom@gmail.com' RETURNING id, email, role"
  );
  
  if (res.rowCount > 0) {
    console.log('Superadmin set:', res.rows[0]);
  } else {
    console.log('User not found. Register first at onto.uz/app/');
  }
  
  await client.end();
}

run().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});