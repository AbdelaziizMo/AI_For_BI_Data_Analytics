# Week 10 - AI for BI & Data Analytics

## Project Overview

This project demonstrates an end-to-end **AI-powered Business Intelligence and Data Analytics pipeline**.

The project combines:

* Oracle Database
* SQL data validation and transformation
* Python data analysis
* Pandas
* SQLAlchemy
* Google Gemini AI
* Prompt Engineering
* Automated Business Intelligence reporting

The objective is to answer a business question using a combination of **SQL analytics, Python-based analysis, and Generative AI**.

---

## Business Question

> **Which services generate the highest revenue and transaction volume, and how does their performance change over time?**

The analysis evaluates service-level revenue, transaction volume, daily trends, growth rates, concentration, and data-quality observations.

---

## Project Architecture

```text
                    ┌─────────────────────┐
                    │    Oracle Database  │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    improved.sql     │
                    │                     │
                    │ Data Validation     │
                    │ Deduplication       │
                    │ Service Join        │
                    │ Revenue Metrics     │
                    │ Volume Metrics      │
                    │ Daily Trends        │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   data_loader.py    │
                    │                     │
                    │ SQL → Pandas        │
                    │ DataFrame           │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │     analysis.py     │
                    │                     │
                    │ Business Metrics    │
                    │ Top Services        │
                    │ Trends              │
                    │ Growth              │
                    │ Concentration       │
                    │ Data Quality        │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   ai_analysis.py    │
                    │                     │
                    │ Prepare AI Input    │
                    │ Prompt Engineering  │
                    │ Gemini Analysis     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    Gemini AI        │
                    │                     │
                    │ BI Interpretation   │
                    │ Insights            │
                    │ Risks               │
                    │ Recommendations     │
                    └──────────┬──────────┘
                               │
                               ▼
              ┌────────────────────────────────┐
              │ output/ai_business_report.md   │
              └────────────────────────────────┘
```

---

# Project Structure

```text
Week10_AI_for_BI_Data_Analytics/
│
├── config/
│   ├── __init__.py
│   └── database.py
│
├── output/
│   └── ai_business_report.md
│
├── prompts/
│   └── prompts.md
│
├── python/
│   ├── ai_analysis.py
│   ├── analysis.py
│   └── data_loader.py
│
├── sql/
│   ├── ai_generated.sql
│   └── improved.sql
│
├── src/
│   └── config.py
│
├── .env
├── .gitignore
├── README.md
├── requirements.txt
└── test_gemini.py
```

---

# Data Processing

The project processes transaction data stored in an Oracle database.

The SQL transformation applies several data-quality and business rules before calculating the analytical metrics.

## Data Validation Rules

The SQL pipeline:

1. Removes records with missing critical values.
2. Keeps transactions where `TotalAmount > 0`.
3. Ensures `TransactionType` exists in the `SERVICES` table.
4. Accepts only valid `IsReversed` values (`0` or `1`).
5. Excludes future-dated transactions.
6. Applies the required analysis period.
7. Removes duplicate `TransactionID` records by keeping the record with the highest `ID`.
8. Excludes reversed transactions from business revenue and transaction-volume calculations.

---

# SQL Analysis

The original AI-generated SQL is stored in:

```text
sql/ai_generated.sql
```

The reviewed and improved version is:

```text
sql/improved.sql
```

The SQL follows this general processing flow:

```text
Raw Transactions
       ↓
Valid Transactions
       ↓
Deduplicated Transactions
       ↓
Valid Service Transactions
       ↓
Business Transactions
       ↓
Daily Service Metrics
       ↓
Service Totals
       ↓
Service Ranking
       ↓
Daily Trends
       ↓
Final BI Dataset
```

The final SQL calculates:

* Daily transaction volume
* Daily revenue
* Average transaction amount
* Total transaction volume
* Total revenue
* Revenue rank
* Volume rank
* Previous-day revenue
* Previous-day transaction volume
* Revenue growth percentage
* Volume growth percentage

---

# Python Data Loading

`python/data_loader.py` is responsible for executing the reviewed SQL query and loading the results into a Pandas DataFrame.

The module:

1. Reads `sql/improved.sql`.
2. Creates the Oracle SQLAlchemy connection.
3. Executes the query.
4. Loads the result into Pandas.
5. Returns the DataFrame.
6. Properly disposes of the database engine.

Example result:

```text
Rows loaded: 2,413
Columns loaded: 14
```

