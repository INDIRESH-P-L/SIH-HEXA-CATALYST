import { useState } from 'react'
import { GraduationCap, Play } from 'lucide-react'

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
import { useAssessmentHistory, useCreateAssessment, useGaps } from '../hooks'
import { errorMessage } from '../lib/api'
import { formatDate } from '../lib/format'
import type { Assessment, AssessmentHistoryItem, SubmitResponse } from '../lib/types'

export default function Assessments() {
  const gaps = useGaps()
  const history = useAssessmentHistory()
  const create = useCreateAssessment()

  const [active, setActive] = useState<Assessment | null>(null)
  const [result, setResult] = useState<SubmitResponse | null>(null)
  const [competencyId, setCompetencyId] = useState('')
  const [count, setCount] = useState(10)

  const openGaps = (gaps.data?.gaps ?? []).filter((gap) => gap.gap > 0)
  const selected = competencyId || openGaps[0]?.competency_id || ''

  async function start() {
    setResult(null)
    const assessment = await create.mutateAsync({ competencyId: selected, count })
    setActive(assessment)
  }

  function reset() {
    setActive(null)
    setResult(null)
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

  // ── Quiz view ──────────────────────────────────────────────────────────────
  if (active) {
    return (
      <>
        <PageHeader
          title={active.competency_name ?? 'Assessment'}
          description={`${active.total_questions} questions. Your answers are saved as you go.`}
          action={
            <Button variant="ghost" onClick={reset}>
              Abandon
            </Button>
          }
        />
        <QuizPlayer assessment={active} onComplete={setResult} />
      </>
    )
  }

  // ── Start view ─────────────────────────────────────────────────────────────
  return (
    <>
      <PageHeader
        title="Assessments"
        description="Take a competency assessment. Scoring is arithmetic; the level update follows fixed rules and never decreases."
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

              {create.isError && <ErrorNote>{errorMessage(create.error)}</ErrorNote>}

              <Button variant="primary" icon={Play} loading={create.isPending} onClick={start}>
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
    </>
  )
}
