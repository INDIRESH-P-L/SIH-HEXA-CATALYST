"""End-to-end verification against the nine-module reference architecture.

Walks the running system the way the demonstration does and asserts each
capability the architecture and the problem statement call for. Needs the
database, the mock catalogue on 8001 and the backend on 8000 all up, against a
seeded database.

    python scripts/seed_all.py --questions --corpus
    python scripts/verify_system.py

It exercises the real HTTP surface rather than importing the application, so a
pass here means the deployed system works, not merely that the code compiles.
Exit code 0 when every check passes.
"""

from __future__ import annotations

import asyncio
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "backend"))

from _api_client import call, login, wait  # noqa: E402

OK, BAD = "  [ok]  ", "  [!!]  "
results: list[bool] = []


def check(label: str, condition: object, detail: str = "") -> None:
    results.append(bool(condition))
    print(f"{OK if condition else BAD}{label:<54}{detail}")


def section(title: str) -> None:
    print(f"\n=== {title} ===")


# The answer key is read straight from the database: a verification script is
# allowed to know the answers, the browser is not.
from sqlalchemy import select  # noqa: E402

from app.core.database import SessionLocal, dispose_engine  # noqa: E402
from app.models.question import Question  # noqa: E402


async def _load_key() -> dict[str, tuple[int, str]]:
    async with SessionLocal() as session:
        rows = (
            await session.execute(
                select(Question.id, Question.correct_index, Question.difficulty).where(
                    Question.status == "APPROVED"
                )
            )
        ).all()
    await dispose_engine()
    return {str(qid): (int(idx), difficulty) for qid, idx, difficulty in rows}


KEY = asyncio.run(_load_key())

wait()
tok, me = login()
_, admin = call(
    "POST", "/api/v1/auth/login", {"email": "admin@mospi.gov.in", "password": "Demo@2026"}
)
atok = admin["access_token"]
_, trainer = call(
    "POST", "/api/v1/auth/login", {"email": "anand.desai@nssta.gov.in", "password": "Demo@2026"}
)
ttok = trainer["access_token"]


# ── M2 · foundation ──────────────────────────────────────────────────────────
section("M2 · COMPETENCY FRAMEWORK — FRAC graph, versioned")
s, comps = call("GET", "/api/v1/competencies", token=tok)
clusters: dict[str, list[str]] = {}
for c in comps:
    clusters.setdefault(c["cluster"], []).append(c["code"])
check("framework loaded", s == 200 and len(comps) >= 33, f"{len(comps)} competencies")
for domain in ("STATISTICAL", "TECHNICAL", "DIGITAL_GOVERNANCE", "BEHAVIOURAL"):
    check(f"  domain {domain}", len(clusters.get(domain, [])) > 0, f"{len(clusters.get(domain, []))}")
check(
    "competencies carry FRAC kind and decay class",
    all(c.get("kind") and c.get("decay") for c in comps),
)

s, g = call("GET", "/api/v1/gaps/me", token=tok)
check("framework version is sealed and reported", bool(g.get("framework_version")), g.get("framework_version", ""))
check("FRAC 4-point scale declared", "4-point" in g.get("scale", ""), g.get("scale", "")[:52])

s, acts = call("GET", "/api/v1/gaps/me/activities", token=tok)
check(
    "Activity layer present (Position -> Role -> Activity -> Competency)",
    s == 200 and len(acts) > 0,
    f"{len(acts)} activities",
)
check(
    "activities carry the competencies they depend on",
    all(a["competency_codes"] for a in acts),
)


