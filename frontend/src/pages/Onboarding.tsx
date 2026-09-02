/**
 * Onboarding wizard — shown once to an officer with no competency evidence.
 *
 * Three steps, matching the approved implementation plan:
 *   1. Employee Profile     → PATCH /profiles/me
 *   2. Competency Self-Assessment → POST /competencies/me/declare (batch)
 *   3. Generating Recommendations → POST /recommendations/generate → /recommendations
 *
 * Step 2 is destructive if repeated: it appends a self-declaration for every
 * competency, and the ledger's latest row per (user, competency) wins. The
 * route guard in App.tsx is what keeps it to one pass; see lib/onboarding.ts.
 *
 * Both forms hold their state in this parent rather than in the step
 * components, because the steps unmount when you move between them and a Back
 * button that silently discards what you typed is worse than no Back button.
 *
 * Design language: identical to the authenticated Karmayogi Bharat shell
 * (tricolor strip, #0B3060 navy, #F58220 saffron, white cards).
 */
import { useState, type Dispatch, type SetStateAction } from 'react'
import {
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
import { fracLabel } from '../lib/format'
import {
  useCompetencies,
  useDeclareBatch,
  useUpdateProfile,
} from '../hooks'

// ── Constants ─────────────────────────────────────────────────────────────────

const TOTAL_STEPS = 3

/** Mirrors ProfileUpdate in backend/app/schemas/profile.py. */
const NAME_MIN = 2
const NAME_MAX = 120
const YEARS_MIN = 0
const YEARS_MAX = 60

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

interface ProfileForm {
  fullName: string
  designation: string
  station: string
  yearsExp: string
  education: string
}

type ClusterLevels = Record<string, number>

// ── Step indicator ────────────────────────────────────────────────────────────

function StepIndicator({ current }: { current: number }) {
  const steps = [
    { label: 'Profile', icon: User2 },
    { label: 'Skills', icon: Brain },
    { label: 'Assessment', icon: Sparkles },
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

/**
 * Validation mirrors the server's Pydantic constraints rather than approximating
 * them, so a rejection is explained next to the field that caused it instead of
 * arriving as an opaque 422.
 */
function validateProfile(form: ProfileForm): Partial<Record<keyof ProfileForm, string>> {
  const errors: Partial<Record<keyof ProfileForm, string>> = {}

  const name = form.fullName.trim()
  if (name.length < NAME_MIN) errors.fullName = `At least ${NAME_MIN} characters.`
  else if (name.length > NAME_MAX) errors.fullName = `At most ${NAME_MAX} characters.`

  const years = form.yearsExp.trim()
  if (years !== '') {
    const parsed = Number.parseInt(years, 10)
    if (Number.isNaN(parsed)) errors.yearsExp = 'Enter a whole number of years.'
    else if (parsed < YEARS_MIN || parsed > YEARS_MAX)
      errors.yearsExp = `Between ${YEARS_MIN} and ${YEARS_MAX}.`
  }

  if (form.designation.trim().length > NAME_MAX)
    errors.designation = `At most ${NAME_MAX} characters.`
  if (form.station.trim().length > NAME_MAX) errors.station = `At most ${NAME_MAX} characters.`
  if (form.education.trim().length > 240) errors.education = 'At most 240 characters.'

  return errors
}

function StepProfile({
  form,
  setForm,
  onNext,
}: {
  form: ProfileForm
  setForm: Dispatch<SetStateAction<ProfileForm>>
  onNext: () => void
}) {
  const { user, applyProfile } = useAuth()
  const updateProfile = useUpdateProfile()
  const profile = user?.profile

  const department = profile?.department ?? 'Ministry of Statistics and Programme Implementation'
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<keyof ProfileForm, string>>>({})
  const [error, setError] = useState<string | null>(null)

  function set<K extends keyof ProfileForm>(key: K, value: string) {
    setForm((prev) => ({ ...prev, [key]: value }))
    setFieldErrors((prev) => ({ ...prev, [key]: undefined }))
  }

  async function handleNext() {
    setError(null)
    const errors = validateProfile(form)
    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors)
      return
    }

    const years = form.yearsExp.trim()
    try {
      const saved = await updateProfile.mutateAsync({
        full_name: form.fullName.trim(),
        designation: form.designation.trim() || undefined,
        station: form.station.trim() || undefined,
        years_experience: years === '' ? undefined : Number.parseInt(years, 10),
        education: form.education.trim() || undefined,
      })
      // AuthProvider holds the profile in state, not in the query cache, so the
      // saved record has to be folded back in or the shell keeps the old name.
      applyProfile(saved)
      onNext()
    } catch {
      setError('Could not save your profile. Please try again.')
    }
  }

  const inputClass =
    'w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-14 text-slate-900 focus:border-[#F58220] focus:outline-none focus:ring-2 focus:ring-[#F58220]/20 transition-colors'
  const errorInputClass =
    'w-full rounded-lg border border-red-300 bg-white px-3 py-2.5 text-14 text-slate-900 focus:border-red-400 focus:outline-none focus:ring-2 focus:ring-red-200 transition-colors'
  const labelClass = 'block text-12 font-semibold text-slate-700 mb-1.5'
  const hintClass = 'mt-1 text-11 font-medium text-red-600'

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="ob-fullname" className={labelClass}>
            Full Name <span className="text-red-500">*</span>
          </label>
          <input
            id="ob-fullname"
            className={fieldErrors.fullName ? errorInputClass : inputClass}
            value={form.fullName}
            onChange={(e) => set('fullName', e.target.value)}
            placeholder="Your full name"
            maxLength={NAME_MAX}
            aria-invalid={Boolean(fieldErrors.fullName)}
            aria-describedby={fieldErrors.fullName ? 'ob-fullname-error' : undefined}
          />
          {fieldErrors.fullName && (
            <p id="ob-fullname-error" className={hintClass}>
              {fieldErrors.fullName}
            </p>
          )}
        </div>
        <div>
          <label htmlFor="ob-designation" className={labelClass}>
            Designation / Post
          </label>
          <input
            id="ob-designation"
            className={fieldErrors.designation ? errorInputClass : inputClass}
            value={form.designation}
            onChange={(e) => set('designation', e.target.value)}
            placeholder="e.g. Statistical Officer"
            maxLength={NAME_MAX}
          />
          {fieldErrors.designation && <p className={hintClass}>{fieldErrors.designation}</p>}
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
            className={fieldErrors.station ? errorInputClass : inputClass}
            value={form.station}
            onChange={(e) => set('station', e.target.value)}
            placeholder="e.g. New Delhi"
            maxLength={NAME_MAX}
          />
          {fieldErrors.station && <p className={hintClass}>{fieldErrors.station}</p>}
        </div>
        <div>
          <label htmlFor="ob-exp" className={labelClass}>
            <Briefcase size={12} className="inline mr-1 text-slate-400" />
            Years of Experience
          </label>
          <input
            id="ob-exp"
            type="number"
            inputMode="numeric"
            min={YEARS_MIN}
            max={YEARS_MAX}
            step={1}
            className={fieldErrors.yearsExp ? errorInputClass : inputClass}
            value={form.yearsExp}
            onChange={(e) => set('yearsExp', e.target.value)}
            aria-invalid={Boolean(fieldErrors.yearsExp)}
            aria-describedby={fieldErrors.yearsExp ? 'ob-exp-error' : undefined}
          />
          {fieldErrors.yearsExp && (
            <p id="ob-exp-error" className={hintClass}>
              {fieldErrors.yearsExp}
            </p>
          )}
        </div>
      </div>

      <div>
        <label htmlFor="ob-education" className={labelClass}>
          <GraduationCap size={12} className="inline mr-1 text-slate-400" />
          Highest Qualification
        </label>
        <input
          id="ob-education"
          className={fieldErrors.education ? errorInputClass : inputClass}
          value={form.education}
          onChange={(e) => set('education', e.target.value)}
          placeholder="e.g. M.Sc. Statistics, IIT Delhi"
          maxLength={240}
        />
        {fieldErrors.education && <p className={hintClass}>{fieldErrors.education}</p>}
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
        disabled={updateProfile.isPending}
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

function StepAssessment({
  levels,
  setLevels,
  onNext,
  onBack,
}: {
  levels: ClusterLevels
  setLevels: Dispatch<SetStateAction<ClusterLevels>>
  onNext: () => void
  onBack: () => void
}) {
  const { data: competencies, isLoading, isError, refetch } = useCompetencies()
  const declareBatch = useDeclareBatch()
  const [error, setError] = useState<string | null>(null)

  async function handleNext() {
    setError(null)
    if (!competencies || competencies.length === 0) {
      setError('The competency framework has not loaded, so nothing can be saved yet.')
      return
    }

    // Every competency in a cluster inherits its cluster's declared level.
    const declarations = competencies.map((c) => ({
      competency_id: c.id,
      level: levels[c.cluster] ?? 1,
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

  // The sliders are built from a static cluster list, so without this branch the
  // form would render perfectly and the Continue button would do nothing at all.
  if (isError || !competencies) {
    return (
      <div className="space-y-4">
        <ErrorNote>
          The competency framework could not be loaded, so your self-assessment cannot be saved
          against it yet.
        </ErrorNote>
        <div className="flex gap-3">
          <button
            type="button"
            onClick={onBack}
            className="flex-1 rounded-xl border border-slate-300 py-3 text-14 font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
          >
            ← Back
          </button>
          <button
            type="button"
            onClick={() => void refetch()}
            className="flex-[2] rounded-xl bg-[#0B3060] py-3 text-14 font-bold text-white hover:bg-[#F58220] transition-colors"
          >
            Try again
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <p className="text-13 text-slate-600 leading-relaxed bg-amber-50 border border-amber-200 rounded-xl px-4 py-3">
        <span className="font-bold text-amber-800">Self-declaration</span> — rate your current level
        in each domain. This is your starting point; formal assessments will refine it. All
        declarations are stored at low confidence (0.25) and will be updated as you complete quizzes.
      </p>

      {Object.entries(CLUSTER_META).map(([cluster, meta]) => {
        const Icon = meta.icon
        const level = levels[cluster] ?? 1
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
                <p className="text-10 font-mono text-slate-400 whitespace-nowrap">/ 4 FRAC</p>
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
                  setLevels((prev) => ({ ...prev, [cluster]: Number(e.target.value) }))
                }
                className="w-full accent-current h-2 rounded-full cursor-pointer"
                style={{ accentColor: meta.color }}
                aria-label={`${meta.label} level`}
              />
              <div className="flex justify-between px-0.5">
                {[0, 1, 2, 3, 4].map((l) => (
                  <span
                    key={l}
                    className={`text-10 font-mono ${l === level ? 'font-black' : 'text-slate-400'}`}
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
                {fracLabel(level)}
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
              Save & Continue
              <ChevronRight size={16} />
            </>
          )}
        </button>
      </div>
    </div>
  )
}

// ── Step 3: Assessment Gate ────────────────────────────────────────────────────
// Replaces the old "auto-generate recommendations" step.
// Instead of calling /recommendations/generate immediately, we tell the officer
// that a competency assessment is required before their learning path is ready.

function StepAssessmentCTA() {
  function goToAssessment() {
    // Hard-navigate so /auth/me is re-fetched (the onboarded flag changed).
    window.location.assign('/initial-assessment')
  }

  return (
    <div className="space-y-6 py-2">
      {/* Success badge */}
      <div className="flex flex-col items-center gap-3 text-center">
        <div className="flex h-20 w-20 items-center justify-center rounded-full bg-emerald-100 shadow-sm">
          <CheckCircle2 size={40} className="text-emerald-500" />
        </div>
        <div>
          <h3 className="text-20 font-black text-slate-900">Profile Created Successfully!</h3>
          <p className="text-13 text-slate-500 mt-1">Your skill levels have been saved.</p>
        </div>
      </div>

      {/* Assessment prompt */}
      <div className="rounded-2xl border border-[#0B3060]/15 bg-gradient-to-br from-[#0B3060]/5 to-[#154399]/8 p-5 space-y-3">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#F58220]/15">
            <Brain size={16} className="text-[#F58220]" />
          </div>
          <p className="text-14 font-bold text-[#0B3060]">One more step before your learning path</p>
        </div>
        <p className="text-13 text-slate-600 leading-relaxed">
          Before we recommend courses, we need to assess your <strong>actual competency level</strong>.
          This short test (~20–25 questions) ensures your recommendations are based on your real
          skills — not just self-reported levels.
        </p>
        <div className="grid grid-cols-3 gap-2 pt-1">
          {[
            { label: 'Questions', value: '20–25' },
            { label: 'Duration', value: '~15 min' },
            { label: 'Competencies', value: '4–6' },
          ].map(({ label, value }) => (
            <div key={label} className="rounded-xl bg-white border border-slate-100 p-3 text-center shadow-sm">
              <p className="text-16 font-black text-[#0B3060]">{value}</p>
              <p className="text-11 text-slate-500">{label}</p>
            </div>
          ))}
        </div>
      </div>

      <button
        type="button"
        onClick={goToAssessment}
        className="w-full flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-[#0B3060] to-[#154399] py-3.5 text-14 font-bold text-white shadow-lg hover:opacity-90 active:scale-[0.98] transition-all"
      >
        <Sparkles size={16} />
        Start Competency Assessment
        <ChevronRight size={16} />
      </button>

      <p className="text-12 text-slate-400 text-center">
        You can retake assessments anytime from your profile.
      </p>
    </div>
  )
}

// ── Main wizard ───────────────────────────────────────────────────────────────

export default function Onboarding() {
  const { user } = useAuth()
  const [step, setStep] = useState(1)

  const profile = user?.profile
  const [form, setForm] = useState<ProfileForm>(() => ({
    fullName: profile?.full_name ?? '',
    designation: profile?.designation ?? '',
    station: profile?.station ?? '',
    yearsExp: String(profile?.years_experience ?? 0),
    education: profile?.education ?? '',
  }))
  const [clusterLevels, setClusterLevels] = useState<ClusterLevels>({
    STATISTICAL: 1,
    TECHNICAL: 1,
    DIGITAL_GOVERNANCE: 1,
    BEHAVIOURAL: 1,
  })

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#F0F4FF] via-[#F8FAFC] to-white flex flex-col">
      {/* Tricolor strip */}
      <div className="tricolor-strip" />

      {/* Header */}
      <header className="bg-white border-b border-slate-200 shadow-sm">
        <div className="mx-auto flex max-w-3xl items-center gap-3 px-4 py-3 sm:px-6">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-[#0B3060] to-[#154399] shadow">
            <svg viewBox="0 0 24 24" className="h-7 w-7 fill-current text-white" aria-hidden="true">
              <path
                d="M12 2L14.5 8.5L21.5 9.5L16.5 14.5L18 21.5L12 18L6 21.5L7.5 14.5L2.5 9.5L9.5 8.5L12 2Z"
                fill="#F58220"
              />
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
              <h2 className="text-24 font-extrabold text-[#0B3060]">Competency Assessment</h2>
              <p className="mt-1 text-14 text-slate-500">
                A short test to measure your actual competency before recommending courses
              </p>
            </>
          )}
        </div>

        {/* White card content */}
        <div className="rounded-2xl border border-slate-200 bg-white p-5 sm:p-6 shadow-sm">
          {step === 1 && <StepProfile form={form} setForm={setForm} onNext={() => setStep(2)} />}
          {step === 2 && (
            <StepAssessment
              levels={clusterLevels}
              setLevels={setClusterLevels}
              onNext={() => setStep(3)}
              onBack={() => setStep(1)}
            />
          )}
          {step === 3 && <StepAssessmentCTA />}
        </div>

        {/* Footer note */}
        <p className="mt-5 text-center text-11 text-slate-400">
          Your data is secured by MoSPI's FRAC competency ledger · SIH 2026
        </p>
      </main>
    </div>
  )
}
