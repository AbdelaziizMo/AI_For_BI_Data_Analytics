import json
import logging
import time
import traceback
from pathlib import Path

from google import genai
from google.genai import types

from src.config import GEMINI_API_KEY


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_NAME = "gemini-3.6-flash"

BASE_DIR = Path(__file__).resolve().parent.parent

PLAN_FILE = BASE_DIR / "output" / "analysis_plan.json"
DATA_FILE = BASE_DIR / "output" / "sanitized_analysis.json"
PROMPT_FILE = BASE_DIR / "prompts" / "visualization_prompt.md"
OUTPUT_FILE = BASE_DIR / "output" / "visualization_plan.json"

logger = logging.getLogger(__name__)


# ============================================================
# FILE HELPERS
# ============================================================

def load_json(file_path: Path):
    """Load JSON data from a file."""

    if not file_path.exists():
        raise FileNotFoundError(
            f"Required file not found: {file_path}"
        )

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def load_prompt(file_path: Path):
    """Load visualization prompt."""

    if not file_path.exists():
        raise FileNotFoundError(
            f"Prompt file not found: {file_path}"
        )

    return file_path.read_text(encoding="utf-8")


# ============================================================
# DATA EXTRACTION
# ============================================================

def extract_rows(sanitized_data):
    """
    Extract analytical rows from sanitized_analysis.json.
    """

    if not isinstance(sanitized_data, dict):
        raise ValueError(
            "Sanitized analysis must be a JSON object."
        )

    if "results" not in sanitized_data:
        raise ValueError(
            "Sanitized analysis JSON does not contain "
            "the required 'results' field."
        )

    rows = sanitized_data["results"]

    if not isinstance(rows, list):
        raise ValueError(
            "Sanitized analysis 'results' must be a list."
        )

    if not rows:
        raise ValueError(
            "Sanitized analytical results contain no rows."
        )

    if not isinstance(rows[0], dict):
        raise ValueError(
            "Each sanitized analytical result must be "
            "a JSON object."
        )

    return rows


# ============================================================
# INPUT PREPARATION
# ============================================================

def prepare_visualization_input(
    analysis_plan,
    sanitized_data,
):
    """
    Prepare sanitized analytical input for Gemini.

    Only aggregated analytical data is provided.
    """

    if not isinstance(analysis_plan, dict):
        raise ValueError(
            "Analysis plan must be a JSON object."
        )

    if not isinstance(sanitized_data, dict):
        raise ValueError(
            "Sanitized analysis must be a JSON object."
        )

    rows = extract_rows(sanitized_data)

    available_fields = list(rows[0].keys())

    sanitized_metadata = {
        "business_question": sanitized_data.get(
            "business_question"
        ),
        "analysis_type": sanitized_data.get(
            "analysis_type"
        ),
        "dimensions": sanitized_data.get(
            "dimensions",
            []
        ),
        "kpis": sanitized_data.get(
            "kpis",
            []
        ),
        "top_n": sanitized_data.get(
            "top_n"
        ),
        "date_range": sanitized_data.get(
            "date_range"
        ),
        "row_count": sanitized_data.get(
            "row_count",
            len(rows)
        ),
        "privacy_status": sanitized_data.get(
            "privacy_status"
        ),
    }

    payload = {
        "analysis_plan": analysis_plan,
        "sanitized_metadata": sanitized_metadata,
        "available_fields": available_fields,
        "sanitized_data": rows,
    }

    return payload


# ============================================================
# GEMINI RETRY HELPER
# ============================================================

def generate_with_retry(
    client,
    model,
    prompt,
    max_retries=4,
):
    """
    Generate Gemini response with retry handling
    for temporary 429/503 errors.
    """

    for attempt in range(max_retries):

        try:

            print(
                f"\nGemini request attempt "
                f"{attempt + 1}/{max_retries}..."
            )

            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    response_mime_type="application/json",
                ),
            )

            print(
                "Gemini response received."
            )

            return response

        except Exception as exc:

            error_message = str(exc)

            is_temporary_error = (
                "503" in error_message
                or "UNAVAILABLE" in error_message
                or "429" in error_message
                or "RESOURCE_EXHAUSTED" in error_message
            )

            if not is_temporary_error:
                raise

            if attempt == max_retries - 1:

                print(
                    f"\nGemini request failed after "
                    f"{max_retries} attempts."
                )

                raise

            wait_seconds = 2 ** attempt

            print(
                "\nGemini is temporarily unavailable."
            )

            print(
                f"Retrying in "
                f"{wait_seconds} seconds..."
            )

            time.sleep(wait_seconds)


