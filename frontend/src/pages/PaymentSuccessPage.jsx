import { useEffect } from 'react'
import { useSearchParams, Link } from 'react-router-dom'

function useBodyClass(className) {
  useEffect(() => { document.body.className = className; return () => { document.body.className = '' } }, [className])
}

export default function PaymentSuccessPage() {
  const [params] = useSearchParams()
  const invId = params.get('inv_id')

  useBodyClass('bodyPayment')

  return (
    <main className="main payment">
      <img src="/images/logo.svg" alt="PRIZMA" className="payment-logo" />
      <div className="payment-body">
        <img src="/images/check-icon.svg" alt="" className="payment-icon" />
        <h1 className="payment-title linear-text">Оплата <br /> успешно прошла!</h1>
        {invId && <p className="payment-price">Заказ #{invId}</p>}
        <p className="payment-text">
          Ответьте на премиум-вопросы и получите полную расшифровку.
          <span>Или перейдите на страницу загрузок.</span>
        </p>
        <Link to="/continue-premium" className="button" style={{ marginTop: 20 }}>Продолжить тест</Link>
        <Link to="/download" className="price-link" style={{ display: 'block', marginTop: 16 }}>К загрузкам</Link>
        <Link to="/" className="price-link" style={{ display: 'block', marginTop: 8 }}>На главную</Link>
      </div>
    </main>
  )
}
