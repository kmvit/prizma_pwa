import { useEffect } from 'react'
import { Link, Navigate } from 'react-router-dom'
import TelegramLoginButton from '../components/TelegramLoginButton'
import { useAuth } from '../contexts/AuthContext'

function useBodyClass(className) {
  useEffect(() => { document.body.className = className; return () => { document.body.className = '' } }, [className])
}

export default function LoginPage() {
  const { user, loading } = useAuth()
  useBodyClass('bodyLogin')

  if (loading) {
    return (
      <main className="main login">
        <div className="login-header">
          <h1 className="login-title linear-text">Загрузка...</h1>
        </div>
      </main>
    )
  }

  if (user) {
    const to = user.is_paid && user.test_completed ? '/download' : user.is_paid ? '/continue-premium' : '/question'
    return <Navigate to={to} replace />
  }

  return (
    <main className="main login">
      <div className="login-header">
        <Link to="/"><img src="/images/logo.svg" alt="PRIZMA" /></Link>
        <h1 className="login-title linear-text">Давайте познакомимся!</h1>
        <p className="login-subtitle">Войдите через Telegram, чтобы начать тест</p>
      </div>
      <div className="login-form">
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <TelegramLoginButton buttonSize="large" />
        </div>
      </div>
    </main>
  )
}
