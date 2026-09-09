
from google import genai
from src.config import GEMINI_API_KEY
from pathlib import Path
import re


# ================================================================
# WEEK 10 - AI FOR BI & DATA ANALYTICS
# AI SQL GENERATOR + AI SQL IMPROVER
# ================================================================


# ================================================================
# GEMINI CLIENT
# ================================================================
from google.genai import types

client = genai.Client( api_key=GEMINI_API_KEY )

MODEL_NAME = "gemini-3.6-flash"

BASE_DIR = Path(__file__).resolve().parent.parent

AI_GENERATED_FILE = BASE_DIR / "sql" / "ai_generated.sql"
IMPROVED_FILE = BASE_DIR / "sql" / "improved.sql"


# ================================================================
# INITIAL SQL GENERATION PROMPT
# ================================================================

prompt = """

You are a Senior Data Engineer and BI Analyst.

I am working on a Week 10 project called:

"AI for BI & Data Analytics"

The goal is to use Generative AI to help generate and improve SQL
for Business Intelligence analysis.

I have an Oracle database with the following tables:

================================================
TABLE: PLAYGROUND.SERVICES
================================================

Columns:

ID              NUMBER(10,0)
NameAr          VARCHAR2(255)

Number of services:
2,889


================================================
TABLE: PLAYGROUND.TRANSACTIONS
================================================

Columns:

TransactionID       VARCHAR2(255)
AccountIDFrom       NUMBER(10,0)
AccountIDTo         NUMBER(10,0)
TotalAmount         NUMBER(18,3)
TransactionType     NUMBER(10,0)
IsReversed          NUMBER(1,0)
OriginalTrx         NUMBER(10,0)
Date                TIMESTAMP
OriginalAmount      NUMBER(18,3)
Fees                NUMBER(18,3)
InvoiceID           NUMBER(10,0)
RequestID           NUMBER(38,0)
ID                  NUMBER(38,0)
BalanceBefore       NUMBER(18,3)


================================================
IMPORTANT RELATIONSHIP
================================================

The following relationship is confirmed and VALID:

TRANSACTIONS."TransactionType" = SERVICES.ID

TransactionType represents the Service ID.

Therefore, this relationship should NOT be treated as an assumption.


================================================
DATASET INFORMATION
================================================

Total transactions:

14,452,056

Minimum transaction date:

2026-07-01 00:00:00.103

Maximum transaction date:

2026-07-12 23:59:59.983

Number of active days:
12


================================================
WEEK 6 DATA QUALITY RULES
================================================

The existing Week 6 Data Quality Framework checks:

1. Duplicate TransactionID

2. NULL values in important columns:
   - TransactionID
   - AccountIDFrom
   - AccountIDTo
   - TotalAmount
   - TransactionType
   - IsReversed
   - Date

3. Invalid transaction amounts:
   TotalAmount <= 0

4. Invalid Service IDs:
   TransactionType must exist in SERVICES.ID

5. Invalid transaction status:
   IsReversed must be 0 or 1

6. Future transaction dates:
   Date must not be greater than SYSTIMESTAMP


================================================
WEEK 6 DATA QUALITY RESULTS
================================================

Duplicate records:
2

Records containing NULL values:
18,232

Invalid / negative transaction amounts:
3

Invalid Service IDs:
1

Invalid transaction statuses:
0

Future transaction dates:
0

Total records:
14,452,056


================================================
BUSINESS QUESTION
================================================

Answer this business question:

"Which services generate the highest revenue and transaction volume,
and how does their performance change over time?"

The analysis should cover the full available dataset:

2026-07-01 through 2026-07-12.


================================================
REQUIREMENTS
================================================

Generate a production-quality Oracle SQL query that:

1. Uses PLAYGROUND.TRANSACTIONS and PLAYGROUND.SERVICES.

2. Applies the existing Week 6 Data Quality rules.

3. Excludes invalid transactions from BI calculations.

4. Handles duplicate TransactionIDs correctly.

5. Validates Service IDs using SERVICES.ID.

6. Uses TransactionType as Service ID.

7. Excludes reversed transactions from revenue and transaction-volume
   calculations because IsReversed = 1 means the transaction was reversed.
   Only IsReversed = 0 should be included in business performance metrics.

8. Calculates daily metrics for each service:

   - Service ID
   - Service Name
   - Transaction Date
   - Daily Transaction Volume
   - Daily Revenue
   - Average Transaction Amount

9. Calculates overall service performance across the 12-day period:

   - Total Transaction Volume
   - Total Revenue
   - Revenue Rank
   - Transaction Volume Rank

10. Calculates day-over-day performance:

   - Previous Day Revenue
   - Previous Day Transaction Volume
   - Revenue Growth %
   - Transaction Volume Growth %

11. Use Oracle SQL window functions such as:

   ROW_NUMBER()
   DENSE_RANK()
   LAG()
   SUM() OVER()

12. Avoid division by zero.

13. Use clear CTEs.

14. Do NOT hardcode individual service IDs.

15. Do NOT assume TransactionType is a generic transaction category.
    It is confirmed to be the Service ID.

16. The final query should be suitable for Power BI / BI analysis.

17. Explain the query after generating it.

18. Explain how the Week 6 Data Quality rules were incorporated.

19. Clearly explain the deduplication strategy.

20. Clearly explain why reversed transactions are excluded.

IMPORTANT:

Do not invent columns that do not exist in the schema.

Do not use ServiceID from TRANSACTIONS because that column does not exist.

Use:

TRANSACTIONS."TransactionType" AS SERVICE_ID

and join:

TRANSACTIONS."TransactionType" = SERVICES.ID


================================================
EXPECTED OUTPUT
================================================

Return:

A. Production-ready Oracle SQL query

B. Explanation of every CTE

C. Explanation of Data Quality filtering

D. Explanation of deduplication

E. Explanation of service ranking

F. Explanation of daily trend analysis

G. Explanation of growth calculations

H. Potential BI insights that can be derived from the result

Do not execute the SQL.
Only generate and explain the SQL.
"""


