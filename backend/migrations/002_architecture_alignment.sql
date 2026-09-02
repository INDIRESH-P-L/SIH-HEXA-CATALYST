-- ═══════════════════════════════════════════════════════════════════════════
--  002 · ARCHITECTURE ALIGNMENT
--
--  Brings the schema onto the nine-module reference architecture:
--
--    * FRAC becomes a 4-point scale, the only scale used anywhere
--    * criticality widens to 1.0 – 3.0
--    * the FRAC graph gains its Activity layer (Position → Role → Activity
--      → Competency) and an immutable framework version
--    * competencies gain a decay class; requirements gain a horizon
--    * M1 gains a multi-source attribute resolver with provenance
--    * M3 gains item calibration, blueprints and proctored/practice modes
--    * M4 gains gap snapshots so a past dashboard recomputes identically
--    * M6 gains an outbox and a nomination state machine
--    * M8 gains source-span traceability and negative examples
--    * M9 gains an append-only event store and rollup marts
-- ═══════════════════════════════════════════════════════════════════════════

-- ─────────────────────────────────────────────────────────────
-- FRAC 4-POINT SCALE
-- 1 Awareness · 2 Application · 3 Leveraging for decisions · 4 SME
-- 0 means no evidence on file, which is distinct from the lowest rung.
-- ─────────────────────────────────────────────────────────────
update competency_evidence set level = 4 where level > 4;
update role_competency_requirements set required_level = 4 where required_level > 4;
update courses set proficiency_level = 4 where proficiency_level > 4;
update assessments set level_before = least(level_before, 4) where level_before > 4;
update assessments set level_after  = least(level_after, 4)  where level_after > 4;

alter table competency_evidence drop constraint if exists competency_evidence_level_check;
alter table competency_evidence
  add constraint competency_evidence_level_check check (level between 0 and 4);

alter table role_competency_requirements
  drop constraint if exists role_competency_requirements_required_level_check;
alter table role_competency_requirements
  add constraint role_competency_requirements_required_level_check
  check (required_level between 1 and 4);

alter table courses drop constraint if exists courses_proficiency_level_check;
alter table courses
  add constraint courses_proficiency_level_check check (proficiency_level between 1 and 4);

-- Criticality widens to 1.0 – 3.0.
alter table role_competency_requirements
  drop constraint if exists role_competency_requirements_criticality_check;
alter table role_competency_requirements
  alter column criticality type numeric(3,2),
  add constraint role_competency_requirements_criticality_check
  check (criticality between 1.0 and 3.0);

-- ─────────────────────────────────────────────────────────────
-- M2 · FRAMEWORK VERSIONING — immutable once sealed
-- Without it a dashboard from last quarter silently rewrites itself and
-- training effectiveness becomes impossible to measure.
-- ─────────────────────────────────────────────────────────────
create table framework_versions (
  id          uuid primary key default uuid_generate_v4(),
  version     text unique not null,          -- 'FRAC-2026.1'
  title       text not null,
  notes       text,
  sealed      boolean not null default false,
  sealed_at   timestamptz,
  created_at  timestamptz default now()
);

alter table role_competency_requirements
  add column framework_version_id uuid references framework_versions(id);

-- Horizon: is this competency needed in the current post, or the next one up?
-- The recommender discounts next-role requirements rather than ignoring them.
create type requirement_horizon as enum ('current_role', 'next_role');
alter table role_competency_requirements
  add column horizon requirement_horizon not null default 'current_role';

-- ─────────────────────────────────────────────────────────────
-- M2 · THE ACTIVITY LAYER
-- FRAC is Position → Role → Activity → Competency. Activities are the
-- concrete actions a role performs; competencies attach to them, which is
-- what makes a gap explainable as "you cannot yet do this activity".
-- ─────────────────────────────────────────────────────────────
create table activities (
  id           uuid primary key default uuid_generate_v4(),
  job_role_id  uuid references job_roles(id) on delete cascade,
  code         text not null,
  name         text not null,
  description  text,
  sequence     int not null default 0,
  created_at   timestamptz default now(),
  unique (job_role_id, code)
);

create table activity_competencies (
  activity_id    uuid references activities(id) on delete cascade,
  competency_id  uuid references competencies(id) on delete cascade,
  required_level int not null check (required_level between 1 and 4),
  primary key (activity_id, competency_id)
);

-- Competency typing and decay, per the framework.
create type competency_kind as enum ('knowledge', 'skill', 'attribute');
create type decay_class as enum
  ('tools_platforms', 'regulatory_procedural', 'methodology', 'behavioural');

alter table competencies add column kind competency_kind not null default 'skill';
alter table competencies add column decay decay_class not null default 'methodology';

-- Months after which evidence is treated as stale. Behavioural does not decay.
create or replace function decay_months(d decay_class)
returns int language sql immutable as $$
  select case d
    when 'tools_platforms'       then 18
    when 'regulatory_procedural' then 12
    when 'methodology'           then 36
    else null
  end;
$$;

