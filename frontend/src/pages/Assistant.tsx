import { useState, type FormEvent } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { BookOpen, MessageSquare, Quote, ShieldAlert, Send } from 'lucide-react'

import {
  Badge,
  Button,
  Card,
  EmptyState,
  ErrorNote,
  PageHeader,
  Skeleton,
  inputClass,
} from '../components/common'
import { AIBadge } from '../components/common/AIBadge'
import { api, API, errorMessage } from '../lib/api'
import type { AssistantAnswer, CorpusStats } from '../lib/types'

const SUGGESTIONS = [
  'What is the difference between WHERE and HAVING?',
  'How does a LEFT JOIN change the denominator of a tabulation?',
  'Why does COUNT on a named column differ from COUNT(*)?',
]

export default function Assistant() {
  const [question, setQuestion] = useState('')
  const [asked, setAsked] = useState<string | null>(null)

  const corpus = useQuery({
    queryKey: ['assistant', 'corpus'],
    queryFn: async () => (await api.get<CorpusStats>(API.v1('/assistant/corpus'))).data,
  })

  const ask = useMutation({
    mutationFn: async (q: string) =>
      (await api.post<AssistantAnswer>(API.v1('/assistant/ask'), { question: q })).data,
  })

  function submit(event: FormEvent) {
    event.preventDefault()
    const q = question.trim()
    if (q.length < 3) return
    setAsked(q)
    ask.mutate(q)
  }

  function useSuggestion(value: string) {
    setQuestion(value)
    setAsked(value)
    ask.mutate(value)
  }

  const answer = ask.data

  return (
    <>
      <PageHeader
        title="Learning assistant"
        description="Answers drawn only from training material a trainer has approved, with citations — and a refusal when the corpus does not cover the question."
      />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
        <div className="space-y-4 lg:col-span-8">
          <Card>
            <form onSubmit={submit}>
              <label htmlFor="question" className="mb-1.5 block text-13 font-medium text-ink">
                Your question
              </label>
              <div className="flex gap-2">
                <input
                  id="question"
                  type="text"
                  className={inputClass}
                  placeholder=""
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                />
                <Button
                  type="submit"
                  variant="primary"
                  icon={Send}
                  loading={ask.isPending}
                  disabled={question.trim().length < 3}
                >
                  Ask
                </Button>
              </div>
              <p className="mt-1.5 text-12 text-ink-3">
                Methodology questions are what this is for — sampling design, national accounts,
                index construction — where a confident wrong answer is worse than none.
              </p>
            </form>

            {ask.isError && <ErrorNote>{errorMessage(ask.error)}</ErrorNote>}

            {!asked && !ask.isPending && (
              <div className="mt-4 border-t border-rule-2 pt-4">
                <p className="eyebrow mb-2">Try one of these</p>
                <div className="flex flex-wrap gap-2">
                  {SUGGESTIONS.map((s) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => useSuggestion(s)}
                      className="rounded border border-rule px-3 py-1.5 text-left text-13 text-ink-2 transition-colors hover:bg-surface-2 hover:text-ink"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </Card>

          {ask.isPending && (
            <Card>
              <Skeleton className="mb-2 h-4 w-1/3" />
              <Skeleton className="mb-2 h-4 w-full" />
              <Skeleton className="h-4 w-2/3" />
            </Card>
          )}

          {answer && !ask.isPending && (
            <Card>
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <p className="text-13 text-ink-2">
                  <MessageSquare size={14} strokeWidth={1.5} className="mr-1.5 inline" aria-hidden />
                  {asked}
                </p>
                <div className="flex items-center gap-2">
                  {answer.refused ? (
                    <Badge tone="emerging">Refused</Badge>
                  ) : (
                    <Badge tone="met">Grounded</Badge>
                  )}
                  <span className="font-mono text-11 text-ink-3">
                    retrieval {answer.retrieval_score.toFixed(2)} · {answer.latency_ms} ms
                  </span>
                </div>
              </div>

              {answer.refused ? (
                <div className="rounded border border-emerging/30 bg-emerging-bg p-3">
                  <p className="flex items-start gap-2 text-14 leading-relaxed text-ink">
                    <ShieldAlert
                      size={16}
                      strokeWidth={1.5}
                      className="mt-0.5 shrink-0 text-emerging"
                      aria-hidden
                    />
                    <span className="max-w-prose">{answer.answer}</span>
                  </p>
                  {answer.refusal_reason && (
                    <p className="mt-2 pl-6 font-mono text-11 text-ink-3">
                      {answer.refusal_reason}
                    </p>
                  )}
                  {answer.suggested_course && (
                    <Link
                      to={`/courses/${answer.suggested_course.course_id}`}
                      className="mt-3 inline-flex items-center gap-1.5 pl-6 text-13 text-accent hover:underline"
                    >
                      <BookOpen size={14} strokeWidth={1.5} aria-hidden />
                      Open {answer.suggested_course.title}
                    </Link>
                  )}
                </div>
              ) : (
                <>
                  <AIBadge source={answer.source === 'ai' ? 'ai' : 'template'} />
                  <p className="mt-2 max-w-prose whitespace-pre-line text-14 leading-relaxed text-ink">
                    {answer.answer}
                  </p>
                </>
              )}

              {answer.citations.length > 0 && (
                <div className="mt-5 border-t border-rule-2 pt-4">
                  <p className="eyebrow mb-2">
                    Sources — every claim traceable to approved material
                  </p>
                  <ol className="space-y-2">
                    {answer.citations.map((c, index) => (
                      <li
                        key={c.chunk_id}
                        className="rounded border border-rule bg-surface-2 p-3"
                      >
                        <div className="flex items-baseline justify-between gap-3">
                          <p className="text-13 font-medium text-ink">
                            <span className="mr-1.5 font-mono text-11 text-ink-3">
                              [{index + 1}]
                            </span>
                            {c.material_title}
                            {c.page_no ? (
                              <span className="ml-1.5 font-mono text-11 text-ink-3">
                                page {c.page_no}
                              </span>
                            ) : null}
                          </p>
                          <span className="font-mono text-11 text-ink-3">
                            {c.score.toFixed(3)}
                          </span>
                        </div>
                        <p className="mt-1.5 flex gap-2 text-12 leading-relaxed text-ink-2">
                          <Quote
                            size={12}
                            strokeWidth={1.5}
                            className="mt-1 shrink-0 text-ink-3"
                            aria-hidden
                          />
                          <span className="line-clamp-4">{c.excerpt.slice(0, 320)}…</span>
                        </p>
                      </li>
                    ))}
                  </ol>
                </div>
              )}

              <p className="mt-4 max-w-prose text-12 leading-relaxed text-ink-3">{answer.note}</p>
            </Card>
          )}
        </div>

        <div className="space-y-4 lg:col-span-4">
          <Card label="Approved corpus">
            {corpus.isLoading && <Skeleton className="h-20 w-full" />}
            {corpus.data && (
              <>
                {corpus.data.indexed_chunks === 0 ? (
                  <EmptyState
                    icon={BookOpen}
                    title="No material has been approved into the corpus yet. A trainer approves uploads before the assistant can answer from them."
                  />
                ) : (
                  <dl className="space-y-2 text-13">
                    <div className="flex justify-between">
                      <dt className="text-ink-2">Approved documents</dt>
                      <dd className="numeral">{corpus.data.approved_materials}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-ink-2">Indexed passages</dt>
                      <dd className="numeral">{corpus.data.indexed_chunks}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-ink-2">Grounding threshold</dt>
                      <dd className="numeral">{corpus.data.grounding_threshold.toFixed(2)}</dd>
                    </div>
                  </dl>
                )}
                {!corpus.data.enabled && (
                  <p className="mt-3 rounded border border-rule bg-surface-2 px-3 py-2 text-12 text-ink-2">
                    The assistant is disabled in this deployment. Set{' '}
                    <code className="font-mono text-11">ASSISTANT_ENABLED=true</code> to turn it
                    on.
                  </p>
                )}
              </>
            )}
          </Card>

          <Card label="How it answers">
            <ol className="space-y-2 text-12 leading-relaxed text-ink-2">
              <li>
                <span className="font-mono text-11 text-ink-3">1 </span>
                Hybrid retrieval — semantic and exact-term — over approved passages only.
              </li>
              <li>
                <span className="font-mono text-11 text-ink-3">2 </span>
                Reranking, then a grounding gate on retrieval confidence.
              </li>
              <li>
                <span className="font-mono text-11 text-ink-3">3 </span>
                Below the threshold it refuses and names the course that covers the topic.
              </li>
              <li>
                <span className="font-mono text-11 text-ink-3">4 </span>
                Above it, the model answers from the passages and every claim is cited.
              </li>
            </ol>
            <p className="mt-3 max-w-prose text-12 leading-relaxed text-ink-3">
              The refusal branch is a feature, not a failure mode. Its rate is a signal about the
              corpus, not about the model.
            </p>
          </Card>
        </div>
      </div>
    </>
  )
}
