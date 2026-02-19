import { useState } from 'react'
import { useInstallPrompt } from '../hooks/useInstallPrompt'

export default function InstallBanner() {
  const { isInstallable, isSafari, triggerInstall, dismiss } = useInstallPrompt()
  const [showSafariHint, setShowSafariHint] = useState(false)

  if (!isInstallable) return null

  const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent)

  return (
    <div
      className="install-banner"
      style={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
        color: '#fff',
        padding: '12px 20px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 12,
        boxShadow: '0 -4px 20px rgba(0,0,0,0.3)',
        zIndex: 9999,
      }}
    >
      <div style={{ fontSize: 14 }}>
        <strong>Установить PRIZMA</strong>
        <span style={{ opacity: 0.9, marginLeft: 6 }}>Доступ с главного экрана</span>
      </div>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', position: 'relative' }}>
        {isSafari ? (
          <div style={{ position: 'relative' }}>
            <button
              type="button"
              onClick={() => setShowSafariHint(!showSafariHint)}
              style={{
                background: 'linear-gradient(90deg, #24B1FD 0%, #9B58FB 100%)',
                color: '#fff',
                border: 'none',
                padding: '8px 16px',
                borderRadius: 8,
                fontWeight: 600,
                cursor: 'pointer',
                fontSize: 14,
              }}
            >
              Как добавить
            </button>
            {showSafariHint && (
              <div
                style={{
                  position: 'absolute',
                  bottom: 'calc(100% + 8px)',
                  left: 0,
                  right: 0,
                  minWidth: 260,
                  padding: 12,
                  background: 'rgba(0,0,0,0.9)',
                  borderRadius: 8,
                  fontSize: 13,
                  lineHeight: 1.5,
                  boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                }}
              >
                {isIOS ? (
                  <>Нажмите <strong>Поделиться</strong> (□↑), затем <strong>«На экран „Домой“»</strong></>
                ) : (
                  <>Меню <strong>Файл</strong> → <strong>«Добавить на Dock»</strong></>
                )}
              </div>
            )}
          </div>
        ) : (
          <button
            type="button"
            onClick={triggerInstall}
            style={{
              background: 'linear-gradient(90deg, #24B1FD 0%, #9B58FB 100%)',
              color: '#fff',
              border: 'none',
              padding: '8px 16px',
              borderRadius: 8,
              fontWeight: 600,
              cursor: 'pointer',
              fontSize: 14,
            }}
          >
            Установить
          </button>
        )}
        <button
          type="button"
          onClick={dismiss}
          style={{
            background: 'transparent',
            color: 'rgba(255,255,255,0.8)',
            border: '1px solid rgba(255,255,255,0.3)',
            padding: '8px 12px',
            borderRadius: 8,
            cursor: 'pointer',
            fontSize: 13,
          }}
        >
          Позже
        </button>
      </div>
    </div>
  )
}
