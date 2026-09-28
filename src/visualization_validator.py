"""
Visualization Plan Validator

Validates AI-generated visualization plans against:
1. visualization_plan.json
2. sanitized_analysis.json

The validator checks:
- Privacy status
- Visualization schema
- Referenced fields
- Data types
- Chart-specific field requirements
- Visualization semantic rules

If any visualization fails validation, generation is blocked.
"""

import json
import sys
from pathlib import Path

import pandas as pd


# ============================================================
# Configuration
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

PLAN_FILE = BASE_DIR / "output" / "visualization_plan.json"
ANALYSIS_FILE = BASE_DIR / "output" / "sanitized_analysis.json"
REPORT_FILE = BASE_DIR / "output" / "visualization_validation.json"


# ============================================================
# Utility Functions
# ============================================================

def load_json(file_path: Path) -> dict:
    """Load a JSON file safely."""

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def is_numeric(series: pd.Series) -> bool:
    """Check whether a pandas Series is numeric."""

    return pd.api.types.is_numeric_dtype(series)


def is_datetime(series: pd.Series) -> bool:
    """Check whether a pandas Series contains datetime values."""

    converted = pd.to_datetime(series, errors="coerce")

    return converted.notna().all()


def is_categorical(series: pd.Series) -> bool:
    """
    Check whether a pandas Series can reasonably be used
    as a categorical field.
    """

    return (
        pd.api.types.is_object_dtype(series)
        or pd.api.types.is_string_dtype(series)
        or pd.api.types.is_categorical_dtype(series)
    )


def field_exists(field: str, dataframe: pd.DataFrame) -> bool:
    """Check whether a field exists in the analytical dataset."""

    return field in dataframe.columns


# ============================================================
# Semantic Mapping
# ============================================================

SEMANTIC_FIELD_MAP = {
    "SERVICE": ["service_name", "service_id"],
    "DATE": ["transaction_date"],

    "TOTAL_REVENUE": ["total_revenue"],
    "TRANSACTION_VOLUME": ["transaction_volume"],

    "REVENUE_SHARE": ["revenue_share"],
    "VOLUME_SHARE": ["volume_share"],

    "REVENUE_GROWTH": ["revenue_growth"],
    "VOLUME_GROWTH": ["volume_growth"],

    "REVENUE_RANK": ["revenue_rank"],
    "VOLUME_RANK": ["volume_rank"],
}


DERIVED_ANALYTICAL_FIELDS = {
    "daily_revenue",
    "daily_transaction_volume",
    "avg_transaction_amount",
    "previous_day_revenue",
    "previous_day_volume",
}


# ============================================================
# Chart Validation
# ============================================================

