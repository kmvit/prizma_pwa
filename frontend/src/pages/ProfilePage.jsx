import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { api } from '../api/client'

function useBodyClass(className) {
  useEffect(() => { document.body.className = className; return () => { document.body.className = '' } }, [className])
}

export default function ProfilePage() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [age, setAge] = useState('')
  const [gender, setGender] = useState('')
  const [selectOpen, setSelectOpen] = useState(false)

  useBodyClass('bodyLogin')

  useEffect(() => {
    if (user) {
      api.getProfile().then((d) => {
        const u = d.user
        setName(u.name || '')
        setAge(u.age || '')
        setGender(u.gender || '')
      })
    }
  }, [user])

  const handleSave = async (e) => {
    e.preventDefault()
    try {
      await api.updateProfile({ name, age: Number(age), gender })
      navigate('/')
    } catch (err) {
      alert(err.message)
    }
  }

  const genderLabel = gender === 'male' ? 'Мужской' : gender === 'female' ? 'Женский' : 'Пол'

  return (
    <main className="main login">
      <div className="login-header">
        <img src="/images/logo.svg" alt="PRIZMA" />
        <h1 className="login-title linear-text">Профиль</h1>
        <p className="login-subtitle">Редактируйте данные для теста</p>
      </div>
      <form className="login-form" onSubmit={handleSave}>
        <div className="login-form-item">
          <input type="text" placeholder="Имя" className="login-form-input" value={name} onChange={(e) => setName(e.target.value)} />
        </div>
        <div className="login-form-item">
          <input type="number" placeholder="Возраст" className="login-form-input" value={age} onChange={(e) => setAge(e.target.value)} min="1" max="120" />
        </div>
        <div className="login-form-item">
          <div className="custom-select">
            <div className={`select-selected ${selectOpen ? 'select-arrow-active' : ''}`} onClick={() => setSelectOpen(!selectOpen)}>
              <span className="select-placeholder">{genderLabel}</span>
              <img src="/images/arrow-bottom-icon.svg" alt="" className="custom-arrow" />
            </div>
            <div className={`select-options ${selectOpen ? 'show' : ''}`}>
              <div className="option" onClick={() => { setGender('male'); setSelectOpen(false) }}>Мужской</div>
              <div className="option" onClick={() => { setGender('female'); setSelectOpen(false) }}>Женский</div>
            </div>
          </div>
        </div>
        <button type="submit" className="button">Сохранить</button>
      </form>
      <button type="button" className="button button-gray" onClick={logout}>Выйти</button>
      <p style={{ textAlign: 'center', marginTop: '16px' }}><Link to="/">На главную</Link></p>
    </main>
  )
}