-- ─────────────────────────────────────────────────────────────
-- M1 · ATTRIBUTE RESOLVER — a composed profile, with provenance
-- Four sources routinely disagree about a designation. Storing one value
-- loses the disagreement; storing each with its source, confidence and
-- effective date lets the resolver choose and an administrator correct.
-- ─────────────────────────────────────────────────────────────
create type attribute_source as enum
  ('sso_claim', 'hr_record', 'self_declared', 'certificate', 'admin_override');

create table profile_attributes (
  id              uuid primary key default uuid_generate_v4(),
  user_id         uuid references auth.users(id) on delete cascade,
  attribute       text not null,               -- 'designation', 'station', ...
  value           text not null,
  source          attribute_source not null,
  confidence      numeric(3,2) not null default 0.50,
  effective_from  date,
  superseded      boolean not null default false,
  note            text,
  created_at      timestamptz default now()
);
create index on profile_attributes (user_id, attribute, created_at desc);

-- DPDP Act 2023: a consent artefact recorded at first login, per purpose.
create table consent_records (
  id           uuid primary key default uuid_generate_v4(),
  user_id      uuid references auth.users(id) on delete cascade,
  purpose      text not null,
  granted      boolean not null default true,
  policy_version text not null default 'v1',
  created_at   timestamptz default now()
);

-- ─────────────────────────────────────────────────────────────
-- M3 · ITEM CALIBRATION, BLUEPRINTS, DELIVERY MODE
-- ─────────────────────────────────────────────────────────────
create type assessment_mode as enum ('proctored', 'practice');
alter table assessments add column mode assessment_mode not null default 'practice';
alter table assessments add column blueprint jsonb;
alter table assessments add column framework_version_id uuid references framework_versions(id);
alter table assessments add column weighted_score numeric(5,2);

-- Item parameters, learned from live responses. Launch uses the estimate from
-- the authored difficulty; the observed value replaces it once enough
-- responses exist.
alter table questions add column bloom_level text;
alter table questions add column difficulty_b numeric(5,3) default 0.0;
alter table questions add column discrimination_a numeric(5,3) default 1.0;
alter table questions add column times_served int not null default 0;
alter table questions add column times_correct int not null default 0;
--  The exact span the item was generated from, so a reviewer can always see
--  where a question came from.
alter table questions add column source_span text;
--  Rejected items are kept and reused as negative examples in later prompts.
alter table questions add column is_negative_example boolean not null default false;

-- SME cut-scores: band boundaries per competency, never one global threshold.
create table competency_cut_scores (
  competency_id  uuid primary key references competencies(id) on delete cascade,
  level_1_min    numeric(5,2) not null default 40.00,
  level_2_min    numeric(5,2) not null default 60.00,
  level_3_min    numeric(5,2) not null default 78.00,
  level_4_min    numeric(5,2) not null default 90.00,
  method         text not null default 'modified_angoff',
  set_by         uuid references auth.users(id),
  created_at     timestamptz default now()
);

-- ─────────────────────────────────────────────────────────────
-- M4 · GAP SNAPSHOTS
-- Snapshotted per (officer, framework version, date) so a dashboard from
-- last quarter recomputes to exactly the same numbers.
-- ─────────────────────────────────────────────────────────────
create table gap_snapshots (
  id                   uuid primary key default uuid_generate_v4(),
  user_id              uuid references auth.users(id) on delete cascade,
  framework_version_id uuid references framework_versions(id),
  taken_on             date not null default current_date,
  rows                 jsonb not null,
  summary              jsonb not null,
  created_at           timestamptz default now(),
  unique (user_id, framework_version_id, taken_on)
);

-- ─────────────────────────────────────────────────────────────
-- M6 · OUTBOX AND THE NOMINATION STATE MACHINE
-- The platform keeps working when the API does not: writes are queued
-- idempotently and retried rather than lost.
-- ─────────────────────────────────────────────────────────────
create type outbox_status as enum ('PENDING', 'SENT', 'FAILED', 'ABANDONED');

create table outbox (
  id             uuid primary key default uuid_generate_v4(),
  idempotency_key text unique not null,
  user_id        uuid references auth.users(id) on delete cascade,
  operation      text not null,                -- 'enrol' | 'nominate'
  payload        jsonb not null,
  status         outbox_status not null default 'PENDING',
  attempts       int not null default 0,
  last_error     text,
  external_ref   text,
  created_at     timestamptz default now(),
  updated_at     timestamptz default now()
);
create index on outbox (status, created_at);

-- requested → approved → confirmed, with rejection available at each step.
create type nomination_state as enum
  ('REQUESTED', 'SUPERVISOR_APPROVED', 'CBU_APPROVED', 'ACADEMY_CONFIRMED', 'REJECTED');

create table nominations (
  id            uuid primary key default uuid_generate_v4(),
  user_id       uuid references auth.users(id) on delete cascade,
  course_id     uuid references courses(id) on delete cascade,
  state         nomination_state not null default 'REQUESTED',
  justification text,
  external_ref  text,
  decided_by    uuid references auth.users(id),
  decided_at    timestamptz,
  decision_note text,
  created_at    timestamptz default now(),
  updated_at    timestamptz default now(),
  unique (user_id, course_id)
);

