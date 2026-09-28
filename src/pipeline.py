import json
import shutil
from pathlib import Path

from src.ai_planner import (
    create_analysis_plan,
    validate_analysis_plan,
)

from src.ai_sql_generator import generate_sql
from src.sql_validator import validate_generated_sql
from src.analysis_executor import main as execute_analysis
from src.privacy_guard import run_privacy_guard
from src.ai_analysis import main as run_ai_analysis
from src.ai_business_report_with_visuals import build_pdf

from src.context_manager import get_relevant_context
from src.follow_up_resolver import build_follow_up_context

from src.chat_history import (
    create_conversation,
    conversation_exists,
    get_conversation,
    add_message,
    add_analysis,
    update_analysis_report_path,
    update_conversation_title,
)

from src.visualization_engine import (
    generate_visualization_spec,
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

OUTPUT_DIR = BASE_DIR / "output"

ANALYSES_DIR = OUTPUT_DIR / "analyses"

REPORT_FILE = OUTPUT_DIR / "ai_business_report.md"

PDF_REPORT_PATH = (
    OUTPUT_DIR / "ai_business_report_final.pdf"
)

# Streamlit dashboard
STREAMLIT_DASHBOARD_URL = (
    "http://127.0.0.1:8501"
)


# ============================================================
# HELPERS
# ============================================================

def load_full_assistant_response(
    report_path: Path,
    fallback_report_path: Path | None = None,
) -> str:

    if report_path.exists():

        return report_path.read_text(
            encoding="utf-8"
        )

    if (
        fallback_report_path
        and fallback_report_path.exists()
    ):

        return fallback_report_path.read_text(
            encoding="utf-8"
        )

    return (
        "The analysis was completed, but the "
        "business report could not be loaded."
    )


def snapshot_analysis_artifacts(
    analysis_id: str,
) -> Path:

    analysis_dir = (
        ANALYSES_DIR
        / str(analysis_id)
    )

    analysis_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    artifact_files = [
        "analysis_plan.json",
        "validated_sql.json",
        "generated_sql.json",
        "aggregated_results.json",
        "sanitized_analysis.json",
        "ai_business_report.md",
        "visualization_spec.json",
    ]

    for filename in artifact_files:

        source = (
            OUTPUT_DIR
            / filename
        )

        destination = (
            analysis_dir
            / filename
        )

        if source.exists():

            shutil.copy2(
                source,
                destination,
            )

    return analysis_dir


def snapshot_pdf_report(
    analysis_id: str,
) -> Path | None:

    analysis_dir = (
        ANALYSES_DIR
        / str(analysis_id)
    )

    analysis_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not PDF_REPORT_PATH.exists():

        return None

    destination = (
        analysis_dir
        / "ai_business_report_final.pdf"
    )

    shutil.copy2(
        PDF_REPORT_PATH,
        destination,
    )

    return destination


def build_conversation_title(
    business_question: str,
) -> str:

    question = " ".join(
        business_question.strip().split()
    )

    if not question:

        return "BI Analysis"

    max_length = 70

    if len(question) <= max_length:

        return question

    return (
        question[:max_length].rstrip()
        + "..."
    )


def build_planner_question(
    business_question: str,
    previous_business_question: str | None = None,
    previous_analysis_plan: dict | None = None,
) -> str:

    if (
        not previous_business_question
        and not previous_analysis_plan
    ):

        return business_question

    context_parts = []

    if previous_business_question:

        context_parts.append(
            "Previous business question:\n"
            f"{previous_business_question}"
        )

    if previous_analysis_plan:

        context_parts.append(
            "Previous analysis plan:\n"
            f"{json.dumps(
                previous_analysis_plan,
                indent=2,
                ensure_ascii=False
            )}"
        )

    context_parts.append(
        "Current follow-up question:\n"
        f"{business_question}"
    )

    return "\n\n".join(
        context_parts
    )


def append_dashboard_link(
    assistant_response: str,
    dashboard_url: str,
) -> str:

    response = (
        assistant_response.rstrip()
    )

    dashboard_section = (
        "\n\n"
        "---\n\n"
        "### 📊 Interactive Dashboard\n\n"
        f"[Open Streamlit Dashboard]"
        f"({dashboard_url})\n\n"
        "The dashboard contains the visualizations "
        "and analysis history for this conversation."
    )

    return (
        response
        + dashboard_section
    )


# ============================================================
# MAIN PIPELINE
# ============================================================

