
import pandas as pd

from python.data_loader import load_data


# ================================================================
# WEEK 10 - AI FOR BI & DATA ANALYTICS
# Business Analysis
# ================================================================


# ================================================================
# Configuration
# ================================================================

TOP_N = 10

# Growth percentages can become extremely large when the
# previous day's value is very small.
# We keep the original SQL growth values but also create
# a filtered business view using a minimum previous-day value.
MIN_PREVIOUS_REVENUE = 100.0
MIN_PREVIOUS_VOLUME = 10


# ================================================================
# Validation
# ================================================================

REQUIRED_COLUMNS = [
    "service_id",
    "service_name",
    "transaction_date",
    "daily_transaction_volume",
    "daily_revenue",
    "avg_transaction_amount",
    "total_transaction_volume",
    "total_revenue",
    "revenue_rank",
    "volume_rank",
    "previous_day_revenue",
    "previous_day_volume",
    "revenue_growth_percent",
    "volume_growth_percent",
]


def validate_dataframe(df: pd.DataFrame) -> None:
    """
    Validate that the DataFrame contains all columns required
    for the business analysis.
    """

    if df.empty:
        raise ValueError("The loaded DataFrame is empty.")

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing required columns: "
            + ", ".join(missing_columns)
        )


# ================================================================
# Overall Metrics
# ================================================================

def calculate_overall_metrics(df: pd.DataFrame) -> dict:
    """
    Calculate overall business metrics.

    IMPORTANT:
    total_revenue and total_transaction_volume columns contain
    service-level totals repeated across daily rows.

    Therefore, using max() is NOT a valid way to calculate
    overall totals.

    Overall totals are calculated from the daily metrics instead.
    """

    total_revenue = df["daily_revenue"].sum()

    total_transaction_volume = (
        df["daily_transaction_volume"].sum()
    )

    number_of_services = df["service_id"].nunique()

    number_of_days = df["transaction_date"].nunique()

    min_date = df["transaction_date"].min()

    max_date = df["transaction_date"].max()

    average_daily_revenue = (
        total_revenue / number_of_days
        if number_of_days > 0
        else 0
    )

    average_daily_volume = (
        total_transaction_volume / number_of_days
        if number_of_days > 0
        else 0
    )

    return {
        "total_revenue": float(total_revenue),
        "total_transaction_volume": int(total_transaction_volume),
        "number_of_services": int(number_of_services),
        "number_of_days": int(number_of_days),
        "start_date": min_date,
        "end_date": max_date,
        "average_daily_revenue": float(average_daily_revenue),
        "average_daily_transaction_volume": float(
            average_daily_volume
        ),
    }


# ================================================================
# Service-Level Summary
# ================================================================

def create_service_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create one row per service using the service-level totals
    already calculated by the SQL query.
    """

    service_summary = (
        df[
            [
                "service_id",
                "service_name",
                "total_revenue",
                "total_transaction_volume",
                "revenue_rank",
                "volume_rank",
            ]
        ]
        .drop_duplicates(subset=["service_id"])
        .copy()
    )

    service_summary = service_summary.sort_values(
        by="total_revenue",
        ascending=False,
    ).reset_index(drop=True)

    return service_summary


# ================================================================
# Top Services by Revenue
# ================================================================

def get_top_revenue_services(
    service_summary: pd.DataFrame,
    top_n: int = TOP_N,
) -> pd.DataFrame:
    """
    Return the top services by total revenue.
    """

    return (
        service_summary[
            [
                "service_id",
                "service_name",
                "total_revenue",
                "revenue_rank",
            ]
        ]
        .sort_values(
            by="total_revenue",
            ascending=False,
        )
        .head(top_n)
        .reset_index(drop=True)
    )


# ================================================================
# Top Services by Transaction Volume
# ================================================================

def get_top_volume_services(
    service_summary: pd.DataFrame,
    top_n: int = TOP_N,
) -> pd.DataFrame:
    """
    Return the top services by total transaction volume.
    """

    return (
        service_summary[
            [
                "service_id",
                "service_name",
                "total_transaction_volume",
                "volume_rank",
            ]
        ]
        .sort_values(
            by="total_transaction_volume",
            ascending=False,
        )
        .head(top_n)
        .reset_index(drop=True)
    )


# ================================================================
# Daily Revenue Trend
# ================================================================

def calculate_daily_revenue_trend(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Aggregate revenue across all services for each day.
    """

    daily_revenue = (
        df.groupby(
            "transaction_date",
            as_index=False,
        )["daily_revenue"]
        .sum()
        .sort_values("transaction_date")
        .reset_index(drop=True)
    )

    daily_revenue["revenue_change"] = (
        daily_revenue["daily_revenue"].diff()
    )

    daily_revenue["revenue_growth_percent"] = (
        daily_revenue["daily_revenue"]
        .pct_change()
        .mul(100)
    )

    return daily_revenue


