import { useEffect, useRef } from 'react'

const TELEGRAM_BOT_USERNAME = import.meta.env.VITE_TELEGRAM_BOT_USERNAME || ''

/**
 * Кнопка входа через Telegram Login Widget.
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

    window.onTelegramAuth = async (user) => {
      try {
        await onAuthRef.current?.(user)
      } catch (e) {
        onErrorRef.current?.(e?.message || String(e))
      }
    }

    const script = document.createElement('script')
    script.async = true
    script.src = 'https://telegram.org/js/telegram-widget.js?22'
    script.setAttribute('data-telegram-login', TELEGRAM_BOT_USERNAME)
    script.setAttribute('data-size', buttonSize)
    script.setAttribute('data-onauth', 'onTelegramAuth')
    script.setAttribute('data-request-access', 'write')
    containerRef.current.innerHTML = ''
    containerRef.current.appendChild(script)

    return () => {
      delete window.onTelegramAuth
    }
  }, [buttonSize])

  if (!TELEGRAM_BOT_USERNAME) return null

  return (
    <div ref={containerRef} className={className} />
  )
}
