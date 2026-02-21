import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=True)

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_DIR = BASE_DIR / "data"
DATABASE_DIR.mkdir(exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{DATABASE_DIR}/prizma.db")
SQL_ECHO = os.getenv("SQL_ECHO", "false").lower() == "true"

# Auth
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production-use-long-random-string")
SESSION_COOKIE_NAME = "prizma_session"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

# Frontend (редиректы после оплаты)
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# Perplexity API
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
PERPLEXITY_MODEL = os.getenv("PERPLEXITY_MODEL", "sonar-pro")
PERPLEXITY_ENABLED = os.getenv("PERPLEXITY_ENABLED", "false").lower() == "true"

# Robokassa (optional for dev)
ROBOKASSA_LOGIN = os.getenv("ROBOKASSA_LOGIN", "")
ROBOKASSA_PASSWORD_1 = os.getenv("ROBOKASSA_PASSWORD_1", "")
ROBOKASSA_PASSWORD_2 = os.getenv("ROBOKASSA_PASSWORD_2", "")
ROBOKASSA_TEST = os.getenv("ROBOKASSA_TEST", "1") == "1"

# Тесты
FREE_QUESTIONS_LIMIT = int(os.getenv("FREE_QUESTIONS_LIMIT", "8"))
PREMIUM_QUESTIONS_COUNT = int(os.getenv("PREMIUM_QUESTIONS_COUNT", "38"))

# Цены
PREMIUM_PRICE_ORIGINAL = float(os.getenv("PREMIUM_PRICE_ORIGINAL", "1.00"))
PREMIUM_PRICE_DISCOUNT = float(os.getenv("PREMIUM_PRICE_DISCOUNT", "1.00"))
