import { useState, useCallback } from 'react'
import { api } from '../api/client'

/**
 * Хук для подписки на Web Push уведомления об акциях.
 * Запрашивает разрешение, подписывается и отправляет subscription на backend.
 */
export function usePushSubscription() {
  const [status, setStatus] = useState('idle') // idle | loading | granted | denied | unsupported | error
  const [error, setError] = useState(null)

  const subscribe = useCallback(async () => {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
      setStatus('unsupported')
      return false
    }

    setStatus('loading')
    setError(null)

    try {
      const { vapid_public_key } = await api.getPushVapidPublic()
      if (!vapid_public_key) {
        setError('Push не настроен на сервере')
        setStatus('error')
        return false
      }

      const reg = await navigator.serviceWorker.ready
      const perm = await Notification.requestPermission()
      if (perm !== 'granted') {
        setStatus('denied')
        return false
      }

      const subscription = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(vapid_public_key),
      })

      const subJson = subscription.toJSON()
      await api.pushSubscribe({
        endpoint: subJson.endpoint,
        keys: subJson.keys,
      })

      setStatus('granted')
      return true
    } catch (e) {
      setError(e.message || 'Ошибка подписки')
      setStatus('error')
      return false
    }
  }, [])

  const unsubscribe = useCallback(async () => {
    if (!('serviceWorker' in navigator)) return
    try {
      const reg = await navigator.serviceWorker.ready
      const sub = await reg.pushManager.getSubscription()
      if (sub) {
        await api.pushUnsubscribe(sub.endpoint)
        await sub.unsubscribe()
      }
      setStatus('idle')
    } catch (e) {
      setError(e.message)
      setStatus('error')
    }
  }, [])

  return { subscribe, unsubscribe, status, error }
}

function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4)
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/')
  const rawData = atob(base64)
  const outputArray = new Uint8Array(rawData.length)
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i)
  }
  return outputArray
}
