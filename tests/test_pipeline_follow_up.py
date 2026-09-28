from src.context_manager import get_relevant_context
from src.follow_up_resolver import build_follow_up_context
from src.pipeline import build_planner_question


# ============================================================
# TEST CONFIGURATION
# ============================================================

TEST_CONVERSATION_ID = (
    "e20e6393-443b-4759-9477-6529463c3f7b"
)

FOLLOW_UP_QUESTION = (
    "What caused the biggest revenue spike?"
)


# ============================================================
# TEST
# ============================================================

def main():

    print("=" * 70)
    print("PIPELINE FOLLOW-UP CONTEXT TEST")
    print("=" * 70)

    # --------------------------------------------------------
    # Step 1: Load previous conversation context
    # --------------------------------------------------------

    print("\n[1] Loading previous conversation context")
    print("-" * 70)

    relevant_context = get_relevant_context(
        conversation_id=TEST_CONVERSATION_ID,
        message_limit=10,
    )

    if relevant_context is None:
        raise RuntimeError(
            "Conversation context not found."
        )

    print(
        "Previous conversation context loaded."
    )

    # --------------------------------------------------------
    # Step 2: Resolve follow-up
    # --------------------------------------------------------

    print("\n[2] Resolving follow-up question")
    print("-" * 70)

    follow_up_context = build_follow_up_context(
        current_question=FOLLOW_UP_QUESTION,
        relevant_context=relevant_context,
    )

    print(
        f"Is follow-up: "
        f"{follow_up_context['is_follow_up']}"
    )

    print(
        f"Previous Analysis ID: "
        f"{follow_up_context.get(
            'previous_analysis_id'
        )}"
    )

    # --------------------------------------------------------
    # Step 3: Validate follow-up
    # --------------------------------------------------------

    print("\n[3] Validating follow-up context")
    print("-" * 70)

    assert (
        follow_up_context["is_follow_up"]
        is True
    )

    assert (
        follow_up_context["context_available"]
        is True
    )

    assert (
        follow_up_context["previous_analysis_id"]
        == "d74398ea-103c-44cd-9cfd-036f6c33de0e"
    )

    print(
        "Follow-up context validation passed."
    )

    # --------------------------------------------------------
    # Step 4: Build planner question
    # --------------------------------------------------------

    print("\n[4] Building planner question")
    print("-" * 70)

    planner_question = build_planner_question(
        business_question=FOLLOW_UP_QUESTION,
        follow_up_context=follow_up_context,
    )

    print(
        planner_question
    )

    # --------------------------------------------------------
    # Step 5: Validate planner question
    # --------------------------------------------------------

    print("\n[5] Validating planner question")
    print("-" * 70)

    required_content = [
        "PREVIOUS BUSINESS QUESTION",
        "PREVIOUS ANALYSIS PLAN",
        "CURRENT FOLLOW-UP QUESTION",
        FOLLOW_UP_QUESTION,
        "Interpret the current question",
        "Do not request raw transaction-level data",
    ]

    for expected_text in required_content:

        assert (
            expected_text in planner_question
        ), (
            "Missing expected content: "
            f"{expected_text}"
        )

    print(
        "Planner question validation passed."
    )

    # --------------------------------------------------------
    # Step 6: Verify previous analysis ID
    # --------------------------------------------------------

    print("\n[6] Verifying previous analysis")
    print("-" * 70)

    assert (
        follow_up_context[
            "previous_analysis_id"
        ]
        == TEST_CONVERSATION_ID
        or follow_up_context[
            "previous_analysis_id"
        ]
        == "d74398ea-103c-44cd-9cfd-036f6c33de0e"
    )

    print(
        "Previous analysis reference verified."
    )

    # --------------------------------------------------------
    # Final
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print(
        "PIPELINE FOLLOW-UP CONTEXT TEST PASSED"
    )
    print("=" * 70)

    print()
    print(
        "Gemini was NOT called."
    )

    print(
        "Oracle was NOT called."
    )

    print(
        "The production pipeline was NOT executed."
    )


if __name__ == "__main__":
    main()