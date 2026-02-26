from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum

Base = declarative_base()


class QuestionType(Enum):
    FREE = "free"
    PAID = "paid"


class PaymentStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ReportGenerationStatus(Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=True)
    telegram_username = Column(String(100), nullable=True)

    # Дополнительная информация профиля
    name = Column(String(100), nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True)

    # Статусы и настройки
    is_paid = Column(Boolean, default=False)
    is_premium_paid = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    current_question_id = Column(Integer, ForeignKey("questions.id"), nullable=True)
    test_completed = Column(Boolean, default=False)

    # Раздельное отслеживание прогресса free/premium тестов
    free_test_completed = Column(Boolean, default=False)
    premium_test_completed = Column(Boolean, default=False)
    current_free_question_id = Column(Integer, nullable=True)
    current_premium_question_id = Column(Integer, nullable=True)

    # Статусы генерации отчетов
    free_report_status = Column(SQLEnum(ReportGenerationStatus), default=ReportGenerationStatus.PENDING)
    premium_report_status = Column(SQLEnum(ReportGenerationStatus), default=ReportGenerationStatus.PENDING)

    # Пути к готовым отчетам
    free_report_path = Column(String(500), nullable=True)
    premium_report_path = Column(String(500), nullable=True)

    # Ошибки генерации
    report_generation_error = Column(Text, nullable=True)

    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    test_started_at = Column(DateTime, nullable=True)
    test_completed_at = Column(DateTime, nullable=True)
    report_generation_started_at = Column(DateTime, nullable=True)
    report_generation_completed_at = Column(DateTime, nullable=True)

    # Таймер спецпредложения
    special_offer_started_at = Column(DateTime, nullable=True)

    # Флаги отправленных уведомлений по таймеру спецпредложения
    notification_6_hours_sent = Column(Boolean, default=False)
    notification_1_hour_sent = Column(Boolean, default=False)
    notification_10_minutes_sent = Column(Boolean, default=False)

    # Связи
    answers = relationship("Answer", back_populates="user")
    payments = relationship("Payment", back_populates="user")
    push_subscriptions = relationship("PushSubscription", back_populates="user", cascade="all, delete-orphan")
    current_question = relationship("Question", foreign_keys=[current_question_id])


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    type = Column(SQLEnum(QuestionType), nullable=False, default=QuestionType.FREE)
    order_number = Column(Integer, nullable=False, unique=True)
    test_version = Column(String(20), default="free")
    is_active = Column(Boolean, default=True)
    allow_voice = Column(Boolean, default=True)
    max_length = Column(Integer, default=1000)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    answers = relationship("Answer", back_populates="question")


class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    text_answer = Column(Text, nullable=True)
    voice_file_id = Column(String(200), nullable=True)
    ai_analysis = Column(Text, nullable=True)
    analysis_status = Column(String(20), default="pending")
    answer_type = Column(String(20), default="text")
    processing_time = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    analyzed_at = Column(DateTime, nullable=True)
    user = relationship("User", back_populates="answers")
    question = relationship("Question", back_populates="answers")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False)
    currency = Column(String(3), default="RUB")
    description = Column(String(255), nullable=True)
    invoice_id = Column(String(100), unique=True, nullable=False)
    robokassa_payment_id = Column(String(100), nullable=True)
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)
    user = relationship("User", back_populates="payments")


class PushSubscription(Base):
    """Web Push подписка пользователя (для уведомлений в PWA)"""

    __tablename__ = "push_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    endpoint = Column(String(1000), nullable=False)
    p256dh = Column(Text, nullable=False)
    auth = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="push_subscriptions")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    pdf_file_path = Column(String(500), nullable=True)
    pdf_file_id = Column(String(200), nullable=True)
    generation_status = Column(String(20), default="pending")
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    generated_at = Column(DateTime, nullable=True)
    user = relationship("User")
