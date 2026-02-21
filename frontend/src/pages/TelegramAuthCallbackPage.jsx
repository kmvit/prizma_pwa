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

    // Передаем все поля от Telegram как есть:
    // подпись считается по полному набору параметров (кроме hash).
    const payload = Object.fromEntries(searchParams.entries())

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
