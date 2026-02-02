const { Client } = require('pg');
const crypto = require('crypto');

const client = new Client({
  connectionString: 'postgresql://postgres:wmTlABjoAdpPKgwWtBDLkQoZvXvjkDcv@shortline.proxy.rlwy.net:52797/railway'
});

async function run() {
  await client.connect();
  console.log('Connected to database');
  
  // Создаём организацию
  const orgId = crypto.randomUUID();
  await client.query(`
    INSERT INTO organizations (id, name, slug, tier) 
    VALUES ($1, 'ONTO Admin', 'onto-admin', 'critical')
  `, [orgId]);
  console.log('Organization created');
  
  // Хэш пароля (SHA256 как в app.py)
  const password = 'OntoAdmin2026!';
  const passwordHash = crypto.createHash('sha256').update(password).digest('hex');
  
  // Создаём superadmin пользователя
  const userId = crypto.randomUUID();
  await client.query(`
    INSERT INTO users (id, email, name, password_hash, organization_id, role, is_active) 
    VALUES ($1, $2, $3, $4, $5, 'superadmin', true)
  `, [userId, 'aristokratrom@gmail.com', 'Tommy', passwordHash, orgId]);
  console.log('Superadmin user created');
  
  // Проверка
  const res = await client.query("SELECT email, role FROM users WHERE role = 'superadmin'");
  console.log('Superadmin:', res.rows[0]);
  
  console.log('\n=== LOGIN CREDENTIALS ===');
  console.log('Email: aristokratrom@gmail.com');
  console.log('Password: OntoAdmin2026!');
  console.log('=========================\n');
  
  await client.end();
}

run().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});