# ============================================================
# AI VISUALIZATION PLANNER
# ============================================================

def generate_visualization_plan():
    """
    Generate a dynamic visualization plan using Gemini.

    The planner is constrained by the actual sanitized
    fields and row count.
    """

    logger.info(
        "Loading analysis plan..."
    )

    analysis_plan = load_json(
        PLAN_FILE
    )

    logger.info(
        "Loading sanitized analytical data..."
    )

    sanitized_data = load_json(
        DATA_FILE
    )

    logger.info(
        "Loading visualization prompt..."
    )

    prompt = load_prompt(
        PROMPT_FILE
    )

    # --------------------------------------------------------
    # Prepare sanitized input.
    # --------------------------------------------------------

    payload = prepare_visualization_input(
        analysis_plan,
        sanitized_data,
    )

    rows = payload["sanitized_data"]
    available_fields = payload["available_fields"]
    row_count = len(rows)

    # --------------------------------------------------------
    # Determine visualization constraints.
    # --------------------------------------------------------

    is_single_observation = row_count == 1

    if is_single_observation:

        visualization_constraints = """
SINGLE-OBSERVATION MODE:

The sanitized analytical result contains EXACTLY ONE row.

Therefore:

1. Do NOT create a line chart.
2. Do NOT create a heatmap.
3. Do NOT create a service-level visualization.
4. Do NOT create a trend chart requiring multiple observations.
5. Do NOT use a series field.
6. Do NOT invent previous dates or baseline values.
7. Do NOT invent service fields.
8. Create at most ONE visualization.
9. Prefer a bar chart representing the single observed KPI.
10. The x-axis must use an actual available categorical/date field.
11. The y-axis must use an actual available numeric KPI.
12. The visualization must represent only the supplied observation.
13. For the current revenue-spike analysis, the preferred
    visualization is:

    DATE → DAILY_REVENUE

    with the observed date as the category and daily revenue
    as the value.

14. REVENUE_GROWTH may be mentioned in the reason/title
    only if supported by the supplied data, but do not invent
    a second observation or comparison point.
"""
    else:

        visualization_constraints = """
MULTI-OBSERVATION MODE:

The sanitized analytical result contains multiple rows.

Choose visualizations that match the actual dimensions,
KPIs, and row structure.

Use only supplied fields.

Do not invent service-level or transaction-level dimensions.
Do not create visualizations that require fields that are
not present.
"""

    # --------------------------------------------------------
    # Build AI request.
    # --------------------------------------------------------

    request = f"""
{prompt}

============================================================
ANALYSIS PLAN
============================================================

{json.dumps(
    payload["analysis_plan"],
    indent=4,
    ensure_ascii=False,
)}

============================================================
SANITIZED ANALYSIS METADATA
============================================================

{json.dumps(
    payload["sanitized_metadata"],
    indent=4,
    ensure_ascii=False,
)}

============================================================
AVAILABLE SANITIZED FIELDS
============================================================

{json.dumps(
    payload["available_fields"],
    indent=4,
    ensure_ascii=False,
)}

============================================================
ROW COUNT
============================================================

{row_count}

============================================================
SANITIZED ANALYTICAL DATA
============================================================

{json.dumps(
    payload["sanitized_data"],
    indent=4,
    ensure_ascii=False,
)}

============================================================
VISUALIZATION CONSTRAINTS
============================================================

{visualization_constraints}

============================================================
STRICT DATA RULES
============================================================

Use ONLY the supplied sanitized analytical data.

Do not invent fields.

Do not invent metrics.

Do not invent dates.

Do not invent service IDs.

Do not invent service names.

Do not invent relationships.

Do not request raw transaction data.

Every x field must exist in the available sanitized fields.

Every y field must exist in the available sanitized fields.

Every series field, if used, must exist in the available
sanitized fields.

Every label field, if used, must exist in the available
sanitized fields.

Do not use:

- transaction_date if it is not available
- service_id if it is not available
- service_name if it is not available
- volume if it is not available
- transaction_count if it is not available

The visualization plan must describe the actual result,
not an earlier analysis.

Return ONLY valid JSON using this structure:

{{
    "visualizations": [
        {{
            "type": "bar",
            "title": "string",
            "x": "available_field",
            "y": "available_numeric_field",
            "reason": "string"
        }}
    ]
}}
"""

    logger.info(
        "Sending visualization planning request to Gemini..."
    )

    client = genai.Client(
        api_key=GEMINI_API_KEY
    )

    response = generate_with_retry(
        client=client,
        model=MODEL_NAME,
        prompt=request,
    )

    if not response.text:

        raise ValueError(
            "Gemini returned an empty visualization plan."
        )

    # --------------------------------------------------------
    # Parse JSON response.
    # --------------------------------------------------------

    try:

        visualization_plan = json.loads(
            response.text
        )

    except json.JSONDecodeError as exc:

        logger.error(
            "Gemini returned invalid JSON."
        )

        logger.error(
            response.text
        )

        raise ValueError(
            "Gemini returned invalid JSON "
            "for visualization plan."
        ) from exc

    return visualization_plan


