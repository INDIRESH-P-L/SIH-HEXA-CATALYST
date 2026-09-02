import { useState } from 'react'
import { Link } from 'react-router-dom'
import { AlertTriangle, ListChecks, Target } from 'lucide-react'

import {
  Badge,
  Card,
  DataTable,
  EmptyState,
  GapBadge,
  LevelBar,
  PageHeader,
  Skeleton,
  type Column,
} from '../components/common'
import { useActivities, useGaps } from '../hooks'
import {
  BAND_MEANING,
  BAND_ORDER,
  CLUSTER_LABEL,
  EVIDENCE_LABEL,
  HORIZON_LABEL,
  formatDate,
} from '../lib/format'
import type { Gap, GapBand } from '../lib/types'

/** Every multiplier behind a priority, laid out so it can be checked. */
function Derivation({ row }: { row: Gap }) {
  const d = row.derivation
  if (!d) return null

  const terms: [string, string, string][] = [
    ['expected − current', `${d.expected} − ${d.current}`, String(d.difference)],
    ['× criticality', 'how load-bearing for the role', d.criticality.toFixed(2)],
    [
      '× (2 − confidence)',
      `evidence at ${d.confidence.toFixed(2)}${d.stale ? ', stale' : ''}`,
      d.uncertainty_multiplier.toFixed(2),
    ],
    ['× horizon', HORIZON_LABEL[d.horizon] ?? d.horizon, d.horizon_multiplier.toFixed(1)],
  ]

  return (
    <div className="rounded border border-rule bg-surface-2 p-3">
      <p className="eyebrow mb-2">Derivation</p>
      <table className="w-full text-12">
        <tbody>
          {terms.map(([term, note, value]) => (
            <tr key={term} className="border-b border-rule-2 last:border-0">
              <td className="py-1 pr-3 font-mono text-ink">{term}</td>
              <td className="py-1 pr-3 text-ink-3">{note}</td>
              <td className="py-1 text-right font-mono tabular text-ink">{value}</td>
            </tr>
          ))}
          <tr>
            <td className="pt-2 font-medium text-ink" colSpan={2}>
              Priority
            </td>
            <td className="pt-2 text-right font-mono font-medium tabular text-ink">
              {d.priority.toFixed(2)}
            </td>
          </tr>
        </tbody>
      </table>
      <p className="mt-2 font-mono text-11 leading-relaxed text-ink-3">{d.formula}</p>
      {d.confidence <= 0.4 && (
        <p className="mt-2 max-w-prose text-12 leading-relaxed text-ink-2">
          Low confidence nearly doubles this priority. The platform treats “we do not know
          whether this officer can do this” as urgent, which is what drives people into
          assessment.
        </p>
      )}
    </div>
  )
}

