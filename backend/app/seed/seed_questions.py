"""Seed a hand-written SQL question bank.

Why this exists: the assessment loop is the centre of the product, and it must
be demonstrable when no GROQ_API_KEY is configured, when the network is down,
or when the free tier is rate-limited. These twenty-two items keep the loop
runnable in all three cases.

These are **not** model-generated and are not presented as such. They are
written against the same handout the generator reads, they carry
``source_type`` metadata marking them as seeded, and the trainer console
distinguishes them from generated items. The AI generation path is a separate
feature demonstrated on its own.

Every item is put through the same deterministic validation gate the generated
ones face, so the bank cannot contain something the gate would have rejected.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import embeddings
from app.core.logging import get_logger
from app.models.competency import Competency
from app.models.question import Question
from app.services.m8_generator import validate

log = get_logger(__name__)

COMPETENCY_CODE = "SQL"

#: Written against SQL_Fundamentals_for_Statistical_Analysis.pdf, so the
#: grounding check has a real source to match against.
SOURCE_TEXT = """
A primary key is a column or combination of columns whose value is unique for
every row and never null. A foreign key is a column in one table whose values
refer to the primary key of another table.
The SELECT statement retrieves data. Writing SELECT followed by an asterisk
returns every column, which is convenient when exploring a table but wasteful
in production queries, because the database must read and transmit columns
nobody will use. The FROM clause names the source table.
The WHERE clause restricts which rows are returned. SELECT DISTINCT removes
duplicate rows from the result. Column aliases introduced with AS rename a
column in the output.
The BETWEEN operator tests whether a value falls within an inclusive range.
The IN operator tests membership of a list. The LIKE operator performs pattern
matching on text, using the percent sign for any sequence of characters and the
underscore for exactly one character.
In SQL a null value means unknown, not zero and not an empty string. Comparing
anything to null with the equals operator yields unknown rather than true. To
test for missing data you must write IS NULL or IS NOT NULL.
Aggregate functions collapse many rows into a single value. COUNT returns the
number of rows, SUM adds a numeric column, AVG returns the arithmetic mean, MIN
and MAX return the smallest and largest values. COUNT with an asterisk counts
rows including rows where every value is null. COUNT applied to a named column
counts only rows where that column is not null. AVG ignores null values
entirely rather than treating them as zero.
GROUP BY divides rows into groups sharing the same value in the named columns
and applies aggregate functions within each group separately. Any column in the
SELECT list not inside an aggregate function must appear in the GROUP BY clause.
HAVING filters groups after aggregation. WHERE filters rows before aggregation.
The database evaluates FROM, then WHERE, then GROUP BY, then HAVING, then
SELECT, and finally ORDER BY.
An INNER JOIN returns only rows that have a match in both tables. A LEFT JOIN
returns every row from the left table together with matching rows from the
right table, filling absent columns with nulls. A RIGHT JOIN keeps every row
from the right table. A FULL OUTER JOIN keeps unmatched rows from both sides. A
CROSS JOIN returns every combination of rows from both tables.
ORDER BY sorts the result, ascending by default, and DESC reverses it. LIMIT
restricts the number of rows returned.
"""

QUESTIONS: list[dict[str, Any]] = [
    {
        "question_text": "In a survey database, what does a primary key guarantee about a table?",
        "options": [
            "Its value is unique for every row and is never null",
            "Its value is sorted in ascending order",
            "It always contains an integer",
            "It is automatically indexed for text search",
        ],
        "correct_index": 0,
        "explanation": "A primary key identifies a row uniquely, so it must be unique across rows and can never be null. Ordering, data type and indexing behaviour are separate concerns.",
        "difficulty": "easy",
        "topic": "Primary keys",
        "source_page": 1,
    },
    {
        "question_text": "What is the role of a foreign key in a relational survey database?",
        "options": [
            "It refers to the primary key of another table",
            "It encrypts a sensitive column before storage",
            "It records the survey round for the row",
            "It removes duplicate rows automatically",
        ],
        "correct_index": 0,
        "explanation": "A foreign key holds values that refer to another table's primary key. That reference is what makes a join between the two tables meaningful.",
        "difficulty": "easy",
        "topic": "Foreign keys",
        "source_page": 1,
    },
    {
        "question_text": "Which clause of a SELECT statement restricts which rows are returned?",
        "options": ["WHERE", "FROM", "ORDER BY", "SELECT"],
        "correct_index": 0,
        "explanation": "WHERE applies a condition and keeps only rows for which it is true. FROM names the table, ORDER BY sorts, and SELECT chooses columns.",
        "difficulty": "easy",
        "topic": "SELECT and WHERE",
        "source_page": 2,
    },
    {
        "question_text": "What does SELECT DISTINCT do to a query result?",
        "options": [
            "Removes duplicate rows from the result",
            "Sorts the result in ascending order",
            "Restricts the result to the first row",
            "Renames the output columns",
        ],
        "correct_index": 0,
        "explanation": "DISTINCT eliminates duplicate rows, which is the usual way to list the set of district codes actually present in a sample.",
        "difficulty": "easy",
        "topic": "SELECT DISTINCT",
        "source_page": 2,
    },
    {
        "question_text": "Why is SELECT with an asterisk considered wasteful in a production query?",
        "options": [
            "The database must read and transmit columns nobody will use",
            "It silently drops rows containing null values",
            "It prevents the WHERE clause from being applied",
            "It always returns the rows in a random order",
        ],
        "correct_index": 0,
        "explanation": "Requesting every column forces the database to read and send data the query does not need, which costs time and bandwidth on large survey tables.",
        "difficulty": "medium",
        "topic": "SELECT",
        "source_page": 2,
    },
    {
        "question_text": "Which operator tests whether a value falls within an inclusive range?",
        "options": [
            "The BETWEEN operator",
            "The IN operator",
            "The LIKE operator",
            "The IS NULL test",
        ],
        "correct_index": 0,
        "explanation": "BETWEEN tests an inclusive range, which suits filtering an age group or an expenditure class. IN tests list membership and LIKE does pattern matching.",
        "difficulty": "easy",
        "topic": "Filtering operators",
        "source_page": 3,
    },
    {
        "question_text": "In the LIKE operator, what does the underscore character stand for?",
        "options": [
            "Exactly one character",
            "Any sequence of characters",
            "A null value",
            "The end of the string",
        ],
        "correct_index": 0,
        "explanation": "The underscore matches exactly one character, while the percent sign matches any sequence of characters including an empty one.",
        "difficulty": "medium",
        "topic": "Pattern matching",
        "source_page": 3,
    },
    {
        "question_text": "In SQL, what does a null value in a survey column mean?",
        "options": [
            "The value is unknown",
            "The value is zero",
            "The value is an empty string",
            "The row has been deleted",
        ],
        "correct_index": 0,
        "explanation": "Null means unknown. It is distinct from zero and from an empty string, which is why non-response must never be compared using the equals operator.",
        "difficulty": "medium",
        "topic": "Null handling",
        "source_page": 3,
    },
    {
        "question_text": "How must a query test whether a column contains missing data?",
        "options": [
            "Using IS NULL or IS NOT NULL",
            "Using the equals operator against null",
            "Using BETWEEN with an empty range",
            "Using COUNT on that column",
        ],
        "correct_index": 0,
        "explanation": "Comparing anything to null with equals yields unknown rather than true, so the row is not returned. IS NULL and IS NOT NULL are the only correct tests.",
        "difficulty": "hard",
        "topic": "Null handling",
        "source_page": 3,
    },
    {
        "question_text": "What is the difference between COUNT with an asterisk and COUNT applied to a named column?",
        "options": [
            "The asterisk counts all rows; a named column counts only rows where it is not null",
            "The asterisk counts distinct rows; a named column counts every row present",
            "There is no difference between the two forms in standard SQL",
            "The asterisk works only when the table declares a primary key",
        ],
        "correct_index": 0,
        "explanation": "COUNT with an asterisk counts rows regardless of nulls. COUNT on a named column skips rows where that column is null, which silently understates a denominator.",
        "difficulty": "hard",
        "topic": "Aggregate functions",
        "source_page": 4,
    },
    {
        "question_text": "How does the AVG function treat null values in a consumption column?",
        "options": [
            "It ignores them entirely rather than treating them as zero",
            "It treats each null as zero when computing the mean",
            "It returns null if any value in the column is null",
            "It replaces nulls with the column median",
        ],
        "correct_index": 0,
        "explanation": "AVG excludes nulls from both the numerator and the denominator, so it returns the mean over responding units, not over all sampled units.",
        "difficulty": "hard",
        "topic": "Aggregate functions",
        "source_page": 4,
    },
    {
        "question_text": "Which aggregate function returns the largest value present in a column?",
        "options": ["MAX", "MIN", "SUM", "COUNT"],
        "correct_index": 0,
        "explanation": "MAX returns the largest value and MIN the smallest. SUM adds values and COUNT reports how many rows there are.",
        "difficulty": "easy",
        "topic": "Aggregate functions",
        "source_page": 4,
    },
    {
        "question_text": "What does the GROUP BY clause do to the rows of a table?",
        "options": [
            "Divides rows into groups and aggregates within each group",
            "Sorts the rows by the value of the named column",
            "Removes every row that contains a null value",
            "Joins the table to itself on the named column",
        ],
        "correct_index": 0,
        "explanation": "GROUP BY forms groups from rows sharing the named values, then applies aggregate functions separately within each group, producing one output row per group.",
        "difficulty": "medium",
        "topic": "GROUP BY",
        "source_page": 5,
    },
    {
        "question_text": "Which columns in the SELECT list must also appear in the GROUP BY clause?",
        "options": [
            "Every column that is not inside an aggregate function",
            "Every column named anywhere in the whole query",
            "Only the columns that form part of the primary key",
            "Only the columns that may contain null values",
        ],
        "correct_index": 0,
        "explanation": "For a column outside an aggregate the database cannot know which of a group's many values to display, so that column must be part of the grouping.",
        "difficulty": "hard",
        "topic": "GROUP BY",
        "source_page": 5,
    },
    {
        "question_text": "What is the essential difference between the WHERE clause and the HAVING clause?",
        "options": [
            "WHERE filters rows before aggregation; HAVING filters groups after it",
            "HAVING filters rows before aggregation; WHERE filters groups after it",
            "WHERE works on text columns and HAVING works on numeric columns",
            "They are interchangeable in every query",
        ],
        "correct_index": 0,
        "explanation": "A condition on an individual record belongs in WHERE. A condition on a computed group value, such as a minimum respondent count, belongs in HAVING because that value does not exist until aggregation has run.",
        "difficulty": "hard",
        "topic": "GROUP BY with HAVING",
        "source_page": 5,
    },
    {
        "question_text": "Which clause filters grouped rows after aggregation, so that districts with few responding households can be suppressed?",
        "options": [
            "HAVING, because the count exists only after aggregation",
            "WHERE, because it filters unwanted records",
            "ORDER BY, because it controls which rows appear",
            "FROM, because it selects the source table",
        ],
        "correct_index": 0,
        "explanation": "The respondent count per district is a computed group value, so the condition can only be applied after grouping, which is what HAVING does.",
        "difficulty": "hard",
        "topic": "GROUP BY with HAVING",
        "source_page": 5,
    },
    {
        "question_text": "What does an INNER JOIN return when a household has no matching member records?",
        "options": [
            "The household is dropped from the result entirely",
            "The household appears with null member columns",
            "The join fails with an error",
            "The household is returned twice",
        ],
        "correct_index": 0,
        "explanation": "An INNER JOIN keeps only rows matched on both sides, so an unmatched household disappears and the denominator changes without warning.",
        "difficulty": "medium",
        "topic": "JOIN types",
        "source_page": 6,
    },
    {
        "question_text": "Which join preserves every row of the left table, filling unmatched right-hand columns with nulls?",
        "options": ["LEFT JOIN", "INNER JOIN", "CROSS JOIN", "RIGHT JOIN"],
        "correct_index": 0,
        "explanation": "A LEFT JOIN returns all left-hand rows and pads the right-hand columns with nulls where no match exists, which preserves the row count of the population of interest.",
        "difficulty": "medium",
        "topic": "JOIN types",
        "source_page": 6,
    },
    {
        "question_text": "Which join keeps unmatched rows from both tables, filling the absent side with nulls?",
        "options": [
            "FULL OUTER JOIN",
            "INNER JOIN",
            "LEFT OUTER JOIN",
            "CROSS JOIN",
        ],
        "correct_index": 0,
        "explanation": "A FULL OUTER JOIN retains unmatched rows from both sides, which makes it the natural tool for reconciling two registers that are each meant to be complete.",
        "difficulty": "medium",
        "topic": "JOIN types",
        "source_page": 6,
    },
    {
        "question_text": "A join that returns every combination of rows from both tables indicates which mistake?",
        "options": [
            "A join condition was omitted, producing a CROSS JOIN",
            "The WHERE clause was applied before the join",
            "The tables were sorted in different orders",
            "An aggregate function was used without GROUP BY",
        ],
        "correct_index": 0,
        "explanation": "Without a join condition the database returns every combination of rows from both tables, so the result size multiplies rather than matching.",
        "difficulty": "hard",
        "topic": "JOIN types",
        "source_page": 6,
    },
    {
        "question_text": "In what order does the database evaluate the clauses of a grouped query?",
        "options": [
            "FROM, WHERE, GROUP BY, HAVING, SELECT, ORDER BY",
            "SELECT, FROM, WHERE, GROUP BY, HAVING, ORDER BY",
            "FROM, SELECT, WHERE, ORDER BY, GROUP BY, HAVING",
            "WHERE, FROM, SELECT, HAVING, GROUP BY, ORDER BY",
        ],
        "correct_index": 0,
        "explanation": "Although SELECT is written first, it is evaluated almost last. Knowing the real order explains why an alias defined in SELECT cannot be used in WHERE.",
        "difficulty": "hard",
        "topic": "Clause evaluation order",
        "source_page": 7,
    },
    {
        "question_text": "What is the default sort direction of the ORDER BY clause?",
        "options": ["Ascending", "Descending", "Insertion order", "Random"],
        "correct_index": 0,
        "explanation": "ORDER BY sorts ascending unless DESC is given, and it runs after aggregation, so a query can order districts by a computed mean.",
        "difficulty": "easy",
        "topic": "ORDER BY",
        "source_page": 7,
    },
]


async def seed_question_bank(session: AsyncSession) -> dict[str, int]:
    """Insert the bank, skipping items already present.

    Matched on question text, so re-running does not duplicate. Each item is
    validated by the same gate generated items pass through; anything that
    fails is reported rather than silently stored.
    """
    competency = await session.scalar(
        select(Competency).where(Competency.code == COMPETENCY_CODE)
    )
    if competency is None:
        raise RuntimeError("Seed the framework before seeding the question bank.")

    existing_texts = set(
        (
            await session.execute(
                select(Question.question_text).where(
                    Question.competency_id == competency.id
                )
            )
        )
        .scalars()
        .all()
    )

    pool: list[list[float]] = [
        list(v)
        for v in (
            await session.execute(
                select(Question.embedding)
                .where(Question.competency_id == competency.id)
                .where(Question.embedding.isnot(None))
            )
        )
        .scalars()
        .all()
        if v is not None
    ]

    inserted = 0
    failed: list[str] = []

    for spec in QUESTIONS:
        if spec["question_text"] in existing_texts:
            continue

        vector = embeddings.embed_one(
            f"{spec['question_text']} {' '.join(spec['options'])}"
        )
        result = validate.validate_item(
            spec, source_chunk=SOURCE_TEXT, embedding=vector, existing_embeddings=pool
        )
        if not result.passed:
            failed.append(f"{spec['question_text'][:50]}: {result.failure_reason()}")
            continue

        session.add(
            Question(
                material_id=None,
                chunk_id=None,
                competency_id=competency.id,
                question_text=spec["question_text"],
                options=spec["options"],
                correct_index=spec["correct_index"],
                explanation=spec["explanation"],
                difficulty=spec["difficulty"],
                topic=spec["topic"],
                # Approved on insert: these are hand-written and reviewed, not
                # model output awaiting a trainer's judgement.
                status="APPROVED",
                validation={
                    **result.as_json(),
                    "origin": "seeded",
                    "note": (
                        "Hand-written reference item, not model-generated. "
                        "Validated by the same deterministic gate."
                    ),
                },
                source_page=spec.get("source_page"),
                embedding=vector,
            )
        )
        pool.append(vector)
        inserted += 1

    await session.flush()

    total = await session.scalar(
        select(func.count())
        .select_from(Question)
        .where(Question.competency_id == competency.id)
        .where(Question.status == "APPROVED")
    )

    if failed:
        for reason in failed:
            log.warning("seed question rejected by the validation gate: %s", reason)

    log.info(
        "question bank: %d inserted, %d approved for %s (%d rejected)",
        inserted,
        int(total or 0),
        COMPETENCY_CODE,
        len(failed),
    )
    return {"inserted": inserted, "total": int(total or 0), "rejected": len(failed)}