---

# Business Analysis

`python/analysis.py` performs the main analytical calculations.

The analysis includes:

### Overall Metrics

* Total revenue
* Total transaction volume
* Number of services
* Number of analysis days
* Average daily revenue
* Average daily transaction volume

### Service Performance

* Top revenue services
* Top volume services
* Revenue ranking
* Volume ranking
* Revenue concentration
* Volume concentration

### Time Analysis

* Daily revenue
* Daily transaction volume
* Day-over-day changes
* Revenue growth
* Volume growth
* Significant increases
* Significant decreases

### Data Quality

* Unexpected NULL values
* Expected analytical NULL values
* Duplicate rows
* Negative revenue
* Negative transaction volume
* Corrupted service names

---

# AI Business Analysis

The project uses Google Gemini to transform the calculated analytical results into a professional BI report.

The AI integration is implemented in:

```text
python/ai_analysis.py
```

The workflow is:

```text
analysis.py
     ↓
Analysis Results
     ↓
JSON Preparation
     ↓
Prompt Template
     ↓
Gemini
     ↓
AI Business Report
     ↓
output/ai_business_report.md
```

The project uses the Gemini Interactions API.

The AI is not responsible for calculating the core business metrics.

Instead:

```text
SQL + Python
     ↓
Calculate reliable metrics
     ↓
Gemini
     ↓
Interpret the metrics
```

This separation helps keep numerical analysis deterministic while using Generative AI primarily for business interpretation and reporting.

---

# Prompt Engineering

The main AI instructions are stored in:

```text
prompts/prompts.md
```

The prompt was designed to reduce unsupported AI assumptions and hallucinations.

The AI is instructed to:

* Use only supplied data.
* Avoid inventing business facts.
* Avoid unsupported causal explanations.
* Separate facts from interpretations.
* Treat hypotheses explicitly.
* Interpret extreme growth percentages using their baselines.
* Prioritize absolute financial impact.
* Keep revenue and transaction volume analysis separate.
* Avoid assuming customer engagement from transaction counts.
* Avoid unsupported profitability or cost assumptions.
* Avoid inventing technical root causes.
* Respect the six-day observation period.
* Provide evidence-based recommendations.

The preferred analytical pattern is:

```text
OBSERVATION
     ↓
BUSINESS INTERPRETATION
     ↓
LIMITATION
```

Recommendations follow:

```text
OBSERVED PATTERN
     ↓
BUSINESS IMPLICATION
     ↓
RECOMMENDED ACTION
```

---

# Key Business Findings

The current analysis covers:

```text
Observation Period:
2026-07-07 → 2026-07-12

Active Services:
582

Total Revenue:
33,912,079,041.22

Total Transactions:
7,016,458
```

## Revenue Concentration

The two highest revenue-generating services are:

| Service          |           Revenue |  Share |
| ---------------- | ----------------: | -----: |
| Balance Transfer | 17,986,458,044.61 | 53.04% |
| Extra Commission | 14,666,461,267.75 | 43.25% |

Together:

```text
Revenue = 32,652,919,312.36
Share   = 96.29%
```

The top 10 revenue services account for:

```text
98.54% of total revenue
```

This indicates a very high concentration of recorded revenue within a small number of services during the observation period.

---

# Transaction Volume Findings

Total transaction volume:

```text
7,016,458
```

The top 10 services by transaction volume account for:

```text
3,754,339 transactions
53.51% of total volume
```

Revenue and transaction-volume rankings are substantially different.

For example:

* Service 3773 ranks #1 in transaction volume.
* Service 395 ranks #1 in revenue.
* Service 866 ranks #2 in revenue but much lower in transaction volume.

This demonstrates that transaction volume alone is not a direct proxy for revenue generation.

---

# Revenue Volatility

Daily revenue varied significantly during the observation period.

Lowest daily revenue:

```text
2026-07-10
225,957,474.81
```

Highest daily revenue:

```text
2026-07-12
15,927,591,717.76
```

Two major service-level spikes contributed substantially to this variation:

```text
Service 866
2026-07-09
14,665,525,894.30 revenue

Service 395
2026-07-12
15,623,246,800.87 revenue
```

The available dataset identifies the observed spikes but does not contain sufficient metadata to establish their underlying causes.

---

# Data Quality Findings

The analysis identified:

```text
Total analytical records:
2,413

Unexpected NULL values:
49

Expected growth-related NULL values:
2,328

Duplicate rows:
0

Negative revenue rows:
0

Negative volume rows:
0
```

