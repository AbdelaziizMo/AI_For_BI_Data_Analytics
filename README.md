# AI for BI & Data Analytics

An end-to-end AI-assisted Business Intelligence and Data Analytics pipeline that combines **Gemini, Oracle, Python, SQL validation, privacy controls, and automated business analysis**.

The project demonstrates how Generative AI can assist BI and Data Engineering workflows while keeping raw transaction-level data inside the controlled execution environment.

---

## 1. Project Overview

This project was developed as part of the **Week 10 – AI for BI & Data Analytics** training task.

The objective is to demonstrate how AI can support a BI/Data professional across multiple stages of an analytical workflow:

* Business question interpretation
* Analysis planning
* SQL generation
* SQL security validation
* Database execution
* KPI and analytical result generation
* Privacy protection
* AI-assisted business interpretation
* Automated business reporting

A key design principle of this project is:

> **Raw transaction-level data is not sent to the AI analyst.**

Gemini generates analytical logic and SQL, while Python validates and executes the approved SQL against Oracle. Only aggregated analytical results are passed through the Privacy Guard to the AI Business Analyst.

---

# 2. Business Question

> **Which services generate the highest revenue and transaction volume, and how does their performance change over time?**

The analysis focuses on:

* Revenue
* Transaction volume
* Revenue share
* Volume share
* Revenue ranking
* Volume ranking
* Daily revenue
* Daily transaction volume
* Average transaction amount
* Revenue growth
* Volume growth

The analysis identifies the **Top 10 services by overall revenue**.

---

# 3. Solution Architecture

```text
Business Question
        │
        ▼
┌───────────────────────┐
│   Gemini AI Planner   │
└───────────┬───────────┘
            │
            ▼
      Analysis Plan
            │
            ▼
┌────────────────────────────┐
│ Gemini SQL Generator       │
│                            │
│ Generates analytical SQL   │
└────────────┬───────────────┘
             │
             ▼
       Generated SQL
             │
             ▼
┌────────────────────────────┐
│ Python SQL Validator       │
│                            │
│ Security & analytical     │
│ validation                 │
└────────────┬───────────────┘
             │
             ▼
       Validated SQL
             │
             ▼
┌────────────────────────────┐
│ Python Execution Layer     │
└────────────┬───────────────┘
             │
             ▼
          Oracle
             │
             ▼
┌────────────────────────────┐
│ Aggregated Analytical Data │
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│ Privacy Guard              │
│                            │
│ Removes blocked/raw fields │
└────────────┬───────────────┘
             │
             ▼
     Sanitized Analysis
             │
             ▼
┌────────────────────────────┐
│ Gemini AI Business Analyst │
└────────────┬───────────────┘
             │
             ▼
      Business Report
```

---

# 4. AI Workflow

## Step 1 – Business Question

The business question is defined as:

> Which services generate the highest revenue and transaction volume, and how does their performance change over time?

---

## Step 2 – Gemini Planner

Gemini converts the business question into a structured analysis plan.

The generated plan identifies:

* Analysis type: `SERVICE_TREND`
* Dimensions:

  * Service
  * Date
* KPIs:

  * Total Revenue
  * Transaction Volume
  * Revenue Share
  * Volume Share
  * Revenue Growth
  * Volume Growth
  * Revenue Rank
  * Volume Rank
* Top N: `10`

Output:

```text
output/analysis_plan.json
```

---

# 5. AI SQL Generation

Gemini generates analytical SQL based on the approved database schema and analysis plan.

The SQL generator is constrained to:

* Approved Oracle tables
* Confirmed table relationships
* Approved analytical logic
* Parameterized date filtering
* Aggregated analytical output
* No raw transaction-level identifiers in the final output

The generated SQL uses techniques including:

* CTEs
* `ROW_NUMBER()`
* Window functions
* `LAG()`
* Ranking
* Aggregation
* Revenue and volume shares
* Daily trend analysis

Generated SQL:

```text
output/generated_sql.json
```

---

# 6. SQL Validation & Security

