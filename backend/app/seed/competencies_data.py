"""The competency framework for India's Official Statistical System.

Four domains, matching the competency map in the problem statement:

  * Statistical      — survey design, sampling, national accounts, price,
                       labour, agricultural and industrial statistics, SDG
                       indicators, metadata standards, data quality
  * Technical        — Python, R, SQL, Stata, SPSS, SAS, GIS, data
                       visualisation, AI/ML, cloud, APIs, open data
  * Digital governance — cybersecurity, data privacy, digital signatures,
                       government cloud, digital public infrastructure
  * Behavioural and managerial — leadership, communication, project
                       management, ethics, decision making, change management

Descriptions are written as real prose because the semantic index is built from
them: the recommender embeds "name. description" and searches the catalogue in
that space. Placeholder text would visibly degrade course matching, which is
the one part of the pipeline an observer can see working or not working.

``frac_type`` follows the iGOT Karmayogi FRAC vocabulary: domain, functional or
behavioural. ``kind`` is the FRAC competency type — knowledge, skill or
attribute. ``decay`` is how fast evidence goes stale: tools and platforms
after 18 months, regulatory and procedural after 12, methodology after 36,
and behavioural never. Decay does not rewrite a level; it lowers confidence,
which raises the gap priority and prompts a re-assessment.
"""

from __future__ import annotations

