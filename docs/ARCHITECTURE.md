# System architecture

AI-Enabled Skill Intelligence Platform for India's Official Statistical System
(MoSPI · Data Informatics & Innovation Division).

Nine modules across five layers. **Deterministic core, AI at the edges — no
language model ever produces or adjusts a competency score.**

---

## 1. How the modules compose

```
SOURCES      Parichay/iGOT SSO   iGOT Karmayogi   NSSTA/TPAC   Uploaded material
                    │                  │              │              │
                    └──────────────────┴──────────────┴──────────────┘
                                       │
                    M6 · iGOT / NSSTA Integration Layer
                    anti-corruption boundary · normalise · sync · enrol / nominate
                                       │
FOUNDATION   M1 · Identity & Profile         M2 · Competency Framework
             position · cadre · history      FRAC graph + embeddings
                    └───────── blueprint ─────────┘
                                       │
MEASURE      M3 · Assessment Engine  ◀── verified items ──  M8 · AI Generator
             adaptive delivery + scoring      extract → generate → verify → review
                                       │
LEDGER       Competency evidence ledger        Normalised catalogue
             append-only · source · confidence · framework version
                                       │
DECIDE       M4 · Skill Gap Engine   M5 · Recommendation   M7 · Learning Assistant
             expected − current      retrieve → rank →      RAG over approved
             ranked                  sequence               corpus, cited
                                       │
OBSERVE      M9 · Analytics & Competency Tracking
             event store → rollups → learner + administrator dashboards
                                       │
                    └──── re-assessment triggers · re-ranking ────┘
```

Three claims hold this together:

1. **Every competency change enters through the evidence ledger**, tagged with
   source, confidence and framework version, so any number on screen can be
   derived on demand.
2. **M6 is the only component that knows an external schema.** When iGOT is
   unreachable the platform serves its local catalogue mirror and queues writes
   in an outbox.
3. **Scoring is reproducible arithmetic over stored responses.** Re-running the
   scorer must reproduce the number exactly; that is the audit test.

---

## 2. Process topology

```
┌──────────────────────────────────────────────────────────────────────────┐
│  REACT 18 · TYPESCRIPT · TAILWIND                            (browser)   │
│  Navigation grouped by architecture layer, not by menu convenience       │
│  Holds: the officer's own JWT. Nothing else.                             │
└───────────────────────────────┬──────────────────────────────────────────┘
                                │  HTTPS · Bearer JWT
┌───────────────────────────────▼──────────────────────────────────────────┐
│  FASTAPI BACKEND                       (single process, port 8000)       │
│  api/v1 · services/M1–M9 · ai/ (llm_client · embeddings · scrub)         │
│  Holds: GROQ_API_KEY, service-role key. Never leaves this process.       │
└──────┬────────────────────────┬──────────────────────────┬───────────────┘
       │ asyncpg                │ httpx + X-API-Key        │ HTTPS
┌──────▼──────────────┐  ┌──────▼───────────────┐  ┌───────▼──────────────┐
│ POSTGRESQL          │  │ MOCK iGOT / NSSTA    │  │ GROQ API             │
│ + pgvector (HNSW)   │  │ CATALOGUE  :8001     │  │ gpt-oss-20b (MCQ)    │
│ + GIN (tsvector)    │  │ separate process     │  │ llama-3.3-70b (prose)│
│ + RLS · 32 tables   │  │ 41 offerings         │  │ llama-3.1-8b (fallbk)│
└─────────────────────┘  └──────────────────────┘  └──────────────────────┘

FastEmbed (bge-small-en-v1.5, 384-dim, ONNX, CPU) runs IN-PROCESS.
```

The catalogue is a **separate process over HTTP with an API key**, not an
in-process module. The backend therefore deals with real latency, timeouts and
5xx responses — which is what makes the integration seam meaningful rather than
decorative.

---

## 3. The three seams

Each is a `typing.Protocol` with two implementations, selected by one
environment variable.

| Seam | Default (`local`) | Production |
|---|---|---|
| **Auth** | `auth.users` shim, PBKDF2-SHA256, HS256 minted here | Supabase Auth (GoTrue) over httpx |
| **Storage** | `backend/storage/materials/{user_id}/{uuid}.{ext}` | Supabase Storage, identical key layout |
| **Catalogue** | `MockProvider` → the service on :8001 | `IgotProvider` → raises `NotConfiguredError` |

