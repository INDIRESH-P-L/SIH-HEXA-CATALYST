# AI-Enabled Skill Intelligence Platform

Competency profiling, deterministic skill-gap analysis, semantic course
recommendation and AI-generated assessments for officials in India's Official
Statistical System.

**Ministry of Statistics and Programme Implementation · Data Informatics &
Innovation Division · Smart India Hackathon 2026**

---

## What it does

An officer's competencies are profiled against their job role, gaps are
computed, courses are recommended from the iGOT Karmayogi and NSSTA catalogues,
quizzes are generated from uploaded training material with a language model,
scored by rule, and the resulting competency change feeds straight back into the
next recommendation.

That last sentence is the product. `POST /assessments/{id}/submit` scores the
quiz, writes the evidence, updates the level, recomputes the gap and regenerates
the recommendation batch — in one transaction, in one request.

```
Officer profile → Competency assessment → Skill-gap analysis → AI recommendation
   → iGOT / NSSTA catalogue → Personalised learning → AI MCQ generation → Quiz
   → Deterministic scoring → Competency update → Recomputed gap → Next recommendation ⟲
```

Nine modules across five layers — sources, foundation, measure, decide,
observe. **Deterministic core, AI at the edges: no language model ever produces
or adjusts a competency score.** Proficiency uses iGOT Karmayogi's **FRAC
4-point scale** throughout.

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full system design.

---

## Running it

Four processes. The first three are required.

### 0 · Prerequisites

