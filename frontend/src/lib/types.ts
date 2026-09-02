/** Shapes returned by the backend, mirroring the Pydantic response models. */

/** Five bands, matching the classification the gap engine produces. */
export type GapBand = 'CRITICAL' | 'SIGNIFICANT' | 'EMERGING' | 'MET' | 'STRENGTH'
export type Horizon = 'current_role' | 'next_role'
export type AssessmentMode = 'proctored' | 'practice'
export type Cluster = 'STATISTICAL' | 'TECHNICAL' | 'DIGITAL_GOVERNANCE' | 'BEHAVIOURAL'
export type CatalogueSource = 'IGOT' | 'NSSTA'
export type LearningFormat = 'SELF_PACED' | 'CLASSROOM' | 'BLENDED' | 'VIRTUAL_LAB'
export type Difficulty = 'easy' | 'medium' | 'hard'
export type QuestionStatus = 'DRAFT' | 'APPROVED' | 'REJECTED'
export type MaterialStatus = 'UPLOADED' | 'EXTRACTED' | 'CHUNKED' | 'GENERATED' | 'FAILED'
export type EnrollmentStatus =
  | 'RECOMMENDED'
  | 'ENROLLED'
  | 'NOMINATION_REQUESTED'
  | 'IN_PROGRESS'
  | 'COMPLETED'

// ── M1 · identity ────────────────────────────────────────────────────────────

export interface JobRole {
  id: string
  code: string
  title: string
  cadre: string
  description: string | null
}

export interface Profile {
  id: string
  full_name: string
  employee_code: string | null
  designation: string | null
  department: string | null
  station: string | null
  cadre: string | null
  years_experience: number | null
  education: string | null
  job_role: JobRole | null
  initial_assessment_completed: boolean
  created_at: string | null
}

export interface Me {
  id: string
  email: string | null
  roles: string[]
  profile: Profile
  auth_mode: string
  /** Whether any competency evidence is on file — the onboarding signal. */
  onboarded: boolean
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: Me
}

// ── M3 · initial competency assessment ───────────────────────────────────────

export interface InitialTopic {
  competency_id: string
  competency_code: string
  competency_name: string
  cluster: string
  required_level: number
  question_count: number
  criticality: number
}

export interface InitialTopicsResponse {
  topics: InitialTopic[]
  total_questions: number
}

export interface StartedAssessmentRef {
  competency_id: string
  competency_code: string
  competency_name: string
  assessment_id: string
  question_count: number
}

export interface InitialStartResponse {
  assessments: StartedAssessmentRef[]
  total_questions: number
}

export interface CompetencyResult {
  competency_id: string
  competency_code: string
  competency_name: string
  score: number
  correct: number
  total: number
  level_before: number
  level_after: number
  level_label: string
  required_level: number
  required_label: string
  gap: number
  gap_band: string
}

export interface InitialCompleteResponse {
  overall_score: number
  results: CompetencyResult[]
  top_gaps: CompetencyResult[]
  strengths: CompetencyResult[]
  ai_insight: string | null
  recommendations_generated: boolean
}

// ── M2 · competency framework ────────────────────────────────────────────────

export interface Competency {
  id: string
  code: string
  name: string
  cluster: Cluster
  description: string
  frac_type: string | null
  kind: string | null
  decay: string | null
}

export interface MyCompetency {
  competency: Competency
  current_level: number
  current_frac: string
  required_level: number | null
  required_frac: string | null
  confidence: number | null
  source_type: string | null
  assessed_at: string | null
}

export interface Requirement {
  competency: Competency
  required_level: number
  required_frac: string
  criticality: number
  horizon: Horizon
}

/** Position → Role → Activity → Competency. */
export interface Activity {
  id: string
  code: string
  name: string
  description: string | null
  sequence: number
  competency_codes: string[]
}

// ── M4 · skill gap ───────────────────────────────────────────────────────────

export interface GapDerivation {
  expected: number
  current: number
  difference: number
  criticality: number
  confidence: number
  uncertainty_multiplier: number
  horizon: string
  horizon_multiplier: number
  stale: boolean
  priority: number
  formula: string
}

export interface Gap {
  competency_id: string
  competency_code: string
  competency_name: string
  cluster: string
  required_level: number
  current_level: number
  gap: number
  band: GapBand
  priority: number
  criticality: number
  horizon: Horizon
  confidence: number
  frac_current: string
  frac_required: string
  stale: boolean
  source_type: string | null
  assessed_at: string | null
  derivation: GapDerivation | null
}

export interface GapSummary {
  total_competencies: number
  critical: number
  significant: number
  emerging: number
  met: number
  strength: number
  open_gaps: number
  top_gaps: Gap[]
  average_current_level: number
  average_required_level: number
  stale_count: number
  unassessed_count: number
}

