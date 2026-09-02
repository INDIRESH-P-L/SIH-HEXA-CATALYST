/**
 * Onboarding wizard — shown once to newly registered officers.
 *
 * Three steps, matching the approved implementation plan:
 *   1. Employee Profile     → PATCH /profiles/me
 *   2. Competency Self-Assessment → POST /competencies/me/declare (batch)
 *   3. Generating Recommendations → POST /recommendations/generate → /recommendations
 *
 * Design language: identical to the authenticated Karmayogi Bharat shell
 * (tricolor strip, #0B3060 navy, #F58220 saffron, white cards).
 */
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  BookOpen,
  Brain,
  Briefcase,
  CheckCircle2,
  ChevronRight,
  GraduationCap,
  LayoutDashboard,
  MapPin,
  Sparkles,
  User2,
} from 'lucide-react'

import { ErrorNote, Spinner } from '../components/common'
import { useAuth } from '../lib/auth'
import { markOnboarded } from '../lib/onboarding'
import {
  useCompetencies,
  useDeclareBatch,
  useGenerateRecommendations,
  useUpdateProfile,
} from '../hooks'

// ── Constants ─────────────────────────────────────────────────────────────────

const TOTAL_STEPS = 3

const FRAC_LABELS: Record<number, string> = {
  0: 'No Experience',
  1: 'Awareness',
  2: 'Application',
  3: 'Leveraging for Decisions',
  4: 'Subject Matter Expert',
}

const CLUSTER_META: Record<
  string,
  { label: string; icon: typeof Brain; color: string; description: string }
> = {
  STATISTICAL: {
    label: 'Statistical Methodology',
    icon: LayoutDashboard,
    color: '#2563EB',
    description: 'Data collection, sampling, indices, survey design, statistical analysis',
  },
  TECHNICAL: {
    label: 'Technical & IT Skills',
    icon: Brain,
    color: '#7C3AED',
    description: 'SQL, R, Python, data visualisation, geospatial tools, IT systems',
  },
  DIGITAL_GOVERNANCE: {
    label: 'Digital Governance',
    icon: Briefcase,
    color: '#0F766E',
    description: 'e-governance, data policy, open data, digital public infrastructure',
  },
  BEHAVIOURAL: {
    label: 'Leadership & Behavioural',
    icon: User2,
    color: '#B45309',
    description: 'Communication, stakeholder engagement, ethics, decision-making under uncertainty',
  },
}

// ── Step indicator ────────────────────────────────────────────────────────────

function StepIndicator({ current }: { current: number }) {
  const steps = [
    { label: 'Profile', icon: User2 },
    { label: 'Skills', icon: Brain },
    { label: 'Recommendations', icon: Sparkles },
  ]

  return (
    <div className="flex items-center justify-center gap-0 mb-8">
      {steps.map((step, idx) => {
        const num = idx + 1
        const done = num < current
        const active = num === current
        const Icon = step.icon

        return (
          <div key={num} className="flex items-center">
            <div className="flex flex-col items-center gap-1.5">
              <div
                className={`flex h-10 w-10 items-center justify-center rounded-full font-bold text-14 transition-all shadow-sm ${
                  done
                    ? 'bg-emerald-500 text-white'
                    : active
                    ? 'bg-[#0B3060] text-white ring-4 ring-[#0B3060]/20'
                    : 'bg-slate-200 text-slate-500'
                }`}
              >
                {done ? <CheckCircle2 size={18} /> : <Icon size={16} />}
              </div>
              <span
                className={`text-11 font-semibold ${
                  active ? 'text-[#0B3060]' : done ? 'text-emerald-600' : 'text-slate-400'
                }`}
              >
                {step.label}
              </span>
            </div>
            {idx < steps.length - 1 && (
              <div
                className={`mx-3 mb-5 h-0.5 w-14 sm:w-20 transition-all ${
                  num < current ? 'bg-emerald-400' : 'bg-slate-200'
                }`}
              />
            )}
          </div>
        )
      })}
    </div>
  )
}

// ── Step 1: Profile ───────────────────────────────────────────────────────────