-- Unmapped external tags queue for administrator review rather than being
-- silently dropped.
create table tag_crosswalk (
  id            uuid primary key default uuid_generate_v4(),
  external_tag  text not null,
  source        catalogue_source not null,
  competency_id uuid references competencies(id),
  reviewed      boolean not null default false,
  created_at    timestamptz default now(),
  unique (source, external_tag)
);

-- ─────────────────────────────────────────────────────────────
-- M7 · APPROVED CORPUS
-- The assistant answers from the organisation's own approved material.
-- Only chunks whose material is approved enter the corpus.
-- ─────────────────────────────────────────────────────────────
alter table learning_materials add column corpus_approved boolean not null default false;
alter table learning_materials add column language text not null default 'en';

create table assistant_queries (
  id              uuid primary key default uuid_generate_v4(),
  user_id         uuid references auth.users(id) on delete cascade,
  question        text not null,
  answer          text,
  citations       jsonb,
  retrieval_score numeric(4,3),
  grounded        boolean not null default false,
  refused         boolean not null default false,
  refusal_reason  text,
  latency_ms      int,
  created_at      timestamptz default now()
);

-- ─────────────────────────────────────────────────────────────
-- M9 · EVENT STORE AND MARTS
-- One append-only stream is what makes every downstream number
-- reconcilable. Dashboards read marts; marts rebuild from events; an event
-- is never edited.
-- ─────────────────────────────────────────────────────────────
create table events (
  id          bigserial primary key,
  actor_id    uuid references auth.users(id),
  verb        text not null,                  -- 'assessment.submitted'
  object_type text,
  object_id   uuid,
  payload     jsonb,
  occurred_at timestamptz not null default now()
);
create index on events (verb, occurred_at desc);
create index on events (actor_id, occurred_at desc);

create table mart_competency (
  id                   uuid primary key default uuid_generate_v4(),
  job_role_id          uuid references job_roles(id),
  competency_id        uuid references competencies(id),
  framework_version_id uuid references framework_versions(id),
  officers             int not null,
  avg_current_level    numeric(4,2) not null,
  avg_required_level   numeric(4,2) not null,
  officers_with_gap    int not null,
  built_at             timestamptz default now(),
  unique (job_role_id, competency_id, framework_version_id)
);

create table mart_training_effectiveness (
  id                  uuid primary key default uuid_generate_v4(),
  course_id           uuid references courses(id),
  cohort              text,
  attendees           int not null,
  avg_level_before    numeric(4,2) not null,
  avg_level_after     numeric(4,2) not null,
  avg_delta           numeric(4,2) not null,
  comparison_delta    numeric(4,2),
  built_at            timestamptz default now()
);

-- ─────────────────────────────────────────────────────────────
-- SIMILARITY SEARCH — 4-point scale, unchanged signature
-- ─────────────────────────────────────────────────────────────
create or replace function match_courses(
  query_embedding vector(384),
  match_count     int default 20,
  min_similarity  float default 0.20
)
returns table (
  course_id uuid, external_id text, source catalogue_source, title text,
  provider text, competency_code text, proficiency_level int,
  duration_hours int, learning_format learning_format,
  prerequisites text[], course_url text, similarity float
)
language sql stable as $$
  select c.id, c.external_id, c.source, c.title, c.provider, c.competency_code,
         c.proficiency_level, c.duration_hours, c.learning_format,
         c.prerequisites, c.course_url,
         1 - (c.embedding <=> query_embedding) as similarity
  from courses c
  where c.status = 'ACTIVE'
    and 1 - (c.embedding <=> query_embedding) > min_similarity
  order by c.embedding <=> query_embedding
  limit match_count;
$$;

-- Lexical retrieval alongside the dense index: exact terms and rare tokens
-- are precisely what an embedding is worst at.
alter table courses add column search_tsv tsvector
  generated always as (
    setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(description, '')), 'B')
  ) stored;
create index on courses using gin (search_tsv);

alter table material_chunks add column search_tsv tsvector
  generated always as (to_tsvector('english', coalesce(content, ''))) stored;
create index on material_chunks using gin (search_tsv);

-- ─────────────────────────────────────────────────────────────
-- ROW LEVEL SECURITY on the new user-scoped tables
-- ─────────────────────────────────────────────────────────────
alter table profile_attributes   enable row level security;
alter table gap_snapshots        enable row level security;
alter table nominations          enable row level security;
alter table assistant_queries    enable row level security;
alter table consent_records      enable row level security;

create policy own_attributes on profile_attributes
  for select using (auth.uid() = user_id);
create policy own_snapshots on gap_snapshots
  for select using (auth.uid() = user_id);
create policy own_nominations on nominations
  for all using (auth.uid() = user_id);
create policy own_assistant_queries on assistant_queries
  for all using (auth.uid() = user_id);
create policy own_consent on consent_records
  for all using (auth.uid() = user_id);
