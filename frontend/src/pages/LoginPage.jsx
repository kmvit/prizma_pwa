import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import TelegramLoginButton from '../components/TelegramLoginButton'

function useBodyClass(className) {
  useEffect(() => { document.body.className = className; return () => { document.body.className = '' } }, [className])
}

export default function LoginPage() {
  useBodyClass('bodyLogin')

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
