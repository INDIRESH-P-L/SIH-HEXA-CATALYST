/**
 * Application shell.
 *
 * Navigation is grouped by the architecture's own layers — foundation,
 * measure, decide, observe — rather than by an arbitrary menu order, so the
 * interface reads the same way the system is built.
 *
 * Fixed 240px sidebar at >=1024px, collapsing to a drawer below. 56px top bar.
 * Content capped at 1200px.
 */
import { useState } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import {
  BarChart3,
  BookOpen,
  GraduationCap,
  LayoutDashboard,
  LogOut,
  Menu,
  MessageSquare,
  Network,
  Target,
  Upload,
  X,
  type LucideIcon,
} from 'lucide-react'

import { useAuth } from '../../lib/auth'

interface NavItem {
  to: string
  label: string
  icon: LucideIcon
  requires?: 'trainer' | 'admin'
}

interface NavGroup {
  label: string
  items: NavItem[]
}

const NAV: NavGroup[] = [
  {
    label: 'Overview',
    items: [{ to: '/', label: 'Dashboard', icon: LayoutDashboard }],
  },
  {
    label: 'Foundation',
    items: [{ to: '/competencies', label: 'My competencies', icon: Target }],
  },
  {
    label: 'Decide',
    items: [
      { to: '/recommendations', label: 'Recommendations', icon: BookOpen },
      { to: '/assistant', label: 'Learning assistant', icon: MessageSquare },
    ],
  },
  {
    label: 'Measure',
    items: [
      { to: '/assessments', label: 'Assessments', icon: GraduationCap },
      { to: '/trainer', label: 'Trainer console', icon: Upload, requires: 'trainer' },
    ],
  },
  {
    label: 'Observe',
    items: [{ to: '/admin', label: 'Workforce analytics', icon: BarChart3, requires: 'admin' }],
  },
  {
    label: 'Reference',
    items: [{ to: '/architecture', label: 'System architecture', icon: Network }],
  },
]

function NavList({ onNavigate }: { onNavigate?: () => void }) {
  const { isTrainer, isAdmin } = useAuth()

  const visible = NAV.map((group) => ({
    ...group,
    items: group.items.filter((item) => {
      if (item.requires === 'trainer') return isTrainer
      if (item.requires === 'admin') return isAdmin
      return true
    }),
  })).filter((group) => group.items.length > 0)

  return (
    <nav aria-label="Main" className="space-y-4">
      {visible.map((group) => (
        <div key={group.label}>
          <p className="mb-1 px-3 font-mono text-11 font-medium uppercase tracking-[0.08em] text-ink-3">
            {group.label}
          </p>
          <ul className="space-y-0.5">
            {group.items.map(({ to, label, icon: Icon }) => (
              <li key={to}>
                <NavLink
                  to={to}
                  end={to === '/'}
                  onClick={onNavigate}
                  className={({ isActive }) =>
                    `flex min-h-[44px] items-center gap-3 rounded px-3 text-14 transition-colors ${
                      isActive
                        ? 'bg-accent-wash font-medium text-accent'
                        : 'text-ink-2 hover:bg-surface-2 hover:text-ink'
                    }`
                  }
                >
                  <Icon size={16} strokeWidth={1.5} aria-hidden />
                  {label}
                </NavLink>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </nav>
  )
}

export function Shell({ children }: { children: React.ReactNode }) {
  const { user, signOut } = useAuth()
  const [drawerOpen, setDrawerOpen] = useState(false)
  const location = useLocation()

  return (
    <div className="min-h-full bg-paper">
      <header className="fixed inset-x-0 top-0 z-30 flex h-topbar items-center justify-between border-b border-rule bg-surface px-4 lg:px-6">
        <div className="flex items-center gap-3">
          <button
            type="button"
            className="inline-flex h-11 w-11 items-center justify-center rounded text-ink-2 hover:bg-surface-2 lg:hidden"
            onClick={() => setDrawerOpen((open) => !open)}
            aria-label={drawerOpen ? 'Close navigation' : 'Open navigation'}
            aria-expanded={drawerOpen}
          >
            {drawerOpen ? <X size={20} strokeWidth={1.5} /> : <Menu size={20} strokeWidth={1.5} />}
          </button>
          <div className="leading-tight">
            <p className="text-14 font-semibold text-ink">Skill Intelligence Platform</p>
            <p className="hidden text-11 text-ink-3 sm:block">
              Ministry of Statistics and Programme Implementation
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {user && (
            <div className="hidden text-right leading-tight sm:block">
              <p className="text-13 font-medium text-ink">{user.profile.full_name}</p>
              <p className="text-11 text-ink-3">
                {user.profile.job_role?.title ?? user.profile.designation ?? 'Officer'}
              </p>
            </div>
          )}
          <button
            type="button"
            onClick={signOut}
            className="inline-flex h-11 w-11 items-center justify-center rounded text-ink-2 hover:bg-surface-2"
            aria-label="Sign out"
          >
            <LogOut size={18} strokeWidth={1.5} />
          </button>
        </div>
      </header>

      <aside className="fixed left-0 top-topbar z-20 hidden h-[calc(100%-56px)] w-60 overflow-y-auto border-r border-rule bg-surface p-3 lg:block">
        <NavList />
      </aside>

      {drawerOpen && (
        <>
          <div
            className="fixed inset-0 top-topbar z-20 bg-ink/20 lg:hidden"
            onClick={() => setDrawerOpen(false)}
            aria-hidden
          />
          <aside className="fixed left-0 top-topbar z-30 h-[calc(100%-56px)] w-60 overflow-y-auto border-r border-rule bg-surface p-3 lg:hidden">
            <NavList onNavigate={() => setDrawerOpen(false)} />
          </aside>
        </>
      )}

      <main className="pt-topbar lg:pl-60">
        <div
          key={location.pathname}
          className="mx-auto max-w-content animate-fade-in px-4 py-6 lg:px-8"
        >
          {children}
        </div>
      </main>
    </div>
  )
}
