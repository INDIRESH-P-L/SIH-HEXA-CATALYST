# Demonstration runbook

Target: **4–4.5 minutes**. Rehearse it twice, once with the network disconnected.

---

## Before you start

```bash
# Start PostgreSQL (or use Supabase cloud DB in backend/.env)
./scripts/start_local_db.sh
cd mock-catalogue && uvicorn main:app --port 8001
cd backend && uvicorn app.main:app --reload
cd frontend && npm run dev
```

Then, from the repository root:

```bash
python scripts/reset_demo.py       # Priya back to SQL level 1, CRITICAL gap
python scripts/verify_system.py    # 71/71 before you walk on stage
```

If a Groq key is configured, warm the cache so nothing depends on the network:

```bash
cd backend && python -m app.seed.seed_demo_cache
```

**Checklist**

- [ ] `GET /health` shows database, embeddings and catalogue all `ok`
- [ ] `scripts/verify_system.py` exits 0
- [ ] Priya's SQL gap reads **1 / 4 · CRITICAL**, priority 11.55
- [ ] Browser zoom at 100%, one tab, `localhost:5173`
- [ ] `Sampling_Methods_Primer.pdf` ready but unopened, for the cold-generation ask

---

## The script

| Time | Screen | Say |
|---|---|---|
| **0:00** | Login | "Priya Sharma, Statistical Officer at MoSPI, four years in post." |
| **0:20** | Dashboard | "Her competency profile against her job role — eight competencies, on the FRAC four-point scale. SQL sits at Awareness where the role needs Subject Matter Expert." |
| **0:45** | My competencies | "Gap analysis on the FRAC four-point scale. SQL is CRITICAL at priority 11.55. Click it — that is 3 levels short, times a criticality of 2.2, times 1.75 because the evidence is a self-declaration we have never verified. **The platform treats not knowing as urgent.** This is arithmetic, not machine learning." |
| **1:05** | Recommendations → Get recommendations | "Five ranked courses. Semantic retrieval over the catalogue, then a deterministic ranking formula." |
| **1:20** | Show score breakdown | "Seven weighted terms, and you can add the column up. Three retrievers fused by reciprocal rank — a dense model cannot see GROUP BY, a text index cannot see meaning. Level fit targets her **next** rung, not the top of the ladder. And stage three places it on a calendar against a realistic monthly hour budget." |
| **1:35** | Context sent to the model | "This is the exact payload the language model received. Job role, competency, levels, course. **No name, no email, no employee code.** Tenure is coarsened to a band. It is stored at generation time, so this is what actually left the process." |
| **1:55** | Open a course | "The **Mock catalogue — 41 sample records** badge. We do not have iGOT API access; production needs authorised credentials from the Capacity Building Commission. That badge is rendered from a live endpoint you can call yourself." |
| **2:10** | Sign in as trainer → Trainer console | "The trainer uploads a real handout." Upload `SQL_Fundamentals_for_Statistical_Analysis.pdf`, competency **SQL & Database Querying**. |
| **2:25** | Generate | "Extraction, cleaning, chunking, embedding, then GPT-OSS-20B with a strict JSON schema. Three items per chunk to stay inside the rate limit." |
| **2:40** | Validation report | "**This is the important screen.** The model wrote the questions. Ten deterministic checks decided which survive — length bias on the answer, near-duplicates, and grounding: at least three content words of the stem must appear in the source passage. No model votes on question quality." |
| **3:00** | Sign in as Priya → Assessments | "She takes the quiz." Answer through it. |
| **3:15** | Submit | "82.9% weighted. The same paper reads 85% unweighted — the weighting penalises the hard items she missed. Open the arithmetic; it reproduces from stored responses. The model never touches the number." |
| **3:25** | Result screen | "SQL moves 1 → 3 — cut-scores measure where she *is*, not how far she moved. Awareness → Leveraging for decisions. CRITICAL → SIGNIFICANT. And priority collapses 11.55 → 2.42, because the level rose *and* a guess was replaced by evidence at 0.90 confidence." |
| **3:40** | Same screen, scroll | "And a **new recommendation** — the top course changed, because level fit now targets level 4. All of that happened inside the one submit request. **The loop has closed.**" |
| **3:50** | Learning assistant | "Ask it something the corpus covers — cited, page-level. Now ask it the capital of France: it **refuses** and names the course instead. A confident wrong answer about sampling methodology is worse than none." |
| **4:05** | Sign in as admin → Workforce analytics | "Gap frequency, the role-by-competency heatmap with cells under five officers suppressed, pre/post delta net of a comparison group, and the append-only event stream every figure rebuilds from." |
| **4:20** | — | "Deterministic where it must be, AI where it helps, and honest about which is which." |

