from pathlib import Path

import pandas as pd

from config.database import get_engine


# ================================================================
# WEEK 10 - AI FOR BI & DATA ANALYTICS
# Data Loader
#
# Purpose:
# Execute improved.sql against Oracle and load the result
# into a pandas DataFrame.
# ================================================================


# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# SQL file
SQL_FILE = BASE_DIR / "sql" / "improved.sql"


def load_sql_query():
    """Read the improved SQL query from the SQL file."""

    if not SQL_FILE.exists():
        raise FileNotFoundError(
            f"SQL file not found: {SQL_FILE}"
        )

    sql_query = SQL_FILE.read_text(encoding="utf-8")

    # Oracle's Python driver expects a SQL statement,
    # not a SQL*Plus-style statement terminated with ';'.
    sql_query = sql_query.strip().rstrip(";")

    return sql_query


def load_data():
    """
    Execute improved.sql in Oracle and return the result
    as a pandas DataFrame.
    """

    sql_query = load_sql_query()

    engine = get_engine()

    try:
        df = pd.read_sql(
            sql_query,
            con=engine,
        )

        return df

    finally:
        engine.dispose()


if __name__ == "__main__":
    print("=" * 60)
    print("WEEK 10 - DATA LOADER TEST")
    print("=" * 60)

    try:
        df = load_data()

        print("\nSQL executed successfully.")
        print(f"Rows loaded: {len(df)}")
        print(f"Columns loaded: {len(df.columns)}")

        print("\nColumns:")
        for column in df.columns:
            print(f" - {column}")

        print("\nFirst 5 rows:")
        print(df.head())

        print("\nData types:")
        print(df.dtypes)

    except Exception as error:
        print("\nERROR:")
        print(error)
        raise
