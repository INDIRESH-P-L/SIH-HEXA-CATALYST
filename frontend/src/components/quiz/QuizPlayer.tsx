/**
 * One question per screen, a 3px accent progress bar at the top, full-width
 * option rows. Next stays disabled until an option is chosen.
 */
import { useState } from 'react'
import { ArrowLeft, ArrowRight, CheckCircle2 } from 'lucide-react'

import { Badge, Button, ErrorNote } from '../common'
import { errorMessage } from '../../lib/api'
import { useAnswer, useSubmitAssessment } from '../../hooks'
import type { Assessment, SubmitResponse } from '../../lib/types'

const OPTION_LETTERS = ['A', 'B', 'C', 'D'] as const

export function QuizPlayer({
  assessment,
  onComplete,
}: {
  assessment: Assessment
  onComplete: (result: SubmitResponse) => void
}) {
  const [index, setIndex] = useState(0)
  const [selections, setSelections] = useState<Record<string, number>>(() =>
    Object.fromEntries(
      assessment.questions
        .filter((q) => q.selected_index !== null)
        .map((q) => [q.id, q.selected_index as number]),
    ),
  )

  const answer = useAnswer()
  const submit = useSubmitAssessment()

  const question = assessment.questions[index]
  const total = assessment.questions.length
  const answeredCount = Object.keys(selections).length
  const isLast = index === total - 1
  const allAnswered = answeredCount === total

  if (!question) return null

  const selected = selections[question.id]

  function choose(optionIndex: number) {
    if (!question) return
    setSelections((current) => ({ ...current, [question.id]: optionIndex }))
    answer.mutate({
      assessmentId: assessment.id,
      questionId: question.id,
      selectedIndex: optionIndex,
    })
  }

  async function handleSubmit() {
    const result = await submit.mutateAsync(assessment.id)
    onComplete(result)
  }

  return (
    <div className="rounded border border-rule bg-surface">
      {/* Progress */}
      <div className="h-[3px] w-full bg-rule-2" role="progressbar" aria-valuenow={index + 1} aria-valuemin={1} aria-valuemax={total}>
        <div
          className="h-full bg-accent transition-[width] duration-200 ease-out"
          style={{ width: `${((index + 1) / total) * 100}%` }}
        />
      </div>

      <div className="p-5 lg:p-6">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <span className="eyebrow">
            Question {index + 1} of {total}
          </span>
          <div className="flex items-center gap-2">
            <Badge>{question.difficulty}</Badge>
            {question.topic && <Badge tone="neutral">{question.topic}</Badge>}
            {question.source_page && (
              <span className="font-mono text-11 text-ink-3">page {question.source_page}</span>
            )}
          </div>
        </div>

        <h2 className="max-w-prose text-16 font-semibold leading-relaxed text-ink">
          {question.question_text}
        </h2>

        <fieldset className="mt-5">
          <legend className="sr-only">Select one answer</legend>
          <div className="space-y-2">
            {question.options.map((option, optionIndex) => {
              const isSelected = selected === optionIndex
              return (
                <label
                  key={optionIndex}
                  className={`flex min-h-[44px] cursor-pointer items-start gap-3 rounded border p-3 transition-colors ${
                    isSelected
                      ? 'border-accent bg-accent-wash'
                      : 'border-rule bg-surface hover:bg-surface-2'
                  }`}
                >
                  <input
                    type="radio"
                    name={`question-${question.id}`}
                    className="sr-only"
                    checked={isSelected}
                    onChange={() => choose(optionIndex)}
                  />
                  <span
                    aria-hidden
                    className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border ${
                      isSelected ? 'border-accent bg-accent' : 'border-rule bg-surface'
                    }`}
                  >
                    {isSelected && <span className="h-2 w-2 rounded-full bg-surface" />}
                  </span>
                  <span className="flex-1 text-14 leading-relaxed text-ink">
                    <span className="mr-2 font-mono text-12 text-ink-3">
                      {OPTION_LETTERS[optionIndex]}
                    </span>
                    {option}
                  </span>
                </label>
              )
            })}
          </div>
        </fieldset>

        {submit.isError && <ErrorNote>{errorMessage(submit.error)}</ErrorNote>}

        <div className="mt-6 flex items-center justify-between gap-3 border-t border-rule-2 pt-4">
          <Button
            variant="ghost"
            icon={ArrowLeft}
            disabled={index === 0}
            onClick={() => setIndex((i) => Math.max(0, i - 1))}
          >
            Previous
          </Button>

          <span className="font-mono text-11 text-ink-3">
            {answeredCount} of {total} answered
          </span>

          {isLast ? (
            <Button
              variant="primary"
              icon={CheckCircle2}
              disabled={!allAnswered}
              loading={submit.isPending}
              onClick={handleSubmit}
            >
              Submit
            </Button>
          ) : (
            <Button
              variant="primary"
              icon={ArrowRight}
              disabled={selected === undefined}
              onClick={() => setIndex((i) => Math.min(total - 1, i + 1))}
            >
              Next
            </Button>
          )}
        </div>

        {isLast && !allAnswered && (
          <p className="mt-2 text-12 text-ink-3">
            Answer every question before submitting. Unanswered questions are marked incorrect.
          </p>
        )}
      </div>
    </div>
  )
}
