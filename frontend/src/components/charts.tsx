/**
 * Recharts components on a light surface.
 *
 * Palette validated for colour-vision deficiency against #FFFFFF. Series
 * colours are never reused for gap severity, and severity colours are never
 * used as a series. One y-axis, never two. No pie or donut charts anywhere.
 */
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  LabelList,
} from 'recharts'

import type { CompetencyGapFrequency, MatrixCell, ProgressPoint, RadarPoint } from '../lib/types'
import { normaliseBand } from '../lib/format'

// Categorical — fixed order, never cycled, at most four series.
export const SERIES = ['#1F4FA3', '#EB6834', '#1BAF7A', '#EDA100'] as const
// Sequential — heatmap only, light to dark.
export const RAMP = ['#CDE2FB', '#9EC5F4', '#5598E7', '#256ABF', '#0D366B'] as const
// Chrome.
const GRID = '#EDF0F4'
const AXIS = '#DCE1E8'
const AXIS_TEXT = '#8A93A1'

// Severity tokens, mirrored from tailwind.config.js for chart fills.
// Recharts needs literal colours; these are the only hex values in the app
// outside the token file.
const BAND_FILL: Record<string, string> = {
  CRITICAL: '#D03B3B',
  SIGNIFICANT: '#C25A2E',
  EMERGING: '#B07800',
  MET: '#0CA30C',
  STRENGTH: '#1F4FA3',
}

const tooltipStyle = {
  contentStyle: {
    border: `1px solid ${AXIS}`,
    borderRadius: 6,
    fontSize: 12,
    fontFamily: 'IBM Plex Sans, system-ui, sans-serif',
    boxShadow: '0 4px 12px rgba(18,22,28,0.08)',
  },
  labelStyle: { color: '#12161C', fontWeight: 600 },
}

// ── CompetencyRadar ──────────────────────────────────────────────────────────

export function CompetencyRadar({ data }: { data: RadarPoint[] }) {
  if (data.length === 0) return null
  const shaped = data.map((point) => ({
    axis: point.competency_code,
    name: point.competency_name,
    Current: point.current_level,
    Required: point.required_level,
  }))

  return (
    <ResponsiveContainer width="100%" height={320}>
      <RadarChart data={shaped} outerRadius="72%">
        <PolarGrid stroke={GRID} />
        <PolarAngleAxis
          dataKey="axis"
          tick={{ fill: AXIS_TEXT, fontSize: 11, fontFamily: 'IBM Plex Mono, monospace' }}
        />
        <PolarRadiusAxis
          domain={[0, 4]}
          tickCount={5}
          tick={{ fill: AXIS_TEXT, fontSize: 10 }}
          axisLine={false}
        />
        {/* Required sits underneath as a filled polygon, current as a stroke. */}
        <Radar name="Required Target (FRAC)" dataKey="Required" stroke="#0F54B9" strokeWidth={1.5} fill="#EAF1FC" fillOpacity={0.6} />
        <Radar
          name="Current Measured Level"
          dataKey="Current"
          stroke="#F58220"
          strokeWidth={2.5}
          fill="#F58220"
          fillOpacity={0.25}
        />
        <Legend wrapperStyle={{ fontSize: 12, paddingTop: 8 }} />
        <Tooltip {...tooltipStyle} />
      </RadarChart>
    </ResponsiveContainer>
  )
}

// ── ProgressLine ─────────────────────────────────────────────────────────────

