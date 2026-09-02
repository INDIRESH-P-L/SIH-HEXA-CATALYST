import { Link } from 'react-router-dom'
import { ArrowRight, Target } from 'lucide-react'

import { CompetencyRadar, ProgressLine } from '../components/charts'
import {
  Card,
  DataTable,
  EmptyState,
  GapBadge,
  LevelBar,
  PageHeader,
  Skeleton,
  StatTile,
  type Column,
} from '../components/common'
import { useGaps, useMyAnalytics } from '../hooks'
import { useAuth } from '../lib/auth'
import type { Gap } from '../lib/types'

export default function Dashboard() {
  const { user } = useAuth()
  const gaps = useGaps()
  const analytics = useMyAnalytics()

  const topGaps = gaps.data?.summary.top_gaps ?? []

  const columns: Column<Gap>[] = [
    {
      key: 'competency',
      header: 'Competency',
      render: (row) => (
        <div>
          <span className="text-ink">{row.competency_name}</span>
          <span className="ml-2 font-mono text-11 text-ink-3">{row.competency_code}</span>
        </div>
      ),
    },
    {
      key: 'level',
      header: 'Level',
      render: (row) => <LevelBar current={row.current_level} required={row.required_level} />,
      width: '190px',
    },
    {
      key: 'gap',
      header: 'Gap',
      numeric: true,
      render: (row) => <span className="numeral">{row.gap}</span>,
      width: '70px',
    },
    {
      key: 'band',
      header: 'Band',
      render: (row) => <GapBadge band={row.band} />,
      width: '110px',
    },
  ]

  return (
    <>
      <PageHeader
        title={`Good day, ${user?.profile.full_name.split(' ')[0] ?? 'Officer'}`}
        description={
          user?.profile.job_role
            ? `${user.profile.job_role.title} · ${user.profile.department ?? 'MoSPI'}`
            : undefined
        }
      />

      {/* Stat tiles */}
      <div className="mb-4 grid grid-cols-2 gap-4 lg:grid-cols-5">
        {analytics.isLoading &&
          Array.from({ length: 5 }).map((_, index) => (
            <div key={index} className="rounded border border-rule bg-surface p-4">
              <Skeleton className="mb-3 h-3 w-24" />
              <Skeleton className="h-8 w-16" />
            </div>
          ))}
        {analytics.data?.tiles.map((tile) => (
          <StatTile key={tile.label} label={tile.label} value={tile.value} unit={tile.unit} />
        ))}
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
        <Card className="lg:col-span-6" label="Competency profile">
          {analytics.isLoading && <Skeleton className="h-72 w-full" />}
          {analytics.data && analytics.data.radar.length > 0 ? (
            <CompetencyRadar data={analytics.data.radar} />
          ) : (
            !analytics.isLoading && (
              <EmptyState
                icon={Target}
                title="No competency requirements are defined for your job role yet."
              />
            )
          )}
        </Card>

        <Card className="lg:col-span-6" label="Average competency level over time">
          {analytics.isLoading && <Skeleton className="h-52 w-full" />}
          {analytics.data && analytics.data.progress.length > 0 ? (
            <ProgressLine data={analytics.data.progress} />
          ) : (
            !analytics.isLoading && (
              <EmptyState
                icon={Target}
                title="Your progress line appears once you have recorded evidence for a competency."
              />
            )
          )}
        </Card>

        <Card
          className="lg:col-span-12"
          label="Priority skill gaps"
          action={
            <Link
              to="/competencies"
              className="inline-flex items-center gap-1 text-13 text-accent hover:underline"
            >
              All competencies
              <ArrowRight size={14} strokeWidth={1.5} aria-hidden />
            </Link>
          }
        >
          {gaps.isLoading && <Skeleton className="h-32 w-full" />}
          {gaps.data && (
            <>
              <DataTable
                columns={columns}
                rows={topGaps}
                keyOf={(row) => row.competency_id}
                caption="Your three highest-priority skill gaps"
                empty={
                  <EmptyState
                    icon={Target}
                    title="No open gaps against your role requirements. Every competency is met."
                  />
                }
              />
              <p className="mt-3 max-w-prose text-12 leading-relaxed text-ink-3">
                Gap analysis is deterministic: priority = (expected − current) × criticality ×
                (2 − confidence) × horizon, on the FRAC four-point scale. The confidence term is
                why an unmeasured competency ranks urgently. No model is involved in any of these
                numbers.
              </p>
            </>
          )}
        </Card>
      </div>
    </>
  )
}
