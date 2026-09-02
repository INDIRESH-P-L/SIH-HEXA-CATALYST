/**
 * InitialAssessment — the competency test that bridges onboarding and recommendations.
 */

import { useEffect, useState } from 'react'
import {
  AlertTriangle,
  ArrowRight,
  Award,
  BookOpen,
  Brain,
  CheckCircle2,
  ChevronRight,
  ClipboardList,
  LayoutDashboard,
  Sparkles,
  Target,
  TrendingUp,
  XCircle,
} from 'lucide-react'

import { Spinner } from '../components/common'
import { useAuth } from '../lib/auth'
import {
  useAnswer,
  useAssessment,
  useCompleteInitialAssessment,
  useInitialAssessmentTopics,
  useStartInitialAssessment,
  useSubmitAssessment,
  useTerminateInitialAssessment,
} from '../hooks'
import type { InitialCompleteResponse, StartedAssessmentRef } from '../lib/types'

// ── Constants ──────────────────────────────────────────────────────────────────

const GAP_COLORS: Record<string, string> = {
  critical: 'bg-red-100 text-red-700 border-red-200',
  high: 'bg-orange-100 text-orange-700 border-orange-200',
  medium: 'bg-amber-100 text-amber-700 border-amber-200',
  none: 'bg-emerald-100 text-emerald-700 border-emerald-200',
  above_required: 'bg-blue-100 text-blue-700 border-blue-200',
}

const GAP_LABELS: Record<string, string> = {
  critical: 'Critical Gap',
  high: 'High Gap',
  medium: 'Moderate Gap',
  none: 'No Gap',
  above_required: 'Above Required',
}

function gapColor(band: string) {
  return GAP_COLORS[band] ?? 'bg-slate-100 text-slate-700 border-slate-200'
}
function gapLabel(band: string) {
  return GAP_LABELS[band] ?? band
}

// ── Score bar ──────────────────────────────────────────────────────────────────

function ScoreBar({ score, color = '#0B3060' }: { score: number; color?: string }) {
  return (
    <div className="h-2.5 w-full rounded-full bg-slate-100 overflow-hidden">
      <div
        className="h-full rounded-full transition-all duration-700"
        style={{ width: `${Math.max(score, 2)}%`, backgroundColor: color }}
      />
    </div>
  )
}

// ── Phase 1: Intro ─────────────────────────────────────────────────────────────

