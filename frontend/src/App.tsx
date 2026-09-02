import { Navigate, Route, Routes } from 'react-router-dom'

import { Shell } from './components/layout/Shell'
import { Spinner } from './components/common'
import { useAuth } from './lib/auth'
import { isOnboarded } from './lib/onboarding'

import AdminDashboard from './pages/AdminDashboard'
import Architecture from './pages/Architecture'
import Assessments from './pages/Assessments'
import Assistant from './pages/Assistant'
import CourseDetail from './pages/CourseDetail'
import Dashboard from './pages/Dashboard'
import LandingPage from './pages/LandingPage'
import Login from './pages/Login'
import MyCompetencies from './pages/MyCompetencies'
import Onboarding from './pages/Onboarding'
import Recommendations from './pages/Recommendations'
import TrainerConsole from './pages/TrainerConsole'

/**
 * Route guard.
 *
 * Checks authentication and role, then redirects new officers (those who have
 * not yet completed the onboarding wizard) to /onboarding.
 *
 * This is a convenience for the interface, not a security boundary: every
 * endpoint re-checks the caller's role server-side against the database. Hiding
 * a link never grants or denies access on its own.
 */
function RequireRole({
  role,
  children,
  skipOnboardingCheck = false,
}: {
  role?: 'trainer' | 'admin'
  children: React.ReactNode
  skipOnboardingCheck?: boolean
}) {
  const { user, loading, isTrainer, isAdmin } = useAuth()

  if (loading) {
    return (
      <div className="flex min-h-full items-center justify-center py-20">
        <Spinner label="Restoring your session" />
      </div>
    )
  }
  if (!user) return <Navigate to="/login" replace />
  if (role === 'trainer' && !isTrainer) return <Navigate to="/" replace />
  if (role === 'admin' && !isAdmin) return <Navigate to="/" replace />

  // Redirect new officers to the onboarding wizard before they see the dashboard.
  // The /onboarding route itself sets skipOnboardingCheck=true to avoid a loop.
  if (!skipOnboardingCheck && !isOnboarded(user.id, user.email)) {
    return <Navigate to="/onboarding" replace />
  }

  return <>{children}</>
}

export default function App() {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="flex min-h-full items-center justify-center">
        <Spinner label="Loading" />
      </div>
    )
  }

  return (
    <Routes>
      {/* Public Landing Page & Portal */}
      <Route path="/portal" element={<LandingPage />} />
      <Route path="/landing" element={<LandingPage />} />

      {/* Unauthenticated Home goes to LandingPage */}
      {!user && <Route path="/" element={<LandingPage />} />}

      {/* Direct Login Page */}
      <Route path="/login" element={user ? <Navigate to="/" replace /> : <Login />} />

      {/* Onboarding wizard — authenticated but bypasses the onboarded check */}
      <Route
        path="/onboarding"
        element={
          <RequireRole skipOnboardingCheck>
            <Onboarding />
          </RequireRole>
        }
      />

      {/* Authenticated Officer Portal */}
      <Route
        path="/*"
        element={
          <RequireRole>
            <Shell>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/competencies" element={<MyCompetencies />} />
                <Route path="/recommendations" element={<Recommendations />} />
                <Route path="/courses/:courseId" element={<CourseDetail />} />
                <Route path="/assessments" element={<Assessments />} />
                <Route path="/assistant" element={<Assistant />} />
                <Route path="/architecture" element={<Architecture />} />
                <Route
                  path="/trainer"
                  element={
                    <RequireRole role="trainer">
                      <TrainerConsole />
                    </RequireRole>
                  }
                />
                <Route
                  path="/admin"
                  element={
                    <RequireRole role="admin">
                      <AdminDashboard />
                    </RequireRole>
                  }
                />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </Shell>
          </RequireRole>
        }
      />
    </Routes>
  )
}