function StepProfile({
  onNext,
}: {
  onNext: () => void
}) {
  const { user } = useAuth()
  const updateProfile = useUpdateProfile()
  const profile = user?.profile

  const [fullName, setFullName] = useState(profile?.full_name ?? '')
  const [designation, setDesignation] = useState(profile?.designation ?? '')
  const [department] = useState(
    profile?.department ?? 'Ministry of Statistics and Programme Implementation',
  )
  const [station, setStation] = useState(profile?.station ?? '')
  const [yearsExp, setYearsExp] = useState(String(profile?.years_experience ?? 0))
  const [education, setEducation] = useState(profile?.education ?? '')
  const [error, setError] = useState<string | null>(null)

  async function handleNext() {
    setError(null)
    try {
      await updateProfile.mutateAsync({
        full_name: fullName.trim() || undefined,
        designation: designation.trim() || undefined,
        station: station.trim() || undefined,
        years_experience: parseInt(yearsExp) || 0,
        education: education.trim() || undefined,
      })
      onNext()
    } catch {
      setError('Could not save your profile. Please try again.')
    }
  }

  const inputClass =
    'w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-14 text-slate-900 focus:border-[#F58220] focus:outline-none focus:ring-2 focus:ring-[#F58220]/20 transition-colors'
  const labelClass = 'block text-12 font-semibold text-slate-700 mb-1.5'

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="ob-fullname" className={labelClass}>
            Full Name <span className="text-red-500">*</span>
          </label>
          <input
            id="ob-fullname"
            className={inputClass}
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="Your full name"
          />
        </div>
        <div>
          <label htmlFor="ob-designation" className={labelClass}>
            Designation / Post
          </label>
          <input
            id="ob-designation"
            className={inputClass}
            value={designation}
            onChange={(e) => setDesignation(e.target.value)}
            placeholder="e.g. Statistical Officer"
          />
        </div>
      </div>

      <div>
        <label htmlFor="ob-department" className={labelClass}>
          Department / Ministry
        </label>
        <input
          id="ob-department"
          className={`${inputClass} bg-slate-50 text-slate-500 cursor-not-allowed`}
          value={department}
          readOnly
          title="Department is set by your registered role"
        />
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="ob-station" className={labelClass}>
            <MapPin size={12} className="inline mr-1 text-slate-400" />
            Station / Posting Location
          </label>
          <input
            id="ob-station"
            className={inputClass}
            value={station}
            onChange={(e) => setStation(e.target.value)}
            placeholder="e.g. New Delhi"
          />
        </div>
        <div>
          <label htmlFor="ob-exp" className={labelClass}>
            <Briefcase size={12} className="inline mr-1 text-slate-400" />
            Years of Experience
          </label>
          <input
            id="ob-exp"
            type="number"
            min={0}
            max={60}
            className={inputClass}
            value={yearsExp}
            onChange={(e) => setYearsExp(e.target.value)}
          />
        </div>
      </div>

      <div>
        <label htmlFor="ob-education" className={labelClass}>
          <GraduationCap size={12} className="inline mr-1 text-slate-400" />
          Highest Qualification
        </label>
        <input
          id="ob-education"
          className={inputClass}
          value={education}
          onChange={(e) => setEducation(e.target.value)}
          placeholder="e.g. M.Sc. Statistics, IIT Delhi"
        />
      </div>

      {/* Role info (read-only) */}
      {profile?.job_role && (
        <div className="rounded-xl border border-[#0B3060]/15 bg-[#EEF4FF] p-3.5 flex items-center gap-3">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#0B3060]/10">
            <Briefcase size={14} className="text-[#0B3060]" />
          </div>
          <div>
            <p className="text-12 font-bold text-[#0B3060]">{profile.job_role.title}</p>
            <p className="text-11 text-slate-500 font-mono">{profile.job_role.cadre} cadre</p>
          </div>
          <span className="ml-auto text-11 bg-[#0B3060]/10 text-[#0B3060] font-bold px-2 py-0.5 rounded">
            Your Role
          </span>
        </div>
      )}

      {error && <ErrorNote>{error}</ErrorNote>}

      <button
        type="button"
        onClick={handleNext}
        disabled={!fullName.trim() || updateProfile.isPending}
        className="w-full flex items-center justify-center gap-2 rounded-xl bg-[#0B3060] py-3 text-14 font-bold text-white shadow-md hover:bg-[#F58220] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {updateProfile.isPending ? (
          <Spinner size={18} label="" />
        ) : (
          <>
            Save Profile & Continue
            <ChevronRight size={16} />
          </>
        )}
      </button>
    </div>
  )
}

