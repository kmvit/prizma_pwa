"""
Сервис Web Push уведомлений.
Тексты сокращены для пушей (ограничение ~120 символов на body).
"""

import asyncio
import json
from pathlib import Path

from pywebpush import webpush, WebPushException
from loguru import logger

from app.config import VAPID_PRIVATE_KEY, VAPID_PUBLIC_KEY, FRONTEND_URL


# Короткие тексты для пушей (как в запросе пользователя)
PUSH_TEXTS = {
    "premium_offer": "Ваша полная психологическая книга-расшифровка на 150 страниц, сейчас доступна по спеццене — всего 3.590 ₽ вместо 6.980 ₽.",
    "6_hours_left": "До конца вашей скидки осталось всего 6 часов!",
    "1_hour_left": "Последний шанс! У вас остался 1 час, чтобы получить свою полную расшифровку за 3.590 ₽",
    "10_minutes_left": "Ваше спецпредложение закрывается!",
}


def _get_vapid_private_key():
    """Вернуть VAPID приватный ключ (путь к файлу или содержимое)"""
    key = (VAPID_PRIVATE_KEY or "").strip()
    if not key:
        return None
    path = Path(key)
    if path.exists():
        return str(path)
    return key


class PushService:
    """Сервис для отправки Web Push уведомлений"""

    def __init__(self):
        self.vapid_private = _get_vapid_private_key()
        self.vapid_public = (VAPID_PUBLIC_KEY or "").strip()
        self.offer_url = f"{FRONTEND_URL.rstrip('/')}/offer" if FRONTEND_URL else "/offer"

        if not self.vapid_private or not self.vapid_public:
            logger.warning(
                "⚠️ VAPID не настроен (VAPID_PRIVATE_KEY, VAPID_PUBLIC_KEY), "
                "Web Push отключен. Сгенерируйте: python -m py_vapid --gen"
            )
            self.enabled = False
        else:
            self.enabled = True
            logger.info("✅ Push сервис инициализирован")

    def _subscription_dict(self, endpoint: str, p256dh: str, auth: str) -> dict:
        return {
            "endpoint": endpoint,
            "keys": {"p256dh": p256dh, "auth": auth},
        }

    def _send_sync(self, subscription: dict, title: str, body: str, url: str = None, tag: str = None) -> bool:
        """Синхронная отправка push (вызывается в executor)"""
        if not self.enabled:
            return False

        payload = {"title": title, "body": body}
        if url:
            payload["url"] = url
        if tag:
            payload["tag"] = tag

        try:
            webpush(
                subscription_info=subscription,
                data=json.dumps(payload),
                vapid_private_key=self.vapid_private,
                vapid_claims={"sub": "mailto:support@prizma.app"},
                ttl=86400,
            )
            return True
        except WebPushException as e:
            logger.warning(f"⚠️ Push не доставлен (подписка может быть устаревшей): {e}")
            return False

    async def _send(self, subscription: dict, title: str, body: str, url: str = None, tag: str = None) -> bool:
        return await asyncio.to_thread(
            self._send_sync, subscription, title, body, url, tag
        )

    async def send_premium_offer(self, endpoint: str, p256dh: str, auth: str) -> bool:
        """Предложение премиум-отчёта после бесплатного"""
        sub = self._subscription_dict(endpoint, p256dh, auth)
        return await self._send(
            sub,
            title="PRIZMA — Спеццена",
            body=PUSH_TEXTS["premium_offer"],
            url=self.offer_url,
            tag="premium_offer",
        )

    async def send_special_offer_6_hours_left(self, endpoint: str, p256dh: str, auth: str) -> bool:
        """За 6 часов до конца акции"""
        sub = self._subscription_dict(endpoint, p256dh, auth)
        return await self._send(
            sub,
            title="PRIZMA — До конца скидки 6 часов",
            body=PUSH_TEXTS["6_hours_left"],
            url=self.offer_url,
            tag="6h",
        )

    async def send_special_offer_1_hour_left(self, endpoint: str, p256dh: str, auth: str) -> bool:
        """За 1 час до конца акции"""
        sub = self._subscription_dict(endpoint, p256dh, auth)
        return await self._send(
            sub,
            title="PRIZMA — Последний шанс",
            body=PUSH_TEXTS["1_hour_left"],
            url=self.offer_url,
            tag="1h",
        )

    async def send_special_offer_10_minutes_left(self, endpoint: str, p256dh: str, auth: str) -> bool:
        """За 10 минут до конца акции"""
        sub = self._subscription_dict(endpoint, p256dh, auth)
        return await self._send(
            sub,
            title="PRIZMA — Акция закрывается",
            body=PUSH_TEXTS["10_minutes_left"],
            url=self.offer_url,
            tag="10m",
        )


push_service = PushService()
