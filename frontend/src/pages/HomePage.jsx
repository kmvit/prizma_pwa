import { useState, useEffect } from 'react'

function useBodyClass(className) {
  useEffect(() => {
    document.body.className = className
    return () => { document.body.className = '' }
  }, [className])
}
import { useNavigate, Navigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { api } from '../api/client'

export default function HomePage() {
  const { user, loading } = useAuth()
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [age, setAge] = useState('')
  const [gender, setGender] = useState('')
  const [timer, setTimer] = useState(43144) // 11:59:04 in seconds
  const [timerActive, setTimerActive] = useState(true)
  const [selectOpen, setSelectOpen] = useState(false)

  useEffect(() => {
    if (!user) return
    api.getProfile().then((d) => {
      const u = d.user
      if (u?.name) setName(u.name)
      if (u?.age) setAge(String(u.age))
      if (u?.gender) setGender(u.gender)
    })
    api.getSpecialOfferTimer().then((d) => {
      if (d.active && d.remaining_seconds > 0) {
        setTimerActive(true)
        setTimer(d.remaining_seconds)
      } else {
        setTimerActive(false)
      }
    })
  }, [user])

  useEffect(() => {
    if (!timerActive || timer <= 0) return
    const id = setInterval(() => setTimer((t) => (t > 0 ? t - 1 : 0)), 1000)
    return () => clearInterval(id)
  }, [timerActive, timer])

  const formatTime = (s) => {
    const h = Math.floor(s / 3600)
    const m = Math.floor((s % 3600) / 60)
    const ss = s % 60
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(ss).padStart(2, '0')}`
  }

  const handleStart = async (e) => {
    e.preventDefault()
    if (!user) {
      navigate('/login')
      return
    }
    if (!name.trim() || !age || !gender) {
      alert('Заполните имя, возраст и пол')
      return
    }
    try {
      await api.updateProfile({ name: name.trim(), age: Number(age), gender })
      navigate('/question')
    } catch (err) {
      alert(err.message)
    }
  }

  const handlePayment = async (e) => {
    e.preventDefault()
    if (!user) {
      navigate('/login')
      return
    }
    try {
      const { payment_url } = await api.startPremiumPayment()
      window.location.href = payment_url
    } catch (err) {
      alert(err.message)
    }
  }

  const genderLabel = gender === 'male' ? 'Мужской' : gender === 'female' ? 'Женский' : 'Пол'

  useBodyClass('main quiz-start-page')

  if (loading) return <div className="main quiz-start-page"><div className="page-wrapper"><p>Загрузка...</p></div></div>
  if (user) {
    const to = user.is_paid && user.test_completed ? '/download' : user.is_paid ? '/continue-premium' : '/question'
    return <Navigate to={to} replace />
  }

  return (
    <main className="main quiz-start-page">
      <div className="page-wrapper page-wrapper-quiz-start">
        <div className="logo-wrapper">
          <img src="/images/prizma-logo-bubble.svg" alt="logo" />
        </div>
        <div className="subtitle">Ваш личный ИИ – психолог и наставник</div>
        <h1 className="linear-text page-head">
          Бесплатный
          <br />
          мини–анализ личности
        </h1>
        <div className="quiz-benefits">
          <div className="quiz-benefit"><span>3 страницы анализа</span></div>
          <div className="quiz-benefit"><span>2 базовые методики</span></div>
          <div className="quiz-benefit"><span>3 рекомендации</span></div>
          <div className="quiz-benefit"><span> Личные инсайты</span></div>
        </div>
        <form className="login-form" onSubmit={handleStart}>
          <div className="form-text">Заполните поля, чтобы начать тест:</div>
          <div className="login-form-item">
            <input
              type="text"
              placeholder="Имя"
              className="login-form-input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>
          <div className="login-form-item">
            <input
              type="number"
              placeholder="Возраст"
              className="login-form-input"
              value={age}
              onChange={(e) => setAge(e.target.value)}
              min="1"
              max="120"
              required
            />
          </div>
          <div className="login-form-item">
            <div className="custom-select">
              <div
                className={`select-selected ${selectOpen ? 'select-arrow-active' : ''}`}
                onClick={() => setSelectOpen(!selectOpen)}
              >
                <span className="select-placeholder">{genderLabel}</span>
                <img src="/images/arrow-bottom-icon.svg" alt="" className="custom-arrow" />
              </div>
              <div className={`select-options ${selectOpen ? 'show' : ''}`}>
                <div className="option" data-value="male" onClick={() => { setGender('male'); setSelectOpen(false) }}>Мужской</div>
                <div className="option" data-value="female" onClick={() => { setGender('female'); setSelectOpen(false) }}>Женский</div>
              </div>
            </div>
          </div>
          <button type="submit" className="quiz-form-notice">
            Ответить на 8 вопросов и получить
            мини–анализ БЕСПЛАТНО
          </button>
        </form>
      </div>
      <div className="quiz-benefits-container">
        <div className="quiz-full-benefit-block">
          <div className="quiz-full-title">
            А что в полной расшифровке?
            <span>– целая книга о вас:</span>
          </div>
          <div className="benefits-wrapper">
            <div className="benefit-card">
              <div className="title">100+ страниц</div>
              <p>анализа вашей личности на 360º</p>
              <p>38 глубоких вопросов</p>
            </div>
            <div className="benefit-card">
              <img src="/images/benefits-text-group.svg" alt="" />
            </div>
            <div className="benefit-text-block">
              <div className="text-title">Нас выбирают:</div>
              <p><span>1000+</span> пользователей</p>
              <p>Эксперты и психологи</p>
              <p>Блогеры</p>
              <div className="rating">
                <img src="/images/rate-star-ico.webp" alt="" />
                <img src="/images/rate-star-ico.webp" alt="" />
                <img src="/images/rate-star-ico.webp" alt="" />
                <img src="/images/rate-star-ico.webp" alt="" />
                <img src="/images/rate-star-ico.webp" alt="" />
              </div>
            </div>
          </div>
          <div className="quiz-full-title quiz-full-title-second">
            12 психологических методик
            <span>– помогут понять:</span>
          </div>
          <div className="quiz-test-cards">
            <div className="test-card blocked">
              <div className="card-ico">
                <img src="/images/test-card-ico1.webp" alt="" />
              </div>
              <div className="card-content">
                <div className="card-title">Кто вы на самом деле?</div>
                <div className="card-description"><p>Откройте свой углубленный психологический портрет</p></div>
              </div>
            </div>
            <div className="test-card blocked">
              <div className="card-ico"><img src="/images/test-card-ico2.webp" alt="" /></div>
              <div className="card-content">
                <div className="card-title">Где ваш истинный потенциал?</div>
                <div className="card-description"><p>Изучите полную карту своих талантов - слепые зоны и возможности</p></div>
              </div>
            </div>
            <div className="test-card blocked">
              <div className="card-ico"><img src="/images/test-card-ico3.webp" alt="" /></div>
              <div className="card-content">
                <div className="card-title">Что мешает росту?</div>
                <div className="card-description"><p>Зоны роста и их проработка. Триггеры, сценарии, установки</p></div>
              </div>
            </div>
            <div className="test-card blocked">
              <div className="card-ico"><img src="/images/test-card-ico4.webp" alt="" /></div>
              <div className="card-content">
                <div className="card-title">Ваши отношения с людьми</div>
                <div className="card-description"><p>Совместимость, стратегии разрешения конфликтов, семейные паттерны</p></div>
              </div>
            </div>
          </div>
          <div className="quiz-test-cards quiz-test-cards-big">
            <div className="test-card blocked">
              <div className="card-content">
                <div className="card-title">Что вас ждет в будущем?</div>
                <div className="card-description"><p>Прогностика развития на 1-3 года, исходя из текущих программ поведения</p></div>
              </div>
            </div>
            <div className="test-card blocked">
              <div className="card-content">
                <div className="card-title">Как себя прокачать?</div>
                <div className="card-description"><p>Система компенсаторики. Персональный план развития</p></div>
              </div>
            </div>
          </div>
          <div className="quiz-test-cards">
            <div className="test-card blocked">
              <div className="card-ico"><img src="/images/test-card-ico5.webp" alt="" /></div>
              <div className="card-content">
                <div className="card-title">Как применить знания?</div>
                <div className="card-description"><p>Практическое приложение. Упражнения для развития и роста</p></div>
              </div>
            </div>
            <div className="test-card blocked">
              <div className="card-ico"><img src="/images/test-card-ico6.webp" alt="" /></div>
              <div className="card-content">
                <div className="card-title">Какие ресурсы помогут?</div>
                <div className="card-description"><p>Персональные инструменты: практики, аффирмации, книги, шаблоны</p></div>
              </div>
            </div>
          </div>
          <div className={`action-block-promo ${!timerActive ? 'action-block-promo-expired' : ''}`}>
            <div className="title">Узнайте себя заново уже сегодня!</div>
            <div className="promo-notice">
              <p>Спецпредложение</p>
              <p>для новых пользователей сгорит:</p>
              <div className="promo-duration decoding-offer-time">{formatTime(timer)}</div>
              <a href="/price" className="promo-button" onClick={(e) => { e.preventDefault(); handlePayment(e) }}>
                {timerActive && <img src="/images/promo-fire-ico.webp" className="promo-ico" alt="" />}
                <div className="promo-price">
                  <div className="price-item decoding-offer-button-current-price">1р</div>
                  {timerActive && <div className="price-item-old decoding-offer-button-old-price"><span>1р</span></div>}
                </div>
                <div className="promo-text">
                  <span>Получить</span>
                  полную расшифровку
                </div>
              </a>
            </div>
            <div className="promo-description">Можно оплатить сразу – пройти позже</div>
          </div>
        </div>
      </div>
      <div style={{ textAlign: 'center', padding: '20px', fontSize: '14px' }}>
        <a href="/api/files/policy" target="_blank" rel="noopener noreferrer" style={{ marginRight: '16px' }}>Конфиденциальность</a>
        <a href="/api/files/offerta" target="_blank" rel="noopener noreferrer">Оферта</a>
      </div>
    </main>
  )
}
