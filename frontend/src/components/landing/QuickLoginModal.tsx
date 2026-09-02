import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { Lock, Mail, ShieldAlert, Sparkles, X } from 'lucide-react'

import { errorMessage } from '../../lib/api'
import { useAuth } from '../../lib/auth'

interface QuickLoginModalProps {
  isOpen: boolean
  onClose: () => void
}

const DEMO_PERSONAS = [
  {
    name: 'Priya Sharma',
    role: 'Statistical Officer (SSS Cadre)',
    roleType: 'Learner · Field Officer',
    email: 'priya.sharma@mospi.gov.in',
    avatar: 'PS',
    color: 'bg-emerald-600',
    description: 'Target learner profile with critical SQL & Sampling skill gaps and automated recommendations.',
  },
  {
    name: 'Anand Desai',
    role: 'Assistant Director (Training)',
    roleType: 'Trainer · NSSTA Academy',
    email: 'anand.desai@nssta.gov.in',
    avatar: 'AD',
    color: 'bg-indigo-600',
    description: 'Training officer with access to AI MCQ Generator, document chunking & question verification gate.',
  },
  {
    name: 'System Administrator',
    role: 'Deputy Director (Systems & DIID)',
    roleType: 'Admin · MoSPI Headquarters',
    email: 'admin@mospi.gov.in',
    avatar: 'SA',
    color: 'bg-amber-600',
    description: 'Full workforce analytics, k-anonymity matrices, framework seals and training effectiveness metrics.',
  },
]

const DEMO_PASSWORD = 'Demo@2026'

export function QuickLoginModal({ isOpen, onClose }: QuickLoginModalProps) {
  const { signIn } = useAuth()
  const navigate = useNavigate()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [activeTab, setActiveTab] = useState<'quick' | 'custom'>('quick')

  if (!isOpen) return null

  async function handlePersonaLogin(userEmail: string) {
    setError(null)
    setBusy(true)
    try {
      await signIn(userEmail, DEMO_PASSWORD)
      onClose()
      navigate('/', { replace: true })
    } catch (caught) {
      setError(errorMessage(caught, 'Sign-in failed. Please ensure backend is running.'))
    } finally {
      setBusy(false)
    }
  }

  async function handleCustomSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setBusy(true)
    try {
      await signIn(email.trim(), password)
      onClose()
      navigate('/', { replace: true })
    } catch (caught) {
      setError(errorMessage(caught, 'Sign-in failed.'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-xl overflow-hidden rounded-xl border border-slate-200 bg-white shadow-2xl">
        {/* Tricolor bar */}
        <div className="tricolor-strip" />

        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-slate-100 bg-[#FFF7ED] px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#0B3060] text-white shadow-sm font-bold">
              🇮🇳
            </div>
            <div>
              <h2 className="text-16 font-bold text-[#0B3060]">Access Skill Intelligence Platform</h2>
              <p className="text-12 text-slate-600">Ministry of Statistics and Programme Implementation</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
          >
            <X size={18} />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6">
          {/* Tabs */}
          <div className="mb-5 flex rounded-lg border border-slate-200 bg-slate-50 p-1">
            <button
              type="button"
              onClick={() => setActiveTab('quick')}
              className={`flex-1 flex items-center justify-center gap-2 rounded-md py-2 text-13 font-semibold transition-all ${
                activeTab === 'quick'
                  ? 'bg-white text-[#0B3060] shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Sparkles size={15} className="text-[#F58220]" />
              1-Click Demo Personas
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('custom')}
              className={`flex-1 flex items-center justify-center gap-2 rounded-md py-2 text-13 font-semibold transition-all ${
                activeTab === 'custom'
                  ? 'bg-white text-[#0B3060] shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Lock size={15} />
              Manual Sign In
            </button>
          </div>

          {error && (
            <div className="mb-4 flex items-center gap-2.5 rounded-lg border border-red-200 bg-red-50 p-3 text-13 text-red-700">
              <ShieldAlert size={16} className="shrink-0 text-red-600" />
              <span>{error}</span>
            </div>
          )}

          {activeTab === 'quick' ? (
            <div className="space-y-3">
              <p className="text-12 text-slate-600 font-medium">
                Select an official role to immediately enter the prototype dashboard:
              </p>
              {DEMO_PERSONAS.map((p) => (
                <button
                  key={p.email}
                  type="button"
                  disabled={busy}
                  onClick={() => handlePersonaLogin(p.email)}
                  className="group flex w-full items-center justify-between rounded-lg border border-slate-200 bg-white p-3.5 text-left transition-all hover:border-[#F58220] hover:bg-[#FFF9F2] hover:shadow-sm"
                >
                  <div className="flex items-center gap-3.5">
                    <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-13 font-bold text-white ${p.color}`}>
                      {p.avatar}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-14 font-bold text-[#0B3060] group-hover:text-[#F58220]">
                          {p.name}
                        </span>
                        <span className="rounded bg-slate-100 px-1.5 py-0.5 text-11 font-medium text-slate-700">
                          {p.roleType}
                        </span>
                      </div>
                      <p className="text-12 text-slate-500">{p.role}</p>
                      <p className="mt-0.5 text-11 text-slate-600 leading-snug">{p.description}</p>
                    </div>
                  </div>
                  <div className="ml-3 shrink-0">
                    <span className="inline-flex items-center gap-1 rounded-md bg-[#0B3060] px-3 py-1.5 text-12 font-semibold text-white group-hover:bg-[#F58220] transition-colors">
                      {busy ? 'Loading...' : 'Launch →'}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          ) : (
            <form onSubmit={handleCustomSubmit} className="space-y-4">
              <div>
                <label htmlFor="modal-email" className="block text-12 font-semibold text-slate-700 mb-1">
                  Official Email Address
                </label>
                <div className="relative">
                  <Mail size={16} className="absolute left-3 top-3 text-slate-400" />
                  <input
                    id="modal-email"
                    type="email"
                    required
                    placeholder="officer@mospi.gov.in"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 py-2.5 pl-10 pr-3 text-14 text-slate-900 focus:border-[#F58220] focus:outline-none focus:ring-2 focus:ring-[#F58220]/20"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="modal-password" className="block text-12 font-semibold text-slate-700 mb-1">
                  Password
                </label>
                <div className="relative">
                  <Lock size={16} className="absolute left-3 top-3 text-slate-400" />
                  <input
                    id="modal-password"
                    type="password"
                    required
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 py-2.5 pl-10 pr-3 text-14 text-slate-900 focus:border-[#F58220] focus:outline-none focus:ring-2 focus:ring-[#F58220]/20"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={busy}
                className="w-full rounded-lg bg-[#0B3060] py-2.5 text-14 font-semibold text-white shadow-sm transition-all hover:bg-[#F58220] disabled:opacity-50"
              >
                {busy ? 'Authenticating...' : 'Sign In'}
              </button>
            </form>
          )}

          <div className="mt-5 rounded-lg bg-slate-50 p-3 text-center text-11 text-slate-500 border border-slate-100">
            🔒 Protected by Official Government RBAC (Role-Based Access Control) & FRAC 4-Point Competency Ledger.
          </div>
        </div>
      </div>
    </div>
  )
}
