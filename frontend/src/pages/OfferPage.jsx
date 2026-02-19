import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { usePaymentRedirect } from '../hooks/usePaymentRedirect'

function useBodyClass(className) {
  useEffect(() => { document.body.className = className; return () => { document.body.className = '' } }, [className])
}

export default function OfferPage() {
  const redirecting = usePaymentRedirect()
  const [reportStatus, setReportStatus] = useState('generating')
  const [progress, setProgress] = useState(0)
  const [specialOffer, setSpecialOffer] = useState(null)
  const [timer, setTimer] = useState(0)
  const intervalRef = useRef()

  useBodyClass('main quiz-completed-base bodyPrice-offer')

  useEffect(() => {
    let mounted = true
    const checkReport = async () => {
      try {
        const res = await api.getReportsStatus()
        const free = res.free?.status
        if (free === 'COMPLETED') {
          if (mounted) setReportStatus('ready')
          return
        }
        if (free === 'PROCESSING') {
          if (mounted) setReportStatus('generating')
          setTimeout(checkReport, 3000)
          return
        }
        if (free === 'PENDING' || free === 'FAILED') {
          const gen = await api.generateReport()
          if (gen.status === 'processing') setReportStatus('generating')
          else if (gen.status === 'already_exists') setReportStatus('ready')
          setTimeout(checkReport, 3000)
        }
      } catch {
        if (mounted) setReportStatus('error')
      }
    }
    checkReport()
    return () => { mounted = false }
  }, [])

  useEffect(() => {
    api.getSpecialOfferTimer().then((d) => {
      setSpecialOffer(d)
      if (d.active && d.remaining_seconds > 0) setTimer(d.remaining_seconds)
    })
  }, [])

  useEffect(() => {
    if (timer <= 0) return
    const id = setInterval(() => setTimer((t) => (t > 0 ? t - 1 : 0)), 1000)
    return () => clearInterval(id)
  }, [timer])

  useEffect(() => {
    if (reportStatus !== 'generating') return
    intervalRef.current = setInterval(() => {
      setProgress((p) => {
        const inc = 0.05 + Math.random() * 0.15
        const next = Math.min(p + inc, 95)
        if (next >= 95) clearInterval(intervalRef.current)
        return next
      })
    }, 600 + Math.random() * 900)
    return () => clearInterval(intervalRef.current)
  }, [reportStatus])

  const formatTime = (s) => {
    const h = Math.floor(s / 3600)
    const m = Math.floor((s % 3600) / 60)
    const ss = s % 60
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(ss).padStart(2, '0')}`
  }

  const handleDownload = () => api.downloadReport('free')

  const handleBuy = async () => {
    try {
      const { payment_url } = await api.startPremiumPayment()
      window.location.href = payment_url
    } catch (err) {
      alert(err?.message || 'Ошибка оплаты')
    }
  }

  const timerActive = specialOffer?.active && timer > 0
  const currentPrice = timerActive ? (specialOffer?.discount_price ?? 999) : (specialOffer?.original_price ?? specialOffer?.discount_price ?? 999)

  if (redirecting) {
    return <main className="main quiz-completed-base"><div className="page-wrapper"><p>Загрузка...</p></div></main>
  }

  return (
    <main className="main quiz-completed-base">
      <div className="page-wrapper page-wrapper-quiz-start">
        <div className="logo-wrapper">
          <img src="/images/logo.svg" alt="PRIZMA" />
        </div>
        <h1 className="linear-text page-head">Базовый мини–анализ личности готов!</h1>
        <div className="quiz-base-head">
          <div className="quiz-benefits">
            <div className="quiz-benefit"><span>3 страницы анализа</span></div>
            <div className="quiz-benefit"><span>3 рекомендации</span></div>
            <div className="quiz-benefit"><span>2 базовые методики</span></div>
            <div className="quiz-benefit"><span>Личные инсайты</span></div>
          </div>
          <div className="quiz-result">
            <img src="/images/result-ico-pdf.webp" alt="" className="quiz-result-img" onError={(e) => { e.target.style.display = 'none' }} />
            {reportStatus === 'ready' ? (
              <button type="button" className="link-download-result" onClick={handleDownload}>
                <span className="download-file-text"><span>Скачать</span></span>
              </button>
            ) : reportStatus === 'generating' ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
                <div style={{ width: 120, height: 6, background: '#eee', borderRadius: 3, overflow: 'hidden' }}>
                  <div style={{ width: `${progress}%`, height: '100%', background: 'linear-gradient(90deg, #24B1FD 0%, #9B58FB 100%)', transition: 'width 0.3s' }} />
                </div>
                <span style={{ fontSize: 12 }}>Генерируем отчёт...</span>
              </div>
            ) : reportStatus === 'error' ? (
              <span style={{ fontSize: 12, color: '#c00' }}>Ошибка. Попробуйте позже.</span>
            ) : null}
          </div>
        </div>
      </div>

      <div className="quiz-benefits-container">
        <div className="quiz-full-benefit-block">
          <div className="quiz-full-title">А что в полной расшифровке? <span>– целая книга о вас:</span></div>
          <div className="decoding decoding-base">
            <div className="decoding-items" style={{ marginBottom: 24 }}>
              <div className="decoding-item">
                <div className="decoding-item-header">
                  <div className="decoding-item-header-icon"><img src="/images/search-icon.svg" alt="" /></div>
                  <h3 className="decoding-item-header-title"><span>110+</span> страниц глубокого анализа личности</h3>
                </div>
              </div>
              <div className="decoding-item">
                <div className="decoding-item-header">
                  <div className="decoding-item-header-icon"><img src="/images/color-wheel.svg" alt="" /></div>
                  <h3 className="decoding-item-header-title"><span>12</span> психологических методик</h3>
                </div>
              </div>
              <div className="decoding-item">
                <div className="decoding-item-header">
                  <div className="decoding-item-header-icon"><img src="/images/bookmark.svg" alt="" /></div>
                  <h3 className="decoding-item-header-title"><span>50+</span> персональных рекомендаций</h3>
                </div>
              </div>
            </div>

            <div className={`action-block-promo ${!timerActive ? 'action-block-promo-expired' : ''}`}>
              <div className="title">Узнайте себя заново уже сегодня!</div>
              <div className="promo-notice">
                <p>Спецпредложение</p>
                <p>для новых пользователей сгорит:</p>
                <div className="promo-duration decoding-offer-time">{formatTime(timer)}</div>
                <button type="button" className="promo-button decoding-offer-button" onClick={handleBuy}>
                  {timerActive && <img src="/images/promo-fire-ico.webp" className="promo-ico" alt="" />}
                  <div className="promo-price">
                    <div className="price-item decoding-offer-button-current-price">{currentPrice} ₽</div>
                    {timerActive && specialOffer?.original_price && (
                      <div className="price-item-old decoding-offer-button-old-price"><span>{specialOffer.original_price} ₽</span></div>
                    )}
                  </div>
                  <div className="promo-text">
                    <span>Получить</span> полную расшифровку
                  </div>
                </button>
              </div>
              <div className="promo-description">Можно оплатить сразу – пройти позже</div>
            </div>
          </div>
        </div>
      </div>

      <div className="price-links" style={{ padding: '24px 20px' }}>
        <Link to="/" className="price-link">На главную</Link>
      </div>
    </main>
  )
}