# ============================================================
# BASIC VALIDATION
# ============================================================

def validate_visualization_plan(
    visualization_plan,
    available_fields,
    rows,
):
    """
    Perform structural and semantic validation.

    Validation is intentionally strict because the
    visualization plan must reflect the actual sanitized data.
    """

    if not isinstance(
        visualization_plan,
        dict,
    ):

        raise ValueError(
            "Visualization plan must be a JSON object."
        )

    visualizations = visualization_plan.get(
        "visualizations"
    )

    if not isinstance(
        visualizations,
        list,
    ):

        raise ValueError(
            "'visualizations' must be a list."
        )

    if not visualizations:

        raise ValueError(
            "Visualization plan contains no visualizations."
        )

    row_count = len(rows)

    # --------------------------------------------------------
    # Single-observation semantic validation.
    # --------------------------------------------------------

    if row_count == 1:

        if len(visualizations) > 1:

            raise ValueError(
                "Single-observation data may contain "
                "at most one visualization."
            )

    # --------------------------------------------------------
    # Validate every visualization.
    # --------------------------------------------------------

    for index, visualization in enumerate(
        visualizations,
        start=1,
    ):

        if not isinstance(
            visualization,
            dict,
        ):

            raise ValueError(
                f"Visualization #{index} must be an object."
            )

        required_fields = [
            "type",
            "title",
            "x",
            "y",
            "reason",
        ]

        for field in required_fields:

            if field not in visualization:

                raise ValueError(
                    f"Visualization #{index} is missing "
                    f"required field: {field}"
                )

        # ----------------------------------------------------
        # Chart type.
        # ----------------------------------------------------

        chart_type = visualization["type"]

        if not isinstance(
            chart_type,
            str,
        ) or not chart_type.strip():

            raise ValueError(
                f"Visualization #{index} has "
                f"an invalid chart type."
            )

        allowed_chart_types = {
            "line",
            "bar",
            "horizontal_bar",
            "heatmap",
            "scatter",
            "pie",
        }

        if chart_type not in allowed_chart_types:

            raise ValueError(
                f"Visualization #{index} uses unsupported "
                f"chart type: {chart_type}"
            )

        # ----------------------------------------------------
        # Single-observation chart restrictions.
        # ----------------------------------------------------

        if row_count == 1:

            if chart_type in {
                "line",
                "heatmap",
                "scatter",
            }:

                raise ValueError(
                    f"Visualization #{index} uses '{chart_type}' "
                    f"with a single observation. "
                    f"Use a bar chart instead."
                )

            if "series" in visualization:

                raise ValueError(
                    f"Visualization #{index} must not use "
                    f"a series field with a single observation."
                )

        # ----------------------------------------------------
        # Title.
        # ----------------------------------------------------

        title = visualization["title"]

        if not isinstance(
            title,
            str,
        ) or not title.strip():

            raise ValueError(
                f"Visualization #{index} has "
                f"an invalid title."
            )

        # ----------------------------------------------------
        # Reason.
        # ----------------------------------------------------

        reason = visualization["reason"]

        if not isinstance(
            reason,
            str,
        ) or not reason.strip():

            raise ValueError(
                f"Visualization #{index} has "
                f"an invalid reason."
            )

        # ----------------------------------------------------
        # X field.
        # ----------------------------------------------------

        x_field = visualization["x"]

        if x_field not in available_fields:

            raise ValueError(
                f"Visualization #{index} references "
                f"unknown x field: {x_field}"
            )

        # ----------------------------------------------------
        # Y field.
        # ----------------------------------------------------

        y_field = visualization["y"]

        if y_field not in available_fields:

            raise ValueError(
                f"Visualization #{index} references "
                f"unknown y field: {y_field}"
            )

        # ----------------------------------------------------
        # Optional series field.
        # ----------------------------------------------------

        if "series" in visualization:

            series_field = visualization["series"]

            if series_field not in available_fields:

                raise ValueError(
                    f"Visualization #{index} references "
                    f"unknown series field: {series_field}"
                )

        # ----------------------------------------------------
        # Optional label field.
        # ----------------------------------------------------

        if "label" in visualization:

            label_field = visualization["label"]

            if label_field not in available_fields:

                raise ValueError(
                    f"Visualization #{index} references "
                    f"unknown label field: {label_field}"
                )