def run_pipeline(
    business_question: str,
    conversation_id: str | None = None,
) -> dict:

    # --------------------------------------------------------
    # 1. Validate user input
    # --------------------------------------------------------

    if (
        not business_question
        or not business_question.strip()
    ):

        raise ValueError(
            "Business question cannot be empty."
        )

    business_question = (
        business_question.strip()
    )

    is_new_conversation = False

    # --------------------------------------------------------
    # 2. Load or create conversation
    # --------------------------------------------------------

    if conversation_id:

        if not conversation_exists(
            conversation_id
        ):

            raise ValueError(
                f"Conversation '{conversation_id}' "
                "does not exist."
            )

        conversation = get_conversation(
            conversation_id
        )

        if not conversation:

            raise ValueError(
                f"Could not load conversation "
                f"'{conversation_id}'."
            )

    else:

        conversation_id = create_conversation(
            title="New BI Analysis"
        )

        is_new_conversation = True

        conversation = get_conversation(
            conversation_id
        )

    # --------------------------------------------------------
    # 3. Follow-up context
    # --------------------------------------------------------

    previous_business_question = None

    previous_analysis_plan = None

    follow_up_context = None

    if (
        not is_new_conversation
        and conversation_id
    ):

        try:

            relevant_context = (
                get_relevant_context(
                    conversation_id=conversation_id,
                    current_question=business_question,
                )
            )

        except TypeError:

            relevant_context = (
                get_relevant_context(
                    conversation_id,
                    business_question,
                )
            )

        if relevant_context:

            follow_up_context = (
                build_follow_up_context(
                    business_question=business_question,
                    context=relevant_context,
                )
            )

            if isinstance(
                relevant_context,
                dict,
            ):

                previous_business_question = (
                    relevant_context.get(
                        "previous_business_question"
                    )
                    or relevant_context.get(
                        "business_question"
                    )
                )

                previous_analysis_plan = (
                    relevant_context.get(
                        "previous_analysis_plan"
                    )
                    or relevant_context.get(
                        "analysis_plan"
                    )
                )

    # --------------------------------------------------------
    # 4. Conversation title
    # --------------------------------------------------------

    if is_new_conversation:

        update_conversation_title(
            conversation_id,
            build_conversation_title(
                business_question
            ),
        )

    # --------------------------------------------------------
    # 5. Save user message
    # --------------------------------------------------------

    add_message(
        conversation_id=conversation_id,
        role="user",
        content=business_question,
    )

    # --------------------------------------------------------
    # 6. Build planner question
    # --------------------------------------------------------

    planner_question = (
        build_planner_question(
            business_question=business_question,
            previous_business_question=(
                previous_business_question
            ),
            previous_analysis_plan=(
                previous_analysis_plan
            ),
        )
    )

    if follow_up_context:

        if isinstance(
            follow_up_context,
            str,
        ):

            planner_question = (
                follow_up_context
            )

        elif isinstance(
            follow_up_context,
            dict,
        ):

            planner_question = json.dumps(
                follow_up_context,
                indent=2,
                ensure_ascii=False,
            )

    # --------------------------------------------------------
    # 7. Gemini Planner
    # --------------------------------------------------------

    analysis_plan = (
        create_analysis_plan(
            planner_question
        )
    )

    if not analysis_plan:

        raise RuntimeError(
            "The AI Planner did not return "
            "an analysis plan."
        )

    # --------------------------------------------------------
    # 8. Validate analysis plan
    # --------------------------------------------------------

    validate_analysis_plan(
        analysis_plan
    )

    # --------------------------------------------------------
    # 9. Create analysis record
    # --------------------------------------------------------

    analysis_id = add_analysis(
        conversation_id=conversation_id,
        business_question=business_question,
        analysis_plan=analysis_plan,
    )

    # --------------------------------------------------------
    # 10. Generate SQL
    # --------------------------------------------------------

    generated_sql = (
        generate_sql()
    )

    if not generated_sql:

        raise RuntimeError(
            "SQL generation failed."
        )

    # --------------------------------------------------------
    # 11. Validate SQL
    # --------------------------------------------------------

    validated_sql = (
        validate_generated_sql()
    )

    if not validated_sql:

        raise RuntimeError(
            "Generated SQL failed validation."
        )

    # --------------------------------------------------------
    # 12. Execute analysis
    # --------------------------------------------------------

    execute_analysis()

    # --------------------------------------------------------
    # 13. Privacy Guard
    # --------------------------------------------------------

    # --------------------------------------------------------
    # 13. Privacy Guard
    # --------------------------------------------------------

    run_privacy_guard()

    # --------------------------------------------------------
    # 13.1 Verify Privacy Guard output
    # --------------------------------------------------------
    #
    # Privacy Guard writes:
    #
    # output/sanitized_analysis.json
    #
    # It does not need to return the sanitized payload.
    # The pipeline verifies the actual file instead.
    # --------------------------------------------------------

    sanitized_source_path = (
        OUTPUT_DIR
        / "sanitized_analysis.json"
    )

    if not sanitized_source_path.exists():

        raise RuntimeError(
            "Privacy Guard completed, but "
            "output/sanitized_analysis.json "
            "was not found."
        )

    # --------------------------------------------------------
    # 13.2 Copy sanitized analysis to analysis folder
    # --------------------------------------------------------

    analysis_directory = (
        ANALYSES_DIR
        / str(analysis_id)
    )

    analysis_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    sanitized_analysis_path = (
        analysis_directory
        / "sanitized_analysis.json"
    )

    shutil.copy2(
        sanitized_source_path,
        sanitized_analysis_path,
    )


    # --------------------------------------------------------
    # 13.1 Verify Privacy Guard output
        # --------------------------------------------------------
        #
        # Privacy Guard writes:
        #
        # output/sanitized_analysis.json
        #
        # The visualization engine works from:
        #
        # output/analyses/<analysis_id>/
        #
        # Therefore we copy the freshly generated
        # sanitized file into the current analysis folder.
        # --------------------------------------------------------

    sanitized_source_path = (
        OUTPUT_DIR
        / "sanitized_analysis.json"
    )

    if not sanitized_source_path.exists():

        raise RuntimeError(
                "Privacy Guard completed, but "
                "output/sanitized_analysis.json "
                "was not found."
        )

    analysis_directory = (
        ANALYSES_DIR
        / str(analysis_id)
    )

    analysis_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    sanitized_analysis_path = (
        analysis_directory
        / "sanitized_analysis.json"
    )

    shutil.copy2(
        sanitized_source_path,
        sanitized_analysis_path,
    )

    # --------------------------------------------------------
    # 14. AI Business Analyst
    # --------------------------------------------------------

    run_ai_analysis()

    if not REPORT_FILE.exists():

        raise RuntimeError(
            "AI Business Analyst did not generate "
            "the business report."
        )

    # --------------------------------------------------------
    # 15. Snapshot analysis artifacts
    # --------------------------------------------------------

    analysis_directory = (
        snapshot_analysis_artifacts(
            analysis_id
        )
    )

    # --------------------------------------------------------
    # 16. Generate visualization specification
    # --------------------------------------------------------

    visualization_spec = (
        generate_visualization_spec(
            analysis_id
        )
    )

    if visualization_spec is None:

        visualization_spec = {}

    # --------------------------------------------------------
    # 17. Snapshot visualization specification
    # --------------------------------------------------------

    analysis_directory = (
        snapshot_analysis_artifacts(
            analysis_id
        )
    )

    # --------------------------------------------------------
    # 18. Build PDF
    # --------------------------------------------------------

    build_pdf()

    # --------------------------------------------------------
    # 19. Snapshot PDF
    # --------------------------------------------------------

    snapshot_pdf_report(
        analysis_id
    )

    # --------------------------------------------------------
    # 20. Load AI response
    # --------------------------------------------------------

    assistant_response = (
        load_full_assistant_response(
            REPORT_FILE,
            REPORT_FILE,
        )
    )

    # --------------------------------------------------------
    # 21. Build dashboard URL
    # --------------------------------------------------------

    dashboard_url = (
        f"{STREAMLIT_DASHBOARD_URL}"
        f"/?conversation_id={conversation_id}"
    )

    # --------------------------------------------------------
    # 22. Append dashboard link
    # --------------------------------------------------------

    assistant_response = (
        append_dashboard_link(
            assistant_response=assistant_response,
            dashboard_url=dashboard_url,
        )
    )

    # --------------------------------------------------------
    # 23. Update report path
    # --------------------------------------------------------

    update_analysis_report_path(
        analysis_id,
        str(REPORT_FILE),
    )

    # --------------------------------------------------------
    # 24. Save assistant response
    # --------------------------------------------------------

    add_message(
        conversation_id=conversation_id,
        role="assistant",
        content=assistant_response,
    )

    # --------------------------------------------------------
    # 25. Return result
    # --------------------------------------------------------

    return {
        "conversation_id": conversation_id,
        "analysis_id": analysis_id,
        "follow_up": bool(
            previous_business_question
            or previous_analysis_plan
        ),
        "report_path": str(
            REPORT_FILE
        ),
        "analysis_directory": str(
            analysis_directory
        ),
        "visualization_spec": (
            visualization_spec
        ),
        "dashboard_url": dashboard_url,
        "answer": assistant_response,
    }