# ================================================================
# HELPER - EXTRACT SQL FROM GEMINI RESPONSE
# ================================================================

def extract_sql(text: str) -> str:
    """
    Extract SQL from Gemini response.

    Handles:
    - ```sql ... ```
    - ``` ... ```
    - Explanation before/after SQL
    """

    if not text:
        raise ValueError("Gemini returned an empty response.")

    text = text.strip()

    # ------------------------------------------------------------
    # Case 1: SQL inside ```sql ... ```
    # ------------------------------------------------------------

    sql_match = re.search(
        r"```sql\s*(.*?)\s*```",
        text,
        flags=re.IGNORECASE | re.DOTALL
    )

    if sql_match:
        sql = sql_match.group(1).strip()

    else:
        # --------------------------------------------------------
        # Case 2: SQL inside generic ``` ... ```
        # --------------------------------------------------------

        generic_match = re.search(
            r"```\s*(.*?)\s*```",
            text,
            flags=re.DOTALL
        )

        if generic_match:
            sql = generic_match.group(1).strip()

        else:
            # ----------------------------------------------------
            # Case 3: Gemini returned raw SQL
            # ----------------------------------------------------

            sql = text

    # ------------------------------------------------------------
    # Remove accidental leading labels
    # ------------------------------------------------------------

    sql = re.sub(
        r"^\s*(A\.\s*)?Production[- ]ready Oracle SQL\s*:?\s*",
        "",
        sql,
        flags=re.IGNORECASE
    )

    sql = sql.strip()

    # ------------------------------------------------------------
    # Basic validation
    # ------------------------------------------------------------

    sql_upper = sql.upper()

    if not ("SELECT" in sql_upper or "WITH" in sql_upper):
        raise ValueError(
            "The AI response does not appear to contain a valid SQL query."
        )

    # SQL file should not contain markdown
    if "```" in sql:
        raise ValueError(
            "Markdown code fences were detected in the generated SQL."
        )

    return sql


# ================================================================
# SAVE FILE
# ================================================================

def save_sql(sql: str, output_file: Path):
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as file:
        file.write(sql.rstrip() + "\n")


# ================================================================
# GENERATE INITIAL SQL
# ================================================================