**Token verification is a single function**, `core.security.decode_token`, used
identically in both auth modes. That function *is* the SSO-ready seam: adopting
Parichay changes the issuer, signing key and claims mapping there and nothing
else. No government SSO is integrated, and the platform says so.

`000_local_auth_shim.sql` creates `schema auth`, `auth.users` and `auth.uid()`
on plain PostgreSQL, so the schema — including every RLS policy — applies
verbatim in both deployments.

---

## 4. M1 · Identity & Employee Profile

Foundation. SSO claims, HR record, self-declaration and certificates compose
into one profile **with provenance**.

Four sources routinely disagree about a designation. Storing one value loses
the disagreement. `profile_attributes` stores each claim with its source,
confidence and effective date, so the resolver can choose, an administrator can
correct, and an officer can see exactly why their record reads as it does.
**Correction is appended as a new row; nothing is overwritten.**

**Position → Role is the most load-bearing field in the platform**: every
expected level, dashboard scope and nomination authority derives from it. An
officer without it gets a specific error saying so rather than an empty page.

DPDP Act 2023 controls: a consent artefact per stated purpose (`consent_records`),
and the PII boundary in §10.

---

## 5. M2 · Competency Framework

Foundation. Mirrors the FRAC model iGOT already uses.

### The graph

```
Position ──1:n──▶ Role ──1:n──▶ Activity ──n:m──▶ Competency
designation       a concrete     knowledge · skill · attribute
+ station         action          + required level 1–4
```

The **Activity** layer is what lets a gap be explained as "you cannot yet do
this part of your job" rather than as an abstract score. The Statistical
Officer has four: extract and tabulate, run a survey round, map indicators,
prepare a release.

### The FRAC 4-point scale — the only scale used anywhere

| | |
|---|---|
| **1** | Awareness |
| **2** | Application |
| **3** | Leveraging for decisions |
| **4** | Subject Matter Expert |

Level **0** is not part of FRAC. It means no evidence is on file, which is a
different statement from "the lowest rung" and is displayed differently.

### The four domains — 33 competencies

| Domain | Count |
|---|---|
| Statistical | 10 — sampling · survey design · national accounts · price · labour · agricultural · industrial · SDG indicators · metadata standards · data quality |
| Technical | 12 — SQL · Python · R · Stata · SPSS · SAS · GIS · data visualisation · AI/ML · cloud & big data · APIs · open data |
| Digital governance | 5 — cybersecurity · data privacy · digital signatures · government cloud · digital public infrastructure |
| Behavioural & managerial | 6 — leadership · communication · project management · ethics · decision making · change management |

### Versioning is not housekeeping

`framework_versions` is **immutable once sealed**. Without it a dashboard from
last quarter silently rewrites itself, and training effectiveness becomes
impossible to measure. There is no unseal operation.

An **emerging gap needs no forecasting model**: diff the sealed version an
officer was last assessed against with the current one, and add the
competencies of the next role up.

### Decay classes

Evidence goes stale at different rates. Decay never rewrites a level — it
lowers **confidence**, which raises priority and prompts re-assessment.

| Class | Window |
|---|---|
| Tools & platforms | 18 months |
| Regulatory & procedural | 12 months |
| Methodology | 36 months |
| Behavioural | does not decay |

---

## 6. M3 · Assessment Engine

Measurement. Adaptive delivery, deterministic scoring, evidence at the
confidence the delivery mode warrants.

### Scoring — difficulty-weighted, reproducible

```
score = 100 × Σ(wᵢ · cᵢ) / Σ(wᵢ)     w: easy 1, medium 2, hard 3
                                       Σ runs over items ATTEMPTED
```

Worked example — easy 3/4, medium 2/3, hard 1/3:

```
numerator   = (1×3) + (2×2) + (3×1) = 10
denominator = (1×4) + (2×3) + (3×3) = 19
score       = 52.6 %
```

The same paper reads **60 % unweighted**. The weighting correctly penalises
failure on the items that discriminate. Unattempted items enter neither side,
so abandoning an assessment does not deflate the items that were answered.

### Bands → FRAC, via SME cut-scores

