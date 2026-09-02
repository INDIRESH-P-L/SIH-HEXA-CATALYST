import { Link } from 'react-router-dom'
import {
  AlertTriangle,
  ArrowRight,
  Award,
  BookOpen,
  Clock,
  GraduationCap,
  Layers,
  Sparkles,
  Target,
  TrendingUp,
} from 'lucide-react'

import { CompetencyRadar, ProgressLine } from '../components/charts'
import {
  DataTable,
  EmptyState,
  GapBadge,
  LevelBar,
  Skeleton,
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
      header: 'Competency & Code',
      render: (row) => (
        <div>
          <div className="font-bold text-slate-900">{row.competency_name}</div>
          <div className="flex items-center gap-2 mt-0.5">
            <span className="font-mono text-11 text-slate-500">{row.competency_code}</span>
            <span className="rounded bg-slate-100 px-1.5 py-0.2 text-10 font-semibold text-slate-600">
              FRAC 4-Point
            </span>
          </div>
        </div>
      ),
    },
    {
      key: 'level',
      header: 'Current vs Required',
      render: (row) => <LevelBar current={row.current_level} required={row.required_level} />,
      width: '210px',
    },
    {
      key: 'gap',
      header: 'Gap Delta',
      numeric: true,
      render: (row) => (
        <span className="font-mono text-14 font-extrabold text-[#0B3060]">
          {row.gap > 0 ? `−${row.gap}` : '0'}
        </span>
      ),
      width: '90px',
    },
    {
      key: 'band',
      header: 'Severity Band',
      render: (row) => <GapBadge band={row.band} />,
      width: '130px',
    },
    {
      key: 'action',
      header: 'Next Action',
      render: () => (
        <Link
          to="/recommendations"
          className="inline-flex items-center gap-1 rounded-md bg-[#0F54B9] px-2.5 py-1 text-11 font-bold text-white shadow-2xs hover:bg-[#0B3060] transition-colors"
        >
          <span>Courses</span>
          <ArrowRight size={12} />
        </Link>
      ),
      width: '100px',
    },
  ]

  return (
    <div className="space-y-6">
      {/* Official Government Greeting Banner */}
      <div className="overflow-hidden rounded-2xl border border-amber-200/90 bg-gradient-to-r from-[#FFFDF9] via-[#FFF9F2] to-[#F0F5FF] p-6 shadow-sm">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-5">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 border border-amber-300 px-2.5 py-0.5 text-11 font-bold text-[#D96B0B] uppercase">
                <Sparkles size={12} />
                iGOT Karmayogi Profile
              </span>
              <span className="text-11 font-semibold text-slate-500 font-mono">
                ID: {user?.id.slice(0, 8)}
              </span>
            </div>

            <h1 className="text-24 sm:text-28 font-extrabold tracking-tight text-[#0B3060]">
              Namaste, {user?.profile.full_name ?? 'Officer'}
            </h1>

            <p className="text-13 sm:text-14 text-slate-700 font-medium">
              {user?.profile.job_role?.title ?? 'Statistical Officer'} ·{' '}
              <span className="text-[#D96B0B] font-bold">
                {user?.profile.department ?? 'Ministry of Statistics & Programme Implementation'}
              </span>
            </p>
          </div>

          {/* Quick Jump Action Pills */}
          <div className="flex flex-wrap items-center gap-2.5 pt-1 lg:pt-0">
            <Link
              to="/competencies"
              className="flex items-center gap-1.5 rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-12 font-bold text-[#0B3060] shadow-xs hover:border-[#F58220] hover:bg-amber-50/50 transition-all"
            >
              <Target size={15} className="text-[#D96B0B]" />
              <span>View FRAC Gaps</span>
            </Link>

            <Link
              to="/assessments"
              className="flex items-center gap-1.5 rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-12 font-bold text-[#0B3060] shadow-xs hover:border-[#F58220] hover:bg-amber-50/50 transition-all"
            >
              <GraduationCap size={15} className="text-[#046A38]" />
              <span>Take Assessment</span>
            </Link>

            <Link
              to="/recommendations"
              className="flex items-center gap-1.5 rounded-xl bg-[#0B3060] px-4 py-2 text-12 font-bold text-white shadow-xs hover:bg-[#154399] transition-all"
            >
              <BookOpen size={15} className="text-amber-300" />
              <span>Recommended Courses</span>
            </Link>
          </div>
        </div>
      </div>

      {/* KPI Metric Stat Tiles */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
        {analytics.isLoading &&
          Array.from({ length: 5 }).map((_, index) => (
            <div key={index} className="rounded-xl border border-slate-200 bg-white p-4">
              <Skeleton className="mb-3 h-3 w-24" />
              <Skeleton className="h-8 w-16" />
            </div>
          ))}

        {analytics.data?.tiles.map((tile) => {
          // Add custom styling per tile
          const isCritical = tile.label.toLowerCase().includes('critical')
          const isOpen = tile.label.toLowerCase().includes('open')
          const isHours = tile.label.toLowerCase().includes('hours')
          const isReassess = tile.label.toLowerCase().includes('re-assessment')

          return (
            <div
              key={tile.label}
              className={`rounded-xl border p-4 shadow-xs transition-all hover:shadow-sm ${
                isCritical && Number(tile.value) > 0
                  ? 'border-red-200 bg-red-50/40'
                  : isOpen
                  ? 'border-amber-200 bg-amber-50/30'
                  : 'border-slate-200 bg-white'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-11 font-bold uppercase tracking-wider text-slate-600 truncate">
                  {tile.label}
                </span>
                {isCritical ? (
                  <AlertTriangle size={15} className="text-red-500 shrink-0" />
                ) : isHours ? (
                  <Clock size={15} className="text-indigo-500 shrink-0" />
                ) : isOpen ? (
                  <Target size={15} className="text-amber-500 shrink-0" />
                ) : (
                  <Layers size={15} className="text-blue-500 shrink-0" />
                )}
              </div>

              <div className="flex items-baseline gap-1">
                <span className="font-mono text-28 font-extrabold text-[#0B3060] tracking-tight">
                  {tile.value}
                </span>
                {tile.unit && (
                  <span className="text-13 font-bold text-slate-500">{tile.unit}</span>
                )}
              </div>

              <div className="mt-1 text-10 font-semibold text-slate-500">
                {isCritical
                  ? 'Priority Skill Gap Action'
                  : isOpen
                  ? 'Active requirements'
                  : isReassess
                  ? 'Decay verified'
                  : 'Accredited record'}
              </div>
            </div>
          )
        })}
      </div>

      {/* Main Grid: Radar Chart + Progress & FRAC Scale */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        {/* Left: Competency Profile Radar Chart (7 Cols) */}
        <div className="lg:col-span-7 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xs">
          <div className="bg-[#0F54B9] px-5 py-3 text-white flex items-center justify-between">
            <h2 className="text-14 font-bold tracking-wide flex items-center gap-2">
              <Target size={17} className="text-amber-300" />
              Role Competency Radar Profile
            </h2>
            <span className="text-11 bg-white/10 px-2 py-0.5 rounded font-mono font-medium">
              FRAC 4-Point Target
            </span>
          </div>

          <div className="p-5 space-y-4">
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
          </div>
        </div>

        {/* Right: Progress & FRAC 4-Point Scale Reference Guide (5 Cols) */}
        <div className="lg:col-span-5 space-y-6">
          {/* Growth over time card */}
          <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xs">
            <div className="bg-[#0B3060] px-5 py-3 text-white flex items-center justify-between">
              <h2 className="text-14 font-bold tracking-wide flex items-center gap-2">
                <TrendingUp size={17} className="text-amber-300" />
                Competency Level Over Time
              </h2>
              <span className="text-11 bg-white/10 px-2 py-0.5 rounded font-mono font-medium">
                Evidence Ledger
              </span>
            </div>

            <div className="p-5">
              {analytics.isLoading && <Skeleton className="h-44 w-full" />}
              {analytics.data && analytics.data.progress.length > 0 ? (
                <ProgressLine data={analytics.data.progress} />
              ) : (
                !analytics.isLoading && (
                  <div className="rounded-xl bg-slate-50 border border-slate-200 p-6 text-center text-slate-500">
                    <Award size={28} className="mx-auto mb-2 text-[#F58220]" />
                    <p className="text-13 font-bold text-slate-800">Your evidence progress line</p>
                    <p className="text-11 text-slate-500 mt-1">
                      Complete an assessment to log your first verified competency evidence point.
                    </p>
                  </div>
                )
              )}
            </div>
          </div>

          {/* Official FRAC 4-Point Scale Reference Widget */}
          <div className="rounded-2xl border border-amber-200 bg-gradient-to-br from-[#FFFDF9] to-[#FFF7ED] p-5 shadow-xs space-y-3">
            <div className="flex items-center justify-between border-b border-amber-200/80 pb-2.5">
              <span className="text-12 font-bold uppercase tracking-wider text-[#0B3060] flex items-center gap-1.5">
                <Layers size={15} className="text-[#D96B0B]" />
                FRAC 4-Point Scale Reference
              </span>
              <span className="text-10 font-mono font-bold text-[#D96B0B] bg-amber-100 px-2 py-0.5 rounded">
                iGOT Standard
              </span>
            </div>

            <div className="grid grid-cols-2 gap-2 text-11">
              <div className="rounded-lg bg-white p-2.5 border border-amber-100 shadow-2xs">
                <div className="font-bold text-[#0B3060]">Level 1 · Awareness</div>
                <div className="text-slate-500 text-10 mt-0.5">Foundational knowledge</div>
              </div>
              <div className="rounded-lg bg-white p-2.5 border border-amber-100 shadow-2xs">
                <div className="font-bold text-[#0B3060]">Level 2 · Application</div>
                <div className="text-slate-500 text-10 mt-0.5">Executes core workflows</div>
              </div>
              <div className="rounded-lg bg-white p-2.5 border border-amber-100 shadow-2xs">
                <div className="font-bold text-[#0B3060]">Level 3 · Leveraging</div>
                <div className="text-slate-500 text-10 mt-0.5">Solves complex problems</div>
              </div>
              <div className="rounded-lg bg-white p-2.5 border border-amber-100 shadow-2xs">
                <div className="font-bold text-[#0B3060]">Level 4 · Pioneering</div>
                <div className="text-slate-500 text-10 mt-0.5">National authority / SME</div>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom: Priority Skill Gaps Table (12 Cols) */}
        <div className="lg:col-span-12 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xs">
          <div className="bg-[#0B3060] px-5 py-3 text-white flex items-center justify-between">
            <h2 className="text-14 font-bold tracking-wide flex items-center gap-2">
              <Target size={17} className="text-amber-300" />
              Priority Skill-Gap Matrix
            </h2>
            <Link
              to="/competencies"
              className="inline-flex items-center gap-1 text-12 font-bold text-amber-300 hover:text-white transition-colors"
            >
              All 33 Competencies
              <ArrowRight size={14} />
            </Link>
          </div>

          <div className="p-5 space-y-4">
            {gaps.isLoading && <Skeleton className="h-32 w-full" />}
            {gaps.data && (
              <>
                <DataTable
                  columns={columns}
                  rows={topGaps}
                  keyOf={(row) => row.competency_id}
                  caption="Your highest-priority role skill gaps"
                  empty={
                    <EmptyState
                      icon={Target}
                      title="No open gaps against your role requirements. Every competency is met."
                    />
                  }
                />
                <div className="rounded-xl bg-blue-50/70 border border-blue-200 p-3.5 text-12 text-[#0B3060] leading-relaxed">
                  📐 <strong>Deterministic Formulation:</strong> Priority = <code className="font-mono font-bold">(Expected − Current) × Criticality × (2 − Confidence) × Horizon</code>. Unmeasured competencies carry a confidence multiplier of 1.75x to rank urgently.
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
