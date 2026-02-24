/**
 * Строит ссылку на Telegram-бота (без параметров).
 * Привязка аккаунта происходит в боте: пользователь вводит email после /start.
 */
export function buildTelegramBotUrl(botUsername) {
  if (!botUsername) return null
  return `https://t.me/${botUsername}`
}
