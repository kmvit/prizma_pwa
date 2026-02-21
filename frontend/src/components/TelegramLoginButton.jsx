import { useEffect, useRef } from 'react'

const TELEGRAM_BOT_USERNAME = import.meta.env.VITE_TELEGRAM_BOT_USERNAME || ''

/**
 * Кнопка входа через Telegram Login Widget.
 * Использует data-auth-url (redirect) — надёжно в Yandex, Safari, при открытии из Telegram.
 * Требует VITE_TELEGRAM_BOT_USERNAME в .env (без @, например PrizmaBot)
 */
export default function TelegramLoginButton({ buttonSize = 'large', className = '' }) {
  const containerRef = useRef(null)

  useEffect(() => {
    if (!TELEGRAM_BOT_USERNAME || !containerRef.current) {
      console.debug('[TG_LOGIN] widget skipped', {
        hasUsername: Boolean(TELEGRAM_BOT_USERNAME),
        hasContainer: Boolean(containerRef.current),
      })
      return
    }

    const authUrl = `${window.location.origin}/auth/telegram/callback`
    console.debug('[TG_LOGIN] render widget', {
      authUrl,
      bot: TELEGRAM_BOT_USERNAME,
      origin: window.location.origin,
    })

    const script = document.createElement('script')
    script.async = true
    script.src = 'https://telegram.org/js/telegram-widget.js?22'
    script.setAttribute('data-telegram-login', TELEGRAM_BOT_USERNAME)
    script.setAttribute('data-size', buttonSize)
    script.setAttribute('data-auth-url', authUrl)
    script.setAttribute('data-request-access', 'write')
    script.onload = () => console.debug('[TG_LOGIN] widget script loaded')
    script.onerror = () => console.error('[TG_LOGIN] widget script failed')
    containerRef.current.innerHTML = ''
    containerRef.current.appendChild(script)
  }, [buttonSize])

  if (!TELEGRAM_BOT_USERNAME) return null

  return (
    <div ref={containerRef} className={className} />
  )
}
