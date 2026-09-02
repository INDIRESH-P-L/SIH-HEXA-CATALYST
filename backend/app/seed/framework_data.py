"""Job roles, activities and the expectation matrix, on the FRAC 4-point scale.

The FRAC graph is Position → Role → Activity → Competency. Activities are the
concrete actions a role performs; competencies attach to them. That layer is
what lets a gap be explained as "you cannot yet do this part of your job"
rather than as an abstract score.

Levels are 1–4 throughout — Awareness, Application, Leveraging for decisions,
Subject Matter Expert — and criticality runs 1.0–3.0.
"""

from __future__ import annotations

FRAMEWORK_VERSION = "FRAC-2026.1"
FRAMEWORK_TITLE = "MoSPI Competency Framework for Official Statistics, 2026.1"
FRAMEWORK_NOTES = (
    "Seeded from the iGOT FRAC dictionary, the UN Global Working Group big-data "
    "framework and GSBPM process phases, with MoSPI subject-matter validation. "
    "Sealing this version freezes the expectation matrix so past dashboards "
    "recompute identically."
)

JOB_ROLES: list[dict[str, str]] = [
    {
        "code": "STAT_OFFICER",
        "title": "Statistical Officer",
        "cadre": "ISS",
        "description": (
            "Field and desk statistical work: survey execution, data processing, "
            "tabulation and first-line analysis for national and state "
            "statistical programmes."
        ),
    },
    {
        "code": "SR_STAT_OFFICER",
        "title": "Senior Statistical Officer",
        "cadre": "ISS",
        "description": (
            "Supervises survey rounds and estimation work, reviews methodology, "
            "and is answerable for the quality of published estimates."
        ),
    },
    {
        "code": "DEP_DIRECTOR",
        "title": "Deputy Director",
        "cadre": "ISS",
        "description": (
            "Directs a statistical division: programme design, inter-ministerial "
            "coordination, release policy and capacity planning."
        ),
    },
    {
        "code": "DATA_SCIENTIST",
        "title": "Data Scientist (Statistical Systems)",
        "cadre": "OTHER",
        "description": (
            "Builds the analytical and machine-learning capability of the "
            "statistical system: automated coding, record linkage, alternative "
            "data sources and the platforms that carry them."
        ),
    },
    {
        "code": "FIELD_SUPERVISOR",
        "title": "Field Supervisor",
        "cadre": "SSS",
        "description": (
            "Leads enumeration in the field: instrument administration, "
            "supervision of enumerators, first-line data quality checks and "
            "liaison with respondents."
        ),
    },
]

# ── Activities: role code → the concrete actions that role performs ──────────
#
# Each carries the competencies it depends on, at the level the activity needs.
# This is the layer that makes a gap explainable.

