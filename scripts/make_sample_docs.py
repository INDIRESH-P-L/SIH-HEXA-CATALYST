"""Generate the sample training handouts used by the demo.

    python scripts/make_sample_docs.py

Writes two PDFs to ``backend/app/seed/assets``:

  * SQL_Fundamentals_for_Statistical_Analysis.pdf — the demo document. The
    content is genuine: extraction, chunking, the grounding check and question
    generation all operate on it, so filler text would visibly break the
    pipeline in front of an audience.
  * Sampling_Methods_Primer.pdf — deliberately held back and never used in the
    scripted run, so a live cold generation can be done on request.

reportlab is a development dependency only (requirements-dev.txt). It builds a
seed asset; it is not part of the running application.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "backend" / "app" / "seed" / "assets"

try:
    from reportlab.lib.enums import TA_JUSTIFY
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
    )
except ImportError:  # pragma: no cover
    print("reportlab is not installed. Run: pip install -r requirements-dev.txt")
    raise SystemExit(1)


# ── Document 1: the SQL handout used in the demo ─────────────────────────────

SQL_HANDOUT: list[tuple[str, list[str]]] = [
    (
        "1. Relational Data in Statistical Work",
        [
            "A relational database stores data as tables. Each table holds rows, "
            "and each row holds one observation. In survey work a row is "
            "typically one household, one member of a household, or one "
            "enterprise. Each column holds one variable, such as district code, "
            "monthly consumption expenditure, or principal activity status.",
            "Every table should have a primary key: a column, or a combination of "
            "columns, whose value is unique for every row and never null. In a "
            "household schedule the primary key is usually the combination of the "
            "first-stage unit identifier, the household serial number and the "
            "survey round. A foreign key is a column in one table whose values "
            "refer to the primary key of another table. Foreign keys are what "
            "make joins meaningful, because they record which rows belong "
            "together.",
            "Structured Query Language, SQL, is the language used to ask questions "
            "of a relational database. A statistical officer who can write SQL can "
            "produce a tabulation directly from the survey database instead of "
            "waiting for a programmer to prepare an extract. That independence is "
            "the practical reason SQL sits in the competency framework.",
        ],
    ),
    (
        "2. SELECT: Choosing Columns and Rows",
        [
            "The SELECT statement retrieves data. Its simplest form names the "
            "columns wanted and the table they come from. Writing SELECT followed "
            "by an asterisk returns every column, which is convenient when "
            "exploring a table but wasteful in production queries, because the "
            "database must read and transmit columns nobody will use.",
            "The FROM clause names the source table. The optional WHERE clause "
            "restricts which rows are returned. A query without a WHERE clause "
            "returns every row in the table, which for a national survey may be "
            "several hundred thousand records.",
            "Column aliases, introduced with the keyword AS, rename a column in "
            "the output. This matters when a query result is going directly into a "
            "published table, because the alias becomes the column heading. "
            "SELECT DISTINCT removes duplicate rows from the result, which is the "
            "usual way to list the set of district codes actually present in a "
            "sample.",
        ],
    ),
    (
        "3. Filtering with WHERE",
        [
            "The WHERE clause takes a condition and keeps only the rows for which "
            "the condition is true. Comparison operators are equals, not equals, "
            "greater than, less than, greater than or equal to, and less than or "
            "equal to. Conditions combine with AND, OR and NOT.",
            "The BETWEEN operator tests whether a value falls within an inclusive "
            "range, which is the natural way to filter an age group or an "
            "expenditure class. The IN operator tests membership of a list, and is "
            "the readable way to restrict a query to a set of state codes. The "
            "LIKE operator performs pattern matching on text, using the percent "
            "sign to stand for any sequence of characters and the underscore to "
            "stand for exactly one character.",
            "Missing data needs care. In SQL a null value means unknown, not zero "
            "and not an empty string. Comparing anything to null with the equals "
            "operator yields unknown rather than true, so a row with a null value "
            "is not returned even by a condition that appears to test for it. To "
            "test for missing data you must write IS NULL or IS NOT NULL. This is "
            "the single most common source of silently wrong tabulations in survey "
            "processing, because non-response is recorded as null.",
        ],
    ),
    (
        "4. Aggregate Functions",
        [
            "Aggregate functions collapse many rows into a single value. COUNT "
            "returns the number of rows. SUM adds a numeric column. AVG returns "
            "the arithmetic mean. MIN and MAX return the smallest and largest "
            "values present.",
            "The distinction between COUNT with an asterisk and COUNT applied to a "
            "named column is important and frequently missed. COUNT with an "
            "asterisk counts rows, including rows where every value is null. COUNT "
            "applied to a named column counts only the rows where that column is "
            "not null. Reporting the second when the first was intended understates "
            "a denominator, and understating a denominator inflates every rate "
            "computed from it.",
            "AVG likewise ignores null values entirely rather than treating them as "
            "zero. If a consumption variable is null for households that did not "
            "respond, AVG returns the mean of the responding households, which is "
            "not the same quantity as the mean over all sampled households. "
            "Deciding which of the two is wanted is a methodological judgement, not "
            "a SQL question, but the officer writing the query has to know that "
            "the choice is being made.",
        ],
    ),
    (
        "5. GROUP BY and HAVING",
        [
            "GROUP BY divides rows into groups that share the same value in the "
            "named columns, and applies aggregate functions within each group "
            "separately. Grouping a household table by district code and applying "
            "AVG to monthly expenditure produces one mean per district. Any column "
            "in the SELECT list that is not inside an aggregate function must "
            "appear in the GROUP BY clause; otherwise the database cannot know "
            "which of the many values in the group to display.",
            "HAVING filters groups after aggregation. WHERE filters rows before "
            "aggregation. This is the difference that matters most, and it is the "
            "one most often confused. A condition on an individual household, such "
            "as excluding households with no members, belongs in WHERE. A condition "
            "on a computed group value, such as keeping only districts where at "
            "least thirty households responded, belongs in HAVING, because the "
            "count does not exist until aggregation has happened.",
            "The two clauses can appear in the same query and often should. A "
            "typical tabulation filters out ineligible records with WHERE, groups "
            "the remainder by district, and then suppresses small cells with "
            "HAVING. The order in which the database evaluates the clauses is FROM, "
            "then WHERE, then GROUP BY, then HAVING, then SELECT, and finally ORDER "
            "BY.",
        ],
    ),
    (
        "6. Join Types",
        [
            "A join combines rows from two tables using a condition, almost always "
            "an equality between a foreign key and a primary key. The join type "
            "determines what happens to rows that have no match on the other side, "
            "and choosing the wrong type is how records disappear from a tabulation "
            "without anyone noticing.",
            "An INNER JOIN returns only the rows that have a match in both tables. "
            "Joining a household table to a member table with an INNER JOIN drops "
            "any household that recorded no members. That may be correct, but it is "
            "a decision, and it silently changes the denominator.",
            "A LEFT JOIN, sometimes written LEFT OUTER JOIN, returns every row from "
            "the left table, together with matching rows from the right table where "
            "they exist. Where no match exists, the columns from the right table are "
            "filled with nulls. This is the join to use when the left table is the "
            "population of interest and the right table supplies optional detail, "
            "because it guarantees the row count of the left table is preserved.",
            "A RIGHT JOIN is the mirror image, keeping every row from the right "
            "table. A FULL OUTER JOIN keeps unmatched rows from both sides, filling "
            "the absent side with nulls, and is the natural tool for reconciling two "
            "registers that are each supposed to be complete. A CROSS JOIN returns "
            "every combination of rows from both tables and is almost never what a "
            "statistical query wants; encountering an unexpectedly enormous result "
            "usually means a join condition was omitted.",
        ],
    ),
    (
        "7. Ordering, Limiting and Reading a Query",
        [
            "ORDER BY sorts the result. The default direction is ascending; DESC "
            "reverses it. Sorting happens after aggregation, so a query can order "
            "districts by their computed mean expenditure. LIMIT restricts the "
            "number of rows returned, which is useful for inspecting a large result "
            "before running the full tabulation.",
            "When reading an unfamiliar query, work outward from the FROM clause "
            "rather than reading top to bottom. Establish which tables are involved "
            "and how they are joined, then find the WHERE conditions that reduce the "
            "rows, then the grouping, then the aggregates. The SELECT list, although "
            "written first, is evaluated almost last and is usually the least "
            "informative part of the query.",
            "Finally, a query that runs is not the same as a query that is correct. "
            "Before publishing any number produced by SQL, check the row count "
            "against an independent source, confirm that nulls have been handled "
            "deliberately, and verify that the join type preserved the intended "
            "denominator.",
        ],
    ),
]

# ── Document 2: held back for a live cold-generation demonstration ───────────

SAMPLING_PRIMER: list[tuple[str, list[str]]] = [
    (
        "1. Probability Sampling",
        [
            "A probability sample is one in which every unit in the population has "
            "a known, non-zero chance of selection. That known probability is what "
            "permits design-based inference: the estimate carries a measurable "
            "sampling error, and a confidence interval means what it claims to "
            "mean. A sample chosen for convenience carries no such guarantee, "
            "however large it is.",
            "The sampling frame is the list from which units are drawn. Frame "
            "quality bounds everything downstream. A frame that omits recently "
            "constructed urban blocks will under-represent new migrants no matter "
            "how carefully the sample is selected from it, and no amount of "
            "weighting recovers units that were never eligible for selection.",
        ],
    ),
    (
        "2. Stratification",
        [
            "Stratification divides the population into mutually exclusive and "
            "exhaustive groups, called strata, and draws an independent sample "
            "within each. Strata are formed on variables known for the whole frame, "
            "such as state, sector and district. Because sampling is independent "
            "within each stratum, the design guarantees representation of every "
            "stratum, which simple random sampling from the whole population does "
            "not.",
            "Stratification reduces variance when strata are internally homogeneous "
            "with respect to the variable being measured and differ from one "
            "another. Allocation across strata may be proportional to stratum size, "
            "or it may be optimal allocation, which additionally accounts for the "
            "variability within each stratum and the cost of enumerating there.",
        ],
    ),
    (
        "3. Multistage Designs and Weights",
        [
            "Large household surveys use multistage designs. First-stage units, "
            "typically villages or urban blocks, are selected with probability "
            "proportional to size. Households are then selected within each chosen "
            "first-stage unit. This concentrates field work geographically and "
            "makes national coverage affordable.",
            "The design weight of a unit is the reciprocal of its overall selection "
            "probability, and it is what makes a sample estimate represent the "
            "population. Weights are then adjusted for non-response and calibrated "
            "against known population totals from the census or from projections. "
            "The design effect measures how much the variance of an estimate has "
            "been inflated relative to simple random sampling of the same size, and "
            "it is the number to quote when someone asks why the sample is larger "
            "than a textbook formula suggests.",
        ],
    ),
]


def build_pdf(path: Path, title: str, subtitle: str, sections: list[tuple[str, list[str]]]) -> None:
    styles = getSampleStyleSheet()
    body = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=15.5,
        alignment=TA_JUSTIFY,
        spaceAfter=8,
    )
    heading = ParagraphStyle(
        "Heading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        spaceBefore=14,
        spaceAfter=7,
    )
    doc_title = ParagraphStyle(
        "DocTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=17,
        spaceAfter=4,
    )
    doc_subtitle = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=10,
        spaceAfter=16,
    )

    story: list[object] = [Paragraph(title, doc_title), Paragraph(subtitle, doc_subtitle)]
    for index, (name, paragraphs) in enumerate(sections):
        story.append(Paragraph(name, heading))
        for text in paragraphs:
            story.append(Paragraph(text, body))
        # One section per page: gives the extractor a realistic multi-page
        # document and keeps page numbers meaningful when a trainer checks a
        # generated question against its source page.
        if index != len(sections) - 1:
            story.append(PageBreak())
        else:
            story.append(Spacer(1, 4))

    SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=22 * mm,
        rightMargin=22 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        title=title,
        author="National Statistical Systems Training Academy (sample material)",
    ).build(story)


def main() -> int:
    ASSETS.mkdir(parents=True, exist_ok=True)

    sql_path = ASSETS / "SQL_Fundamentals_for_Statistical_Analysis.pdf"
    build_pdf(
        sql_path,
        "SQL Fundamentals for Statistical Analysis",
        "Training handout — sample material prepared for this prototype.",
        SQL_HANDOUT,
    )

    sampling_path = ASSETS / "Sampling_Methods_Primer.pdf"
    build_pdf(
        sampling_path,
        "Sampling Methods: A Primer",
        "Training handout — held back for live generation.",
        SAMPLING_PRIMER,
    )

    for path in (sql_path, sampling_path):
        print(f"  wrote {path.relative_to(ROOT)}  ({path.stat().st_size:,} bytes)")

    # Prove the document round-trips through our own extractor.
    sys.path.insert(0, str(ROOT / "backend"))
    from app.services.m8_generator.extract import extract  # noqa: E402

    result = extract(sql_path.read_bytes(), "pdf")
    print(
        f"  extraction check: {result.page_count} pages, "
        f"{result.char_count:,} characters"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
