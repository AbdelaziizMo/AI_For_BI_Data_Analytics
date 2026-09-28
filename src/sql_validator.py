import json
import re
from pathlib import Path


# ================================================================
# WEEK 10 - AI FOR BI & DATA ANALYTICS
# SQL SECURITY VALIDATOR
# ================================================================

BASE_DIR = Path(__file__).resolve().parent.parent

GENERATED_SQL_FILE = (
    BASE_DIR / "output" / "generated_sql.json"
)

VALIDATED_SQL_FILE = (
    BASE_DIR / "output" / "validated_sql.json"
)


# ================================================================
# APPROVED DATABASE OBJECTS
# ================================================================

ALLOWED_TABLES = {
    "PLAYGROUND.TRANSACTIONS",
    "PLAYGROUND.SERVICES",
}

ALLOWED_TRANSACTION_COLUMNS = {
    "TransactionID",
    "AccountIDFrom",
    "AccountIDTo",
    "TotalAmount",
    "TransactionType",
    "IsReversed",
    "OriginalTrx",
    "Date",
    "OriginalAmount",
    "Fees",
    "InvoiceID",
    "RequestID",
    "ID",
    "BalanceBefore",
}

ALLOWED_SERVICE_COLUMNS = {
    "ID",
    "NameAr",
}


# ================================================================
# SECURITY BLOCKLIST
# ================================================================

FORBIDDEN_KEYWORDS = {
    "INSERT",
    "UPDATE",
    "DELETE",
    "MERGE",
    "DROP",
    "ALTER",
    "TRUNCATE",
    "CREATE",
    "GRANT",
    "REVOKE",
    "EXECUTE",
    "CALL",
}


# ================================================================
# BLOCKED FINAL OUTPUT COLUMNS
# ================================================================

BLOCKED_OUTPUT_COLUMNS = {
    "TRANSACTIONID",
    "ACCOUNTIDFROM",
    "ACCOUNTIDTO",
    "ORIGINALTRX",
    "INVOICEID",
    "REQUESTID",
    "BALANCEBEFORE",
}


# ================================================================
# REQUIRED BIND PARAMETERS
# ================================================================

REQUIRED_BIND_PARAMETERS = {
    "start_date",
    "end_date",
}


# ================================================================
# LOAD GENERATED SQL
# ================================================================

