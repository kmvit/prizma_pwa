"""
Обработчик команды /start.
При первом запуске запрашивает email и привязывает Telegram к аккаунту на сайте.
"""
import re

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

from app.config import FRONTEND_URL
from app.services.database_service import db_service
from loguru import logger

router = Router()


class LinkStates(StatesGroup):
    waiting_email = State()


def _is_valid_email(text: str) -> bool:
    """Простая проверка формата email"""
    if not text or len(text) > 254:
        return False
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, text.strip()))


def _render_welcome_message() -> str:
    return """
👋 <b>Добро пожаловать в PRIZMA!</b>

Ваш личный ИИ психолог поможет:
🧠 Расшифровать личность
📊 Получить психологический анализ
💡 Узнать сильные стороны и зоны роста

Начните тест прямо сейчас!
    """.strip()


async def _send_welcome(message: Message):
    """Отправка приветствия и кнопки перехода на сайт"""
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
        _render_welcome_message(),
        reply_markup=keyboard,
        parse_mode="HTML",
    )


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Обработка команды /start: если пользователь не привязан — запрашиваем email"""
    chat_id = message.chat.id
    await state.clear()

    try:
        user = await db_service.get_user_by_telegram_id(chat_id)
        if user:
            logger.info(f"👤 /start от {chat_id}: пользователь уже привязан (user_id={user.id})")
            await _send_welcome(message)
            return

        await state.set_state(LinkStates.waiting_email)
        await message.answer(
            "📧 Введите email, с которым вы регистрировались на сайте:",
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error(f"❌ Ошибка при обработке /start для {chat_id}: {e}")
        await state.clear()
        try:
            await message.answer("❌ Произошла ошибка. Попробуйте позже.")
        except Exception:
            pass


@router.message(LinkStates.waiting_email)
async def process_email(message: Message, state: FSMContext):
    """Обработка введённого email: поиск аккаунта и привязка"""
    chat_id = message.chat.id
    text = (message.text or "").strip()

    if not text:
        await message.answer("❌ Введите корректный email.")
        return

    if not _is_valid_email(text):
        await message.answer("❌ Неверный формат email. Введите email, с которым регистрировались на сайте.")
        return

    try:
        user = await db_service.get_user_by_email(text)
        if not user:
            await message.answer(
                "❌ Пользователь с таким email не найден. "
                "Зарегистрируйтесь на сайте и попробуйте снова."
            )
            return

        if user.telegram_id and user.telegram_id != chat_id:
            await message.answer("⚠️ Этот email уже привязан к другому аккаунту Telegram.")
            await state.clear()
            return

        if user.telegram_id == chat_id:
            await state.clear()
            await _send_welcome(message)
            return

        await db_service.update_user(user.id, {
            "telegram_id": chat_id,
            "telegram_username": message.from_user.username,
        })
        logger.info(f"🔗 Telegram {chat_id} привязан к пользователю {user.id} (email: {text})")
        await state.clear()
        await message.answer("✅ Аккаунт успешно привязан!")

        await _send_welcome(message)

    except Exception as e:
        logger.error(f"❌ Ошибка при привязке email для {chat_id}: {e}")
        await state.clear()
        try:
            await message.answer("❌ Произошла ошибка. Попробуйте позже.")
        except Exception:
            pass
