import { useEffect, useState } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { api } from '../api/client'

/**
 * Обработка redirect от Telegram Login Widget.
 * Telegram перенаправляет сюда после авторизации с query-параметрами.
 */
export default function TelegramAuthCallbackPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [status, setStatus] = useState('Ожидание...')

  useEffect(() => {
    const hash = searchParams.get('hash')
    if (!hash) {
      setStatus('Ошибка: нет данных авторизации')
      setTimeout(() => navigate('/login'), 2000)
      return
    }

    const payload = {
      id: parseInt(searchParams.get('id') || '0', 10),
      first_name: searchParams.get('first_name') || '',
      last_name: searchParams.get('last_name') || undefined,
      username: searchParams.get('username') || undefined,
      photo_url: searchParams.get('photo_url') || undefined,
      auth_date: parseInt(searchParams.get('auth_date') || '0', 10),
      hash,
    }

    setStatus('Вход...')
    api
      .loginTelegram(payload)
      .then(() => {
        window.location.replace('/question')
      })
      .catch((e) => {
        setStatus(`Ошибка: ${e?.message || 'не удалось войти'}`)
        setTimeout(() => navigate('/login'), 2000)
      })
  }, [searchParams, navigate])

  return (
    <main className="main login">
      <div className="login-header">
        <h1 className="login-title linear-text">{status}</h1>
      </div>
    </main>
  )
}
