from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

OUTPUT_DIR = BASE_DIR / "output"

ANALYSES_DIR = (
    OUTPUT_DIR / "analyses"
)


# ============================================================
# HELPERS
# ============================================================

def normalize_key(
    value: Any,
) -> str:
    return str(
        value
    ).strip().lower()


def question_contains(
    question: str,
    *words: str,
) -> bool:
    """
    Check whether the business question contains
    one or more target phrases.
    """

    q = normalize_key(
        question
    )

    return any(
        re.search(
            rf"\b{re.escape(normalize_key(word))}\b",
            q,
        )
        for word in words
    )


def find_column(
    rows: list[dict],
    *candidates: str,
) -> str | None:
    """
    Find an actual column name while handling
    different casing.
    """

    if not rows:
        return None

    mapping = {
        normalize_key(key): key
        for key in rows[0].keys()
    }

    for candidate in candidates:

        normalized_candidate = (
            normalize_key(candidate)
        )

        if normalized_candidate in mapping:

            return mapping[
                normalized_candidate
            ]

    return None


# ============================================================
# LOAD ANALYSIS
# ============================================================

def load_sanitized_analysis(
    analysis_id: str,
) -> dict:
    """
    Load the sanitized analysis belonging to
    one specific analysis.
    """

    path = (
        ANALYSES_DIR
        / str(analysis_id)
        / "sanitized_analysis.json"
    )

    if not path.exists():

        raise FileNotFoundError(
            "Missing sanitized analysis: "
            f"{path}"
        )

    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


# ============================================================
# VISUAL SELECTION
# ============================================================

def build_visualization_spec(
    analysis: dict,
) -> dict:
    """
    Build visualization specifications based only on
    the current sanitized analysis and current business question.

    No previous analysis is used.
    No global visualization plan is used.
    """

    analysis_id = analysis.get(
        "analysis_id"
    )

    question = analysis.get(
        "business_question",
        "",
    )

    analysis_type = normalize_key(
        analysis.get(
            "analysis_type",
            "",
        )
    )

    rows = analysis.get(
        "results",
        [],
    )

    # ========================================================
    # EMPTY DATA
    # ========================================================

    if not rows:

        return {
            "analysis_id": analysis_id,
            "business_question": question,
            "analysis_type": analysis_type,
            "visuals": [],
        }

    # ========================================================
    # DETECT COLUMNS
    # ========================================================

    date_column = find_column(
        rows,
        "date",
        "transaction_date",
        "trx_date",
        "day",
    )

    revenue_column = find_column(
        rows,
        "daily_revenue",
        "total_revenue",
        "revenue",
    )

    revenue_growth_column = find_column(
        rows,
        "revenue_growth",
    )

    revenue_share_column = find_column(
        rows,
        "revenue_share",
    )

    service_id_column = find_column(
        rows,
        "service_id",
    )

    service_name_column = find_column(
        rows,
        "service_name",
        "service",
        "name",
    )

    # ========================================================
    # VISUALS
    # ========================================================

    visuals: list[dict] = []

    # ========================================================
    # 1. REVENUE SPIKE / PEAK
    # ========================================================

    is_spike_question = question_contains(
        question,
        "biggest revenue spike",
        "largest revenue spike",
        "revenue spike",
        "revenue spikes",
        "peak revenue",
        "highest revenue",
        "largest spike",
        "biggest spike",
    )

    if (
        is_spike_question
        and date_column
        and revenue_column
    ):

        visuals.append(
            {
                "type": "daily_revenue_peak",
                "title": "Daily Revenue Trend",
                "x": date_column,
                "y": revenue_column,
                "highlight": "max",
            }
        )

    # ========================================================
    # 2. REVENUE TREND
    # ========================================================

    is_revenue_trend_question = question_contains(
        question,
        "revenue trend",
        "revenue trends",
        "trend",
        "over time",
        "daily revenue",
        "revenue performance",
        "revenue during",
    )

    if (
        is_revenue_trend_question
        and date_column
        and revenue_column
        and not is_spike_question
    ):

        visuals.append(
            {
                "type": "line",
                "title": "Revenue Trend",
                "x": date_column,
                "y": revenue_column,
            }
        )

    # ========================================================
    # 3. REVENUE GROWTH
    # ========================================================

    is_growth_question = question_contains(
        question,
        "growth",
        "increase",
        "decrease",
        "change",
        "growth rate",
        "percentage change",
    )

    if (
        is_growth_question
        and date_column
        and revenue_growth_column
    ):

        visuals.append(
            {
                "type": "line",
                "title": "Revenue Growth",
                "x": date_column,
                "y": revenue_growth_column,
            }
        )

    # ========================================================
    # 4. TOP SERVICES
    # ========================================================

    is_service_question = question_contains(
        question,
        "service",
        "services",
        "top service",
        "top services",
        "highest service",
        "service ranking",
        "rank",
        "ranking",
        "contribution",
    )

    service_category = (
        service_name_column
        or service_id_column
    )

    if (
        is_service_question
        and service_category
        and revenue_column
    ):

        visuals.append(
            {
                "type": "top_services",
                "title": "Top Services by Revenue",
                "category": service_category,
                "value": revenue_column,
            }
        )

    # ========================================================
    # 5. REVENUE SHARE
    # ========================================================

    is_share_question = question_contains(
        question,
        "share",
        "distribution",
        "contribution",
        "percentage of revenue",
        "revenue share",
    )

    if (
        is_share_question
        and revenue_share_column
        and service_category
    ):

        visuals.append(
            {
                "type": "revenue_share",
                "title": "Revenue Contribution by Service",
                "category": service_category,
                "value": revenue_share_column,
            }
        )

    # ========================================================
    # 6. FALLBACK
    # ========================================================

    if not visuals:

        if (
            date_column
            and revenue_column
        ):

            visuals.append(
                {
                    "type": "line",
                    "title": "Revenue Over Time",
                    "x": date_column,
                    "y": revenue_column,
                }
            )

        elif (
            service_category
            and revenue_column
        ):

            visuals.append(
                {
                    "type": "top_services",
                    "title": "Revenue by Service",
                    "category": service_category,
                    "value": revenue_column,
                }
            )

    # ========================================================
    # RESULT
    # ========================================================

    return {
        "analysis_id": analysis_id,
        "business_question": question,
        "analysis_type": analysis_type,
        "visuals": visuals,
    }


# ============================================================
# SAVE VISUALIZATION SPEC
# ============================================================

def generate_visualization_spec(
    analysis_id: str,
) -> dict:
    """
    Generate and save a visualization specification
    for exactly one analysis.
    """

    analysis_id = str(
        analysis_id
    )

    analysis = load_sanitized_analysis(
        analysis_id
    )

    analysis["analysis_id"] = analysis_id

    spec = build_visualization_spec(
        analysis
    )

    output_dir = (
        ANALYSES_DIR
        / analysis_id
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        output_dir
        / "visualization_spec.json"
    )

    output_path.write_text(
        json.dumps(
            spec,
            indent=4,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return spec


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":

    print(
        "Visualization Engine ready."
    )