COMPETENCIES: list[dict[str, str]] = [
    # ── STATISTICAL ──────────────────────────────────────────────────────────
    {
        "code": "SAMPLING",
        "name": "Sampling Theory & Survey Sampling",
        "cluster": "STATISTICAL",
        "frac_type": "domain",
        "kind": "knowledge",
        "decay": "methodology",
        "description": (
            "Designing and evaluating probability samples for official statistics. "
            "Covers simple random, systematic, stratified and multistage designs, "
            "probability proportional to size selection, sample allocation under "
            "cost and precision constraints, design effects, and the construction "
            "and calibration of survey weights for national household and "
            "enterprise surveys."
        ),
    },
    {
        "code": "SURVEY_DESIGN",
        "name": "Survey Design & Questionnaire Development",
        "cluster": "STATISTICAL",
        "frac_type": "domain",
        "kind": "knowledge",
        "decay": "methodology",
        "description": (
            "Turning a measurement objective into a field instrument. Covers "
            "concept and definition setting, question wording, response "
            "categories, reference periods, skip logic, cognitive testing and "
            "pilot studies, and the diagnosis of non-response and measurement "
            "error as evidence of instrument defects."
        ),
    },
    {
        "code": "NATIONAL_ACCOUNTS",
        "name": "National Accounts & Macro Aggregates",
        "cluster": "STATISTICAL",
        "frac_type": "domain",
        "kind": "knowledge",
        "decay": "methodology",
        "description": (
            "Compiling national accounts under the System of National Accounts "
            "framework. Covers the production, income and expenditure approaches "
            "to gross domestic product, supply and use tables, deflation to "
            "constant prices, treatment of the unorganised sector, and base-year "
            "revision practice."
        ),
    },
    {
        "code": "PRICE_STATISTICS",
        "name": "Price Statistics & Index Numbers",
        "cluster": "STATISTICAL",
        "frac_type": "domain",
        "kind": "knowledge",
        "decay": "methodology",
        "description": (
            "Constructing and maintaining price indices such as the consumer and "
            "wholesale price indices. Covers item basket selection, weighting "
            "diagrams derived from consumption expenditure surveys, price "
            "collection protocols, quality adjustment, index number formulae and "
            "their bias properties, and base revision."
        ),
    },
    {
        "code": "LABOUR_STATISTICS",
        "name": "Labour & Employment Statistics",
        "cluster": "STATISTICAL",
        "frac_type": "domain",
        "kind": "knowledge",
        "decay": "methodology",
        "description": (
            "Measuring the labour force and employment conditions. Covers the "
            "international definitions of employment, unemployment and labour "
            "force participation, activity status classification on usual and "
            "current weekly status, informal sector and informal employment "
            "measurement, wage and earnings statistics, and the design of the "
            "Periodic Labour Force Survey."
        ),
    },
    {
        "code": "AGRI_STATISTICS",
        "name": "Agricultural Statistics",
        "cluster": "STATISTICAL",
        "frac_type": "domain",
        "kind": "knowledge",
        "decay": "methodology",
        "description": (
            "Estimating agricultural area, production and yield. Covers crop "
            "cutting experiments and general crop estimation surveys, land use "
            "classification and area enumeration, livestock and fisheries "
            "statistics, cost of cultivation studies, and the growing use of "
            "remote sensing to supplement traditional field enumeration."
        ),
    },
    {
        "code": "INDUSTRIAL_STATISTICS",
        "name": "Industrial & Enterprise Statistics",
        "cluster": "STATISTICAL",
        "frac_type": "domain",
        "kind": "knowledge",
        "decay": "methodology",
        "description": (
            "Measuring industrial output and enterprise activity. Covers the "
            "Annual Survey of Industries, the Index of Industrial Production, "
            "business registers and their maintenance, the National Industrial "
            "Classification, unincorporated enterprise surveys, and the treatment "
            "of the factory and non-factory segments."
        ),
    },
    {
        "code": "SDG_INDICATORS",
        "name": "SDG Indicators & Monitoring Frameworks",
        "cluster": "STATISTICAL",
        "frac_type": "domain",
        "kind": "knowledge",
        "decay": "methodology",
        "description": (
            "Reporting against the Sustainable Development Goal indicator "
            "framework and the National Indicator Framework. Covers indicator "
            "metadata, tier classification, mapping indicators to survey and "
            "administrative sources, disaggregation requirements, and the "
            "assessment of data gaps across line ministries."
        ),
    },
    {
        "code": "METADATA_STANDARDS",
        "name": "Metadata Standards & Statistical Classifications",
        "cluster": "STATISTICAL",
        "frac_type": "domain",
        "kind": "knowledge",
        "decay": "methodology",
        "description": (
            "Documenting statistical data so it can be found, understood and "
            "reused. Covers the Generic Statistical Business Process Model, "
            "SDMX for data and metadata exchange, DDI for microdata "
            "documentation, standard classifications such as NIC and NCO, and the "
            "maintenance of concordances when a classification is revised."
        ),
    },
    {
        "code": "DATA_QUALITY",
        "name": "Data Quality Frameworks & Assurance",
        "cluster": "STATISTICAL",
        "frac_type": "domain",
        "kind": "knowledge",
        "decay": "methodology",
        "description": (
            "Assessing and assuring the quality of official statistics. Covers "
            "the quality dimensions of relevance, accuracy, timeliness, "
            "accessibility, coherence and comparability, the National Quality "
            "Assurance Framework, editing and imputation strategy, sampling and "
            "non-sampling error decomposition, and the publication of quality "
            "declarations alongside releases."
        ),
    },
    # ── TECHNICAL ────────────────────────────────────────────────────────────
    {
        "code": "SQL",
        "name": "SQL & Database Querying",
        "cluster": "TECHNICAL",
        "frac_type": "functional",
        "kind": "skill",
        "decay": "tools_platforms",
        "description": (
            "Querying relational databases holding survey and administrative "
            "data. Covers SELECT statements and filtering with WHERE, sorting, "
            "aggregate functions, GROUP BY with HAVING, the four join types, "
            "subqueries and common table expressions, and the design of indexes "
            "and schemas for large tabulation workloads."
        ),
    },
    {
        "code": "PYTHON",
        "name": "Python for Data Processing",
        "cluster": "TECHNICAL",
        "frac_type": "functional",
        "kind": "skill",
        "decay": "tools_platforms",
        "description": (
            "Programming in Python to process statistical data. Covers core "
            "language constructs, reading fixed-width and delimited survey files, "
            "the pandas and NumPy stack for merging and reshaping schedules, "
            "applying design weights, handling missing responses, and packaging a "
            "reproducible processing pipeline."
        ),
    },
    {
        "code": "R_STATS",
        "name": "R for Statistical Computing",
        "cluster": "TECHNICAL",
        "frac_type": "functional",
        "kind": "skill",
        "decay": "tools_platforms",
        "description": (
            "Using R for design-based estimation and statistical modelling. "
            "Covers the survey package for weighted means, ratios and totals with "
            "correct standard errors under complex designs, regression and "
            "hypothesis testing, and reproducible reporting so published tables "
            "regenerate when inputs are revised."
        ),
    },
    {
        "code": "STATA",
        "name": "Stata for Survey Analysis",
        "cluster": "TECHNICAL",
        "frac_type": "functional",
        "kind": "skill",
        "decay": "tools_platforms",
        "description": (
            "Analysing complex survey data in Stata. Covers the svyset family for "
            "declaring stratification, clustering and weights, do-file discipline "
            "for reproducible analysis, data management with merge and reshape, "
            "panel and time-series commands, and the production of publication "
            "tables directly from estimation output."
        ),
    },
    {
        "code": "SPSS",
        "name": "SPSS for Statistical Analysis",
        "cluster": "TECHNICAL",
        "frac_type": "functional",
        "kind": "skill",
        "decay": "tools_platforms",
        "description": (
            "Using SPSS for descriptive and inferential analysis of survey data. "
            "Covers variable and value label management, the complex samples "
            "module for design-based estimation, cross-tabulation and "
            "significance testing, syntax files for repeatable analysis, and "
            "output export into statistical releases."
        ),
    },
    {
        "code": "SAS",
        "name": "SAS for Large-Scale Data Processing",
        "cluster": "TECHNICAL",
        "frac_type": "functional",
        "kind": "skill",
        "decay": "tools_platforms",
        "description": (
            "Processing large statistical datasets in SAS. Covers the DATA step "
            "and PROC SQL, merging and summarising survey files at scale, the "
            "SURVEYMEANS and SURVEYFREQ procedures for design-based estimation, "
            "macro programming for repeated survey rounds, and batch execution "
            "for production pipelines."
        ),
    },
    {
        "code": "GIS",
        "name": "Geospatial Analysis & Mapping",
        "cluster": "TECHNICAL",
        "frac_type": "functional",
        "kind": "skill",
        "decay": "tools_platforms",
        "description": (
            "Applying geographic information systems to statistical work. Covers "
            "coordinate reference systems, vector and raster data, administrative "
            "boundary hierarchies down to village level, choropleth mapping of "
            "indicators, geocoding of sampling frames, and spatial checks on field "
            "coverage."
        ),
    },
    {
        "code": "DATA_VIZ",
        "name": "Data Visualisation & Statistical Reporting",
        "cluster": "TECHNICAL",
        "frac_type": "functional",
        "kind": "skill",
        "decay": "tools_platforms",
        "description": (
            "Communicating statistical results visually and in writing. Covers "
            "chart selection for the question being answered, honest axis scaling, "
            "accessible colour, representation of sampling uncertainty, small "
            "multiples for state and district comparison, and dashboard design "
            "for policy audiences."
        ),
    },
    {
        "code": "MACHINE_LEARNING",
        "name": "Artificial Intelligence & Machine Learning",
        "cluster": "TECHNICAL",
        "frac_type": "functional",
        "kind": "skill",
        "decay": "tools_platforms",
        "description": (
            "Applying supervised and unsupervised learning to statistical office "
            "problems. Covers automated coding of occupation and industry text, "
            "record linkage across administrative registers, outlier detection in "
            "enterprise returns, evaluation discipline under class imbalance, the "
            "use of large language models for text processing, and the limits of "
            "prediction as a substitute for measurement."
        ),
    },
    {
        "code": "CLOUD",
        "name": "Cloud Computing & Big Data Platforms",
        "cluster": "TECHNICAL",
        "frac_type": "functional",
        "kind": "skill",
        "decay": "tools_platforms",
        "description": (
            "Running analytical workloads on cloud and big data platforms. Covers "
            "service models and shared responsibility, object storage, managed "
            "databases, distributed processing for datasets too large for a single "
            "machine, container basics, and cost control for analytical workloads."
        ),
    },
    {
        "code": "APIS",
        "name": "APIs & System Interoperability",
        "cluster": "TECHNICAL",
        "frac_type": "functional",
        "kind": "skill",
        "decay": "tools_platforms",
        "description": (
            "Exchanging data between government systems through interfaces. "
            "Covers REST principles, authentication and API keys, pagination and "
            "rate limiting, schema versioning and backward compatibility, SDMX "
            "web services for statistical exchange, and the design of an interface "
            "contract that outlives the system behind it."
        ),
    },
    {
        "code": "OPEN_DATA",
        "name": "Open Data & Data Dissemination",
        "cluster": "TECHNICAL",
        "frac_type": "functional",
        "kind": "skill",
        "decay": "regulatory_procedural",
        "description": (
            "Publishing statistics for public reuse. Covers the National Data "
            "Sharing and Accessibility Policy, machine-readable formats and "
            "licensing, dataset cataloguing and discoverability, versioning and "
            "revision notices, microdata release procedures, and the balance "
            "between openness and respondent confidentiality."
        ),
    },
    # ── DIGITAL GOVERNANCE ───────────────────────────────────────────────────
    {
        "code": "CYBERSECURITY",
        "name": "Cybersecurity for Statistical Systems",
        "cluster": "DIGITAL_GOVERNANCE",
        "frac_type": "functional",
        "kind": "skill",
        "decay": "tools_platforms",
        "description": (
            "Protecting statistical systems and the data they hold. Covers threat "
            "models relevant to a statistical office, access control and least "
            "privilege, secure handling of unit-level data in transit and at rest, "
            "incident response and reporting obligations, secure configuration "
            "baselines, and the CERT-In directions applicable to government bodies."
        ),
    },
    {
        "code": "DATA_PRIVACY",
        "name": "Data Privacy & Statistical Disclosure Control",
        "cluster": "DIGITAL_GOVERNANCE",
        "frac_type": "behavioural",
        "kind": "skill",
        "decay": "regulatory_procedural",
        "description": (
            "Protecting the confidentiality of unit-level statistical data. "
            "Covers the legal duty of confidentiality owed to respondents under "
            "the Collection of Statistics Act, obligations under the Digital "
            "Personal Data Protection Act, identification risk assessment, cell "
            "suppression, rounding and record swapping, and preparation of "
            "public-use microdata files."
        ),
    },
    {
        "code": "DIGITAL_SIGNATURES",
        "name": "Digital Signatures & e-Authentication",
        "cluster": "DIGITAL_GOVERNANCE",
        "frac_type": "functional",
        "kind": "skill",
        "decay": "regulatory_procedural",
        "description": (
            "Establishing authenticity and non-repudiation in government "
            "workflows. Covers public key infrastructure, digital signature "
            "certificates and their classes, the legal standing of electronic "
            "signatures under the Information Technology Act, eSign and Aadhaar-"
            "based authentication, and the signing of statistical releases and "
            "official approvals."
        ),
    },
    {
        "code": "GOV_CLOUD",
        "name": "Government Cloud & Empanelled Infrastructure",
        "cluster": "DIGITAL_GOVERNANCE",
        "frac_type": "functional",
        "kind": "skill",
        "decay": "regulatory_procedural",
        "description": (
            "Deploying on government cloud infrastructure. Covers the MeghRaj "
            "policy, empanelled cloud service providers and their audit "
            "obligations, data localisation requirements for government "
            "workloads, the National Informatics Centre hosting model, and the "
            "procurement and security clearance path for a new deployment."
        ),
    },
    {
        "code": "DPI",
        "name": "Digital Public Infrastructure",
        "cluster": "DIGITAL_GOVERNANCE",
        "frac_type": "domain",
        "kind": "knowledge",
        "decay": "regulatory_procedural",
        "description": (
            "Working within India's digital public infrastructure. Covers the "
            "identity, payments and data-exchange layers, consent-based data "
            "sharing through account aggregator patterns, API Setu and "
            "interoperability standards, the use of administrative data held in "
            "these systems as a statistical source, and the governance questions "
            "that raises."
        ),
    },
    # ── BEHAVIOURAL AND MANAGERIAL ───────────────────────────────────────────
    {
        "code": "LEADERSHIP",
        "name": "Leadership & Team Development",
        "cluster": "BEHAVIOURAL",
        "frac_type": "behavioural",
        "kind": "attribute",
        "decay": "behavioural",
        "description": (
            "Leading statistical teams and units. Covers setting direction under "
            "competing demands, delegation and development of subordinate staff, "
            "performance conversations, building technical capability inside a "
            "unit, and representing the statistical position to administrative "
            "leadership without overstating what the data supports."
        ),
    },
    {
        "code": "COMMUNICATION",
        "name": "Communication & Statistical Literacy Outreach",
        "cluster": "BEHAVIOURAL",
        "frac_type": "behavioural",
        "kind": "attribute",
        "decay": "behavioural",
        "description": (
            "Explaining statistics to people who are not statisticians. Covers "
            "writing for policy readers, press releases and briefing notes, "
            "handling questions about revisions and methodology changes, "
            "communicating uncertainty without inviting dismissal, and responding "
            "to public misinterpretation of a published figure."
        ),
    },
    {
        "code": "PROJECT_MGMT",
        "name": "Project & Survey Operations Management",
        "cluster": "BEHAVIOURAL",
        "frac_type": "behavioural",
        "kind": "skill",
        "decay": "methodology",
        "description": (
            "Planning and controlling statistical projects from sanction to "
            "release. Covers work breakdown and scheduling across field seasons, "
            "budgeting for enumerator deployment, risk registers for non-response "
            "and field disruption, quality assurance checkpoints, and reporting to "
            "controlling authorities and stakeholders."
        ),
    },
    {
        "code": "ETHICS",
        "name": "Professional Ethics & Statistical Independence",
        "cluster": "BEHAVIOURAL",
        "frac_type": "behavioural",
        "kind": "attribute",
        "decay": "behavioural",
        "description": (
            "Upholding the integrity of official statistics. Covers the "
            "Fundamental Principles of Official Statistics, professional "
            "independence in the face of pressure on a result, impartiality in "
            "method selection, release calendars and equal access, the duty owed "
            "to respondents, and the correct handling of an error found after "
            "publication."
        ),
    },
    {
        "code": "DECISION_MAKING",
        "name": "Evidence-Based Decision Making",
        "cluster": "BEHAVIOURAL",
        "frac_type": "behavioural",
        "kind": "attribute",
        "decay": "behavioural",
        "description": (
            "Turning statistical evidence into defensible decisions. Covers "
            "framing a policy question so data can answer it, reasoning under "
            "uncertainty and with incomplete evidence, distinguishing correlation "
            "from causation in a policy argument, cost and risk trade-offs, and "
            "documenting the basis of a decision so it can be reviewed later."
        ),
    },
    {
        "code": "CHANGE_MGMT",
        "name": "Change Management & Digital Adoption",
        "cluster": "BEHAVIOURAL",
        "frac_type": "behavioural",
        "kind": "attribute",
        "decay": "behavioural",
        "description": (
            "Leading the adoption of new methods and systems in a statistical "
            "office. Covers stakeholder analysis and resistance, phased rollout of "
            "a new instrument or platform, training and support during transition, "
            "the migration from paper to computer-assisted personal interviewing, "
            "and sustaining a change after the project team disbands."
        ),
    },
]


def by_cluster() -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for competency in COMPETENCIES:
        grouped.setdefault(competency["cluster"], []).append(competency)
    return grouped


CODES: set[str] = {c["code"] for c in COMPETENCIES}
