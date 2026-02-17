import { useEffect, useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { api } from '../api/client'

/**
 * Редирект на правильную страницу по статусу оплаты и прохождения тестов.
 * - Оплативший + премиум НЕ пройден → /question
 * - Оплативший + премиум пройден → /download
 * - Бесплатный + free пройден → /offer
 * - Бесплатный + free НЕ пройден → остаётся
 */
export function usePaymentRedirect() {
  const navigate = useNavigate()
  const location = useLocation()
  const pathname = location.pathname
  const [checking, setChecking] = useState(true)

  useEffect(() => {
    api.getMe()
      .then((me) => {
        const redirectTo = getRedirectForPath(pathname, me)
        if (redirectTo) {
          navigate(redirectTo, { replace: true })
        }
      })
      .catch(() => {})
      .finally(() => setChecking(false))
  }, [pathname, navigate])

  return checking
}

function getRedirectForPath(path, me) {
  if (!me) return null
  const paid = !!me.is_paid
  const completed = !!me.test_completed

  // /offer — только для бесплатных после free теста. Оплативший → continue-premium или download
  if (path === '/offer' && paid) {
    return completed ? '/download' : '/continue-premium'
  }

  // /price — оплатившему не нужна
  if (path === '/price' && paid) {
    return '/download'
  }

  // /question — free завершил free → offer; paid завершил premium → download
  if (path === '/question') {
    if (!paid && completed) return '/offer'
    if (paid && completed) return '/download'
  }

  // /continue-premium — только для оплативших, премиум не пройден. Иначе редирект
  if (path === '/continue-premium') {
    if (!paid) return '/'
    if (completed) return '/download'
  }

  // /answers — оплативший, но премиум не пройден → страница «продолжить тест»
  if (path === '/answers' && paid && !completed) {
    return '/continue-premium'
  }

  // /download — бесплатный ещё не прошёл тест → /question
  if (path === '/download' && !paid && !completed) {
    return '/question'
  }

  return null
}
