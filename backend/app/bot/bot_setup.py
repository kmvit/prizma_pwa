"""
Настройка и инициализация Telegram бота через aiogram.
Использует polling для получения обновлений (не требует webhook).
"""
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import MenuButtonDefault
from loguru import logger

from app.config import TELEGRAM_BOT_TOKEN
from app.bot.handlers import start

bot = None
dp = None

if TELEGRAM_BOT_TOKEN:
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(start.router)
    logger.info("✅ Aiogram бот инициализирован")
else:
    logger.warning("⚠️ TELEGRAM_BOT_TOKEN не настроен, бот не инициализирован")


async def start_polling():
    """Запустить polling для получения обновлений от Telegram"""
    if not bot or not dp:
        logger.warning("⚠️ Бот не инициализирован, polling не запущен")
        return
    try:
        logger.info("🔄 Запуск polling для получения обновлений от Telegram...")
        try:
            await bot.delete_webhook(drop_pending_updates=True)
        except Exception as e:
            logger.debug(f"Webhook не настроен или ошибка: {e}")

        # Убираем кастомную кнопку «Открыть приложение», возвращаем стандартное меню
        try:
            await bot.set_chat_menu_button(menu_button=MenuButtonDefault())
            logger.info("✅ Кнопка меню сброшена на стандартную")
        except Exception as e:
            logger.debug(f"Сброс кнопки меню: {e}")

        await dp.start_polling(bot, skip_updates=True)
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске polling: {e}")


async def stop_polling():
    """Остановить polling"""
    if dp:
        try:
            await dp.stop_polling()
            logger.info("✅ Polling остановлен")
        except Exception as e:
            logger.error(f"❌ Ошибка при остановке polling: {e}")


async def close_bot():
    """Закрыть сессию бота"""
    if bot:
        await bot.session.close()
        logger.info("✅ Сессия бота закрыта")
