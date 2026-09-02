/**
 * The core component set from the design system.
 *
 * Every colour comes from a token in tailwind.config.js. There are no raw hex
 * values here, no shadows on cards (hairline borders only), no gradients, and
 * no `dark:` variants.
 */
import { AlertCircle, type LucideIcon } from 'lucide-react'
import type { ButtonHTMLAttributes, ReactNode } from 'react'

import { BAND_CLASSES, normaliseBand } from '../../lib/format'
import type { GapBand } from '../../lib/types'

// ── Card ─────────────────────────────────────────────────────────────────────

export function Card({
  children,
  className = '',
  label,
  action,
  as: Tag = 'section',
}: {
  children: ReactNode
  className?: string
  /** Mono eyebrow shown in the header row. */
  label?: string
  /** One ghost action, right-aligned in the header row. */
  action?: ReactNode
  as?: 'section' | 'div' | 'article'
}) {
  return (
    <Tag className={`rounded border border-rule bg-surface p-5 ${className}`}>
      {(label || action) && (
        <header className="mb-4 flex items-center justify-between gap-3">
          {label ? <h2 className="eyebrow">{label}</h2> : <span />}
          {action}
        </header>
      )}
      {children}
    </Tag>
  )
}

// ── Button ───────────────────────────────────────────────────────────────────

type ButtonVariant = 'primary' | 'secondary' | 'ghost'

const BUTTON_VARIANTS: Record<ButtonVariant, string> = {
  primary: 'bg-accent text-surface hover:bg-accent/90',
  secondary: 'bg-surface border border-rule text-ink hover:bg-surface-2',
  ghost: 'bg-transparent text-ink-2 hover:bg-surface-2 hover:text-ink',
}

export function Button({
  children,
  variant = 'secondary',
  loading = false,
  icon: Icon,
  className = '',
  disabled,
  ...rest
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant
  loading?: boolean
  icon?: LucideIcon
}) {
  return (
    <button
      // min-w keeps the width locked while the label swaps for a spinner, so
      // nothing on the row jumps.
      className={`inline-flex h-control min-w-[7rem] items-center justify-center gap-2 rounded px-4 text-14 font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-40 ${BUTTON_VARIANTS[variant]} ${className}`}
      disabled={disabled || loading}
      {...rest}
    >
      {loading ? (
        <Spinner size={16} label="" />
      ) : (
        <>
          {Icon && <Icon size={16} strokeWidth={1.5} aria-hidden />}
          {children}
        </>
      )}
    </button>
  )
}

// ── Spinner ──────────────────────────────────────────────────────────────────

export function Spinner({ size = 20, label = 'Loading' }: { size?: number; label?: string }) {
  return (
    <span className="inline-flex items-center gap-2" role="status">
      <svg
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill="none"
        className="animate-spin text-ink-3"
        aria-hidden
      >
        <circle cx="12" cy="12" r="9" stroke="currentColor" strokeOpacity="0.25" strokeWidth="2" />
        <path
          d="M21 12a9 9 0 0 0-9-9"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
        />
      </svg>
      {label ? <span className="text-13 text-ink-2">{label}</span> : <span className="sr-only">Loading</span>}
    </span>
  )
}

// ── Badge ────────────────────────────────────────────────────────────────────

export function Badge({
  children,
  tone = 'neutral',
  className = '',
}: {
  children: ReactNode
  tone?: 'neutral' | 'accent' | 'met' | 'critical' | 'significant' | 'emerging' | 'strength'
  className?: string
}) {
  const tones: Record<string, string> = {
    neutral: 'bg-surface-2 text-ink-2 border-rule',
    accent: 'bg-accent-wash text-accent border-accent-line',
    met: BAND_CLASSES.MET,
    critical: BAND_CLASSES.CRITICAL,
    significant: BAND_CLASSES.SIGNIFICANT,
    emerging: BAND_CLASSES.EMERGING,
    strength: BAND_CLASSES.STRENGTH,
  }
  return (
    <span
      className={`inline-flex items-center rounded border px-2 py-0.5 font-mono text-11 font-medium uppercase tracking-[0.06em] ${tones[tone]} ${className}`}
    >
      {children}
    </span>
  )
}

