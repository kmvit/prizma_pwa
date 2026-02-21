from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.config import DATABASE_URL, SQL_ECHO
from app.database.models import Base

engine = create_async_engine(
    DATABASE_URL,
    echo=SQL_ECHO,
    poolclass=NullPool
)

async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def _run_migrations(conn):
    """Миграция: добавление колонок для Telegram-авторизации"""
    from sqlalchemy import text
    result = await conn.execute(text("PRAGMA table_info(users)"))
    existing = {row[1] for row in result.fetchall()}
    for col, col_type in [
        ("telegram_id", "BIGINT"),
        ("telegram_username", "VARCHAR(100)"),
    ]:
        if col not in existing:
            await conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} {col_type}"))


async def init_db():
    """Инициализация базы данных"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _run_migrations(conn)