export interface GapList {
  job_role_code: string | null
  job_role_title: string | null
  framework_version: string | null
  method: string
  scale: string
  gaps: Gap[]
  summary: GapSummary
  reassessment_candidates: string[]
}

// ── M6 · catalogue ───────────────────────────────────────────────────────────

export interface Course {
  id: string
  external_id: string
  source: CatalogueSource
  title: string
  provider: string
  competency_code: string
  proficiency_level: number
  duration_hours: number
  description: string
  prerequisites: string[]
  learning_format: LearningFormat
  course_url: string | null
  status: string
  session_start: string | null
  seats: number | null
  synced_at: string | null
}

export interface ProviderInfo {
  provider: string
  is_mock: boolean
  description: string
  base_url: string | null
  record_count: number | null
  embedded_count: number | null
  reachable: boolean | null
  circuit_state: string | null
}

export interface Enrollment {
  id: string
  course_id: string
  status: EnrollmentStatus
  external_ref: string | null
  enrolled_at: string | null
  completed_at: string | null
  created_at: string | null
  course: Course | null
  note: string | null
}

// ── M5 · recommendations ─────────────────────────────────────────────────────

export interface PathwayStep {
  order: number
  starts_on: string
  ends_on: string
  months_required: number
  anchored: boolean
}

export interface ScoreBreakdown {
  gap_priority: number
  semantic_similarity: number
  level_fit: number
  prerequisites_met: number
  effort_fit: number
  department_priority: number
  recency_language: number
  weights: Record<string, number>
  final_score: number
  fusion_score?: number
  retrievers?: string[]
  fusion?: string
  gap_derivation?: GapDerivation | null
  sequence?: PathwayStep | null
}

export interface Recommendation {
  id: string
  batch_id: string
  rank: number
  score: number
  course: Course
  competency_id: string | null
  competency_code: string | null
  competency_name: string | null
  current_level: number | null
  required_level: number | null
  gap_band: string | null
  explanation: string | null
  explanation_source: 'ai' | 'template'
  breakdown: ScoreBreakdown
  created_at: string | null
}

export interface RecommendationBatch {
  batch_id: string
  generated_at: string
  count: number
  ai_explanations: number
  llm_available: boolean
  recommendations: Recommendation[]
}

export interface RecommendationContext {
  recommendation_id: string
  rank: number
  score: number
  breakdown: ScoreBreakdown
  ai_context_sent: Record<string, unknown>
  context_note: string
  explanation: string | null
  explanation_source: string
  model: string | null
}

// ── M8 · materials and questions ─────────────────────────────────────────────

export interface Material {
  id: string
  title: string
  filename: string
  file_type: string
  competency_id: string | null
  competency_code: string | null
  competency_name: string | null
  status: MaterialStatus
  page_count: number | null
  char_count: number | null
  chunk_count: number | null
  question_count: number | null
  approved_count: number | null
  error: string | null
  created_at: string | null
}

export interface CheckResult {
  passed: boolean
  detail: string | null
}

export interface ValidationReport {
  passed: boolean
  failed_checks: string[]
  checks: Record<string, CheckResult>
}

export interface Question {
  id: string
  material_id: string | null
  competency_id: string | null
  question_text: string
  options: string[]
  correct_index: number
  explanation: string
  difficulty: Difficulty
  topic: string | null
  status: QuestionStatus
  validation: ValidationReport | null
  source_page: number | null
  created_at: string | null
}

export interface GenerationSummary {
  material_id: string
  requested: number
  generated: number
  passed: number
  rejected: number
  retried: number
  chunks_used: number
  llm_available: boolean
  model: string | null
  rejection_reasons: Record<string, number>
  check_pass_counts: Record<string, number>
  questions: Question[]
  rejected_questions: Question[]
  note: string | null
}

// ── M3 · assessments ─────────────────────────────────────────────────────────

export interface QuizQuestion {
  id: string
  position: number
  question_text: string
  options: string[]
  difficulty: Difficulty
  topic: string | null
  source_page: number | null
  selected_index: number | null
}

export interface Assessment {
  id: string
  status: 'IN_PROGRESS' | 'SUBMITTED' | 'ABANDONED'
  competency_id: string | null
  competency_code: string | null
  competency_name: string | null
  material_id: string | null
  total_questions: number
  answered_count: number
  started_at: string | null
  questions: QuizQuestion[]
}

export interface GapSnapshot {
  gap: number
  band: string
  frac: string | null
}

/** The arithmetic behind a score, reproducible from stored responses. */
export interface ScoringBreakdown {
  weighted_score: number
  raw_score: number
  numerator: number
  denominator: number
  attempted: number
  correct: number
  total_items: number
  weights: Record<string, number>
  per_difficulty: Record<string, { correct: number; attempted: number }>
  formula: string
}

export interface NewRecommendationRef {
  rank: number
  course_id: string
  title: string
  provider: string
  source: string
  proficiency_level: number
  duration_hours: number
  explanation: string | null
  explanation_source: string
}

