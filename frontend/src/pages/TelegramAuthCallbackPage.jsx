import { useEffect, useState } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../contexts/AuthContext'

/**
 * Обработка redirect от Telegram Login Widget.
 * Telegram перенаправляет сюда после авторизации с query-параметрами.
 */
export default function TelegramAuthCallbackPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { checkAuth } = useAuth()
  const [status, setStatus] = useState('Ожидание...')

  useEffect(() => {
    let cancelled = false
    console.debug('[TG_CALLBACK] opened', {
      href: window.location.href,
      search: window.location.search,
    })

    const hash = searchParams.get('hash')
    if (!hash) {
      console.warn('[TG_CALLBACK] missing hash, redirect to /login')
      setStatus('Ошибка: нет данных авторизации')
      setTimeout(() => navigate('/login'), 2000)
      return
    }

    // Передаем все поля от Telegram как есть:
    // подпись считается по полному набору параметров (кроме hash).
    const payload = Object.fromEntries(searchParams.entries())
    console.debug('[TG_CALLBACK] payload keys', Object.keys(payload))

    const login = async () => {
      try {
        setStatus('Вход...')
        console.debug('[TG_CALLBACK] calling /api/auth/telegram')
        await api.loginTelegram(payload)
        console.debug('[TG_CALLBACK] /api/auth/telegram ok, checking auth context')
        await checkAuth()
        console.debug('[TG_CALLBACK] checkAuth done, navigate /question')
        if (!cancelled) navigate('/question', { replace: true })
      } catch (e) {
        console.error('[TG_CALLBACK] login failed', e)
        if (!cancelled) {
          setStatus(`Ошибка: ${e?.message || 'не удалось войти'}`)
          setTimeout(() => navigate('/login'), 2000)
        }
      }
    }

    login()
    return () => {
      cancelled = true
    }
  }, [searchParams, navigate, checkAuth])

  return (
    <main className="main login">
      <div className="login-header">
        <h1 className="login-title linear-text">{status}</h1>
      </div>
    </main>
  )
}
