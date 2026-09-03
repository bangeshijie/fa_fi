# database.py
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.database import  async_db_session



async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI依赖注入：获取异步数据库会话"""
    async with async_db_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