Python **3.11** (not 3.14 — FastEmbed's ONNX runtime has no 3.14 wheels),
Node 18+, Docker Desktop.

### 1 · Database

```bash
docker compose up -d db
```

PostgreSQL 16 with pgvector, on host port **5433** to avoid colliding with a
local 5432.

### 2 · Backend

```bash
cd backend
py -3.11 -m venv .venv
.venv/Scripts/python -m pip install -r requirements-dev.txt   # Windows
# .venv/bin/python -m pip install -r requirements-dev.txt     # Unix
cp ../.env.example .env
```

Then, from the repository root:

```bash
python scripts/apply_migrations.py
python scripts/make_sample_docs.py
```

### 3 · Mock catalogue — its own process, port 8001

```bash
cd mock-catalogue && uvicorn main:app --port 8001
```

### 4 · Seed, then start the backend

```bash
python scripts/seed_all.py --questions --corpus
```

```bash
cd backend && uvicorn app.main:app --reload
```

### 5 · Frontend

```bash
cd frontend && npm install && npm run dev
```

Open **http://localhost:5173**. API documentation is at
**http://localhost:8000/docs**.

### Demo accounts

| Email | Password | Role |
|---|---|---|
| `priya.sharma@mospi.gov.in` | `Demo@2026` | Statistical Officer — the demo officer |
| `anand.desai@nssta.gov.in` | `Demo@2026` | Assistant Director (Training) — trainer |
| `admin@mospi.gov.in` | `Demo@2026` | System Administrator — admin |

Also seeded: a Senior Statistical Officer, a Deputy Director, a Data Scientist
and a Field Supervisor, so the workforce dashboard has range.

---

## Verifying it

```bash
cd backend && pytest -q
```

216 tests over the deterministic core: the gap engine and its priority
formula, difficulty-weighted scoring and SME cut-scores, retrieval fusion,
ranking, prerequisite sequencing and calendar placement, all ten validation
checks, the PII scrubber, chunking, the LLM client's cache and fallback
behaviour, and the catalogue contract.

With the whole system running:

```bash
python scripts/verify_system.py
```

71 checks that walk the live HTTP surface the way the demonstration does, one
per capability the architecture and the problem statement call for. Exit code 0
when all pass.

Between rehearsals:

```bash
python scripts/reset_demo.py
```

Clears what a demo run produced and returns Priya Sharma to SQL level 1, a
CRITICAL gap. Keeps the framework, the users, their baselines, the catalogue,
the question bank, the seeded prior-training history and the approved corpus.

---

## What is real, what is mocked, what is AI

The honest version, also in [`docs/HONESTY_MATRIX.md`](docs/HONESTY_MATRIX.md).

| Capability | Status |
|---|---|
| Auth, RBAC, row-level security | Implemented |
| Competency framework — 33 competencies, 4 domains, 5 roles, 18 activities | Implemented |
| FRAC graph: Position → Role → Activity → Competency | Implemented |
| Immutable, sealed framework versions | Implemented |
| Competency profile with provenance (source, confidence, effective date) | Implemented |
| Skill-gap analysis | Implemented — **deterministic**, not machine learning |
| Evidence decay by class | Implemented — lowers confidence, never rewrites a level |
| Course catalogue | **Mocked** — 41 records behind a real interface |
| Semantic + lexical + tag retrieval, RRF fusion | Implemented |
| Recommendation ranking and sequencing | Implemented — **deterministic**, 7 terms + DAG + calendar |
| Recommendation explanations | **AI** — Groq Llama 3.3 70B on anonymised context |
| MCQ generation from uploaded documents | **AI** — Groq GPT-OSS 20B, strict JSON |
| MCQ validation gate | Implemented — **10 deterministic checks, no model** |
| Difficulty-weighted scoring, SME cut-scores | Implemented — **rule-based, no model** |
| Grounded assistant with citations and a refusal branch | Implemented — **AI**, over an approved corpus |
| Learner and administrator dashboards | Implemented |
| Append-only event store, rollup marts, k-anonymity | Implemented |
| Training effectiveness vs. a comparison group | Implemented |
| Real iGOT enrolment | **Requires authorised API access** |
| NSSTA nomination workflow | **State machine only** — approvals need academy integration |
| Government SSO (Parichay) | Architecture only, not integrated |
| Multilingual delivery, virtual labs, IRT, skill forecasting | Future work |

**The catalogue layer is a mock service conforming to a documented interface.
Production deployment requires authorised API credentials from the Capacity
Building Commission (iGOT) and NSSTA.** The interface says so on every screen
that shows catalogue data, and `GET /api/v1/catalogue/provider-info` returns
`{"provider": "mock", "is_mock": true}` so the claim can be checked directly.

---

## Running without a Groq key

Everything works. `llm_client` raises `LLMUnavailable`, every caller substitutes
a deterministic template, and the interface labels the result
**"Template (AI unavailable)"** rather than passing it off as model output. The
seeded question bank keeps the assessment loop demonstrable.

Add `GROQ_API_KEY` to `backend/.env` and the AI paths activate with no code
change. To make the demonstration survive a dead network:

```bash
cd backend && python -m app.seed.seed_demo_cache
```

---

## Licences

Every runtime dependency and why it was chosen.

| Package | Licence | Role |
|---|---|---|
| FastAPI | MIT | HTTP framework |
| Uvicorn | BSD-3-Clause | ASGI server |
| Pydantic | MIT | Request/response models |
| SQLAlchemy | MIT | ORM, async |
| asyncpg | Apache-2.0 | PostgreSQL driver |
| pgvector | PostgreSQL Licence | Vector type and HNSW index |
| python-jose | MIT | JWT verification |
| groq | Apache-2.0 | LLM client |
| FastEmbed | Apache-2.0 | Local embeddings (bge-small-en-v1.5) |
| **pdfplumber** | **MIT** | **PDF text extraction** |
| python-docx | MIT | DOCX extraction |
| python-pptx | MIT | PPTX extraction |
| httpx | BSD-3-Clause | Catalogue and GoTrue client |
| React | MIT | Interface |
| Tailwind CSS | MIT | Design tokens |
| Recharts | MIT | Charts |
| IBM Plex | SIL OFL 1.1 | Typefaces, self-hosted |

**PyMuPDF is deliberately excluded.** It is AGPL-3.0, and many government IT
policies prohibit AGPL dependencies. pdfplumber (MIT) does the same job.

---

## Deploying against Supabase

The platform runs on local PostgreSQL by default and needs no credentials. To
switch to the Supabase stack, change environment variables only:

```ini
AUTH_MODE=supabase
STORAGE_MODE=supabase
SUPABASE_URL=https://<ref>.supabase.co
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
SUPABASE_JWT_SECRET=...
DB_URL=postgresql+asyncpg://postgres.<ref>:<pw>@aws-0-<region>.pooler.supabase.com:5432/postgres
```

Use the **Supavisor pooler**, not `db.<ref>.supabase.co:5432` — the direct
endpoint is IPv6-only and times out on most laptops and campus networks. Session
mode (5432) is right for a laptop-hosted demo. Transaction mode (6543) is
detected automatically and switches the engine to `NullPool` with the
prepared-statement cache disabled.

The migration runner skips the local auth shim in Supabase mode, because GoTrue
already owns that schema. `001_initial_schema.sql` is unchanged between the two.

---

## Repository layout

```
backend/     FastAPI application, migrations, seeds, 216 tests
frontend/    React 18 + TypeScript + Tailwind, strict mode
mock-catalogue/  Separate FastAPI service on :8001, 41 offerings
scripts/     migrations · seeding · reset · verification · keep-alive
docs/        ARCHITECTURE · HONESTY_MATRIX · DEMO_RUNBOOK
```
