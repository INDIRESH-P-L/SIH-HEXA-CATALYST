import { Activity, BarChart3, EyeOff, RefreshCw } from 'lucide-react'

import { GapDistribution, LevelDistribution, WorkforceHeatmap } from '../components/charts'
import {
  Badge,
  Button,
  Card,
  DataTable,
  EmptyState,
  GapBadge,
  PageHeader,
  Skeleton,
  StatTile,
  type Column,
} from '../components/common'
import { MockNotice } from '../components/common/MockNotice'
import {
  useAdminOverview,
  useCompetencyMatrix,
  useEventStream,
  useRebuildMarts,
  useTrainingEffectiveness,
  useBlockedAccounts,
  useUnblockUser,
} from '../hooks'
import { formatDateTime } from '../lib/format'
import type { CompetencyGapFrequency, TrainingEffectivenessRow } from '../lib/types'

export default function AdminDashboard() {
  const overview = useAdminOverview()
  const matrix = useCompetencyMatrix()
  const effectiveness = useTrainingEffectiveness()
  const events = useEventStream()
  const rebuild = useRebuildMarts()
  const blocked = useBlockedAccounts()
  const unblock = useUnblockUser()

  const gapColumns: Column<CompetencyGapFrequency>[] = [
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
      key: 'officers',
      header: 'With a gap',
      numeric: true,
      render: (row) =>
        row.suppressed ? (
          <span className="inline-flex items-center gap-1 text-12 text-ink-3">
            <EyeOff size={12} strokeWidth={1.5} aria-hidden />
            suppressed
          </span>
        ) : (
          <span className="numeral">
            {row.officers_with_gap}
            <span className="text-ink-3"> / {row.officers}</span>
          </span>
        ),
      width: '130px',
    },
    {
      key: 'avg_gap',
      header: 'Avg gap',
      numeric: true,
      render: (row) => (
        <span className="numeral">{row.suppressed ? '—' : row.average_gap.toFixed(2)}</span>
      ),
      width: '90px',
    },
    {
      key: 'avg_current',
      header: 'Avg level',
      numeric: true,
      render: (row) => (
        <span className="numeral text-ink-2">
          {row.suppressed
            ? '—'
            : `${row.average_current_level.toFixed(2)} / ${row.average_required_level.toFixed(1)}`}
        </span>
      ),
      width: '120px',
    },
    {
      key: 'band',
      header: 'Dominant band',
      render: (row) => <GapBadge band={row.dominant_band} />,
      width: '140px',
    },
  ]

  const effectivenessColumns: Column<TrainingEffectivenessRow>[] = [
    {
      key: 'course',
      header: 'Programme',
      render: (row) => (
        <div>
          <span className="text-ink">{row.course_title}</span>
          <span className="ml-2 font-mono text-11 text-ink-3">{row.competency_code}</span>
        </div>
      ),
    },
    {
      key: 'source',
      header: 'Source',
      render: (row) => <Badge>{row.source}</Badge>,
      width: '90px',
    },
    {
      key: 'completions',
      header: 'Completions',
      numeric: true,
      render: (row) => <span className="numeral">{row.completions}</span>,
      width: '110px',
    },
    {
      key: 'delta',
      header: 'Level change',
      numeric: true,
      render: (row) => (
        <span className="numeral">
          {row.average_level_before.toFixed(1)} <span className="text-ink-3">→</span>{' '}
          {row.average_level_after.toFixed(1)}
        </span>
      ),
      width: '130px',
    },
    {
      key: 'net',
      header: 'Net of comparison',
      numeric: true,
      render: (row) => (
        <span className="numeral">
          {row.net_delta != null ? (
            <>
              {row.net_delta > 0 ? '+' : ''}
              {row.net_delta.toFixed(2)}
            </>
          ) : (
            <span className="text-ink-3">—</span>
          )}
        </span>
      ),
      width: '150px',
    },
  ]

  return (
    <>
      <PageHeader
        title="Workforce analytics"
        description="Deterministic aggregates over the evidence ledger. Cells covering fewer than five officers are suppressed."
        action={
          <Button
            variant="secondary"
            icon={RefreshCw}
            loading={rebuild.isPending}
            onClick={() => rebuild.mutate()}
          >
            Rebuild marts
          </Button>
        }
      />

      <div className="mb-4 grid grid-cols-2 gap-4 lg:grid-cols-5">
        {overview.isLoading &&
          Array.from({ length: 5 }).map((_, index) => (
            <div key={index} className="rounded border border-rule bg-surface p-4">
              <Skeleton className="mb-3 h-3 w-24" />
              <Skeleton className="h-8 w-16" />
            </div>
          ))}
        {overview.data?.tiles.map((tile) => (
          <StatTile key={tile.label} label={tile.label} value={tile.value} unit={tile.unit} />
        ))}
      </div>

      {overview.data && (
        <Card className="mb-4">
          <p className="flex flex-wrap items-center gap-x-6 gap-y-2 text-13 text-ink-2">
            <span>
              <span className="numeral">{overview.data.unassessed_requirements}</span> requirements
              never measured
            </span>
            <span>
              <span className="numeral">{overview.data.stale_evidence_rows}</span> pieces of
              evidence past their decay window
            </span>
            <span>
              <span className="numeral">{overview.data.events_recorded}</span> events in the stream
            </span>
            <span className="font-mono text-11 text-ink-3">
              k-anonymity threshold {overview.data.k_anonymity_threshold}
            </span>
          </p>
        </Card>
      )}

      {/* Blocked Accounts Management */}
      <Card className="mb-4" label="User Access Management (Blocked Accounts)">
        {blocked.isLoading && <Skeleton className="h-24 w-full" />}
        {blocked.data && (
          <DataTable
            columns={[
              {
                key: 'user',
                header: 'User',
                render: (row) => (
                  <div>
                    <span className="text-ink font-semibold">{row.full_name}</span>
                    <span className="ml-2 font-mono text-11 text-ink-3">{row.email}</span>
                  </div>
                ),
              },
              {
                key: 'blocked_until',
                header: 'Blocked Until',
                render: (row) => (
                  <span className="font-mono text-12 text-red-600">
                    {formatDateTime(row.blocked_until)}
                  </span>
                ),
                width: '200px',
              },
              {
                key: 'action',
                header: 'Action',
                render: (row) => (
                  <Button
                    variant="secondary"
                    onClick={() => unblock.mutate(row.id)}
                    loading={unblock.isPending}
                    className="h-7 text-11"
                  >
                    Unblock Now
                  </Button>
                ),
                width: '120px',
              },
            ]}
            rows={blocked.data}
            keyOf={(row) => row.id}
            caption="Users currently locked out due to security violations during assessments."
            empty={<EmptyState icon={Activity} title="No users are currently blocked." />}
          />
        )}
      </Card>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
        <Card className="lg:col-span-7" label="Gap frequency by competency">
          {overview.isLoading && <Skeleton className="h-64 w-full" />}
          {overview.data && overview.data.gap_frequency.length > 0 ? (
            <GapDistribution data={overview.data.gap_frequency} />
          ) : (
            !overview.isLoading && (
              <EmptyState icon={BarChart3} title="No gap data across the workforce yet." />
            )
          )}
        </Card>

        <Card className="lg:col-span-5" label="Competency level distribution">
          {overview.isLoading && <Skeleton className="h-56 w-full" />}
          {overview.data && <LevelDistribution data={overview.data.level_distribution} />}
        </Card>

        <Card className="lg:col-span-12" label="Workforce heatmap — job role × competency">
          {matrix.isLoading && <Skeleton className="h-56 w-full" />}
          {matrix.data && matrix.data.cells.length > 0 ? (
            <>
              <WorkforceHeatmap cells={matrix.data.cells} />
              <p className="mt-3 max-w-prose text-12 leading-relaxed text-ink-3">
                Cells covering fewer than {matrix.data.k_anonymity_threshold} officers are
                suppressed rather than shown as a number that could identify an individual. No
                individual score appears in any workforce view.
              </p>
            </>
          ) : (
            !matrix.isLoading && (
              <EmptyState icon={BarChart3} title="No role requirement data to plot." />
            )
          )}
        </Card>

        <Card className="lg:col-span-12" label="Gap frequency detail">
          {overview.data && (
            <>
              <DataTable
                columns={gapColumns}
                rows={overview.data.gap_frequency}
                keyOf={(row) => row.competency_code}
                caption="How often each competency falls short across the workforce"
                empty={<EmptyState icon={BarChart3} title="No gaps recorded." />}
              />
              <p className="mt-3 max-w-prose text-12 leading-relaxed text-ink-3">
                {overview.data.note}
              </p>
            </>
          )}
        </Card>

        <Card
          className="lg:col-span-12"
          label="Training effectiveness — did it work, not did they attend"
        >
          {effectiveness.isLoading && <Skeleton className="h-24 w-full" />}
          {effectiveness.data && (
            <>
              <DataTable
                columns={effectivenessColumns}
                rows={effectiveness.data.rows}
                keyOf={(row) => row.course_id}
                caption="Average competency level either side of a recorded completion"
                empty={
                  <EmptyState
                    icon={BarChart3}
                    title="No completed enrolments yet, so no pre/post comparison is possible."
                  />
                }
              />
              <p className="mt-3 max-w-prose text-12 leading-relaxed text-ink-3">
                {effectiveness.data.note}
              </p>
            </>
          )}
        </Card>

        <Card className="lg:col-span-12" label="Event stream">
          {events.isLoading && <Skeleton className="h-24 w-full" />}
          {events.data && (
            <>
              <div className="mb-3 flex flex-wrap gap-1.5">
                {Object.entries(events.data.by_verb)
                  .sort((a, b) => b[1] - a[1])
                  .slice(0, 12)
                  .map(([verb, count]) => (
                    <span
                      key={verb}
                      className="inline-flex items-center gap-1.5 rounded border border-rule bg-surface-2 px-2 py-0.5 font-mono text-11 text-ink-2"
                    >
                      {verb}
                      <span className="tabular text-ink">{count}</span>
                    </span>
                  ))}
              </div>
              <ul className="space-y-1">
                {events.data.recent.slice(0, 10).map((event) => (
                  <li
                    key={event.id}
                    className="flex items-baseline justify-between gap-4 border-b border-rule-2 py-1.5 last:border-0"
                  >
                    <span className="flex items-center gap-2 text-13 text-ink">
                      <Activity size={12} strokeWidth={1.5} className="text-ink-3" aria-hidden />
                      <span className="font-mono text-12">{event.verb}</span>
                    </span>
                    <span className="font-mono text-11 text-ink-3">
                      {formatDateTime(event.occurred_at)}
                    </span>
                  </li>
                ))}
              </ul>
              <p className="mt-3 max-w-prose text-12 leading-relaxed text-ink-3">
                Append-only, {events.data.total} events. Dashboards read marts, marts rebuild from
                events, and an event is never edited — which is what makes every figure above
                reconcilable.
              </p>
            </>
          )}
        </Card>

        <div className="lg:col-span-12">
          <MockNotice />
        </div>
      </div>
    </>
  )
}