def validate_chart(chart: dict, dataframe: pd.DataFrame) -> dict:
    """
    Validate a single visualization definition.
    """

    errors = []
    warnings = []

    chart_type = chart.get("type")
    title = chart.get("title", "Untitled Visualization")

    # --------------------------------------------------------
    # Basic schema
    # --------------------------------------------------------

    if not chart_type:
        errors.append("Missing visualization type.")

    if not title:
        errors.append("Missing visualization title.")

    supported_types = {
        "line",
        "horizontal_bar",
        "scatter",
    }

    if chart_type not in supported_types:
        errors.append(
            f"Unsupported visualization type: {chart_type}. "
            f"Supported types: {sorted(supported_types)}"
        )

    # --------------------------------------------------------
    # Field extraction
    # --------------------------------------------------------

    x_field = chart.get("x")
    y_field = chart.get("y")
    series_field = chart.get("series")
    label_field = chart.get("label")

    # --------------------------------------------------------
    # Validate referenced fields
    # --------------------------------------------------------

    referenced_fields = []

    for field_name, field_value in {
        "x": x_field,
        "y": y_field,
        "series": series_field,
        "label": label_field,
    }.items():

        if field_value:
            referenced_fields.append(field_value)

            if not field_exists(field_value, dataframe):
                errors.append(
                    f"{field_name} field '{field_value}' "
                    f"does not exist in sanitized_analysis.json."
                )

    # Stop type checks if required fields are missing.
    if errors:
        return {
            "title": title,
            "type": chart_type,
            "status": "REJECT",
            "fields": "INVALID",
            "types": "NOT_CHECKED",
            "semantic_rules": "NOT_CHECKED",
            "errors": errors,
            "warnings": warnings,
        }

    # --------------------------------------------------------
    # Field type validation
    # --------------------------------------------------------

    type_errors = []

    if chart_type == "line":

        if not x_field or not y_field:
            type_errors.append(
                "Line chart requires both x and y fields."
            )

        else:
            if not is_datetime(dataframe[x_field]):
                type_errors.append(
                    f"Line chart x field '{x_field}' "
                    f"must be datetime-compatible."
                )

            if not is_numeric(dataframe[y_field]):
                type_errors.append(
                    f"Line chart y field '{y_field}' "
                    f"must be numeric."
                )

            if series_field:

                if not is_categorical(dataframe[series_field]):
                    type_errors.append(
                        f"Line chart series field '{series_field}' "
                        f"must be categorical."
                    )

    elif chart_type == "horizontal_bar":

        if not x_field or not y_field:
            type_errors.append(
                "Horizontal bar chart requires both x and y fields."
            )

        else:
            if not is_numeric(dataframe[x_field]):
                type_errors.append(
                    f"Horizontal bar x field '{x_field}' "
                    f"must be numeric."
                )

            if not is_categorical(dataframe[y_field]):
                type_errors.append(
                    f"Horizontal bar y field '{y_field}' "
                    f"must be categorical."
                )

    elif chart_type == "scatter":

        if not x_field or not y_field:
            type_errors.append(
                "Scatter chart requires both x and y fields."
            )

        else:
            if not is_numeric(dataframe[x_field]):
                type_errors.append(
                    f"Scatter x field '{x_field}' "
                    f"must be numeric."
                )

            if not is_numeric(dataframe[y_field]):
                type_errors.append(
                    f"Scatter y field '{y_field}' "
                    f"must be numeric."
                )

            if label_field:

                if not is_categorical(dataframe[label_field]):
                    type_errors.append(
                        f"Scatter label field '{label_field}' "
                        f"must be categorical."
                    )

    if type_errors:
        errors.extend(type_errors)

    # --------------------------------------------------------
    # Semantic validation
    # --------------------------------------------------------

    semantic_errors = []

    # x and y should never be identical.
    if x_field and y_field and x_field == y_field:
        semantic_errors.append(
            "x and y fields cannot be the same."
        )

    # Series should not be the x-axis.
    if chart_type == "line" and series_field:

        if series_field == x_field:
            semantic_errors.append(
                "Line chart series field cannot be the same "
                "as the x-axis field."
            )

    # Scatter label should not be x or y.
    if chart_type == "scatter" and label_field:

        if label_field == x_field:
            semantic_errors.append(
                "Scatter label field cannot be the same "
                "as the x-axis field."
            )

        if label_field == y_field:
            semantic_errors.append(
                "Scatter label field cannot be the same "
                "as the y-axis field."
            )

    # Horizontal bar needs categorical dimension on y.
    if chart_type == "horizontal_bar":

        if y_field == x_field:
            semantic_errors.append(
                "Horizontal bar chart dimension and measure "
                "cannot use the same field."
            )

    if semantic_errors:
        errors.extend(semantic_errors)

    # --------------------------------------------------------
    # Warnings
    # --------------------------------------------------------

    # Informational warning for fields that are derived analytical
    # measures rather than explicitly declared KPIs.
    for field in referenced_fields:

        declared = any(
            field in candidates
            for candidates in SEMANTIC_FIELD_MAP.values()
        )

        if not declared and field in DERIVED_ANALYTICAL_FIELDS:

            warnings.append(
                f"'{field}' is a derived analytical measure "
                f"and is not explicitly listed in the KPI metadata."
            )

    # --------------------------------------------------------
    # Final status
    # --------------------------------------------------------

    status = "PASS" if not errors else "REJECT"

    return {
        "title": title,
        "type": chart_type,
        "fields": "VALID" if not errors else "INVALID",
        "types": "VALID" if not type_errors else "INVALID",
        "semantic_rules": (
            "VALID"
            if not semantic_errors
            else "INVALID"
        ),
        "status": status,
        "referenced_fields": referenced_fields,
        "errors": errors,
        "warnings": warnings,
    }


# ============================================================
# Main Validation
# ============================================================