ACTIVITIES: dict[str, list[dict[str, object]]] = {
    "STAT_OFFICER": [
        {
            "code": "EXTRACT_TABULATE",
            "name": "Extract and tabulate survey data",
            "description": (
                "Pull unit-level records from the survey database and produce "
                "the tabulations a release or a policy question requires."
            ),
            "competencies": {"SQL": 4, "PYTHON": 3, "DATA_VIZ": 2},
        },
        {
            "code": "RUN_SURVEY_ROUND",
            "name": "Execute a survey round in the field",
            "description": (
                "Administer the schedule, supervise enumeration, and resolve "
                "field problems against the sampling design."
            ),
            "competencies": {"SAMPLING": 3, "SURVEY_DESIGN": 3, "PROJECT_MGMT": 3},
        },
        {
            "code": "MAP_INDICATORS",
            "name": "Map indicators to administrative geography",
            "description": (
                "Join tabulated indicators to boundary layers and publish "
                "district-level maps."
            ),
            "competencies": {"GIS": 2, "DATA_VIZ": 3},
        },
        {
            "code": "PREPARE_RELEASE",
            "name": "Prepare tables for a statistical release",
            "description": (
                "Assemble, check and document tables to release standard, with "
                "a quality declaration."
            ),
            "competencies": {"DATA_VIZ": 3, "DATA_QUALITY": 3, "SQL": 3},
        },
    ],
    "SR_STAT_OFFICER": [
        {
            "code": "REVIEW_METHODOLOGY",
            "name": "Review and sign off survey methodology",
            "description": (
                "Assess a proposed design against precision and cost, and take "
                "responsibility for the estimates it produces."
            ),
            "competencies": {"SAMPLING": 4, "SURVEY_DESIGN": 4, "DATA_QUALITY": 3},
        },
        {
            "code": "SUPERVISE_ESTIMATION",
            "name": "Supervise estimation and weighting",
            "description": (
                "Direct weighting, calibration and variance estimation, and "
                "reconcile results against previous rounds."
            ),
            "competencies": {"R_STATS": 3, "PYTHON": 3, "SAMPLING": 4},
        },
        {
            "code": "DOCUMENT_SURVEY",
            "name": "Document a survey to metadata standard",
            "description": (
                "Produce the metadata that makes a survey findable, "
                "interpretable and reusable."
            ),
            "competencies": {"METADATA_STANDARDS": 3, "DATA_QUALITY": 3},
        },
        {
            "code": "BRIEF_STAKEHOLDERS",
            "name": "Brief policy stakeholders on results",
            "description": (
                "Explain findings, revisions and uncertainty to readers who are "
                "not statisticians."
            ),
            "competencies": {"COMMUNICATION": 3, "DATA_VIZ": 3},
        },
    ],
    "DEP_DIRECTOR": [
        {
            "code": "PLAN_PROGRAMME",
            "name": "Plan the divisional statistical programme",
            "description": (
                "Set the survey and release calendar against capacity, budget "
                "and ministerial demand."
            ),
            "competencies": {"PROJECT_MGMT": 4, "LEADERSHIP": 3, "DECISION_MAKING": 3},
        },
        {
            "code": "COMPILE_ACCOUNTS",
            "name": "Oversee national accounts compilation",
            "description": (
                "Direct the compilation of macro aggregates and defend the "
                "resulting estimates."
            ),
            "competencies": {"NATIONAL_ACCOUNTS": 4, "PRICE_STATISTICS": 3},
        },
        {
            "code": "ASSURE_QUALITY",
            "name": "Assure the quality of published statistics",
            "description": (
                "Apply the quality assurance framework across the division's "
                "outputs and publish quality declarations."
            ),
            "competencies": {"DATA_QUALITY": 4, "ETHICS": 4, "DATA_PRIVACY": 3},
        },
        {
            "code": "COORDINATE_SDG",
            "name": "Coordinate SDG reporting across ministries",
            "description": (
                "Assemble indicator returns from line ministries and assess "
                "gaps against the National Indicator Framework."
            ),
            "competencies": {"SDG_INDICATORS": 4, "COMMUNICATION": 3},
        },
    ],
    "DATA_SCIENTIST": [
        {
            "code": "AUTOMATE_CODING",
            "name": "Automate occupation and industry coding",
            "description": (
                "Build and evaluate classifiers that assign NCO and NIC codes "
                "to free-text survey responses."
            ),
            "competencies": {"MACHINE_LEARNING": 4, "PYTHON": 4},
        },
        {
            "code": "LINK_REGISTERS",
            "name": "Link administrative registers",
            "description": (
                "Match records across registers without a common key, and "
                "quantify the linkage error."
            ),
            "competencies": {"MACHINE_LEARNING": 3, "SQL": 4, "DATA_PRIVACY": 3},
        },
        {
            "code": "BUILD_PIPELINE",
            "name": "Build and operate a processing platform",
            "description": (
                "Stand up the cloud infrastructure and interfaces that carry "
                "statistical production."
            ),
            "competencies": {"CLOUD": 3, "APIS": 3, "CYBERSECURITY": 3},
        },
    ],
    "FIELD_SUPERVISOR": [
        {
            "code": "SUPERVISE_ENUMERATION",
            "name": "Supervise enumerators in the field",
            "description": (
                "Allocate workload, observe interviews and correct instrument "
                "administration in the field."
            ),
            "competencies": {"SURVEY_DESIGN": 3, "PROJECT_MGMT": 3, "COMMUNICATION": 3},
        },
        {
            "code": "CROP_ESTIMATION",
            "name": "Conduct crop cutting experiments",
            "description": (
                "Execute the general crop estimation protocol and record yields "
                "to standard."
            ),
            "competencies": {"AGRI_STATISTICS": 3, "SAMPLING": 2},
        },
        {
            "code": "FIELD_QUALITY_CHECK",
            "name": "Run first-line data quality checks",
            "description": (
                "Screen returns for internal consistency and non-response "
                "before they leave the field."
            ),
            "competencies": {"DATA_QUALITY": 3, "LABOUR_STATISTICS": 2},
        },
    ],
}


# ── The expectation matrix ───────────────────────────────────────────────────
#
# role code → competency code → (required level 1-4, criticality 1.0-3.0, horizon)
#
# The Statistical Officer matrix is the demonstration profile. Eight axes is
# the radar's maximum, and these values produce a readable spread against the
# seeded baseline: one CRITICAL, one EMERGING, five SIGNIFICANT and one MET.