# ============================================================
# CLI
# ============================================================

def main():

    print("=" * 70)

    print(
        "AI FOR BI DATA ANALYTICS PIPELINE"
    )

    print("=" * 70)

    business_question = input(
        "\nEnter your business question:\n> "
    ).strip()

    if not business_question:

        print(
            "Business question cannot be empty."
        )

        return

    conversation_id = input(
        "\nExisting conversation ID "
        "(press Enter for a new conversation):\n> "
    ).strip()

    if not conversation_id:

        conversation_id = None

    try:

        result = run_pipeline(
            business_question=business_question,
            conversation_id=conversation_id,
        )

        print(
            "\n"
            + "=" * 70
        )

        print(
            "PIPELINE COMPLETED"
        )

        print(
            "=" * 70
        )

        print(
            f"\nConversation ID:\n"
            f"{result['conversation_id']}"
        )

        print(
            f"\nAnalysis ID:\n"
            f"{result['analysis_id']}"
        )

        print(
            f"\nAnalysis Directory:\n"
            f"{result['analysis_directory']}"
        )

        print(
            f"\nStreamlit Dashboard:\n"
            f"{result['dashboard_url']}"
        )

        print(
            "\n"
            + "=" * 70
        )

    except Exception as exc:

        print(
            "\n"
            + "=" * 70
        )

        print(
            "PIPELINE FAILED"
        )

        print(
            "=" * 70
        )

        print(
            f"\nError:\n{exc}"
        )

        raise


if __name__ == "__main__":
    main()