def generate_initial_sql():

    print("\n" + "=" * 70)
    print("AI SQL GENERATOR")
    print("=" * 70)

    print("\nGenerating initial SQL using Gemini...")

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    if not response.text:
        raise ValueError("Gemini returned an empty response.")

    print("\nGemini response received.")

    sql = extract_sql(response.text)

    save_sql(sql, AI_GENERATED_FILE)

    print("\nInitial SQL saved successfully:")
    print(f"File: {AI_GENERATED_FILE}")

    return sql


# ================================================================
# COLLECT USER PROBLEMS
# ================================================================

def collect_problems():

    print("\n" + "=" * 70)
    print("SQL REVIEW")
    print("=" * 70)

    print(
        "\nEnter the problems or improvements you want the AI to fix."
    )

    print(
        "Enter one problem per line."
    )

    print(
        "Type DONE when you finish."
    )

    print("\nExample:")
    print("Problem: hard-coded dates")
    print("Problem: use START_DATE and END_DATE parameters")
    print("Problem: keep highest ID for duplicate TransactionID")
    print("Problem: growth should return NULL when previous value is missing")
    print("Problem: SQL file should contain SQL only")
    print("Problem: DONE")

    problems = []

    while True:

        user_input = input("\nProblem: ").strip()

        if not user_input:
            continue

        if user_input.upper() == "DONE":
            break

        problems.append(user_input)

    return problems


# ================================================================
# BUILD IMPROVEMENT PROMPT
# ================================================================

def build_improvement_prompt(
    original_sql: str,
    problems: list[str]
) -> str:

    problems_text = "\n".join(
        f"{index}. {problem}"
        for index, problem in enumerate(problems, start=1)
    )

    improvement_prompt = f"""

You are a Senior Data Engineer reviewing an AI-generated Oracle SQL
query for a production BI pipeline.

This is part of a Week 10 project:

"AI for BI & Data Analytics"


================================================
BUSINESS QUESTION
================================================

"Which services generate the highest revenue and transaction volume,
and how does their performance change over time?"


================================================
DATABASE SCHEMA
================================================

TABLE: PLAYGROUND.SERVICES

ID              NUMBER(10,0)
NameAr          VARCHAR2(255)


TABLE: PLAYGROUND.TRANSACTIONS

TransactionID       VARCHAR2(255)
AccountIDFrom       NUMBER(10,0)
AccountIDTo         NUMBER(10,0)
TotalAmount         NUMBER(18,3)
TransactionType     NUMBER(10,0)
IsReversed          NUMBER(1,0)
OriginalTrx         NUMBER(10,0)
Date                TIMESTAMP
OriginalAmount      NUMBER(18,3)
Fees                NUMBER(18,3)
InvoiceID           NUMBER(10,0)
RequestID           NUMBER(38,0)
ID                  NUMBER(38,0)
BalanceBefore       NUMBER(18,3)


================================================
CONFIRMED RELATIONSHIP
================================================

TRANSACTIONS.TransactionType = SERVICES.ID

TransactionType is the Service ID.


================================================
WEEK 6 DATA QUALITY RULES
================================================

The SQL must:

1. Remove NULL values from important columns.

2. Remove invalid transaction amounts:
   TotalAmount <= 0

3. Remove invalid Service IDs by requiring a matching SERVICES.ID.

4. Remove invalid transaction status.

5. Remove future transactions:
   Date must not be greater than SYSTIMESTAMP.

6. Handle duplicate TransactionID correctly.


================================================
BUSINESS RULES
================================================

1. Only IsReversed = 0 is included in business performance metrics.

2. TransactionType is the Service ID.

3. The analysis covers:

   START_DATE <= Date < END_DATE

4. START_DATE and END_DATE must be implemented as bind parameters:

   :start_date
   :end_date

5. Do NOT hardcode dates.

6. Do NOT hardcode service IDs.

7. The SQL must be valid Oracle SQL.

8. The SQL must be suitable for pandas / SQLAlchemy execution.

9. The result should support Power BI / BI analysis.

10. Daily metrics must include:

   Service ID
   Service Name
   Transaction Date
   Daily Transaction Volume
   Daily Revenue
   Average Transaction Amount

11. Overall service metrics must include:

   Total Transaction Volume
   Total Revenue
   Revenue Rank
   Volume Rank

12. Day-over-day metrics must include:

   Previous Day Revenue
   Previous Day Transaction Volume
   Revenue Growth %
   Volume Growth %

13. Use appropriate Oracle window functions such as:

   ROW_NUMBER()
   DENSE_RANK()
   LAG()
   SUM() OVER()

14. Avoid division by zero.

15. If there is no previous day or previous value is zero,
    growth should be NULL rather than 0.

16. Deduplication rule:

    When duplicate TransactionID values exist, keep exactly one
    record using the highest TRANSACTIONS.ID.

17. Use clear CTEs.

18. Do not invent columns.

19. Do not use ServiceID from TRANSACTIONS.

20. Use:

    TRANSACTIONS.TransactionType AS Service_ID


================================================
USER-IDENTIFIED PROBLEMS
================================================

The user reviewed the original AI-generated SQL and identified
the following problems:

{problems_text}


================================================
ORIGINAL AI-GENERATED SQL
================================================

{original_sql}


================================================
YOUR TASK
================================================

Fix ALL of the user-identified problems.

Also verify that the final SQL follows ALL business rules above.

Do not blindly modify the query.

Review the SQL as a Senior Data Engineer.

Make the query:

- correct
- production-ready
- deterministic
- Oracle-compatible
- suitable for SQLAlchemy/pandas
- suitable for Power BI
- free of unnecessary explanations

IMPORTANT:

Your response MUST contain ONLY the final SQL query.

Do NOT include:

- markdown
- ```sql
- ``` 
- explanations
- comments outside the SQL
- "Here is the query"
- "A."
- "Production-ready SQL"

Return SQL ONLY.
"""


    return improvement_prompt


