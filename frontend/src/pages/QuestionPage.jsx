import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { usePaymentRedirect } from '../hooks/usePaymentRedirect'

function useBodyClass(className) {
  useEffect(() => { document.body.className = className; return () => { document.body.className = '' } }, [className])
}

export default function QuestionPage() {
  const navigate = useNavigate()
  const redirecting = usePaymentRedirect()
  const [data, setData] = useState(null)
  const [answer, setAnswer] = useState('')
  const [loading, setLoading] = useState(true)

  useBodyClass('bodyQuestion')

  useEffect(() => {
    loadQuestion()
  }, [])

  const redirectAfterTestCompleted = async (isFree) => {
    if (isFree) navigate('/offer')
    else navigate('/loading')
  }

  const loadQuestion = async () => {
    try {
      const d = await api.getCurrentQuestion()
      setData(d)
      setAnswer('')
    } catch (e) {
      if (e.message?.includes('уже завершен')) {
        try {
          const me = await api.getMe()
          redirectAfterTestCompleted(!me?.is_paid)
        } catch {
          navigate('/loading')
        }
      } else {
        alert(e.message)
      }
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (answer.length < 350) {
      alert('Ответ должен быть не менее 350 символов')
      return
    }
    try {
      const res = await api.submitAnswer(answer)
      if (res.status === 'test_completed') {
        const isFree = res.is_paid !== true
        redirectAfterTestCompleted(isFree)
      } else {
        setData({ question: res.next_question, progress: res.progress, user: data?.user })
        setAnswer('')
      }
    } catch (err) {
      alert(err.message)
    }
  }

  if (redirecting || loading || !data) {
    return (
      <main className="main question">
        <p className="question-title">Загрузка...</p>
      </main>
    )
  }

  const { question, progress } = data

  return (
    <main className="main question">
      <div className="question-header">
        <div className="question-prev-button-container">
          <h1 className="question-num linear-text">Вопрос <span className="current-question">{progress?.current}</span> из <span className="question-count">{progress?.total}</span></h1>
        </div>
        <p className="question-title" id="questionText">{question.text}</p>
      </div>
      <div className="question-area-container">
        <p className="question-area-note"><span>*</span> Ваши ответы должны быть более 350 знаков<br />Отвечайте неторопливо, подробно и вдумчиво</p>
        <form onSubmit={handleSubmit}>
          <textarea className="question-area" id="questionArea" value={answer} onChange={(e) => setAnswer(e.target.value)} placeholder="Ваш ответ..." minLength={350} maxLength={5000} required />
          <div className="question-submit-wrap">
            <button type="submit" className="button-triangle">
              <span>Следующий вопрос</span>
              <img src="/images/button-triangle.svg" alt="" />
            </button>
          </div>
        </form>
      </div>
    </main>
  )
}
