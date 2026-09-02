import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ArrowLeft, Lock, Mail, Sparkles } from 'lucide-react'

import { ErrorNote } from '../components/common'
import { errorMessage } from '../lib/api'
import { useAuth } from '../lib/auth'

/** Seeded local accounts, listed with rich visual cards for seamless demo access. */
const DEMO_ACCOUNTS = [
  {
    name: 'Priya Sharma',
    email: 'priya.sharma@mospi.gov.in',
    role: 'Statistical Officer (SSS Cadre) — Target Learner',
    badge: 'Learner Profile',
    badgeColor: 'bg-emerald-100 text-emerald-800 border-emerald-200',
    avatarBg: 'bg-emerald-600',
  },
  {
    name: 'Anand Desai',
    email: 'anand.desai@nssta.gov.in',
    role: 'Assistant Director (Training) — NSSTA Academy',
    badge: 'Trainer & Creator',
    badgeColor: 'bg-indigo-100 text-indigo-800 border-indigo-200',
    avatarBg: 'bg-indigo-600',
  },
  {
    name: 'System Administrator',
    email: 'admin@mospi.gov.in',
    role: 'Deputy Director (Systems & DIID) — Admin',
    badge: 'System Admin',
    badgeColor: 'bg-amber-100 text-amber-800 border-amber-200',
    avatarBg: 'bg-amber-600',
  },
]
const DEMO_PASSWORD = 'Demo@2026'

