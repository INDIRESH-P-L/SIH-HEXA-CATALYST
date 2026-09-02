/**
 * The result screen, and the one choreographed moment in the application:
 * the LevelBar fills to the measured level, then the GapBadge crossfades from
 * the old band to the new one.
 *
 * Every number here was computed by rule on the server, from stored responses.
 * Only the written feedback came from a language model, and it is labelled
 * with its source.
 */
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, RotateCcw, ShieldCheck } from 'lucide-react'

import { Badge, Button, Card, GapBadge, LevelBar } from '../common'
import { AIBadge } from '../common/AIBadge'
import type { SubmitResponse } from '../../lib/types'

/** The scoring arithmetic, laid out so it can be checked by hand. */
function ScoreArithmetic({ result }: { result: SubmitResponse }) {
  const b = result.breakdown
  const bands = Object.entries(b.per_difficulty)

  return (
    <div className="rounded border border-rule bg-surface-2 p-3">
      <p className="eyebrow mb-2">How this score was reached</p>
      <div className="overflow-x-auto">
        <table className="w-full text-12">
          <thead>
            <tr className="border-b border-rule">
              <th className="py-1 pr-3 text-left font-mono text-11 uppercase tracking-[0.06em] text-ink-2">
                Difficulty
              </th>
              <th className="py-1 px-2 text-right font-mono text-11 uppercase tracking-[0.06em] text-ink-2">
                Weight
              </th>
              <th className="py-1 px-2 text-right font-mono text-11 uppercase tracking-[0.06em] text-ink-2">
                Correct
              </th>
              <th className="py-1 px-2 text-right font-mono text-11 uppercase tracking-[0.06em] text-ink-2">
                Earned
              </th>
              <th className="py-1 pl-2 text-right font-mono text-11 uppercase tracking-[0.06em] text-ink-2">
                Available
              </th>
            </tr>
          </thead>
          <tbody>
            {bands.map(([difficulty, counts]) => {
              const weight = b.weights[difficulty] ?? 0
              return (
                <tr key={difficulty} className="border-b border-rule-2">
                  <td className="py-1 pr-3 text-ink">{difficulty}</td>
                  <td className="py-1 px-2 text-right font-mono tabular text-ink-3">×{weight}</td>
                  <td className="py-1 px-2 text-right font-mono tabular text-ink">
                    {counts.correct}/{counts.attempted}
                  </td>
                  <td className="py-1 px-2 text-right font-mono tabular text-ink">
                    {counts.correct * weight}
                  </td>
                  <td className="py-1 pl-2 text-right font-mono tabular text-ink-3">
                    {counts.attempted * weight}
                  </td>
                </tr>
              )
            })}
            <tr>
              <td className="pt-2 font-medium text-ink" colSpan={3}>
                Weighted total
              </td>
              <td className="pt-2 text-right font-mono font-medium tabular text-ink">
                {b.numerator}
              </td>
              <td className="pt-2 text-right font-mono font-medium tabular text-ink">
                {b.denominator}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p className="mt-2 font-mono text-11 text-ink-3">
        {b.numerator} / {b.denominator} = {result.score.toFixed(2)}% · unweighted the same paper
        reads {result.raw_score.toFixed(2)}%
      </p>
      <p className="mt-2 max-w-prose text-12 leading-relaxed text-ink-2">
        The weighting penalises failure on the items that discriminate. Only items you attempted
        enter the denominator.
      </p>
    </div>
  )
}

