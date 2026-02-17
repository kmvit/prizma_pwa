import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { usePaymentRedirect } from '../hooks/usePaymentRedirect'

function useBodyClass(className) {
  useEffect(() => { document.body.className = className; return () => { document.body.className = '' } }, [className])
}

export default function ContinuePremiumPage() {
  const navigate = useNavigate()
  const redirecting = usePaymentRedirect()

  useBodyClass('main quiz-start-page')

  const handleContinue = (e) => {
    e.preventDefault()
    navigate('/question')
  }

  if (redirecting) {
    return <div className="main quiz-start-page"><div className="page-wrapper"><p>Загрузка...</p></div></div>
  }

  return (
    <main className="main quiz-start-page">
      <div className="page-wrapper page-wrapper-quiz-start">
        <div className="logo-wrapper">
          <img src="/images/prizma-logo-bubble.svg" alt="logo" />
        </div>
        <div className="subtitle">Ваш личный ИИ – психолог и наставник</div>
        <h1 className="linear-text page-head">
          Полная
          <br />
          расшифровка личности
        </h1>
        <div className="quiz-benefits">
          <div className="quiz-benefit"><span>110+ страниц анализа</span></div>
          <div className="quiz-benefit"><span>12 методик</span></div>
          <div className="quiz-benefit"><span>38 вопросов</span></div>
          <div className="quiz-benefit"><span>50+ рекомендаций</span></div>
        </div>
        <div className="login-form">
          <button type="button" className="quiz-form-notice" onClick={handleContinue}>
            Продолжить или начать тест
          </button>
        </div>
      </div>
      <div className="quiz-benefits-container">
        <div className="quiz-full-benefit-block">
          <div className="quiz-full-title">
            Ваша полная расшифровка
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
        </div>
      </div>
    </main>
  )
}
