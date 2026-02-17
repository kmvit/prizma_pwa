#!/usr/bin/env python3
"""Загрузка вопросов в БД. Запуск: python -m app.database.seed_data"""

import asyncio
import json
from pathlib import Path

from sqlalchemy import delete

from app.database.database import init_db, async_session
from app.database.models import Question, QuestionType


async def load_questions():
    data_dir = Path(__file__).parent.parent.parent / "data"
    free_path = data_dir / "questions_free.json"
    premium_path = data_dir / "questions_premium.json"

    all_questions = []
    with open(free_path, "r", encoding="utf-8") as f:
        free_data = json.load(f)
    free_questions = free_data["questions"]
    all_questions.extend(free_questions)

    with open(premium_path, "r", encoding="utf-8") as f:
        premium_data = json.load(f)
    premium_questions = premium_data["questions"]
    all_questions.extend(premium_questions)

    async with async_session() as session:
        await session.execute(delete(Question))
        current_order = 1
        for q in free_questions:
            session.add(Question(
                text=q["text"],
                type=QuestionType.FREE,
                test_version="free",
                order_number=current_order,
                allow_voice=q.get("allow_voice", True),
                max_length=q.get("max_length", 1000)
            ))
            current_order += 1
        for q in premium_questions:
            session.add(Question(
                text=q["text"],
                type=QuestionType.PAID,
                test_version="premium",
                order_number=current_order,
                allow_voice=q.get("allow_voice", True),
                max_length=q.get("max_length", 1000)
            ))
            current_order += 1
        await session.commit()
    print("Questions loaded:", len(all_questions))


async def main():
    await init_db()
    await load_questions()


if __name__ == "__main__":
    asyncio.run(main())