// ── Step 2: Competency Self-Assessment ────────────────────────────────────────

function StepAssessment({ onNext, onBack }: { onNext: () => void; onBack: () => void }) {
  const { data: competencies, isLoading } = useCompetencies()
  const declareBatch = useDeclareBatch()
  const [error, setError] = useState<string | null>(null)

  // Group by cluster

  const [clusterLevels, setClusterLevels] = useState<Record<string, number>>({
    STATISTICAL: 1,
    TECHNICAL: 1,
    DIGITAL_GOVERNANCE: 1,
    BEHAVIOURAL: 1,
  })

  async function handleNext() {
    setError(null)
    if (!competencies) return

    // Build batch: every competency in a cluster gets its cluster's level
    const declarations = competencies.map((c) => ({
      competency_id: c.id,
      level: clusterLevels[c.cluster] ?? 1,
      note: 'Initial self-declaration (onboarding)',
    }))

    try {
      await declareBatch.mutateAsync(declarations)
      onNext()
    } catch {
      setError('Could not save your declarations. Please try again.')
    }
  }

  if (isLoading) {
    return (
      <div className="flex justify-center py-10">
        <Spinner label="Loading competency framework…" />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <p className="text-13 text-slate-600 leading-relaxed bg-amber-50 border border-amber-200 rounded-xl px-4 py-3">
        <span className="font-bold text-amber-800">Self-declaration</span> — rate your current level in each domain. This is your starting point; formal assessments will refine it. All declarations are stored at low confidence (0.25) and will be updated as you complete quizzes.
      </p>

      {Object.entries(CLUSTER_META).map(([cluster, meta]) => {
        const Icon = meta.icon
        const level = clusterLevels[cluster] ?? 1
        return (
          <div
            key={cluster}
            className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm hover:border-[#0B3060]/30 transition-colors"
          >
            <div className="flex items-start gap-3 mb-4">
              <div
                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-white shadow-sm"
                style={{ backgroundColor: meta.color }}
              >
                <Icon size={18} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-13 font-bold text-slate-900">{meta.label}</p>
                <p className="text-11 text-slate-500 mt-0.5">{meta.description}</p>
              </div>
              <div className="shrink-0 text-right">
                <p className="text-20 font-black tabular" style={{ color: meta.color }}>
                  {level}
                </p>
                <p className="text-10 font-mono text-slate-400 whitespace-nowrap">
                  / 4 FRAC
                </p>
              </div>
            </div>

            {/* FRAC level slider */}
            <div className="space-y-2">
              <input
                type="range"
                min={0}
                max={4}
                step={1}
                value={level}
                onChange={(e) =>
                  setClusterLevels((prev) => ({
                    ...prev,
                    [cluster]: Number(e.target.value),
                  }))
                }
                className="w-full accent-current h-2 rounded-full cursor-pointer"
                style={{ accentColor: meta.color }}
                aria-label={`${meta.label} level`}
              />
              <div className="flex justify-between px-0.5">
                {[0, 1, 2, 3, 4].map((l) => (
                  <span
                    key={l}
                    className={`text-10 font-mono ${
                      l === level ? 'font-black' : 'text-slate-400'
                    }`}
                    style={l === level ? { color: meta.color } : {}}
                  >
                    {l}
                  </span>
                ))}
              </div>
              <p
                className="text-12 font-semibold text-center py-1.5 rounded-lg"
                style={{ color: meta.color, backgroundColor: meta.color + '15' }}
              >
                {FRAC_LABELS[level]}
              </p>
            </div>
          </div>
        )
      })}

      {error && <ErrorNote>{error}</ErrorNote>}

      <div className="flex gap-3 pt-2">
        <button
          type="button"
          onClick={onBack}
          className="flex-1 rounded-xl border border-slate-300 py-3 text-14 font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
        >
          ← Back
        </button>
        <button
          type="button"
          onClick={handleNext}
          disabled={declareBatch.isPending}
          className="flex-[2] flex items-center justify-center gap-2 rounded-xl bg-[#0B3060] py-3 text-14 font-bold text-white shadow-md hover:bg-[#F58220] transition-colors disabled:opacity-50"
        >
          {declareBatch.isPending ? (
            <Spinner size={18} label="Saving…" />
          ) : (
            <>
              Save & Generate Recommendations
              <ChevronRight size={16} />
            </>
          )}
        </button>
      </div>
    </div>
  )
}

// ── Step 3: Generating Recommendations ───────────────────────────────────────

function StepRecommendations({ userId }: { userId: string; onBack: () => void }) {
  const navigate = useNavigate()
  const generate = useGenerateRecommendations()
  const [error, setError] = useState<string | null>(null)
  const [done, setDone] = useState(false)

  useEffect(() => {
    // Auto-trigger on mount
    async function run() {
      try {
        await generate.mutateAsync()
        markOnboarded(userId)
        setDone(true)
        // Brief pause so the success state is visible
        setTimeout(() => navigate('/recommendations', { replace: true }), 1800)
      } catch {
        setError(
          'Could not generate recommendations right now. You can try again from the Recommendations page.',
        )
        // Still mark onboarded so the wizard doesn't loop
        markOnboarded(userId)
      }
    }
    void run()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  if (error) {
    return (
      <div className="space-y-5 text-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-amber-100 mx-auto">
          <Sparkles size={28} className="text-amber-600" />
        </div>
        <h3 className="text-18 font-bold text-slate-900">Almost there!</h3>
        <p className="text-14 text-slate-600 max-w-sm mx-auto">
          Your profile and skill levels were saved. The AI recommender will run when you visit the Recommendations page.
        </p>
        <ErrorNote>{error}</ErrorNote>
        <button
          type="button"
          onClick={() => {
            navigate('/recommendations', { replace: true })
          }}
          className="w-full rounded-xl bg-[#0B3060] py-3 text-14 font-bold text-white hover:bg-[#F58220] transition-colors"
        >
          Go to Recommendations →
        </button>
      </div>
    )
  }

  if (done) {
    return (
      <div className="flex flex-col items-center gap-4 py-6 text-center">
        <div className="flex h-20 w-20 items-center justify-center rounded-full bg-emerald-100 shadow-sm animate-bounce-once">
          <CheckCircle2 size={40} className="text-emerald-500" />
        </div>
        <h3 className="text-20 font-black text-slate-900">You're all set!</h3>
        <p className="text-14 text-slate-500">Redirecting to your personalised learning path…</p>
        <div className="mt-2">
          <Spinner label="Loading recommendations" />
        </div>
      </div>
    )
  }

  // Loading state
  return (
    <div className="space-y-6 py-4">
      <div className="flex flex-col items-center gap-4 text-center">
        <div className="relative flex h-20 w-20 items-center justify-center">
          <div className="absolute inset-0 rounded-full border-4 border-[#0B3060]/10 animate-ping" />
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-[#0B3060] to-[#154399] shadow-lg">
            <Sparkles size={28} className="text-[#F58220]" />
          </div>
        </div>
        <div>
          <h3 className="text-18 font-bold text-slate-900">Generating your learning path…</h3>
          <p className="text-13 text-slate-500 mt-1">
            The AI is matching courses to your skill profile
          </p>
        </div>
      </div>

      {/* Animated pipeline steps */}
      {[
        { icon: Brain, label: 'Analysing your competency profile', delay: '0s' },
        { icon: BookOpen, label: 'Scanning iGOT & NSSTA course catalogue', delay: '0.4s' },
        { icon: Sparkles, label: 'Ranking by skill-gap priority (Groq AI)', delay: '0.8s' },
        { icon: CheckCircle2, label: 'Building your personalised pathway', delay: '1.2s' },
      ].map(({ icon: Icon, label, delay }) => (
        <div
          key={label}
          className="flex items-center gap-3 rounded-xl border border-slate-100 bg-slate-50 px-4 py-3 opacity-0 animate-fade-in"
          style={{ animationDelay: delay, animationFillMode: 'forwards' }}
        >
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#0B3060]/10">
            <Icon size={15} className="text-[#0B3060]" />
          </div>
          <p className="text-13 font-medium text-slate-700">{label}</p>
          <Spinner size={14} label="" />
        </div>
      ))}
    </div>
  )
}

// ── Main wizard ───────────────────────────────────────────────────────────────

export default function Onboarding() {
  const { user } = useAuth()
  const [step, setStep] = useState(1)

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#F0F4FF] via-[#F8FAFC] to-white flex flex-col">
      {/* Tricolor strip */}
      <div className="tricolor-strip" />

      {/* Header */}
      <header className="bg-white border-b border-slate-200 shadow-sm">
        <div className="mx-auto flex max-w-3xl items-center gap-3 px-4 py-3 sm:px-6">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-[#0B3060] to-[#154399] shadow">
            <svg viewBox="0 0 24 24" className="h-7 w-7 fill-current text-white" aria-hidden="true">
              <path d="M12 2L14.5 8.5L21.5 9.5L16.5 14.5L18 21.5L12 18L6 21.5L7.5 14.5L2.5 9.5L9.5 8.5L12 2Z" fill="#F58220" />
              <circle cx="12" cy="13" r="3.5" fill="#FFFFFF" />
              <circle cx="12" cy="13" r="1.5" fill="#0B3060" />
            </svg>
          </div>
          <div>
            <h1 className="text-15 font-extrabold text-[#0B3060] leading-none">
              Karmayogi Bharat · MoSPI
            </h1>
            <p className="text-11 text-slate-500 font-medium mt-0.5">
              Officer Onboarding · Step {step} of {TOTAL_STEPS}
            </p>
          </div>
          <div className="ml-auto hidden sm:flex items-center gap-2 bg-[#EEF4FF] rounded-lg px-3 py-1.5">
            <div className="h-6 w-6 rounded-full bg-[#0B3060] flex items-center justify-center text-white font-bold text-11">
              {user?.profile.full_name?.charAt(0) ?? '?'}
            </div>
            <span className="text-12 font-semibold text-[#0B3060] max-w-[140px] truncate">
              {user?.profile.full_name}
            </span>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 mx-auto w-full max-w-2xl px-4 py-8 sm:px-6">
        <StepIndicator current={step} />

        {/* Step title cards */}
        <div className="mb-6 text-center">
          {step === 1 && (
            <>
              <h2 className="text-24 font-extrabold text-[#0B3060]">Complete Your Profile</h2>
              <p className="mt-1 text-14 text-slate-500">
                Help us personalise your learning journey within the OSS ecosystem
              </p>
            </>
          )}
          {step === 2 && (
            <>
              <h2 className="text-24 font-extrabold text-[#0B3060]">Competency Self-Assessment</h2>
              <p className="mt-1 text-14 text-slate-500">
                Rate your current skill level across the four FRAC competency clusters
              </p>
            </>
          )}
          {step === 3 && (
            <>
              <h2 className="text-24 font-extrabold text-[#0B3060]">Personalising Your Path</h2>
              <p className="mt-1 text-14 text-slate-500">
                AI is curating courses from iGOT & NSSTA based on your skill gaps
              </p>
            </>
          )}
        </div>

        {/* White card content */}
        <div className="rounded-2xl border border-slate-200 bg-white p-5 sm:p-6 shadow-sm">
          {step === 1 && <StepProfile onNext={() => setStep(2)} />}
          {step === 2 && (
            <StepAssessment onNext={() => setStep(3)} onBack={() => setStep(1)} />
          )}
          {step === 3 && user && (
            <StepRecommendations userId={user.id} onBack={() => setStep(2)} />
          )}
        </div>

        {/* Footer note */}
        <p className="mt-5 text-center text-11 text-slate-400">
          🔒 Your data is secured by MoSPI's FRAC competency ledger · SIH 2026
        </p>
      </main>
    </div>
  )
}
