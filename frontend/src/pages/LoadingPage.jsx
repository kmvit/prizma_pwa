import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { usePaymentRedirect } from '../hooks/usePaymentRedirect'

function useBodyClass(className) {
  useEffect(() => { document.body.className = className; return () => { document.body.className = '' } }, [className])
}

export default function LoadingPage() {
  const navigate = useNavigate()
  const redirecting = usePaymentRedirect()
  const [status, setStatus] = useState('generating')
  const [progress, setProgress] = useState(0)
  const [statusText, setStatusText] = useState('Анализируем ваши ответы...')
  const intervalRef = useRef()

  useBodyClass('bodyLoading')

  useEffect(() => {
    if (redirecting) return
    let mounted = true
    const check = async () => {
      try {
        const me = await api.getMe()
        const res = await api.getReportsStatus()
        const isPaid = me?.is_paid

        if (isPaid) {
          const premium = res.premium?.status
          if (premium === 'COMPLETED') {
            if (mounted) navigate('/download', { replace: true })
            return
          }
          if (premium === 'PROCESSING') {
            if (mounted) setStatus('generating')
            setTimeout(check, 3000)
            return
          }
          if (premium === 'PENDING' || premium === 'FAILED') {
            const gen = await api.generatePremiumReport().catch(() => ({}))
            if (gen?.status === 'processing') setStatus('generating')
            setTimeout(check, 3000)
          }
          return
        }

        const free = res.free?.status
        if (free === 'COMPLETED') {
          if (mounted) navigate('/offer', { replace: true })
          return
        }
        if (free === 'PROCESSING') {
          if (mounted) setStatus('generating')
          setTimeout(check, 3000)
          return
        }
        if (free === 'PENDING' || free === 'FAILED') {
          const gen = await api.generateReport()
          if (gen.status === 'processing') setStatus('generating')
          else if (gen.status === 'already_exists') {
            if (mounted) navigate('/offer', { replace: true })
            return
          }
          setTimeout(check, 3000)
        }
      } catch {
        if (mounted) setStatus('error')
      }
    }
    check()
    return () => { mounted = false }
  }, [navigate, redirecting])

  useEffect(() => {
    if (status !== 'generating') return
    intervalRef.current = setInterval(() => {
      setProgress((p) => {
        const inc = 0.05 + Math.random() * 0.15
        const next = Math.min(p + inc, 95)
        if (next >= 95) clearInterval(intervalRef.current)
        return next
      })
    }, 600 + Math.random() * 900)
    return () => clearInterval(intervalRef.current)
  }, [status])

  const handleDownload = () => api.downloadReport('free')

  return (
    <main className="main loading">
      <div className="loading-header">
        <img src="/images/logo.svg" alt="PRIZMA" />
        <h1 className="loading-title linear-text">Анализируем ваши ответы</h1>
      </div>
      <div className="loading-animation">
        <div className="loading-spinner">
          <div className="spinner-ring" />
          <div className="spinner-ring" />
          <div className="spinner-ring" />
        </div>
        <div className="progress-container">
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${progress}%` }} />
          </div>
          <div className="progress-text">{Math.round(progress)}%</div>
        </div>
      </div>
      <div className="loading-time">
        <div>{statusText}</div>
        {status === 'ready' && <button type="button" className="button" onClick={handleDownload}>Скачать отчет</button>}
        {status === 'generating' && <div className="loading-hint">Это может занять до 5-10 минут</div>}
      </div>
      <div className="loading-links">
        <a href="/" className="price-link">На главную</a>
      </div>
    </main>
  )
}