Cut-scores are set **per competency** by a subject-matter panel (modified
Angoff), never as one global threshold: 60 % on sampling theory and 60 % on
spreadsheet hygiene are not the same statement about an officer.

The measured level is the level recorded. An officer demonstrating level 3 is
recorded at level 3, from a starting point of 1 — an assessment measures where
someone *is*, not how far they moved. Two guards remain: below five attempted
items nothing changes, and **levels never decrease**.

### Delivery

| Mode | Evidence confidence | Counts towards workforce dashboards |
|---|---|---|
| Proctored | 0.90 | yes |
| Practice | 0.50 | no |

Integrity: pool rotation (least-served items first), option shuffle, blueprint
recorded with the paper. Item difficulty is calibrated from live responses —
weighted CTT at launch, Elo in shadow, IRT viable at ~200 responses per item.

**The language model reads the response pattern *after* scoring to name a
misconception. It never produces or adjusts the number**, because a competency
score feeds nomination and posting decisions and must be defensible by anyone
holding the scoring rule.

---

## 7. M4 · Skill Gap Engine

Decision. Pure functions, zero I/O, fully unit-tested.

```
priority = (expected − current) × criticality × (2 − confidence) × horizon
```

**The `(2 − confidence)` term is the one that matters.** An unmeasured or
stale competency sits near 0.25 confidence, which nearly doubles its priority.
The engine surfaces *"we do not know whether this officer can do this"* as
urgent — the honest position, and the one that drives people into assessment.

| Band | Meaning |
|---|---|
| **CRITICAL** | Two or more levels below, on a competency the role marks as load-bearing |
| **SIGNIFICANT** | Below the level the role expects |
| **EMERGING** | New in this framework version, or needed in the next post up |
| **MET** | At expectation |
| **STRENGTH** | Above expectation — a candidate mentor |

A two-level shortfall in an *incidental* competency is SIGNIFICANT, not
CRITICAL. Otherwise the word stops meaning anything and every dashboard is red.

Criticality runs **1.0–3.0**. Horizon discounts a next-role requirement to 0.6
rather than ignoring it. Every row carries its full derivation, and the
interface shows it. Results snapshot per (officer, framework version, date), so
a dashboard from last quarter recomputes identically.

**Worked example.** Priya Sharma, SQL required 4, self-declared 1, criticality
2.2, confidence 0.25:

```
3 × 2.2 × 1.75 × 1.0 = 11.55   CRITICAL
```

After a proctored assessment at 82 % weighted → level 3 at confidence 0.90:

```
1 × 2.2 × 1.10 × 1.0 =  2.42   SIGNIFICANT
```

The priority collapses for two reasons at once: the level rose, *and* a guess
was replaced by evidence.

---

## 8. M5 · Recommendation Engine

Decision. Three stages. Collapsing them into one similarity search is the
common mistake — it produces recommendations that are topically plausible and
operationally useless.

### Stage 1 · Retrieve — ≈100 per gap

| Retriever | Good at |
|---|---|
| Dense (pgvector HNSW, cosine) | meaning |
| Lexical (BM25 over tsvector) | exact terms and rare tokens — SDMX, PLFS, GROUP BY |
| Tag match (competency code) | what the catalogue itself asserts |

Combined by **reciprocal rank fusion, k = 60**. Fusion needs only the ordering,
not scores that can be compared — normalising cosine similarity against a
term-frequency score requires assumptions that do not hold.

### Stage 2 · Rank — seven weighted terms

```
final = 0.30 · gap_priority          normalised against the largest open gap
      + 0.20 · semantic_similarity   cosine, competency ↔ course
      + 0.15 · level_fit             1.0 when course level == current + 1
      + 0.10 · prerequisites_met     1.0 when every prerequisite is held
      + 0.10 · effort_fit            can a serving officer absorb this?
      + 0.08 · department_priority   what the MDO is pushing
      + 0.07 · recency_language      freshness and whether they can read it
```

`level_fit` targets **current + 1**, not the required level: recommend the next
rung, not the top of the ladder. `effort_fit` is what stops a three-week
residential programme being proposed to an officer with four hours a month — it
outranks it rather than excluding it. Hard constraints pin mandatory courses and
drop completed ones; a diversity cap allows at most two per competency.

