import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import TelegramLoginButton from '../components/TelegramLoginButton'

function useBodyClass(className) {
  useEffect(() => { document.body.className = className; return () => { document.body.className = '' } }, [className])
}

export default function LoginPage() {
  const { loginTelegram } = useAuth()
  const [err, setErr] = useState('')

  useBodyClass('bodyLogin')

  return (
    <main className="main login">
      <div className="login-header">
        <Link to="/"><img src="/images/logo.svg" alt="PRIZMA" /></Link>
        <h1 className="login-title linear-text">Давайте познакомимся!</h1>
        <p className="login-subtitle">Войдите через Telegram, чтобы начать тест</p>
      </div>
      <div className="login-form">
        {err && <p style={{ color: '#fb0e12', fontSize: '14px', marginBottom: '10px', textAlign: 'center' }}>{err}</p>}
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <TelegramLoginButton
            onAuth={async (user) => {
              await loginTelegram(user)
              window.location.replace('/')
            }}
            onError={setErr}
            buttonSize="large"
          />
        </div>
      </div>
    </main>
  )
}