// ── GapBadge ─────────────────────────────────────────────────────────────────

/**
 * Always renders the word. Colour never carries the meaning on its own.
 *
 * Five bands: CRITICAL, SIGNIFICANT, EMERGING, MET, STRENGTH.
 */
export function GapBadge({ band, className = '' }: { band: GapBand | string; className?: string }) {
  const value = normaliseBand(band)
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2 py-0.5 font-mono text-11 font-medium uppercase tracking-[0.06em] ${BAND_CLASSES[value]} ${className}`}
    >
      {value}
    </span>
  )
}

// ── LevelBar ─────────────────────────────────────────────────────────────────

/**
 * The signature component: current level, required level and the gap between
 * them, in about 100px and without a word of explanation.
 *
 * Four segments — the FRAC scale is four points, not five. An officer with no
 * evidence on file shows no filled segments and is labelled accordingly,
 * because "unmeasured" is a different statement from "lowest rung".
 *
 * The requirement is marked by a tick sitting above the bar.
 */
export function LevelBar({
  current,
  required,
  showLabel = true,
  animate = false,
  className = '',
}: {
  current: number
  required?: number | null
  showLabel?: boolean
  /** The one choreographed moment in the application: the post-quiz advance. */
  animate?: boolean
  className?: string
}) {
  const levels = [1, 2, 3, 4]
  const label = required != null ? `${current} / ${required}` : `${current}`

  // Segment geometry in pixels, so the requirement tick lands exactly on the
  // centre of its segment. Mixing percentages with pixel gaps drifts.
  const SEGMENT_W = 20
  const SEGMENT_GAP = 4
  const tickLeft =
    required != null ? (required - 1) * (SEGMENT_W + SEGMENT_GAP) + SEGMENT_W / 2 : 0

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <div className="relative pt-2">
        {required != null && required >= 1 && required <= 4 && (
          <span
            aria-hidden
            title={`Required level ${required}`}
            className="absolute top-0 h-1.5 w-0.5 -translate-x-1/2 bg-ink-3"
            style={{ left: `${tickLeft}px` }}
          />
        )}
        <div
          className="flex gap-1"
          role="img"
          aria-label={
            current === 0
              ? `No evidence on file, ${required ?? 4} required`
              : `Level ${current} of ${required ?? 4}`
          }
        >
          {levels.map((level) => {
            const filled = level <= current
            return (
              <span
                key={level}
                className={`h-2 w-5 origin-left rounded-sm ${
                  filled ? 'bg-accent' : 'bg-rule-2'
                } ${animate && filled && level === current ? 'animate-level-fill' : ''}`}
              />
            )
          })}
        </div>
      </div>
      {showLabel && (
        <span className={`numeral ${current === 0 ? 'text-ink-3' : 'text-ink-2'}`}>
          {label}
        </span>
      )}
    </div>
  )
}

// ── StatTile ─────────────────────────────────────────────────────────────────

export function StatTile({
  label,
  value,
  unit,
  delta,
  className = '',
}: {
  label: string
  value: number | string
  unit?: string | null
  delta?: number | null
  className?: string
}) {
  return (
    <div className={`rounded border border-rule bg-surface p-4 ${className}`}>
      <p className="eyebrow mb-2">{label}</p>
      <p className="font-mono text-32 font-medium tabular text-ink">
        {value}
        {unit ? <span className="ml-1 text-16 text-ink-3">{unit}</span> : null}
      </p>
      {delta != null && delta !== 0 && (
        <p className="mt-1 flex items-center gap-1 text-12 text-ink-2">
          <span aria-hidden>{delta > 0 ? '▲' : '▼'}</span>
          <span>
            {delta > 0 ? '+' : ''}
            {delta} since last period
          </span>
        </p>
      )}
    </div>
  )
}

// ── DataTable ────────────────────────────────────────────────────────────────

export interface Column<T> {
  key: string
  header: string
  numeric?: boolean
  render: (row: T) => ReactNode
  width?: string
}

export function DataTable<T>({
  columns,
  rows,
  keyOf,
  empty,
  caption,
}: {
  columns: Column<T>[]
  rows: T[]
  keyOf: (row: T) => string
  empty?: ReactNode
  caption?: string
}) {
  if (rows.length === 0 && empty) return <>{empty}</>

  return (
    // Wide tables scroll inside their own container; the page never scrolls
    // horizontally at any width.
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-13">
        {caption && <caption className="sr-only">{caption}</caption>}
        <thead>
          <tr className="border-b border-rule bg-surface-2">
            {columns.map((column) => (
              <th
                key={column.key}
                scope="col"
                style={column.width ? { width: column.width } : undefined}
                className={`px-3 py-2 font-mono text-11 font-medium uppercase tracking-[0.06em] text-ink-2 ${
                  column.numeric ? 'text-right tabular' : 'text-left'
                }`}
              >
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={keyOf(row)}
              className="border-b border-rule-2 transition-colors hover:bg-accent-wash/40"
            >
              {columns.map((column) => (
                <td
                  key={column.key}
                  data-numeric={column.numeric ? '' : undefined}
                  className={`h-11 px-3 align-middle ${column.numeric ? 'text-right tabular' : 'text-left'}`}
                >
                  {column.render(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ── EmptyState ───────────────────────────────────────────────────────────────

/** Never a bare "No data": always an icon, a line of text, and one action. */
export function EmptyState({
  icon: Icon,
  title,
  action,
}: {
  icon: LucideIcon
  title: string
  action?: ReactNode
}) {
  return (
    <div className="flex flex-col items-center gap-3 rounded border border-dashed border-rule bg-surface-2 px-6 py-10 text-center">
      <Icon size={20} strokeWidth={1.5} className="text-ink-3" aria-hidden />
      <p className="max-w-prose text-14 text-ink-2">{title}</p>
      {action}
    </div>
  )
}

// ── ErrorNote ────────────────────────────────────────────────────────────────

/** Errors render below the thing they belong to, with an icon, not just colour. */
export function ErrorNote({ children }: { children: ReactNode }) {
  return (
    <p className="mt-2 flex items-start gap-2 text-13 text-critical" role="alert">
      <AlertCircle size={16} strokeWidth={1.5} className="mt-0.5 shrink-0" aria-hidden />
      <span>{children}</span>
    </p>
  )
}

// ── Field ────────────────────────────────────────────────────────────────────

/** Every input carries a visible label. Never placeholder-only. */
export function Field({
  id,
  label,
  hint,
  error,
  children,
}: {
  id: string
  label: string
  hint?: string
  error?: string | null
  children: ReactNode
}) {
  return (
    <div>
      <label htmlFor={id} className="mb-1.5 block text-13 font-medium text-ink">
        {label}
      </label>
      {children}
      {hint && !error && <p className="mt-1 text-12 text-ink-3">{hint}</p>}
      {error && <ErrorNote>{error}</ErrorNote>}
    </div>
  )
}

export const inputClass =
  'h-control w-full rounded border border-rule bg-surface px-3 text-14 text-ink placeholder:text-ink-3 focus:border-accent'

// ── PageHeader ───────────────────────────────────────────────────────────────

export function PageHeader({
  title,
  description,
  action,
}: {
  title: string
  description?: string
  action?: ReactNode
}) {
  return (
    <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
      <div>
        <h1 className="text-24 font-semibold text-ink">{title}</h1>
        {description && <p className="mt-1 max-w-prose text-14 text-ink-2">{description}</p>}
      </div>
      {action}
    </div>
  )
}

// ── Skeleton ─────────────────────────────────────────────────────────────────

/** A plain block, never a shimmer gradient. */
export function Skeleton({ className = 'h-4 w-full' }: { className?: string }) {
  return <div className={`rounded-sm bg-rule-2 ${className}`} aria-hidden />
}
