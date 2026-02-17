import { useInstallPrompt } from '../hooks/useInstallPrompt'

export default function InstallBanner() {
  const { isInstallable, triggerInstall, dismiss } = useInstallPrompt()

  if (!isInstallable) return null

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
      <div style={{ display: 'flex', gap: 8 }}>
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
