import { useState, type FormEvent } from 'react'
import { Check, FileText, Sparkles, Upload, X } from 'lucide-react'

import {
  Badge,
  Button,
  Card,
  DataTable,
  EmptyState,
  ErrorNote,
  Field,
  PageHeader,
  Skeleton,
  inputClass,
  type Column,
} from '../components/common'
import { ValidationReport } from '../components/trainer/ValidationReport'
import {
  useCompetencies,
  useGenerateQuestions,
  useMaterialQuestions,
  useMaterials,
  useReviewQuestion,
  useUploadMaterial,
} from '../hooks'
import { errorMessage } from '../lib/api'
import { formatDate } from '../lib/format'
import type { Material, Question } from '../lib/types'

const STATUS_TONE: Record<string, 'neutral' | 'accent' | 'met' | 'critical'> = {
  UPLOADED: 'neutral',
  EXTRACTED: 'neutral',
  CHUNKED: 'accent',
  GENERATED: 'met',
  FAILED: 'critical',
}

export default function TrainerConsole() {
  const materials = useMaterials()
  const competencies = useCompetencies()
  const upload = useUploadMaterial()
  const generate = useGenerateQuestions()
  const review = useReviewQuestion()

  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [file, setFile] = useState<File | null>(null)
  const [title, setTitle] = useState('')
  const [competencyId, setCompetencyId] = useState('')
  const [numQuestions, setNumQuestions] = useState(12)

  const questions = useMaterialQuestions(selectedId)
  const selected = materials.data?.find((m) => m.id === selectedId) ?? null

  async function handleUpload(event: FormEvent) {
    event.preventDefault()
    if (!file || !competencyId) return
    const created = await upload.mutateAsync({
      file,
      title: title.trim() || file.name.replace(/\.[^.]+$/, ''),
      competencyId,
    })
    setSelectedId(created.id)
    setFile(null)
    setTitle('')
  }

  const materialColumns: Column<Material>[] = [
    {
      key: 'title',
      header: 'Material',
      render: (row) => (
        <button
          type="button"
          onClick={() => setSelectedId(row.id)}
          className="text-left text-ink hover:text-accent hover:underline"
        >
          {row.title}
          <span className="ml-2 font-mono text-11 uppercase text-ink-3">{row.file_type}</span>
        </button>
      ),
    },
    {
      key: 'competency',
      header: 'Competency',
      render: (row) => (
        <span className="font-mono text-11 text-ink-2">{row.competency_code ?? '—'}</span>
      ),
      width: '110px',
    },
    {
      key: 'status',
      header: 'Status',
      render: (row) => <Badge tone={STATUS_TONE[row.status] ?? 'neutral'}>{row.status}</Badge>,
      width: '120px',
    },
    {
      key: 'pages',
      header: 'Pages',
      numeric: true,
      render: (row) => <span className="numeral text-ink-2">{row.page_count ?? '—'}</span>,
      width: '70px',
    },
    {
      key: 'chunks',
      header: 'Chunks',
      numeric: true,
      render: (row) => <span className="numeral text-ink-2">{row.chunk_count ?? 0}</span>,
      width: '75px',
    },
    {
      key: 'questions',
      header: 'Approved',
      numeric: true,
      render: (row) => (
        <span className="numeral">
          {row.approved_count ?? 0}
          <span className="text-ink-3"> / {row.question_count ?? 0}</span>
        </span>
      ),
      width: '95px',
    },
    {
      key: 'created',
      header: 'Uploaded',
      render: (row) => <span className="text-ink-2">{formatDate(row.created_at)}</span>,
      width: '120px',
    },
  ]

  return (
    <>
      <PageHeader
        title="Trainer console"
        description="Upload training material, generate assessment items from it, and review what the validation gate accepted."
      />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
        <Card className="lg:col-span-5" label="Upload material">
          <form onSubmit={handleUpload} className="space-y-4">
            <Field
              id="file"
              label="Document"
              hint="PDF, DOCX or PPTX, up to 10 MB. Scanned documents with no text layer are rejected with an explanation."
            >
              <input
                id="file"
                type="file"
                accept=".pdf,.docx,.pptx"
                required
                className="block w-full text-13 text-ink-2 file:mr-3 file:h-control file:rounded file:border file:border-rule file:bg-surface file:px-3 file:text-13 file:font-medium file:text-ink hover:file:bg-surface-2"
                onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              />
            </Field>

            <Field id="title" label="Title" hint="Defaults to the file name.">
              <input
                id="title"
                type="text"
                className={inputClass}
                value={title}
                onChange={(event) => setTitle(event.target.value)}
              />
            </Field>

            <Field id="competency" label="Target competency">
              <select
                id="competency"
                required
                className={inputClass}
                value={competencyId}
                onChange={(event) => setCompetencyId(event.target.value)}
              >
                <option value="">Select a competency…</option>
                {competencies.data?.map((competency) => (
                  <option key={competency.id} value={competency.id}>
                    {competency.name}
                  </option>
                ))}
              </select>
            </Field>

            {upload.isError && <ErrorNote>{errorMessage(upload.error)}</ErrorNote>}

            <Button
              type="submit"
              variant="primary"
              icon={Upload}
              loading={upload.isPending}
              disabled={!file || !competencyId}
            >
              Upload and extract
            </Button>
          </form>
        </Card>

        <Card className="lg:col-span-7" label="Materials">
          {materials.isLoading && <Skeleton className="h-32 w-full" />}
          {materials.data && (
            <DataTable
              columns={materialColumns}
              rows={materials.data}
              keyOf={(row) => row.id}
              caption="Materials you have uploaded"
              empty={
                <EmptyState
                  icon={FileText}
                  title="No material uploaded yet. Start with the sample SQL handout."
                />
              }
            />
          )}
        </Card>
      </div>

      {selected && (
        <div className="mt-4 space-y-4">
          {selected.error && (
            <Card>
              <ErrorNote>{selected.error}</ErrorNote>
            </Card>
          )}

          <Card
            label={`Generate questions — ${selected.title}`}
            action={
              <span className="font-mono text-11 text-ink-3">
                {selected.page_count ?? 0} pages · {selected.char_count?.toLocaleString() ?? 0}{' '}
                characters · {selected.chunk_count ?? 0} chunks
              </span>
            }
          >
            <div className="flex flex-wrap items-end gap-4">
              <div className="w-40">
                <Field id="num" label="Questions to attempt">
                  <input
                    id="num"
                    type="number"
                    min={1}
                    max={30}
                    className={inputClass}
                    value={numQuestions}
                    onChange={(event) => setNumQuestions(Number(event.target.value))}
                  />
                </Field>
              </div>
              <Button
                variant="primary"
                icon={Sparkles}
                loading={generate.isPending}
                disabled={selected.status === 'FAILED'}
                onClick={() =>
                  generate.mutate({ materialId: selected.id, numQuestions })
                }
              >
                Generate
              </Button>
              <p className="max-w-prose text-12 text-ink-3">
                Three items per chunk, one chunk per request, to stay inside the provider’s
                per-minute token ceiling.
              </p>
            </div>
            {generate.isError && <ErrorNote>{errorMessage(generate.error)}</ErrorNote>}
          </Card>

          {generate.data && <ValidationReport summary={generate.data} />}

          <Card label="Question bank">
            {questions.isLoading && <Skeleton className="h-32 w-full" />}
            {questions.data && questions.data.length === 0 && (
              <EmptyState
                icon={FileText}
                title="No questions generated from this material yet."
              />
            )}
            <ul className="space-y-3">
              {questions.data?.map((question) => (
                <QuestionRow
                  key={question.id}
                  question={question}
                  onReview={(status) => review.mutate({ id: question.id, status })}
                  busy={review.isPending}
                />
              ))}
            </ul>
          </Card>
        </div>
      )}
    </>
  )
}

