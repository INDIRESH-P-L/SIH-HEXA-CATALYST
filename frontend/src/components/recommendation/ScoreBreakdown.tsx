/**
 * Every term of the ranking formula, with its weight and contribution, plus
 * how the candidate was retrieved and where it lands on the calendar.
 *
 * The point of showing this is that the ordering is arithmetic, not a model
 * judgement. Anyone can add the column up.
 */
import { CalendarDays, Search } from 'lucide-react'

import { RANK_TERM_LABELS, RANK_TERM_NOTES, formatDate } from '../../lib/format'
import type { ScoreBreakdown } from '../../lib/types'

export function ScoreBreakdownTable({ breakdown }: { breakdown: ScoreBreakdown }) {
  const terms = Object.keys(RANK_TERM_LABELS)
  const values = breakdown as unknown as Record<string, number>
  const sequence = breakdown.sequence

  return (
    <div className="space-y-3">
      <div className="rounded border border-rule bg-surface-2 p-3">
        <p className="eyebrow mb-2">Stage 2 · ranking — deterministic</p>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-13">
            <thead>
              <tr className="border-b border-rule">
                <th
                  scope="col"
                  className="py-1.5 pr-3 text-left font-mono text-11 uppercase tracking-[0.06em] text-ink-2"
                >
                  Term
                </th>
                <th
                  scope="col"
                  className="py-1.5 px-2 text-right font-mono text-11 uppercase tracking-[0.06em] text-ink-2"
                >
                  Value
                </th>
                <th
                  scope="col"
                  className="py-1.5 px-2 text-right font-mono text-11 uppercase tracking-[0.06em] text-ink-2"
                >
                  Weight
                </th>
                <th
                  scope="col"
                  className="py-1.5 pl-2 text-right font-mono text-11 uppercase tracking-[0.06em] text-ink-2"
                >
                  Contribution
                </th>
              </tr>
            </thead>
            <tbody>
              {terms.map((term) => {
                const value = values[term] ?? 0
                const weight = breakdown.weights[term] ?? 0
                return (
                  <tr key={term} className="border-b border-rule-2">
                    <td className="py-1.5 pr-3">
                      <span className="text-ink">{RANK_TERM_LABELS[term]}</span>
                      <span className="ml-2 hidden text-12 text-ink-3 xl:inline">
                        {RANK_TERM_NOTES[term]}
                      </span>
                    </td>
                    <td className="py-1.5 px-2 text-right font-mono tabular text-ink">
                      {value.toFixed(3)}
                    </td>
                    <td className="py-1.5 px-2 text-right font-mono tabular text-ink-3">
                      {weight.toFixed(2)}
                    </td>
                    <td className="py-1.5 pl-2 text-right font-mono tabular text-ink">
                      {(value * weight).toFixed(4)}
                    </td>
                  </tr>
                )
              })}
              <tr>
                <td className="py-2 pr-3 font-medium text-ink" colSpan={3}>
                  Final score
                </td>
                <td className="py-2 pl-2 text-right font-mono font-medium tabular text-ink">
                  {breakdown.final_score.toFixed(4)}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {breakdown.retrievers && (
        <div className="rounded border border-rule bg-surface-2 p-3">
          <p className="eyebrow mb-2">Stage 1 · retrieval</p>
          <p className="flex flex-wrap items-center gap-2 text-12 text-ink-2">
            <Search size={14} strokeWidth={1.5} className="text-ink-3" aria-hidden />
            {breakdown.retrievers.map((r) => (
              <span key={r} className="rounded border border-rule bg-surface px-2 py-0.5 font-mono text-11">
                {r}
              </span>
            ))}
            <span className="text-ink-3">
              combined by {breakdown.fusion ?? 'reciprocal rank fusion'}
            </span>
          </p>
          <p className="mt-2 max-w-prose text-12 leading-relaxed text-ink-3">
            Three retrievers, because a dense model smooths away exact terms like SDMX or GROUP BY
            and a text index cannot see meaning. Fusion needs only their ordering, not scores that
            can be compared.
            {breakdown.fusion_score != null && (
              <span className="ml-1 font-mono">
                fused {breakdown.fusion_score.toFixed(3)}
              </span>
            )}
          </p>
        </div>
      )}

      {sequence && (
        <div className="rounded border border-rule bg-surface-2 p-3">
          <p className="eyebrow mb-2">Stage 3 · sequencing</p>
          <p className="flex flex-wrap items-center gap-2 text-12 text-ink-2">
            <CalendarDays size={14} strokeWidth={1.5} className="text-ink-3" aria-hidden />
            Step {sequence.order} · {formatDate(sequence.starts_on)} –{' '}
            {formatDate(sequence.ends_on)} · about {sequence.months_required} month
            {sequence.months_required === 1 ? '' : 's'} at your study budget
            {sequence.anchored && (
              <span className="rounded border border-accent-line bg-accent-wash px-2 py-0.5 font-mono text-11 text-accent">
                dated session
              </span>
            )}
          </p>
          <p className="mt-2 max-w-prose text-12 leading-relaxed text-ink-3">
            {sequence.anchored
              ? 'The academy fixes when this runs; self-paced study flows around it.'
              : 'Placed after its prerequisites, against a realistic monthly hour budget.'}
          </p>
        </div>
      )}
    </div>
  )
}
