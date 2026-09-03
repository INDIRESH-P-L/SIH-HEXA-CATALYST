import { useState, useMemo } from 'react'
import {
  AlertCircle,
  BarChart3,
  CheckCircle2,
  Clock,
  EyeOff,
  Lock,
  RefreshCw,
  Search,
  ShieldAlert,
  ShieldCheck,
  Unlock,
  UserCheck,
  Users,
  UserX,
} from 'lucide-react'

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
import { errorMessage } from '../lib/api'

import {
  useAdminOverview,
  useAllAccounts,
  useBlockedAccounts,
  useBlockUser,
  useCompetencyMatrix,
  useEventStream,
  useRebuildMarts,
  useTrainingEffectiveness,
  useUnblockUser,
} from '../hooks'
import { formatDateTime } from '../lib/format'
import type { CompetencyGapFrequency, TrainingEffectivenessRow } from '../lib/types'

interface AdminDashboardProps {
  defaultTab?: 'accounts' | 'analytics'
}

export default function AdminDashboard({ defaultTab = 'accounts' }: AdminDashboardProps) {
  const [activeTab, setActiveTab] = useState<'accounts' | 'analytics'>(defaultTab)

  // Account Management data
  const accountsQuery = useAllAccounts()
  const blockedQuery = useBlockedAccounts()
  const unblockMutation = useUnblockUser()
  const blockMutation = useBlockUser()

  // Workforce Analytics data
  const overview = useAdminOverview()
  const matrix = useCompetencyMatrix()
  const effectiveness = useTrainingEffectiveness()
  const events = useEventStream()
  const rebuild = useRebuildMarts()

  // Filters for account management
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'blocked'>('all')
  const [roleFilter, setRoleFilter] = useState<string>('all')

  const accounts = accountsQuery.data ?? []
  const blockedAccounts = blockedQuery.data ?? []

  const stats = useMemo(() => {
    const total = accounts.length
    const blockedCount = accounts.filter((a) => a.is_blocked).length
    const activeCount = total - blockedCount
    const adminCount = accounts.filter((a) => a.roles.includes('admin')).length
    const trainerCount = accounts.filter((a) => a.roles.includes('trainer')).length
    return { total, activeCount, blockedCount, adminCount, trainerCount }
  }, [accounts])

  const filteredAccounts = useMemo(() => {
    return accounts.filter((account) => {
      // Search text
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase()
        const matchesName = account.full_name?.toLowerCase().includes(q)
        const matchesEmail = account.email?.toLowerCase().includes(q)
        const matchesCode = account.employee_code?.toLowerCase().includes(q)
        const matchesStation = account.station?.toLowerCase().includes(q)
        const matchesDept = account.department?.toLowerCase().includes(q)
        if (!matchesName && !matchesEmail && !matchesCode && !matchesStation && !matchesDept) {
          return false
        }
      }

      // Status filter
      if (statusFilter === 'active' && account.is_blocked) return false
      if (statusFilter === 'blocked' && !account.is_blocked) return false

      // Role filter
      if (roleFilter !== 'all' && !account.roles.includes(roleFilter)) return false

      return true
    })
  }, [accounts, searchQuery, statusFilter, roleFilter])

  // Columns for Workforce Analytics
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
        title="Admin Control Center"
        description="Institutional governance and account administration for the MoSPI Skill Intelligence Platform."
        action={
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => {
                void accountsQuery.refetch()
                void blockedQuery.refetch()
              }}
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-12 font-semibold text-slate-700 hover:bg-slate-50 transition-colors shadow-2xs"
            >
              <RefreshCw size={14} className={accountsQuery.isFetching ? 'animate-spin' : ''} />
              <span>Refresh Accounts</span>
            </button>
          </div>
        }
      />

      {/* Error Alert Banner when accounts query fails */}
      {accountsQuery.isError && (
        <div className="mb-6 flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-red-800 shadow-xs">
          <AlertCircle size={20} className="text-red-600 shrink-0 mt-0.5" />
          <div className="flex-1 text-12">
            <p className="font-bold text-red-900">Failed to fetch accounts from database</p>
            <p className="mt-0.5 text-red-700">
              {errorMessage(
                accountsQuery.error,
                'Could not load official user accounts. Please verify your connection or session.',
              )}
            </p>
          </div>
          <button
            type="button"
            onClick={() => void accountsQuery.refetch()}
            className="rounded-lg bg-red-600 px-3 py-1 text-11 font-bold text-white hover:bg-red-700 transition-colors"
          >
            Retry
          </button>
        </div>
      )}

      {/* Top Primary Navigation Tabs */}
      <div className="mb-6 flex border-b border-slate-200 bg-white px-4 rounded-xl shadow-2xs">
        <button
          type="button"
          onClick={() => setActiveTab('accounts')}
          className={`flex items-center gap-2 py-3.5 px-4 font-bold text-13 border-b-2 transition-colors ${
            activeTab === 'accounts'
              ? 'border-[#0B3060] text-[#0B3060]'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Users size={16} />
          <span>Account Management</span>
          {stats.blockedCount > 0 && (
            <span className="ml-1 rounded-full bg-red-600 px-2 py-0.5 text-10 text-white font-black animate-pulse">
              {stats.blockedCount} Blocked
            </span>
          )}
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('analytics')}
          className={`flex items-center gap-2 py-3.5 px-4 font-bold text-13 border-b-2 transition-colors ${
            activeTab === 'analytics'
              ? 'border-[#0B3060] text-[#0B3060]'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <BarChart3 size={16} />
          <span>Workforce Analytics</span>
        </button>
      </div>

      {activeTab === 'accounts' ? (
        /* ================= ACCOUNT MANAGEMENT VIEW ================= */
        <div className="space-y-6">
          {/* Key Stat Tiles */}
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-2xs">
              <div className="flex items-center justify-between text-slate-500 mb-2">
                <span className="text-11 font-bold uppercase tracking-wider">Total Accounts</span>
                <Users size={18} className="text-[#0B3060]" />
              </div>
              <div className="text-28 font-extrabold text-[#0B3060]">{stats.total}</div>
              <p className="mt-1 text-11 text-slate-500">Officers, trainers & admins registered</p>
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-2xs">
              <div className="flex items-center justify-between text-slate-500 mb-2">
                <span className="text-11 font-bold uppercase tracking-wider">Active Accounts</span>
                <UserCheck size={18} className="text-emerald-600" />
              </div>
              <div className="text-28 font-extrabold text-emerald-700">{stats.activeCount}</div>
              <p className="mt-1 text-11 text-emerald-600 font-medium">In good standing with active access</p>
            </div>

            <div
              className={`rounded-xl border p-4 shadow-2xs transition-colors ${
                stats.blockedCount > 0
                  ? 'border-red-300 bg-red-50/50'
                  : 'border-slate-200 bg-white'
              }`}
            >
              <div className="flex items-center justify-between text-slate-500 mb-2">
                <span className="text-11 font-bold uppercase tracking-wider text-red-700">
                  Blocked / Terminated
                </span>
                <UserX size={18} className="text-red-600" />
              </div>
              <div className="text-28 font-extrabold text-red-600">{stats.blockedCount}</div>
              <p className="mt-1 text-11 text-red-700 font-medium">
                {stats.blockedCount > 0 ? 'Assessment lockouts requiring admin action' : 'No accounts locked'}
              </p>
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-2xs">
              <div className="flex items-center justify-between text-slate-500 mb-2">
                <span className="text-11 font-bold uppercase tracking-wider">Admins & Trainers</span>
                <ShieldCheck size={18} className="text-indigo-600" />
              </div>
              <div className="text-28 font-extrabold text-indigo-900">
                {stats.adminCount + stats.trainerCount}
              </div>
              <p className="mt-1 text-11 text-slate-500">
                {stats.adminCount} Admin{stats.adminCount !== 1 ? 's' : ''} · {stats.trainerCount} Trainer{stats.trainerCount !== 1 ? 's' : ''}
              </p>
            </div>
          </div>

          {/* Active Blocked Accounts Alert Notice */}
          {stats.blockedCount > 0 && (
            <div className="rounded-xl border-2 border-red-300 bg-gradient-to-r from-red-50 via-amber-50 to-white p-5 shadow-xs">
              <div className="flex items-start gap-3.5">
                <div className="rounded-lg bg-red-600 p-2.5 text-white shadow-xs">
                  <ShieldAlert size={22} />
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <h3 className="text-14 font-extrabold text-red-900">
                      Security Alert: {stats.blockedCount} Officer Account(s) Currently Blocked
                    </h3>
                    <span className="text-11 font-bold bg-red-100 text-red-800 px-2.5 py-0.5 rounded-full border border-red-200">
                      5-Hour Assessment Violation Lockout
                    </span>
                  </div>
                  <p className="mt-1 text-12 text-slate-700 leading-relaxed max-w-3xl">
                    These accounts were terminated during an assessment due to repeated proctoring violations
                    (e.g., leaving the window, multiple faces detected, or audio cues). As an Administrator,
                    you can review and <strong>immediately unblock</strong> an officer below.
                  </p>

                  <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    {blockedAccounts.map((user) => (
                      <div
                        key={user.id}
                        className="rounded-lg border border-red-200 bg-white p-3 shadow-2xs flex flex-col justify-between"
                      >
                        <div>
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-13 text-slate-900 truncate">
                              {user.full_name}
                            </span>
                            <span className="rounded bg-red-100 px-1.5 py-0.5 text-9 font-extrabold text-red-700 uppercase">
                              Locked
                            </span>
                          </div>
                          <p className="font-mono text-11 text-slate-500 truncate">{user.email}</p>
                          <div className="mt-2 flex items-center gap-1.5 text-11 text-red-600">
                            <Clock size={12} />
                            <span>Until: {formatDateTime(user.blocked_until)}</span>
                          </div>
                        </div>

                        <button
                          type="button"
                          onClick={() => unblockMutation.mutate(user.id)}
                          disabled={unblockMutation.isPending}
                          className="mt-3 inline-flex w-full items-center justify-center gap-1.5 rounded-md bg-emerald-600 py-1.5 px-3 text-12 font-bold text-white hover:bg-emerald-700 transition-colors shadow-2xs disabled:opacity-50"
                        >
                          <Unlock size={14} />
                          <span>Unblock Account Now</span>
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* User Directory & Account Controls */}
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-2xs">
            <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h2 className="text-15 font-bold text-[#0B3060]">Official User Directory</h2>
                <p className="text-12 text-slate-500">
                  Search, monitor statuses, manage access permissions, and unblock accounts.
                </p>
              </div>

              {/* Filters Bar */}
              <div className="flex flex-wrap items-center gap-2.5">
                {/* Search Bar */}
                <div className="relative w-64">
                  <Search size={14} className="absolute left-3 top-2.5 text-slate-400" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search by name, email, code..."
                    className="w-full rounded-lg border border-slate-200 bg-slate-50/70 py-1.5 pl-8 pr-3 text-12 text-slate-800 placeholder-slate-400 focus:bg-white focus:border-[#0B3060] focus:outline-none"
                  />
                </div>

                {/* Status Filter */}
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value as any)}
                  className="rounded-lg border border-slate-200 bg-slate-50/70 py-1.5 px-2.5 text-12 font-medium text-slate-700 focus:bg-white focus:outline-none"
                >
                  <option value="all">All Statuses</option>
                  <option value="active">Active Only</option>
                  <option value="blocked">Blocked Only</option>
                </select>

                {/* Role Filter */}
                <select
                  value={roleFilter}
                  onChange={(e) => setRoleFilter(e.target.value)}
                  className="rounded-lg border border-slate-200 bg-slate-50/70 py-1.5 px-2.5 text-12 font-medium text-slate-700 focus:bg-white focus:outline-none"
                >
                  <option value="all">All Roles</option>
                  <option value="employee">Statistical Officers</option>
                  <option value="trainer">Trainers</option>
                  <option value="admin">Administrators</option>
                </select>
              </div>
            </div>

            {/* Accounts Table */}
            {accountsQuery.isLoading ? (
              <div className="py-8">
                <Skeleton className="h-48 w-full" />
              </div>
            ) : accountsQuery.isError ? (
              <div className="py-12 text-center">
                <AlertCircle size={32} className="mx-auto text-red-400 mb-2" />
                <p className="text-13 font-bold text-red-800">Unable to load official accounts</p>
                <p className="text-11 text-red-600 mt-1">
                  {errorMessage(accountsQuery.error, 'An error occurred while communicating with the database.')}
                </p>
                <button
                  type="button"
                  onClick={() => void accountsQuery.refetch()}
                  className="mt-3 inline-flex items-center gap-1 rounded-lg border border-red-300 bg-white px-3 py-1.5 text-11 font-bold text-red-700 hover:bg-red-50 transition-colors"
                >
                  <RefreshCw size={12} />
                  <span>Try Again</span>
                </button>
              </div>
            ) : filteredAccounts.length === 0 ? (
              <div className="py-12 text-center">
                <Users size={32} className="mx-auto text-slate-300 mb-2" />
                <p className="text-13 font-bold text-slate-700">No user accounts match your filters</p>
                <p className="text-11 text-slate-500">Try clearing the search query or changing filters.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-12">
                  <thead>
                    <tr className="border-b border-slate-200 bg-slate-50/80 text-10 font-bold uppercase tracking-wider text-slate-600">
                      <th className="py-3 px-4">Official / User</th>
                      <th className="py-3 px-4">Code & Cadre</th>
                      <th className="py-3 px-4">Roles</th>
                      <th className="py-3 px-4">Account Status</th>
                      <th className="py-3 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {filteredAccounts.map((account) => (
                      <tr
                        key={account.id}
                        className={`hover:bg-slate-50/80 transition-colors ${
                          account.is_blocked ? 'bg-red-50/30' : ''
                        }`}
                      >
                        {/* Official Info */}
                        <td className="py-3.5 px-4">
                          <div className="flex items-center gap-3">
                            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-200 font-bold text-12 text-[#0B3060]">
                              {account.full_name
                                .split(' ')
                                .map((n) => n[0])
                                .slice(0, 2)
                                .join('')}
                            </div>
                            <div className="min-w-0">
                              <div className="font-bold text-slate-900 truncate">
                                {account.full_name}
                              </div>
                              <div className="font-mono text-11 text-slate-500 truncate">
                                {account.email}
                              </div>
                            </div>
                          </div>
                        </td>

                        {/* Code & Cadre */}
                        <td className="py-3.5 px-4 text-slate-700">
                          <div className="font-mono text-11 font-semibold text-slate-800">
                            {account.employee_code ?? '—'}
                          </div>
                          <div className="text-10 text-slate-500">
                            {account.cadre ?? 'ISS'} · {account.station ?? 'HQ'}
                          </div>
                        </td>

                        {/* Roles */}
                        <td className="py-3.5 px-4">
                          <div className="flex flex-wrap gap-1">
                            {account.roles.map((role) => (
                              <span
                                key={role}
                                className={`rounded px-2 py-0.5 text-10 font-bold uppercase ${
                                  role === 'admin'
                                    ? 'bg-purple-100 text-purple-800 border border-purple-200'
                                    : role === 'trainer'
                                    ? 'bg-amber-100 text-amber-800 border border-amber-200'
                                    : 'bg-blue-50 text-blue-800 border border-blue-200'
                                }`}
                              >
                                {role}
                              </span>
                            ))}
                          </div>
                        </td>

                        {/* Status */}
                        <td className="py-3.5 px-4">
                          {account.is_blocked ? (
                            <div>
                              <span className="inline-flex items-center gap-1.5 rounded-full bg-red-100 px-2.5 py-1 text-11 font-bold text-red-700 border border-red-200">
                                <Lock size={12} />
                                <span>Locked (Terminated)</span>
                              </span>
                              {account.blocked_until && (
                                <div className="mt-1 text-10 text-red-600 font-mono">
                                  Until {formatDateTime(account.blocked_until)}
                                </div>
                              )}
                            </div>
                          ) : (
                            <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1 text-11 font-bold text-emerald-700 border border-emerald-200">
                              <CheckCircle2 size={12} />
                              <span>Active</span>
                            </span>
                          )}
                        </td>

                        {/* Actions */}
                        <td className="py-3.5 px-4 text-right">
                          {account.is_blocked ? (
                            <Button
                              variant="primary"
                              onClick={() => unblockMutation.mutate(account.id)}
                              loading={unblockMutation.isPending}
                              className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold h-8 text-11 px-3 shadow-xs"
                            >
                              <Unlock size={13} className="mr-1" />
                              Unblock
                            </Button>
                          ) : (
                            <button
                              type="button"
                              onClick={() => {
                                if (
                                  window.confirm(
                                    `Are you sure you want to lock the account for ${account.full_name} for 5 hours?`
                                  )
                                ) {
                                  blockMutation.mutate({ userId: account.id, hours: 5 })
                                }
                              }}
                              disabled={blockMutation.isPending}
                              className="inline-flex items-center gap-1 text-11 font-semibold text-slate-500 hover:text-red-600 px-2 py-1 rounded hover:bg-red-50 transition-colors"
                              title="Lock account for 5 hours"
                            >
                              <Lock size={12} />
                              <span>Lock (5h)</span>
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* ================= WORKFORCE ANALYTICS VIEW ================= */
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-15 font-bold text-[#0B3060]">Workforce Analytics & Aggregates</h2>
              <p className="text-12 text-slate-500">
                Deterministic aggregates over the evidence ledger. Cells covering fewer than five officers are suppressed.
              </p>
            </div>
            <Button
              variant="secondary"
              icon={RefreshCw}
              loading={rebuild.isPending}
              onClick={() => rebuild.mutate()}
            >
              Rebuild marts
            </Button>
          </div>

          <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
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
                    {events.data.recent.map((event) => (
                      <li
                        key={event.id}
                        className="flex flex-wrap items-baseline gap-x-3 gap-y-0.5 rounded px-2 py-1 text-12 hover:bg-surface-2"
                      >
                        <span className="font-mono text-11 text-ink-3">
                          {formatDateTime(event.occurred_at)}
                        </span>
                        <span className="font-mono text-11 text-brand">{event.verb}</span>
                        <span className="text-ink">{event.object_type ?? 'system'}</span>
                        {event.object_id && (
                          <span className="text-11 text-ink-3 font-mono">({event.object_id})</span>
                        )}
                      </li>
                    ))}
                  </ul>
                </>
              )}
            </Card>
          </div>
        </div>
      )}
    </>
  )
}
