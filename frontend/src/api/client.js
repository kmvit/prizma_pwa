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

  downloadReport: (type = 'free') => {
    const path = type === 'premium' ? '/me/download/premium-report' : '/me/download/report'
    window.open(BASE + path, '_blank')
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
}