# ================================================================
# Daily Transaction Volume Trend
# ================================================================

def calculate_daily_volume_trend(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Aggregate transaction volume across all services for each day.
    """

    daily_volume = (
        df.groupby(
            "transaction_date",
            as_index=False,
        )["daily_transaction_volume"]
        .sum()
        .sort_values("transaction_date")
        .reset_index(drop=True)
    )

    daily_volume["volume_change"] = (
        daily_volume["daily_transaction_volume"].diff()
    )

    daily_volume["volume_growth_percent"] = (
        daily_volume["daily_transaction_volume"]
        .pct_change()
        .mul(100)
    )

    return daily_volume


# ================================================================
# Combined Daily Trend
# ================================================================

def create_daily_business_trend(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Combine daily revenue and transaction volume into one
    business trend DataFrame.
    """

    daily_revenue = calculate_daily_revenue_trend(df)

    daily_volume = calculate_daily_volume_trend(df)

    daily_trend = pd.merge(
        daily_revenue,
        daily_volume,
        on="transaction_date",
        how="outer",
    )

    return daily_trend.sort_values(
        "transaction_date"
    ).reset_index(drop=True)


# ================================================================
# Revenue Growth Analysis
# ================================================================

def calculate_revenue_growth_analysis(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Analyze service-level revenue growth.

    Returns:
        1. Raw growth ranking.
        2. Business-filtered growth ranking.

    The filtered version ignores extremely small previous-day
    revenue values because they can create misleading growth
    percentages.
    """

    growth_df = (
        df[
            [
                "service_id",
                "service_name",
                "transaction_date",
                "daily_revenue",
                "previous_day_revenue",
                "revenue_growth_percent",
            ]
        ]
        .dropna(
            subset=[
                "revenue_growth_percent",
            ]
        )
        .copy()
    )

    raw_growth = (
        growth_df
        .sort_values(
            "revenue_growth_percent",
            ascending=False,
        )
        .head(TOP_N)
        .reset_index(drop=True)
    )

    filtered_growth = growth_df[
        growth_df["previous_day_revenue"]
        >= MIN_PREVIOUS_REVENUE
    ].copy()

    filtered_growth = (
        filtered_growth
        .sort_values(
            "revenue_growth_percent",
            ascending=False,
        )
        .head(TOP_N)
        .reset_index(drop=True)
    )

    return raw_growth, filtered_growth


# ================================================================
# Revenue Decline Analysis
# ================================================================

def calculate_revenue_decline_analysis(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Analyze service-level revenue declines.
    """

    growth_df = (
        df[
            [
                "service_id",
                "service_name",
                "transaction_date",
                "daily_revenue",
                "previous_day_revenue",
                "revenue_growth_percent",
            ]
        ]
        .dropna(
            subset=[
                "revenue_growth_percent",
            ]
        )
        .copy()
    )

    raw_decline = (
        growth_df
        .sort_values(
            "revenue_growth_percent",
            ascending=True,
        )
        .head(TOP_N)
        .reset_index(drop=True)
    )

    filtered_decline = growth_df[
        growth_df["previous_day_revenue"]
        >= MIN_PREVIOUS_REVENUE
    ].copy()

    filtered_decline = (
        filtered_decline
        .sort_values(
            "revenue_growth_percent",
            ascending=True,
        )
        .head(TOP_N)
        .reset_index(drop=True)
    )

    return raw_decline, filtered_decline


# ================================================================
# Volume Growth Analysis
# ================================================================

def calculate_volume_growth_analysis(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Analyze service-level transaction volume growth.
    """

    growth_df = (
        df[
            [
                "service_id",
                "service_name",
                "transaction_date",
                "daily_transaction_volume",
                "previous_day_volume",
                "volume_growth_percent",
            ]
        ]
        .dropna(
            subset=[
                "volume_growth_percent",
            ]
        )
        .copy()
    )

    raw_growth = (
        growth_df
        .sort_values(
            "volume_growth_percent",
            ascending=False,
        )
        .head(TOP_N)
        .reset_index(drop=True)
    )

    filtered_growth = growth_df[
        growth_df["previous_day_volume"]
        >= MIN_PREVIOUS_VOLUME
    ].copy()

    filtered_growth = (
        filtered_growth
        .sort_values(
            "volume_growth_percent",
            ascending=False,
        )
        .head(TOP_N)
        .reset_index(drop=True)
    )

    return raw_growth, filtered_growth


# ================================================================
# Volume Decline Analysis
# ================================================================

def calculate_volume_decline_analysis(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Analyze service-level transaction volume declines.
    """

    growth_df = (
        df[
            [
                "service_id",
                "service_name",
                "transaction_date",
                "daily_transaction_volume",
                "previous_day_volume",
                "volume_growth_percent",
            ]
        ]
        .dropna(
            subset=[
                "volume_growth_percent",
            ]
        )
        .copy()
    )

    raw_decline = (
        growth_df
        .sort_values(
            "volume_growth_percent",
            ascending=True,
        )
        .head(TOP_N)
        .reset_index(drop=True)
    )

    filtered_decline = growth_df[
        growth_df["previous_day_volume"]
        >= MIN_PREVIOUS_VOLUME
    ].copy()

    filtered_decline = (
        filtered_decline
        .sort_values(
            "volume_growth_percent",
            ascending=True,
        )
        .head(TOP_N)
        .reset_index(drop=True)
    )

    return raw_decline, filtered_decline


# ================================================================
# Revenue Concentration
# ================================================================

def calculate_revenue_concentration(
    service_summary: pd.DataFrame,
    overall_revenue: float,
    top_n: int = TOP_N,
) -> dict:
    """
    Calculate how much of the total revenue is generated
    by the top N services.
    """

    top_revenue = (
        service_summary
        .nlargest(
            top_n,
            "total_revenue",
        )["total_revenue"]
        .sum()
    )

    concentration_percent = (
        (top_revenue / overall_revenue) * 100
        if overall_revenue > 0
        else 0
    )

    return {
        "top_n": top_n,
        "top_n_revenue": float(top_revenue),
        "top_n_revenue_share_percent": float(
            concentration_percent
        ),
    }


# ================================================================
# Volume Concentration
# ================================================================

def calculate_volume_concentration(
    service_summary: pd.DataFrame,
    overall_volume: int,
    top_n: int = TOP_N,
) -> dict:
    """
    Calculate how much of the total transaction volume is
    generated by the top N services.
    """

    top_volume = (
        service_summary
        .nlargest(
            top_n,
            "total_transaction_volume",
        )["total_transaction_volume"]
        .sum()
    )

    concentration_percent = (
        (top_volume / overall_volume) * 100
        if overall_volume > 0
        else 0
    )

    return {
        "top_n": top_n,
        "top_n_transaction_volume": int(top_volume),
        "top_n_volume_share_percent": float(
            concentration_percent
        ),
    }


# ================================================================
# Data Quality Analysis
# ================================================================

def calculate_data_quality(df: pd.DataFrame) -> dict:
    """
    Calculate meaningful data-quality metrics.

    NULLs in previous_day_* and growth columns are expected
    for the first day of each service and are therefore not
    automatically considered data-quality problems.
    """

    growth_columns = [
        "previous_day_revenue",
        "previous_day_volume",
        "revenue_growth_percent",
        "volume_growth_percent",
    ]

    other_columns = [
        column
        for column in df.columns
        if column not in growth_columns
    ]

    unexpected_nulls = int(
        df[other_columns].isnull().sum().sum()
    )

    expected_growth_nulls = int(
        df[growth_columns].isnull().sum().sum()
    )

    duplicate_rows = int(
        df.duplicated().sum()
    )

    invalid_revenue_rows = int(
        (df["daily_revenue"] < 0).sum()
    )

    invalid_volume_rows = int(
        (df["daily_transaction_volume"] < 0).sum()
    )

    return {
        "total_rows": int(len(df)),
        "total_columns": int(len(df.columns)),
        "unexpected_null_values": unexpected_nulls,
        "expected_growth_null_values": expected_growth_nulls,
        "duplicate_rows": duplicate_rows,
        "negative_revenue_rows": invalid_revenue_rows,
        "negative_volume_rows": invalid_volume_rows,
    }


# ================================================================
# Main Analysis Function
# ================================================================

def analyze_data(df: pd.DataFrame) -> dict:
    """
    Execute the complete business analysis pipeline.
    """

    validate_dataframe(df)

    overall = calculate_overall_metrics(df)

    service_summary = create_service_summary(df)

    top_revenue_services = get_top_revenue_services(
        service_summary
    )

    top_volume_services = get_top_volume_services(
        service_summary
    )

    daily_revenue_trend = calculate_daily_revenue_trend(
        df
    )

    daily_volume_trend = calculate_daily_volume_trend(
        df
    )

    daily_business_trend = create_daily_business_trend(
        df
    )

    (
        raw_revenue_growth,
        filtered_revenue_growth,
    ) = calculate_revenue_growth_analysis(df)

    (
        raw_revenue_decline,
        filtered_revenue_decline,
    ) = calculate_revenue_decline_analysis(df)

    (
        raw_volume_growth,
        filtered_volume_growth,
    ) = calculate_volume_growth_analysis(df)

    (
        raw_volume_decline,
        filtered_volume_decline,
    ) = calculate_volume_decline_analysis(df)

    revenue_concentration = (
        calculate_revenue_concentration(
            service_summary,
            overall["total_revenue"],
        )
    )

    volume_concentration = (
        calculate_volume_concentration(
            service_summary,
            overall["total_transaction_volume"],
        )
    )

    data_quality = calculate_data_quality(df)

    return {
        "overall": overall,

        "service_summary": service_summary,

        "top_revenue_services": top_revenue_services,

        "top_volume_services": top_volume_services,

        "daily_revenue_trend": daily_revenue_trend,

        "daily_volume_trend": daily_volume_trend,

        "daily_business_trend": daily_business_trend,

        "raw_revenue_growth": raw_revenue_growth,

        "filtered_revenue_growth": filtered_revenue_growth,

        "raw_revenue_decline": raw_revenue_decline,

        "filtered_revenue_decline": filtered_revenue_decline,

        "raw_volume_growth": raw_volume_growth,

        "filtered_volume_growth": filtered_volume_growth,

        "raw_volume_decline": raw_volume_decline,

        "filtered_volume_decline": filtered_volume_decline,

        "revenue_concentration": revenue_concentration,

        "volume_concentration": volume_concentration,

        "data_quality": data_quality,
    }


# ================================================================
# Printing Helpers
# ================================================================

def print_dataframe(
    title: str,
    df: pd.DataFrame,
) -> None:
    """
    Print a DataFrame with a consistent format.
    """

    print(f"\n{title}")
    print("-" * 70)

    if df.empty:
        print("No data available.")
        return

    print(
        df.to_string(
            index=False,
        )
    )


def print_analysis(results: dict) -> None:
    """
    Print business analysis results in a readable format.
    """

    print("\n" + "=" * 70)
    print("WEEK 10 - BUSINESS ANALYSIS")
    print("=" * 70)

    # ------------------------------------------------------------
    # Overall Metrics
    # ------------------------------------------------------------

    overall = results["overall"]

    print("\nOVERALL METRICS")
    print("-" * 70)

    print(
        f"Total Revenue: "
        f"{overall['total_revenue']:,.2f}"
    )

    print(
        f"Total Transaction Volume: "
        f"{overall['total_transaction_volume']:,}"
    )

    print(
        f"Number of Services: "
        f"{overall['number_of_services']:,}"
    )

    print(
        f"Analysis Days: "
        f"{overall['number_of_days']:,}"
    )

    print(
        f"Start Date: "
        f"{overall['start_date']}"
    )

    print(
        f"End Date: "
        f"{overall['end_date']}"
    )

    print(
        f"Average Daily Revenue: "
        f"{overall['average_daily_revenue']:,.2f}"
    )

    print(
        f"Average Daily Transaction Volume: "
        f"{overall['average_daily_transaction_volume']:,.2f}"
    )

    # ------------------------------------------------------------
    # Top Revenue Services
    # ------------------------------------------------------------

    print_dataframe(
        "TOP 10 SERVICES BY REVENUE",
        results["top_revenue_services"],
    )

    # ------------------------------------------------------------
    # Top Volume Services
    # ------------------------------------------------------------

    print_dataframe(
        "TOP 10 SERVICES BY TRANSACTION VOLUME",
        results["top_volume_services"],
    )

    # ------------------------------------------------------------
    # Daily Business Trend
    # ------------------------------------------------------------

    print_dataframe(
        "DAILY BUSINESS TREND",
        results["daily_business_trend"],
    )

    # ------------------------------------------------------------
    # Raw Revenue Growth
    # ------------------------------------------------------------

    print_dataframe(
        "RAW HIGHEST REVENUE GROWTH",
        results["raw_revenue_growth"],
    )

    # ------------------------------------------------------------
    # Filtered Revenue Growth
    # ------------------------------------------------------------

    print_dataframe(
        "BUSINESS-FILTERED HIGHEST REVENUE GROWTH",
        results["filtered_revenue_growth"],
    )

    # ------------------------------------------------------------
    # Raw Revenue Decline
    # ------------------------------------------------------------

    print_dataframe(
        "RAW HIGHEST REVENUE DECLINE",
        results["raw_revenue_decline"],
    )

    # ------------------------------------------------------------
    # Filtered Revenue Decline
    # ------------------------------------------------------------

    print_dataframe(
        "BUSINESS-FILTERED HIGHEST REVENUE DECLINE",
        results["filtered_revenue_decline"],
    )

    # ------------------------------------------------------------
    # Raw Volume Growth
    # ------------------------------------------------------------

    print_dataframe(
        "RAW HIGHEST VOLUME GROWTH",
        results["raw_volume_growth"],
    )

    # ------------------------------------------------------------
    # Filtered Volume Growth
    # ------------------------------------------------------------

    print_dataframe(
        "BUSINESS-FILTERED HIGHEST VOLUME GROWTH",
        results["filtered_volume_growth"],
    )

    # ------------------------------------------------------------
    # Raw Volume Decline
    # ------------------------------------------------------------

    print_dataframe(
        "RAW HIGHEST VOLUME DECLINE",
        results["raw_volume_decline"],
    )

    # ------------------------------------------------------------
    # Filtered Volume Decline
    # ------------------------------------------------------------

    print_dataframe(
        "BUSINESS-FILTERED HIGHEST VOLUME DECLINE",
        results["filtered_volume_decline"],
    )

    # ------------------------------------------------------------
    # Concentration
    # ------------------------------------------------------------

    revenue_concentration = results[
        "revenue_concentration"
    ]

    volume_concentration = results[
        "volume_concentration"
    ]

    print("\nREVENUE CONCENTRATION")
    print("-" * 70)

    print(
        f"Top {revenue_concentration['top_n']} "
        f"Revenue: "
        f"{revenue_concentration['top_n_revenue']:,.2f}"
    )

    print(
        f"Top {revenue_concentration['top_n']} "
        f"Revenue Share: "
        f"{revenue_concentration['top_n_revenue_share_percent']:.2f}%"
    )

    print("\nTRANSACTION VOLUME CONCENTRATION")
    print("-" * 70)

    print(
        f"Top {volume_concentration['top_n']} "
        f"Transaction Volume: "
        f"{volume_concentration['top_n_transaction_volume']:,}"
    )

    print(
        f"Top {volume_concentration['top_n']} "
        f"Volume Share: "
        f"{volume_concentration['top_n_volume_share_percent']:.2f}%"
    )

    # ------------------------------------------------------------
    # Data Quality
    # ------------------------------------------------------------

    quality = results["data_quality"]

    print("\nDATA QUALITY")
    print("-" * 70)

    print(
        f"Rows: "
        f"{quality['total_rows']:,}"
    )

    print(
        f"Columns: "
        f"{quality['total_columns']:,}"
    )

    print(
        f"Unexpected NULL Values: "
        f"{quality['unexpected_null_values']:,}"
    )

    print(
        f"Expected Growth NULL Values: "
        f"{quality['expected_growth_null_values']:,}"
    )

    print(
        f"Duplicate Rows: "
        f"{quality['duplicate_rows']:,}"
    )

    print(
        f"Negative Revenue Rows: "
        f"{quality['negative_revenue_rows']:,}"
    )

    print(
        f"Negative Volume Rows: "
        f"{quality['negative_volume_rows']:,}"
    )

    print("\n" + "=" * 70)
    print("BUSINESS ANALYSIS COMPLETED")
    print("=" * 70)


# ================================================================
# Main
# ================================================================

if __name__ == "__main__":

    print("=" * 70)
    print("WEEK 10 - LOADING DATA FOR ANALYSIS")
    print("=" * 70)

    try:
        df = load_data()

        print(
            f"\nLoaded {len(df):,} rows successfully."
        )

        results = analyze_data(df)

        print_analysis(results)

    except Exception as error:

        print("\nERROR:")
        print(error)

        raise
