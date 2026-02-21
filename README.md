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
- `FRONTEND_URL` — URL фронта (для редиректов оплаты)
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
