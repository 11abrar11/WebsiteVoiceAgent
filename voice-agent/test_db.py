import asyncio
from app.database.connection import engine
from sqlalchemy import text

async def test_db():
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("DB Connection OK:", result.scalar())
    except Exception as e:
        print("DB Connection Failed:", e)

asyncio.run(test_db())
