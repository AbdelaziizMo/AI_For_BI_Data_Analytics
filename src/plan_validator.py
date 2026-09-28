import json
from pathlib import Path


# ================================================================
# WEEK 10 - AI FOR BI & DATA ANALYTICS
# ANALYSIS PLAN VALIDATOR
# ================================================================

BASE_DIR = Path(__file__).resolve().parent.parent
PLAN_FILE = BASE_DIR / "output" / "analysis_plan.json"


# ================================================================
# SUPPORTED CAPABILITIES
# ================================================================

SUPPORTED_ANALYSIS_TYPES = {
    "SERVICE_PERFORMANCE",
    "TIME_TREND",
    "SERVICE_TREND",
    "SERVICE_RANKING",
    "REVENUE_CONCENTRATION",
}

SUPPORTED_DIMENSIONS = {
    "SERVICE",
    "DATE",
}

SUPPORTED_KPIS = {
    "TOTAL_REVENUE",
    "TRANSACTION_VOLUME",
    "REVENUE_SHARE",
    "VOLUME_SHARE",
    "REVENUE_GROWTH",
    "VOLUME_GROWTH",
    "REVENUE_RANK",
    "VOLUME_RANK",
    "DAILY_REVENUE",
    "DAILY_VOLUME",
    "AVERAGE_TRANSACTION_VALUE",
}


# ================================================================
# LOAD ANALYSIS PLAN
# ================================================================

