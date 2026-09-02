-- ═══════════════════════════════════════════════════════════════════════════
--  001 · INITIAL SCHEMA
--  Applies identically on Supabase PostgreSQL and on local Postgres+pgvector.
--  auth.users is provided by Supabase Auth, or by 000_local_auth_shim.sql.
-- ═══════════════════════════════════════════════════════════════════════════

-- ─────────────────────────────────────────────────────────────
-- EXTENSIONS
-- ─────────────────────────────────────────────────────────────
create extension if not exists "uuid-ossp";
create extension if not exists vector;

-- ─────────────────────────────────────────────────────────────
-- M1 · IDENTITY & PROFILE
-- ─────────────────────────────────────────────────────────────
create type app_role as enum ('employee', 'trainer', 'admin');
create type cadre_type as enum ('ISS', 'SSS', 'STATE', 'OTHER');

create table job_roles (
  id            uuid primary key default uuid_generate_v4(),
  code          text unique not null,          -- 'STAT_OFFICER'
  title         text not null,                 -- 'Statistical Officer'
  cadre         cadre_type not null default 'ISS',
  description   text,
  created_at    timestamptz default now()
);

create table profiles (
  id                uuid primary key references auth.users(id) on delete cascade,
  full_name         text not null,
  employee_code     text unique,
  designation       text,
  department        text default 'Ministry of Statistics and Programme Implementation',
  station           text,
  job_role_id       uuid references job_roles(id),
  cadre             cadre_type default 'ISS',
  years_experience  int default 0,
  education         text,
  created_at        timestamptz default now(),
  updated_at        timestamptz default now()
);

create table user_roles (
  user_id  uuid references auth.users(id) on delete cascade,
  role     app_role not null default 'employee',
  primary key (user_id, role)
);

-- ─────────────────────────────────────────────────────────────
-- M2 · COMPETENCY FRAMEWORK
-- ─────────────────────────────────────────────────────────────
create type competency_cluster as enum
  ('STATISTICAL', 'TECHNICAL', 'DIGITAL_GOVERNANCE', 'BEHAVIOURAL');

create table competencies (
  id           uuid primary key default uuid_generate_v4(),
  code         text unique not null,           -- 'SQL'
  name         text not null,                  -- 'SQL & Database Querying'
  cluster      competency_cluster not null,
  description  text not null,                  -- used to build the embedding
  frac_type    text default 'domain',          -- domain | functional | behavioural
  embedding    vector(384),
  created_at   timestamptz default now()
);

create table role_competency_requirements (
  job_role_id     uuid references job_roles(id) on delete cascade,
  competency_id   uuid references competencies(id) on delete cascade,
  required_level  int not null check (required_level between 1 and 5),
  criticality     numeric(3,2) not null default 1.00 check (criticality between 1.0 and 2.0),
  primary key (job_role_id, competency_id)
);

-- ─────────────────────────────────────────────────────────────
-- EVIDENCE LEDGER — append-only, the source of truth for levels
-- ─────────────────────────────────────────────────────────────
create type evidence_source as enum
  ('self_declared', 'assessment', 'course_completion', 'admin_set');

create table competency_evidence (
  id             uuid primary key default uuid_generate_v4(),
  user_id        uuid references auth.users(id) on delete cascade,
  competency_id  uuid references competencies(id) on delete cascade,
  level          int not null check (level between 0 and 5),
  score          numeric(5,2),                  -- quiz % if applicable
  source_type    evidence_source not null,
  source_ref     uuid,                          -- assessment_id / course_id
  confidence     numeric(3,2) not null default 0.50,
  note           text,
  created_at     timestamptz default now()
);
create index on competency_evidence (user_id, competency_id, created_at desc);

-- current level = latest evidence row per (user, competency)
create view user_competency as
select distinct on (e.user_id, e.competency_id)
  e.user_id, e.competency_id, e.level as current_level,
  e.confidence, e.source_type, e.created_at as assessed_at
