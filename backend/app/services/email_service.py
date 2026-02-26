"""
Сервис для отправки уведомлений на email через SMTP.
Содержание сообщений соответствует уведомлениям в Telegram.
"""

import asyncio
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from app.config import (
    FRONTEND_URL,
    API_BASE_URL,
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USER,
    SMTP_PASSWORD,
    SMTP_FROM_EMAIL,
    SMTP_USE_TLS,
)
from loguru import logger


def _is_valid_email(email: str) -> bool:
    """Проверить, что email настоящий (не tg_xxx@prizma.telegram)"""
    if not email or not isinstance(email, str):
        return False
    email = email.strip().lower()
    if email.startswith("tg_") and "@prizma.telegram" in email:
        return False
    return "@" in email and "." in email


def _build_download_url(telegram_id: int | None, user_id: int, is_premium: bool) -> str:
    """Собрать URL для скачивания отчёта"""
    base = (API_BASE_URL or FRONTEND_URL or "").rstrip("/")
    if not base:
        return ""
    if telegram_id:
        path = f"/download/premium-report/{telegram_id}" if is_premium else f"/download/report/{telegram_id}"
        return f"{base}{path}"
    return f"{base}/download"


class EmailService:
    """Сервис для отправки email-уведомлений"""

    def __init__(self):
        self.host = SMTP_HOST
        self.port = SMTP_PORT
        self.user = SMTP_USER
        self.password = SMTP_PASSWORD
        self.from_email = SMTP_FROM_EMAIL or self.user or "noreply@prizma.local"
        self.use_tls = SMTP_USE_TLS
        self.webapp_url = (FRONTEND_URL or "").rstrip("/")
        self.api_base_url = (API_BASE_URL or FRONTEND_URL or "").rstrip("/")

        if not self.host or not self.user or not self.password:
            logger.warning("⚠️ SMTP не настроен (SMTP_HOST, SMTP_USER, SMTP_PASSWORD), отправка на email отключена")
            self.enabled = False
        else:
            self.enabled = True
            logger.info("✅ Email сервис инициализирован")

    async def _send_email(
        self, to_email: str, subject: str, body_text: str, body_html: str | None = None, attachment_path: str | None = None
    ) -> bool:
        """Отправить email (синхронно в executor)"""
        if not self.enabled:
            return False

        def _do_send():
            try:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = self.from_email
                msg["To"] = to_email

                msg.attach(MIMEText(body_text, "plain", "utf-8"))
                if body_html:
                    msg.attach(MIMEText(body_html, "html", "utf-8"))

                if attachment_path and os.path.exists(attachment_path):
                    with open(attachment_path, "rb") as f:
                        part = MIMEApplication(f.read(), _subtype="pdf" if attachment_path.lower().endswith(".pdf") else "octet-stream")
                        part.add_header("Content-Disposition", "attachment", filename=os.path.basename(attachment_path))
                        msg.attach(part)

                with smtplib.SMTP(self.host, self.port) as server:
                    if self.use_tls:
                        server.starttls()
                    server.login(self.user, self.password)
                    server.sendmail(self.from_email, [to_email], msg.as_string())
                return True
            except Exception as e:
                logger.error(f"❌ Ошибка SMTP при отправке на {to_email}: {e}")
                return False

        return await asyncio.to_thread(_do_send)

    async def send_report_ready_notification(
        self,
        email: str,
        report_path: str,
        is_premium: bool,
        telegram_id: int | None,
        user_id: int,
    ) -> bool:
        """Отправить уведомление о готовности отчёта"""
        if not self.enabled or not _is_valid_email(email):
            return False

        report_type = "премиум" if is_premium else "бесплатный"
        download_url = _build_download_url(telegram_id, user_id, is_premium)
        link_line = f"Скачать отчёт: {download_url}" if download_url else "Войдите в веб-приложение для скачивания отчёта."
        link_html = f'<p><a href="{download_url}">Скачать отчёт</a></p>' if download_url else "<p>Войдите в веб-приложение для скачивания отчёта.</p>"

        subject = f"🎉 Ваш {report_type} отчёт PRIZMA готов!"

        body_text = f"""
Ваш {report_type} отчет готов!

Мы проанализировали ваши ответы и создали персональный психологический портрет.

{link_line}

Вы также можете скачать отчёт в веб-приложении.
        """.strip()

        body_html = f"""
<p>Ваш <strong>{report_type}</strong> отчёт готов!</p>
<p>Мы проанализировали ваши ответы и создали персональный психологический портрет.</p>
{link_html}
<p>Вы также можете скачать отчёт в веб-приложении.</p>
        """.strip()

        # Пробуем прикрепить файл, если не слишком большой (например, до 15 МБ)
        try:
            size_mb = os.path.getsize(report_path) / (1024 * 1024)
            attachment_path = report_path if size_mb < 15 else None
        except Exception:
            attachment_path = None

        success = await self._send_email(
            email, subject, body_text, body_html, attachment_path=attachment_path
        )
        if success:
            logger.info(f"✅ Email-уведомление о готовности отчёта отправлено на {email}")
        return success

    async def send_error_notification(self, email: str, error_message: str) -> bool:
        """Отправить уведомление об ошибке"""
        if not self.enabled or not _is_valid_email(email):
            return False

        subject = "❌ Ошибка при генерации отчёта PRIZMA"

        body_text = f"""
Произошла ошибка при генерации отчета

Мы уже работаем над решением проблемы.

Попробуйте снова через несколько минут или обратитесь в поддержку.

Ошибка: {error_message}
        """.strip()

        success = await self._send_email(email, subject, body_text)
        if success:
            logger.info(f"✅ Email-уведомление об ошибке отправлено на {email}")
        return success

    async def send_premium_offer(self, email: str) -> bool:
        """Отправить предложение премиум-отчёта (после бесплатного)"""
        if not self.enabled or not _is_valid_email(email):
            return False

        offer_url = f"{self.webapp_url}/offer" if self.webapp_url else ""

        subject = "🎁 Спецпредложение: полная расшифровка за 3.590 ₽"

        body_text = """
Ваша полная психологическая книга-расшифровка на 150 страниц доступна по спеццене — всего 3.590 ₽ вместо 6.980 ₽.

Успейте воспользоваться предложением прямо сейчас.

PRIZMA – ваш личный тренер по развитию, доступный всегда, без ограничений по времени.

Откройте глубокое понимание себя и план действий на годы вперёд.

Хотите получить по акции?
        """.strip()

        body_html = f"""
<p><strong>Ваша полная психологическая книга-расшифровка на 150 страниц</strong> сейчас доступна по спеццене — всего 3.590 ₽ вместо 6.980 ₽.</p>
<p>Успейте воспользоваться предложением прямо сейчас.</p>
<p>PRIZMA – ваш личный тренер по развитию, доступный всегда, без ограничений по времени.</p>
<p>Откройте глубокое понимание себя и план действий на годы вперёд.</p>
<p><a href="{offer_url}">🔥 Хочу получить по акции!</a></p>
        """.strip()

        success = await self._send_email(email, subject, body_text, body_html)
        if success:
            logger.info(f"✅ Email-предложение премиум-отчёта отправлено на {email}")
        return success

    async def send_special_offer_6_hours_left(self, email: str) -> bool:
        """Отправить уведомление за 6 часов до конца акции"""
        if not self.enabled or not _is_valid_email(email):
            return False

        offer_url = f"{self.webapp_url}/offer" if self.webapp_url else ""

        subject = "⏳ До конца скидки осталось 6 часов!"

        body_text = """
До конца вашей скидки осталось всего 6 часов!
Полный аудит вашей личности ещё доступен по акции 3.590 ₽ вместо 6.980 ₽

По цене одного сеанса у психолога вы получаете 150 страниц личностного аудита и персональные шаги для роста:

• Глубокий психологический портрет с анализом Big Five и MBTI
• Уникальные архетипы и когнитивный профиль
• Анализ эмоционального интеллекта и управления состояниями
• Персональный прогноз развития на 1–3 года
• И многое другое...
        """.strip()

        body_html = f"""
<p><strong>До конца вашей скидки осталось всего 6 часов!</strong></p>
<p>Полный аудит вашей личности ещё доступен по акции 3.590 ₽ вместо 6.980 ₽</p>
<p>По цене одного сеанса у психолога вы получаете 150 страниц личностного аудита и персональные шаги для роста.</p>
<p><a href="{offer_url}">🔥 Хочу получить начать трансформацию!</a></p>
        """.strip()

        success = await self._send_email(email, subject, body_text, body_html)
        if success:
            logger.info(f"✅ Email-уведомление «6 часов» отправлено на {email}")
        return success

    async def send_special_offer_1_hour_left(self, email: str) -> bool:
        """Отправить уведомление за 1 час до конца акции"""
        if not self.enabled or not _is_valid_email(email):
            return False

        offer_url = f"{self.webapp_url}/offer" if self.webapp_url else ""

        subject = "⚡ Последний шанс! Остался 1 час"

        body_text = """
Последний шанс!
У вас остался 1 час, чтобы получить свою полную расшифровку за 3.590 ₽
Дальше цена снова вырастет до 6.980 ₽

Помните, это вложение в ваше понимание себя и ключ к вашему развитию.
        """.strip()

        body_html = f"""
<p><strong>Последний шанс!</strong></p>
<p>У вас остался 1 час, чтобы получить свою полную расшифровку за 3.590 ₽. Дальше цена снова вырастет до 6.980 ₽</p>
<p><a href="{offer_url}">🔥 Хочу изучить себя на 100%</a></p>
        """.strip()

        success = await self._send_email(email, subject, body_text, body_html)
        if success:
            logger.info(f"✅ Email-уведомление «1 час» отправлено на {email}")
        return success

    async def send_special_offer_10_minutes_left(self, email: str) -> bool:
        """Отправить уведомление за 10 минут до конца акции"""
        if not self.enabled or not _is_valid_email(email):
            return False

        offer_url = f"{self.webapp_url}/offer" if self.webapp_url else ""

        subject = "🚨 Ваше спецпредложение закрывается!"

        body_text = """
Ваше спецпредложение закрывается!
Вы больше не сможете получить полную расшифровку со скидкой –50%
        """.strip()

        body_html = f"""
<p><strong>Ваше спецпредложение закрывается!</strong></p>
<p>Вы больше не сможете получить полную расшифровку со скидкой –50%</p>
<p><a href="{offer_url}">🔥 Успеть в последний вагон</a></p>
        """.strip()

        success = await self._send_email(email, subject, body_text, body_html)
        if success:
            logger.info(f"✅ Email-уведомление «10 минут» отправлено на {email}")
        return success


email_service = EmailService()
