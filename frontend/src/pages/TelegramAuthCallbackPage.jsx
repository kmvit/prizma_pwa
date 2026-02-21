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
    const hash = searchParams.get('hash')
    if (!hash) {
      setStatus('Ошибка: нет данных авторизации')
      setTimeout(() => navigate('/login'), 2000)
      return
    }

    const payload = Object.fromEntries(searchParams.entries())

    const login = async () => {
      try {
        setStatus('Вход...')
        await api.loginTelegram(payload)
        await checkAuth()
        if (!cancelled) navigate('/question', { replace: true })
      } catch (e) {
        if (!cancelled) {
          setStatus(`Ошибка: ${e?.message || 'не удалось войти'}`)
          setTimeout(() => navigate('/login'), 2000)
        }
      }
    }

    login()
    return () => { cancelled = true }
  }, [searchParams, navigate, checkAuth])

  return (
    <main className="main login">
      <div className="login-header">
        <h1 className="login-title linear-text">{status}</h1>
      </div>
    </main>
  )
}
