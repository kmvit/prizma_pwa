import { useState, useEffect } from 'react'
import { useNavigate, useLocation, Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import TelegramLoginButton from '../components/TelegramLoginButton'

function useBodyClass(className) {
  useEffect(() => { document.body.className = className; return () => { document.body.className = '' } }, [className])
}

export default function RegisterPage() {
  const { register, loginTelegram } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState(location.state?.name ?? '')
  const [err, setErr] = useState('')

  useBodyClass('bodyLogin')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setErr('')
    try {
      await register(email, password, name)
      navigate('/login')
    } catch (e) {
      setErr(e.message)
    }
  }

  return (
    <main className="main login">
      <div className="login-header">
        <Link to="/"><img src="/images/logo.svg" alt="PRIZMA" /></Link>
        <h1 className="login-title linear-text">Регистрация</h1>
        <p className="login-subtitle">Создайте аккаунт для прохождения теста</p>
      </div>
      <form className="login-form" onSubmit={handleSubmit}>
        <div className="login-form-item">
          <input type="email" placeholder="Email" className="login-form-input" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </div>
        <div className="login-form-item">
          <input type="password" placeholder="Пароль (мин. 6 символов)" className="login-form-input" value={password} onChange={(e) => setPassword(e.target.value)} minLength={6} required />
        </div>
        <div className="login-form-item">
          <input type="text" placeholder="Имя" className="login-form-input" value={name} onChange={(e) => setName(e.target.value)} />
        </div>
        {err && <p style={{ color: '#fb0e12', fontSize: '14px', marginBottom: '10px' }}>{err}</p>}
        <button type="submit" className="button">Зарегистрироваться</button>
        <p style={{ textAlign: 'center', margin: '16px 0 8px', opacity: 0.8, fontSize: '14px' }}>— или —</p>
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <TelegramLoginButton
            onAuth={async (user) => {
              await loginTelegram(user)
              navigate('/')
            }}
            onError={setErr}
            buttonSize="large"
          />
        </div>
      </form>
      <p style={{ textAlign: 'center' }}>Уже есть аккаунт? <Link to="/login">Войти</Link></p>
    </main>
  )
}
