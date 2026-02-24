#!/usr/bin/env python3
"""
Скрипт для очистки базы данных.
Удаляет пользователей и связанные данные, сохраняет вопросы.

Запуск: python clear_database.py
"""

import asyncio
from sqlalchemy import delete, select, func

from app.database.database import async_session, init_db
from app.database.models import User, Answer, Payment, Report
from loguru import logger


async def clear_database():
    """Очистка всех пользовательских данных (сохраняем вопросы)"""
    try:
        await init_db()
        logger.info("🧹 Начинаем очистку базы данных...")

        async with async_session() as session:
            users_count = await session.scalar(select(func.count()).select_from(User))
            answers_count = await session.scalar(select(func.count()).select_from(Answer))
            payments_count = await session.scalar(select(func.count()).select_from(Payment))
            reports_count = await session.scalar(select(func.count()).select_from(Report))

            logger.info(
                f"📊 Найдено: users={users_count}, answers={answers_count}, "
                f"payments={payments_count}, reports={reports_count}"
            )

            await session.execute(delete(Answer))
            await session.execute(delete(Payment))
            await session.execute(delete(Report))
            await session.execute(delete(User))
            await session.commit()

            logger.info("✅ База данных очищена (вопросы сохранены)")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(clear_database())