function QuestionRow({
  question,
  onReview,
  busy,
}: {
  question: Question
  onReview: (status: 'APPROVED' | 'REJECTED') => void
  busy: boolean
}) {
  const tone =
    question.status === 'APPROVED'
      ? 'met'
      : question.status === 'REJECTED'
        ? 'critical'
        : 'neutral'

  return (
    <li className="rounded border border-rule p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <p className="max-w-prose flex-1 text-14 leading-relaxed text-ink">
          {question.question_text}
        </p>
        <div className="flex items-center gap-2">
          <Badge tone={tone}>{question.status}</Badge>
          <Badge>{question.difficulty}</Badge>
        </div>
      </div>

      <ol className="mt-3 space-y-1">
        {question.options.map((option, index) => (
          <li
            key={index}
            className={`flex items-start gap-2 rounded px-2 py-1 text-13 ${
              index === question.correct_index ? 'bg-met-bg text-ink' : 'text-ink-2'
            }`}
          >
            <span className="font-mono text-11 text-ink-3">
              {String.fromCharCode(65 + index)}
            </span>
            <span className="flex-1">{option}</span>
            {index === question.correct_index && (
              <Check size={14} strokeWidth={2} className="mt-0.5 text-met" aria-label="Correct answer" />
            )}
          </li>
        ))}
      </ol>

      <p className="mt-2 max-w-prose text-12 leading-relaxed text-ink-2">
        {question.explanation}
      </p>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        {question.topic && <Badge tone="neutral">{question.topic}</Badge>}
        {question.source_page && (
          <span className="font-mono text-11 text-ink-3">page {question.source_page}</span>
        )}
        {question.validation && (
          <span
            className={`font-mono text-11 ${question.validation.passed ? 'text-met' : 'text-critical'}`}
          >
            {question.validation.passed
              ? 'passed all 10 checks'
              : `failed: ${question.validation.failed_checks.join(', ')}`}
          </span>
        )}
      </div>

      {question.status !== 'APPROVED' && (
        <div className="mt-3 flex gap-2">
          <Button
            variant="secondary"
            icon={Check}
            loading={busy}
            onClick={() => onReview('APPROVED')}
          >
            Approve
          </Button>
          {question.status !== 'REJECTED' && (
            <Button variant="ghost" icon={X} loading={busy} onClick={() => onReview('REJECTED')}>
              Reject
            </Button>
          )}
        </div>
      )}
    </li>
  )
}
