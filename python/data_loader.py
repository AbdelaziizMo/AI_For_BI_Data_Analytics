from pathlib import Path

from datetime import datetime

import pandas as pd
from sqlalchemy import text

from config.database import get_engine
from src.config import START_DATE, END_DATE


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
    sql_query = load_sql_query()

    engine = get_engine()

    try:
        print("=" * 70)
        print("LOADING DATA FROM ORACLE")
        print("=" * 70)
        print(f"SQL File    : {SQL_FILE}")
        print(f"START_DATE  : {START_DATE}")
        print(f"END_DATE    : {END_DATE}")
        print()

        start_date = datetime.strptime(START_DATE, "%Y-%m-%d %H:%M:%S")
        end_date = datetime.strptime(END_DATE, "%Y-%m-%d %H:%M:%S")

        sql = text(sql_query)

        df = pd.read_sql(
            sql,
            con=engine,
            params={
                "start_date": start_date,
                "end_date": end_date,
            },
        )

        # Normalize column names for Python analysis
        df.columns = [col.lower() for col in df.columns]

        print("\nColumns returned from SQL:")
        for col in df.columns:
            print(f"  - {col}")

        print(f"Rows loaded    : {len(df):,}")
        print(f"Columns loaded : {len(df.columns)}")
        print()

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