# ============================================================
# SAVE
# ============================================================

def save_visualization_plan(
    visualization_plan,
):
    """Save generated visualization plan."""

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            visualization_plan,
            file,
            indent=4,
            ensure_ascii=False,
        )

    logger.info(
        "Visualization plan saved to: %s",
        OUTPUT_FILE,
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("AI VISUALIZATION PLANNER")
    print("=" * 70)

    try:

        # ----------------------------------------------------
        # STEP 1
        # ----------------------------------------------------

        print(
            "\n[1/4] Loading analysis plan..."
        )

        analysis_plan = load_json(
            PLAN_FILE
        )

        # ----------------------------------------------------
        # STEP 2
        # ----------------------------------------------------

        print(
            "[2/4] Loading sanitized analytical data..."
        )

        sanitized_data = load_json(
            DATA_FILE
        )

        rows = extract_rows(
            sanitized_data
        )

        available_fields = list(
            rows[0].keys()
        )

        print(
            f"Loaded {len(rows)} sanitized rows."
        )

        print(
            f"Available fields: "
            f"{len(available_fields)}"
        )

        print(
            "Available fields:"
        )

        for field in available_fields:

            print(
                f"  - {field}"
            )

        print(
            "Privacy status: "
            f"{sanitized_data.get('privacy_status', 'UNKNOWN')}"
        )

        # ----------------------------------------------------
        # STEP 3
        # ----------------------------------------------------

        print(
            "\n[3/4] Generating visualization plan..."
        )

        visualization_plan = (
            generate_visualization_plan()
        )

        print(
            "Gemini visualization plan received."
        )

        print(
            "\nValidating visualization structure..."
        )

        validate_visualization_plan(
            visualization_plan,
            available_fields,
            rows,
        )

        print(
            "Visualization validation passed."
        )

        # ----------------------------------------------------
        # STEP 4
        # ----------------------------------------------------

        save_visualization_plan(
            visualization_plan
        )

        print(
            "\n[4/4] Visualization plan completed."
        )

        print(
            "\n" + "=" * 70
        )

        print(
            "VISUALIZATION PLANNER "
            "COMPLETED SUCCESSFULLY"
        )

        print(
            "=" * 70
        )

        print(
            f"\nSaved to: {OUTPUT_FILE}"
        )

        print(
            "\nGenerated visualizations:"
        )

        for index, visualization in enumerate(
            visualization_plan["visualizations"],
            start=1,
        ):

            print(
                f"{index}. "
                f"{visualization['type']} - "
                f"{visualization['title']}"
            )

    except Exception as error:

        print(
            "\n" + "=" * 70
        )

        print(
            "VISUALIZATION PLANNER FAILED"
        )

        print(
            "=" * 70
        )

        print(
            f"\nError Type: "
            f"{type(error).__name__}"
        )

        print(
            f"Error: {error}"
        )

        print(
            "\nFull traceback:"
        )

        traceback.print_exc()

        raise SystemExit(1)


if __name__ == "__main__":
    main()