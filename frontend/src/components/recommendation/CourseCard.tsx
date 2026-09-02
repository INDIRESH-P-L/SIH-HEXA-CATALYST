/**
 * A ranked recommendation.
 *
 * One row: rank numeral, title with provider and meta chips, score right
 * aligned. The explanation sits in an inset marked with its source. The score
 * breakdown and the exact context sent to the model are both openable, because
 * the interesting claim is not that a model wrote a sentence — it is that the
 * ranking is arithmetic anyone can check.
 */
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Clock, Layers, MonitorPlay } from 'lucide-react'

import { Badge, Button, GapBadge } from '../common'
import { AIBadge } from '../common/AIBadge'
import { FORMAT_LABEL, formatScore } from '../../lib/format'
import type { Recommendation } from '../../lib/types'
import { AIContextPanel } from './AIContextPanel'
import { ScoreBreakdownTable } from './ScoreBreakdown'

export function CourseCard({ item }: { item: Recommendation }) {
  const [showBreakdown, setShowBreakdown] = useState(false)
  const { course } = item

  return (
    <article className="rounded border border-rule bg-surface p-5">
      <div className="flex gap-4">
        <span className="font-mono text-24 leading-none text-ink-3 tabular" aria-label={`Rank ${item.rank}`}>
          {item.rank}
        </span>

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="min-w-0">
              <h3 className="text-16 font-semibold text-ink">
                <Link to={`/courses/${course.id}`} className="hover:text-accent hover:underline">
                  {course.title}
                </Link>
              </h3>
              <p className="mt-0.5 text-13 text-ink-2">{course.provider}</p>
            </div>
            <div className="text-right">
              <p className="eyebrow">Score</p>
              <p className="font-mono text-16 font-medium tabular text-ink">
                {formatScore(item.score)}
              </p>
            </div>
          </div>

          <div className="mt-3 flex flex-wrap items-center gap-2">
            <Badge tone={course.source === 'IGOT' ? 'accent' : 'neutral'}>{course.source}</Badge>
            <span className="inline-flex items-center gap-1 text-12 text-ink-2">
              <Clock size={14} strokeWidth={1.5} aria-hidden />
              {course.duration_hours} h
            </span>
            <span className="inline-flex items-center gap-1 text-12 text-ink-2">
              <Layers size={14} strokeWidth={1.5} aria-hidden />
              Level {course.proficiency_level}
            </span>
            <span className="inline-flex items-center gap-1 text-12 text-ink-2">
              <MonitorPlay size={14} strokeWidth={1.5} aria-hidden />
              {FORMAT_LABEL[course.learning_format] ?? course.learning_format}
            </span>
            {item.competency_code && (
              <span className="inline-flex items-center gap-1.5 text-12 text-ink-2">
                <span className="font-mono text-11 text-ink-3">
                  {item.competency_code} {item.current_level}/{item.required_level}
                </span>
                {item.gap_band && <GapBadge band={item.gap_band} />}
              </span>
            )}
          </div>

          {item.explanation && (
            <div className="mt-4 border-l-[3px] border-accent bg-surface-2 py-2 pl-3 pr-2">
              <AIBadge source={item.explanation_source} />
              <p className="mt-1 max-w-prose text-14 leading-relaxed text-ink">
                {item.explanation}
              </p>
            </div>
          )}

          <div className="mt-4 flex flex-wrap items-center gap-2">
            <Button
              variant="ghost"
              onClick={() => setShowBreakdown((open) => !open)}
              aria-expanded={showBreakdown}
            >
              {showBreakdown ? 'Hide score breakdown' : 'Show score breakdown'}
            </Button>
            <Link
              to={`/courses/${course.id}`}
              className="inline-flex h-control min-w-[7rem] items-center justify-center rounded border border-rule bg-surface px-4 text-14 font-medium text-ink hover:bg-surface-2"
            >
              Open course
            </Link>
          </div>

          {showBreakdown && (
            <div className="mt-4 space-y-4 animate-fade-in">
              <ScoreBreakdownTable breakdown={item.breakdown} />
              <AIContextPanel recommendationId={item.id} />
            </div>
          )}
        </div>
      </div>
    </article>
  )
}
