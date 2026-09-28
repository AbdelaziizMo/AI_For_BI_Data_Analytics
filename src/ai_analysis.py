import json
import time
from pathlib import Path
from typing import Optional, Dict, Any

from google import genai
from google.genai import types

from src.config import GEMINI_API_KEY, OUTPUT_DIR


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_NAME = "gemini-3.6-flash"

INPUT_FILE = OUTPUT_DIR / "sanitized_analysis.json"

PROMPT_FILE = (
    Path(__file__).resolve().parent.parent
    / "prompts"
    / "analyst_prompt.md"
)

REPORT_FILE = OUTPUT_DIR / "ai_business_report.md"


# ============================================================
# LOAD PROMPT
# ============================================================

def load_prompt():
    """Load the analyst prompt from the external markdown file."""

    if not PROMPT_FILE.exists():
        raise FileNotFoundError(
            f"Prompt file not found: {PROMPT_FILE}"
        )

    return PROMPT_FILE.read_text(
        encoding="utf-8"
    )


# ============================================================
# LOAD SANITIZED DATA
# ============================================================

def load_sanitized_data():
    """Load privacy-approved analytical data."""

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Sanitized data not found: {INPUT_FILE}"
        )

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


# ============================================================
# VALIDATE INPUT
# ============================================================

def validate_input(data):
    """Validate the sanitized AI input."""

    required_fields = {
        "business_question",
        "analysis_type",
        "dimensions",
        "kpis",
        "top_n",
        "date_range",
        "results",
    }

    missing_fields = (
        required_fields
        - set(data.keys())
    )

    if missing_fields:
        raise ValueError(
            "Missing required fields: "
            + ", ".join(
                sorted(missing_fields)
            )
        )

    if data.get("privacy_status") != "SANITIZED":
        raise ValueError(
            "Privacy validation failed. "
            "Only SANITIZED data can be sent to Gemini."
        )


# ============================================================
# BUILD FOLLOW-UP CONTEXT
# ============================================================

def build_follow_up_context(
    follow_up_context: Optional[Dict[str, Any]],
) -> str:
    """
    Build the previous-analysis context for a follow-up question.

    Only analytical metadata is included.

    Raw transaction data is never loaded here.
    """

    if not follow_up_context:
        return ""

    if not follow_up_context.get(
        "context_available"
    ):
        return ""

    if not follow_up_context.get(
        "is_follow_up"
    ):
        return ""

    previous_question = (
        follow_up_context.get(
            "previous_business_question"
        )
    )

    previous_analysis_id = (
        follow_up_context.get(
            "previous_analysis_id"
        )
    )

    previous_plan = (
        follow_up_context.get(
            "previous_analysis_plan"
        )
    )

    previous_report_path = (
        follow_up_context.get(
            "previous_report_path"
        )
    )

    return f"""
---

PREVIOUS ANALYSIS CONTEXT:

The current question is a follow-up to a previous BI analysis.

Previous Analysis ID:
{previous_analysis_id}

Previous Business Question:
{previous_question}

Previous Analysis Plan:
{json.dumps(
    previous_plan,
    ensure_ascii=False,
    indent=2,
)}

Previous Report Path:
{previous_report_path}

IMPORTANT FOLLOW-UP RULES:

1. Treat the previous analysis as context for the current question.
2. Resolve references such as "the spike", "the service",
   "the revenue", "it", or "that result" using the previous context.
3. Do not invent facts that are not present in the current
   sanitized analytical results or the previous context.
4. If the current sanitized results are sufficient to answer
   the question, use them directly.
5. If the available information is insufficient, clearly state
   what information is missing.
6. Do not request or expose raw transaction-level data.
"""


# ============================================================
# BUILD ANALYSIS REQUEST
# ============================================================

