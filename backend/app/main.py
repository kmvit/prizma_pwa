#!/usr/bin/env python3
"""PRIZMA PWA - FastAPI backend"""

import asyncio
import decimal
import glob
import logging
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Response, Cookie
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError
from fastapi.responses import RedirectResponse, FileResponse

from app.auth.auth import (
    get_current_user,
    hash_password,
    verify_password,
    create_session,
    delete_session,
    verify_telegram_auth,
)
from app.config import (
    FRONTEND_URL,
    TELEGRAM_BOT_TOKEN,
    FREE_QUESTIONS_LIMIT,
    PREMIUM_PRICE_ORIGINAL,
    PREMIUM_PRICE_DISCOUNT,
    ROBOKASSA_LOGIN,
    ROBOKASSA_PASSWORD_1,
    ROBOKASSA_PASSWORD_2,
    ROBOKASSA_TEST,
    SESSION_COOKIE_NAME,
    PERPLEXITY_ENABLED,
)
from app.database.database import init_db
from app.database.models import User, ReportGenerationStatus, PaymentStatus
from app.models.api_models import (
    AnswerRequest,
    UserProfileUpdate,
    RegisterRequest,
    LoginRequest,
    QuestionResponse,
    ProgressResponse,
    UserStatusResponse,
    CurrentQuestionResponse,
    NextQuestionResponse,
    UserProgressResponse,
    UserProfileResponse,
)
from app.services.database_service import db_service
from app.services.oplata import RobokassaService
from loguru import logger