export interface SubmitResponse {
  assessment_id: string
  score: number
  raw_score: number
  breakdown: ScoringBreakdown
  mode: AssessmentMode
  confidence: number
  correct_count: number
  attempted: number
  total_questions: number
  competency: { id: string | null; code: string; name: string }
  level_before: number
  level_after: number
  level_changed: boolean
  frac_before: string
  frac_after: string
  gap_before: GapSnapshot
  gap_after: GapSnapshot
  priority_before: number
  priority_after: number
  weak_topics: string[]
  strong_topics: string[]
  revisit: boolean
  ai_feedback: string
  feedback_source: 'ai' | 'template'
  new_recommendations: NewRecommendationRef[]
  evidence_id: string
  scoring_note: string
}

export interface AssessmentHistoryItem {
  id: string
  status: string
  competency_code: string | null
  competency_name: string | null
  total_questions: number
  correct_count: number | null
  score: number | null
  level_before: number | null
  level_after: number | null
  started_at: string | null
  submitted_at: string | null
}

// ── M7 · assistant ───────────────────────────────────────────────────────────

export interface AssistantCitation {
  material_id: string
  material_title: string
  chunk_id: string
  page_no: number | null
  excerpt: string
  score: number
}

export interface AssistantAnswer {
  answer: string
  citations: AssistantCitation[]
  grounded: boolean
  refused: boolean
  refusal_reason: string | null
  retrieval_score: number
  source: string
  suggested_course: { course_id: string; title: string; source: string } | null
  latency_ms: number
  note: string
}

export interface CorpusStats {
  approved_materials: number
  indexed_chunks: number
  grounding_threshold: number
  enabled: boolean
}

// ── M9 · analytics ───────────────────────────────────────────────────────────

export interface StatTileData {
  label: string
  value: number
  unit: string | null
  delta: number | null
}

export interface RadarPoint {
  competency_code: string
  competency_name: string
  current_level: number
  required_level: number
}

export interface ProgressPoint {
  at: string
  average_level: number
  competency_code: string | null
  level: number | null
}

export interface MyAnalytics {
  competencies_tracked: number
  average_current_level: number
  average_required_level: number
  gaps_open: number
  critical_gaps: number
  stale_competencies: number
  unassessed_competencies: number
  learning_hours_completed: number
  courses_completed: number
  courses_in_progress: number
  assessments_taken: number
  levels_gained: number
  radar: RadarPoint[]
  progress: ProgressPoint[]
  tiles: StatTileData[]
}

export interface CompetencyGapFrequency {
  competency_code: string
  competency_name: string
  officers_with_gap: number
  average_gap: number
  average_current_level: number
  average_required_level: number
  dominant_band: GapBand
  officers: number
  suppressed: boolean
}

export interface LevelDistributionBucket {
  level: number
  frac_label: string
  count: number
}

export interface EventRecord {
  id: number
  verb: string
  object_type: string | null
  object_id: string | null
  payload: Record<string, unknown> | null
  occurred_at: string
}

export interface EventStream {
  total: number
  by_verb: Record<string, number>
  recent: EventRecord[]
}

export interface AdminOverview {
  total_officers: number
  total_competencies: number
  total_courses: number
  total_assessments: number
  officers_with_critical_gap: number
  stale_evidence_rows: number
  unassessed_requirements: number
  events_recorded: number
  band_counts: Record<string, number>
  level_distribution: LevelDistributionBucket[]
  gap_frequency: CompetencyGapFrequency[]
  tiles: StatTileData[]
  k_anonymity_threshold: number
  note: string
}

export interface MatrixCell {
  job_role_code: string
  job_role_title: string
  competency_code: string
  competency_name: string
  average_level: number
  required_level: number
  officers: number
  suppressed: boolean
}

export interface CompetencyMatrix {
  job_roles: string[]
  competencies: string[]
  cells: MatrixCell[]
  k_anonymity_threshold: number
}

export interface TrainingEffectivenessRow {
  course_id: string
  course_title: string
  source: string
  competency_code: string
  completions: number
  average_level_before: number
  average_level_after: number
  average_delta: number
  comparison_delta: number | null
  net_delta: number | null
  suppressed: boolean
}

export interface TrainingEffectiveness {
  rows: TrainingEffectivenessRow[]
  k_anonymity_threshold: number
  note: string
}

// ── system ───────────────────────────────────────────────────────────────────

export interface ComponentHealth {
  status: 'ok' | 'degraded' | 'down' | 'disabled'
  detail: string | null
  latency_ms: number | null
}

export interface Health {
  status: 'ok' | 'degraded' | 'down' | 'disabled'
  app: string
  env: string
  auth_mode: string
  storage_mode: string
  catalogue_provider: string
  database: ComponentHealth
  embeddings: ComponentHealth
  llm: ComponentHealth
  catalogue: ComponentHealth
}
