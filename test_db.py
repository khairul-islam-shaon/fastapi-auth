import asyncio

from sqlalchemy import text

from app.db.session import engine


async def test_connection():
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        print("Database connection OK:", result.scalar())

    await engine.dispose()


asyncio.run(test_connection())