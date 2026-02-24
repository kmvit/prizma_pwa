/**
 * Строит deep link на Telegram-бота с параметром start.
 * Параметр: base64(encodeURIComponent(email)) — максимум 64 символа (лимит Telegram).
 *
 * В боте при /start param приходит в message.text после "start ".
 * Декодирование на бэкенде: decodeURIComponent(atob(param))
 */
export function buildTelegramBotUrl(botUsername, email) {
  if (!botUsername) return null
  const base = `https://t.me/${botUsername}`
  if (!email || typeof email !== 'string') return base
  try {
    const encoded = btoa(encodeURIComponent(email)).replace(/=+$/, '')
    const param = encoded.slice(0, 64)
    return param ? `${base}?start=${param}` : base
  } catch {
    return base
  }
}
