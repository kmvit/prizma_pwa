import { useEffect } from 'react'
import { Link } from 'react-router-dom'

function useBodyClass(className) {
  useEffect(() => { document.body.className = className; return () => { document.body.className = '' } }, [className])
}

export default function PaymentFailPage() {
  useBodyClass('bodyPayment')

  return (
    <main className="main payment">
      <img src="/images/logo.svg" alt="PRIZMA" className="payment-logo" />
      <div className="payment-body">
        <img src="/images/cross-icon.svg" alt="" className="payment-icon uncomplete-payment-icon" />
        <h1 className="payment-title linear-text uncomplete-payment-title">Оплата не выполнена</h1>
        <p className="payment-text uncomplete-payment-text">
          Попробуйте позже или свяжитесь с поддержкой.
          <span>Вы можете повторить попытку оплаты.</span>
        </p>
        <Link to="/price" className="button" style={{ marginTop: 20 }}>Повторить оплату</Link>
        <Link to="/" className="price-link" style={{ display: 'block', marginTop: 16 }}>На главную</Link>
      </div>
    </main>
  )
}
