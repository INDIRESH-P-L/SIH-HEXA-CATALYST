import { useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ArrowLeft, Briefcase, Lock, Mail, Sparkles, User2, UserPlus } from 'lucide-react'

import { ErrorNote, Spinner } from '../components/common'
import { api, API, errorMessage } from '../lib/api'
import { useAuth } from '../lib/auth'
import type { JobRole } from '../lib/types'

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

// ── Sign-up form ──────────────────────────────────────────────────────────────

function SignUpForm() {
  const { signIn } = useAuth()
  const navigate = useNavigate()

  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [jobRoleCode, setJobRoleCode] = useState('STAT_OFFICER')
  const [jobRoles, setJobRoles] = useState<JobRole[]>([])
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  // Fetch job roles (public endpoint needs auth — use a guest-friendly approach:
  // we call /job-roles with the register flow inline; job roles are fetched
  // without auth using the register endpoint's public context)
  useEffect(() => {
    // Fetch from a known seeded demo token or just hard-code the list from seed data
    const hardcodedRoles: JobRole[] = [
      { id: '', code: 'STAT_OFFICER', title: 'Statistical Officer', cadre: 'ISS', description: null },
      { id: '', code: 'SR_STAT_OFFICER', title: 'Senior Statistical Officer', cadre: 'ISS', description: null },
      { id: '', code: 'DEP_DIRECTOR', title: 'Deputy Director', cadre: 'ISS', description: null },
      { id: '', code: 'FIELD_SUPERVISOR', title: 'Field Supervisor', cadre: 'SSS', description: null },
      { id: '', code: 'DATA_SCIENTIST', title: 'Data Scientist (Statistical Systems)', cadre: 'OTHER', description: null },
    ]
    setJobRoles(hardcodedRoles)
  }, [])

  async function handleRegister(event: FormEvent) {
    event.preventDefault()
    setError(null)

    if (password !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }

    setBusy(true)
    try {
      // Call the register endpoint directly — signIn will store the token
      await api.post(API.v1('/auth/register'), {
        email: email.trim(),
        password,
        full_name: fullName.trim(),
        job_role_code: jobRoleCode,
      })
      // Now sign in to populate the auth context with the new token
      await signIn(email.trim(), password)
      navigate('/onboarding', { replace: true })
    } catch (caught: unknown) {
      // Give actionable messages for the two most common failure modes
      const status = (caught as { response?: { status?: number } })?.response?.status
      if (status === 409) {
        setError('That email is already registered. Please sign in instead.')
      } else if (status === 422) {
        // Parse Pydantic validation errors
        const detail = (caught as any)?.response?.data?.detail
        let msg = 'the password must be at least 8 characters.' // default
        if (Array.isArray(detail) && detail.length > 0) {
          const loc = detail[0].loc.join('.')
          msg = `${loc}: ${detail[0].msg}`
        }
        setError(`Validation failed — ${msg}`)
      } else {
        setError(errorMessage(caught, 'Registration failed. Please try again.'))
      }
    } finally {
      setBusy(false)
    }
  }

  const inputClass =
    'w-full rounded-lg border border-slate-300 py-2.5 pl-10 pr-3 text-14 text-slate-900 focus:border-[#F58220] focus:outline-none focus:ring-2 focus:ring-[#F58220]/20'
  const labelClass = 'block text-12 font-semibold text-slate-700 mb-1'

  return (
    <form onSubmit={handleRegister} className="space-y-4" noValidate>
      {/* Full Name */}
      <div>
        <label htmlFor="reg-name" className={labelClass}>
          Full Name <span className="text-red-500">*</span>
        </label>
        <div className="relative">
          <User2 size={16} className="absolute left-3 top-3 text-slate-400" />
          <input
            id="reg-name"
            type="text"
            autoComplete="name"
            required
            placeholder="Your full name"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            className={inputClass}
          />
        </div>
      </div>

      {/* Email */}
      <div>
        <label htmlFor="reg-email" className={labelClass}>
          Official Email <span className="text-red-500">*</span>
        </label>
        <div className="relative">
          <Mail size={16} className="absolute left-3 top-3 text-slate-400" />
          <input
            id="reg-email"
            type="email"
            autoComplete="email"
            required
            placeholder="officer@mospi.gov.in"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={inputClass}
          />
        </div>
      </div>

      {/* Job Role */}
      <div>
        <label htmlFor="reg-role" className={labelClass}>
          <Briefcase size={12} className="inline mr-1 text-slate-400" />
          Job Role / Designation
        </label>
        <select
          id="reg-role"
          value={jobRoleCode}
          onChange={(e) => setJobRoleCode(e.target.value)}
          className="w-full rounded-lg border border-slate-300 py-2.5 px-3 text-14 text-slate-900 focus:border-[#F58220] focus:outline-none focus:ring-2 focus:ring-[#F58220]/20 bg-white"
        >
          {jobRoles.map((r) => (
            <option key={r.code} value={r.code}>
              {r.title} ({r.cadre})
            </option>
          ))}
        </select>
      </div>

      {/* Password */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div>
          <label htmlFor="reg-password" className={labelClass}>
            Password <span className="text-red-500">*</span>
          </label>
          <div className="relative">
            <Lock size={16} className="absolute left-3 top-3 text-slate-400" />
            <input
              id="reg-password"
              type="password"
              autoComplete="new-password"
              required
              placeholder="Min. 8 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={inputClass}
            />
          </div>
        </div>
        <div>
          <label htmlFor="reg-confirm" className={labelClass}>
            Confirm Password <span className="text-red-500">*</span>
          </label>
          <div className="relative">
            <Lock size={16} className="absolute left-3 top-3 text-slate-400" />
            <input
              id="reg-confirm"
              type="password"
              autoComplete="new-password"
              required
              placeholder="Repeat password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className={inputClass}
            />
          </div>
        </div>
      </div>

      {error && <ErrorNote>{error}</ErrorNote>}

      <button
        type="submit"
        disabled={busy || !fullName.trim() || !email.trim() || !password}
        className="w-full flex items-center justify-center gap-2 rounded-lg bg-[#0B3060] py-2.5 text-14 font-bold text-white shadow-md hover:bg-[#F58220] transition-colors disabled:opacity-50"
      >
        {busy ? (
          <Spinner size={18} label="Creating account…" />
        ) : (
          <>
            <UserPlus size={16} />
            Create Account & Continue
          </>
        )}
      </button>

      <p className="text-center text-11 text-slate-400">
        By registering you agree to the MoSPI data usage policy
      </p>
    </form>
  )
}

// ── Main Login page ───────────────────────────────────────────────────────────

export default function Login() {
  const { signIn } = useAuth()
  const navigate = useNavigate()

  const [tab, setTab] = useState<'signin' | 'signup'>('signin')
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

        {/* Tab switcher — Sign In / Sign Up */}
        <div className="flex rounded-xl border border-slate-200 bg-white p-1 mb-5 shadow-sm">
          <button
            type="button"
            onClick={() => setTab('signin')}
            className={`flex-1 rounded-lg py-2 text-13 font-bold transition-all ${
              tab === 'signin'
                ? 'bg-[#0B3060] text-white shadow-sm'
                : 'text-slate-500 hover:text-[#0B3060]'
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => setTab('signup')}
            className={`flex-1 rounded-lg py-2 text-13 font-bold transition-all flex items-center justify-center gap-1.5 ${
              tab === 'signup'
                ? 'bg-[#F58220] text-white shadow-sm'
                : 'text-slate-500 hover:text-[#F58220]'
            }`}
          >
            <UserPlus size={14} />
            Sign Up
          </button>
        </div>

        {tab === 'signin' && (
          <>
            {/* 1-Click Demo Personas Quick Launch */}
            <div className="overflow-hidden rounded-2xl border-2 border-amber-200 bg-white shadow-xl mb-5">
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
          </>
        )}

        {tab === 'signup' && (
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-md">
            <div className="border-b border-slate-100 pb-3 mb-5">
              <h2 className="text-14 font-bold uppercase tracking-wider text-slate-700 flex items-center gap-2">
                <UserPlus size={15} className="text-[#F58220]" />
                New Officer Registration
              </h2>
              <p className="text-12 text-slate-500 mt-1">
                Create your account and start the onboarding assessment
              </p>
            </div>
            <SignUpForm />
          </div>
        )}

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
