"""
Обработчик команды /start.
Поддерживает deep link с email (параметр start из ссылки t.me/Bot?start=...).
"""
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

from app.config import FRONTEND_URL
from app.services.database_service import db_service
from app.services.telegram_service import decode_start_param
from loguru import logger

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Обработка команды /start (включая deep link с параметром)"""
    chat_id = message.chat.id

    # Извлекаем параметр из /start PARAM
    text = message.text or ""
    parts = text.split(maxsplit=1)
    start_param = parts[1] if len(parts) > 1 else ""

    email = decode_start_param(start_param) if start_param else None
    if email:
        logger.info(f"🚀 /start от {chat_id} с параметром email: {email}")

    try:
        user = await db_service.get_user_by_telegram_id(chat_id)
        if not user and email:
            # Пользователь пришёл по ссылке с email — привязываем Telegram к существующему аккаунту
            user = await db_service.get_user_by_email(email)
            if user and not user.telegram_id:
                await db_service.update_user(user.id, {"telegram_id": chat_id, "telegram_username": message.from_user.username})
                logger.info(f"🔗 Telegram {chat_id} привязан к пользователю {user.id} (email: {email})")
        if not user:
            user = await db_service.create_telegram_user(
                telegram_id=chat_id,
                first_name=message.from_user.first_name or "",
                last_name=message.from_user.last_name,
                username=message.from_user.username,
            )
            logger.info(f"👤 Пользователь создан: id={user.id}, telegram_id={chat_id}")

        welcome_text = """
👋 <b>Добро пожаловать в PRIZMA!</b>

Ваш личный ИИ психолог поможет:
🧠 Расшифровать личность
📊 Получить психологический анализ
💡 Узнать сильные стороны и зоны роста

Начните тест прямо сейчас!
        """.strip()

        keyboard_buttons = []
        if FRONTEND_URL:
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text="🚀 Начать тест",
                    web_app={"url": FRONTEND_URL.rstrip("/") + "/"},
                )
            ])

        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons) if keyboard_buttons else None

        await message.answer(
            welcome_text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )

    except Exception as e:
        logger.error(f"❌ Ошибка при обработке /start для {chat_id}: {e}")
        try:
            await message.answer("❌ Произошла ошибка. Попробуйте позже.")
        except Exception:
            pass