REQUIREMENTS: dict[str, dict[str, tuple[int, str, str]]] = {
    "STAT_OFFICER": {
        # Required 4 against a self-declared 1 — the demonstration subject.
        "SQL": (4, "2.20", "current_role"),
        "SAMPLING": (4, "2.50", "current_role"),
        "SURVEY_DESIGN": (3, "2.00", "current_role"),
        "PYTHON": (3, "1.80", "current_role"),
        "DATA_VIZ": (3, "1.50", "current_role"),
        "PROJECT_MGMT": (3, "1.40", "current_role"),
        "GIS": (2, "1.20", "current_role"),
        # Needed in the next post up, not this one: real, but discounted to 0.6
        # rather than ignored. This is what an EMERGING gap looks like.
        "DATA_QUALITY": (3, "2.00", "next_role"),
    },
    "SR_STAT_OFFICER": {
        "SAMPLING": (4, "2.80", "current_role"),
        "SURVEY_DESIGN": (4, "2.40", "current_role"),
        "DATA_QUALITY": (4, "2.60", "current_role"),
        "SQL": (3, "1.80", "current_role"),
        "PYTHON": (3, "1.80", "current_role"),
        "R_STATS": (3, "1.60", "current_role"),
        "DATA_VIZ": (3, "1.50", "current_role"),
        "METADATA_STANDARDS": (3, "1.90", "current_role"),
        "DATA_PRIVACY": (3, "2.10", "current_role"),
        "PROJECT_MGMT": (3, "1.70", "current_role"),
        "COMMUNICATION": (3, "1.60", "current_role"),
        "LEADERSHIP": (3, "1.50", "next_role"),
    },
    "DEP_DIRECTOR": {
        "NATIONAL_ACCOUNTS": (4, "2.70", "current_role"),
        "PRICE_STATISTICS": (3, "2.30", "current_role"),
        "SDG_INDICATORS": (3, "2.10", "current_role"),
        "DATA_QUALITY": (4, "2.80", "current_role"),
        "SAMPLING": (3, "1.90", "current_role"),
        "SURVEY_DESIGN": (3, "1.70", "current_role"),
        "DATA_PRIVACY": (4, "2.50", "current_role"),
        "GOV_CLOUD": (2, "1.40", "current_role"),
        "PROJECT_MGMT": (4, "2.60", "current_role"),
        "LEADERSHIP": (4, "2.60", "current_role"),
        "DECISION_MAKING": (4, "2.40", "current_role"),
        "ETHICS": (4, "3.00", "current_role"),
        "CHANGE_MGMT": (3, "1.80", "current_role"),
    },
    "DATA_SCIENTIST": {
        "PYTHON": (4, "2.70", "current_role"),
        "MACHINE_LEARNING": (4, "2.70", "current_role"),
        "SQL": (4, "2.20", "current_role"),
        "CLOUD": (3, "1.90", "current_role"),
        "APIS": (3, "1.80", "current_role"),
        "DATA_VIZ": (3, "1.60", "current_role"),
        "R_STATS": (2, "1.20", "current_role"),
        "CYBERSECURITY": (3, "2.10", "current_role"),
        "DATA_PRIVACY": (4, "2.60", "current_role"),
        "OPEN_DATA": (3, "1.50", "current_role"),
        "DATA_QUALITY": (3, "1.90", "next_role"),
    },
    "FIELD_SUPERVISOR": {
        "SURVEY_DESIGN": (3, "2.40", "current_role"),
        "SAMPLING": (2, "1.90", "current_role"),
        "AGRI_STATISTICS": (3, "2.00", "current_role"),
        "LABOUR_STATISTICS": (2, "1.70", "current_role"),
        "DATA_QUALITY": (3, "2.50", "current_role"),
        "GIS": (2, "1.40", "current_role"),
        "PROJECT_MGMT": (3, "2.00", "current_role"),
        "COMMUNICATION": (3, "1.80", "current_role"),
        "CHANGE_MGMT": (2, "1.30", "current_role"),
    },
}


# ── SME cut-scores ───────────────────────────────────────────────────────────
#
# Band boundaries per competency, set by a subject-matter panel using modified
# Angoff. Never one global threshold: 60% on sampling theory and 60% on
# spreadsheet hygiene are not the same statement about an officer.
#
# Competencies absent from this map use the platform defaults.

CUT_SCORES: dict[str, tuple[float, float, float, float]] = {
    # code: (level 1 min, level 2 min, level 3 min, level 4 min)
    "SQL": (40.0, 58.0, 76.0, 90.0),
    "SAMPLING": (45.0, 65.0, 82.0, 93.0),
    "NATIONAL_ACCOUNTS": (45.0, 65.0, 82.0, 93.0),
    "DATA_PRIVACY": (50.0, 70.0, 85.0, 95.0),
    "ETHICS": (50.0, 70.0, 85.0, 95.0),
    "CYBERSECURITY": (50.0, 70.0, 85.0, 95.0),
}
