import { useState, useEffect } from 'react'
import {
  AlertTriangle,
  CheckCircle2,
  GraduationCap,
  Lock,
  Play,
  Shield,
  ShieldAlert,
  ShieldCheck,
  XCircle,
} from 'lucide-react'

import {
  Button,
  Card,
  DataTable,
  EmptyState,
  ErrorNote,
  Field,
  LevelBar,
  PageHeader,
  Skeleton,
  inputClass,
  type Column,
} from '../components/common'
import { QuizPlayer } from '../components/quiz/QuizPlayer'
import { ResultScreen } from '../components/quiz/ResultScreen'
import {
  useAssessmentHistory,
  useCreateAssessment,
  useGaps,
  useTerminateAssessment,
} from '../hooks'
import { errorMessage } from '../lib/api'
import { formatDate } from '../lib/format'
import type { Assessment, AssessmentHistoryItem, SubmitResponse } from '../lib/types'

export default function Assessments() {
  const gaps = useGaps()
  const history = useAssessmentHistory()
  const create = useCreateAssessment()
  const terminateMutation = useTerminateAssessment()

  const [active, setActive] = useState<Assessment | null>(null)
  const [result, setResult] = useState<SubmitResponse | null>(null)
  const [competencyId, setCompetencyId] = useState('')
  const [count, setCount] = useState(10)

  // Security & Proctoring state
  const [showAgreement, setShowAgreement] = useState(false)
  const [warnings, setWarnings] = useState(0)
  const [showWarningModal, setShowWarningModal] = useState(false)
  const [isTerminated, setIsTerminated] = useState(false)

  const openGaps = (gaps.data?.gaps ?? []).filter((gap) => gap.gap > 0)
  const selected = competencyId || openGaps[0]?.competency_id || ''

  // Proctoring security listeners during active assessment
  useEffect(() => {
    if (!active || isTerminated) return

    const handleViolation = () => {
      setWarnings((w) => {
        const next = w + 1
        if (next >= 3) {
          terminateMutation.mutateAsync().catch(console.error)
          setIsTerminated(true)
          setActive(null)
          if (document.fullscreenElement) {
            document.exitFullscreen().catch(() => {})
          }
        } else {
          setShowWarningModal(true)
        }
        return next
      })
    }

    const handleVisibilityChange = () => {
      if (document.visibilityState === 'hidden') {
        handleViolation()
      }
    }

    const handleFullscreenChange = () => {
      if (!document.fullscreenElement && !showWarningModal) {
        handleViolation()
      }
    }

    const handleBlur = () => {
      if (!showWarningModal) {
        handleViolation()
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    document.addEventListener('fullscreenchange', handleFullscreenChange)
    window.addEventListener('blur', handleBlur)

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
      document.removeEventListener('fullscreenchange', handleFullscreenChange)
      window.removeEventListener('blur', handleBlur)
    }
  }, [active, showWarningModal, isTerminated, terminateMutation])

  function handleStartClick() {
    // Show security agreement before beginning
    setShowAgreement(true)
  }

  async function proceedWithAssessment() {
    setShowAgreement(false)
    setResult(null)
    setWarnings(0)
    setShowWarningModal(false)
    setIsTerminated(false)

    // Request fullscreen for proctoring security
    try {
      if (!document.fullscreenElement) {
        await document.documentElement.requestFullscreen()
      }
    } catch {
      // Browser may block if user didn't interact directly, handled gracefully
    }

    const assessment = await create.mutateAsync({ competencyId: selected, count })
    setActive(assessment)
  }

  function handleDismissWarning() {
    setShowWarningModal(false)
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {})
    }
  }

  function reset() {
    if (document.fullscreenElement) {
      document.exitFullscreen().catch(() => {})
    }
    setActive(null)
    setResult(null)
    setIsTerminated(false)
  }

  const columns: Column<AssessmentHistoryItem>[] = [
    {
      key: 'competency',
      header: 'Competency',
      render: (row) => (
        <div>
          <span className="text-ink">{row.competency_name ?? '—'}</span>
          <span className="ml-2 font-mono text-11 text-ink-3">{row.competency_code}</span>
        </div>
      ),
    },
    {
      key: 'score',
      header: 'Score',
      numeric: true,
      render: (row) => (
        <span className="numeral">{row.score != null ? `${row.score.toFixed(0)}%` : '—'}</span>
      ),
      width: '80px',
    },
    {
      key: 'correct',
      header: 'Correct',
      numeric: true,
      render: (row) => (
        <span className="numeral text-ink-2">
          {row.correct_count ?? '—'} / {row.total_questions}
        </span>
      ),
      width: '90px',
    },
    {
      key: 'level',
      header: 'Level change',
      render: (row) =>
        row.level_after != null ? (
          <span className="numeral">
            {row.level_before} <span className="text-ink-3">→</span> {row.level_after}
          </span>
        ) : (
          <span className="text-ink-3">—</span>
        ),
      width: '120px',
    },
    {
      key: 'submitted',
      header: 'Submitted',
      render: (row) => <span className="text-ink-2">{formatDate(row.submitted_at)}</span>,
      width: '130px',
    },
  ]

  // ── Terminated view ────────────────────────────────────────────────────────
  if (isTerminated) {
    return (
      <div className="mx-auto max-w-lg rounded-2xl border border-red-200 bg-white p-8 text-center shadow-lg my-12">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-red-100 text-red-600 mb-4">
          <XCircle size={36} />
        </div>
        <h2 className="text-22 font-extrabold text-slate-900">Assessment Terminated</h2>
        <p className="mt-2 text-13 text-slate-600 leading-relaxed">
          Your assessment was terminated because you exceeded the 3 allowable security warnings
          (tab switching, window focus loss, or leaving full-screen).
        </p>
        <div className="mt-5 rounded-xl border border-red-200 bg-red-50 p-4 text-left">
          <div className="flex items-center gap-2 text-13 font-bold text-red-800">
            <Lock size={15} />
            <span>Account Blocked for 5 Hours</span>
          </div>
          <p className="mt-1 text-11 text-red-700 leading-relaxed">
            Due to academic integrity protocol, your account is temporarily restricted.
            Only a system administrator can review and unblock your account in the Admin Panel.
          </p>
        </div>
        <button
          type="button"
          onClick={() => window.location.assign('/')}
          className="mt-6 w-full rounded-xl bg-slate-900 py-3 text-13 font-bold text-white hover:bg-slate-800 transition-colors shadow-xs"
        >
          Return to Dashboard
        </button>
      </div>
    )
  }

  // ── Result view ────────────────────────────────────────────────────────────
  if (result) {
    return (
      <>
        <PageHeader
          title="Assessment result"
          description="Scored deterministically, competency level updated, gap recomputed and recommendations regenerated in a single request."
        />
        <ResultScreen result={result} onRetake={reset} />
      </>
    )
  }

  // ── Quiz view (Proctored) ──────────────────────────────────────────────────
  if (active) {
    return (
      <div className="space-y-4">
        {/* Floating Proctoring Security Header */}
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-blue-200 bg-gradient-to-r from-blue-50 via-indigo-50 to-white px-4 py-2.5 shadow-xs">
          <div className="flex items-center gap-2.5">
            <span className="relative flex h-2.5 w-2.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-emerald-500" />
            </span>
            <div className="flex items-center gap-1.5">
              <ShieldCheck size={16} className="text-[#0B3060]" />
              <span className="text-11 font-extrabold uppercase tracking-wider text-[#0B3060]">
                AI-Proctored Secure Session Active
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span
              className={`rounded-full px-2.5 py-0.5 text-10 font-black uppercase tracking-wider border ${
                warnings === 0
                  ? 'bg-emerald-100 text-emerald-800 border-emerald-200'
                  : warnings === 1
                  ? 'bg-amber-100 text-amber-800 border-amber-300 animate-pulse'
                  : 'bg-red-100 text-red-800 border-red-300 animate-pulse'
              }`}
            >
              Warnings: {warnings} / 3
            </span>
            <span className="hidden sm:inline-block text-10 text-slate-500 font-mono">
              Fullscreen & Focus Enforced
            </span>
          </div>
        </div>

        <PageHeader
          title={active.competency_name ?? 'Competency Assessment'}
          description={`${active.total_questions} questions. Your answers are saved as you go.`}
          action={
            <Button variant="ghost" onClick={reset} className="text-12 text-slate-500 hover:text-red-600">
              Abandon Assessment
            </Button>
          }
        />

        <QuizPlayer
          assessment={active}
          onComplete={(res) => {
            if (document.fullscreenElement) {
              document.exitFullscreen().catch(() => {})
            }
            setResult(res)
          }}
        />

        {/* Warning Dialog Modal */}
        {showWarningModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4 backdrop-blur-xs">
            <div className="w-full max-w-md rounded-2xl border-2 border-amber-400 bg-white p-6 shadow-2xl animate-scale-in text-center">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-amber-100 text-amber-600 mb-3">
                <AlertTriangle size={30} />
              </div>
              <h3 className="text-18 font-black text-slate-900">
                Security Violation Warning ({warnings} of 3)
              </h3>
              <p className="mt-2 text-13 text-slate-600 leading-relaxed">
                You have switched tabs, left full-screen, or lost focus on the assessment window.
                This violation has been logged.
              </p>
              <div className="mt-3 rounded-lg bg-red-50 p-2.5 text-11 font-bold text-red-700 border border-red-200">
                Warning: Reaching 3 violations will immediately terminate your assessment and lock your account for 5 hours.
              </div>
              <button
                type="button"
                onClick={handleDismissWarning}
                className="mt-5 w-full rounded-xl bg-[#0B3060] py-2.5 text-13 font-bold text-white hover:bg-[#154399] transition-colors shadow-xs"
              >
                Return to Full-Screen & Resume Test
              </button>
            </div>
          </div>
        )}
      </div>
    )
  }

  // ── Start view ─────────────────────────────────────────────────────────────
  return (
    <>
      <PageHeader
        title="Assessments"
        description="Take a competency assessment. AI-proctoring ensures academic integrity with strict full-screen and tab-switch monitoring."
      />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
        <Card className="lg:col-span-5" label="Start an assessment">
          {gaps.isLoading && <Skeleton className="h-32 w-full" />}
          {gaps.data && openGaps.length === 0 && (
            <EmptyState
              icon={GraduationCap}
              title="You have no open gaps. Every competency meets its requirement."
            />
          )}
          {openGaps.length > 0 && (
            <div className="space-y-4">
              <Field id="competency" label="Competency">
                <select
                  id="competency"
                  className={inputClass}
                  value={selected}
                  onChange={(event) => setCompetencyId(event.target.value)}
                >
                  {openGaps.map((gap) => (
                    <option key={gap.competency_id} value={gap.competency_id}>
                      {gap.competency_name} — level {gap.current_level} of {gap.required_level} (
                      {gap.band})
                    </option>
                  ))}
                </select>
              </Field>

              <Field
                id="count"
                label="Number of questions"
                hint="At least five questions are needed for a result to change your level."
              >
                <input
                  id="count"
                  type="number"
                  min={5}
                  max={50}
                  className={inputClass}
                  value={count}
                  onChange={(event) => setCount(Number(event.target.value))}
                />
              </Field>

              {/* Proctoring notice banner */}
              <div className="rounded-lg border border-amber-200 bg-amber-50/60 p-3 text-11 text-amber-900">
                <div className="flex items-center gap-1.5 font-bold mb-1">
                  <Shield size={13} className="text-amber-700" />
                  <span>Secure AI-Proctored Test</span>
                </div>
                <p className="text-slate-600 text-10 leading-relaxed">
                  Full-screen is required. Exceeding 3 tab switches or focus violations triggers automatic termination and a 5-hour account lockout.
                </p>
              </div>

              {create.isError && <ErrorNote>{errorMessage(create.error)}</ErrorNote>}

              <Button
                variant="primary"
                icon={Play}
                loading={create.isPending}
                onClick={handleStartClick}
              >
                Start assessment
              </Button>
            </div>
          )}
        </Card>

        <Card className="lg:col-span-7" label="Current standing">
          {gaps.data && (
            <ul className="space-y-3">
              {openGaps.slice(0, 6).map((gap) => (
                <li key={gap.competency_id} className="flex items-center justify-between gap-4">
                  <div className="min-w-0">
                    <p className="truncate text-14 text-ink">{gap.competency_name}</p>
                    <p className="font-mono text-11 text-ink-3">{gap.competency_code}</p>
                  </div>
                  <LevelBar current={gap.current_level} required={gap.required_level} />
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>

      <Card className="mt-4" label="History">
        {history.isLoading && <Skeleton className="h-32 w-full" />}
        {history.data && (
          <DataTable
            columns={columns}
            rows={history.data}
            keyOf={(row) => row.id}
            caption="Your previous assessments"
            empty={
              <EmptyState icon={GraduationCap} title="You have not taken an assessment yet." />
            }
          />
        )}
      </Card>

      {/* Security Agreement Modal */}
      {showAgreement && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4 backdrop-blur-xs">
          <div className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl animate-scale-in">
            <div className="flex items-center gap-3 mb-4">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-100 text-[#0B3060]">
                <ShieldAlert size={24} />
              </div>
              <div>
                <h3 className="text-16 font-black text-slate-900">
                  AI-Proctored Secure Assessment Protocol
                </h3>
                <p className="text-11 text-slate-500">Ministry of Statistics & Programme Implementation</p>
              </div>
            </div>

            <div className="space-y-3 rounded-xl border border-slate-200 bg-slate-50 p-4 text-12 text-slate-700">
              <div className="flex items-start gap-2">
                <CheckCircle2 size={16} className="text-emerald-600 mt-0.5 shrink-0" />
                <p>
                  <strong>Full-Screen Enforced:</strong> The assessment will expand to full-screen. Exiting full-screen is recorded as a violation.
                </p>
              </div>
              <div className="flex items-start gap-2">
                <CheckCircle2 size={16} className="text-emerald-600 mt-0.5 shrink-0" />
                <p>
                  <strong>No Tab Switching:</strong> Navigating away from this tab or minimizing the browser window is prohibited.
                </p>
              </div>
              <div className="flex items-start gap-2">
                <AlertTriangle size={16} className="text-amber-600 mt-0.5 shrink-0" />
                <p>
                  <strong>3-Warning Limit:</strong> You will receive a warning on your 1st and 2nd violation. A 3rd violation results in <strong>immediate termination</strong>.
                </p>
              </div>
              <div className="flex items-start gap-2">
                <Lock size={16} className="text-red-600 mt-0.5 shrink-0" />
                <p>
                  <strong>5-Hour Account Lockout:</strong> If terminated, your account will be locked for 5 hours and can only be unlocked by an administrator in the Admin Panel.
                </p>
              </div>
            </div>

            <div className="mt-6 flex items-center justify-end gap-3">
              <button
                type="button"
                onClick={() => setShowAgreement(false)}
                className="rounded-xl px-4 py-2 text-12 font-bold text-slate-600 hover:bg-slate-100 transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={proceedWithAssessment}
                disabled={create.isPending}
                className="inline-flex items-center gap-1.5 rounded-xl bg-[#0B3060] px-5 py-2.5 text-12 font-bold text-white hover:bg-[#154399] transition-colors shadow-xs disabled:opacity-50"
              >
                <ShieldCheck size={15} />
                <span>Agree & Enter Secure Assessment</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
