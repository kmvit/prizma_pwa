import { useState, useEffect } from 'react'

const DISMISS_KEY = 'prizma_install_dismissed'
const DISMISS_DAYS = 7

export function useInstallPrompt() {
  const [deferredPrompt, setDeferredPrompt] = useState(null)
  const [isInstallable, setIsInstallable] = useState(false)
  const [isInstalled, setIsInstalled] = useState(false)

  useEffect(() => {
    const handler = (e) => {
      e.preventDefault()
      setDeferredPrompt(e)
      setIsInstallable(true)
    }

    const hide = () => {
      setIsInstalled(true)
      setIsInstallable(false)
      setDeferredPrompt(null)
    }

    if (window.matchMedia('(display-mode: standalone)').matches) {
      setIsInstalled(true)
      return
    }
    if (navigator.standalone === true) {
      setIsInstalled(true)
      return
    }
    if (document.referrer.includes('android-app://')) {
      setIsInstalled(true)
      return
    }

    const dismissed = localStorage.getItem(DISMISS_KEY)
    if (dismissed) {
      const d = parseInt(dismissed, 10)
      if (Date.now() - d < DISMISS_DAYS * 24 * 60 * 60 * 1000) return
    }

    window.addEventListener('beforeinstallprompt', handler)
    window.addEventListener('appinstalled', hide)

    return () => {
      window.removeEventListener('beforeinstallprompt', handler)
      window.removeEventListener('appinstalled', hide)
    }
  }, [])

  const triggerInstall = async () => {
    if (!deferredPrompt) return
    deferredPrompt.prompt()
    const { outcome } = await deferredPrompt.userChoice
    if (outcome === 'accepted') {
      setDeferredPrompt(null)
      setIsInstallable(false)
    }
  }

  const dismiss = () => {
    localStorage.setItem(DISMISS_KEY, String(Date.now()))
    setIsInstallable(false)
    setDeferredPrompt(null)
  }

  return { isInstallable, isInstalled, triggerInstall, dismiss }
}