function IntroScreen({ onStart, loading }: { onStart: () => void; loading: boolean }) {
  const { data: topics, isLoading } = useInitialAssessmentTopics()

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner label="Preparing your assessment..." />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-[#0B3060] to-[#154399] shadow-lg mx-auto">
          <ClipboardList size={30} className="text-white" />
        </div>
        <h1 className="text-26 font-black text-[#0B3060]">Initial Competency Assessment</h1>
        <p className="text-14 text-slate-500 max-w-md mx-auto">
          Answer honestly. Your results determine your personalised learning path.
        </p>
      </div>

      <div className="grid grid-cols-3 gap-3">
        {[
          { label: 'Questions', value: String(topics?.total_questions ?? '20-25') },
          { label: 'Duration', value: '~15 min' },
          { label: 'Competencies', value: String(topics?.topics.length ?? 4) },
        ].map(({ label, value }) => (
          <div key={label} className="rounded-2xl border border-slate-200 bg-white p-4 text-center shadow-sm">
            <p className="text-22 font-black text-[#0B3060]">{value}</p>
            <p className="text-12 text-slate-500 mt-0.5">{label}</p>
          </div>
        ))}
      </div>

      {topics && topics.topics.length > 0 && (
        <div className="rounded-2xl border border-[#0B3060]/10 bg-[#0B3060]/5 p-4 space-y-3">
          <p className="text-13 font-bold text-[#0B3060] flex items-center gap-2">
            <Target size={14} />
            Competencies you will be tested on
          </p>
          <div className="space-y-2">
            {topics.topics.map((t) => (
              <div key={t.competency_id} className="flex items-center justify-between text-13">
                <span className="font-medium text-slate-700">{t.competency_name}</span>
                <span className="text-slate-400">{t.question_count} questions</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 space-y-1.5">
        <p className="text-13 font-bold text-amber-800 flex items-center gap-2">
          <AlertTriangle size={14} />
          Important
        </p>
        <ul className="text-13 text-amber-700 space-y-1 list-disc list-inside">
          <li>Scores are calculated by the system, not an AI</li>
          <li>Screen sharing is required for proctoring</li>
          <li>Do NOT switch tabs or leave full-screen mode</li>
        </ul>
      </div>

      <button
        id="start-assessment-btn"
        onClick={onStart}
        disabled={loading}
        className="w-full flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-[#0B3060] to-[#154399] py-4 text-15 font-bold text-white shadow-lg hover:opacity-90 active:scale-[0.98] transition-all disabled:opacity-60"
      >
        {loading ? <Spinner label="" /> : (
          <>
            <Brain size={18} />
            Start Assessment
            <ChevronRight size={18} />
          </>
        )}
      </button>
    </div>
  )
}

// ── Phase 2: Quiz ──────────────────────────────────────────────────────────────

function QuizScreen({
  ref_,
  totalQuestions,
  assessmentIndex,
  totalAssessments,
  onDone,
}: {
  ref_: StartedAssessmentRef
  totalQuestions: number
  assessmentIndex: number
  totalAssessments: number
  onDone: (assessmentId: string) => void
}) {
  const { data: assessment, isLoading } = useAssessment(ref_.assessment_id)
  const answerMutation = useAnswer()
  const submitMutation = useSubmitAssessment()

  const [selected, setSelected] = useState<number | null>(null)
  const [localIdx, setLocalIdx] = useState(0)
  const [submitting, setSubmitting] = useState(false)

  const questions = assessment?.questions ?? []
  const question = questions[localIdx]
  const isLast = localIdx === questions.length - 1

  useEffect(() => {
    setSelected(question?.selected_index ?? null)
  }, [localIdx, question])

  async function handleSelect(idx: number) {
    if (!question || answerMutation.isPending) return
    setSelected(idx)
    await answerMutation.mutateAsync({
      assessmentId: ref_.assessment_id,
      questionId: question.id,
      selectedIndex: idx,
    })
  }

  async function handleNext() {
    if (selected === null) return
    if (!isLast) {
      setLocalIdx((i) => i + 1)
    } else {
      setSubmitting(true)
      try {
        await submitMutation.mutateAsync(ref_.assessment_id)
        onDone(ref_.assessment_id)
      } finally {
        setSubmitting(false)
      }
    }
  }

  if (isLoading || !assessment || !question) {
    return (
      <div className="flex min-h-[300px] items-center justify-center">
        <Spinner label="Loading questions..." />
      </div>
    )
  }

  const overallProgress =
    ((assessmentIndex * assessment.total_questions + localIdx) / totalQuestions) * 100

  return (
    <div className="space-y-5">
      <div className="space-y-2">
        <div className="flex items-center justify-between text-12 text-slate-500">
          <span className="font-semibold text-[#0B3060]">{ref_.competency_name}</span>
          <span>Question {localIdx + 1} of {questions.length}</span>
        </div>
        <div className="h-2 w-full rounded-full bg-slate-100 overflow-hidden">
          <div
            className="h-full rounded-full bg-gradient-to-r from-[#0B3060] to-[#F58220] transition-all duration-500"
            style={{ width: `${overallProgress}%` }}
          />
        </div>
        <div className="flex items-center justify-between text-11 text-slate-400">
          <span>Competency {assessmentIndex + 1} of {totalAssessments}</span>
          <span>{Math.round(overallProgress)}% overall</span>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm space-y-4">
        <div className="flex items-start gap-3">
          <span className="shrink-0 flex h-7 w-7 items-center justify-center rounded-lg bg-[#0B3060]/10 text-12 font-bold text-[#0B3060]">
            {localIdx + 1}
          </span>
          <p className="text-15 font-semibold text-slate-800 leading-snug">{question.question_text}</p>
        </div>

        {question.difficulty && (
          <span className={`inline-block text-11 font-bold px-2 py-0.5 rounded-full ${
            question.difficulty === 'hard' ? 'bg-red-100 text-red-700' :
            question.difficulty === 'medium' ? 'bg-amber-100 text-amber-700' :
            'bg-emerald-100 text-emerald-700'
          }`}>
            {question.difficulty.charAt(0).toUpperCase() + question.difficulty.slice(1)}
          </span>
        )}

        <div className="space-y-2.5 pt-1">
          {(question.options ?? []).map((opt, idx) => {
            const isSelected = selected === idx
            return (
              <button
                key={idx}
                id={`option-${idx}`}
                onClick={() => void handleSelect(idx)}
                disabled={answerMutation.isPending}
                className={`w-full flex items-center gap-3 rounded-xl border p-3.5 text-left text-14 font-medium transition-all ${
                  isSelected
                    ? 'border-[#0B3060] bg-[#0B3060]/10 text-[#0B3060] shadow-sm'
                    : 'border-slate-200 bg-slate-50 text-slate-700 hover:border-[#0B3060]/30 hover:bg-[#0B3060]/5'
                }`}
              >
                <span className={`shrink-0 flex h-6 w-6 items-center justify-center rounded-full border-2 text-11 font-bold transition-all ${
                  isSelected ? 'border-[#0B3060] bg-[#0B3060] text-white' : 'border-slate-300 text-slate-500'
                }`}>
                  {String.fromCharCode(65 + idx)}
                </span>
                {opt}
              </button>
            )
          })}
        </div>
      </div>

      <button
        id="next-question-btn"
        onClick={() => void handleNext()}
        disabled={selected === null || submitting}
        className="w-full flex items-center justify-center gap-2 rounded-2xl bg-[#0B3060] py-3.5 text-14 font-bold text-white shadow hover:bg-[#154399] active:scale-[0.98] transition-all disabled:opacity-40"
      >
        {submitting ? <Spinner label="" /> : isLast ? (
          <><CheckCircle2 size={16} /> Submit &amp; Continue</>
        ) : (
          <>Next <ArrowRight size={16} /></>
        )}
      </button>
    </div>
  )
}

// ── Phase 3: Processing ────────────────────────────────────────────────────────

function ProcessingScreen() {
  return (
    <div className="space-y-6 py-8 text-center">
      <div className="relative flex h-24 w-24 items-center justify-center mx-auto">
        <div className="absolute inset-0 rounded-full border-4 border-[#0B3060]/10 animate-ping" />
        <div className="flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-[#0B3060] to-[#154399] shadow-lg">
          <Brain size={32} className="text-[#F58220]" />
        </div>
      </div>
      <div>
        <h2 className="text-20 font-black text-slate-900">Analysing Your Responses</h2>
        <p className="text-14 text-slate-500 mt-1 max-w-sm mx-auto">
          Calculating competency scores, identifying gaps, and generating AI insights...
        </p>
      </div>
      <div className="space-y-2.5 max-w-xs mx-auto text-left">
        {[
          { icon: Target, label: 'Scoring each competency', delay: '0s' },
          { icon: TrendingUp, label: 'Calculating skill gaps', delay: '0.4s' },
          { icon: Sparkles, label: 'Generating AI insight', delay: '0.8s' },
          { icon: BookOpen, label: 'Matching courses to gaps', delay: '1.2s' },
        ].map(({ icon: Icon, label, delay }) => (
          <div
            key={label}
            className="flex items-center gap-3 rounded-xl border border-slate-100 bg-slate-50 px-4 py-2.5 opacity-0 animate-fade-in"
            style={{ animationDelay: delay, animationFillMode: 'forwards' }}
          >
            <Icon size={14} className="text-[#0B3060] shrink-0" />
            <p className="text-13 text-slate-600">{label}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Phase 4: Results ───────────────────────────────────────────────────────────

function ResultsScreen({ data }: { data: InitialCompleteResponse }) {
  const overallColor =
    data.overall_score >= 75 ? '#10b981' :
    data.overall_score >= 50 ? '#F58220' : '#ef4444'

  return (
    <div className="space-y-5">
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm text-center space-y-3">
        <div className="flex flex-col items-center gap-1">
          <div className="text-48 font-black leading-none" style={{ color: overallColor }}>
            {Math.round(data.overall_score)}<span className="text-20">%</span>
          </div>
          <p className="text-14 font-bold text-slate-600">Overall Competency Score</p>
        </div>
        <ScoreBar score={data.overall_score} color={overallColor} />
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm space-y-4">
        <h3 className="text-14 font-bold text-slate-800 flex items-center gap-2">
          <Target size={15} className="text-[#0B3060]" />
          Competency Breakdown
        </h3>
        <div className="space-y-4">
          {data.results.map((r) => {
            const barColor =
              r.gap_band === 'critical' ? '#ef4444' :
              r.gap_band === 'high' ? '#f97316' :
              r.gap_band === 'medium' ? '#f59e0b' : '#10b981'
            return (
              <div key={r.competency_id} className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-13 font-semibold text-slate-700">{r.competency_name}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-13 font-black" style={{ color: barColor }}>{Math.round(r.score)}%</span>
                    <span className="text-11 text-slate-400">{r.level_label}</span>
                  </div>
                </div>
                <ScoreBar score={r.score} color={barColor} />
                <div className="flex items-center justify-between text-11 text-slate-400">
                  <span>{r.correct}/{r.total} correct</span>
                  <span className={`px-1.5 py-0.5 rounded-full border text-10 font-bold ${gapColor(r.gap_band)}`}>
                    {gapLabel(r.gap_band)}
                  </span>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {data.top_gaps.length > 0 && (
        <div className="rounded-2xl border border-red-100 bg-red-50/50 p-4 space-y-3">
          <h3 className="text-13 font-bold text-red-800 flex items-center gap-2">
            <AlertTriangle size={14} />
            Top Skill Gaps
          </h3>
          <div className="space-y-2">
            {data.top_gaps.map((r, i) => (
              <div key={r.competency_id} className="flex items-center justify-between rounded-xl border border-red-100 bg-white px-3 py-2 text-13">
                <div className="flex items-center gap-2">
                  <span className="text-11 font-bold text-slate-400">#{i + 1}</span>
                  <span className="font-medium text-slate-700">{r.competency_name}</span>
                </div>
                <span className={`px-2 py-0.5 rounded-full border text-11 font-bold ${gapColor(r.gap_band)}`}>
                  {gapLabel(r.gap_band)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {data.strengths.length > 0 && (
        <div className="rounded-2xl border border-emerald-100 bg-emerald-50/50 p-4 space-y-3">
          <h3 className="text-13 font-bold text-emerald-800 flex items-center gap-2">
            <Award size={14} />
            Your Strengths
          </h3>
          <div className="space-y-2">
            {data.strengths.map((r) => (
              <div key={r.competency_id} className="flex items-center justify-between rounded-xl border border-emerald-100 bg-white px-3 py-2 text-13">
                <span className="font-medium text-slate-700">{r.competency_name}</span>
                <span className="text-12 font-bold text-emerald-600">{r.level_label} · {Math.round(r.score)}%</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {data.ai_insight && (
        <div className="rounded-2xl border border-[#0B3060]/10 bg-gradient-to-br from-[#0B3060]/5 to-[#154399]/8 p-4 space-y-2">
          <h3 className="text-13 font-bold text-[#0B3060] flex items-center gap-2">
            <Sparkles size={14} />
            AI Insight
          </h3>
          <p className="text-13 text-slate-600 leading-relaxed italic">"{data.ai_insight}"</p>
        </div>
      )}

      <div className="space-y-2 pt-1">
        <button
          id="view-recommendations-btn"
          onClick={() => window.location.assign('/recommendations')}
          className="w-full flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-[#0B3060] to-[#154399] py-4 text-15 font-bold text-white shadow-lg hover:opacity-90 active:scale-[0.98] transition-all"
        >
          <BookOpen size={18} />
          View Personalised Learning Path
          <ArrowRight size={16} />
        </button>
        <button
          id="go-dashboard-btn"
          onClick={() => window.location.assign('/')}
          className="w-full flex items-center justify-center gap-2 rounded-2xl border border-slate-200 bg-white py-3 text-14 font-semibold text-slate-600 hover:bg-slate-50 transition-colors"
        >
          <LayoutDashboard size={16} />
          Go to Dashboard
        </button>
      </div>
    </div>
  )
}

// ── Main page ──────────────────────────────────────────────────────────────────

type Phase = 'intro' | 'quiz' | 'processing' | 'results' | 'terminated'

export default function InitialAssessment() {
  const { user } = useAuth()
  const [phase, setPhase] = useState<Phase>('intro')
  const [assessments, setAssessments] = useState<StartedAssessmentRef[]>([])
  const [quizIndex, setQuizIndex] = useState(0)
  const [submittedIds, setSubmittedIds] = useState<string[]>([])
  const [results, setResults] = useState<InitialCompleteResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  
  // Proctoring state
  const [warnings, setWarnings] = useState(0)
  const [showWarning, setShowWarning] = useState(false)
  const [screenStream, setScreenStream] = useState<MediaStream | null>(null)

  const startMutation = useStartInitialAssessment()
  const completeMutation = useCompleteInitialAssessment()
  const terminateMutation = useTerminateInitialAssessment()

  useEffect(() => {
    if (user?.profile.initial_assessment_completed) {
      window.location.assign('/')
    }
  }, [user])

  // Proctoring effect
  useEffect(() => {
    if (phase !== 'quiz') return

    const handleViolation = () => {
      setWarnings(w => {
        const newW = w + 1
        if (newW >= 3) {
          terminateMutation.mutateAsync().catch(console.error)
          setPhase('terminated')
          if (document.fullscreenElement) {
             document.exitFullscreen().catch(() => {})
          }
        } else {
          setShowWarning(true)
        }
        return newW
      })
    }

    const handleVisibilityChange = () => {
      if (document.visibilityState === 'hidden') {
        handleViolation()
      }
    }

    const handleFullscreenChange = () => {
      if (!document.fullscreenElement && !showWarning) {
        handleViolation()
      }
    }

    const handleBlur = () => {
      if (!showWarning) {
        handleViolation()
      }
    }

    const handleStreamEnded = () => {
      if (!showWarning) {
        handleViolation()
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    document.addEventListener('fullscreenchange', handleFullscreenChange)
    window.addEventListener('blur', handleBlur)

    if (screenStream) {
      const track = screenStream.getVideoTracks()[0]
      if (track) track.addEventListener('ended', handleStreamEnded)
    }

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
      document.removeEventListener('fullscreenchange', handleFullscreenChange)
      window.removeEventListener('blur', handleBlur)
      if (screenStream) {
        const track = screenStream.getVideoTracks()[0]
        if (track) track.removeEventListener('ended', handleStreamEnded)
      }
    }
  }, [phase, showWarning, screenStream])

  // Stop screen stream when phase changes to processing or terminated
  useEffect(() => {
    if (phase === 'processing' || phase === 'terminated' || phase === 'results') {
       if (screenStream) {
          screenStream.getTracks().forEach(t => t.stop())
       }
    }
  }, [phase, screenStream])

  async function handleStart() {
    setError(null)
    
    let stream: MediaStream | null = null
    try {
      // Request screen sharing
      stream = await navigator.mediaDevices.getDisplayMedia({ video: true })
    } catch (e) {
      setError('You must share your screen to take this proctored assessment.')
      return
    }

    try {
      await document.documentElement.requestFullscreen()
    } catch (e) {
      setError('Please allow full-screen mode to start the proctored assessment.')
      stream.getTracks().forEach(t => t.stop())
      return
    }

    try {
      const data = await startMutation.mutateAsync()
      setAssessments(data.assessments)
      setScreenStream(stream)
      setPhase('quiz')
    } catch {
      setError('Failed to start the assessment. Please refresh and try again.')
      stream.getTracks().forEach(t => t.stop())
    }
  }

  async function handleQuizDone(assessmentId: string) {
    const newSubmitted = [...submittedIds, assessmentId]
    setSubmittedIds(newSubmitted)
    const nextIdx = quizIndex + 1
    if (nextIdx < assessments.length) {
      setQuizIndex(nextIdx)
    } else {
      if (document.fullscreenElement) {
         document.exitFullscreen().catch(() => {})
      }
      setPhase('processing')
      try {
        const completeData = await completeMutation.mutateAsync(newSubmitted)
        setResults(completeData)
        setPhase('results')
      } catch {
        setError('Assessment scored, but summary could not be generated. Your results are saved.')
        setPhase('results')
      }
    }
  }

  const totalQuestions = assessments.reduce((s, a) => s + a.question_count, 0)

  function acknowledgeWarning() {
    setShowWarning(false)
    document.documentElement.requestFullscreen().catch(() => {})
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#F0F4FF] via-[#F8FAFC] to-white flex flex-col">
      <div className="tricolor-strip" />

      <header className="bg-white border-b border-slate-200 shadow-sm sticky top-0 z-10">
        <div className="mx-auto flex max-w-2xl items-center gap-3 px-4 py-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-[#0B3060] to-[#154399]">
            <ClipboardList size={18} className="text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-14 font-bold text-[#0B3060] truncate">Skill Intelligence Platform</p>
            <p className="text-11 text-slate-400">Initial Competency Assessment · MoSPI</p>
          </div>
          {phase === 'quiz' && (
            <div className="text-right">
              <p className="text-12 font-bold text-[#0B3060]">{quizIndex + 1}/{assessments.length}</p>
              <p className="text-11 text-slate-400">competencies</p>
            </div>
          )}
        </div>
      </header>

      <main className="mx-auto w-full max-w-2xl flex-1 px-4 py-6 sm:px-6">
        {error && (
          <div className="mb-4 flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4">
            <XCircle size={16} className="text-red-500 mt-0.5 shrink-0" />
            <p className="text-13 text-red-700">{error}</p>
          </div>
        )}

        {phase === 'intro' && <IntroScreen onStart={() => void handleStart()} loading={startMutation.isPending} />}

        {phase === 'quiz' && assessments[quizIndex] && (
          <QuizScreen
            ref_={assessments[quizIndex]}
            totalQuestions={totalQuestions}
            assessmentIndex={quizIndex}
            totalAssessments={assessments.length}
            onDone={(id) => void handleQuizDone(id)}
          />
        )}

        {showWarning && phase === 'quiz' && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/80 p-4">
            <div className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-xl text-center space-y-4">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-red-100">
                <AlertTriangle size={32} className="text-red-600" />
              </div>
              <div>
                <h3 className="text-18 font-black text-slate-900">Security Warning</h3>
                <p className="text-14 text-slate-500 mt-2">
                  You have switched tabs, lost window focus, exited full-screen, or stopped screen sharing. This is a proctored assessment.
                </p>
                <p className="text-14 font-bold text-red-600 mt-2">
                  Warning {warnings} of 3
                </p>
              </div>
              <button
                onClick={acknowledgeWarning}
                className="w-full rounded-xl bg-red-600 py-3 text-14 font-bold text-white hover:bg-red-700 transition-colors"
              >
                Acknowledge & Return
              </button>
            </div>
          </div>
        )}

        {phase === 'processing' && <ProcessingScreen />}

        {phase === 'results' && results && <ResultsScreen data={results} />}

        {phase === 'results' && !results && (
          <div className="text-center space-y-4 py-12">
            <CheckCircle2 size={48} className="text-emerald-500 mx-auto" />
            <h2 className="text-20 font-black text-slate-900">Assessment Complete!</h2>
            <p className="text-14 text-slate-500">Your scores have been saved.</p>
            <button onClick={() => window.location.assign('/recommendations')} className="w-full rounded-2xl bg-[#0B3060] py-3.5 text-14 font-bold text-white">
              View Recommendations
            </button>
          </div>
        )}

        {phase === 'terminated' && (
          <div className="text-center space-y-4 py-12">
            <XCircle size={48} className="text-red-500 mx-auto" />
            <h2 className="text-20 font-black text-slate-900">Assessment Terminated</h2>
            <p className="text-14 text-slate-500 mt-2">
              Your assessment was terminated because you exceeded the maximum allowed security warnings (tab switches, focus loss, or leaving full-screen).
            </p>
            <p className="text-14 font-bold text-red-600 mt-4">
              Your account has been blocked for 5 hours.
            </p>
            <button
              onClick={() => window.location.assign('/')}
              className="mt-4 rounded-xl bg-slate-200 px-6 py-2.5 text-14 font-semibold text-slate-700 hover:bg-slate-300 transition-colors"
            >
              Back to Dashboard
            </button>
          </div>
        )}
      </main>

      <footer className="py-4 text-center text-11 text-slate-400">
        MoSPI · FRAC Competency Assessment · SIH 2026
      </footer>
    </div>
  )
}
