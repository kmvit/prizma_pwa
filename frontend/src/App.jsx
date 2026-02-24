import { Fragment } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './contexts/AuthContext'
import InstallBanner from './components/InstallBanner'
import HomePage from './pages/HomePage'
import RegisterPage from './pages/RegisterPage'
import LoginPage from './pages/LoginPage'
import ProfilePage from './pages/ProfilePage'
import QuestionPage from './pages/QuestionPage'
import LoadingPage from './pages/LoadingPage'
import OfferPage from './pages/OfferPage'
import AnswersPage from './pages/AnswersPage'
import PricePage from './pages/PricePage'
import DownloadPage from './pages/DownloadPage'
import DownloadReportByLinkPage from './pages/DownloadReportByLinkPage'
import PaymentSuccessPage from './pages/PaymentSuccessPage'
import PaymentFailPage from './pages/PaymentFailPage'
import ContinuePremiumPage from './pages/ContinuePremiumPage'

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="loading-screen">Загрузка...</div>
  if (!user) return <Navigate to="/" replace />
  return children
}

export default function App() {
  return (
    <Fragment>
      <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/profile"
        element={
          <ProtectedRoute>
            <ProfilePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/continue-premium"
        element={
          <ProtectedRoute>
            <ContinuePremiumPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/question"
        element={
          <ProtectedRoute>
            <QuestionPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/loading"
        element={
          <ProtectedRoute>
            <LoadingPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/offer"
        element={
          <ProtectedRoute>
            <OfferPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/answers"
        element={
          <ProtectedRoute>
            <AnswersPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/price"
        element={
          <ProtectedRoute>
            <PricePage />
          </ProtectedRoute>
        }
      />
      <Route path="/download/premium-report/:telegramId" element={<DownloadReportByLinkPage type="premium" />} />
      <Route path="/download/report/:telegramId" element={<DownloadReportByLinkPage type="free" />} />
      <Route
        path="/download"
        element={
          <ProtectedRoute>
            <DownloadPage />
          </ProtectedRoute>
        }
      />
      <Route path="/payment/success" element={<PaymentSuccessPage />} />
      <Route path="/payment/fail" element={<PaymentFailPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <InstallBanner />
    </Fragment>
  )
}
