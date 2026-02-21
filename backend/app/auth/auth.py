import hashlib
import hmac
import secrets
import time
from typing import Optional, Any

import bcrypt
from fastapi import HTTPException, status, Cookie
from loguru import logger

from app.config import SESSION_COOKIE_NAME, TELEGRAM_BOT_TOKEN
from app.database.models import User
from app.services.database_service import db_service

# In-memory session store (for production use Redis)
_sessions: dict[str, int] = {}  # session_id -> user_id


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_session(user_id: int) -> str:
    sid = secrets.token_urlsafe(32)
    _sessions[sid] = user_id
    return sid


def get_user_id_from_session(session_id: str) -> Optional[int]:
    return _sessions.get(session_id)


def delete_session(session_id: str) -> None:
    _sessions.pop(session_id, None)


def verify_telegram_auth(data: dict[str, Any], bot_token: str) -> bool:
    """
    Проверка подлинности данных от Telegram Login Widget.
    https://core.telegram.org/widgets/login#checking-authorization
    """
    received_hash = str(data.get("hash") or "").strip().lower()
    if not received_hash or not bot_token:
        return False

    allowed_keys = {
        "id",
        "first_name",
        "last_name",
        "username",
        "photo_url",
        "auth_date",
        "allows_write_to_pm",
        "language_code",
    }
    # data_check_string: поля в алфавитном порядке (кроме hash), key=value через \n
    check_data = {
        k: str(v)
        for k, v in data.items()
        if k in allowed_keys and v is not None
    }
    parts = [f"{k}={check_data[k]}" for k in sorted(check_data.keys())]
    data_check_string = "\n".join(parts)
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    computed = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest().lower()
    is_valid = hmac.compare_digest(computed, received_hash)
    if not is_valid:
        logger.warning(
            "TG verify mismatch: keys={} received_hash_prefix={} computed_hash_prefix={} data_check_string={}",
            sorted(check_data.keys()),
            received_hash[:10],
            computed[:10],
            data_check_string,
        )
    return is_valid


async def get_current_user(
    session_id: Optional[str] = Cookie(None, alias=SESSION_COOKIE_NAME)
) -> User:
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    user_id = get_user_id_from_session(session_id)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )
    user = await db_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user