def load_analysis_plan() -> dict:
    if not PLAN_FILE.exists():
        raise FileNotFoundError(
            f"Analysis plan not found:\n{PLAN_FILE}"
        )

    with open(
        PLAN_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        plan = json.load(file)

    if not isinstance(plan, dict):
        raise ValueError(
            "Analysis plan must be a JSON object."
        )

    return plan


# ================================================================
# VALIDATE REQUIRED FIELDS
# ================================================================

def validate_required_fields(plan: dict) -> None:

    required_fields = {
        "business_question",
        "analysis_type",
        "dimensions",
        "kpis",
    }

    missing_fields = required_fields - plan.keys()

    if missing_fields:
        raise ValueError(
            "Missing required fields: "
            + ", ".join(sorted(missing_fields))
        )


# ================================================================
# VALIDATE BUSINESS QUESTION
# ================================================================

def validate_business_question(plan: dict) -> None:

    question = plan.get("business_question")

    if not isinstance(question, str):
        raise ValueError(
            "business_question must be a string."
        )

    if not question.strip():
        raise ValueError(
            "business_question cannot be empty."
        )


# ================================================================
# VALIDATE ANALYSIS TYPE
# ================================================================

def validate_analysis_type(plan: dict) -> None:

    analysis_type = plan.get("analysis_type")

    if analysis_type not in SUPPORTED_ANALYSIS_TYPES:
        raise ValueError(
            f"Unsupported analysis_type: {analysis_type}"
        )


# ================================================================
# VALIDATE DIMENSIONS
# ================================================================

def validate_dimensions(plan: dict) -> None:

    dimensions = plan.get("dimensions")

    if not isinstance(dimensions, list):
        raise ValueError(
            "dimensions must be a list."
        )

    if not dimensions:
        raise ValueError(
            "dimensions cannot be empty."
        )

    unsupported_dimensions = (
        set(dimensions) - SUPPORTED_DIMENSIONS
    )

    if unsupported_dimensions:
        raise ValueError(
            "Unsupported dimension(s): "
            + ", ".join(sorted(unsupported_dimensions))
        )


# ================================================================
# VALIDATE KPIs
# ================================================================

def validate_kpis(plan: dict) -> None:

    kpis = plan.get("kpis")

    if not isinstance(kpis, list):
        raise ValueError(
            "kpis must be a list."
        )

    if not kpis:
        raise ValueError(
            "kpis cannot be empty."
        )

    unsupported_kpis = set(kpis) - SUPPORTED_KPIS

    if unsupported_kpis:
        raise ValueError(
            "Unsupported KPI(s): "
            + ", ".join(sorted(unsupported_kpis))
        )


# ================================================================
# VALIDATE TOP N
# ================================================================

def validate_top_n(plan: dict) -> None:

    if "top_n" not in plan:
        return

    top_n = plan["top_n"]

    if not isinstance(top_n, int):
        raise ValueError(
            "top_n must be an integer."
        )

    if top_n <= 0:
        raise ValueError(
            "top_n must be greater than zero."
        )

    if top_n > 100:
        raise ValueError(
            "top_n cannot be greater than 100."
        )


# ================================================================
# VALIDATE PLAN CONSISTENCY
# ================================================================

def validate_plan_consistency(plan: dict) -> None:

    analysis_type = plan["analysis_type"]
    dimensions = set(plan["dimensions"])
    kpis = set(plan["kpis"])

    # ------------------------------------------------------------
    # SERVICE_PERFORMANCE
    # ------------------------------------------------------------

    if analysis_type == "SERVICE_PERFORMANCE":

        if "SERVICE" not in dimensions:
            raise ValueError(
                "SERVICE_PERFORMANCE analysis requires SERVICE dimension."
            )

        performance_kpis = {
            "TOTAL_REVENUE",
            "TRANSACTION_VOLUME",
            "AVERAGE_TRANSACTION_VALUE",
            "REVENUE_SHARE",
            "VOLUME_SHARE",
            "REVENUE_RANK",
            "VOLUME_RANK",
        }

        if not performance_kpis.intersection(kpis):
            raise ValueError(
                "SERVICE_PERFORMANCE requires at least one service performance KPI."
            )

    # ------------------------------------------------------------
    # TIME_TREND
    # ------------------------------------------------------------

    if analysis_type == "TIME_TREND":

        if "DATE" not in dimensions:
            raise ValueError(
                "TIME_TREND analysis requires DATE dimension."
            )

        trend_kpis = {
            "DAILY_REVENUE",
            "DAILY_VOLUME",
            "REVENUE_GROWTH",
            "VOLUME_GROWTH",
        }

        if not trend_kpis.intersection(kpis):
            raise ValueError(
                "TIME_TREND requires at least one time-trend KPI."
            )

    # ------------------------------------------------------------
    # SERVICE_TREND
    # ------------------------------------------------------------

    if analysis_type == "SERVICE_TREND":

        if "SERVICE" not in dimensions:
            raise ValueError(
                "SERVICE_TREND analysis requires SERVICE dimension."
            )

        if "DATE" not in dimensions:
            raise ValueError(
                "SERVICE_TREND analysis requires DATE dimension."
            )

        trend_kpis = {
            "REVENUE_GROWTH",
            "VOLUME_GROWTH",
            "DAILY_REVENUE",
            "DAILY_VOLUME",
        }

        if not trend_kpis.intersection(kpis):
            raise ValueError(
                "SERVICE_TREND requires at least one trend KPI."
            )

    # ------------------------------------------------------------
    # SERVICE_RANKING
    # ------------------------------------------------------------

    if analysis_type == "SERVICE_RANKING":

        if "SERVICE" not in dimensions:
            raise ValueError(
                "SERVICE_RANKING analysis requires SERVICE dimension."
            )

        ranking_kpis = {
            "REVENUE_RANK",
            "VOLUME_RANK",
        }

        if not ranking_kpis.intersection(kpis):
            raise ValueError(
                "SERVICE_RANKING requires at least one ranking KPI."
            )

    # ------------------------------------------------------------
    # REVENUE_CONCENTRATION
    # ------------------------------------------------------------

    if analysis_type == "REVENUE_CONCENTRATION":

        if "SERVICE" not in dimensions:
            raise ValueError(
                "REVENUE_CONCENTRATION analysis requires SERVICE dimension."
            )

        if "REVENUE_SHARE" not in kpis:
            raise ValueError(
                "REVENUE_CONCENTRATION requires REVENUE_SHARE KPI."
            )

# ================================================================
# MAIN VALIDATION FUNCTION
# ================================================================

def validate_analysis_plan(plan: dict) -> None:

    validate_required_fields(plan)
    validate_business_question(plan)
    validate_analysis_type(plan)
    validate_dimensions(plan)
    validate_kpis(plan)
    validate_top_n(plan)
    validate_plan_consistency(plan)


# ================================================================
# CLI
# ================================================================
if __name__ == "__main__":

    print()
    print("=" * 70)
    print("WEEK 10 - ANALYSIS PLAN VALIDATOR")
    print("=" * 70)

    try:

        print()
        print("[1/3] Loading analysis plan...")

        plan = load_analysis_plan()

        print("Analysis plan loaded successfully.")

        print()
        print("[2/3] Validating analysis plan...")

        print("  [1/6] Checking required fields...")
        validate_required_fields(plan)
        print("        PASS")

        print("  [2/6] Checking business question...")
        validate_business_question(plan)
        print("        PASS")

        print("  [3/6] Checking analysis type...")
        validate_analysis_type(plan)
        print("        PASS")

        print("  [4/6] Checking dimensions...")
        validate_dimensions(plan)
        print("        PASS")

        print("  [5/6] Checking KPIs...")
        validate_kpis(plan)
        print("        PASS")

        print("  [6/6] Checking plan consistency...")
        validate_top_n(plan)
        validate_plan_consistency(plan)
        print("        PASS")

        print()
        print("=" * 70)
        print("ANALYSIS PLAN VALIDATION PASSED")
        print("=" * 70)

    except Exception as error:

        print()
        print("=" * 70)
        print("ANALYSIS PLAN VALIDATION FAILED")
        print("=" * 70)

        print()
        print(f"Error: {error}")

        raise