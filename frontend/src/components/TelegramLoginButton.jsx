import { useEffect, useRef } from 'react'

const TELEGRAM_BOT_USERNAME = import.meta.env.VITE_TELEGRAM_BOT_USERNAME || ''

/**
 * Кнопка входа через Telegram Login Widget.
 * Использует data-auth-url (redirect) — надёжно в Yandex, Safari, при открытии из Telegram.
 * Требует VITE_TELEGRAM_BOT_USERNAME в .env (без @, например PrizmaBot)
 */
export default function TelegramLoginButton({ onAuth, onError, buttonSize = 'large', className = '' }) {
  const containerRef = useRef(null)
  const onAuthRef = useRef(onAuth)
  const onErrorRef = useRef(onError)
  onAuthRef.current = onAuth
  onErrorRef.current = onError

  useEffect(() => {
    if (!TELEGRAM_BOT_USERNAME || !containerRef.current) return

    const authUrl = `${window.location.origin}/auth/telegram/callback`

    const script = document.createElement('script')
    script.async = true
    script.src = 'https://telegram.org/js/telegram-widget.js?22'
    script.setAttribute('data-telegram-login', TELEGRAM_BOT_USERNAME)
    script.setAttribute('data-size', buttonSize)
    script.setAttribute('data-auth-url', authUrl)
    script.setAttribute('data-request-access', 'write')
    containerRef.current.innerHTML = ''
    containerRef.current.appendChild(script)
  }, [buttonSize])

  if (!TELEGRAM_BOT_USERNAME) return null

  return (
    <div ref={containerRef} className={className} />
  )
}
