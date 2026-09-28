import json
from datetime import datetime

import pandas as pd
from sqlalchemy import text

from src.config import (
    START_DATE,
    END_DATE,
    OUTPUT_DIR,
)
from src.database import get_engine


VALIDATED_SQL_FILE = OUTPUT_DIR / "validated_sql.json"
RESULT_FILE = OUTPUT_DIR / "aggregated_results.json"


def load_validated_sql():
    """
    Load SQL that has already passed the security validator.
    """

    if not VALIDATED_SQL_FILE.exists():
        raise FileNotFoundError(
            f"Validated SQL file not found: {VALIDATED_SQL_FILE}"
        )

    with open(
        VALIDATED_SQL_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    queries = data.get("queries", [])

    if not queries:
        raise ValueError(
            "No validated queries found."
        )

    return data, queries


def execute_query(query_name, query_sql):
    """
    Execute validated analytical SQL against Oracle.

    Only aggregated analytical results are returned.
    """

    start_date = datetime.strptime(
        START_DATE,
        "%Y-%m-%d %H:%M:%S",
    )

    end_date = datetime.strptime(
        END_DATE,
        "%Y-%m-%d %H:%M:%S",
    )

    params = {
        "start_date": start_date,
        "end_date": end_date,
    }

    print()
    print("=" * 70)
    print(f"Executing query: {query_name}")
    print("=" * 70)

    engine = get_engine()

    try:
        with engine.connect() as connection:

            dataframe = pd.read_sql(
                text(query_sql),
                connection,
                params=params,
            )

        print(
            f"Query executed successfully."
        )

        print(
            f"Rows returned: {len(dataframe):,}"
        )

        print(
            f"Columns returned: {len(dataframe.columns)}"
        )

        return dataframe

    finally:
        engine.dispose()


def save_results(
    validated_metadata,
    query_name,
    dataframe,
):
    """
    Save aggregated analytical results.

    No raw transaction-level records are saved.
    """

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    results = (
        dataframe
        .astype(object)
        .where(
            pd.notna(dataframe),
            None,
        )
        .to_dict(
            orient="records"
        )
    )

    output = {
        "business_question": validated_metadata.get(
            "business_question"
        ),

        "analysis_type": validated_metadata.get(
            "analysis_type"
        ),

        "dimensions": validated_metadata.get(
            "dimensions",
            [],
        ),

        "kpis": validated_metadata.get(
            "kpis",
            [],
        ),

        "top_n": validated_metadata.get(
            "top_n"
        ),

        "query_name": query_name,

        "date_range": {
            "start": START_DATE,
            "end": END_DATE,
        },

        "row_count": len(results),

        "results": results,
    }

    with open(
        RESULT_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            output,
            file,
            indent=4,
            ensure_ascii=False,
            default=str,
            allow_nan=False,
        )

    print()
    print(
        f"Aggregated results saved to:"
    )
    print(RESULT_FILE)


def main():

    print("=" * 70)
    print("WEEK 10 - AI GENERATED SQL EXECUTOR")
    print("=" * 70)

    print()
    print("[1/3] Loading validated SQL...")

    metadata, queries = load_validated_sql()

    print(
        f"Loaded {len(queries)} validated query(s)."
    )

    print()
    print("[2/3] Executing validated SQL...")

    for query in queries:

        query_name = query["name"]
        query_sql = query["sql"]

        dataframe = execute_query(
            query_name=query_name,
            query_sql=query_sql,
        )

        print()
        print("Sample results:")
        print(
            dataframe.head(5).to_string(
                index=False
            )
        )

        save_results(
            validated_metadata=metadata,
            query_name=query_name,
            dataframe=dataframe,
        )

    print()
    print("[3/3] Execution completed.")

    print()
    print("=" * 70)
    print("ORACLE EXECUTION PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()