### Stage 3 · Sequence

Prerequisite **DAG topological sort** (a prerequisite the officer already holds
creates no edge), then **calendar placement**: dated NSSTA sessions are anchors,
self-paced iGOT courses fill around them against a monthly hour budget. A cycle
in a malformed catalogue degrades to the original order rather than raising.

Cold start, honestly: there is no collaborative-filtering signal on day one. The
launch system is content-based and rule-weighted, and the seam for a
collaborative term stays empty until M9 has real outcome data.

---

## 9. M6 · iGOT / NSSTA Integration Layer

Action. **One anti-corruption boundary — no external schema passes this line.**

Two adapters, because the two catalogues behave nothing alike. iGOT is a
REST/JSON platform synced with checkpoints; the NSSTA calendar is a published
document. One is **enrolled into** directly; the other requires a **nomination
a human approves**:

```
REQUESTED → SUPERVISOR_APPROVED → CBU_APPROVED → ACADEMY_CONFIRMED
                                 └── REJECTED at any step
```

Resilience: a circuit breaker opens after three consecutive failures and reads
fall back to the local mirror; writes queue in an **idempotent outbox** and are
retried. Unmapped external tags enter an administrator review queue rather than
being silently dropped — a dropped tag is a course that never surfaces.

**Design for the demonstration you will actually give.** Production iGOT
credentials are not obtainable during a hackathon. Because the adapter sits
behind an interface, the platform ships a fixture-backed implementation selected
by configuration, and the contract tests run against the `CatalogueProvider`
Protocol rather than either implementation. "Have you integrated?" then has a
real answer: contract, tests, fixture, and the switch.

---

## 10. M7 · Learning & AI Assistant

Action. Retrieval-grounded assistance over an **approved corpus** — cited, and
willing to say it does not know.

```
question → hybrid retrieve (dense + lexical, RRF) → rerank
        → GROUNDING GATE
           ├─ below threshold → refuse, and name the course that covers it
           └─ above           → answer from the passages, every claim cited
```

The assistant answers from the organisation's own approved material, not from
whatever the model happens to remember. That is what makes it usable for
methodology questions — sampling design, national accounts, price index
construction — where a confident wrong answer is worse than no answer.

**The grounding threshold is calibrated, not guessed.** bge-small produces a
narrow range: on-topic questions against this corpus score 0.58–0.75, while a
question with nothing to do with the material still scores ≈0.36 because both
texts are English prose. The threshold sits at **0.50**, above that noise floor.
A threshold set at the floor admits exactly the confident wrong answers the gate
exists to prevent.

**The refusal branch is a feature, not a failure mode.** Its rate is a quality
signal about the corpus, not about the model. Refusals are recorded as
deliberately as answers.

With no language model available the assistant quotes the corpus verbatim
rather than inventing prose — less fluent, still correct, still cited.

---

## 11. M8 · AI Assessment Generator

Measurement. **The verification gate is the whole point.**

```
upload → extract → clean → chunk → embed → select chunks
       → generate (gpt-oss-20b, strict json_schema, 3 items/chunk)
       → VERIFY — ten deterministic checks, no model
       → one retry with the failure reason → then dropped
       → trainer review gate → item bank → calibration
```

Generation is the easy half. An unverified LLM question bank fails in
predictable ways: two defensible answers, a distractor that is obviously wrong,
a key that is simply the longest option, a stem answerable from general
knowledge without the source. The critique loop catches those before a human
sees them.

| # | Check | Rule |
|---|---|---|
| 1 | option count | exactly 4, non-empty |
| 2 | option uniqueness | no two equal, case-insensitive |
| 3 | key range | 0 ≤ correct_index ≤ 3 |
| 4 | stem length | 15–300 characters |
| 5 | explanation | ≥20 chars, not a restatement of the key |
| 6 | banned options | no "all/none of the above", "both A and B" |
| 7 | length bias | key not >40 % longer than the mean distractor |
| 8 | near-duplicate | cosine <0.95 vs the bank *and* the current batch |
| 9 | difficulty | easy / medium / hard |
| 10 | grounding | ≥3 stem content words appear in the source passage |

**Traceability**: every published item carries its source document, page and the
exact span it was generated from.

