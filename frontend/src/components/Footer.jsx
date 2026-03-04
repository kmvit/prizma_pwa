export default function Footer() {
  return (
    <footer className="app-footer">
      <div className="app-footer-links">
        <a href="/api/files/policy" target="_blank" rel="noopener noreferrer">Конфиденциальность</a>
        <a href="/api/files/offerta" target="_blank" rel="noopener noreferrer">Оферта</a>
      </div>
      <div className="app-footer-contacts">
        <a href="mailto:myprizma@mail.ru">myprizma@mail.ru</a>
        <span>ИНН: 220455941810</span>
      </div>
    </footer>
  )
}
