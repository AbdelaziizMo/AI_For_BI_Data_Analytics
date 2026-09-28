import json
import time
from pathlib import Path

from google import genai

from src.config import GEMINI_API_KEY, OUTPUT_DIR


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

MODEL_NAME = "gemini-3.6-flash"

PROMPT_FILE = (
    Path(__file__).resolve().parent.parent
    / "prompts"
    / "planner_prompt.md"
)

OUTPUT_FILE = OUTPUT_DIR / "analysis_plan.json"


# ---------------------------------------------------------
# Allowed catalog
# ---------------------------------------------------------

ALLOWED_DIMENSIONS = {
    "SERVICE",
    "DATE",
}

ALLOWED_KPIS = {
    "TOTAL_REVENUE",
    "TRANSACTION_VOLUME",
    "AVERAGE_TRANSACTION_VALUE",
    "REVENUE_SHARE",
    "VOLUME_SHARE",
    "REVENUE_RANK",
    "VOLUME_RANK",
    "DAILY_REVENUE",
    "DAILY_VOLUME",
    "REVENUE_GROWTH",
    "VOLUME_GROWTH",
    "REVENUE_CONCENTRATION",
}

ALLOWED_ANALYSIS_TYPES = {
    "SERVICE_PERFORMANCE",
    "TIME_TREND",
    "SERVICE_TREND",
    "REVENUE_CONCENTRATION",
}


# ---------------------------------------------------------
# Prompt loader
# ---------------------------------------------------------

def load_planner_prompt():
    """Load planner instructions from planner_prompt.md."""

    if not PROMPT_FILE.exists():
        raise FileNotFoundError(
            f"Planner prompt not found: {PROMPT_FILE}"
        )

    return PROMPT_FILE.read_text(
        encoding="utf-8"
    )


# ---------------------------------------------------------
# Planner validation
# ---------------------------------------------------------

def validate_analysis_plan(plan):
    """
    Validate Gemini's analysis plan against
    the approved analytical catalog.

    Returns:
        True if the plan is valid.

    Raises:
        ValueError if the plan is invalid.
    """

    if not isinstance(plan, dict):
        raise ValueError(
            "Analysis plan must be a JSON object."
        )

    required_fields = {
        "business_question",
        "analysis_type",
        "dimensions",
        "kpis",
        "top_n",
    }

    missing_fields = (
        required_fields - plan.keys()
    )

    if missing_fields:
        raise ValueError(
            "Missing required fields: "
            + ", ".join(
                sorted(missing_fields)
            )
        )

    if not isinstance(
        plan["business_question"],
        str,
    ):
        raise ValueError(
            "business_question must be a string."
        )

    if not plan["business_question"].strip():
        raise ValueError(
            "business_question cannot be empty."
        )

    if (
        plan["analysis_type"]
        not in ALLOWED_ANALYSIS_TYPES
    ):
        raise ValueError(
            "Invalid analysis_type: "
            f"{plan['analysis_type']}"
        )

    if not isinstance(
        plan["dimensions"],
        list,
    ):
        raise ValueError(
            "dimensions must be a list."
        )

    if not isinstance(
        plan["kpis"],
        list,
    ):
        raise ValueError(
            "kpis must be a list."
        )

    invalid_dimensions = (
        set(plan["dimensions"])
        - ALLOWED_DIMENSIONS
    )

    if invalid_dimensions:
        raise ValueError(
            "Invalid dimensions: "
            + ", ".join(
                sorted(invalid_dimensions)
            )
        )

    invalid_kpis = (
        set(plan["kpis"])
        - ALLOWED_KPIS
    )

    if invalid_kpis:
        raise ValueError(
            "Invalid KPIs: "
            + ", ".join(
                sorted(invalid_kpis)
            )
        )

    if not isinstance(
        plan["top_n"],
        int,
    ):
        raise ValueError(
            "top_n must be an integer."
        )

    if not 1 <= plan["top_n"] <= 50:
        raise ValueError(
            "top_n must be between 1 and 50."
        )

    return True


# ---------------------------------------------------------
# Gemini request with retry
# ---------------------------------------------------------