Several service names also contain unreadable character sequences such as:

```text
¿¿¿
```

These values reduce reporting clarity and service attribution.

The available dataset does not provide enough technical metadata to establish the root cause of the corrupted text.

---

# AI Report Output

The generated AI business report is saved automatically to:

```text
output/ai_business_report.md
```

This file contains:

* Executive Summary
* Key Business Findings
* Revenue Analysis
* Transaction Volume Analysis
* Growth and Decline Analysis
* Data Quality Observations
* Business Risks
* Recommendations

---

# Technologies Used

| Technology      | Purpose                                         |
| --------------- | ----------------------------------------------- |
| Python          | Main programming language                       |
| Oracle Database | Source database                                 |
| SQL             | Data transformation and analytical calculations |
| Pandas          | Data analysis                                   |
| SQLAlchemy      | Database connectivity                           |
| python-oracledb | Oracle database driver                          |
| Google Gemini   | AI-powered BI interpretation                    |
| python-dotenv   | Environment configuration                       |
| Markdown        | AI report format                                |

---

# Environment Configuration

Database and API credentials are stored in `.env`.

Example:

```env
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=your_host
DB_PORT=1521
DB_SERVICE=your_service

GEMINI_API_KEY=your_gemini_api_key
```

Never commit real credentials to source control.

---

# Installation

Create and activate a Python virtual environment if required:

```powershell
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\activate
```

Install project dependencies:

```powershell
pip install -r requirements.txt
```

---

# Running the Project

## 1. Test Database Data Loading

Run:

```powershell
python -m python.data_loader
```

Expected output includes:

```text
SQL executed successfully.
Rows loaded: 2,413
Columns loaded: 14
```

---

## 2. Run Business Analysis

Run:

```powershell
python -m python.analysis
```

This calculates the business metrics and prints the analytical results.

---

## 3. Generate the AI Business Report

Run:

```powershell
python -m python.ai_analysis
```

The complete pipeline will execute:

```text
Oracle
  ↓
SQL
  ↓
Pandas
  ↓
Business Analysis
  ↓
Gemini
  ↓
Markdown Report
```

The final report will be created at:

```text
output/ai_business_report.md
```

---

# Project Design Principles

This project follows several important analytical principles.

### 1. SQL First, AI Second

The core numerical calculations are performed using SQL and Python before sending the results to Gemini.

### 2. Evidence-Based AI

Gemini receives calculated metrics rather than raw uncontrolled assumptions.

### 3. Human Review of AI-Generated SQL

The initial AI-generated SQL is reviewed and improved before becoming the production analytical query.

```text
AI-generated SQL
       ↓
Human Review
       ↓
Improved SQL
       ↓
Production Analysis
```

### 4. Conservative Business Interpretation

The AI is instructed not to claim causes that cannot be demonstrated from the available data.

### 5. Separation of Revenue and Volume

Revenue and transaction volume are analyzed independently because high processing volume does not necessarily imply high revenue.

---

# Limitations

The current analysis has several limitations:

1. The observation window covers only six active transaction days.
2. The dataset does not contain customer-level information.
3. Cost, margin, and profitability information is not available.
4. Operational metadata explaining revenue spikes is not available.
5. The root cause of corrupted service-name values cannot be established from the dataset alone.
6. Unexpected NULL values require additional source-level investigation.
7. Short observation periods should not be used to establish long-term trends without additional historical data.

---

# Future Improvements

Potential extensions include:

* Interactive Power BI dashboard
* Revenue and volume trend visualizations
* Automated data-quality reports
* Historical trend analysis
* Service-level anomaly detection
* Revenue concentration monitoring
* Automated BI alerts
* Additional transaction-level metadata
* Unit economics analysis using cost and margin data
* Scheduled AI-generated BI reports

---

# Conclusion

This project demonstrates how traditional Business Intelligence techniques can be combined with Generative AI.

The analytical workflow separates responsibilities:

```text
Oracle + SQL
    ↓
Data Validation & Transformation

Python + Pandas
    ↓
Business Metrics & Analysis

Gemini AI
    ↓
Business Interpretation & Reporting
```

The result is an end-to-end AI-assisted BI pipeline capable of transforming transactional data into a structured, evidence-based business intelligence report.

The project demonstrates that Generative AI can enhance BI analysis while keeping the underlying numerical calculations and data transformations deterministic and auditable.

