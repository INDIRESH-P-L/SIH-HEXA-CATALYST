# Honesty matrix

What is implemented, what is mocked, what is AI-generated, and what is not
built. Written so that anything claimed here can be checked in the running
system rather than taken on trust.

---

## The one rule

**This prototype does not have access to the official iGOT Karmayogi or NSSTA
APIs.** Obtaining it requires authorised credentials from the Capacity Building
Commission (iGOT) and from the academy (NSSTA).

The correct phrasing, used consistently in the code, the interface and this
repository:

> The catalogue layer is a mock service conforming to a documented interface.
> Production deployment requires authorised API credentials from the Capacity
> Building Commission (iGOT) and NSSTA.

**Verify it yourself:**

```bash
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/api/v1/catalogue/provider-info
```

```json
{ "provider": "mock", "is_mock": true, "record_count": 41,
  "description": "Mock catalogue service conforming to a documented interface. Production deployment requires authorised API credentials from the Capacity Building Commission (iGOT) and NSSTA." }
```

The interface renders that response as a visible badge — **"Mock catalogue — 41
sample records"** — on the recommendations page, every course page and the
administrator dashboard. It is not a tooltip and it is not hidden.

---

## Capability status

| Capability | Status | Where to check |
|---|---|---|
| Authentication, RBAC, row-level security | **Implemented** | `core/security.py`; `migrations/001` policies |
| Competency framework — 33 competencies, 4 domains | **Implemented** | `GET /competencies` |
| Job roles and requirement matrices — 5 roles, 50 rows | **Implemented** | `GET /job-roles/{id}/requirements` |
| Competency profile from role, education, experience, prior training | **Implemented** | `GET /auth/me`, `GET /catalogue/my-enrollments` |
| Evidence ledger, append-only, confidence-weighted | **Implemented** | `competency_evidence`, `user_competency` view |
| Skill-gap analysis | **Implemented — deterministic** | `GET /gaps/me`; every row carries its `derivation` |
| FRAC 4-point scale, used everywhere | **Implemented** | `scale` on the gap response |
| Course catalogue | **MOCKED** — 41 records behind a real interface | `GET /catalogue/provider-info` |
| Retrieval — semantic, lexical and tag, RRF-fused | **Implemented** | `retrievers` on every breakdown |
| Recommendation retrieve → rank → sequence | **Implemented — deterministic** (7 terms, prerequisite DAG, calendar) | `GET /recommendations/{id}/breakdown` |
| Recommendation explanations | **AI** — Groq Llama 3.3 70B | `explanation_source` field |
| MCQ generation from documents | **AI** — Groq GPT-OSS 20B, strict JSON | `POST /materials/{id}/generate` |
| MCQ validation gate | **Implemented — 10 checks, no model** | `questions.validation` |
| Quiz delivery and scoring | **Implemented — rule-based, difficulty-weighted** | `breakdown` on the submit payload |
| SME cut-scores per competency | **Implemented** | `competency_cut_scores` |
| Proctored vs practice evidence | **Implemented** — 0.90 vs 0.50 | `mode` and `confidence` on submit |
| Competency update | **Implemented — rule-based** | `services/m3_scoring.py` |
| Instant evaluation with explanations | **Implemented** | submit payload |
| Personalised feedback prose | **AI** — with template fallback | `feedback_source` field |
| Learner dashboard | **Implemented** | `GET /analytics/me` |
| Administrator dashboard | **Implemented** | `GET /analytics/admin/*` |
| LLM cache, audit trail, PII scrubber | **Implemented** | `llm_cache`, `llm_audit`, `tests/test_scrub.py` |
| Real iGOT enrolment | **Requires authorised API access** | `igot_provider.py` raises with the reason |
| NSSTA / TPAC nomination workflow | **State machine modelled**; the approvals themselves belong to people and are not wired | `nominations.state` |
| Government SSO (Parichay) | **Architecture only** | `core/security.decode_token` is the seam |
| Grounded assistant (M7) | **Implemented — AI**, over an approved corpus, with a refusal branch | `POST /assistant/ask` |
| Assistant grounding gate | **Implemented** — calibrated at 0.50, refuses below it | `retrieval_score` on every answer |
| Append-only event store | **Implemented** | `GET /analytics/admin/events` |
| k-anonymity on workforce aggregates | **Implemented** — threshold 5, suppressed cells marked not zeroed | `suppressed` on every cell and row |
| Training effectiveness — pre/post vs. a comparison group | **Implemented** | `GET /analytics/admin/training-effectiveness`, `net_delta` per programme |
| Framework versioning, sealed and immutable | **Implemented** | `framework_version` on the gap response |
| Activity layer (Position → Role → Activity → Competency) | **Implemented** | `GET /gaps/me/activities` |
| Evidence decay by class | **Implemented** — lowers confidence, never a level | `stale` on every gap row |
| Multilingual delivery (Bhashini) | **Not started** — seam only | — |
| Cross-encoder reranking for the assistant | **Not started** | — |
| OCR for scanned uploads | **Not started** | — |
| Adaptive testing, IRT calibration | **Not started** | — |
| Predictive skill forecasting | **Not started** — needs historical data | — |
| Collaborative filtering | **Not started** — needs enrolment history | — |
| Virtual labs | **Modelled as a course format only** | `learning_format: VIRTUAL_LAB` |

