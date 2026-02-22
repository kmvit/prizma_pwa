import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'

/**
 * Публичная страница для скачивания отчёта по ссылке из Telegram-уведомления.
 * Открывается без авторизации, получает файл через fetch и программно запускает скачивание.
 * @param {object} props
 * @param {'free'|'premium'} props.type - free: бесплатный отчёт, premium: премиум-отчёт
 */
export default function DownloadReportByLinkPage({ type = 'free' }) {
  const { telegramId } = useParams()
  const [status, setStatus] = useState('loading') // loading | success | error
  const [message, setMessage] = useState('')

  useEffect(() => {
    if (!telegramId) {
      setStatus('error')
      setMessage('Неверная ссылка')
      return
    }

    let cancelled = false

    async function doDownload() {
      try {
        const apiPath = type === 'premium' ? '/api/download/premium-report' : '/api/download/report'
        const res = await fetch(`${apiPath}/${telegramId}`)
        if (cancelled) return

        if (!res.ok) {
          const err = await res.json().catch(() => ({ detail: res.statusText }))
          const detail = err.detail || err.error || 'Ошибка при загрузке'
          setStatus('error')
          setMessage(detail)
          return
        }

        const blob = await res.blob()
        if (cancelled) return

        const disposition = res.headers.get('Content-Disposition')
        const filenameMatch = disposition?.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
        const filename = filenameMatch
          ? filenameMatch[1].replace(/['"]/g, '').trim()
          : `prizma-report-${telegramId}.${blob.type?.includes('pdf') ? 'pdf' : 'txt'}`

        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = filename
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)

        if (!cancelled) {
          setStatus('success')
        }
      } catch (e) {
        if (!cancelled) {
          setStatus('error')
          setMessage(e?.message || 'Не удалось скачать отчёт')
        }
      }
    }

    doDownload()
    return () => { cancelled = true }
  }, [telegramId, type])

  return (
    <main className="main download" style={{ minHeight: '60vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ textAlign: 'center', padding: 24 }}>
        <img src="/images/logo.svg" alt="PRIZMA" style={{ marginBottom: 24 }} />
        {status === 'loading' && <p>Скачивание отчёта...</p>}
        {status === 'success' && (
          <p style={{ color: 'var(--accent, #4ade80)' }}>✓ Отчёт скачан! Проверьте папку загрузок.</p>
        )}
        {status === 'error' && (
          <p style={{ color: '#ef4444' }}>{message}</p>
        )}
      </div>
    </main>
  )
}
