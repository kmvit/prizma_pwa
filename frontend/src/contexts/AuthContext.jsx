import { createContext, useContext, useState, useEffect } from 'react'
import { api } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  const checkAuth = async () => {
    try {
      const data = await api.getMe()
      setUser(data)
    } catch {
      setUser(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    checkAuth()
  }, [])

  const register = async (email, password, name) => {
    const res = await api.register(email, password, name)
    await checkAuth()
    return res
  }

  const login = async (email, password) => {
    await api.login(email, password)
    await checkAuth()
  }

  const loginTelegram = async (telegramUser) => {
    await api.loginTelegram(telegramUser)
    await checkAuth()
  }

  const logout = async () => {
    await api.logout()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, register, login, loginTelegram, logout, checkAuth }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