export default function Login() {
  const { signIn } = useAuth()
  const navigate = useNavigate()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setBusy(true)
    try {
      await signIn(email.trim(), password)
      navigate('/', { replace: true })
    } catch (caught) {
      setError(errorMessage(caught, 'Sign-in failed.'))
    } finally {
      setBusy(false)
    }
  }

  async function useAccount(targetEmail: string) {
    setEmail(targetEmail)
    setPassword(DEMO_PASSWORD)
    setError(null)
    setBusy(true)
    try {
      await signIn(targetEmail, DEMO_PASSWORD)
      navigate('/', { replace: true })
    } catch (caught) {
      setError(errorMessage(caught, 'Sign-in failed.'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#FFF7ED] via-[#FFF3E3] to-[#F8FAFC] flex flex-col justify-between">
      {/* Top Tricolor Strip */}
      <div className="tricolor-strip" />

      {/* Top Navigation Back link */}
      <div className="mx-auto w-full max-w-5xl px-4 py-4 sm:px-6">
        <Link
          to="/portal"
          className="inline-flex items-center gap-2 text-13 font-bold text-[#0B3060] hover:text-[#F58220] transition-colors"
        >
          <ArrowLeft size={16} />
          <span>Back to Karmayogi Public Portal</span>
        </Link>
      </div>

      {/* Center Container */}
      <div className="mx-auto w-full max-w-xl px-4 py-6">
        {/* Header Branding */}
        <div className="text-center mb-6 space-y-2">
          <div className="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-[#0B3060] to-[#154399] text-white shadow-lg mx-auto">
            <svg viewBox="0 0 24 24" className="h-9 w-9 fill-current" aria-hidden="true">
              <path d="M12 2L14.5 8.5L21.5 9.5L16.5 14.5L18 21.5L12 18L6 21.5L7.5 14.5L2.5 9.5L9.5 8.5L12 2Z" fill="#F58220" />
              <circle cx="12" cy="13" r="3.5" fill="#FFFFFF" />
              <circle cx="12" cy="13" r="1.5" fill="#0B3060" />
            </svg>
          </div>
          <h1 className="text-24 sm:text-28 font-extrabold text-[#0B3060] tracking-tight">
            Karmayogi Bharat | MoSPI
          </h1>
          <p className="text-13 font-semibold text-[#D96B0B]">
            AI-Enabled Skill Intelligence Platform · Smart India Hackathon 2026
          </p>
        </div>

        {/* 1-Click Demo Personas Quick Launch */}
        <div className="overflow-hidden rounded-2xl border-2 border-amber-200 bg-white shadow-xl mb-6">
          <div className="bg-gradient-to-r from-[#0B3060] to-[#154399] px-5 py-3 text-white flex items-center justify-between">
            <span className="text-13 font-bold flex items-center gap-1.5">
              <Sparkles size={16} className="text-amber-300" />
              1-Click Demo Access
            </span>
            <span className="text-11 bg-white/10 px-2 py-0.5 rounded font-mono">
              Ready to Launch
            </span>
          </div>

          <div className="p-4 space-y-2.5 bg-gradient-to-b from-[#FFFDF9] to-white">
            {DEMO_ACCOUNTS.map((account) => (
              <button
                key={account.email}
                type="button"
                disabled={busy}
                onClick={() => useAccount(account.email)}
                className="group flex w-full items-center justify-between rounded-xl border border-slate-200 bg-white p-3 text-left transition-all hover:border-[#F58220] hover:bg-[#FFF9F2] hover:shadow-md"
              >
                <div className="flex items-center gap-3">
                  <div className={`flex h-9 w-9 items-center justify-center rounded-lg text-white font-bold text-12 shadow-sm ${account.avatarBg}`}>
                    {account.name.split(' ').map(n => n[0]).join('')}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-13 font-bold text-slate-900 group-hover:text-[#F58220]">
                        {account.name}
                      </span>
                      <span className={`rounded border px-1.5 py-0.2 text-10 font-bold ${account.badgeColor}`}>
                        {account.badge}
                      </span>
                    </div>
                    <span className="block font-mono text-11 text-slate-500">{account.email}</span>
                  </div>
                </div>

                <div className="shrink-0 ml-2">
                  <span className="inline-flex items-center rounded-lg bg-[#0B3060] px-3 py-1.5 text-11 font-bold text-white group-hover:bg-[#F58220] transition-colors shadow-sm">
                    Enter →
                  </span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Manual Credentials Box */}
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-md space-y-4">
          <div className="border-b border-slate-100 pb-2">
            <h2 className="text-14 font-bold uppercase tracking-wider text-slate-700">
              Government Official Sign In
            </h2>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            <div>
              <label htmlFor="email" className="block text-12 font-semibold text-slate-700 mb-1">
                Official Email
              </label>
              <div className="relative">
                <Mail size={16} className="absolute left-3 top-3 text-slate-400" />
                <input
                  id="email"
                  type="email"
                  autoComplete="username"
                  required
                  placeholder="officer@mospi.gov.in"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  className="w-full rounded-lg border border-slate-300 py-2.5 pl-10 pr-3 text-14 text-slate-900 focus:border-[#F58220] focus:outline-none focus:ring-2 focus:ring-[#F58220]/20"
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-12 font-semibold text-slate-700 mb-1">
                Password
              </label>
              <div className="relative">
                <Lock size={16} className="absolute left-3 top-3 text-slate-400" />
                <input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  placeholder="••••••••"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  className="w-full rounded-lg border border-slate-300 py-2.5 pl-10 pr-3 text-14 text-slate-900 focus:border-[#F58220] focus:outline-none focus:ring-2 focus:ring-[#F58220]/20"
                />
              </div>
            </div>

            {error && <ErrorNote>{error}</ErrorNote>}

            <button
              type="submit"
              disabled={busy}
              className="w-full rounded-lg bg-[#0B3060] py-2.5 text-14 font-bold text-white shadow-md hover:bg-[#F58220] transition-colors disabled:opacity-50"
            >
              {busy ? 'Authenticating...' : 'Sign In with Password'}
            </button>
          </form>
        </div>

        <p className="mt-4 text-center text-11 text-slate-500">
          🔒 Authenticated against the local FRAC 4-point competency ledger. No external network required.
        </p>
      </div>

      {/* Bottom Footer Note */}
      <div className="py-4 text-center text-11 text-slate-400 border-t border-slate-200">
        © 2026 Ministry of Statistics and Programme Implementation (MoSPI)
      </div>
    </div>
  )
}