def build_analysis_request(
    prompt,
    data,
    follow_up_context=None,
):
    """
    Build the request sent to Gemini.

    Supports both:
        - New analysis
        - Follow-up analysis
    """

    follow_up_section = (
        build_follow_up_context(
            follow_up_context
        )
    )

    return f"""
{prompt}

---

CURRENT BUSINESS QUESTION:

{data["business_question"]}

---

ANALYSIS PLAN:

Analysis Type:
{data["analysis_type"]}

Dimensions:
{json.dumps(
    data["dimensions"],
    ensure_ascii=False,
)}

KPIs:
{json.dumps(
    data["kpis"],
    ensure_ascii=False,
)}

Top N:
{data["top_n"]}

Date Range:
{json.dumps(
    data["date_range"],
    ensure_ascii=False,
)}

{follow_up_section}

---

CURRENT SANITIZED AGGREGATED RESULTS:

{json.dumps(
    data["results"],
    ensure_ascii=False,
    indent=2,
)}

---

PRIVACY STATUS:

SANITIZED

The data above has passed the privacy validation layer.

Do not assume access to raw transaction-level data.

---

Produce the final BI analysis report now.
"""


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
    Generate Gemini response with controlled retry handling.

    429 / RESOURCE_EXHAUSTED:
        Stop immediately.
        Do not retry quota errors.

    503 / UNAVAILABLE:
        Retry with exponential backoff.

    Other errors:
        Stop immediately.
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
            )

            print(
                "Gemini response received."
            )

            return response

        except Exception as exc:

            error_message = str(exc)

            # ------------------------------------------------
            # QUOTA ERROR
            # ------------------------------------------------

            is_quota_error = (
                "429" in error_message
                or "RESOURCE_EXHAUSTED" in error_message
            )

            if is_quota_error:

                print()
                print(
                    "Gemini quota exceeded."
                )

                print(
                    "Stopping immediately without retry."
                )

                print(
                    "Please wait for the quota to reset "
                    "or check your Gemini API plan/billing."
                )

                raise

            # ------------------------------------------------
            # TEMPORARY SERVICE ERROR
            # ------------------------------------------------

            is_service_unavailable = (
                "503" in error_message
                or "UNAVAILABLE" in error_message
            )

            if is_service_unavailable:

                if attempt == max_retries - 1:

                    print()
                    print(
                        "Gemini service remained unavailable "
                        f"after {max_retries} attempts."
                    )

                    raise

                wait_seconds = 2 ** attempt

                print()
                print(
                    "Gemini service is temporarily unavailable."
                )

                print(
                    f"Retrying in {wait_seconds} seconds..."
                )

                time.sleep(
                    wait_seconds
                )

                continue

            # ------------------------------------------------
            # UNKNOWN ERROR
            # ------------------------------------------------

            raise


# ============================================================
# GENERATE ANALYSIS
# ============================================================

def generate_analysis(
    follow_up_context=None,
):
    """
    Generate the business analysis using Gemini.

    follow_up_context is optional so the existing pipeline
    continues to work unchanged.
    """

    prompt = load_prompt()

    data = load_sanitized_data()

    validate_input(data)

    # --------------------------------------------------------
    # Gemini client
    #
    # attempts=1 disables SDK-level automatic retries.
    # Application-level retry logic is handled explicitly
    # by generate_with_retry().
    # --------------------------------------------------------

    client = genai.Client(
        api_key=GEMINI_API_KEY,
        http_options=types.HttpOptions(
            retry_options=types.HttpRetryOptions(
                attempts=1
            )
        )
    )

    request = build_analysis_request(
        prompt=prompt,
        data=data,
        follow_up_context=follow_up_context,
    )

    response = generate_with_retry(
        client=client,
        model=MODEL_NAME,
        prompt=request,
    )

    if not response.text:
        raise ValueError(
            "Gemini returned an empty response."
        )

    return response.text


# ============================================================
# SAVE REPORT
# ============================================================

def save_report(report):
    """Save the AI-generated business report."""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT_FILE.write_text(
        report,
        encoding="utf-8",
    )

    print(
        f"Report saved to: {REPORT_FILE}"
    )


# ============================================================
# MAIN
# ============================================================

def main(
    follow_up_context=None,
):
    print()
    print("=" * 60)
    print("AI BI ANALYST")
    print("=" * 60)

    try:

        print()
        print("[1/3] Loading sanitized data...")

        report = generate_analysis(
            follow_up_context=follow_up_context
        )

        print(
            "Sanitized data loaded successfully."
        )

        if follow_up_context:
            if follow_up_context.get(
                "is_follow_up"
            ):
                print(
                    "Follow-up context detected."
                )

        print()
        print("[2/3] Generating Gemini analysis...")

        save_report(report)

        print()
        print("[3/3] Analysis completed.")

        print()
        print("=" * 60)
        print("GEMINI ANALYSIS COMPLETED SUCCESSFULLY")
        print("=" * 60)

        return report

    except Exception as error:

        print()
        print("ERROR:")
        print(error)

        raise


# ============================================================
# STANDALONE EXECUTION
# ============================================================

if __name__ == "__main__":
    main()