**The trainer gate stays.** Automated verification raises the hit rate that
reaches a reviewer; it does not replace the reviewer, because a bad question in
a government assessment is a real cost. Rejected items are kept and reused as
negative examples, so the generator improves with each review round.

Three items per chunk, one chunk per request, is a token-budget decision: the
free tier allows roughly 8,000 tokens per minute.

---

## 12. M9 · Analytics & Competency Tracking

Observation. An event backbone, two dashboards, and the one metric that says
whether training worked.

```
producers → EVENT STORE → nightly rollups → marts → dashboards
            append-only    per officer,      competency mart
            actor·verb·    role, MDO         training-effectiveness mart
            object·time
```

One append-only stream is what makes every downstream number reconcilable.
**Dashboards read marts, marts rebuild from events, and an event is never
edited.** If a figure is disputed, the answer is to replay the events.

### Training effectiveness — the metric nobody else shows

Completion percentage answers *"did they attend"*. **Pre/post competency delta
answers *"did it work"*.**

```
delta = mean(post-programme level) − mean(pre-programme level), same officers
net   = delta − the same change among officers who did NOT attend
```

Computed per programme against a framework version — which is why M2 versioning
and the M4 snapshot exist at all. The comparison group is not a randomised
control, and the payload says so; it is the honest available counterfactual.

**This is the number a capacity-building unit actually needs**: a completion
percentage tells them people showed up; a pre/post delta per programme tells
them which programmes are worth the seats.

### Privacy guard

- **k-anonymity ≥ 5.** No aggregate over fewer than five officers. Suppressed
  cells say they were suppressed rather than reading as zero.
- **No individual score in any MDO-wide view.**
- **Practice attempts stay out of administrator dashboards** — real evidence for
  the learner at 0.50 confidence, noise for workforce planning.

### Predictive — honest about what it needs

Completion-risk modelling and skill-demand forecasting are documented seams, not
claims. Both need a term of history before they beat a simple heuristic.

---

## 13. The evidence ledger

No table stores a mutable "current level". A level is the most recent row in
`competency_evidence` for a (user, competency) pair, read through the
`user_competency` view.

| Source | Confidence |
|---|---|
| Self-declared | 0.25 |
| Practice assessment | 0.50 |
| iGOT course completion | 0.45 |
| NSSTA programme completion | 0.80 |
| Proctored assessment | 0.90 |
| Administrator override | 1.00 |

Because the ledger is append-only, every number the interface shows traces to
the row that produced it, and the progress line extends the instant an
assessment is submitted — the same row that changed the level adds the point.

---

## 14. Where AI is used, and where it is not

| Concern | Mechanism | Model? |
|---|---|---|
| Competency → course matching | bge-small embeddings + pgvector HNSW | embeddings, computed locally |
| Retrieval fusion | reciprocal rank | **No** |
| Recommendation ranking and sequencing | seven-term formula, DAG, calendar | **No** |
| Recommendation explanation | Groq llama-3.3-70b on anonymised context | **Yes** |
| Question generation | Groq gpt-oss-20b, strict JSON schema | **Yes** |
| Question validation | ten deterministic checks | **No** |
| Quiz scoring | difficulty-weighted arithmetic | **No** |
| Competency level update | SME cut-scores | **No** |
| Gap, band, priority | arithmetic | **No** |
| Weak-topic identification | weighted frequency count | **No** |
| Quiz feedback prose | Groq llama-3.3-70b, after scoring | **Yes** |
| Assistant answers | Groq, over retrieved approved passages, cited | **Yes** |
| Every dashboard figure | SQL aggregate | **No** |

**Nothing that produces a number is produced by a model.**

---

## 15. The AI governance layer

Every LLM call passes through `ai/llm_client.complete()`. Nothing else imports
the `groq` package, which makes the controls impossible to bypass by accident:

1. **Cache** — `sha256(prompt_version + model + purpose + system + prompt)`.
   This is what makes the demonstration work with the network disconnected.
2. **Retry** — one retry on rate-limit after 2 s, then a fall back to
   `llama-3.1-8b-instant`, which has separate headroom.
3. **Degrade** — total failure raises `LLMUnavailable`; every caller substitutes
   a deterministic template, and the interface labels it **"Template (AI
   unavailable)"** rather than passing it off as model output.