---

## The four sentences that matter

1. "Gap analysis and scoring are **rule-based, and that is a strength** — nothing that affects an officer's record is decided by a model. The scorer is a pure function of stored responses; re-run it and you get the same number."
2. "This is the exact anonymised payload that went to the model. **No personal data leaves the process.**"
3. "The catalogue is a **mock behind a documented interface**. Production needs authorised iGOT credentials. Call `/catalogue/provider-info` and check."
4. "The assistant **refuses** when the approved corpus does not cover a question. That branch is a feature — its rate tells you about the corpus, not the model."

---

## Anticipated questions

**"Is this really integrated with iGOT?"**
No, and we do not claim it is. It is a mock service conforming to a documented
interface — a separate process, over HTTP, with an API key, artificial latency
and simulated outages. The contract tests run against the `CatalogueProvider`
protocol, not the mock, so a real provider drops in without touching anything
else. Production requires authorised credentials from the Capacity Building
Commission.

**"How do you know the generated questions are any good?"**
We do not trust the model to tell us. Ten deterministic checks decide, and the
report shows which check rejected each dropped item. The strongest is grounding:
at least three content words of the stem must appear in the source passage, so a
question written from the model's own prior knowledge rather than from the
uploaded handout is rejected.

**"What if the language model is unavailable?"**
The product loses wording, not function. Ranking, scoring, levels and gaps are
all deterministic. Explanations and feedback fall back to templates, and the
interface labels them "Template (AI unavailable)" rather than passing them off
as model output. We rehearse with the network disconnected.

**"What about personal data?"**
`ai/scrub.py` is a whitelist that raises on anything unexpected, plus an
assertion on every outbound prompt. `tests/test_scrub.py` feeds a full officer
record in and asserts no name, email, employee code, phone or Aadhaar survives.
We can run that test now.

**"Can it generate from something it has not seen?"**
Yes — `Sampling_Methods_Primer.pdf` was deliberately held back. Upload it live.

**"Is it secure enough for government?"**
Prototype depth, honestly. Real: JWT verification through one function, RBAC
read server-side from the database, row-level security, keys server-side only,
audit logging, upload validation, an explicit CORS allowlist, and k-anonymity
on every workforce aggregate. Not done: penetration testing, formal STQC
certification, and user-scoped database connections so row-level security is
the primary control rather than the second line.

**"How would this scale?"**
Embeddings are CPU-bound and in-process — past a few hundred concurrent users
they move behind their own service. Generation is synchronous and would become a
job queue at real trainer volumes. Those are the two honest bottlenecks; the
scaling notes are in `docs/ARCHITECTURE.md`.

---

## If something breaks

| Symptom | Fix |
|---|---|
| Catalogue badge says unreachable | The mock service is down. Recommendations still work from the local mirror — say so, it demonstrates the circuit breaker. |
| Generation returns nothing | Rate limit. Say so plainly and show the pre-seeded question bank; the loop still runs. |
| Backend port already bound | `python scripts/stop_backend.py --port 8000` |
| Data looks wrong mid-demo | `python scripts/reset_demo.py`, then reload |
| Everything is wrong | `python scripts/apply_migrations.py --reset && python scripts/seed_all.py --questions --corpus` |

Never improvise a claim under pressure. If something does not work, say what it
would do and why it is not doing it. The honesty is the differentiator.


---

## If a judge asks about the architecture

Open **System architecture** in the sidebar. It renders the nine modules across
five layers from live endpoints — the competency count, the catalogue size, the
corpus size and the active seams are read from the running system, not typed
into a slide. Each module card opens to the design decision behind it.

The three sentences worth having ready:

- "Deterministic core, AI at the edges. No language model ever produces or
  adjusts a competency score, because that score feeds nomination and posting
  decisions and has to be defensible by anyone holding the scoring rule."
- "Every competency change enters through an append-only evidence ledger tagged
  with source, confidence and framework version, so any number on screen can be
  derived on demand."
- "M6 is the only component that knows an external schema. When iGOT is
  unreachable we serve our own mirror and queue the writes."
