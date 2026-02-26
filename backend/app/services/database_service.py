from typing import Optional, List
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
import glob
from pathlib import Path

from app.database.models import User, Question, Answer, Payment, Report, PushSubscription, QuestionType, PaymentStatus, ReportGenerationStatus
from app.database.database import async_session
from app.config import FREE_QUESTIONS_LIMIT, PREMIUM_QUESTIONS_COUNT
from loguru import logger


class DatabaseService:
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Получить пользователя по email"""
        async with async_session() as session:
            stmt = select(User).where(User.email == email)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID"""
        async with async_session() as session:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Получить пользователя по Telegram ID"""
        async with async_session() as session:
            stmt = select(User).where(User.telegram_id == telegram_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def create_user(self, email: str, password_hash: str, name: Optional[str] = None) -> User:
        """Создать нового пользователя"""
        async with async_session() as session:
            user = User(
                email=email,
                password_hash=password_hash,
                name=name
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

    async def create_telegram_user(
        self,
        telegram_id: int,
        first_name: str,
        last_name: Optional[str] = None,
        username: Optional[str] = None,
    ) -> User:
        """Создать пользователя при первом входе через Telegram"""
        from app.auth.auth import hash_password
        email = f"tg_{telegram_id}@prizma.telegram"
        name = f"{first_name} {last_name or ''}".strip() or first_name
        async with async_session() as session:
            user = User(
                email=email,
                password_hash=hash_password(str(telegram_id)),  # placeholder, не используется
                name=name,
                telegram_id=telegram_id,
                telegram_username=username,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

    async def update_user_profile(self, user_id: int, name: Optional[str] = None, age: Optional[int] = None, gender: Optional[str] = None) -> User:
        """Обновить профиль пользователя"""
        async with async_session() as session:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one()
            if name is not None:
                user.name = name
            if age is not None:
                user.age = age
            if gender is not None:
                user.gender = gender
            user.updated_at = datetime.utcnow()
            await session.commit()
            return user

    async def update_user(self, user_id: int, update_data: dict) -> User:
        """Обновить пользователя с произвольными полями"""
        async with async_session() as session:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one()
            for field, value in update_data.items():
                if hasattr(user, field):
                    setattr(user, field, value)
            user.updated_at = datetime.utcnow()
            await session.commit()
            return user

    async def start_test(self, user_id: int) -> User:
        """Начать тест для пользователя"""
        async with async_session() as session:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one()
            if user.test_completed and not user.current_question_id:
                return user
            if user.current_question_id:
                return user
            first_question = await self.get_first_question()
            user.current_question_id = first_question.id
            user.test_started_at = datetime.utcnow()
            user.test_completed = False
            user.test_completed_at = None
            await session.commit()
            return user

    async def complete_test(self, user_id: int, test_version: str = "free") -> User:
        """Завершить тест для пользователя"""
        async with async_session() as session:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one()
            reports_dir = Path("reports")
            reports_dir.mkdir(exist_ok=True)
            if test_version == "free":
                pattern = str(reports_dir / f"prizma_report_{user_id}_*.pdf")
                for old_report in glob.glob(pattern):
                    try:
                        Path(old_report).unlink()
                    except Exception as e:
                        logger.warning(f"Не удалось удалить старый отчет {old_report}: {e}")
                user.free_test_completed = True
                user.current_free_question_id = None
            else:
                pattern = str(reports_dir / f"prizma_premium_report_{user_id}_*.pdf")
                for old_report in glob.glob(pattern):
                    try:
                        Path(old_report).unlink()
                    except Exception as e:
                        logger.warning(f"Не удалось удалить старый отчет {old_report}: {e}")
                user.premium_test_completed = True
                user.current_premium_question_id = None
            user.test_completed = True
            user.test_completed_at = datetime.utcnow()
            user.current_question_id = None
            await session.commit()
            return user

    async def upgrade_to_premium_and_continue_test(self, user_id: int) -> User:
        """Обновить до премиум и продолжить тест"""
        async with async_session() as session:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one()
            user.is_paid = True
            user.is_premium_paid = True
            user.test_completed = False
            user.test_completed_at = None
            answers = await self.get_user_answers(user_id)
            if answers:
                answered = [a for a in answers if a.question]
                if answered:
                    last_q = max(answered, key=lambda x: x.question.order_number)
                    next_q = await self.get_next_question(last_q.question_id, "premium")
                    if next_q:
                        user.current_question_id = next_q.id
                    else:
                        user.test_completed = True
                        user.test_completed_at = datetime.utcnow()
            user.updated_at = datetime.utcnow()
            await session.commit()
            return user

    async def update_user_test_status(self, user_id: int, test_completed: bool) -> User:
        async with async_session() as session:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one()
            user.test_completed = test_completed
            user.test_completed_at = datetime.utcnow() if test_completed else None
            user.updated_at = datetime.utcnow()
            await session.commit()
            return user

    async def get_first_question(self, test_version: str = "free") -> Question:
        async with async_session() as session:
            from sqlalchemy import and_
            stmt = select(Question).where(
                and_(Question.is_active == True, Question.test_version == test_version)
            ).order_by(Question.order_number).limit(1)
            result = await session.execute(stmt)
            return result.scalar_one()

    async def get_question(self, question_id: int) -> Optional[Question]:
        async with async_session() as session:
            stmt = select(Question).where(Question.id == question_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_next_question(self, current_question_id: int, test_version: str = "free") -> Optional[Question]:
        async with async_session() as session:
            from sqlalchemy import and_
            curr = await self.get_question(current_question_id)
            if not curr:
                return None
            stmt = select(Question).where(
                and_(
                    Question.order_number > curr.order_number,
                    Question.is_active == True,
                    Question.test_version == test_version
                )
            ).order_by(Question.order_number).limit(1)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_total_questions(self, test_version: str = "free") -> int:
        return FREE_QUESTIONS_LIMIT if test_version == "free" else PREMIUM_QUESTIONS_COUNT

    async def save_answer(self, user_id: int, question_id: int, text_answer: str = None,
                         voice_file_id: str = None, answer_type: str = "text") -> Answer:
        async with async_session() as session:
            answer = Answer(
                user_id=user_id,
                question_id=question_id,
                text_answer=text_answer,
                voice_file_id=voice_file_id,
                answer_type=answer_type
            )
            session.add(answer)
            await session.commit()
            await session.refresh(answer)
            return answer

    async def clear_user_answers(self, user_id: int) -> int:
        async with async_session() as session:
            stmt = delete(Answer).where(Answer.user_id == user_id)
            result = await session.execute(stmt)
            deleted = result.rowcount
            await session.commit()
            return deleted

    async def get_user_answers(self, user_id: int) -> List[Answer]:
        async with async_session() as session:
            stmt = select(Answer).options(selectinload(Answer.question)).where(
                Answer.user_id == user_id
            ).order_by(Answer.created_at)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_user_answers_by_test_version(self, user_id: int, test_version: str) -> List[Answer]:
        async with async_session() as session:
            from sqlalchemy import and_
            stmt = (
                select(Answer)
                .options(selectinload(Answer.question))
                .join(Question, Answer.question_id == Question.id)
                .where(
                    Answer.user_id == user_id,
                    Question.test_version == test_version,
                    Question.is_active == True
                )
                .order_by(Question.order_number)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def create_payment(self, uid: int, amount: int, currency: str, description: str,
                             invoice_id: str, status: PaymentStatus) -> Payment:
        """amount - сумма в копейках (int)"""
        async with async_session() as session:
            payment = Payment(
                user_id=uid,
                amount=amount,
                currency=currency,
                description=description,
                invoice_id=invoice_id,
                status=status
            )
            session.add(payment)
            await session.commit()
            await session.refresh(payment)
            return payment

    async def get_payment_by_invoice_id(self, invoice_id: str) -> Optional[Payment]:
        async with async_session() as session:
            stmt = select(Payment).where(Payment.invoice_id == invoice_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_payment_by_id(self, payment_id: int) -> Optional[Payment]:
        async with async_session() as session:
            stmt = select(Payment).where(Payment.id == payment_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def update_payment_status(self, payment_id: int, status: PaymentStatus,
                                    robokassa_payment_id: str = None) -> Payment:
        async with async_session() as session:
            stmt = select(Payment).where(Payment.id == payment_id)
            result = await session.execute(stmt)
            payment = result.scalar_one()
            payment.status = status
            if robokassa_payment_id:
                payment.robokassa_payment_id = robokassa_payment_id
            if status == PaymentStatus.COMPLETED:
                payment.paid_at = datetime.utcnow()
            await session.commit()
            return payment

    async def update_report_generation_status(self, user_id: int, report_type: str,
                                             status: ReportGenerationStatus,
                                             report_path: str = None, error: str = None) -> User:
        async with async_session() as session:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one()
            if report_type == "free":
                user.free_report_status = status
                if report_path:
                    user.free_report_path = report_path
            elif report_type == "premium":
                user.premium_report_status = status
                if report_path:
                    user.premium_report_path = report_path
            if error:
                user.report_generation_error = error
            if status == ReportGenerationStatus.PROCESSING:
                user.report_generation_started_at = datetime.utcnow()
            elif status in (ReportGenerationStatus.COMPLETED, ReportGenerationStatus.FAILED):
                user.report_generation_completed_at = datetime.utcnow()
            user.updated_at = datetime.utcnow()
            await session.commit()
            return user

    async def get_report_generation_status(self, user_id: int, report_type: str) -> dict:
        user = await self.get_user_by_id(user_id)
        if not user:
            return {"status": "user_not_found"}
        if report_type == "free":
            return {
                "status": user.free_report_status.value,
                "report_path": user.free_report_path,
                "error": user.report_generation_error,
                "started_at": user.report_generation_started_at,
                "completed_at": user.report_generation_completed_at
            }
        elif report_type == "premium":
            return {
                "status": user.premium_report_status.value,
                "report_path": user.premium_report_path,
                "error": user.report_generation_error,
                "started_at": user.report_generation_started_at,
                "completed_at": user.report_generation_completed_at
            }
        return {"status": "invalid_report_type"}

    async def is_report_generating(self, user_id: int, report_type: str) -> bool:
        info = await self.get_report_generation_status(user_id, report_type)
        return info.get("status") == ReportGenerationStatus.PROCESSING.value

    async def reset_stuck_reports(self, user_id: int) -> bool:
        user = await self.get_user_by_id(user_id)
        if not user or not user.report_generation_started_at:
            return False
        diff = datetime.utcnow() - user.report_generation_started_at
        if diff <= timedelta(minutes=10):
            return False
        update_data = {}
        if user.free_report_status == ReportGenerationStatus.PROCESSING:
            update_data["free_report_status"] = ReportGenerationStatus.PENDING
            update_data["free_report_path"] = None
            update_data["report_generation_error"] = "Отчет завис"
        if user.premium_report_status == ReportGenerationStatus.PROCESSING:
            update_data["premium_report_status"] = ReportGenerationStatus.PENDING
            update_data["premium_report_path"] = None
            update_data["report_generation_error"] = "Отчет завис"
        if update_data:
            await self.update_user(user_id, update_data)
        return True

    async def get_questions_by_version(self, test_version: str) -> List[Question]:
        async with async_session() as session:
            from sqlalchemy import and_
            stmt = select(Question).where(
                and_(Question.is_active == True, Question.test_version == test_version)
            ).order_by(Question.order_number)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def save_push_subscription(self, user_id: int, endpoint: str, p256dh: str, auth: str) -> PushSubscription:
        """Сохранить или обновить push-подписку (по endpoint — одно устройство может переподписываться)"""
        async with async_session() as session:
            stmt = select(PushSubscription).where(
                PushSubscription.user_id == user_id,
                PushSubscription.endpoint == endpoint,
            )
            result = await session.execute(stmt)
            sub = result.scalar_one_or_none()
            if sub:
                sub.p256dh = p256dh
                sub.auth = auth
            else:
                sub = PushSubscription(
                    user_id=user_id,
                    endpoint=endpoint,
                    p256dh=p256dh,
                    auth=auth,
                )
                session.add(sub)
            await session.commit()
            await session.refresh(sub)
            return sub

    async def get_push_subscriptions(self, user_id: int) -> List[PushSubscription]:
        """Получить все push-подписки пользователя"""
        async with async_session() as session:
            stmt = select(PushSubscription).where(PushSubscription.user_id == user_id)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def delete_push_subscription(self, user_id: int, endpoint: str) -> bool:
        """Удалить push-подписку по endpoint"""
        async with async_session() as session:
            stmt = delete(PushSubscription).where(
                PushSubscription.user_id == user_id,
                PushSubscription.endpoint == endpoint,
            )
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0


db_service = DatabaseService()
