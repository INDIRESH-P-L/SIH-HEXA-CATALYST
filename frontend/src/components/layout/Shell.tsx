import { useState } from 'react'
import { NavLink, useLocation, Link } from 'react-router-dom'
import {
  BarChart3,
  BookOpen,
  GraduationCap,
  Home,
  LayoutDashboard,
  LogOut,
  Menu,
  MessageSquare,
  Search,
  Shield,
  Target,
  Upload,
  Users,
  X,
  type LucideIcon,
} from 'lucide-react'

import { useAuth } from '../../lib/auth'

interface NavItem {
  to: string
  label: string
  subtitle?: string
  icon: LucideIcon
  requires?: 'trainer' | 'admin'
  badge?: string
}

interface NavGroup {
  label: string
  items: NavItem[]
}

const OFFICER_NAV: NavGroup[] = [
  {
    label: 'Karmayogi Hubs',
    items: [
      { to: '/', label: 'Officer Dashboard', subtitle: 'Overview & gaps', icon: LayoutDashboard },
      { to: '/competencies', label: 'Competency Hub', subtitle: 'FRAC 4-point profiler', icon: Target },
      { to: '/recommendations', label: 'Learning Hub', subtitle: 'iGOT / NSSTA courses', icon: BookOpen },
      { to: '/assessments', label: 'Assessment Hub', subtitle: 'Deterministic scoring', icon: GraduationCap },
      { to: '/assistant', label: 'Learning Assistant', subtitle: 'Grounded AI tutor', icon: MessageSquare, badge: 'AI' },
    ],
  },
  {
    label: 'Public Portal',
    items: [
      { to: '/portal', label: 'Karmayogi Public Portal', subtitle: 'Landing & stats', icon: Home },
    ],
  },
]

const ADMIN_NAV: NavGroup[] = [
  {
    label: 'Admin Control Center',
    items: [
      { to: '/admin', label: 'Account Management', subtitle: 'Manage accounts & unblock', icon: Users },
      { to: '/admin/analytics', label: 'Workforce Analytics', subtitle: 'Marts & k-anonymity', icon: BarChart3 },
      { to: '/portal', label: 'Karmayogi Public Portal', subtitle: 'Landing & stats', icon: Home },
    ],
  },
]

const TRAINER_NAV: NavGroup[] = [
  {
    label: 'Trainer Academy',
    items: [
      { to: '/trainer', label: 'Trainer Studio', subtitle: 'MCQ generator & gate', icon: Upload },
      { to: '/portal', label: 'Karmayogi Public Portal', subtitle: 'Landing & stats', icon: Home },
    ],
  },
]

