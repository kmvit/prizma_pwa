import secrets
from typing import Optional

import bcrypt
from fastapi import HTTPException, status, Cookie

from app.config import SESSION_COOKIE_NAME
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