from competency_evidence e
order by e.user_id, e.competency_id, e.created_at desc;

-- ─────────────────────────────────────────────────────────────
-- M6 · CATALOGUE MIRROR  (synced from the mock service)
-- ─────────────────────────────────────────────────────────────
create type catalogue_source  as enum ('IGOT', 'NSSTA');
create type learning_format   as enum ('SELF_PACED', 'CLASSROOM', 'BLENDED', 'VIRTUAL_LAB');

create table courses (
  id                 uuid primary key default uuid_generate_v4(),
  external_id        text not null,             -- 'IGOT-SQL-101'
  source             catalogue_source not null,
  title              text not null,
  provider           text not null,
  competency_code    text not null,             -- joins to competencies.code
  proficiency_level  int not null check (proficiency_level between 1 and 5),
  duration_hours     int not null,
  description        text not null,
  prerequisites      text[] default '{}',
  learning_format    learning_format not null,
  course_url         text,
  status             text default 'ACTIVE',
  session_start      date,                      -- NSSTA dated programmes only
  seats              int,                       -- NSSTA only
  embedding          vector(384),
  synced_at          timestamptz default now(),
  unique (source, external_id)
);

create type enrollment_status as enum
  ('RECOMMENDED', 'ENROLLED', 'NOMINATION_REQUESTED', 'IN_PROGRESS', 'COMPLETED');

create table enrollments (
  id            uuid primary key default uuid_generate_v4(),
  user_id       uuid references auth.users(id) on delete cascade,
  course_id     uuid references courses(id) on delete cascade,
  status        enrollment_status not null default 'RECOMMENDED',
  external_ref  text,                           -- id returned by the catalogue service
  enrolled_at   timestamptz,
  completed_at  timestamptz,
  created_at    timestamptz default now(),
  unique (user_id, course_id)
);

-- ─────────────────────────────────────────────────────────────
-- M5 · RECOMMENDATIONS
-- ─────────────────────────────────────────────────────────────
create table recommendations (
  id             uuid primary key default uuid_generate_v4(),
  batch_id       uuid not null,
  user_id        uuid references auth.users(id) on delete cascade,
  course_id      uuid references courses(id) on delete cascade,
  competency_id  uuid references competencies(id),
  rank           int not null,
  score          numeric(6,4) not null,
  breakdown      jsonb not null,                -- every term of the ranking formula
  explanation    text,                          -- LLM-written, may be null on fallback
  created_at     timestamptz default now()
);
create index on recommendations (user_id, batch_id, rank);

-- ─────────────────────────────────────────────────────────────
-- M8 · LEARNING MATERIAL & GENERATED QUESTIONS
-- ─────────────────────────────────────────────────────────────
create type material_status as enum ('UPLOADED','EXTRACTED','CHUNKED','GENERATED','FAILED');

create table learning_materials (
  id             uuid primary key default uuid_generate_v4(),
  uploaded_by    uuid references auth.users(id),
  title          text not null,
  filename       text not null,
  storage_path   text not null,
  file_type      text not null,                 -- pdf | docx | pptx
  competency_id  uuid references competencies(id),
  status         material_status default 'UPLOADED',
  page_count     int,
  char_count     int,
  error          text,
  created_at     timestamptz default now()
);

create table material_chunks (
  id            uuid primary key default uuid_generate_v4(),
  material_id   uuid references learning_materials(id) on delete cascade,
  chunk_index   int not null,
  content       text not null,
  page_no       int,
  embedding     vector(384),
  created_at    timestamptz default now()
);
create index on material_chunks (material_id, chunk_index);

create type question_status as enum ('DRAFT','APPROVED','REJECTED');