4. **Audit** — an `llm_audit` row on every path, cache hits included, so the
   trail records what was *asked*, not only what was billed.
5. **PII boundary** — `scrub.build_context()` is whitelist-only and raises on
   any unexpected key; `assert_no_pii()` runs on every outbound prompt *and*
   system message.

What actually reaches the model, verifiable at
`GET /recommendations/{id}/breakdown`:

```json
{ "job_role_title": "Statistical Officer", "competency_name": "SQL & Database Querying",
  "competency_code": "SQL", "current_level": 1, "required_level": 4, "gap": 3,
  "gap_band": "CRITICAL", "frac_current": "Awareness",
  "frac_required": "Subject Matter Expert", "years_experience_band": "3-5",
  "course_title": "SQL Fundamentals for Statistical Analysis", "course_level": 2 }
```

Exact tenure is coarsened to a band: a precise tenure alongside a role and a
station can identify one officer.

---

## 16. Resilience

| Failure | Behaviour |
|---|---|
| Groq unreachable / rate-limited / no key | Retry, fallback model, then templates. Ranking, scoring and levels unaffected. |
| Catalogue service down | Breaker opens after 3 failures; reads fall back to the mirror; writes queue in the outbox. `MOCK_FLAKY=true` demonstrates it. |
| Assistant corpus thin | Refuses and routes to the course that covers the topic. |
| Scanned PDF, no text layer | Material marked FAILED with an explanation. |
| Empty question bank | 409 explaining a trainer must approve items first. |
| Officer without a job role | Specific error naming Position → Role as the missing binding. |
| Supabase project idle 7 days | `/health/keepalive` + `scripts/keepalive.py`. |
| Supavisor transaction mode | Port 6543 detected ⇒ `NullPool` + `statement_cache_size=0`. |

---

## 17. Security

1. **Key custody** — `GROQ_API_KEY` and the service-role key exist only in the
   backend process.
2. **One verification function**, HS256, audience and issuer checked.
3. **RBAC read server-side** from `user_roles` on every request. A role claim
   inside a token is never trusted. Route guards in the interface are a
   convenience, not a boundary.
4. **Row-level security** on every user-scoped table.
5. **PII never reaches the model** — whitelist, assertion, and a test.
6. **Audit** — `llm_audit`, `activity_log`, and the append-only event store.
7. **Uploads** — extension and MIME validated, 10 MB cap, server-generated
   object key; the client filename is display metadata only.
8. **CORS** — explicit origin allowlist, never `*`.
9. **Answer keys** are never sent to the browser while an assessment is open.
10. **k-anonymity** on every workforce aggregate.

---

## 18. Scaling path

Honest notes, not claims:

- **Embeddings** are CPU-bound and in-process. Past a few hundred concurrent
  users, move FastEmbed behind its own service or batch on a worker.
- **Generation** is synchronous. At real trainer volumes it becomes a job queue
  — the one place the "no queues" rule would need revisiting.
- **HNSW** on 41 rows is a formality; it earns its place in the thousands.
- **The rollup job** runs on demand here. In production it is nightly, off the
  event stream, which is what the marts exist for.
- **RLS** is currently the second line of defence behind a service-role
  connection. Production would run user-scoped connections so RLS is primary.
- **A cross-encoder reranker** for M7 is the documented upgrade; a second model
  on the request path is a cost this prototype has not earned.

---

## 19. What is not built

| Capability | Status | Prerequisite |
|---|---|---|
| Live iGOT Karmayogi API | **Not integrated** | Authorised credentials from the Capacity Building Commission |
| NSSTA approval workflow | State machine modelled; approvals not wired to people | Academy process integration |
| Parichay / government SSO | Architecture only | Identity provider onboarding |
| Multilingual delivery (Bhashini) | Seam only | Translation and ASR/TTS service |
| Virtual labs | Modelled as a course format | Containerised sandbox infrastructure |
| Adaptive testing / IRT calibration | Elo shadow only | ~200 responses per item |
| Predictive skill forecasting | Not started | Historical workforce data |
| Collaborative filtering | Seam kept empty | Real enrolment and outcome history |
| OCR for scanned uploads | Not started | OCR service |
| Cross-encoder reranking | Not started | Model hosting budget |
