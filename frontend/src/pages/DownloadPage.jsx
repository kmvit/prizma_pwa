import { useState, useEffect } from 'react'
import { api } from '../api/client'
import { usePaymentRedirect } from '../hooks/usePaymentRedirect'
import { usePushSubscription } from '../hooks/usePushSubscription'

function useBodyClass(className) {
  useEffect(() => { document.body.className = className; return () => { document.body.className = '' } }, [className])
}

export default function DownloadPage() {
  const redirecting = usePaymentRedirect()
  const { subscribe, status: pushStatus } = usePushSubscription()
  const [status, setStatus] = useState(null)

  useBodyClass('bodyDownload')

  useEffect(() => {
    api.getReportsStatus().then(setStatus)
  }, [])

  if (redirecting || !status) {
    return (
      <main className="main download">
        <div className="download-header">
          <img src="/images/logo.svg" alt="PRIZMA" />
          <p style={{ marginTop: 20 }}>Загрузка...</p>
        </div>
      </main>
    )
  }

  const freeReady = status.free?.status === 'COMPLETED'
  const premiumReady = status.premium?.status === 'COMPLETED'
  const premiumProcessing = status.premium?.status === 'PROCESSING'

  return (
    <main className="main download">
      <div className="download-top">
        <div className="download-header">
          <img src="/images/logo.svg" alt="PRIZMA" />
        </div>
        <div className="decoding">
          <h2 className="decoding-title">ВАША ПОЛНАЯ <br /> РАСШИФРОВКА ГОТОВА!</h2>
          <div className="decoding-items">
            <div className="decoding-item">
              <div className="decoding-item-header">
                <div className="decoding-item-header-icon">
                  <img src="/images/search-icon.svg" alt="" />
                </div>
                <h3 className="decoding-item-header-title"><span>110+</span> страниц глубокого анализа личности</h3>
              </div>
              <div className="decoding-item-list">
                <div className="decoding-item-list-item">
                  <span>Аналитика</span> <br />
                  (ваш психотип, слабые и сильные стороны, взаимодействие с окружающими, программы поведения, триггеры)
                </div>
                <div className="decoding-item-list-item">
                  <span>Компенсаторика</span> <br />
                  (ваши стратегии того, что можно улучшить и как это сделать)
                </div>
                <div className="decoding-item-list-item">
                  <span>Прогностика</span> на 3-5 лет — возможные сценарии развития вашей жизни
                </div>
              </div>
            </div>
            <div className="decoding-item">
              <div className="decoding-item-header">
                <div className="decoding-item-header-icon">
                  <img src="/images/color-wheel.svg" alt="" />
                </div>
                <h3 className="decoding-item-header-title"><span>12</span> психологических методик</h3>
              </div>
            </div>
            <div className="decoding-item">
              <div className="decoding-item-header">
                <div className="decoding-item-header-icon">
                  <img src="/images/bookmark.svg" alt="" />
                </div>
                <h3 className="decoding-item-header-title"><span>50+</span> персональных рекомендаций, ресурсов и инструментов</h3>
              </div>
            </div>
            <div className="decoding-item">
              <div className="decoding-item-header">
                <div className="decoding-item-header-icon">
                  <img src="/images/AI.svg" alt="" />
                </div>
                <h3 className="decoding-item-header-title">Продвинутая и точная модель ИИ</h3>
              </div>
            </div>
          </div>
          <div className="decoding-download">
            <div className="decoding-download-image">
              <img src="/images/file.png" alt="" />
            </div>
            {freeReady && (
              <a href="/api/me/download/report" download className="decoding-download-button">
                <span className="download-file-text"><span>Скачать бесплатный отчёт</span></span>
              </a>
            )}
            {premiumReady && (
              <a href="/api/me/download/premium-report" download className="decoding-download-button">
                <span className="download-file-text"><span>Скачать премиум отчёт</span></span>
              </a>
            )}
          </div>
        </div>
      </div>
      {pushStatus !== 'granted' && pushStatus !== 'unsupported' && pushStatus !== 'denied' && (
        <div style={{ margin: '24px 20px', padding: 16, background: 'rgba(36,177,253,0.1)', borderRadius: 8, textAlign: 'center' }}>
          <p style={{ margin: '0 0 10px', fontSize: 14, color: '#2B2D68' }}>Получать напоминания об акциях?</p>
          <button
            type="button"
            style={{ padding: '8px 20px', background: 'linear-gradient(90deg, #24B1FD 0%, #9B58FB 100%)', border: 'none', borderRadius: 8, color: '#fff', fontWeight: 600, cursor: 'pointer', fontSize: 14 }}
            onClick={subscribe}
            disabled={pushStatus === 'loading'}
          >
            {pushStatus === 'loading' ? 'Подписка...' : 'Включить уведомления'}
          </button>
        </div>
      )}
      {(premiumProcessing || (!freeReady && !premiumReady && !premiumProcessing)) && (
        <p style={{ textAlign: 'center', marginTop: 24 }}>
          {premiumProcessing && <>Премиум отчёт генерируется...</>}
          {!freeReady && !premiumReady && !premiumProcessing && <>Отчёты пока не готовы. Проверьте страницу позже.</>}
        </p>
      )}
    </main>
  )
}
