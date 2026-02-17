import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

function useBodyClass(className) {
  useEffect(() => { document.body.className = className; return () => { document.body.className = '' } }, [className])
}

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [err, setErr] = useState('')

  useBodyClass('bodyLogin')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setErr('')
    try {
      await login(email, password)
      navigate('/')
    } catch (e) {
      setErr(e.message)
    }
  }

  return (
    <main className="main login">
      <div className="login-header">
        <Link to="/"><img src="/images/logo.svg" alt="PRIZMA" /></Link>
        <h1 className="login-title linear-text">Давайте познакомимся!</h1>
        <p className="login-subtitle">Введите свои данные ниже.<br />Они ВАЖНЫ для результатов вашего аудита</p>
      </div>
      <form className="login-form" onSubmit={handleSubmit}>
        <div className="login-form-item">
          <input type="email" placeholder="Email" className="login-form-input" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </div>
        <div className="login-form-item">
          <input type="password" placeholder="Пароль" className="login-form-input" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </div>
        {err && <p style={{ color: '#fb0e12', fontSize: '14px', marginBottom: '10px' }}>{err}</p>}
        <button type="submit" className="button">Войти</button>
      </form>
      <p style={{ textAlign: 'center' }}>Нет аккаунта? <Link to="/register">Регистрация</Link></p>
    </main>
  )
}