create table questions (
  id             uuid primary key default uuid_generate_v4(),
  material_id    uuid references learning_materials(id) on delete cascade,
  chunk_id       uuid references material_chunks(id),
  competency_id  uuid references competencies(id),
  question_text  text not null,
  options        jsonb not null,                -- exactly 4 strings
  correct_index  int not null check (correct_index between 0 and 3),
  explanation    text not null,
  difficulty     text not null check (difficulty in ('easy','medium','hard')),
  topic          text,
  status         question_status default 'DRAFT',
  validation     jsonb,                         -- which checks passed / failed
  source_page    int,
  embedding      vector(384),                   -- for near-duplicate detection
  created_at     timestamptz default now()
);

-- ─────────────────────────────────────────────────────────────
-- M3 · ASSESSMENTS
-- ─────────────────────────────────────────────────────────────
create type assessment_status as enum ('IN_PROGRESS','SUBMITTED','ABANDONED');

create table assessments (
  id                uuid primary key default uuid_generate_v4(),
  user_id           uuid references auth.users(id) on delete cascade,
  competency_id     uuid references competencies(id),
  material_id       uuid references learning_materials(id),
  status            assessment_status default 'IN_PROGRESS',
  total_questions   int not null,
  correct_count     int,
  score             numeric(5,2),
  level_before      int,
  level_after       int,
  feedback          text,                       -- LLM-written
  started_at        timestamptz default now(),
  submitted_at      timestamptz
);

create table assessment_questions (
  assessment_id   uuid references assessments(id) on delete cascade,
  question_id     uuid references questions(id),
  position        int not null,
  selected_index  int,
  is_correct      boolean,
  primary key (assessment_id, question_id)
);

-- ─────────────────────────────────────────────────────────────
-- AI GOVERNANCE
-- ─────────────────────────────────────────────────────────────
create table llm_cache (
  cache_key   text primary key,                 -- sha256(model + purpose + prompt)
  model       text not null,
  purpose     text not null,
  response    jsonb not null,
  created_at  timestamptz default now()
);

create table llm_audit (
  id             uuid primary key default uuid_generate_v4(),
  user_id        uuid references auth.users(id),
  purpose        text not null,
  model          text not null,
  prompt_hash    text not null,
  prompt_preview text,                          -- ALREADY SCRUBBED, safe to store
  input_tokens   int, output_tokens int,
  latency_ms     int, cache_hit boolean default false,
  success        boolean default true, error text,
  created_at     timestamptz default now()
);

create table activity_log (
  id          uuid primary key default uuid_generate_v4(),
  user_id     uuid references auth.users(id),
  action      text not null,
  entity      text, entity_id uuid,
  metadata    jsonb,
  created_at  timestamptz default now()
);

-- ─────────────────────────────────────────────────────────────
-- VECTOR INDEXES
-- ─────────────────────────────────────────────────────────────
create index on competencies    using hnsw (embedding vector_cosine_ops);
create index on courses         using hnsw (embedding vector_cosine_ops);
create index on material_chunks using hnsw (embedding vector_cosine_ops);
create index on questions       using hnsw (embedding vector_cosine_ops);

-- ─────────────────────────────────────────────────────────────
-- SIMILARITY SEARCH FUNCTION
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

-- ─────────────────────────────────────────────────────────────
-- ROW LEVEL SECURITY
-- ─────────────────────────────────────────────────────────────
alter table profiles             enable row level security;
alter table competency_evidence  enable row level security;
alter table recommendations      enable row level security;
alter table assessments          enable row level security;
alter table enrollments          enable row level security;
alter table learning_materials   enable row level security;

create policy own_profile on profiles
  for select using (auth.uid() = id);
create policy own_profile_update on profiles
  for update using (auth.uid() = id);
create policy own_evidence on competency_evidence
  for select using (auth.uid() = user_id);
create policy own_recommendations on recommendations
  for select using (auth.uid() = user_id);
create policy own_assessments on assessments
  for all using (auth.uid() = user_id);
create policy own_enrollments on enrollments
  for all using (auth.uid() = user_id);
create policy trainer_materials on learning_materials
  for all using (auth.uid() = uploaded_by);

-- The FastAPI backend uses the SERVICE ROLE key and bypasses RLS for admin
-- aggregates. RLS is the second line of defence, not the only one.
