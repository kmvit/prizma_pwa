# PRIZMA PWA — User Flow и логика страниц

Эталон /Users/home/PycharmProjects/perplexy_bot

Документ описывает, какую страницу видит пользователь в каждой ситуации и какие действия доступны.

---

## Карта маршрутов

| Путь | Страница | Требует логин | Описание |
|------|----------|---------------|----------|
| `/` | HomePage | Нет | Лендинг / форма старта теста |
| `/register` | RegisterPage | Нет | Регистрация по email |
| `/login` | LoginPage | Нет | Вход по email |
| `/profile` | ProfilePage | Да | Профиль пользователя |
| `/question` | QuestionPage | Да | Вопросы теста |
| `/loading` | LoadingPage | Да | Ожидание генерации отчёта |
| `/offer` | OfferPage | Да | Оффер после бесплатного теста (скачать отчёт + премиум) |
| `/answers` | AnswersPage | Да | Список ответов пользователя |
| `/price` | PricePage | Да | Оплата премиум-отчёта |
| `/download` | DownloadPage | Да | Скачивание отчётов |
| `/payment/success` | PaymentSuccessPage | Нет | Успешная оплата (возврат с Robokassa) |
| `/payment/fail` | PaymentFailPage | Нет | Неуспешная оплата |

---

## Основной сценарий (Happy Path)

### 1. Новый пользователь

```
/ (HomePage)
  → «Начать тест» → нет аккаунта
  → /register (RegisterPage)
  → после регистрации → redirect на /question
```

### 2. Пользователь с аккаунтом

```
/ (HomePage)
  → пользователь УЖЕ залогинен
  → автоматический redirect на /question (страница главной не показывается)
```

### 3. Прохождение теста

```
/question (QuestionPage)
  → GET /api/me/current-question
  → если тест уже завершён (ошибка «уже завершен») → бесплатный: /offer, платный: /loading
  → иначе: показ вопроса
  → ответ ≥350 символов → POST /api/me/answer
  → если status=test_completed → бесплатный: /offer, платный: /loading
  → иначе: следующий вопрос
```

### 4. Генерация отчёта

```
/loading (LoadingPage)
  → GET /api/me/reports-status
  → если free.status=COMPLETED → «Готово!», кнопка «Скачать отчет»
  → если PENDING/FAILED → POST /api/me/generate-report
  → polling каждые 3 сек
  → ссылки: «К странице загрузок» (/download), «На главную» (/)
```

### 5. Скачивание отчёта

```
/download (DownloadPage)
  → GET /api/me/reports-status
  → показ кнопок: «Скачать бесплатный отчет» / «Скачать премиум отчет»
  → или «Премиум отчет генерируется...»
  → ссылка «На главную» (/)
```

---

## Дополнительные сценарии

### Покупка премиум-отчёта

```
Переход на /price возможен:
  - по ссылке «Получить полную расшифровку» с главной (если бы показывалась)
  - по ссылке «Повторить оплату» с /payment/fail
  - прямым вводом URL

/price (PricePage)
  → GET /api/me/special-offer-timer (цена, таймер спецпредложения)
  → «Оплатить» → POST /api/me/start-premium-payment
  → редирект на Robokassa (внешний сервис)
  → после оплаты → /payment/success?inv_id=...
  → при отмене/ошибке → /payment/fail
```

### После оплаты

```
/payment/success
  → текст «Оплата успешно прошла!»
  → ссылки: «К загрузкам» (/download), «На главную» (/)

/payment/fail
  → текст «Оплата не выполнена»
  → ссылки: «Повторить оплату» (/price), «На главную» (/)
```

### Просмотр ответов

```
/answers (AnswersPage)
  → GET /api/me/progress
  → аккордеон: вопрос → ответ
  → кнопка «Скачать отчет» → /download
  → «На главную» (/)

⚠️ На страницу /answers нет явной навигации в приложении.
   Пользователь может попасть только по прямому URL.
```

### Вход / регистрация

```
/login (LoginPage)
  → успешный вход → redirect на / (главная)
  → оттуда при user → redirect на /question

/register (RegisterPage)
  → успешная регистрация → redirect на /question
```

---

## Решения по редиректам

| Условие | Результат |
|---------|-----------|
| Заход на `/`, user залогинен | Сразу `/question` |
| Заход на `/question`, тест завершён (бесплатный) | `/offer` |
| Заход на `/question`, тест завершён (платный) | `/loading` |
| Заход на защищённую страницу без логина | `/` (главная) |
| Неизвестный путь | `/` |
| Оплата успешна (Robokassa) | `/payment/success` |
| Оплата неуспешна | `/payment/fail` |

---

## Защищённые страницы (ProtectedRoute)

Требуют `api.getMe()` = OK. Иначе → redirect на `/` (главная, оттуда — регистрация или вход):

- `/profile`
- `/question`
- `/loading`
- `/offer`
- `/answers`
- `/price`
- `/download`

Не защищены:

- `/`, `/register`, `/login` — публичный доступ
- `/payment/success`, `/payment/fail` — возврат с Robokassa (может быть в новом окне)

---

## Итоговая схема

```
                    ┌─────────────┐
                    │     /      │
                    │  HomePage  │
                    └─────┬─────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
     user=null       user?           user?
     [форма]    [redirect]     [redirect]
          │               │               │
          ▼               └───────┬───────┘
     /register                     │
     /login                        ▼
          │                  /question
          │                        │
          └────────────┬───────────┘
                       │
                       │ test_completed
              ┌────────┴────────┐
              ▼                 ▼
         /offer (free)     /loading (paid)
              │                 │
              └────────┬────────┘
                       │
          ┌────────────┼────────────┐
          │            │            │
     /download    /answers      /
          │            │
          └─────┬──────┘
               │
          /price ──► Robokassa ──► /payment/success
                                  /payment/fail
```
