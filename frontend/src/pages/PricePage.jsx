import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { usePaymentRedirect } from '../hooks/usePaymentRedirect'

function useBodyClass(className) {
  useEffect(() => { document.body.className = className; return () => { document.body.className = '' } }, [className])
}

export default function PricePage() {
  const redirecting = usePaymentRedirect()
  const [specialOffer, setSpecialOffer] = useState(null)

  useBodyClass('bodyPrice')

  useEffect(() => {
    api.getSpecialOfferTimer().then(setSpecialOffer)
  }, [])

  const handleBuy = async () => {
    try {
      const { payment_url } = await api.startPremiumPayment()
      window.location.href = payment_url
    } catch (err) {
      alert(err?.message || 'Ошибка оплаты')
    }
  }

  const currentPrice = specialOffer?.discount_price ?? specialOffer?.original_price ?? 999

  if (redirecting) {
    return <main className="main price"><div className="price-logo"><p>Загрузка...</p></div></main>
  }

  return (
    <main className="main price">
      <div className="price-logo">
        <img src="/images/logo.svg" alt="PRIZMA" />
      </div>
      <div className="decoding decoding-base">
        <h2 className="decoding-title decoding-title-price">Базовая расшифровка</h2>
        <div className="decoding-body">
          <div className="decoding-list">
            <div className="decoding-list-item">
              <img src="/images/done-icon.svg" alt="" />
              <span>3 страницы анализа</span>
            </div>
            <div className="decoding-list-item">
              <img src="/images/done-icon.svg" alt="" />
              <span>3 рекомендации</span>
            </div>
            <div className="decoding-list-item">
              <img src="/images/done-icon.svg" alt="" />
              <span>2 базовые методики</span>
            </div>
            <div className="decoding-list-item">
              <img src="/images/done-icon.svg" alt="" />
              <span>Личные инсайты</span>
            </div>
          </div>
        </div>
      </div>

      <div className="decoding">
        <h2 className="decoding-title decoding-title-price">Полная расшифровка</h2>
        <div className="decoding-items">
          <div className="decoding-item">
            <div className="decoding-item-header">
              <div className="decoding-item-header-icon">
                <img src="/images/search-icon.svg" alt="" />
              </div>
              <h3 className="decoding-item-header-title"><span>110+</span> страниц глубокого анализа личности</h3>
            </div>
            <div className="decoding-item-list">
              <div className="decoding-item-list-item"><span>Аналитика</span> — психотип, слабые и сильные стороны</div>
              <div className="decoding-item-list-item"><span>Компенсаторика</span> — стратегии улучшения</div>
              <div className="decoding-item-list-item"><span>Прогностика</span> на 3–5 лет</div>
            </div>
          </div>
          <div className="decoding-item">
            <div className="decoding-item-header">
              <div className="decoding-item-header-icon">
                <img src="/images/color-wheel.svg" alt="" />
              </div>
              <h3 className="decoding-item-header-title"><span>12</span> психологических методик</h3>
            </div>
          </div>
          <div className="decoding-item">
            <div className="decoding-item-header">
              <div className="decoding-item-header-icon">
                <img src="/images/bookmark.svg" alt="" />
              </div>
              <h3 className="decoding-item-header-title"><span>50+</span> персональных рекомендаций</h3>
            </div>
          </div>
          <div className="decoding-item">
            <div className="decoding-item-header">
              <div className="decoding-item-header-icon">
                <img src="/images/AI.svg" alt="" />
              </div>
              <h3 className="decoding-item-header-title">Продвинутая модель ИИ</h3>
            </div>
          </div>
        </div>
        <div className="decoding-buy">
          <p className="decoding-buy-price">{currentPrice} ₽</p>
          <p className="decoding-buy-price-text">рублей</p>
          <button className="decoding-buy-button" onClick={handleBuy}>Оплатить</button>
        </div>
      </div>

      <div className="price-links">
        <Link to="/" className="price-link">На главную</Link>
      </div>
    </main>
  )
}
