import json
import re
from src.config import OUTPUT_DIR


INPUT_FILE = OUTPUT_DIR / "aggregated_results.json"
OUTPUT_FILE = OUTPUT_DIR / "sanitized_analysis.json"


# Only these fields are allowed to reach the AI model.
# Field matching is case-insensitive and underscore-insensitive.
ALLOWED_FIELDS = {
    "service_id",
    "service_name",
    "date",
    "transaction_date",
    "revenue_rank",
    "volume_rank",
    "total_revenue",
    "transaction_volume",
    "daily_revenue",
    "daily_transaction_volume",
    "avg_transaction_amount",
    "revenue_share",
    "volume_share",
    "previous_day_revenue",
    "revenue_growth",
    "previous_day_volume",
    "volume_growth",
}


# Fields that must never be sent to the AI model.
# Field matching is case-insensitive and underscore-insensitive.
BLOCKED_FIELDS = {
    "transactionid",
    "accountidfrom",
    "accountidto",
    "originaltrx",
    "invoiceid",
    "requestid",
    "id",
    "balancebefore",
}


def normalize_field_name(field_name):
    """
    Normalize field names for safe comparison.

    This makes the comparison insensitive to:
    - uppercase/lowercase
    - underscores
    - spaces
    - other non-alphanumeric characters

    Examples:
        Service ID -> serviceid
        service_id -> serviceid
        SERVICE ID -> serviceid

        Total Service Revenue -> totalservicerevenue
        total_service_revenue -> totalservicerevenue
    """

    return re.sub(
        r"[^a-z0-9]",
        "",
        str(field_name).strip().lower()
    )


def load_aggregated_results():
    """Load Oracle-generated aggregated results."""

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def validate_no_blocked_fields(results):
    """
    Ensure that no sensitive/raw fields exist.

    Field matching is case-insensitive
    and underscore-insensitive.
    """

    normalized_blocked_fields = {
        normalize_field_name(field)
        for field in BLOCKED_FIELDS
    }

    for row in results:

        normalized_fields = {
            normalize_field_name(field)
            for field in row.keys()
        }

        blocked_found = (
            normalized_fields.intersection(
                normalized_blocked_fields
            )
        )

        if blocked_found:
            raise ValueError(
                "Privacy violation detected. "
                "Blocked fields found: "
                + ", ".join(
                    sorted(blocked_found)
                )
            )


def sanitize_results(results):
    """
    Keep only approved aggregated analytical fields.

    The Oracle/Pandas output schema is explicitly mapped
    to the standardized snake_case schema used by the
    Privacy Guard and AI Analyst.
    """

    # Explicit mapping from the actual aggregated output
    # schema to the standardized analytical schema.
    FIELD_MAPPING = {
        "serviceid": "service_id",
        "servicename": "service_name",

        # Time-trend analytical date.
        # This is an approved analytical dimension,
        # not a raw transaction-level field.
        "date": "date",

        "transactiondate": "transaction_date",

        "dailyrevenue": "daily_revenue",
        "dailytransactionvolume": "daily_transaction_volume",
        "averagetransactionamount": "avg_transaction_amount",

        "totalservicerevenue": "total_revenue",
        "totaltransactionvolume": "transaction_volume",

        "revenuerank": "revenue_rank",
        "volumerank": "volume_rank",

        "revenueshare": "revenue_share",
        "volumeshare": "volume_share",

        "previousdayrevenue": "previous_day_revenue",
        "previousdaytransactionvolume": "previous_day_volume",

        "revenuegrowth": "revenue_growth",
        "volumegrowth": "volume_growth",
    }

    sanitized_results = []

    for row in results:

        sanitized_row = {}

        for field, value in row.items():

            normalized_field = normalize_field_name(
                field
            )

            standardized_field = FIELD_MAPPING.get(
                normalized_field
            )

            if standardized_field is not None:

                # Extra safety check:
                # only fields explicitly present in
                # ALLOWED_FIELDS can be included.
                if standardized_field in ALLOWED_FIELDS:

                    sanitized_row[
                        standardized_field
                    ] = value

        sanitized_results.append(
            sanitized_row
        )

    # Prevent an empty payload from reaching
    # the AI model.
    if not sanitized_results:
        raise ValueError(
            "No sanitized rows were produced."
        )

    # Every row must contain at least one
    # approved analytical field.
    if all(
        not row
        for row in sanitized_results
    ):
        raise ValueError(
            "Privacy Guard removed all fields "
            "from every row. "
            "Check FIELD_MAPPING against "
            "the aggregated output schema."
        )

    return sanitized_results


def build_sanitized_payload(data):
    """
    Build the final payload allowed to reach
    the AI model.
    """

    results = data.get(
        "results",
        []
    )

    validate_no_blocked_fields(
        results
    )

    sanitized_results = sanitize_results(
        results
    )

    payload = {
        "business_question": data[
            "business_question"
        ],

        "analysis_type": data[
            "analysis_type"
        ],

        "dimensions": data[
            "dimensions"
        ],

        "kpis": data[
            "kpis"
        ],

        "top_n": data[
            "top_n"
        ],

        "date_range": data[
            "date_range"
        ],

        "row_count": len(
            sanitized_results
        ),

        "privacy_status": "SANITIZED",

        "data_source": (
            "Oracle aggregated analytical results"
        ),

        "results": sanitized_results,
    }

    return payload


def save_sanitized_payload(payload):
    """Save sanitized data for the AI Analyst."""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            payload,
            file,
            indent=4,
            ensure_ascii=False,
            allow_nan=False,
        )

    print(
        f"Sanitized results saved to: "
        f"{OUTPUT_FILE}"
    )


def run_privacy_guard():
    """
    Run the complete privacy validation
    and sanitization process.
    """

    print()
    print("=" * 60)
    print("AI BI PRIVACY GUARD")
    print("=" * 60)

    print()
    print(
        "[1/4] Loading aggregated results..."
    )

    data = load_aggregated_results()

    results = data.get(
        "results",
        []
    )

    print(
        f"Loaded {len(results)} "
        "aggregated rows."
    )

    print()
    print(
        "[2/4] Checking for blocked fields..."
    )

    validate_no_blocked_fields(
        results
    )

    print(
        "No blocked/raw fields detected."
    )

    print()
    print(
        "[3/4] Sanitizing analytical results..."
    )

    payload = build_sanitized_payload(
        data
    )

    print(
        "Approved fields per row: "
        f"{len(ALLOWED_FIELDS)}"
    )

    print(
        "Sanitized rows: "
        f"{len(payload['results'])}"
    )

    print()
    print(
        "[4/4] Saving sanitized payload..."
    )

    save_sanitized_payload(
        payload
    )

    print()
    print("=" * 60)
    print(
        "PRIVACY GUARD COMPLETED SUCCESSFULLY"
    )
    print("=" * 60)


if __name__ == "__main__":
    run_privacy_guard()