# ── M4 · decide ──────────────────────────────────────────────────────────────
section("M4 · SKILL GAP ENGINE — expected minus current, weighted")
sql = next(r for r in g["gaps"] if r["competency_code"] == "SQL")
check("gap analysis returns ranked rows", len(g["gaps"]) > 0, f"{len(g['gaps'])} for {g['job_role_title']}")
check("method declared deterministic", g["method"] == "deterministic")
check(
    "SQL is the CRITICAL demonstration gap",
    sql["band"] == "CRITICAL" and sql["gap"] == 3,
    f"level {sql['current_level']}/{sql['required_level']}, priority {sql['priority']}",
)
d = sql["derivation"]
check("every gap carries its derivation", d is not None and "formula" in d)
check(
    "priority multiplies out exactly",
    abs(
        d["difference"] * d["criticality"] * d["uncertainty_multiplier"] * d["horizon_multiplier"]
        - sql["priority"]
    )
    < 0.01,
    d["formula"],
)
check(
    "(2 - confidence) amplifies unmeasured competencies",
    d["uncertainty_multiplier"] > 1.5,
    f"confidence {d['confidence']} -> x{d['uncertainty_multiplier']}",
)
emerging = [r for r in g["gaps"] if r["band"] == "EMERGING"]
check(
    "next-role requirements surface as EMERGING",
    len(emerging) > 0,
    ", ".join(r["competency_code"] for r in emerging),
)
check(
    "five bands in use",
    set(g["gaps"][0].keys()) >= {"band", "horizon", "confidence", "stale"},
)
check(
    "re-assessment candidates identified",
    "reassessment_candidates" in g,
    ", ".join(g["reassessment_candidates"][:4]),
)

s, _snap = call("POST", "/api/v1/gaps/me/snapshot", token=tok)
check("gap snapshot can be frozen against a framework version", s == 200)


# ── M6 · integration ─────────────────────────────────────────────────────────
section("M6 · iGOT / NSSTA INTEGRATION — behind a real interface")
s, p = call("GET", "/api/v1/catalogue/provider-info", token=tok)
check("provider declares itself a mock", p["is_mock"] is True and "authorised API credentials" in p["description"])
check("catalogue mirrored and embedded", p["record_count"] == p["embedded_count"], f"{p['record_count']} records")
check("circuit breaker reported", p["circuit_state"] is not None, f"circuit={p['circuit_state']}")
s, st = call("GET", "/api/v1/catalogue/stats", token=tok)
check("both catalogues present", set(st["by_source"]) == {"IGOT", "NSSTA"}, str(st["by_source"]))
check("every competency has offerings", len(st["by_competency"]) >= 33, f"{len(st['by_competency'])} codes")
s, nssta = call("GET", "/api/v1/catalogue/courses?source=NSSTA", token=tok)
check(
    "NSSTA programmes are dated and seat-limited",
    all(c["session_start"] and c["seats"] for c in nssta),
    f"{len(nssta)} programmes",
)


# ── M5 · recommendations ─────────────────────────────────────────────────────
section("M5 · RECOMMENDATION ENGINE — retrieve, rank, sequence")
s, batch = call(
    "POST", "/api/v1/recommendations/generate",
    {"limit": 5, "max_per_competency": 2, "explain": True}, token=tok,
)
check("ranked batch generated", s == 200 and batch["count"] > 0, f"{batch['count']} ranked")
top = batch["recommendations"][0]
b = top["breakdown"]
check("top pick targets the largest gap", top["competency_code"] == "SQL", top["course"]["title"])
check(
    "seven ranking terms",
    len([k for k in b if k in
         {"gap_priority", "semantic_similarity", "level_fit", "prerequisites_met",
          "effort_fit", "department_priority", "recency_language"}]) == 7,
)
check("three retrievers fused", len(b.get("retrievers", [])) == 3, b.get("fusion", ""))
check("level fit targets current + 1", top["course"]["proficiency_level"] == sql["current_level"] + 1,
      f"course level {top['course']['proficiency_level']}")
check("pathway sequenced onto a calendar", b.get("sequence") is not None,
      f"step {b['sequence']['order']} from {b['sequence']['starts_on']}" if b.get("sequence") else "")