# ================================================================
# GENERATE IMPROVED SQL
# ================================================================

def generate_improved_sql(
    original_sql: str,
    problems: list[str]
):

    if not problems:
        print("\nNo problems were entered.")
        print("Skipping SQL improvement.")

        return None

    print("\n" + "=" * 70)
    print("AI SQL IMPROVER")
    print("=" * 70)

    print("\nSending original SQL and review comments to Gemini...")

    improvement_prompt = build_improvement_prompt(
        original_sql,
        problems
    )

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=improvement_prompt
    )

    if not response.text:
        raise ValueError(
            "Gemini returned an empty response while improving SQL."
        )

    improved_sql = extract_sql(response.text)

    save_sql(improved_sql, IMPROVED_FILE)

    print("\nImproved SQL generated successfully:")
    print(f"File: {IMPROVED_FILE}")

    return improved_sql


# ================================================================
# MAIN PIPELINE
# ================================================================

def main():

    print("\n" + "=" * 70)
    print("WEEK 10 - AI FOR BI & DATA ANALYTICS")
    print("AI SQL GENERATION + AI SQL IMPROVEMENT")
    print("=" * 70)

    try:

        # --------------------------------------------------------
        # STEP 1
        # Generate initial SQL
        # --------------------------------------------------------

        original_sql = generate_initial_sql()

        # --------------------------------------------------------
        # STEP 2
        # Ask user for problems
        # --------------------------------------------------------

        problems = collect_problems()

        # --------------------------------------------------------
        # STEP 3
        # Generate improved SQL
        # --------------------------------------------------------

        generate_improved_sql(
            original_sql,
            problems
        )

        # --------------------------------------------------------
        # DONE
        # --------------------------------------------------------

        print("\n" + "=" * 70)
        print("PIPELINE COMPLETED")
        print("=" * 70)

        print("\nGenerated files:")

        print(f"1. {AI_GENERATED_FILE}")

        if problems:
            print(f"2. {IMPROVED_FILE}")

        print("\nNext step:")
        print("Run data_loader.py to load improved.sql into pandas.")

        print("=" * 70)

    except Exception as e:

        print("\n" + "=" * 70)
        print("ERROR")
        print("=" * 70)

        print(str(e))

        raise


# ================================================================
# ENTRY POINT
# ================================================================

if __name__ == "__main__":
    main()