export function ProgressLine({ data }: { data: ProgressPoint[] }) {
  if (data.length === 0) return null
  // One point per evidence event. Same-day events are common in a single
  // session, so the tick shows the time as well as the date.
  const shaped = data.map((point) => {
    const at = new Date(point.at)
    return {
      at: at.toLocaleString('en-IN', {
        day: '2-digit',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit',
      }),
      level: point.average_level,
      competency: point.competency_code ?? '',
    }
  })

  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={shaped} margin={{ top: 8, right: 16, bottom: 4, left: -16 }}>
        <CartesianGrid stroke={GRID} vertical={false} />
        <XAxis
          dataKey="at"
          stroke={AXIS}
          tick={{ fill: AXIS_TEXT, fontSize: 10 }}
          tickLine={false}
          interval="preserveStartEnd"
          minTickGap={24}
        />
        <YAxis
          domain={[0, 4]}
          ticks={[0, 1, 2, 3, 4]}
          allowDecimals={false}
          stroke={AXIS}
          tick={{ fill: AXIS_TEXT, fontSize: 11 }}
          tickLine={false}
        />
        <Tooltip
          {...tooltipStyle}
          cursor={{ stroke: AXIS, strokeDasharray: '3 3' }}
          formatter={(value: number) => [value, 'Average level']}
          labelFormatter={(label: string, payload) => {
            const code = payload?.[0]?.payload?.competency
            return code ? `${label} · ${code} updated` : label
          }}
        />
        {/* No legend: the card title names the series. */}
        <Line
          type="monotone"
          dataKey="level"
          name="Average level"
          stroke={SERIES[0]}
          strokeWidth={2}
          dot={{ r: 3, fill: SERIES[0] }}
          activeDot={{ r: 5 }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}

// ── GapDistribution ──────────────────────────────────────────────────────────

/** Horizontal bars: competency names are long. Fill is the severity token. */
export function GapDistribution({ data }: { data: CompetencyGapFrequency[] }) {
  if (data.length === 0) return null
  const shaped = data.slice(0, 10).map((row) => ({
    code: row.competency_code,
    officers: row.officers_with_gap,
    band: normaliseBand(row.dominant_band),
  }))

  return (
    <ResponsiveContainer width="100%" height={Math.max(220, shaped.length * 34)}>
      <BarChart data={shaped} layout="vertical" margin={{ top: 4, right: 40, bottom: 4, left: 8 }}>
        <CartesianGrid stroke={GRID} horizontal={false} />
        <XAxis
          type="number"
          allowDecimals={false}
          stroke={AXIS}
          tick={{ fill: AXIS_TEXT, fontSize: 11 }}
          tickLine={false}
        />
        <YAxis
          type="category"
          dataKey="code"
          width={130}
          stroke={AXIS}
          tick={{ fill: AXIS_TEXT, fontSize: 11, fontFamily: 'IBM Plex Mono, monospace' }}
          tickLine={false}
        />
        <Tooltip {...tooltipStyle} cursor={{ fill: '#E7EDF8' }} />
        <Bar dataKey="officers" name="Officers with a gap" barSize={18} radius={[0, 4, 4, 0]}>
          {shaped.map((row) => (
            <Cell key={row.code} fill={BAND_FILL[row.band] ?? SERIES[0]} />
          ))}
          {/* Direct value labels, so meaning never rests on colour alone. */}
          <LabelList
            dataKey="officers"
            position="right"
            style={{ fill: AXIS_TEXT, fontSize: 11, fontFamily: 'IBM Plex Mono, monospace' }}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

// ── LevelDistribution ────────────────────────────────────────────────────────

export function LevelDistribution({
  data,
}: {
  data: { level: number; frac_label: string; count: number }[]
}) {
  if (data.length === 0) return null
  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} margin={{ top: 12, right: 8, bottom: 4, left: -16 }}>
        <CartesianGrid stroke={GRID} vertical={false} />
        <XAxis
          dataKey="level"
          stroke={AXIS}
          tick={{ fill: AXIS_TEXT, fontSize: 11, fontFamily: 'IBM Plex Mono, monospace' }}
          tickLine={false}
        />
        <YAxis
          allowDecimals={false}
          stroke={AXIS}
          tick={{ fill: AXIS_TEXT, fontSize: 11 }}
          tickLine={false}
        />
        <Tooltip
          {...tooltipStyle}
          cursor={{ fill: '#E7EDF8' }}
          formatter={(value: number) => [value, 'Competency records']}
          labelFormatter={(level: number) =>
            `Level ${level} — ${data.find((d) => d.level === level)?.frac_label ?? ''}`
          }
        />
        <Bar dataKey="count" name="Competency records" fill={SERIES[0]} barSize={28} radius={[4, 4, 0, 0]}>
          <LabelList
            dataKey="count"
            position="top"
            style={{ fill: AXIS_TEXT, fontSize: 11, fontFamily: 'IBM Plex Mono, monospace' }}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

// ── WorkforceHeatmap ─────────────────────────────────────────────────────────

/** Not Recharts: a CSS grid. Rows are job roles, columns competencies. */
export function WorkforceHeatmap({ cells }: { cells: MatrixCell[] }) {
  if (cells.length === 0) return null

  const roles = Array.from(new Set(cells.map((c) => c.job_role_title))).sort()
  const competencies = Array.from(new Set(cells.map((c) => c.competency_code))).sort()
  const lookup = new Map(cells.map((c) => [`${c.job_role_title}|${c.competency_code}`, c]))

  /** Level 0-4 to a ramp step. Ink flips to white on the two darkest steps. */
  function stepFor(level: number): { background: string; color: string } {
    const index = Math.max(0, Math.min(RAMP.length - 1, Math.round((level / 4) * (RAMP.length - 1))))
    return { background: RAMP[index]!, color: index >= 3 ? '#FFFFFF' : '#12161C' }
  }

  return (
    <div className="overflow-x-auto">
      <div className="inline-block min-w-full">
        <div
          className="grid gap-0.5"
          style={{ gridTemplateColumns: `160px repeat(${competencies.length}, 32px)` }}
        >
          <div />
          {competencies.map((code) => (
            <div
              key={code}
              className="flex h-20 items-end justify-center pb-1 font-mono text-11 text-ink-3"
            >
              <span className="[writing-mode:vertical-rl] rotate-180 whitespace-nowrap">{code}</span>
            </div>
          ))}

          {roles.map((role) => (
            <div key={role} className="contents">
              <div className="flex h-8 items-center pr-2 text-12 text-ink-2">{role}</div>
              {competencies.map((code) => {
                const cell = lookup.get(`${role}|${code}`)
                if (!cell) {
                  return (
                    <div
                      key={code}
                      className="flex h-8 w-8 items-center justify-center rounded-sm bg-rule-2 font-mono text-11 text-ink-3"
                      title={`${role} · ${code}: not required`}
                    >
                      –
                    </div>
                  )
                }
                if (cell.suppressed) {
                  // Withheld to protect individuals. A suppressed cell says so
                  // rather than reading as a zero.
                  return (
                    <div
                      key={code}
                      className="flex h-8 w-8 items-center justify-center rounded-sm border border-dashed border-rule bg-surface-2 font-mono text-11 text-ink-3"
                      title={`${role} · ${cell.competency_name}: suppressed — fewer than the k-anonymity threshold of officers`}
                    >
                      ·
                    </div>
                  )
                }
                const style = stepFor(cell.average_level)
                return (
                  <div
                    key={code}
                    className="flex h-8 w-8 items-center justify-center rounded-sm font-mono text-11 tabular"
                    style={style}
                    title={`${role} · ${cell.competency_name}: average level ${cell.average_level} of ${cell.required_level} required (${cell.officers} officer${cell.officers === 1 ? '' : 's'})`}
                  >
                    {cell.average_level.toFixed(1)}
                  </div>
                )
              })}
            </div>
          ))}
        </div>

        <div className="mt-4 flex items-center gap-2">
          <span className="eyebrow">Average level</span>
          <div className="flex gap-0.5">
            {RAMP.map((colour, index) => (
              <span
                key={colour}
                className="flex h-5 w-8 items-center justify-center rounded-sm font-mono text-11"
                style={{ background: colour, color: index >= 3 ? '#FFFFFF' : '#12161C' }}
              >
                {index}
              </span>
            ))}
            <span className="ml-1 flex h-5 items-center font-mono text-11 text-ink-3">4</span>
          </div>
          <span className="ml-3 inline-flex items-center gap-1.5 font-mono text-11 text-ink-3">
            <span className="inline-block h-5 w-8 rounded-sm border border-dashed border-rule bg-surface-2" />
            suppressed
          </span>
        </div>
      </div>
    </div>
  )
}