export function ResultScreen({
  result,
  onRetake,
}: {
  result: SubmitResponse
  onRetake?: () => void
}) {
  const [advanced, setAdvanced] = useState(false)
  const [showArithmetic, setShowArithmetic] = useState(false)

  useEffect(() => {
    if (!result.level_changed) {
      setAdvanced(true)
      return
    }
    const timer = window.setTimeout(() => setAdvanced(true), 600)
    return () => window.clearTimeout(timer)
  }, [result.level_changed])

  const shownLevel = advanced ? result.level_after : result.level_before
  const shownBand = advanced ? result.gap_after.band : result.gap_before.band
  const shownFrac = advanced ? result.frac_after : result.frac_before
  const requiredLevel = result.gap_before.gap + result.level_before

  return (
    <div className="space-y-4">
      <Card>
        <div className="flex flex-wrap items-end justify-between gap-6">
          <div>
            <p className="eyebrow mb-1">Weighted score</p>
            <p className="font-mono text-48 font-medium tabular leading-none text-ink">
              {result.score.toFixed(0)}
              <span className="text-24 text-ink-3">%</span>
            </p>
            <p className="mt-2 text-13 text-ink-2">
              {result.correct_count} of {result.attempted} attempted correct
              <span className="ml-2 font-mono text-11 text-ink-3">
                unweighted {result.raw_score.toFixed(0)}%
              </span>
            </p>
            <div className="mt-2 flex items-center gap-2">
              <Badge tone={result.mode === 'proctored' ? 'accent' : 'neutral'}>
                {result.mode}
              </Badge>
              <span className="font-mono text-11 text-ink-3">
                evidence confidence {result.confidence.toFixed(2)}
              </span>
            </div>
          </div>

          <div className="min-w-[240px]">
            <p className="eyebrow mb-2">
              {result.competency.code} · {result.competency.name}
            </p>
            <LevelBar
              current={shownLevel}
              required={requiredLevel}
              animate={advanced && result.level_changed}
            />
            <p className="mt-2 text-13 text-ink-2">{shownFrac}</p>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <span className="text-12 text-ink-3">Gap</span>
              <span key={shownBand} className="animate-fade-in">
                <GapBadge band={shownBand} />
              </span>
              {result.level_changed && advanced && (
                <span className="text-12 text-ink-2">
                  was <span className="font-mono">{result.gap_before.band}</span>
                </span>
              )}
            </div>
            <p className="mt-2 font-mono text-11 text-ink-3">
              priority {result.priority_before.toFixed(2)} → {result.priority_after.toFixed(2)}
            </p>
          </div>
        </div>

        {result.level_changed ? (
          <p className="mt-5 rounded border border-met/30 bg-met-bg px-3 py-2 text-13 text-met">
            Competency level moved from {result.level_before} to {result.level_after}. An evidence
            record has been appended to your ledger at confidence {result.confidence.toFixed(2)},
            replacing a self-declaration.
          </p>
        ) : (
          <p className="mt-5 rounded border border-rule bg-surface-2 px-3 py-2 text-13 text-ink-2">
            {result.revisit
              ? 'Your level is unchanged. Levels never decrease; this competency stays in your gap list so it will be targeted again.'
              : 'Your level is unchanged for this attempt, but the evidence behind it is now stronger.'}
          </p>
        )}

        <div className="mt-4">
          <Button variant="ghost" onClick={() => setShowArithmetic((open) => !open)}>
            {showArithmetic ? 'Hide the arithmetic' : 'Show the arithmetic'}
          </Button>
          {showArithmetic && (
            <div className="mt-3 animate-fade-in">
              <ScoreArithmetic result={result} />
            </div>
          )}
        </div>
      </Card>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card label="Feedback">
          <AIBadge source={result.feedback_source} />
          <p className="mt-2 max-w-prose text-14 leading-relaxed text-ink">{result.ai_feedback}</p>

          {result.weak_topics.length > 0 && (
            <div className="mt-4">
              <p className="eyebrow mb-2">Topics to revisit</p>
              <div className="flex flex-wrap gap-2">
                {result.weak_topics.map((topic) => (
                  <Badge key={topic} tone="significant">
                    {topic}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {result.strong_topics.length > 0 && (
            <div className="mt-3">
              <p className="eyebrow mb-2">Handled confidently</p>
              <div className="flex flex-wrap gap-2">
                {result.strong_topics.map((topic) => (
                  <Badge key={topic} tone="met">
                    {topic}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          <p className="mt-4 flex max-w-prose items-start gap-2 text-12 leading-relaxed text-ink-3">
            <ShieldCheck size={14} strokeWidth={1.5} className="mt-0.5 shrink-0" aria-hidden />
            <span>{result.scoring_note}</span>
          </p>
        </Card>

        <Card
          label="Next recommendation"
          action={
            <Link
              to="/recommendations"
              className="inline-flex items-center gap-1 text-13 text-accent hover:underline"
            >
              All recommendations
              <ArrowRight size={14} strokeWidth={1.5} aria-hidden />
            </Link>
          }
        >
          {result.new_recommendations.length === 0 ? (
            <p className="text-13 text-ink-2">No open gaps remain to recommend against.</p>
          ) : (
            <ul className="space-y-3">
              {result.new_recommendations.slice(0, 3).map((item) => (
                <li
                  key={item.course_id}
                  className="border-b border-rule-2 pb-3 last:border-0 last:pb-0"
                >
                  <div className="flex items-start gap-3">
                    <span className="font-mono text-16 tabular text-ink-3">{item.rank}</span>
                    <div className="min-w-0">
                      <Link
                        to={`/courses/${item.course_id}`}
                        className="text-14 font-medium text-ink hover:text-accent hover:underline"
                      >
                        {item.title}
                      </Link>
                      <p className="mt-0.5 text-12 text-ink-2">
                        {item.source} · level {item.proficiency_level} · {item.duration_hours} h
                      </p>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
          <p className="mt-4 max-w-prose text-12 leading-relaxed text-ink-3">
            This batch was regenerated against your updated level, in the same request that scored
            the assessment. The loop has closed.
          </p>
        </Card>
      </div>

      {onRetake && (
        <div className="flex justify-center">
          <Button variant="secondary" icon={RotateCcw} onClick={onRetake}>
            Take another assessment
          </Button>
        </div>
      )}
    </div>
  )
}