Generated SQL is **never executed directly**.

Before execution, the Python SQL Validator checks the generated queries.

Validation includes:

1. Statement count
2. Read-only restrictions
3. `SELECT` / `WITH` requirement
4. Wildcard usage
5. Approved database tables
6. Bind parameters
7. Date filtering
8. Approved service relationship
9. Analytical output and privacy rules

The validator blocks dangerous operations such as:

```text
INSERT
UPDATE
DELETE
MERGE
DROP
ALTER
TRUNCATE
CREATE
GRANT
REVOKE
```

The generated query must be analytical and read-only.

Validated SQL:

```text
output/validated_sql.json
```

---

# 7. Oracle Execution

The validated SQL is executed through Python against the Oracle training database.

The execution layer:

* Loads validated SQL
* Uses date bind parameters
* Connects to Oracle
* Executes the validated query
* Retrieves aggregated analytical results
* Saves the results as JSON

Output:

```text
output/aggregated_results.json
```

The final analytical result contains aggregated service-level and daily metrics rather than raw transaction records.

---

# 8. Privacy Guard

The Privacy Guard is an important part of the architecture.

Its purpose is to ensure that only approved analytical fields are passed to the AI Business Analyst.

### Allowed analytical fields

Examples include:

```text
service_id
service_name
transaction_date
revenue_rank
volume_rank
total_revenue
transaction_volume
daily_revenue
daily_transaction_volume
avg_transaction_amount
revenue_share
volume_share
previous_day_revenue
revenue_growth
previous_day_volume
volume_growth
```

### Blocked raw fields

Examples include:

```text
transactionid
accountidfrom
accountidto
originaltrx
invoiceid
requestid
balancebefore
```

The Privacy Guard:

1. Loads aggregated results
2. Checks for blocked fields
3. Keeps only approved analytical fields
4. Creates a sanitized payload
5. Verifies that the sanitized payload is not empty
6. Saves the sanitized data

Output:

```text
output/sanitized_analysis.json
```

This creates a clear boundary between:

```text
Oracle / Raw Data Environment
            │
            ▼
      Aggregated Data
            │
            ▼
       Privacy Guard
            │
            ▼
       Gemini Analyst
```

---

# 9. AI Business Analyst

After the Privacy Guard completes successfully, Gemini receives the sanitized aggregated analytical data.

The AI Business Analyst generates a structured business report containing:

* Executive Summary
* Key Insights
* Service Performance
* Time Trend Analysis
* Revenue vs Volume Analysis
* Recommendations
* Data Limitations

The analyst is instructed to:

* Use only the supplied aggregated data
* Avoid inventing business causes
* Never request or assume raw transaction-level data
* Treat missing observations as unavailable rather than zero
* Clearly distinguish observations from hypotheses
* Validate numerical relationships
* Respect the Top-N scope
* Avoid unsupported customer behavior claims

Final report:

```text
output/ai_business_report.md
```

---

# 10. Key Analytical Findings

For the analyzed period **July 7–12, 2026**:

### Revenue Concentration

The top two services generated:

* Balance Transfer: **53.04%**
* Extra Commission: **43.25%**

Combined:

**96.29%**

The complete Top-10 revenue group represents:

**98.53%**

Services outside the Top 10 represent:

**1.47%**

---

### High-Volume Services

Examples include:

| Service                 | Transactions | Revenue Share |
| ----------------------- | -----------: | ------------: |
| Balance Transfer        |      209,169 |        53.04% |
| WE ADSL                 |      103,291 |         0.11% |
| South Cairo Electricity |       92,618 |         0.06% |

This demonstrates that transaction volume and revenue contribution can differ significantly.

---

### Major Revenue Spikes

Two significant single-day spikes were identified:

**Extra Commission – July 9**

```text
Daily Revenue: 14.67B
Transactions: 749
Observed Daily Average Transaction Value: 19.58M
```

**Balance Transfer – July 12**

```text
Daily Revenue: 15.62B
Transactions: 45,238
Observed Daily Average Transaction Value: 345,356.71
```

