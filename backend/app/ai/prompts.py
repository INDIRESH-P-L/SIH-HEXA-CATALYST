"""Every prompt template, in one versioned place.

Bumping ``PROMPT_VERSION`` changes the cache key for every prompt, which is the
intended way to invalidate cached responses after editing wording.

All templates take only the whitelisted context fields from ``ai.scrub``. None
of them can be filled with a name, an email or an identifier.
"""

from __future__ import annotations

PROMPT_VERSION = "v1"

# ── System messages ──────────────────────────────────────────────────────────

SYSTEM_RECOMMENDATION = (
    "You advise officials in India's Official Statistical System (Ministry of "
    "Statistics and Programme Implementation) on capacity building. You write "
    "for a working civil servant: plain, specific, no marketing language. "
    "You never invent facts about a course beyond what you are given, and you "
    "never address the reader by name because you are not given one."
)

SYSTEM_FEEDBACK = (
    "You write short, constructive feedback on a competency assessment taken by "
    "an official in India's Official Statistical System. You are given the "
    "score and the topics answered incorrectly. You never restate the score as "
    "a judgement of the person, and you never invent topics that are not in the "
    "list you were given."
)

SYSTEM_MCQ = (
    "You write multiple-choice assessment items for civil-service training in "
    "official statistics. You write items only about content that appears in "
    "the source passage you are given. Every distractor must be plausible to "
    "someone who half-knows the material and clearly wrong to someone who knows "
    "it. You never write 'all of the above', 'none of the above' or 'both A and "
    "B'. You never make the correct option conspicuously longer than the others."
)

SYSTEM_ASSISTANT = (
    "You answer questions about uploaded training material for officials in "
    "India's Official Statistical System, using only the passages provided. "
    "If the passages do not contain the answer, you say so."
)

# ── Recommendation explanation (llama-3.3-70b-versatile, plain text) ─────────

RECOMMENDATION = """A {job_role_title} needs level {required_level} in {competency_name} \
({frac_required} on the FRAC scale). They are currently assessed at level \
{current_level} ({frac_current}), a {gap_band} gap.

The system has matched this course:
  Title:    {course_title}
  Level:    {proficiency}
  Duration: {course_duration_hours} hours
  Format:   {course_format}
  Provider: {provider}

Write 2 to 3 sentences, maximum 60 words, explaining to that officer why this \
course is a sensible next step for them. Be concrete about what closing this \
gap enables in their work. Do not use bullet points, headings, or a greeting. \
Do not mention that you are an AI. Start directly with the substance."""

# ── Quiz feedback (llama-3.3-70b-versatile, plain text) ─────────────────────

FEEDBACK = """An officer completed a {total_questions}-question assessment in \
{competency_name} and scored {score}% ({correct_count} correct).

Topics answered correctly: {strong_topics}
Topics answered incorrectly: {weak_topics}

Write 2 to 3 sentences, maximum 70 words, addressed to that officer. Open by \
acknowledging what they handled well, then name the specific topics to revisit \
and say briefly why each matters in statistical work. Do not repeat the \
percentage. No bullet points, no headings, no greeting."""

# ── MCQ generation (openai/gpt-oss-20b, strict json_schema) ─────────────────

MCQ_GENERATION = """Source passage from a training handout on {competency_name}:

\"\"\"
{source_excerpt}
\"\"\"

Write exactly {num_questions} multiple-choice questions that test understanding \
of this passage.

Requirements:
- Every question must be answerable from the passage above and from nothing else.
- Exactly 4 options per question. Exactly one is correct.
- Distractors must be plausible but clearly wrong to someone who understands \
the passage. Do not use 'all of the above', 'none of the above' or 'both A and B'.
- Do not make the correct option noticeably longer than the distractors.
- The question stem must be between 15 and 300 characters.
- The explanation must be at least 20 characters and must say why the correct \
option is correct, not merely restate it.
- 'topic' must be a short phrase naming the specific concept tested, for \
example 'INNER JOIN' or 'GROUP BY with HAVING'.
- Difficulty mix requested: {difficulty_mix}."""

MCQ_RETRY_SUFFIX = """

A previous attempt at this passage was rejected by automated validation for the \
following reason: {retry_reason}

Write replacement questions that do not repeat that fault."""

# ── Assistant (M7, stretch scope — not enabled in Round 2) ──────────────────

ASSISTANT = """Passages from the uploaded training material:

{source_excerpt}

Question: {topic}

Answer using only the passages above, in at most 120 words. If they do not \
contain the answer, say that the uploaded material does not cover it."""


# ── Deterministic fallbacks ─────────────────────────────────────────────────
# Used verbatim whenever the LLM is unavailable. The interface must never show
# an empty card or a blank feedback panel (§1 rule 7).

FALLBACK_RECOMMENDATION = (
    "Recommended because your {competency_name} level is {current_level} against "
    "a required {required_level} for {job_role_title}, and this "
    "{course_duration_hours}-hour {course_format} course targets level "
    "{proficiency}."
)

FALLBACK_FEEDBACK_WITH_TOPICS = (
    "You answered {correct_count} of {total_questions} questions correctly. "
    "Focus your next session on {weak_topics}, then reattempt this assessment "
    "to move your {competency_name} level forward."
)

FALLBACK_FEEDBACK_CLEAN = (
    "You answered {correct_count} of {total_questions} questions correctly "
    "across every topic in this assessment. Continue to the next recommended "
    "course to build on {competency_name}."
)