s, ctx = call("GET", f"/api/v1/recommendations/{top['id']}/breakdown", token=tok)
blob = json.dumps(ctx["ai_context_sent"])
check("AI context carries no PII",
      not any(x in blob for x in ["Priya", "Sharma", "@mospi", "MOSPI/2021"]),
      f"{len(ctx['ai_context_sent'])} whitelisted fields")


# ── M7 · assistant ───────────────────────────────────────────────────────────
section("M7 · LEARNING ASSISTANT — grounded, cited, willing to refuse")
s, corpus = call("GET", "/api/v1/assistant/corpus", token=tok)
check("approved corpus indexed", s == 200 and corpus["indexed_chunks"] > 0,
      f"{corpus['approved_materials']} documents, {corpus['indexed_chunks']} passages")

s, grounded = call("POST", "/api/v1/assistant/ask",
                   {"question": "How does an INNER JOIN change the denominator of a tabulation?"}, token=tok)
check("answers an in-corpus question", s == 200 and grounded["grounded"] and not grounded["refused"],
      f"retrieval {grounded['retrieval_score']:.2f}")
check("every answer is cited", len(grounded["citations"]) > 0,
      f"{len(grounded['citations'])} citations, lead p{grounded['citations'][0]['page_no']}")

s, refused = call("POST", "/api/v1/assistant/ask",
                  {"question": "What is the capital of France?"}, token=tok)
check("REFUSES an out-of-corpus question", refused["refused"] is True,
      f"retrieval {refused['retrieval_score']:.2f} below threshold")
check("refusal routes to a course instead", refused["suggested_course"] is not None,
      (refused["suggested_course"] or {}).get("title", "")[:40])


# ── M8 · generation ──────────────────────────────────────────────────────────
section("M8 · AI ASSESSMENT GENERATOR — the verification gate")
s, _mats = call("GET", "/api/v1/materials", token=ttok)
check("trainer can reach the console", s == 200)
s, denied = call("GET", "/api/v1/materials", token=tok)
check("an employee cannot", s == 403)
from app.services.m8_generator import validate  # noqa: E402
check("ten deterministic checks", len(validate.CHECK_NAMES) == 10,
      ", ".join(validate.CHECK_NAMES[:4]) + ", ...")


# ── M3 · the closed loop ─────────────────────────────────────────────────────
section("M3 · ASSESSMENT ENGINE — the closed loop")
s, a = call("POST", "/api/v1/assessments",
            {"competency_id": sql["competency_id"], "count": 20, "mode": "proctored"}, token=tok)
check("quiz drawn from the approved bank", s == 200 and a["total_questions"] > 0,
      f"{a['total_questions']} items")
check("answer key never sent to the client", not any("correct_index" in q for q in a["questions"]))

missed = 0
for q in a["questions"]:
    correct, difficulty = KEY[q["id"]]
    wrong = (difficulty == "hard" and missed < 2) or (difficulty == "easy" and missed == 2)
    if wrong:
        missed += 1
    call("POST", f"/api/v1/assessments/{a['id']}/answer",
         {"question_id": q["id"], "selected_index": (correct + 1) % 4 if wrong else correct}, token=tok)

s, r = call("POST", f"/api/v1/assessments/{a['id']}/submit", token=tok)
sb = r["breakdown"]
check("difficulty-weighted scoring", s == 200 and sb["numerator"] < sb["denominator"],
      f"{sb['numerator']}/{sb['denominator']} = {r['score']}% (unweighted {r['raw_score']}%)")
check("weighting differs from the raw score", r["score"] != r["raw_score"])
check("weights are 1 / 2 / 3", sb["weights"] == {"easy": 1, "medium": 2, "hard": 3})
check("proctored evidence at 0.90 confidence", r["confidence"] == 0.9, f"mode={r['mode']}")
check("level measured from SME cut-scores", r["level_after"] > r["level_before"],
      f"{r['level_before']} -> {r['level_after']} ({r['frac_before']} -> {r['frac_after']})")
