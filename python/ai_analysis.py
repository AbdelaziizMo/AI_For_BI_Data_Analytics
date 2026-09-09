
from pathlib import Path
import json

from google import genai

from src.config import GEMINI_API_KEY
from python.data_loader import load_data
from python.analysis import analyze_data


# ================================================================
# WEEK 10 - AI FOR BI & DATA ANALYTICS
# AI-Generated Business Analysis
# ================================================================

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_NAME = "gemini-3.6-flash"

PROMPT_FILE = BASE_DIR / "prompts" / "prompts.md"
OUTPUT_DIR = BASE_DIR / "output"
AI_REPORT_FILE = OUTPUT_DIR / "ai_business_report.md"


# ================================================================
# GEMINI CLIENT
# ================================================================

def get_gemini_client():
    """Create and return a Gemini client."""

    if not GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY is not configured."
        )

    return genai.Client(
        api_key=GEMINI_API_KEY
    )


# ================================================================
# PROMPT LOADING
# ================================================================

def load_prompt_template():
    """Load the AI analysis prompt template."""

    if not PROMPT_FILE.exists():
        raise FileNotFoundError(
            f"Prompt file not found: {PROMPT_FILE}"
        )

    return PROMPT_FILE.read_text(
        encoding="utf-8"
    )


# ================================================================
# PREPARE ANALYSIS DATA
# ================================================================

def prepare_ai_input(results):
    """
    Convert analysis results into a JSON-serializable structure
    that can be sent to Gemini.
    """

    prepared_data = {}

    for key, value in results.items():

        if hasattr(value, "to_dict"):
            prepared_data[key] = value.to_dict(
                orient="records"
            )

        elif hasattr(value, "item"):
            prepared_data[key] = value.item()

        elif isinstance(value, dict):
            prepared_data[key] = value

        elif isinstance(value, (list, tuple)):
            prepared_data[key] = list(value)

        else:
            prepared_data[key] = value

    return prepared_data


# ================================================================
# BUILD AI PROMPT
# ================================================================

def build_analysis_prompt(
    template,
    analysis_data
):
    """
    Combine the prompt template with the calculated
    business analysis results.
    """

    analysis_json = json.dumps(
        analysis_data,
        indent=2,
        default=str,
        ensure_ascii=False,
    )

    task = """
TASK:

Generate a professional Business Intelligence report based
ONLY on the supplied analysis results.

Important analytical rules:

1. Do not invent facts, business processes, causes, customer
   behavior, accounting practices, technical architecture,
   operational events, partner activity, or organizational
   context.

2. Do not claim causation unless it is directly supported by
   the supplied data.

3. Clearly distinguish between:
   - FACT
   - INTERPRETATION
   - HYPOTHESIS

4. When discussing a pattern, use:

   OBSERVATION
   ->
   BUSINESS INTERPRETATION
   ->
   LIMITATION

5. Extreme percentage growth must always be interpreted
   together with the previous-day baseline and absolute change.

6. Prioritize absolute business impact over very large
   percentage changes caused by small baselines.

7. Keep revenue analysis and transaction-volume analysis
   separate.

8. Do not interpret transaction volume as customer engagement,
   retention, or customer count unless such data is explicitly
   provided.

9. Do not infer profitability, costs, margins, infrastructure
   usage, operational overhead, or financial health because
   those metrics are not provided.

10. Do not assume that revenue spikes are caused by:
    - batch processing
    - institutional settlement
    - accounting adjustments
    - clearing
    - corporate transfers
    - campaigns
    - partner activity
    - system events

11. If a cause cannot be established from the data, explicitly
    state that the cause requires further investigation.

12. Do not invent technical root causes for NULL values,
    corrupted text, encoding problems, or other data-quality
    issues.

13. Risk language must remain conservative.

    Prefer:
    - creates dependency risk
    - warrants monitoring
    - may increase exposure
    - could affect performance
    - requires further investigation

    Avoid unsupported claims such as:
    - will cause
    - will eliminate
    - will paralyze
    - guarantees
    - proves
    - confirms root cause

14. Recommendations must follow:

    OBSERVED PATTERN
    ->
    BUSINESS IMPLICATION
    ->
    RECOMMENDED ACTION

15. The analysis covers only the supplied observation period.
    Do not describe patterns as long-term, permanent, structural,
    sustainable, or recurring beyond the available data.

16. Prioritize:

    Evidence > Interpretation > Hypothesis

17. Answer the original business question directly:

    "Which services generate the highest revenue and transaction
    volume, and how does their performance change over time?"

REPORT STRUCTURE:

# Business Intelligence Report: Transaction Dataset Analysis

## EXECUTIVE SUMMARY

## KEY BUSINESS FINDINGS

## REVENUE ANALYSIS

## TRANSACTION VOLUME ANALYSIS

## GROWTH AND DECLINE ANALYSIS

## DATA QUALITY OBSERVATIONS

## BUSINESS RISKS

## RECOMMENDATIONS

Before finalizing the report, perform an internal quality check:

- Are all numerical values supported by the provided data?
- Are percentage calculations consistent with the supplied metrics?
- Are revenue and volume clearly separated?
- Are extreme growth percentages interpreted using their baselines?
- Are unsupported causal explanations avoided?
- Are customer behavior assumptions avoided?
- Are technical root causes avoided?
- Are profitability and cost assumptions avoided?
- Are recommendations tied to observed evidence?
- Is the six-day observation-window limitation clearly respected?

Return only the final professional BI report.
"""

    final_prompt = f"""
{template}

{task}

============================================================
SUPPLIED BUSINESS ANALYSIS DATA
============================================================

{analysis_json}
"""

    return final_prompt