def main():

    print("=" * 60)
    print("VISUALIZATION VALIDATOR")
    print("=" * 60)

    # --------------------------------------------------------
    # Step 1: Load visualization plan
    # --------------------------------------------------------

    print("\n[1/4] Loading visualization plan...")

    try:
        plan = load_json(PLAN_FILE)

    except Exception as error:
        print(f"ERROR: {error}")
        sys.exit(1)

    visualizations = plan.get("visualizations")

    if not isinstance(visualizations, list):
        print(
            "ERROR: 'visualizations' must be a list."
        )
        sys.exit(1)

    print(
        f"Found {len(visualizations)} visualizations."
    )

    if len(visualizations) == 0:
        print(
            "ERROR: Visualization plan contains no visualizations."
        )
        sys.exit(1)

    # --------------------------------------------------------
    # Step 2: Load sanitized analytical data
    # --------------------------------------------------------

    print("\n[2/4] Loading sanitized analytical data...")

    try:
        analysis = load_json(ANALYSIS_FILE)

    except Exception as error:
        print(f"ERROR: {error}")
        sys.exit(1)

    results = analysis.get("results")

    if not isinstance(results, list):
        print(
            "ERROR: 'results' must be a list "
            "inside sanitized_analysis.json."
        )
        sys.exit(1)

    if not results:
        print(
            "ERROR: 'results' contains no analytical rows."
        )
        sys.exit(1)

    dataframe = pd.DataFrame(results)

    print(
        f"Loaded {len(dataframe):,} rows."
    )

    print(
        f"Available fields: {len(dataframe.columns)}"
    )

    # --------------------------------------------------------
    # Step 3: Privacy validation
    # --------------------------------------------------------

    print("\n[3/4] Checking privacy status...")

    privacy_status = analysis.get("privacy_status")

    print(
        f"Privacy status: {privacy_status}"
    )

    if privacy_status != "SANITIZED":

        print(
            "\nERROR: Analytical data is not marked as SANITIZED."
        )

        print(
            "Visualization generation has been BLOCKED."
        )

        report = {
            "status": "BLOCKED",
            "reason": "privacy_status is not SANITIZED",
            "privacy_status": privacy_status,
            "total_visualizations": len(visualizations),
            "passed": 0,
            "rejected": len(visualizations),
            "visualizations": [],
        }

        with open(
            REPORT_FILE,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                report,
                file,
                indent=4,
                ensure_ascii=False,
            )

        sys.exit(1)

    # --------------------------------------------------------
    # Step 4: Validate visualizations
    # --------------------------------------------------------

    print("\n[4/4] Validating visualizations...")

    validation_results = []

    passed = 0
    rejected = 0

    for index, chart in enumerate(
        visualizations,
        start=1
    ):

        result = validate_chart(
            chart,
            dataframe
        )

        validation_results.append(result)

        print(
            f"\n[{index}] {result['title']}"
        )

        print(
            f"    Type: {result['type']}"
        )

        print(
            f"    Fields: {result['fields']}"
        )

        print(
            f"    Types: {result['types']}"
        )

        print(
            f"    Semantic rules: "
            f"{result['semantic_rules']}"
        )

        print(
            f"    Status: {result['status']}"
        )

        if result["warnings"]:

            for warning in result["warnings"]:
                print(
                    f"    WARNING: {warning}"
                )

        if result["errors"]:

            for error in result["errors"]:
                print(
                    f"    ERROR: {error}"
                )

        if result["status"] == "PASS":
            passed += 1
        else:
            rejected += 1

    # --------------------------------------------------------
    # Final status
    # --------------------------------------------------------

    if rejected == 0:
        overall_status = "SAFE_TO_GENERATE"
    else:
        overall_status = "BLOCKED"

    report = {
        "status": overall_status,
        "privacy_status": privacy_status,

        "analysis_type": analysis.get(
            "analysis_type"
        ),

        "business_question": analysis.get(
            "business_question"
        ),

        "dimensions": analysis.get(
            "dimensions",
            []
        ),

        "kpis": analysis.get(
            "kpis",
            []
        ),

        "total_visualizations": len(
            visualizations
        ),

        "passed": passed,

        "rejected": rejected,

        "visualizations": validation_results,
    }

    # --------------------------------------------------------
    # Save validation report
    # --------------------------------------------------------

    with open(
        REPORT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            report,
            file,
            indent=4,
            ensure_ascii=False,
        )

    # --------------------------------------------------------
    # Console summary
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    print(
        f"Total visualizations: "
        f"{len(visualizations)}"
    )

    print(
        f"Passed: {passed}"
    )

    print(
        f"Rejected: {rejected}"
    )

    print(
        f"Status: {overall_status}"
    )

    print(
        f"\nValidation report saved to:"
        f"\n{REPORT_FILE}"
    )

    print("=" * 60)

    # --------------------------------------------------------
    # Block visualization generation if unsafe
    # --------------------------------------------------------

    if rejected > 0:

        print(
            "\nVisualization generation BLOCKED."
        )

        print(
            "Fix the rejected visualization plan "
            "before generating charts."
        )

        sys.exit(1)

    print(
        "\nVisualization plan passed validation."
    )

    print(
        "SAFE_TO_GENERATE"
    )

    sys.exit(0)


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    main()