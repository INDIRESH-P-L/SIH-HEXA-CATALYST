"""Expanded initial-assessment question bank.

Seeds approved MCQ questions for PYTHON, SAMPLING, SURVEY_DESIGN, DATA_QUALITY,
and DATA_VIZ competencies so that the initial competency assessment has questions
to serve for roles in the Official Statistical System.

Each question is inserted directly as APPROVED (same as the SQL bank),
bypassing the AI-generation gate because these are hand-written reference items.
The embedding validation gate is also skipped to avoid requiring a live
embedding model at seed time. The questions are stored with ``status='APPROVED'``
and ``validation.origin='seeded'`` to be auditable in the trainer console.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.competency import Competency
from app.models.question import Question

log = get_logger(__name__)

# ── Question bank definition ──────────────────────────────────────────────────
# Each entry: question_text, options (4), correct_index (0-based), explanation,
# difficulty (easy|medium|hard), topic, competency_code.

BANK: list[dict[str, Any]] = [
    # ── PYTHON ───────────────────────────────────────────────────────────────
    {
        "competency_code": "PYTHON",
        "question_text": "Which Python library is most commonly used for data manipulation and analysis?",
        "options": ["NumPy", "Matplotlib", "Pandas", "SciPy"],
        "correct_index": 2,
        "explanation": "Pandas provides DataFrame structures for data cleaning and analysis.",
        "difficulty": "easy",
        "topic": "Data Libraries",
    },
    {
        "competency_code": "PYTHON",
        "question_text": "What does the 'df.dropna()' function do in Pandas?",
        "options": [
            "Drops all columns with NA in name",
            "Removes rows containing any missing values",
            "Fills NA values with zero",
            "Counts the number of NA values",
        ],
        "correct_index": 1,
        "explanation": "dropna() removes rows (or columns) that contain missing/NaN values.",
        "difficulty": "easy",
        "topic": "Data Cleaning",
    },
    {
        "competency_code": "PYTHON",
        "question_text": "In Python, what is the output of: list(range(2, 10, 3))?",
        "options": ["[2, 5, 8]", "[2, 4, 6, 8]", "[3, 6, 9]", "[2, 5, 8, 11]"],
        "correct_index": 0,
        "explanation": "range(start, stop, step) → 2, 5, 8 (stops before 10).",
        "difficulty": "easy",
        "topic": "Python Basics",
    },
    {
        "competency_code": "PYTHON",
        "question_text": "Which method applies a function to every element of a Pandas Series?",
        "options": ["df.apply()", "df.map()", "series.apply()", "series.map()"],
        "correct_index": 3,
        "explanation": "Series.map() applies a function element-wise to a Series.",
        "difficulty": "medium",
        "topic": "Data Transformation",
    },
    {
        "competency_code": "PYTHON",
        "question_text": "What does 'groupby' return before an aggregation is applied in Pandas?",
        "options": [
            "A DataFrame with grouped values",
            "A DataFrameGroupBy object",
            "A list of DataFrames",
            "A dictionary of indices",
        ],
        "correct_index": 1,
        "explanation": "groupby() returns a DataFrameGroupBy object. Aggregation (e.g. .mean()) produces the result.",
        "difficulty": "medium",
        "topic": "Data Aggregation",
    },
    {
        "competency_code": "PYTHON",
        "question_text": "Which of the following correctly reads a CSV file and sets the first column as the index?",
        "options": [
            "pd.read_csv('f.csv', index=0)",
            "pd.read_csv('f.csv', set_index=0)",
            "pd.read_csv('f.csv', index_col=0)",
            "pd.read_csv('f.csv', header=0)",
        ],
        "correct_index": 2,
        "explanation": "index_col=0 tells Pandas to use the first column as the row index.",
        "difficulty": "medium",
        "topic": "File I/O",
    },
    {
        "competency_code": "PYTHON",
        "question_text": "In NumPy, which operation broadcasts correctly to add a shape (3,1) array to a shape (1,4) array?",
        "options": [
            "It raises a shape mismatch error",
            "Result shape is (3,4) by broadcasting rules",
            "Result shape is (3,1)",
            "Result shape is (1,4)",
        ],
        "correct_index": 1,
        "explanation": "NumPy broadcasting expands (3,1) and (1,4) to both become (3,4).",
        "difficulty": "hard",
        "topic": "NumPy",
    },
    {
        "competency_code": "PYTHON",
        "question_text": "What is the correct way to handle exceptions in Python when reading an external file?",
        "options": [
            "Use 'catch' block",
            "Use 'try/except' block",
            "Use 'on_error' parameter",
            "Use 'assert' statement",
        ],
        "correct_index": 1,
        "explanation": "Python uses try/except to catch and handle exceptions.",
        "difficulty": "easy",
        "topic": "Error Handling",
    },
    {
        "competency_code": "PYTHON",
        "question_text": "Which Pandas function merges two DataFrames on a common column (like SQL JOIN)?",
        "options": ["pd.concat()", "pd.merge()", "pd.join()", "pd.append()"],
        "correct_index": 1,
        "explanation": "pd.merge() performs SQL-style joins on common keys.",
        "difficulty": "medium",
        "topic": "Data Merging",
    },
    {
        "competency_code": "PYTHON",
        "question_text": "What does 'df.describe()' return for a numeric DataFrame?",
        "options": [
            "Column data types",
            "First 5 rows of the DataFrame",
            "Summary statistics: count, mean, std, min, max, quartiles",
            "The shape of the DataFrame",
        ],
        "correct_index": 2,
        "explanation": "describe() outputs descriptive statistics for numeric columns.",
        "difficulty": "easy",
        "topic": "Exploratory Analysis",
    },

    # ── SAMPLING ──────────────────────────────────────────────────────────────
    {
        "competency_code": "SAMPLING",
        "question_text": "Which sampling method ensures every member of the population has an equal chance of selection?",
        "options": [
            "Convenience sampling",
            "Simple random sampling",
            "Quota sampling",
            "Purposive sampling",
        ],
        "correct_index": 1,
        "explanation": "Simple random sampling gives each unit an equal and independent chance of selection.",
        "difficulty": "easy",
        "topic": "Sampling Methods",
    },
    {
        "competency_code": "SAMPLING",
        "question_text": "In stratified random sampling, the population is divided into:",
        "options": [
            "Clusters based on geography",
            "Homogeneous subgroups called strata",
            "Random groups of equal size",
            "Systematic intervals",
        ],
        "correct_index": 1,
        "explanation": "Stratified sampling divides the population into mutually exclusive, homogeneous strata before sampling.",
        "difficulty": "easy",
        "topic": "Stratified Sampling",
    },
    {
        "competency_code": "SAMPLING",
        "question_text": "What is the main advantage of cluster sampling over simple random sampling?",
        "options": [
            "It eliminates sampling error",
            "It is more cost-effective for geographically dispersed populations",
            "It always produces smaller standard errors",
            "It requires a complete sampling frame",
        ],
        "correct_index": 1,
        "explanation": "Cluster sampling reduces travel/enumeration costs by sampling clusters (e.g. villages) rather than individuals.",
        "difficulty": "medium",
        "topic": "Cluster Sampling",
    },
    {
        "competency_code": "SAMPLING",
        "question_text": "The sampling frame is best described as:",
        "options": [
            "A diagram showing the survey structure",
            "The complete list of units from which the sample is drawn",
            "The set of questions asked in the survey",
            "The statistical model used for estimation",
        ],
        "correct_index": 1,
        "explanation": "The sampling frame is the operational definition of the population — the list from which units are selected.",
        "difficulty": "easy",
        "topic": "Sampling Concepts",
    },
    {
        "competency_code": "SAMPLING",
        "question_text": "Systematic sampling selects every k-th unit after a random start. A key risk is:",
        "options": [
            "Underrepresentation of large units",
            "Periodicity bias if the list has a periodic pattern",
            "Requirement of a complete sampling frame",
            "Higher cost than simple random sampling",
        ],
        "correct_index": 1,
        "explanation": "Periodicity bias occurs when the sampling interval coincides with a cyclical pattern in the list.",
        "difficulty": "medium",
        "topic": "Systematic Sampling",
    },
    {
        "competency_code": "SAMPLING",
        "question_text": "In Probability Proportional to Size (PPS) sampling, larger units have:",
        "options": [
            "Equal chance as smaller units",
            "Lower chance than smaller units",
            "Higher probability of selection proportional to their size measure",
            "No chance of selection",
        ],
        "correct_index": 2,
        "explanation": "PPS selects units with probabilities proportional to a size measure (e.g., number of workers), reducing variance for skewed populations.",
        "difficulty": "hard",
        "topic": "PPS Sampling",
    },
    {
        "competency_code": "SAMPLING",
        "question_text": "The design effect (DEFF) in complex surveys measures:",
        "options": [
            "Non-response rates in the sample",
            "The ratio of the actual variance to the variance under SRS of the same size",
            "The proportion of the population sampled",
            "The cost per unit in the sample",
        ],
        "correct_index": 1,
        "explanation": "DEFF = Var(complex design) / Var(SRS). DEFF > 1 means the design is less efficient than SRS.",
        "difficulty": "hard",
        "topic": "Design Effect",
    },
    {
        "competency_code": "SAMPLING",
        "question_text": "Non-sampling error differs from sampling error in that it:",
        "options": [
            "Decreases as sample size increases",
            "Is caused only by using a biased sampling frame",
            "Cannot be reduced by increasing sample size and includes response and processing errors",
            "Only occurs in census operations",
        ],
        "correct_index": 2,
        "explanation": "Non-sampling errors (measurement error, non-response, data processing errors) are not reduced by larger samples.",
        "difficulty": "medium",
        "topic": "Survey Errors",
    },
    {
        "competency_code": "SAMPLING",
        "question_text": "Which formula gives the required sample size n for estimating a proportion p with margin of error e at 95% confidence (z=1.96)?",
        "options": [
            "n = z² × p(1-p) / e²",
            "n = z × p / e",
            "n = z² / e²",
            "n = p × e / z²",
        ],
        "correct_index": 0,
        "explanation": "n = z² × p(1-p) / e² is the standard formula for sample size for proportions.",
        "difficulty": "hard",
        "topic": "Sample Size Determination",
    },
    {
        "competency_code": "SAMPLING",
        "question_text": "In two-stage cluster sampling, the primary sampling units (PSUs) are:",
        "options": [
            "Individual respondents",
            "Clusters selected in the first stage",
            "Strata selected before sampling",
            "Replacement units for non-respondents",
        ],
        "correct_index": 1,
        "explanation": "PSUs are the clusters (e.g., villages, blocks) selected in the first stage; secondary units are sampled within them.",
        "difficulty": "medium",
        "topic": "Multi-stage Sampling",
    },

    # ── SURVEY_DESIGN ─────────────────────────────────────────────────────────
    {
        "competency_code": "SURVEY_DESIGN",
        "question_text": "A closed-ended question in a survey:",
        "options": [
            "Allows respondents to answer in their own words",
            "Provides a fixed set of response options",
            "Is only used in qualitative surveys",
            "Avoids measurement bias entirely",
        ],
        "correct_index": 1,
        "explanation": "Closed-ended questions offer predefined response categories, making data easier to code and analyse.",
        "difficulty": "easy",
        "topic": "Questionnaire Design",
    },
    {
        "competency_code": "SURVEY_DESIGN",
        "question_text": "The 'reference period' in a survey question refers to:",
        "options": [
            "The time period within which the respondent recalls information",
            "The date the survey was published",
            "The period the enumerator spends per household",
            "The validity period of the consent form",
        ],
        "correct_index": 0,
        "explanation": "Reference period anchors the respondent's recall to a specific time window (e.g., 'last 30 days').",
        "difficulty": "easy",
        "topic": "Questionnaire Design",
    },
    {
        "competency_code": "SURVEY_DESIGN",
        "question_text": "Recall bias in surveys occurs when:",
        "options": [
            "Respondents give socially desirable answers",
            "Enumerators record incorrect data intentionally",
            "Respondents inaccurately remember past events or behaviours",
            "The sampling frame misses certain population groups",
        ],
        "correct_index": 2,
        "explanation": "Recall bias is memory-related measurement error, particularly acute for long reference periods.",
        "difficulty": "medium",
        "topic": "Survey Errors",
    },
    {
        "competency_code": "SURVEY_DESIGN",
        "question_text": "Pre-testing a questionnaire is done to:",
        "options": [
            "Select the final sample",
            "Train enumerators on data entry software",
            "Identify problems with question wording, flow and response options before the main survey",
            "Calculate the required sample size",
        ],
        "correct_index": 2,
        "explanation": "Pre-testing (pilot) reveals ambiguous wording, skip logic errors, and translation issues before fieldwork.",
        "difficulty": "easy",
        "topic": "Pilot Testing",
    },
    {
        "competency_code": "SURVEY_DESIGN",
        "question_text": "Which data collection mode generally achieves the highest response rate?",
        "options": [
            "Web (online) surveys",
            "Mail surveys",
            "Face-to-face personal interviews",
            "Interactive voice response (IVR)",
        ],
        "correct_index": 2,
        "explanation": "Face-to-face interviews typically achieve the highest response rates due to personal contact, at the cost of higher expense.",
        "difficulty": "medium",
        "topic": "Data Collection Modes",
    },
    {
        "competency_code": "SURVEY_DESIGN",
        "question_text": "Unit non-response in a survey refers to:",
        "options": [
            "A respondent refusing to answer one or more questions",
            "An entire sampled unit (household or individual) failing to participate",
            "Questions left blank due to skip patterns",
            "Enumerator errors in recording responses",
        ],
        "correct_index": 1,
        "explanation": "Unit non-response is when a selected unit provides no data at all; item non-response is when individual questions are skipped.",
        "difficulty": "medium",
        "topic": "Non-Response",
    },
    {
        "competency_code": "SURVEY_DESIGN",
        "question_text": "CAPI (Computer-Assisted Personal Interviewing) reduces which type of error?",
        "options": [
            "Coverage error",
            "Sampling error",
            "Data entry and skip-logic errors",
            "Recall bias",
        ],
        "correct_index": 2,
        "explanation": "CAPI enforces skip patterns and range checks electronically, reducing transcription and routing errors.",
        "difficulty": "medium",
        "topic": "Data Collection Technology",
    },
    {
        "competency_code": "SURVEY_DESIGN",
        "question_text": "Double-barrelled questions are problematic because:",
        "options": [
            "They are too long for respondents to read",
            "They ask about two different things simultaneously, making answers ambiguous",
            "They use technical jargon",
            "They are only suitable for literate respondents",
        ],
        "correct_index": 1,
        "explanation": "e.g., 'Do you support the policy and its funding?' — the respondent may agree with one part but not the other.",
        "difficulty": "easy",
        "topic": "Questionnaire Design",
    },
    {
        "competency_code": "SURVEY_DESIGN",
        "question_text": "Weighting in survey estimation is used to:",
        "options": [
            "Reduce the physical weight of survey forms",
            "Correct for unequal selection probabilities and non-response so estimates represent the target population",
            "Make all strata equal in size",
            "Remove outliers from the dataset",
        ],
        "correct_index": 1,
        "explanation": "Weights are the inverse of selection probabilities, adjusted for non-response and calibrated to known totals.",
        "difficulty": "hard",
        "topic": "Estimation and Weighting",
    },
    {
        "competency_code": "SURVEY_DESIGN",
        "question_text": "In a longitudinal (panel) survey, the same respondents are interviewed:",
        "options": [
            "Once, at a single point in time",
            "In different regions each round",
            "Repeatedly over time to track change",
            "After being replaced each round",
        ],
        "correct_index": 2,
        "explanation": "Panel surveys follow the same units over time, enabling measurement of change at the individual level.",
        "difficulty": "medium",
        "topic": "Survey Types",
    },

    # ── DATA_QUALITY ──────────────────────────────────────────────────────────
    {
        "competency_code": "DATA_QUALITY",
        "question_text": "Which of the following is NOT one of the five core dimensions of data quality?",
        "options": ["Accuracy", "Timeliness", "Consistency", "Scalability"],
        "correct_index": 3,
        "explanation": "Core data quality dimensions include accuracy, completeness, consistency, timeliness, and validity. Scalability is a system attribute, not a data quality dimension.",
        "difficulty": "easy",
        "topic": "Data Quality Dimensions",
    },
    {
        "competency_code": "DATA_QUALITY",
        "question_text": "Data completeness refers to:",
        "options": [
            "Whether data values are within expected ranges",
            "Whether all required data fields contain valid values",
            "Whether the data has been encrypted",
            "Whether data is collected from the entire population",
        ],
        "correct_index": 1,
        "explanation": "Completeness measures whether all mandatory fields are populated without missing values.",
        "difficulty": "easy",
        "topic": "Data Quality Dimensions",
    },
    {
        "competency_code": "DATA_QUALITY",
        "question_text": "An outlier in a dataset is best described as:",
        "options": [
            "A data point with a missing value",
            "A data point that falls outside the expected distribution or range",
            "A duplicate record in the dataset",
            "A data point collected from a different source",
        ],
        "correct_index": 1,
        "explanation": "Outliers are values that differ significantly from other observations and may indicate errors or genuine anomalies.",
        "difficulty": "easy",
        "topic": "Data Anomalies",
    },
    {
        "competency_code": "DATA_QUALITY",
        "question_text": "Hot-deck imputation fills missing values by:",
        "options": [
            "Using the overall mean of the variable",
            "Substituting a value from a similar responding unit in the same dataset",
            "Deleting all records with missing values",
            "Using a regression model to predict the missing value",
        ],
        "correct_index": 1,
        "explanation": "Hot-deck imputation replaces missing values with actual values from a 'donor' record that closely matches the recipient.",
        "difficulty": "medium",
        "topic": "Imputation Methods",
    },
    {
        "competency_code": "DATA_QUALITY",
        "question_text": "Data validation rules are used to:",
        "options": [
            "Compress data for storage",
            "Automatically correct all errors in the dataset",
            "Check that data values meet defined constraints before or after entry",
            "Encrypt sensitive fields in the database",
        ],
        "correct_index": 2,
        "explanation": "Validation rules (range checks, type checks, consistency checks) ensure data conforms to defined standards.",
        "difficulty": "easy",
        "topic": "Data Validation",
    },
    {
        "competency_code": "DATA_QUALITY",
        "question_text": "The concept of 'fitness for purpose' in data quality means:",
        "options": [
            "Data must be collected by government agencies",
            "Data quality requirements depend on how the data will be used",
            "Data must pass all statistical validation tests",
            "Data must be available in digital format",
        ],
        "correct_index": 1,
        "explanation": "Data quality is relative — the same dataset may be fit for one purpose but inadequate for another requiring higher precision.",
        "difficulty": "medium",
        "topic": "Data Quality Concepts",
    },
    {
        "competency_code": "DATA_QUALITY",
        "question_text": "Which technique detects duplicate records in a large administrative dataset?",
        "options": [
            "Data normalisation",
            "Record linkage / probabilistic matching",
            "Hot-deck imputation",
            "Winsorisation",
        ],
        "correct_index": 1,
        "explanation": "Record linkage compares records across or within datasets using fuzzy matching to identify duplicates without exact keys.",
        "difficulty": "medium",
        "topic": "Data Deduplication",
    },
    {
        "competency_code": "DATA_QUALITY",
        "question_text": "Winsorisation is a technique used to handle:",
        "options": [
            "Missing values in survey data",
            "Extreme outliers that distort estimates without deletion",
            "Duplicate records in a database",
            "Measurement errors in qualitative data",
        ],
        "correct_index": 1,
        "explanation": "Winsorisation caps extreme values at a percentile threshold, reducing their influence while keeping all records.",
        "difficulty": "hard",
        "topic": "Outlier Treatment",
    },
    {
        "competency_code": "DATA_QUALITY",
        "question_text": "Referential integrity in a relational database ensures that:",
        "options": [
            "All numeric columns contain non-null values",
            "Foreign key values always reference an existing primary key",
            "Data is stored in normalised third normal form",
            "Index structures are maintained for fast queries",
        ],
        "correct_index": 1,
        "explanation": "Referential integrity means a foreign key value must match an existing primary key in the referenced table.",
        "difficulty": "medium",
        "topic": "Database Quality",
    },
    {
        "competency_code": "DATA_QUALITY",
        "question_text": "A data quality assessment framework typically includes all EXCEPT:",
        "options": [
            "Profiling data to measure quality dimensions",
            "Establishing quality thresholds",
            "Marketing the database to external users",
            "Root cause analysis of quality issues",
        ],
        "correct_index": 2,
        "explanation": "DQ frameworks focus on measurement, thresholds, root-cause analysis, and remediation — not marketing.",
        "difficulty": "medium",
        "topic": "DQ Frameworks",
    },

    # ── DATA_VIZ ──────────────────────────────────────────────────────────────
    {
        "competency_code": "DATA_VIZ",
        "question_text": "Which chart type is most appropriate for showing the composition of a whole as parts?",
        "options": ["Line chart", "Scatter plot", "Pie or donut chart", "Box plot"],
        "correct_index": 2,
        "explanation": "Pie/donut charts show part-to-whole relationships. They work best with 2–5 categories.",
        "difficulty": "easy",
        "topic": "Chart Selection",
    },
    {
        "competency_code": "DATA_VIZ",
        "question_text": "A box plot displays which five summary statistics?",
        "options": [
            "Mean, mode, range, variance, kurtosis",
            "Minimum, Q1, median, Q3, maximum",
            "Count, mean, std, min, max",
            "P10, P25, P50, P75, P90",
        ],
        "correct_index": 1,
        "explanation": "Box plots show the five-number summary: min, lower quartile (Q1), median, upper quartile (Q3), max.",
        "difficulty": "easy",
        "topic": "Statistical Charts",
    },
    {
        "competency_code": "DATA_VIZ",
        "question_text": "What is the main purpose of a scatter plot?",
        "options": [
            "To show trends over time",
            "To display the relationship or correlation between two continuous variables",
            "To compare categories side by side",
            "To show the frequency distribution of one variable",
        ],
        "correct_index": 1,
        "explanation": "Scatter plots reveal correlation, clusters, and outliers between two quantitative variables.",
        "difficulty": "easy",
        "topic": "Chart Selection",
    },
    {
        "competency_code": "DATA_VIZ",
        "question_text": "The principle of 'data-ink ratio' in visualisation design (Tufte) recommends:",
        "options": [
            "Using as many colours as possible to highlight data",
            "Maximising the proportion of ink used to display actual data rather than decoration",
            "Always using 3D effects to make charts visually appealing",
            "Including gridlines and borders on every chart",
        ],
        "correct_index": 1,
        "explanation": "Tufte's data-ink ratio principle: remove all non-data ink (chart junk) to focus attention on the data.",
        "difficulty": "medium",
        "topic": "Visualisation Principles",
    },
    {
        "competency_code": "DATA_VIZ",
        "question_text": "Which visualisation is most suitable for displaying the distribution of a large continuous dataset?",
        "options": ["Bar chart", "Pie chart", "Histogram", "Gantt chart"],
        "correct_index": 2,
        "explanation": "Histograms show the frequency distribution of continuous data by grouping values into bins.",
        "difficulty": "easy",
        "topic": "Chart Selection",
    },
    {
        "competency_code": "DATA_VIZ",
        "question_text": "A choropleth map is used to:",
        "options": [
            "Show network connections between nodes",
            "Display geographic variation by shading regions according to a statistical variable",
            "Compare distributions of multiple groups",
            "Visualise time-series data with multiple variables",
        ],
        "correct_index": 1,
        "explanation": "Choropleth maps shade geographic areas proportional to a variable (e.g., state-level poverty rates).",
        "difficulty": "medium",
        "topic": "Geospatial Visualisation",
    },
    {
        "competency_code": "DATA_VIZ",
        "question_text": "When comparing multiple time series on the same chart, which principle is critical?",
        "options": [
            "Use a separate y-axis for each series by default",
            "Ensure the y-axis starts at zero for line charts",
            "Use consistent scales and clear legends to avoid misinterpretation",
            "Always use a stacked area chart",
        ],
        "correct_index": 2,
        "explanation": "Consistent scales and clear legends prevent misleading comparisons between series.",
        "difficulty": "medium",
        "topic": "Visualisation Principles",
    },
    {
        "competency_code": "DATA_VIZ",
        "question_text": "Which Python library is specifically designed for interactive, web-based statistical visualisations?",
        "options": ["Matplotlib", "Seaborn", "Plotly", "Pillow"],
        "correct_index": 2,
        "explanation": "Plotly produces interactive charts renderable in web browsers, supporting hover, zoom, and filter controls.",
        "difficulty": "medium",
        "topic": "Visualisation Tools",
    },
    {
        "competency_code": "DATA_VIZ",
        "question_text": "Dual y-axes on a single chart can be problematic because:",
        "options": [
            "They require two datasets",
            "They can mislead viewers about the relationship between two variables by manipulating scale",
            "They are unsupported by most charting libraries",
            "They increase the data-ink ratio",
        ],
        "correct_index": 1,
        "explanation": "Dual axes allow arbitrary scale manipulation that can falsely imply correlation or patterns.",
        "difficulty": "hard",
        "topic": "Visualisation Pitfalls",
    },
    {
        "competency_code": "DATA_VIZ",
        "question_text": "In a dashboard for government statistics, 'drill-down' functionality allows users to:",
        "options": [
            "Export data to a spreadsheet",
            "Navigate from a high-level summary to more detailed underlying data",
            "Apply colour themes to the dashboard",
            "Schedule automated report delivery",
        ],
        "correct_index": 1,
        "explanation": "Drill-down lets users click on an aggregate value to see the detailed breakdown (e.g., national → state → district).",
        "difficulty": "medium",
        "topic": "Dashboard Design",
    },
]


async def seed_initial_assessment_bank(session: AsyncSession) -> dict[str, int]:
    """Insert hand-written MCQs for the initial-assessment competencies.

    Idempotent: skips questions whose text already exists for that competency.
    Returns counts per competency.
    """
    from app.ai import embeddings  # import here so caller can skip if no model

    competency_codes = set(q["competency_code"] for q in BANK)

    # Load competency map: code → id
    comp_map: dict[str, Competency] = {}
    for code in competency_codes:
        comp = await session.scalar(select(Competency).where(Competency.code == code))
        if comp is None:
            log.warning("Competency %s not found — skipping those questions.", code)
        else:
            comp_map[code] = comp

    totals: dict[str, int] = {c: 0 for c in competency_codes}

    for spec in BANK:
        code = spec["competency_code"]
        comp = comp_map.get(code)
        if comp is None:
            continue

        # Idempotency: skip if already seeded
        existing = await session.scalar(
            select(Question.id)
            .where(Question.competency_id == comp.id)
            .where(Question.question_text == spec["question_text"])
        )
        if existing is not None:
            continue

        try:
            vector = embeddings.embed_one(
                f"{spec['question_text']} {' '.join(spec['options'])}"
            )
        except Exception:
            vector = None  # embed_one may fail without a model; store without embedding

        session.add(
            Question(
                material_id=None,
                chunk_id=None,
                competency_id=comp.id,
                question_text=spec["question_text"],
                options=spec["options"],
                correct_index=spec["correct_index"],
                explanation=spec["explanation"],
                difficulty=spec["difficulty"],
                topic=spec["topic"],
                status="APPROVED",
                validation={
                    "origin": "seeded",
                    "note": (
                        "Hand-written reference item for initial competency assessment. "
                        "Not model-generated."
                    ),
                    "passed": True,
                },
                source_page=None,
                embedding=vector,
                is_negative_example=False,
            )
        )
        totals[code] = totals.get(code, 0) + 1

    await session.flush()

    # Count totals
    for code, comp in comp_map.items():
        n = await session.scalar(
            select(func.count())
            .select_from(Question)
            .where(Question.competency_id == comp.id)
            .where(Question.status == "APPROVED")
        )
        log.info("%-25s approved questions: %d", code, int(n or 0))

    return totals
