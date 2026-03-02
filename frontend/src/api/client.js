const BASE = '/api'

async function fetchApi(url, options = {}) {
  const res = await fetch(BASE + url, {
    ...options,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || err.error || String(err))
  }
  return res.json()
}

export const api = {
  register: (email, password, name) =>
    fetchApi('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, name }),
    }),

  login: (email, password) =>
    fetchApi('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  loginTelegram: (telegramUser) =>
    fetchApi('/auth/telegram', {
      method: 'POST',
      body: JSON.stringify(telegramUser),
    }),

  logout: () =>
    fetchApi('/auth/logout', { method: 'POST' }),

  getMe: () => fetchApi('/me'),

  getProfile: () => fetchApi('/me/profile'),

  updateProfile: (data) =>
    fetchApi('/me/profile', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getCurrentQuestion: () => fetchApi('/me/current-question'),

  submitAnswer: (textAnswer, answerType = 'text') =>
    fetchApi('/me/answer', {
      method: 'POST',
      body: JSON.stringify({ text_answer: textAnswer, answer_type: answerType }),
    }),

  getProgress: () => fetchApi('/me/progress'),

  generateReport: () =>
    fetchApi('/me/generate-report', { method: 'POST' }),

  getReportStatus: () => fetchApi('/me/report-status'),

  getReportsStatus: () => fetchApi('/me/reports-status'),

  downloadReport: async (type = 'free') => {
    const path = type === 'premium' ? '/me/download/premium-report' : '/me/download/report'
    try {
      const res = await fetch(BASE + path, { credentials: 'include' })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(err.detail || err.error || String(err))
      }
      const blob = await res.blob()
      const disposition = res.headers.get('Content-Disposition')
      const filenameMatch = disposition?.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
      const filename = filenameMatch ? filenameMatch[1].replace(/['"]/g, '') : `prizma-report.${blob.type?.includes('pdf') ? 'pdf' : 'txt'}`
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (e) {
      console.error('Download failed:', e)
      throw e
    }
  },

  generatePremiumReport: () =>
    fetchApi('/me/generate-premium-report', { method: 'POST' }),

  getPremiumReportStatus: () => fetchApi('/me/premium-report-status'),

  startPremiumPayment: () =>
    fetchApi('/me/start-premium-payment', { method: 'POST' }),

  getSpecialOfferTimer: () => fetchApi('/me/special-offer-timer'),

  resetSpecialOfferTimer: () =>
    fetchApi('/me/reset-special-offer-timer', { method: 'POST' }),

  resetTest: () =>
    fetchApi('/me/reset-test', { method: 'POST' }),

  getPushVapidPublic: () => fetchApi('/me/push-vapid-public'),

  pushSubscribe: (subscription) =>
    fetchApi('/me/push-subscribe', {
      method: 'POST',
      body: JSON.stringify(subscription),
    }),

  pushUnsubscribe: (endpoint) =>
    fetchApi('/me/push-subscribe', {
      method: 'DELETE',
      body: JSON.stringify({ endpoint }),
    }),

  sendTestPush: () => fetchApi('/me/send-test-push', { method: 'POST' }),
}
