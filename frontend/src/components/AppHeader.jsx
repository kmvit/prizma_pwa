import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function AppHeader() {
  const { user } = useAuth()

  return (
    <header className="app-header">
      {user ? (
        <span className="app-header-user">
          {user.telegram_username ? `@${user.telegram_username}` : user.name || 'user'} ({user.id})
        </span>
      ) : (
        <Link to="/login" className="app-header-login">Войти</Link>
      )}
    </header>
  )
}
