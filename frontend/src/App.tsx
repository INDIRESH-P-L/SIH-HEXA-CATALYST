import { Navigate, Route, Routes } from 'react-router-dom'

import { Shell } from './components/layout/Shell'
import { Spinner } from './components/common'
import { useAuth } from './lib/auth'

import AdminDashboard from './pages/AdminDashboard'
import Architecture from './pages/Architecture'
import Assessments from './pages/Assessments'
import Assistant from './pages/Assistant'
import CourseDetail from './pages/CourseDetail'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import MyCompetencies from './pages/MyCompetencies'
import Recommendations from './pages/Recommendations'
import TrainerConsole from './pages/TrainerConsole'

/**
 * Route guard.
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
      <Route path="/login" element={user ? <Navigate to="/" replace /> : <Login />} />

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