---

## Where a model is used, and where it is not

**Nothing that produces a number is produced by a model.**

### The model writes

- one explanatory sentence per recommendation;
- candidate question stems, options and explanations;
- the prose wrapper around a quiz result.

### Deterministic code decides

- the gap, its band and its priority;
- the ranking, diversity capping and calendar sequencing of every recommendation;
- whether the assistant is allowed to answer at all;
- whether a generated question is usable — all ten checks;
- the quiz score;
- the competency level change;
- which topics were weak;
- every figure on every dashboard.

When the model is unavailable, the product loses wording, never function. The
interface labels templated text **"Template (AI unavailable)"** rather than
presenting it as model output.

---

## Privacy

`ai/scrub.py` is a whitelist. `build_context()` raises on any key not on the
list; `assert_no_pii()` runs on every outbound prompt and system message.

The complete payload sent to the model for a recommendation:

```json
{ "job_role_title": "Statistical Officer",
  "competency_name": "SQL & Database Querying", "competency_code": "SQL",
  "current_level": 1, "required_level": 4, "gap": 3, "gap_band": "CRITICAL",
  "frac_current": "Awareness",
  "frac_required": "Subject Matter Expert",
  "years_experience_band": "3-5",
  "course_title": "SQL Fundamentals for Statistical Analysis",
  "course_level": 2, "course_duration_hours": 12,
  "course_format": "SELF_PACED", "provider": "iGOT Karmayogi — Capacity Building Commission" }
```

No name, no email, no employee code, no station, no identifier. Exact tenure is
coarsened to a band, because a precise tenure alongside a role and a station can
identify one officer.

This payload is stored at generation time and rendered in the interface behind
**"Context sent to the model — no personal data"**, so it is the payload that
actually left the process rather than a reconstruction.

`tests/test_scrub.py` feeds a complete officer record — name, email, employee
code, station, phone, Aadhaar, user id — through the context builder and asserts
none of it survives.

---

## Language used, and language avoided

| Do not say | Say |
|---|---|
| "Integrated with iGOT Karmayogi" | "Conforms to a documented catalogue interface; production requires authorised credentials" |
| "AI-powered skill-gap analysis" | "Rule-based skill-gap analysis" — and note that being deterministic is the point |
| "The assistant knows our methodology" | "The assistant answers only from material a trainer approved, and refuses otherwise" |
| "Adaptive testing" | "Difficulty-weighted scoring with item calibration in shadow; full IRT needs ~200 responses per item" |
| "AI grades your quiz" | "Scoring is arithmetic. The model writes the feedback." |
| "Government SSO" | "SSO-ready: token verification is one function" |
| "Predicts future skill needs" | "Predictive forecasting is future work; it needs historical workforce data" |
| "Validated by AI" | "Validated by ten deterministic checks" |

---

## Licence position

`pdfplumber` (MIT) is used for PDF extraction. **PyMuPDF is deliberately
excluded**: it is AGPL-3.0, and many government IT policies prohibit AGPL
dependencies. Every runtime dependency and its licence is tabulated in the
README.
