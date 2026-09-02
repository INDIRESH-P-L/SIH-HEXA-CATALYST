/** Presentation helpers. Nothing here computes a domain value. */
import type { GapBand } from './types'

/**
 * The FRAC 4-point proficiency scale — the only scale used anywhere in the
 * platform. Level 0 is not part of FRAC: it means no evidence is on file,
 * which is a different statement from "the lowest rung".
 */
export const FRAC_LABELS: Record<number, string> = {
  0: 'No evidence',
  1: 'Awareness',
  2: 'Application',
  3: 'Leveraging for decisions',
  4: 'Subject Matter Expert',
}

export const FRAC_SHORT: Record<number, string> = {
  0: '—',
  1: 'Awareness',
  2: 'Application',
  3: 'Leveraging',
  4: 'SME',
}

export const MAX_LEVEL = 4

export function fracLabel(level: number): string {
  return FRAC_LABELS[Math.max(0, Math.min(MAX_LEVEL, level))] ?? FRAC_LABELS[0]!
}

export function fracShort(level: number): string {
  return FRAC_SHORT[Math.max(0, Math.min(MAX_LEVEL, level))] ?? FRAC_SHORT[0]!
}

/** Severity always carries its word. Colour never carries the meaning alone. */
export const BAND_ORDER: GapBand[] = [
  'CRITICAL',
  'SIGNIFICANT',
  'EMERGING',
  'MET',
  'STRENGTH',
]

export const BAND_CLASSES: Record<GapBand, string> = {
  CRITICAL: 'bg-critical-bg text-critical border-critical/30',
  SIGNIFICANT: 'bg-significant-bg text-significant border-significant/30',
  EMERGING: 'bg-emerging-bg text-emerging border-emerging/30',
  MET: 'bg-met-bg text-met border-met/30',
  STRENGTH: 'bg-strength-bg text-strength border-strength/30',
}

export const BAND_BAR: Record<GapBand, string> = {
  CRITICAL: 'bg-critical',
  SIGNIFICANT: 'bg-significant',
  EMERGING: 'bg-emerging',
  MET: 'bg-met',
  STRENGTH: 'bg-strength',
}

/** What each band means, shown next to the counts rather than assumed. */
export const BAND_MEANING: Record<GapBand, string> = {
  CRITICAL: 'Two or more levels below, on a competency the role marks as load-bearing',
  SIGNIFICANT: 'Below the level the role expects',
  EMERGING: 'New in this framework version, or needed in the next post up',
  MET: 'At the level the role expects',
  STRENGTH: 'Above expectation — a candidate mentor',
}

export function normaliseBand(band: string | null | undefined): GapBand {
  const upper = (band ?? '').toUpperCase()
  return (BAND_ORDER as string[]).includes(upper) ? (upper as GapBand) : 'MET'
}

export const HORIZON_LABEL: Record<string, string> = {
  current_role: 'Current role',
  next_role: 'Next role',
}

export const FORMAT_LABEL: Record<string, string> = {
  SELF_PACED: 'Self-paced',
  CLASSROOM: 'Classroom',
  BLENDED: 'Blended',
  VIRTUAL_LAB: 'Virtual lab',
}

export const CLUSTER_LABEL: Record<string, string> = {
  STATISTICAL: 'Statistical',
  TECHNICAL: 'Technical',
  DIGITAL_GOVERNANCE: 'Digital governance',
  BEHAVIOURAL: 'Behavioural & managerial',
}

export const KIND_LABEL: Record<string, string> = {
  knowledge: 'Knowledge',
  skill: 'Skill',
  attribute: 'Attribute',
}

export const DECAY_LABEL: Record<string, string> = {
  tools_platforms: 'Tools & platforms — 18 months',
  regulatory_procedural: 'Regulatory & procedural — 12 months',
  methodology: 'Methodology — 36 months',
  behavioural: 'Behavioural — does not decay',
}

export const EVIDENCE_LABEL: Record<string, string> = {
  self_declared: 'Self-declared',
  course_completion: 'Course completion',
  assessment: 'Assessment',
  admin_set: 'Administrator',
}

export function formatHours(hours: number): string {
  return `${hours} h`
}

export function formatPercent(value: number, digits = 0): string {
  return `${value.toFixed(digits)}%`
}

export function formatScore(value: number): string {
  return value.toFixed(4)
}

export function formatPriority(value: number): string {
  return value.toFixed(2)
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return '—'
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return '—'
  return date.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
}

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return '—'
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return '—'
  return date.toLocaleString('en-IN', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function titleCase(value: string): string {
  return value.charAt(0).toUpperCase() + value.slice(1).toLowerCase()
}

/** The ten deterministic validation checks, in the order the report shows them. */
export const CHECK_LABELS: Record<string, string> = {
  option_count: 'Four non-empty options',
  option_uniqueness: 'No duplicate options',
  key_range: 'Answer key in range',
  stem_length: 'Stem length 15–300',
  explanation: 'Explanation present and not a restatement',
  banned_options: 'No “all/none of the above”',
  length_bias: 'No length bias on the key',
  near_duplicate: 'Not a near-duplicate',
  difficulty: 'Valid difficulty',
  grounding: 'Grounded in the source passage',
}

export function checkLabel(key: string): string {
  return CHECK_LABELS[key] ?? key.replace(/_/g, ' ')
}

/** Difficulty weights, mirrored from the scorer so the UI can show the sum. */
export const DIFFICULTY_WEIGHT: Record<string, number> = { easy: 1, medium: 2, hard: 3 }

/** The names the ranking formula uses, and what each term measures. */
export const RANK_TERM_LABELS: Record<string, string> = {
  gap_priority: 'Gap priority',
  semantic_similarity: 'Semantic similarity',
  level_fit: 'Level fit',
  prerequisites_met: 'Prerequisites met',
  effort_fit: 'Effort fit',
  department_priority: 'Departmental priority',
  recency_language: 'Recency & language',
}

export const RANK_TERM_NOTES: Record<string, string> = {
  gap_priority: 'This gap’s priority relative to the largest open gap',
  semantic_similarity: 'Cosine similarity between the competency and the course',
  level_fit: 'How close the course level is to your current level plus one',
  prerequisites_met: '1.0 when every prerequisite competency is held',
  effort_fit: 'Whether the hours fit a serving officer’s monthly budget',
  department_priority: 'Raised for competencies the department is pushing',
  recency_language: 'Freshness of the record and whether you can read it',
}
