import { cleanupOutdatedCaches, precacheAndRoute } from 'workbox-precaching'
import { clientsClaim } from 'workbox-core'

self.skipWaiting()
clientsClaim()

cleanupOutdatedCaches()
precacheAndRoute(self.__WB_MANIFEST)

// Web Push: показываем уведомление при получении push
self.addEventListener('push', (event) => {
  let data = { title: 'PRIZMA', body: '' }
  if (event.data) {
    try {
      data = { ...data, ...JSON.parse(event.data.text()) }
    } catch (_) {}
  }
  const options = {
    body: data.body || '',
    icon: '/images/prizma-logo-bubble.svg',
    badge: '/images/prizma-logo-bubble.svg',
    tag: data.tag || 'prizma',
    data: { url: data.url || '/' },
  }
  event.waitUntil(self.registration.showNotification(data.title || 'PRIZMA', options))
})

// Клик по уведомлению — открыть URL
self.addEventListener('notificationclick', (event) => {
  event.notification.close()
  let url = event.notification.data?.url || '/'
  if (!url.startsWith('http')) {
    url = new URL(url, self.location.origin).href
  }
  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      for (const client of clientList) {
        if (client.url.includes(self.location.origin) && 'focus' in client) {
          client.navigate(url)
          return client.focus()
        }
      }
      if (self.clients.openWindow) {
        return self.clients.openWindow(url)
      }
    })
  )
})