def generate_with_retry(
    client,
    model,
    prompt,
    config,
    max_retries=4,
):
    """
    Generate Gemini content with controlled retry behavior.

    Retry policy:

    - 503 / UNAVAILABLE:
        Retry with exponential backoff.

    - 429 / RESOURCE_EXHAUSTED:
        Stop immediately.

    - Other errors:
        Stop immediately.
    """

    for attempt in range(max_retries):

        try:

            print(
                "\nGemini request attempt "
                f"{attempt + 1}/{max_retries}..."
            )

            response = (
                client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=config,
                )
            )

            print(
                "Gemini response received."
            )

            return response

        except Exception as exc:

            error_message = str(exc)

            # -------------------------------------------------
            # QUOTA EXCEEDED
            # -------------------------------------------------

            is_quota_error = (
                "429" in error_message
                or "RESOURCE_EXHAUSTED"
                in error_message
            )

            if is_quota_error:

                print(
                    "\nGemini quota exceeded."
                )

                print(
                    "Stopping immediately without retry."
                )

                print(
                    "Please wait for the quota to reset "
                    "or check your Gemini API plan/billing."
                )

                raise

            # -------------------------------------------------
            # TEMPORARY SERVICE ERROR
            # -------------------------------------------------

            is_service_unavailable = (
                "503" in error_message
                or "UNAVAILABLE" in error_message
            )

            if is_service_unavailable:

                if attempt == max_retries - 1:

                    print(
                        "\nGemini request failed after "
                        f"{max_retries} attempts."
                    )

                    raise

                wait_seconds = 2 ** attempt

                print(
                    "\nGemini service is temporarily unavailable."
                )

                print(
                    f"Retrying in {wait_seconds} seconds..."
                )

                time.sleep(
                    wait_seconds
                )

                continue

            # -------------------------------------------------
            # UNKNOWN / NON-RETRYABLE ERROR
            # -------------------------------------------------

            raise


# ---------------------------------------------------------
# Gemini Planner
# ---------------------------------------------------------

def create_analysis_plan(
    business_question
):
    """
    Send the business question to Gemini
    and create a validated analysis plan.
    """

    if not GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY is not configured."
        )

    if (
        not business_question
        or not business_question.strip()
    ):
        raise ValueError(
            "Business question cannot be empty."
        )

    prompt = load_planner_prompt()

    client = genai.Client(
        api_key=GEMINI_API_KEY
    )

    full_prompt = f"""
{prompt}

Business Question:
{business_question}

Return only the required JSON object.
"""

    response = generate_with_retry(
        client=client,
        model=MODEL_NAME,
        prompt=full_prompt,
        config={
            "temperature": 0,
            "response_mime_type": "application/json",
        },
    )

    if not response.text:
        raise ValueError(
            "Gemini returned an empty response."
        )

    try:

        plan = json.loads(
            response.text
        )

    except json.JSONDecodeError as exc:

        raise ValueError(
            "Gemini returned invalid JSON."
        ) from exc

    # -----------------------------------------------------
    # Validate the plan before returning it
    # -----------------------------------------------------

    validate_analysis_plan(
        plan
    )

    # -----------------------------------------------------
    # Save the plan
    # -----------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            plan,
            indent=4,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return plan


# ---------------------------------------------------------
# CLI
# ---------------------------------------------------------

if __name__ == "__main__":

    print("=" * 70)
    print(
        "AI BUSINESS QUESTION PLANNER"
    )
    print("=" * 70)

    business_question = input(
        "\nEnter your business question:\n> "
    ).strip()

    try:

        plan = create_analysis_plan(
            business_question
        )

        print(
            "\n"
            + "=" * 70
        )

        print(
            "AI ANALYSIS PLAN"
        )

        print(
            "=" * 70
        )

        print(
            json.dumps(
                plan,
                indent=4,
                ensure_ascii=False,
            )
        )

        print(
            "=" * 70
        )

        print(
            f"Saved to: {OUTPUT_FILE}"
        )

    except Exception as exc:

        print(
            "\n"
            + "=" * 70
        )

        print(
            "PLANNER ERROR"
        )

        print(
            "=" * 70
        )

        print(
            str(exc)
        )