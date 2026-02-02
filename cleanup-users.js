const { Client } = require('pg');

const client = new Client({
  connectionString: 'postgresql://postgres:wmTlABjoAdpPKgwWtBDLkQoZvXvjkDcv@shortline.proxy.rlwy.net:52797/railway'
});

async function run() {
  await client.connect();
  console.log('Connected to database');
  
  // Удаляем в правильном порядке (из-за foreign keys)
  await client.query('DELETE FROM audit_log');
  console.log('Deleted audit_log');
  
  await client.query('DELETE FROM api_keys');
  console.log('Deleted api_keys');
  
  await client.query('DELETE FROM certificates');
  console.log('Deleted certificates');
  
  await client.query('DELETE FROM evaluations');
  console.log('Deleted evaluations');
  
  await client.query('DELETE FROM subscriptions');
  console.log('Deleted subscriptions');
  
  await client.query('DELETE FROM usage_events');
  console.log('Deleted usage_events');
  
  await client.query('DELETE FROM users');
  console.log('Deleted users');
  
  await client.query('DELETE FROM organizations');
  console.log('Deleted organizations');
  
  // Проверка
  const res = await client.query('SELECT COUNT(*) FROM users');
  console.log('Users remaining:', res.rows[0].count);
  
  await client.end();
  console.log('Cleanup completed!');
}

run().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});