function NavList({ onNavigate }: { onNavigate?: () => void }) {
  const { user, isTrainer, isAdmin } = useAuth()

  const visible = isAdmin
    ? ADMIN_NAV
    : isTrainer
    ? TRAINER_NAV
    : OFFICER_NAV.map((group) => ({
        ...group,
        items: group.items.filter((item) => {
          if (item.requires === 'trainer') return isTrainer
          return true
        }),
      })).filter((group) => group.items.length > 0)

  return (
    <div className="flex h-full flex-col justify-between">
      <nav aria-label="Main" className="space-y-6">
        {visible.map((group) => (
          <div key={group.label}>
            <p className="mb-2 px-3 text-10 font-bold uppercase tracking-wider text-slate-600">
              {group.label}
            </p>
            <ul className="space-y-1">
              {group.items.map(({ to, label, subtitle, icon: Icon, badge }) => (
                <li key={to}>
                  <NavLink
                    to={to}
                    end={to === '/' || to === '/admin' || to === '/trainer'}
                    onClick={onNavigate}
                    className={({ isActive }) =>
                      `group relative flex items-center justify-between rounded-xl px-3 py-2.5 transition-all ${
                        isActive
                          ? 'bg-[#0B3060] text-white shadow-sm font-semibold'
                          : 'text-slate-700 hover:bg-slate-100/80 hover:text-slate-900 font-medium'
                      }`
                    }
                  >
                    {({ isActive }) => (
                      <>
                        <div className="flex items-center gap-3 min-w-0">
                          <div
                            className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${
                              isActive
                                ? 'bg-white/10 text-amber-300'
                                : 'bg-slate-100 text-[#0B3060] group-hover:bg-slate-200'
                            }`}
                          >
                            <Icon size={16} strokeWidth={isActive ? 2 : 1.75} />
                          </div>
                          <div className="truncate">
                            <span className="block text-13 leading-tight truncate">{label}</span>
                            {subtitle && (
                              <span
                                className={`block text-10 truncate leading-tight ${
                                  isActive ? 'text-slate-300' : 'text-slate-600'
                                }`}
                              >
                                {subtitle}
                              </span>
                            )}
                          </div>
                        </div>

                        {badge && (
                          <span
                            className={`rounded px-1.5 py-0.5 text-9 font-extrabold uppercase ${
                              isActive
                                ? 'bg-amber-400 text-[#0B3060]'
                                : 'bg-amber-100 text-[#D96B0B]'
                            }`}
                          >
                            {badge}
                          </span>
                        )}
                      </>
                    )}
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>

      {/* Cadre Badge at Bottom of Sidebar */}
      {user && (
        isAdmin ? (
          <div className="mt-6 rounded-xl border border-indigo-200 bg-gradient-to-br from-slate-50 to-indigo-50/40 p-3.5 shadow-xs">
            <div className="flex items-center gap-2 mb-1.5">
              <Shield size={13} className="text-indigo-600" />
              <span className="text-10 font-bold uppercase tracking-wider text-[#0B3060]">
                Platform Administrator
              </span>
            </div>
            <div className="text-12 font-bold text-slate-900 truncate">
              {user.profile.full_name}
            </div>
            <div className="text-11 font-semibold text-indigo-700 truncate">
              System Administration
            </div>
            <div className="mt-2 pt-2 border-t border-indigo-100 flex items-center justify-between text-10 text-slate-600 font-mono">
              <span>Security Scope:</span>
              <span className="font-bold text-[#0B3060]">ACCOUNT_MGMT</span>
            </div>
          </div>
        ) : isTrainer ? (
          <div className="mt-6 rounded-xl border border-amber-300 bg-gradient-to-br from-amber-50 to-orange-50/40 p-3.5 shadow-xs">
            <div className="flex items-center gap-2 mb-1.5">
              <Upload size={13} className="text-amber-700" />
              <span className="text-10 font-bold uppercase tracking-wider text-[#0B3060]">
                Academy Trainer
              </span>
            </div>
            <div className="text-12 font-bold text-slate-900 truncate">
              {user.profile.full_name}
            </div>
            <div className="text-11 font-semibold text-amber-900 truncate">
              NSSTA Training Academy
            </div>
            <div className="mt-2 pt-2 border-t border-amber-200 flex items-center justify-between text-10 text-slate-600 font-mono">
              <span>Studio Access:</span>
              <span className="font-bold text-[#0B3060]">MCQ_GATEWAY</span>
            </div>
          </div>
        ) : (
          <div className="mt-6 rounded-xl border border-amber-200 bg-gradient-to-br from-[#FFF9F2] to-white p-3.5 shadow-xs">
            <div className="flex items-center gap-2 mb-1.5">
              <span className="flex h-2 w-2 rounded-full bg-emerald-500" />
              <span className="text-10 font-bold uppercase tracking-wider text-[#0B3060]">
                SPARROW APAR Connected
              </span>
            </div>
            <div className="text-12 font-bold text-slate-900 truncate">
              {user.profile.full_name}
            </div>
            <div className="text-11 text-slate-500 truncate">
              {user.profile.job_role?.title ?? 'Statistical Officer'}
            </div>
            <div className="mt-2 pt-2 border-t border-amber-100 flex items-center justify-between text-10 text-slate-600 font-mono">
              <span>Framework:</span>
              <span className="font-bold text-[#0B3060]">FRAC-2026.1</span>
            </div>
          </div>
        )
      )}
    </div>
  )
}

export function Shell({ children }: { children: React.ReactNode }) {
  const { user, signOut, isAdmin, isTrainer } = useAuth()
  const [drawerOpen, setDrawerOpen] = useState(false)
  const location = useLocation()

  return (
    <div className="min-h-full bg-[#F4F6F9]">
      {/* Top Tricolor Strip */}
      <div className="fixed inset-x-0 top-0 z-40">
        <div className="tricolor-strip" />
      </div>

      {/* Main Top Header */}
      <header className="fixed inset-x-0 top-[4px] z-30 flex h-[62px] items-center justify-between border-b border-slate-200/90 bg-white px-4 lg:px-6 shadow-xs">
        {/* Left: Brand & Mobile Trigger */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            className="inline-flex h-10 w-10 items-center justify-center rounded-lg text-slate-600 hover:bg-slate-100 lg:hidden"
            onClick={() => setDrawerOpen((open) => !open)}
            aria-label={drawerOpen ? 'Close navigation' : 'Open navigation'}
            aria-expanded={drawerOpen}
          >
            {drawerOpen ? <X size={20} strokeWidth={1.5} /> : <Menu size={20} strokeWidth={1.5} />}
          </button>

          <Link
            to={isAdmin ? "/admin" : isTrainer ? "/trainer" : "/"}
            className="flex items-center gap-3 group shrink-0"
          >
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-[#0B3060] to-[#154399] text-white shadow-xs">
              <svg viewBox="0 0 24 24" className="h-6 w-6 fill-current" aria-hidden="true">
                <path d="M12 2L14.5 8.5L21.5 9.5L16.5 14.5L18 21.5L12 18L6 21.5L7.5 14.5L2.5 9.5L9.5 8.5L12 2Z" fill="#F58220" />
                <circle cx="12" cy="13" r="3.5" fill="#FFFFFF" />
                <circle cx="12" cy="13" r="1.5" fill="#0B3060" />
              </svg>
            </div>
            <div className="flex flex-col justify-center">
              <div className="flex items-center gap-2">
                <span className="text-15 font-extrabold tracking-tight text-[#0B3060] whitespace-nowrap">कर्मयोगी भारत</span>
                <span className="hidden sm:inline-block text-10 font-bold text-[#D96B0B] bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200 uppercase tracking-wide whitespace-nowrap">
                  {isAdmin ? 'ADMIN CONSOLE' : isTrainer ? 'TRAINER STUDIO' : 'iGOT MoSPI'}
                </span>
              </div>
              <p className="hidden md:block text-10 font-medium text-slate-500 whitespace-nowrap">
                Ministry of Statistics & Programme Implementation
              </p>
            </div>
          </Link>
        </div>

        {/* Center Search Bar Mockup */}
        <div className="hidden md:flex items-center max-w-md w-full mx-6">
          <div className="relative w-full">
            <Search size={15} className="absolute left-3.5 top-2.5 text-slate-400" />
            <input
              type="text"
              readOnly
              placeholder={
                isAdmin
                  ? "Search user accounts, official emails, blocked statuses..."
                  : isTrainer
                  ? "Search training materials, generated MCQs, competencies..."
                  : "Search FRAC competencies, accredited iGOT courses, questions..."
              }
              className="w-full rounded-full border border-slate-200 bg-slate-50/80 py-1.5 pl-10 pr-4 text-12 text-slate-700 placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#0F54B9]/20"
            />
          </div>
        </div>

        {/* Right Actions & Officer Profile Chip */}
        <div className="flex items-center gap-3">
          <Link
            to="/portal"
            className="hidden sm:inline-flex items-center gap-1.5 rounded-full border border-amber-300 bg-[#FFF7ED] px-3.5 py-1.5 text-12 font-bold text-[#D96B0B] hover:bg-amber-100 transition-colors shadow-2xs"
          >
            <span>🏛️ Public Portal</span>
          </Link>

          {user && (
            <div className="flex items-center gap-2.5 border-l border-slate-200 pl-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-[#0B3060] to-[#154399] text-white font-bold text-12 shadow-xs">
                {user.profile.full_name.split(' ').map((n) => n[0]).join('')}
              </div>
              <div className="hidden text-left leading-tight sm:block">
                <p className="text-13 font-bold text-[#0B3060]">{user.profile.full_name}</p>
                <span className="inline-block text-10 font-semibold text-slate-500 truncate max-w-[150px]">
                  {isAdmin
                    ? 'System Administrator'
                    : isTrainer
                    ? 'Academy Trainer'
                    : (user.profile.job_role?.title ?? 'Statistical Officer')}
                </span>
              </div>
            </div>
          )}

          <button
            type="button"
            onClick={signOut}
            className="inline-flex h-9 w-9 items-center justify-center rounded-lg text-slate-500 hover:bg-red-50 hover:text-red-600 transition-colors"
            title="Sign out"
            aria-label="Sign out"
          >
            <LogOut size={18} strokeWidth={1.5} />
          </button>
        </div>
      </header>

      {/* Fixed Sidebar */}
      <aside className="fixed left-0 top-[66px] z-20 hidden h-[calc(100%-66px)] w-64 overflow-y-auto border-r border-slate-200 bg-white p-4 lg:block shadow-xs">
        <NavList />
      </aside>

      {/* Mobile Drawer */}
      {drawerOpen && (
        <>
          <div
            className="fixed inset-0 top-[66px] z-20 bg-slate-900/40 backdrop-blur-xs lg:hidden"
            onClick={() => setDrawerOpen(false)}
            aria-hidden
          />
          <aside className="fixed left-0 top-[66px] z-30 h-[calc(100%-66px)] w-64 overflow-y-auto border-r border-slate-200 bg-white p-4 lg:hidden shadow-xl">
            <NavList onNavigate={() => setDrawerOpen(false)} />
          </aside>
        </>
      )}

      {/* Main Content View */}
      <main className="pt-[66px] lg:pl-64">
        <div
          key={location.pathname}
          className="mx-auto max-w-6xl animate-fade-in px-4 py-6 sm:px-6 lg:px-8"
        >
          {children}
        </div>
      </main>
    </div>
  )
}