The aggregated dataset does not provide enough information to determine the operational cause of these spikes.

---

# 11. Project Structure

```text
AI_For_BI_Data_Analytics/
│
├── output/
│   ├── aggregated_results.json
│   ├── ai_business_report.md
│   ├── analysis_plan.json
│   ├── generated_sql.json
│   └── sanitized_analysis.json
│
├── prompts/
│   ├── analyst_prompt.md
│   ├── planner_prompt.md
│   └── sql_generator_prompt.md
│
├── sql/
│   ├── analysis_queries.sql
│   ├── improved.sql
│   └── kpi_queries.sql
│
├── src/
│   ├── __init__.py
│   ├── ai_analysis.py
│   ├── ai_planner.py
│   ├── ai_sql_generator.py
│   ├── analysis.py
│   ├── analysis_executor.py
│   ├── config.py
│   ├── data_loader.py
│   ├── database.py
│   ├── privacy_guard.py
│   └── sql_validator.py
│
├── tests/
│   ├── test_analysis.py
│   ├── test_kpis.py
│   └── test_privacy.py
│
├── .env
├── .gitignore
├── README.md
├── requirements.txt
└── test_gemini.py
```

---

# 12. Technologies

### Programming

* Python
* SQL

### Database

* Oracle Database

### AI

* Google Gemini

### Python Libraries

* `google-genai`
* `pandas`
* `SQLAlchemy`
* `oracledb`
* `python-dotenv`
* `pytest`

### Data Engineering / BI Concepts

* ETL / ELT concepts
* Data Quality
* SQL validation
* Data privacy
* Data aggregation
* Window functions
* CTEs
* Analytical SQL
* KPI generation
* Business intelligence
* AI-assisted analytics

---

# 13. Security & Privacy Design

The project follows a **validate-before-execute** approach.

Gemini-generated SQL is treated as untrusted generated code.

The execution sequence is:

```text
AI Generated SQL
       ↓
SQL Validator
       ↓
PASS?
  ├── NO  → Reject
  │
  └── YES
       ↓
Oracle Execution
```

The AI Business Analyst does not receive raw transaction-level identifiers.

Instead:

```text
Raw / Transaction Data
        ↓
SQL Aggregation
        ↓
Aggregated Results
        ↓
Privacy Guard
        ↓
Sanitized Results
        ↓
Gemini Analyst
```

This reduces unnecessary exposure of sensitive transaction-level information.

---

# 14. Configuration

Environment variables are stored in `.env`.

Example configuration:

```text
START_DATE=2026-07-07 00:00:00
END_DATE=2026-07-13 00:00:00
```

The end date is treated as an **exclusive boundary**.

Therefore, the analysis covers:

```text
July 7
July 8
July 9
July 10
July 11
July 12
```

Never commit `.env` or database credentials to GitHub.

---

# 15. Installation

Create and activate a Python environment, then install the required dependencies:

```powershell
pip install -r requirements.txt
```

Configure the required environment variables in:

```text
.env
```

Make sure the Oracle connection and Gemini API configuration are available before running the pipeline.

---

# 16. Running the Pipeline

### 1. Generate the analysis plan

```powershell
python -m src.ai_planner
```

Output:

```text
output/analysis_plan.json
```

---

### 2. Generate SQL

```powershell
python -m src.ai_sql_generator
```

Output:

```text
output/generated_sql.json
```

---

### 3. Validate generated SQL

```powershell
python -m src.sql_validator
```

Expected result:

```text
All generated queries passed validation.

SQL VALIDATION PASSED
```

Output:

```text
output/validated_sql.json
```

---

### 4. Execute validated SQL

```powershell
python -m src.analysis_executor
```

Output:

```text
output/aggregated_results.json
```

---

### 5. Run Privacy Guard

```powershell
python -m src.privacy_guard
```

Expected result:

```text
PRIVACY GUARD COMPLETED SUCCESSFULLY
```

Output:

