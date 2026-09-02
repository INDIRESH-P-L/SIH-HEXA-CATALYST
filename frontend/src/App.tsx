import { Navigate, Route, Routes } from 'react-router-dom'

import { Shell } from './components/layout/Shell'
import { Spinner } from './components/common'
import { useAuth } from './lib/auth'
import { needsInitialAssessment, needsOnboarding } from './lib/onboarding'

import AdminDashboard from './pages/AdminDashboard'
import Architecture from './pages/Architecture'
import Assessments from './pages/Assessments'
import Assistant from './pages/Assistant'
import CourseDetail from './pages/CourseDetail'
import Dashboard from './pages/Dashboard'
import InitialAssessment from './pages/InitialAssessment'
import LandingPage from './pages/LandingPage'
import Login from './pages/Login'
import MyCompetencies from './pages/MyCompetencies'
import Onboarding from './pages/Onboarding'
import Recommendations from './pages/Recommendations'
import TrainerConsole from './pages/TrainerConsole'

/**
 * Route guard.
 *
 * Checks authentication and role, then redirects officers who have no
 * competency evidence on file to the onboarding wizard.
 *
 * This is a convenience for the interface, not a security boundary: every
 * endpoint re-checks the caller's role server-side against the database. Hiding
 * a link never grants or denies access on its own.
 */
function RequireRole({
  role,
  children,
}: {
  role?: 'trainer' | 'admin'
  children: React.ReactNode
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

  if (needsOnboarding(user)) return <Navigate to="/onboarding" replace />
  // Gate: assessed users (employees without initial_assessment_completed) go to the assessment.
  if (needsInitialAssessment(user)) return <Navigate to="/initial-assessment" replace />

  return <>{children}</>
}

/**
 * The wizard's own guard — the mirror image of the one above.
 *
 * Re-entering the wizard is destructive: it appends a self-declaration for
 * every competency, which supersedes assessment evidence in the ledger. So an
 * officer who is already onboarded is sent away rather than allowed back in by
 * a typed URL or a stale bookmark.
 */
function RequireOnboarding({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="flex min-h-full items-center justify-center py-20">
        <Spinner label="Restoring your session" />
      </div>
    )
  }
  if (!user) return <Navigate to="/login" replace />
  if (!needsOnboarding(user)) return <Navigate to="/" replace />

  return <>{children}</>
}

/**
 * Assessment guard — for the /initial-assessment route.
 * Redirects away if the user doesn't need to take it.
 */
function RequireInitialAssessment({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="flex min-h-full items-center justify-center py-20">
        <Spinner label="Restoring your session" />
      </div>
    )
  }
  if (!user) return <Navigate to="/login" replace />
  if (needsOnboarding(user)) return <Navigate to="/onboarding" replace />
  if (!needsInitialAssessment(user)) return <Navigate to="/" replace />

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

      {/* Onboarding wizard — only for officers who have not been through it */}
      <Route
        path="/onboarding"
        element={
          <RequireOnboarding>
            <Onboarding />
          </RequireOnboarding>
        }
      />

      {/* Initial competency assessment — after onboarding, before recommendations */}
      <Route
        path="/initial-assessment"
        element={
          <RequireInitialAssessment>
            <InitialAssessment />
          </RequireInitialAssessment>
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
