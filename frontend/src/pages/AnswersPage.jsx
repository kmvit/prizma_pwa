import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { usePaymentRedirect } from '../hooks/usePaymentRedirect'

function useBodyClass(className) {
  useEffect(() => { document.body.className = className; return () => { document.body.className = '' } }, [className])
}

export default function AnswersPage() {
  const redirecting = usePaymentRedirect()
  const [progress, setProgress] = useState(null)
  const [openIndex, setOpenIndex] = useState(0)

  useBodyClass('bodyAnswers')

  useEffect(() => {
    api.getProgress().then(setProgress)
  }, [])

  if (redirecting || !progress) return <main className="main answers"><div className="answers-logo"><p>Загрузка...</p></div></main>

  const answers = progress.answers || []
  const total = progress.progress?.total || 0
  const answered = progress.progress?.answered || 0

  return (
    <main className="main answers">
      <div className="answers-logo">
        <img src="/images/logo.svg" alt="PRIZMA" />
      </div>
      <h1 className="answers-title linear-text">Ваши ответы</h1>
      <p className="answers-subtitle">Отвечено: {answered} из {total}</p>
      <div id="answers-acc">
        {answers.map((a, i) => {
          const q = typeof a.question === 'object' ? a.question : null
          const qNum = q?.order_number ?? i + 1
          const questionText = q?.text?.slice(0, 80) || `Вопрос ${qNum}`
          const isOpen = openIndex === i
          return (
            <div key={i} className="answers-acc-item">
              <button
                type="button"
                className={`answers-acc-header ${isOpen ? 'active' : ''}`}
                onClick={() => setOpenIndex(isOpen ? -1 : i)}
              >
                {questionText}{questionText.length >= 80 ? '…' : ''}
              </button>
              <div className="answers-acc-content" style={{ display: isOpen ? 'block' : 'none', padding: '0 0 22px 0', borderBottom: '1px solid #e5e5e5' }}>
                <p>{a.text_answer || '—'}</p>
              </div>
            </div>
          )
        })}
      </div>
      <Link to="/download" className="button button-answers">Скачать отчет</Link>
      <p style={{ textAlign: 'center', marginTop: 24 }}><Link to="/">На главную</Link></p>
    </main>
  )
}
