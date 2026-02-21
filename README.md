# PRIZMA PWA

Психологический тест с ИИ-анализом. PWA на React + FastAPI.

## Структура

- `backend/` — FastAPI, SQLite, аутентификация по email
- `frontend/` — React (Vite), PWA

## Запуск

### Backend

```bash
cd backend
cp env.example .env
# Отредактируйте .env при необходимости
pip install -r requirements.txt
python -m app.database.seed_data   # загрузка вопросов
python run.py                      # или: uvicorn app.main:app --reload --port 8080
```

API: http://localhost:8080  
Docs: http://localhost:8080/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Приложение: http://localhost:5173

Vite проксирует `/api` на backend (8080).

## Переменные окружения (.env)

- `SECRET_KEY` — ключ для сессий
- `FRONTEND_URL` — URL фронта (для редиректов оплаты и ссылок в Telegram)
- `API_BASE_URL` — URL API для ссылок на скачивание в уведомлениях (если не задан — используется `FRONTEND_URL`)
- `TELEGRAM_BOT_TOKEN` — для авторизации и уведомлений в бота
- `DATABASE_URL` — SQLite по умолчанию
- `PERPLEXITY_API_KEY`, `PERPLEXITY_ENABLED` — для ИИ-анализа
- `ROBOKASSA_*` — для приёма платежей

## Регистрация и вход

Пользователи регистрируются по email + пароль или через Telegram. Все действия с тестом и отчётами — после входа.

### Telegram-авторизация

1. Создайте бота через [@BotFather](https://t.me/BotFather), привяжите домен: `/setdomain`
2. **Backend** (.env): `TELEGRAM_BOT_TOKEN=токен_от_BotFather`
3. **Frontend** (.env): `VITE_TELEGRAM_BOT_USERNAME=имя_бота` (без @, например `PrizmaBot`)
4. Для локальной разработки нужен HTTPS (например, [ngrok](https://ngrok.com/))

### Telegram-уведомления в бота

Пользователи с `telegram_id` в БД получают уведомления в того же бота (по `TELEGRAM_BOT_TOKEN`):

- **Отчёт готов** — после генерации бесплатного или премиум-отчёта (PDF или ссылка на скачивание)
- **Предложение премиума** — после бесплатного отчёта (с кнопкой «Хочу получить по акции!»)
- **Спецпредложение по таймеру** — за 6 часов, за 1 час и за 10 минут до конца скидки (12 часов)
- **Ошибка генерации** — если отчёт не удалось сгенерировать

Фоновая задача проверяет таймеры каждые 5 минут. При запросе `/api/me/special-offer-timer` выполняется разовая проверка.

**Эндпоинты для отладки:**

- `POST /api/user/{telegram_id}/send-special-offer-notification` — body: `{"notification_type": "6_hours_left" | "1_hour_left" | "10_minutes_left"}`
- `POST /api/user/{telegram_id}/send-all-special-offer-notifications` — отправить все три уведомления

**Ссылки на скачивание из уведомлений:** `GET /api/download/report/{telegram_id}` и `GET /api/download/premium-report/{telegram_id}`.