def load_generated_sql() -> dict:

    if not GENERATED_SQL_FILE.exists():
        raise FileNotFoundError(
            f"Generated SQL file not found: "
            f"{GENERATED_SQL_FILE}"
        )

    with open(
        GENERATED_SQL_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(
            "generated_sql.json must contain a JSON object."
        )

    if "queries" not in data:
        raise ValueError(
            "generated_sql.json is missing 'queries'."
        )

    if not isinstance(data["queries"], list):
        raise ValueError(
            "'queries' must be a list."
        )

    if not data["queries"]:
        raise ValueError(
            "No generated queries were found."
        )

    return data


# ================================================================
# REMOVE SQL COMMENTS
# ================================================================

def remove_sql_comments(sql: str) -> str:

    # Remove /* ... */ comments
    sql = re.sub(
        r"/\*.*?\*/",
        " ",
        sql,
        flags=re.DOTALL,
    )

    # Remove -- comments
    sql = re.sub(
        r"--[^\n]*",
        " ",
        sql,
    )

    return sql


# ================================================================
# CHECK FOR MULTIPLE STATEMENTS
# ================================================================

def validate_single_statement(sql: str):

    cleaned = remove_sql_comments(sql).strip()

    # A trailing semicolon is allowed.
    without_trailing_semicolon = cleaned.rstrip(";").strip()

    if ";" in without_trailing_semicolon:
        raise ValueError(
            "Multiple SQL statements are not allowed."
        )


# ================================================================
# CHECK READ-ONLY SQL
# ================================================================

def validate_read_only(sql: str):

    cleaned = remove_sql_comments(sql)

    # Remove quoted strings before checking keywords.
    normalized = re.sub(
        r"'(?:''|[^'])*'",
        " ",
        cleaned,
    )

    for keyword in FORBIDDEN_KEYWORDS:

        pattern = rf"\b{re.escape(keyword)}\b"

        if re.search(
            pattern,
            normalized,
            flags=re.IGNORECASE,
        ):
            raise ValueError(
                f"Forbidden SQL keyword detected: {keyword}"
            )


# ================================================================
# CHECK SQL START
# ================================================================

def validate_select_statement(sql: str):

    cleaned = remove_sql_comments(sql).strip()

    # Remove trailing semicolon
    cleaned = cleaned.rstrip(";").strip()

    upper_sql = cleaned.upper()

    if not (
        upper_sql.startswith("SELECT")
        or upper_sql.startswith("WITH")
    ):
        raise ValueError(
            "SQL must start with SELECT or WITH."
        )


# ================================================================
# CHECK SELECT *
# ================================================================

def validate_no_select_star(sql: str):

    cleaned = remove_sql_comments(sql)

    if re.search(
        r"\bSELECT\s+\*",
        cleaned,
        flags=re.IGNORECASE,
    ):
        raise ValueError(
            "SELECT * is not allowed."
        )

    if re.search(
        r",\s*\*",
        cleaned,
        flags=re.IGNORECASE,
    ):
        raise ValueError(
            "Wildcard column selection is not allowed."
        )


# ================================================================
# CHECK TABLES
# ================================================================
def validate_tables(sql: str):
    cleaned = remove_sql_comments(sql)

    # ---------------------------------------------------------
    # 1. Extract real database tables from FROM / JOIN
    # ---------------------------------------------------------
    table_pattern = re.compile(
        r"""
        \b(?:FROM|JOIN)\s+
        (?:
            ([A-Z][A-Z0-9_$#]*)\.
        )?
        ([A-Z][A-Z0-9_$#]*)
        """,
        flags=re.IGNORECASE | re.VERBOSE,
    )

    matches = table_pattern.findall(cleaned)

    if not matches:
        raise ValueError(
            "No database table reference was detected "
            "after FROM/JOIN."
        )

    # ---------------------------------------------------------
    # 2. Extract CTE names from WITH ... AS
    # ---------------------------------------------------------
    cte_pattern = re.compile(
        r"""
        \b([A-Z][A-Z0-9_$#]*)\s+AS\s*\(
        """,
        flags=re.IGNORECASE | re.VERBOSE,
    )

    cte_matches = cte_pattern.findall(cleaned)

    cte_names = {
        cte.upper()
        for cte in cte_matches
    }

    # ---------------------------------------------------------
    # 3. Collect referenced objects
    # ---------------------------------------------------------
    found_tables = set()

    for schema, table in matches:

        schema = schema.upper()
        table = table.upper()

        # If this is a CTE, it is internal and allowed.
        if not schema and table in cte_names:
            continue

        if schema:
            found_tables.add(
                f"{schema}.{table}"
            )
        else:
            found_tables.add(table)

    # ---------------------------------------------------------
    # 4. Compare against approved database tables
    # ---------------------------------------------------------
    allowed_tables_upper = {
        table.upper()
        for table in ALLOWED_TABLES
    }

    invalid_tables = (
        found_tables
        - allowed_tables_upper
    )

    if invalid_tables:
        raise ValueError(
            "Unapproved table(s) detected: "
            + ", ".join(sorted(invalid_tables))
        )

# ================================================================
# CHECK BIND PARAMETERS
# ================================================================

def validate_bind_parameters(sql: str):

    binds = set(
        re.findall(
            r":([A-Za-z_][A-Za-z0-9_]*)",
            sql,
        )
    )

    missing = (
        REQUIRED_BIND_PARAMETERS
        - binds
    )

    if missing:
        raise ValueError(
            "Required bind parameter(s) missing: "
            + ", ".join(sorted(missing))
        )


# ================================================================
# CHECK DATE FILTER
# ================================================================

def validate_date_filter(sql: str):

    normalized = re.sub(
        r"\s+",
        " ",
        remove_sql_comments(sql),
    ).upper()

    has_start_date = (
        ":START_DATE" in normalized
    )

    has_end_date = (
        ":END_DATE" in normalized
    )

    if not has_start_date or not has_end_date:
        raise ValueError(
            "SQL must use both :start_date and :end_date."
        )

    # The SQL must contain a lower-bound and upper-bound
    # transaction date filter.
    has_date_reference = (
        '"DATE"' in normalized
        or "T.DATE" in normalized
        or ".DATE" in normalized
    )

    if not has_date_reference:
        raise ValueError(
            "SQL does not contain a transaction date reference."
        )


# ================================================================
# CHECK CONFIRMED RELATIONSHIP
# ================================================================

def validate_service_relationship(sql: str):

    normalized = re.sub(
        r"\s+",
        " ",
        remove_sql_comments(sql),
    ).upper()

    transaction_type_reference = (
        '"TRANSACTIONTYPE"' in normalized
        or "TRANSACTIONTYPE" in normalized
    )

    service_id_reference = (
        '"ID"' in normalized
        or ".ID" in normalized
    )

    if not transaction_type_reference:
        raise ValueError(
            "SQL does not reference TransactionType."
        )

    if not service_id_reference:
        raise ValueError(
            "SQL does not reference SERVICES.ID."
        )


# ================================================================
# CHECK RAW OUTPUT
# ================================================================

def extract_final_select(sql: str) -> str:
    """
    Extract a conservative representation of the final SELECT.

    This is intentionally simple. The validator does not try to
    fully parse Oracle SQL here.
    """

    cleaned = remove_sql_comments(sql).strip()

    # Find the last SELECT in the statement.
    matches = list(
        re.finditer(
            r"\bSELECT\b",
            cleaned,
            flags=re.IGNORECASE,
        )
    )

    if not matches:
        return ""

    return cleaned[matches[-1].start():]


def validate_no_blocked_final_output(sql: str):

    final_select = extract_final_select(sql)

    if not final_select:
        raise ValueError(
            "Unable to identify final SELECT statement."
        )

    upper_final = final_select.upper()

    for column in BLOCKED_OUTPUT_COLUMNS:

        if re.search(
            rf"\b{re.escape(column)}\b",
            upper_final,
        ):
            raise ValueError(
                "Blocked raw transaction field appears in "
                f"final SELECT: {column}"
            )


# ================================================================
# CHECK RAW TRANSACTION OUTPUT PATTERNS
# ================================================================
def validate_aggregated_output(sql: str):
    """
    Ensure the generated SQL produces analytical/aggregated output
    and does not expose raw transaction-level identifiers.
    """

    cleaned = remove_sql_comments(sql).upper()

    # ---------------------------------------------------------
    # 1. Analytical functions
    # ---------------------------------------------------------
    analytical_patterns = [
        r"\bSUM\s*\(",
        r"\bCOUNT\s*\(",
        r"\bAVG\s*\(",
        r"\bMIN\s*\(",
        r"\bMAX\s*\(",
        r"\bRANK\s*\(",
        r"\bDENSE_RANK\s*\(",
        r"\bROW_NUMBER\s*\(",
        r"\bLAG\s*\(",
        r"\bLEAD\s*\(",
    ]

    has_analytical_function = any(
        re.search(pattern, cleaned)
        for pattern in analytical_patterns
    )

    if not has_analytical_function:
        raise ValueError(
            "SQL does not appear to contain "
            "analytical aggregation/window functions."
        )

    # ---------------------------------------------------------
    # 2. Check final SELECT for blocked raw identifiers
    # ---------------------------------------------------------
    final_select = extract_final_select(cleaned)

    blocked_output_fields = {
        "TRANSACTIONID",
        "ACCOUNTIDFROM",
        "ACCOUNTIDTO",
        "ORIGINALTRX",
        "INVOICEID",
        "REQUESTID",
        "BALANCEBEFORE",
    }

    blocked_found = []

    for field in blocked_output_fields:

        pattern = rf"\b{re.escape(field)}\b"

        if re.search(pattern, final_select):
            blocked_found.append(field)

    if blocked_found:
        raise ValueError(
            "Blocked raw field(s) detected in final output: "
            + ", ".join(sorted(blocked_found))
        )


# ================================================================
# VALIDATE ONE QUERY
# ================================================================

def validate_query(
    query_name: str,
    sql: str,
):

    if not isinstance(sql, str):
        raise ValueError(
            f"SQL for '{query_name}' must be a string."
        )

    if not sql.strip():
        raise ValueError(
            f"SQL for '{query_name}' is empty."
        )

    print(
        f"\nValidating query: {query_name}"
    )

    print("  [1/9] Checking statement count...")
    validate_single_statement(sql)

    print("  [2/9] Checking read-only restrictions...")
    validate_read_only(sql)

    print("  [3/9] Checking SELECT/WITH...")
    validate_select_statement(sql)

    print("  [4/9] Checking wildcard usage...")
    validate_no_select_star(sql)

    print("  [5/9] Checking approved tables...")
    validate_tables(sql)

    print("  [6/9] Checking bind parameters...")
    validate_bind_parameters(sql)

    print("  [7/9] Checking date filtering...")
    validate_date_filter(sql)

    print("  [8/9] Checking service relationship...")
    validate_service_relationship(sql)

    print("  [9/9] Checking analytical output/privacy...")
    validate_no_blocked_final_output(sql)
    validate_aggregated_output(sql)

    print(
        f"  PASS: {query_name}"
    )


# ================================================================
# SAVE VALIDATED SQL
# ================================================================

def save_validated_sql(
    data: dict,
):

    VALIDATED_SQL_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output = {
        "business_question": data.get(
            "business_question"
        ),
        "analysis_type": data.get(
            "analysis_type"
        ),
        "dimensions": data.get(
            "dimensions",
            []
        ),
        "kpis": data.get(
            "kpis",
            []
        ),
        "top_n": data.get(
            "top_n"
        ),
        "validation_status": "PASSED",
        "queries": data["queries"],
    }

    with open(
        VALIDATED_SQL_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            output,
            file,
            indent=4,
            ensure_ascii=False,
        )

    print(
        f"\nValidated SQL saved to:"
        f"\n{VALIDATED_SQL_FILE}"
    )


# ================================================================
# MAIN VALIDATION PIPELINE
# ================================================================

def validate_generated_sql():

    print()
    print("=" * 70)
    print("WEEK 10 - SQL SECURITY VALIDATOR")
    print("=" * 70)

    print(
        "\n[1/3] Loading generated SQL..."
    )

    data = load_generated_sql()

    queries = data["queries"]

    print(
        f"Loaded {len(queries)} generated query(s)."
    )

    print(
        "\n[2/3] Validating generated SQL..."
    )

    for query in queries:

        validate_query(
            query_name=query["name"],
            sql=query["sql"],
        )

    print(
        "\nAll generated queries passed validation."
    )

    print(
        "\n[3/3] Saving validated SQL..."
    )

    save_validated_sql(
        data
    )

    print()
    print("=" * 70)
    print("SQL VALIDATION PASSED")
    print("=" * 70)

    return data


# ================================================================
# ENTRY POINT
# ================================================================

if __name__ == "__main__":
    validate_generated_sql()