app = FastAPI(
    title="PRIZMA API",
    description="API для психологического тестирования с ИИ-анализом",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

@app.on_event("startup")
async def startup():
    await init_db()
    logger.info("Database initialized")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FILES_DIR = Path(__file__).resolve().parent.parent / "files"


@app.get("/api/files/policy")
async def serve_policy():
    """Политика конфиденциальности"""
    path = FILES_DIR / "policy.docx"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Файл не найден")
    return FileResponse(path, filename="politika-konfidencialnosti.docx", media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


@app.get("/api/files/offerta")
async def serve_offerta():
    """Оферта"""
    path = FILES_DIR / "offerta.docx"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Файл не найден")
    return FileResponse(path, filename="offerta.docx", media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


async def update_current_question(user_id: int, question_id: int):
    from sqlalchemy import update as sql_update
    from app.database.database import async_session
    async with async_session() as session:
        stmt = sql_update(User).where(User.id == user_id).values(
            current_question_id=question_id,
            updated_at=datetime.utcnow()
        )
        await session.execute(stmt)
        await session.commit()


# --- Auth ---

@app.post("/api/auth/register")
async def register(data: RegisterRequest):
    existing = await db_service.get_user_by_email(data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")
    try:
        user = await db_service.create_user(
            email=data.email,
            password_hash=hash_password(data.password),
            name=data.name
        )
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")
    sid = create_session(user.id)
    response = Response(status_code=201)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=sid,
        httponly=True,
        samesite="lax",
        max_age=86400 * 30,
    )
    return {"status": "ok", "user": {"id": user.id, "email": user.email, "name": user.name}}


@app.post("/api/auth/login")
async def login(data: LoginRequest, response: Response):
    user = await db_service.get_user_by_email(data.email)
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    sid = create_session(user.id)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=sid,
        httponly=True,
        samesite="lax",
        max_age=86400 * 30,
    )
    return {"status": "ok", "user": {"id": user.id, "email": user.email, "name": user.name}}


@app.post("/api/auth/telegram")
async def login_telegram(data: dict, response: Response):
    """Авторизация через Telegram Login Widget"""
    logger.info(
        "TG auth request: keys={} has_hash={} id={} auth_date={}",
        sorted(list(data.keys())),
        bool(data.get("hash")),
        data.get("id"),
        data.get("auth_date"),
    )
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TG auth failed: TELEGRAM_BOT_TOKEN is empty")
        raise HTTPException(status_code=503, detail="Telegram авторизация не настроена")

    required_fields = ("id", "first_name", "auth_date", "hash")
    if any(data.get(field) in (None, "") for field in required_fields):
        logger.warning("TG auth failed: required fields missing")
        raise HTTPException(status_code=400, detail="Некорректные данные Telegram")

    try:
        auth_date = int(data.get("auth_date"))
        telegram_id = int(data.get("id"))
    except (TypeError, ValueError):
        logger.warning("TG auth failed: invalid id/auth_date format")
        raise HTTPException(status_code=400, detail="Некорректный формат данных Telegram")

    # Проверка freshness (replay attack prevention)
    if abs(time.time() - auth_date) > 300:
        logger.warning("TG auth failed: auth_date too old/new")
        raise HTTPException(status_code=401, detail="Данные авторизации устарели")

    if not verify_telegram_auth(data, TELEGRAM_BOT_TOKEN):
        logger.warning("TG auth failed: signature mismatch for telegram_id={}", telegram_id)
        raise HTTPException(status_code=401, detail="Неверная подпись Telegram")

    user = await db_service.get_user_by_telegram_id(telegram_id)
    if not user:
        logger.info("TG auth: creating new telegram user id={}", telegram_id)
        user = await db_service.create_telegram_user(
            telegram_id=telegram_id,
            first_name=str(data.get("first_name", "")),
            last_name=data.get("last_name"),
            username=data.get("username"),
        )
    sid = create_session(user.id)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=sid,
        httponly=True,
        samesite="lax",
        max_age=86400 * 30,
    )
    logger.info("TG auth success: user_id={} telegram_id={}", user.id, telegram_id)
    return {"status": "ok", "user": {"id": user.id, "email": user.email, "name": user.name}}


@app.post("/api/auth/logout")
async def logout(response: Response, session_id: Optional[str] = Cookie(None, alias=SESSION_COOKIE_NAME)):
    if session_id:
        delete_session(session_id)
    response.delete_cookie(SESSION_COOKIE_NAME)
    return {"status": "ok"}


@app.get("/api/me")
async def get_me(user: User = Depends(get_current_user)):
    is_telegram = user.telegram_id and user.email and user.email.startswith("tg_")
    return {
        "id": user.id,
        "email": None if is_telegram else user.email,
        "name": user.name,
        "telegram_username": user.telegram_username if user.telegram_id else None,
        "age": user.age,
        "gender": user.gender,
        "is_paid": user.is_paid,
        "test_completed": user.test_completed,
        "premium_test_completed": user.premium_test_completed,
    }


# --- Quiz / Profile ---

@app.get("/api/me/profile", response_model=UserProfileResponse)
async def get_profile(user: User = Depends(get_current_user)):
    return UserProfileResponse(
        status="ok",
        user={
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "age": user.age,
            "gender": user.gender,
        },
        payment_status=None
    )


@app.post("/api/me/profile", response_model=UserProfileResponse)
async def update_profile(data: UserProfileUpdate, user: User = Depends(get_current_user)):
    await db_service.update_user_profile(user.id, name=data.name, age=data.age, gender=data.gender)
    u = await db_service.get_user_by_id(user.id)
    return UserProfileResponse(
        status="ok",
        user={
            "id": u.id,
            "email": u.email,
            "name": u.name,
            "age": u.age,
            "gender": u.gender,
        }
    )


@app.get("/api/me/current-question", response_model=CurrentQuestionResponse)
async def get_current_question(user: User = Depends(get_current_user)):
    user = await db_service.get_user_by_id(user.id)  # свежая версия
    if not user.current_question_id:
        if user.is_paid and user.free_test_completed:
            first_premium = await db_service.get_first_question("premium")
            await db_service.update_user(user.id, {"current_question_id": first_premium.id})
            user = await db_service.get_user_by_id(user.id)
        else:
            user = await db_service.start_test(user.id)
    else:
        current_q = await db_service.get_question(user.current_question_id)
        if current_q and current_q.test_version == "free" and user.is_paid:
            first_premium = await db_service.get_first_question("premium")
            await db_service.update_user(user.id, {"current_question_id": first_premium.id})
            user = await db_service.get_user_by_id(user.id)
    if user.test_completed and not user.is_paid:
        raise HTTPException(status_code=400, detail="Тест уже завершен")
    if user.test_completed and user.is_paid:
        user.test_completed = False
        user.test_completed_at = None
        await db_service.update_user_test_status(user.id, False)

    question = await db_service.get_question(user.current_question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    test_version = "premium" if user.is_paid else "free"
    total = await db_service.get_total_questions(test_version)
    answers = await db_service.get_user_answers_by_test_version(user.id, test_version)
    display_current = (
        question.order_number - FREE_QUESTIONS_LIMIT if test_version == "premium" else question.order_number
    )

    return CurrentQuestionResponse(
        question=QuestionResponse(
            id=question.id,
            text=question.text,
            order_number=question.order_number,
            type=question.type.value,
            allow_voice=question.allow_voice,
            max_length=question.max_length,
        ),
        progress=ProgressResponse(current=display_current, total=total, answered=len(answers)),
        user=UserStatusResponse(is_paid=user.is_paid, test_completed=user.test_completed),
    )


@app.post("/api/me/answer", response_model=NextQuestionResponse)
async def save_answer(data: AnswerRequest, background_tasks: BackgroundTasks, user: User = Depends(get_current_user)):
    if not user.current_question_id:
        raise HTTPException(status_code=400, detail="No active question")
    current_q = await db_service.get_question(user.current_question_id)
    if not current_q:
        raise HTTPException(status_code=404, detail="Question not found")

    await db_service.save_answer(user.id, current_q.id, text_answer=data.text_answer, answer_type=data.answer_type)

    test_version = "premium" if user.is_paid else "free"
    next_q = await db_service.get_next_question(current_q.id, test_version)

    if next_q:
        await update_current_question(user.id, next_q.id)
        total = await db_service.get_total_questions(test_version)
        answers = await db_service.get_user_answers_by_test_version(user.id, test_version)
        display = next_q.order_number - FREE_QUESTIONS_LIMIT if test_version == "premium" else next_q.order_number
        return NextQuestionResponse(
            status="next_question",
            next_question=QuestionResponse(
                id=next_q.id,
                text=next_q.text,
                order_number=next_q.order_number,
                type=next_q.type.value,
                allow_voice=next_q.allow_voice,
                max_length=next_q.max_length,
            ),
            progress=ProgressResponse(current=display, total=total, answered=len(answers)),
        )
    else:
        await db_service.complete_test(user.id, test_version)
        if not user.is_paid and not user.special_offer_started_at:
            await db_service.update_user(user.id, {"special_offer_started_at": datetime.utcnow()})
        if not user.is_paid:
            background_tasks.add_task(_generate_report_bg, user.id, "free")
        elif user.is_paid:
            background_tasks.add_task(_generate_report_bg, user.id, "premium")
        return NextQuestionResponse(status="test_completed", message="Тест завершен", is_paid=user.is_paid)


@app.get("/api/me/progress", response_model=UserProgressResponse)
async def get_progress(user: User = Depends(get_current_user)):
    answers = await db_service.get_user_answers(user.id)
    test_version = "premium" if user.is_paid else "free"
    total = await db_service.get_total_questions(test_version)
    return UserProgressResponse(
        user={
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "is_paid": user.is_paid,
            "test_completed": user.test_completed,
        },
        progress={"total": total, "answered": len(answers)},
        answers=[{
            "question_id": a.question_id,
            "text_answer": a.text_answer,
            "question": {"text": a.question.text, "order_number": a.question.order_number} if a.question else None,
        } for a in answers],
    )


# --- Reports ---

async def _generate_simple_report_async(user_id: int, report_type: str) -> str:
    """Простая генерация отчета (без Perplexity) - текст по Q&A"""
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    prefix = f"prizma_premium_report_{user_id}" if report_type == "premium" else f"prizma_report_{user_id}"
    out_path = reports_dir / f"{prefix}_{ts}.txt"
    questions = await db_service.get_questions_by_version(report_type)
    answers = await db_service.get_user_answers_by_test_version(user_id, report_type)
    qa = {}
    for a in answers:
        if a.question:
            qa[a.question.order_number] = (a.question.text, a.text_answer or "")
    lines = ["PRIZMA - Психологический отчет\n", "=" * 60]
    for order in sorted(qa.keys()):
        qtext, atext = qa[order]
        lines.append(f"\nВопрос {order}: {qtext}")
        lines.append(f"Ответ: {atext}")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return str(out_path)


async def _generate_report_bg(user_id: int, report_type: str):
    """Фоновая генерация отчета"""
    try:
        await db_service.update_report_generation_status(user_id, report_type, ReportGenerationStatus.PROCESSING)
        user = await db_service.get_user_by_id(user_id)
        questions = await db_service.get_questions_by_version(report_type)
        answers = await db_service.get_user_answers_by_test_version(user_id, report_type)

        if PERPLEXITY_ENABLED:
            logger.info(f"Генерация отчёта через Perplexity AI для user_id={user_id} (report_type={report_type})")
            try:
                from app.services.perplexity import AIAnalysisService
                ai = AIAnalysisService()
                if report_type == "premium":
                    result = await ai.generate_premium_report(user, questions, answers)
                else:
                    result = await ai.generate_psychological_report(user, questions, answers)
                if result.get("success"):
                    report_path = result["report_file"]
                else:
                    raise Exception(result.get("error", "AI error"))
            except Exception as e:
                logger.warning(f"Perplexity failed: {e}, falling back to simple report")
                report_path = await _generate_simple_report_async(user_id, report_type)
        else:
            report_path = await _generate_simple_report_async(user_id, report_type)

        if report_path:
            await db_service.update_report_generation_status(
                user_id, report_type, ReportGenerationStatus.COMPLETED, report_path=report_path
            )
            if not user.special_offer_started_at:
                await db_service.update_user(user_id, {"special_offer_started_at": datetime.utcnow()})
        else:
            await db_service.update_report_generation_status(
                user_id, report_type, ReportGenerationStatus.FAILED, error="Ошибка генерации"
            )
    except Exception as e:
        logger.error(f"Report generation error: {e}")
        await db_service.update_report_generation_status(
            user_id, report_type, ReportGenerationStatus.FAILED, error=str(e)
        )


async def _generate_simple_report(user_id: int, report_type: str) -> str:
    return await _generate_simple_report_async(user_id, report_type)


@app.post("/api/me/generate-report")
async def start_report_generation(background_tasks: BackgroundTasks, user: User = Depends(get_current_user)):
    if not user.test_completed and not user.is_paid:
        raise HTTPException(status_code=400, detail="Завершите тест")
    if user.is_premium_paid:
        return {"status": "premium_paid", "message": "Используется премиум отчет"}

    await db_service.reset_stuck_reports(user.id)
    if await db_service.is_report_generating(user.id, "free"):
        return {"status": "already_processing", "message": "Отчет уже генерируется"}

    reports_dir = Path("reports")
    for pattern in [f"prizma_report_{user.id}_*.pdf", f"prizma_report_{user.id}_*.txt"]:
        existing = glob.glob(str(reports_dir / pattern))
        if existing:
            latest = max(existing, key=lambda x: Path(x).stat().st_mtime)
            return {"status": "already_exists", "message": "Отчет готов", "report_path": latest}

    await db_service.update_report_generation_status(user.id, "free", ReportGenerationStatus.PROCESSING)
    background_tasks.add_task(_generate_report_bg, user.id, "free")
    return {"status": "processing", "message": "Генерация запущена"}


@app.get("/api/me/report-status")
async def check_report_status(user: User = Depends(get_current_user)):
    return await db_service.get_report_generation_status(user.id, "free")


@app.get("/api/me/reports-status")
async def get_reports_status(user: User = Depends(get_current_user)):
    free = await db_service.get_report_generation_status(user.id, "free")
    premium = await db_service.get_report_generation_status(user.id, "premium")
    return {"free": free, "premium": premium}


@app.get("/api/me/download/report")
async def download_report(user: User = Depends(get_current_user)):
    if not user.test_completed:
        raise HTTPException(status_code=400, detail="Тест не завершен")
    if user.is_premium_paid:
        return RedirectResponse(url="/api/me/download/premium-report")
    reports_dir = Path("reports")
    files = glob.glob(str(reports_dir / f"prizma_report_{user.id}_*"))
    if files:
        latest = max(files, key=lambda x: Path(x).stat().st_mtime)
        return FileResponse(latest, filename=f"prizma-report-{user.id}{Path(latest).suffix}")
    if await db_service.is_report_generating(user.id, "free"):
        raise HTTPException(status_code=202, detail="Отчет генерируется")
    if PERPLEXITY_ENABLED:
        raise HTTPException(status_code=404, detail="Отчет еще не готов. Обновите страницу и дождитесь завершения генерации.")
    report_path = await _generate_simple_report(user.id, "free")
    return FileResponse(report_path, filename=f"prizma-report-{user.id}.txt")


@app.get("/api/me/download/premium-report")
async def download_premium_report(user: User = Depends(get_current_user)):
    if not user.is_premium_paid:
        raise HTTPException(status_code=400, detail="Премиум не оплачен")
    reports_dir = Path("reports")
    for pattern in [f"prizma_premium_report_{user.id}_*"]:
        files = glob.glob(str(reports_dir / pattern))
        if files:
            latest = max(files, key=lambda x: Path(x).stat().st_mtime)
            return FileResponse(latest, filename=f"prizma-premium-{user.id}.{Path(latest).suffix}")
    if await db_service.is_report_generating(user.id, "premium"):
        raise HTTPException(status_code=202, detail="Отчет генерируется")
    raise HTTPException(status_code=404, detail="Отчет не найден")


@app.post("/api/me/generate-premium-report")
async def start_premium_report(background_tasks: BackgroundTasks, user: User = Depends(get_current_user)):
    if not user.is_premium_paid:
        raise HTTPException(status_code=400, detail="Оплатите премиум")
    await db_service.reset_stuck_reports(user.id)
    if await db_service.is_report_generating(user.id, "premium"):
        return {"status": "already_processing"}
    await db_service.update_report_generation_status(user.id, "premium", ReportGenerationStatus.PROCESSING)
    background_tasks.add_task(_generate_report_bg, user.id, "premium")
    return {"status": "processing"}


@app.get("/api/me/premium-report-status")
async def premium_report_status(user: User = Depends(get_current_user)):
    return await db_service.get_report_generation_status(user.id, "premium")


@app.post("/api/me/stop-report-generation")
async def stop_report(user: User = Depends(get_current_user)):
    await db_service.update_report_generation_status(user.id, "premium", ReportGenerationStatus.PENDING)
    return {"status": "ok"}


@app.post("/api/me/reset-test")
async def reset_test(user: User = Depends(get_current_user)):
    await db_service.clear_user_answers(user.id)
    await db_service.update_user(user.id, {
        "current_question_id": None,
        "test_completed": False,
        "test_completed_at": None,
        "free_test_completed": False,
        "premium_test_completed": False,
    })
    return {"status": "ok"}


# --- Special offer timer ---

@app.get("/api/me/special-offer-timer")
async def get_special_offer_timer(user: User = Depends(get_current_user)):
    if not user.special_offer_started_at:
        return {"active": False, "remaining_seconds": 0}
    from datetime import timedelta
    end = user.special_offer_started_at + timedelta(hours=12)
    remaining = (end - datetime.utcnow()).total_seconds()
    return {
        "active": remaining > 0,
        "remaining_seconds": max(0, int(remaining)),
        "discount_price": PREMIUM_PRICE_DISCOUNT,
        "original_price": PREMIUM_PRICE_ORIGINAL,
    }


@app.post("/api/me/reset-special-offer-timer")
async def reset_special_offer_timer(user: User = Depends(get_current_user)):
    await db_service.update_user(user.id, {"special_offer_started_at": datetime.utcnow()})
    return {"status": "ok"}


# --- Payment ---

@app.post("/api/me/start-premium-payment")
async def start_premium_payment(user: User = Depends(get_current_user)):
    timer_info = await get_special_offer_timer(user)
    if timer_info.get("active"):
        amount_decimal = decimal.Decimal(str(PREMIUM_PRICE_DISCOUNT))
    else:
        amount_decimal = decimal.Decimal(str(PREMIUM_PRICE_ORIGINAL))
    amount_kopecks = int(amount_decimal * 100)
    is_test_int = 1 if ROBOKASSA_TEST else 0

    # 1. Создаём платёж (как в perplexy_bot)
    payment = await db_service.create_payment(
        user.id,
        amount_kopecks,
        "RUB",
        f"Премиум отчет для пользователя {user.id}",
        str(int(time.time() * 1_000_000)),  # временный invoice_id
        PaymentStatus.PENDING,
    )
    inv_id = payment.id

    robokassa = RobokassaService(
        ROBOKASSA_LOGIN or "",
        ROBOKASSA_PASSWORD_1 or "",
        ROBOKASSA_PASSWORD_2 or "",
        is_test_int,
    )

    # Robokassa может отклонять localhost — используем 127.0.0.1 для локальной разработки
    base_url = FRONTEND_URL.replace("localhost", "127.0.0.1") if "localhost" in FRONTEND_URL else FRONTEND_URL
    success_url = f"{base_url}/payment/success?inv_id={inv_id}"
    fail_url = f"{base_url}/payment/fail"

    link = robokassa.generate_payment_link(
        cost=amount_decimal,
        number=inv_id,
        description=f"PRIZMA premium {user.id}",
        is_test=is_test_int,
        success_url=success_url,
        fail_url=fail_url,
    )
    return {"payment_url": link, "invoice_id": str(inv_id)}


@app.get("/api/payment/success")
async def payment_success(inv_id: Optional[str] = None):
    return RedirectResponse(url=f"{FRONTEND_URL}/payment/success?inv_id={inv_id or ''}")


@app.get("/api/payment/fail")
async def payment_fail():
    return RedirectResponse(url=f"{FRONTEND_URL}/payment/fail")


@app.get("/api/robokassa/result")
async def robokassa_result(OutSum: str, InvId: str, SignatureValue: str):
    try:
        pid = int(InvId)
    except (ValueError, TypeError):
        return "bad sign"
    payment = await db_service.get_payment_by_id(pid)
    if not payment:
        return "bad sign"
    robokassa = RobokassaService(
        ROBOKASSA_LOGIN or "",
        ROBOKASSA_PASSWORD_1 or "",
        ROBOKASSA_PASSWORD_2 or "",
        1 if ROBOKASSA_TEST else 0,
    )
    if not robokassa.check_signature_result(OutSum, InvId, SignatureValue):
        return "bad sign"
    await db_service.update_payment_status(payment.id, PaymentStatus.COMPLETED)
    user = await db_service.get_user_by_id(payment.user_id)
    if user:
        await db_service.upgrade_to_premium_and_continue_test(user.id)
    return "OK"


@app.get("/api/robokassa/success")
async def robokassa_success(OutSum: str, InvId: str, SignatureValue: str):
    try:
        pid = int(InvId)
    except (ValueError, TypeError):
        return RedirectResponse(url=f"{FRONTEND_URL}/payment/fail")
    payment = await db_service.get_payment_by_id(pid)
    if not payment:
        return RedirectResponse(url=f"{FRONTEND_URL}/payment/fail")
    robokassa = RobokassaService(
        ROBOKASSA_LOGIN or "",
        ROBOKASSA_PASSWORD_1 or "",
        ROBOKASSA_PASSWORD_2 or "",
        1 if ROBOKASSA_TEST else 0,
    )
    if not robokassa.check_signature_success(OutSum, InvId, SignatureValue):
        return RedirectResponse(url=f"{FRONTEND_URL}/payment/fail")
    await db_service.update_payment_status(payment.id, PaymentStatus.COMPLETED)
    user = await db_service.get_user_by_id(payment.user_id)
    if user:
        await db_service.upgrade_to_premium_and_continue_test(user.id)
    return RedirectResponse(url=f"{FRONTEND_URL}/payment/success?inv_id={InvId}")


@app.get("/api/robokassa/fail")
async def robokassa_fail():
    return RedirectResponse(url=f"{FRONTEND_URL}/payment/fail")


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/info")
async def info():
    return {"name": "PRIZMA API", "version": "1.0.0"}