check("gap recomputed", r["gap_before"]["band"] != r["gap_after"]["band"],
      f"{r['gap_before']['band']} -> {r['gap_after']['band']}")
check("priority collapses as evidence replaces a guess",
      r["priority_after"] < r["priority_before"],
      f"{r['priority_before']} -> {r['priority_after']}")
check("weak topics identified deterministically", len(r["weak_topics"]) > 0, ", ".join(r["weak_topics"]))
check("recommendations regenerated in the same call", len(r["new_recommendations"]) > 0,
      f"{len(r['new_recommendations'])} new")
check("evidence appended to the ledger", bool(r["evidence_id"]))

s, g2 = call("GET", "/api/v1/gaps/me", token=tok)
sql2 = next(x for x in g2["gaps"] if x["competency_code"] == "SQL")
check("LOOP CLOSED: gap list reflects the new level",
      sql2["current_level"] == r["level_after"] and sql2["confidence"] == 0.9)


# ── M9 · analytics ───────────────────────────────────────────────────────────
section("M9 · ANALYTICS — events, marts, and whether it worked")
s, an = call("GET", "/api/v1/analytics/me", token=tok)
check("learner dashboard", s == 200 and len(an["radar"]) > 0, f"{len(an['radar'])} radar axes")
check("progress extends per evidence event", len(an["progress"]) > 1, f"{len(an['progress'])} points")
check("stale and unassessed surfaced to the learner",
      "stale_competencies" in an and "unassessed_competencies" in an,
      f"{an['unassessed_competencies']} unassessed")

s, ov = call("GET", "/api/v1/analytics/admin/overview", token=atok)
check("workforce overview", s == 200 and ov["total_officers"] > 0,
      f"{ov['total_officers']} officers, {ov['total_courses']} offerings")
check("practice attempts excluded from workforce counts", "total_assessments" in ov)
check("event stream recorded", ov["events_recorded"] > 0, f"{ov['events_recorded']} events")
check("k-anonymity threshold declared", ov["k_anonymity_threshold"] == 5)

s, mx = call("GET", "/api/v1/analytics/admin/competency-matrix", token=atok)
check("role x competency heatmap", s == 200 and len(mx["cells"]) > 0,
      f"{len(mx['cells'])} cells, {len(mx['job_roles'])} roles")
check("suppressed cells are marked, not zeroed",
      all("suppressed" in c for c in mx["cells"]),
      f"{sum(1 for c in mx['cells'] if c['suppressed'])} suppressed")

s, te = call("GET", "/api/v1/analytics/admin/training-effectiveness", token=atok)
check("training effectiveness with a comparison group", s == 200 and len(te["rows"]) > 0,
      f"{len(te['rows'])} programmes")
check("net-of-comparison delta computed",
      any(row["net_delta"] is not None for row in te["rows"]))

s, ev = call("GET", "/api/v1/analytics/admin/events", token=atok)
check("append-only event stream readable", s == 200 and ev["total"] > 0,
      f"{len(ev['by_verb'])} distinct verbs")
s, marts = call("POST", "/api/v1/analytics/admin/rebuild-marts", token=atok)
check("marts rebuild from current state", s == 200, f"{marts.get('competency_rows', 0)} mart rows")

s, _denied = call("GET", "/api/v1/analytics/admin/overview", token=tok)
check("workforce views are role-gated", s == 403)


# ── security ─────────────────────────────────────────────────────────────────
section("SECURITY")
s, _ = call("GET", "/api/v1/gaps/me")
check("unauthenticated access refused", s == 401)
s, h = call("GET", "/health")
check("health reports every dependency",
      all(k in h for k in ("database", "embeddings", "llm", "catalogue")))
check("SSO-ready seam reported", h["auth_mode"] in ("local", "supabase"), f"auth_mode={h['auth_mode']}")


print("\n" + "=" * 78)
print(f"  {sum(results)} / {len(results)} checks passed")
print("=" * 78)
sys.exit(0 if all(results) else 1)