export default function MyCompetencies() {
  const { data, isLoading } = useGaps()
  const activities = useActivities()
  const [openRow, setOpenRow] = useState<string | null>(null)

  const columns: Column<Gap>[] = [
    {
      key: 'competency',
      header: 'Competency',
      render: (row) => (
        <div>
          <button
            type="button"
            onClick={() => setOpenRow(openRow === row.competency_id ? null : row.competency_id)}
            className="text-left text-ink hover:text-accent hover:underline"
          >
            {row.competency_name}
          </button>
          <div className="mt-0.5 flex flex-wrap items-center gap-2">
            <span className="font-mono text-11 text-ink-3">{row.competency_code}</span>
            <span className="text-11 text-ink-3">
              {CLUSTER_LABEL[row.cluster] ?? row.cluster}
            </span>
            {row.horizon === 'next_role' && <Badge tone="emerging">Next role</Badge>}
            {row.stale && (
              <span className="inline-flex items-center gap-1 text-11 text-emerging">
                <AlertTriangle size={11} strokeWidth={1.5} aria-hidden />
                stale
              </span>
            )}
          </div>
        </div>
      ),
    },
    {
      key: 'level',
      header: 'Current / expected',
      render: (row) => <LevelBar current={row.current_level} required={row.required_level} />,
      width: '180px',
    },
    {
      key: 'frac',
      header: 'FRAC proficiency',
      render: (row) => (
        <div className="text-12 leading-tight">
          <span className={row.current_level === 0 ? 'text-ink-3' : 'text-ink'}>
            {row.frac_current}
          </span>
          <span className="mx-1 text-ink-3" aria-hidden>
            →
          </span>
          <span className="text-ink-2">{row.frac_required}</span>
        </div>
      ),
    },
    {
      key: 'evidence',
      header: 'Evidence',
      render: (row) => (
        <div className="text-12 leading-tight">
          <span className={row.source_type ? 'text-ink-2' : 'text-ink-3'}>
            {row.source_type ? EVIDENCE_LABEL[row.source_type] ?? row.source_type : 'None on file'}
          </span>
          <div className="font-mono text-11 text-ink-3">
            conf {row.confidence.toFixed(2)}
            {row.assessed_at ? ` · ${formatDate(row.assessed_at)}` : ''}
          </div>
        </div>
      ),
      width: '150px',
    },
    {
      key: 'criticality',
      header: 'Crit.',
      numeric: true,
      render: (row) => <span className="numeral text-ink-3">{row.criticality.toFixed(2)}</span>,
      width: '64px',
    },
    {
      key: 'priority',
      header: 'Priority',
      numeric: true,
      render: (row) => <span className="numeral">{row.priority.toFixed(2)}</span>,
      width: '80px',
    },
    {
      key: 'band',
      header: 'Band',
      render: (row) => <GapBadge band={row.band} />,
      width: '130px',
    },
  ]

  const summary = data?.summary
  const counts: Record<GapBand, number> = {
    CRITICAL: summary?.critical ?? 0,
    SIGNIFICANT: summary?.significant ?? 0,
    EMERGING: summary?.emerging ?? 0,
    MET: summary?.met ?? 0,
    STRENGTH: summary?.strength ?? 0,
  }

  const openGap = data?.gaps.find((g) => g.competency_id === openRow)

  return (
    <>
      <PageHeader
        title="My competencies"
        description={
          data?.job_role_title
            ? `Measured against the expectation matrix for ${data.job_role_title}.`
            : undefined
        }
        action={
          <Link
            to="/recommendations"
            className="inline-flex h-control items-center justify-center rounded bg-accent px-4 text-14 font-medium text-surface hover:bg-accent/90"
          >
            Get recommendations
          </Link>
        }
      />

      {summary && (
        <div className="mb-4 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
          {BAND_ORDER.map((band) => (
            <div key={band} className="rounded border border-rule bg-surface p-4">
              <GapBadge band={band} />
              <p className="mt-2 font-mono text-32 font-medium tabular text-ink">
                {counts[band]}
              </p>
              <p className="mt-0.5 text-11 leading-tight text-ink-3">{BAND_MEANING[band]}</p>
            </div>
          ))}
        </div>
      )}

      {summary && (summary.stale_count > 0 || summary.unassessed_count > 0) && (
        <Card className="mb-4">
          <p className="flex flex-wrap items-center gap-2 text-13 text-ink-2">
            <AlertTriangle size={16} strokeWidth={1.5} className="text-emerging" aria-hidden />
            <span>
              <span className="numeral">{summary.unassessed_count}</span> unmeasured and{' '}
              <span className="numeral">{summary.stale_count}</span> stale. Unmeasured
              competencies sit at low confidence, which raises their priority — the platform
              surfaces not knowing as urgent.
            </span>
            {data?.reassessment_candidates.length ? (
              <span className="flex flex-wrap gap-1.5">
                {data.reassessment_candidates.slice(0, 6).map((code) => (
                  <Badge key={code} tone="emerging">
                    {code}
                  </Badge>
                ))}
              </span>
            ) : null}
          </p>
        </Card>
      )}

      <Card label="Gap analysis — deterministic">
        {isLoading && <Skeleton className="h-64 w-full" />}
        {data && (
          <>
            <DataTable
              columns={columns}
              rows={data.gaps}
              keyOf={(row) => row.competency_id}
              caption="Your competencies against your role's expectation matrix"
              empty={
                <EmptyState
                  icon={Target}
                  title="No competency requirements are defined for your job role."
                />
              }
            />
            {openGap && (
              <div className="mt-4 animate-fade-in">
                <p className="mb-2 text-13 font-medium text-ink">
                  {openGap.competency_name} — how this priority was reached
                </p>
                <Derivation row={openGap} />
              </div>
            )}
            <p className="mt-4 max-w-prose text-12 leading-relaxed text-ink-3">
              {data.method === 'deterministic'
                ? 'Rule-based arithmetic, not machine learning. '
                : ''}
              priority = (expected − current) × criticality × (2 − confidence) × horizon. Levels
              come from an append-only evidence ledger, so every figure above traces to the record
              that produced it. Select a competency to see its derivation.
            </p>
            <p className="mt-1 font-mono text-11 text-ink-3">
              {data.scale}
              {data.framework_version ? ` · ${data.framework_version}` : ''}
            </p>
          </>
        )}
      </Card>

      {activities.data && activities.data.length > 0 && (
        <Card className="mt-4" label="What your role actually does">
          <p className="mb-3 max-w-prose text-13 text-ink-2">
            FRAC is Position → Role → Activity → Competency. These are the activities your post
            performs, and the competencies each one depends on — which is what a gap means in
            practice.
          </p>
          <ol className="space-y-3">
            {activities.data.map((activity) => (
              <li key={activity.id} className="border-b border-rule-2 pb-3 last:border-0 last:pb-0">
                <div className="flex items-start gap-3">
                  <ListChecks
                    size={16}
                    strokeWidth={1.5}
                    className="mt-0.5 shrink-0 text-ink-3"
                    aria-hidden
                  />
                  <div>
                    <p className="text-14 font-medium text-ink">{activity.name}</p>
                    {activity.description && (
                      <p className="mt-0.5 max-w-prose text-12 leading-relaxed text-ink-2">
                        {activity.description}
                      </p>
                    )}
                    <div className="mt-1.5 flex flex-wrap gap-1.5">
                      {activity.competency_codes.map((code) => (
                        <Badge key={code}>{code}</Badge>
                      ))}
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ol>
        </Card>
      )}
    </>
  )
}
