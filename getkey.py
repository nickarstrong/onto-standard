import asyncio, asyncpg
async def main():
    url = input('DATABASE_URL: ')
    conn = await asyncpg.connect(url)
    row = await conn.fetchrow("SELECT provider_api_key FROM models WHERE id='552f8fac-c2c7-43a6-b181-60dba480b0e8'")
    print(row['provider_api_key'] if row else 'Not found')
    await conn.close()
asyncio.run(main())