```text
output/sanitized_analysis.json
```

---

### 6. Generate the AI Business Report

```powershell
python -m src.ai_analysis
```

Output:

```text
output/ai_business_report.md
```

---

# 17. Testing

The project includes automated tests for:

* Analytical logic
* KPI calculations
* Privacy controls

Run:

```powershell
python -m pytest -v
```

The current test suite has been successfully executed with:

```text
16 passed
```

The Google Gemini dependency may display an AFC-related warning during execution. This warning comes from the external `google-genai` library and does not indicate a project execution failure.

---

# 18. Data Quality Considerations

The analytical workflow preserves several data-quality principles:

### Missing Data

Missing observations are treated as unavailable data rather than zero activity.

### Duplicate Transactions

The SQL generation logic uses deterministic deduplication with:

```sql
ROW_NUMBER() OVER (
    PARTITION BY TransactionID
    ORDER BY ID DESC
)
```

### Reversed Transactions

The analytical query applies the project-defined transaction validity rule:

```text
IsReversed = 0
```

### Service Relationship

The confirmed relationship used by the analytical SQL is:

```text
TRANSACTIONS.TransactionType = SERVICES.ID
```

### Encoding Issue

One service name contains corrupted characters:

```text
Service ID 1527
```

The AI report does not attempt to reconstruct the corrupted service name without reliable source information.

---

# 19. Important Limitations

### Aggregated Data Only

The AI Business Analyst receives aggregated analytical results rather than transaction-level records.

Therefore, it cannot reliably determine:

* Individual transaction causes
* Customer-level behavior
* Exact operational root causes
* User-level patterns

### Short Time Window

The analysis covers only six days:

```text
July 7–12, 2026
```

Therefore, the findings should not be interpreted as long-term seasonal trends.

### Top-10 Scope

The analytical output focuses on the Top 10 services by overall revenue.

Services outside the Top 10 are not represented individually in the analytical output.

### Service Metadata

Service ID 1527 contains corrupted service-name text.

---

# 20. Design Principles

This project follows several important engineering principles:

### 1. AI does not directly control the database

Generated SQL must pass Python validation before execution.

### 2. Validate before execution

AI-generated code is treated as untrusted input.

### 3. Minimize data exposure

Only aggregated analytical results are provided to the AI Business Analyst.

### 4. Separate computation from interpretation

Python and Oracle perform the analytical computation.

Gemini interprets the resulting analytical metrics and generates the business report.

### 5. Evidence-based AI

The analyst is instructed not to invent causes, business events, or unsupported customer behavior.

### 6. Reproducible workflow

The major intermediate artifacts are saved as JSON/Markdown files, allowing each stage of the workflow to be inspected independently.

---

# 21. Future Improvements

Potential future enhancements include:

* Stronger SQL column-level validation
* Additional KPI validation
* Automated numerical reconciliation of AI-generated reports
* More comprehensive data-quality checks
* Local AI model evaluation
* Automated report generation
* Dashboard integration
* CI/CD pipeline
* Query performance monitoring
* Additional business questions and analysis types
* Automated anomaly detection
* Metadata and data lineage integration

---

# 22. Final Workflow Summary

```text
Business Question
        ↓
Gemini Planner
        ↓
Analysis Plan
        ↓
Gemini SQL Generator
        ↓
Generated SQL
        ↓
Python SQL Validator
        ↓
Validated SQL
        ↓
Oracle
        ↓
Aggregated Analytical Results
        ↓
Privacy Guard
        ↓
Sanitized Analytical Data
        ↓
Gemini Business Analyst
        ↓
AI Business Report
```

---

## Project Outcome

This project demonstrates a practical approach to integrating Generative AI into a BI/Data Engineering workflow while maintaining important controls around:

* SQL safety
* Data privacy
* Analytical correctness
* Data quality
* Reproducibility
* Evidence-based business interpretation

The main principle is:

> **AI assists the analytical workflow, but Python validation, database controls, and privacy boundaries remain responsible for execution and data protection.**