# ================================================================
# GENERATE AI ANALYSIS
# ================================================================

def generate_ai_analysis(prompt: str) -> str:
    """
    Send the business analysis prompt to Gemini using
    the Interactions API and return the generated response.
    """

    client = get_gemini_client()

    interaction = client.interactions.create(
        model=MODEL_NAME,
        input=prompt,
    )

    if not interaction.output_text:
        raise ValueError(
            "Gemini returned an empty response."
        )

    return interaction.output_text.strip()


# ================================================================
# SAVE AI REPORT
# ================================================================

def save_ai_report(report: str):
    """
    Save the generated AI business report as a Markdown file.
    """

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    AI_REPORT_FILE.write_text(
        report,
        encoding="utf-8",
    )

    return AI_REPORT_FILE


# ================================================================
# MAIN AI ANALYSIS PIPELINE
# ================================================================

def run_ai_analysis():
    """
    Execute the complete AI business analysis pipeline.
    """

    print("=" * 70)
    print("WEEK 10 - AI BUSINESS ANALYSIS")
    print("=" * 70)

    # ------------------------------------------------------------
    # STEP 1 - LOAD DATA
    # ------------------------------------------------------------

    print("\n[1/5] Loading data from Oracle...")

    df = load_data()

    print(
        f"Loaded {len(df):,} rows successfully."
    )

    # ------------------------------------------------------------
    # STEP 2 - BUSINESS ANALYSIS
    # ------------------------------------------------------------

    print("\n[2/5] Running business analysis...")

    results = analyze_data(df)

    print("Business analysis completed.")

    # ------------------------------------------------------------
    # STEP 3 - PREPARE AI INPUT
    # ------------------------------------------------------------

    print("\n[3/5] Preparing AI analysis input...")

    analysis_data = prepare_ai_input(
        results
    )

    print("AI input prepared.")

    # ------------------------------------------------------------
    # STEP 4 - GENERATE AI REPORT
    # ------------------------------------------------------------

    print("\n[4/5] Generating AI business report...")

    prompt_template = load_prompt_template()

    final_prompt = build_analysis_prompt(
        prompt_template,
        analysis_data,
    )

    ai_report = generate_ai_analysis(
        final_prompt
    )

    print("AI analysis completed.")

    # ------------------------------------------------------------
    # STEP 5 - SAVE REPORT
    # ------------------------------------------------------------

    print("\n[5/5] Saving AI business report...")

    report_path = save_ai_report(
        ai_report
    )

    print(
        f"AI report saved successfully:\n"
        f"{report_path}"
    )

    return ai_report


# ================================================================
# SCRIPT ENTRY POINT
# ================================================================

if __name__ == "__main__":

    try:

        report = run_ai_analysis()

        print("\n")
        print("=" * 70)
        print("AI-GENERATED BUSINESS REPORT")
        print("=" * 70)
        print("\n")

        print(report)

        print("\n")
        print("=" * 70)
        print("AI BUSINESS ANALYSIS COMPLETED")
        print("=" * 70)

    except Exception as error:

        print("\n")
        print("=" * 70)
        print("ERROR")
        print("=" * 70)

        print(error)

        raise
