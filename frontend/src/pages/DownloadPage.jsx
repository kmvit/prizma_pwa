import { useState, useEffect, useMemo } from 'react'
import { api } from '../api/client'
import { usePaymentRedirect } from '../hooks/usePaymentRedirect'
import { useAuth } from '../contexts/AuthContext'
import { buildTelegramBotUrl } from '../utils/telegram'

const TELEGRAM_BOT_USERNAME = import.meta.env.VITE_TELEGRAM_BOT_USERNAME || ''

function useBodyClass(className) {
  useEffect(() => { document.body.className = className; return () => { document.body.className = '' } }, [className])
}

export default function DownloadPage() {
  const redirecting = usePaymentRedirect()
  const { user } = useAuth()
  const [status, setStatus] = useState(null)

  useBodyClass('bodyDownload')

  const telegramBotUrl = useMemo(
    () => buildTelegramBotUrl(TELEGRAM_BOT_USERNAME, user?.email),
    [user?.email]
  )

  useEffect(() => {
    api.getReportsStatus().then(setStatus)
  }, [])

  const [downloadError, setDownloadError] = useState(null)
  const handleDownloadFree = async () => {
    setDownloadError(null)
    try {
      await api.downloadReport('free')
    } catch (e) {
      setDownloadError(e?.message || 'Не удалось скачать')
    }
  }
  const handleDownloadPremium = async () => {
    setDownloadError(null)
    try {
      await api.downloadReport('premium')
    } catch (e) {
      setDownloadError(e?.message || 'Не удалось скачать')
    }
  }

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
              <button type="button" className="decoding-download-button" onClick={handleDownloadFree}>
                <span className="download-file-text"><span>Скачать бесплатный отчёт</span></span>
              </button>
            )}
            {premiumReady && (
              <button type="button" className="decoding-download-button" onClick={handleDownloadPremium}>
                <span className="download-file-text"><span>Скачать премиум отчёт</span></span>
              </button>
            )}
            {telegramBotUrl && (
              <a
                href={telegramBotUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="decoding-download-button decoding-telegram-button"
              >
                <svg className="telegram-icon" viewBox="0 0 24 24" width="20" height="20" aria-hidden>
                  <path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.2.2 0 00-.05-.18c-.06-.05-.14-.03-.21-.02-.09.02-1.49.95-4.22 2.79-.4.27-.76.41-1.08.4-.36-.01-1.04-.2-1.55-.37-.63-.2-1.12-.31-1.08-.66.02-.18.27-.36.74-.55 2.92-1.27 4.86-2.11 5.83-2.51 2.78-1.16 3.35-1.36 3.73-1.36.08 0 .27.02.39.12.1.08.13.19.14.27-.01.06.01.24 0 .38z"/>
                </svg>
                <span className="download-file-text"><span>Открыть в Telegram</span></span>
              </a>
            )}
          </div>
        </div>
      </div>
      {downloadError && (
        <p style={{ textAlign: 'center', marginTop: 24, color: '#c00' }}>{downloadError}</p>
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
