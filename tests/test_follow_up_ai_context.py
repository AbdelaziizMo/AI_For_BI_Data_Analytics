from src.context_manager import get_relevant_context
from src.follow_up_resolver import build_follow_up_context
from src.ai_analysis import (
    load_prompt,
    load_sanitized_data,
    validate_input,
    build_analysis_request,
)


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
    print("AI FOLLOW-UP CONTEXT INTEGRATION TEST")
    print("=" * 70)

    # --------------------------------------------------------
    # Step 1: Load conversation context
    # --------------------------------------------------------

    print("\n[1] Loading conversation context")
    print("-" * 70)

    relevant_context = get_relevant_context(
        conversation_id=TEST_CONVERSATION_ID,
        message_limit=10,
    )

    if relevant_context is None:
        raise RuntimeError(
            "Conversation context not found."
        )

    print("Conversation context loaded.")

    # --------------------------------------------------------
    # Step 2: Build follow-up context
    # --------------------------------------------------------

    print("\n[2] Building follow-up context")
    print("-" * 70)

    follow_up_context = build_follow_up_context(
        current_question=FOLLOW_UP_QUESTION,
        relevant_context=relevant_context,
    )

    print(
        "Follow-up context:"
    )

    print(follow_up_context)

    # --------------------------------------------------------
    # Step 3: Validate follow-up detection
    # --------------------------------------------------------

    print("\n[3] Validating follow-up detection")
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
        "Follow-up detection passed."
    )

    # --------------------------------------------------------
    # Step 4: Load sanitized data
    # --------------------------------------------------------

    print("\n[4] Loading sanitized analytical data")
    print("-" * 70)

    data = load_sanitized_data()

    validate_input(data)

    print(
        "Sanitized data validated successfully."
    )

    # --------------------------------------------------------
    # Step 5: Override current question
    #
    # We do NOT modify the actual sanitized file.
    # We only create a temporary copy in memory.
    # --------------------------------------------------------

    test_data = data.copy()

    test_data[
        "business_question"
    ] = FOLLOW_UP_QUESTION

    # --------------------------------------------------------
    # Step 6: Build Gemini request
    # --------------------------------------------------------

    print("\n[5] Building Gemini request")
    print("-" * 70)

    prompt = load_prompt()

    request = build_analysis_request(
        prompt=prompt,
        data=test_data,
        follow_up_context=follow_up_context,
    )

    print(
        "Gemini request built successfully."
    )

    # --------------------------------------------------------
    # Step 7: Validate context exists in request
    # --------------------------------------------------------

    print("\n[6] Validating generated request")
    print("-" * 70)

    required_context = [
        "CURRENT BUSINESS QUESTION",
        FOLLOW_UP_QUESTION,
        "PREVIOUS ANALYSIS CONTEXT",
        "Previous Analysis ID:",
        "d74398ea-103c-44cd-9cfd-036f6c33de0e",
        "Previous Business Question:",
        "Previous Analysis Plan:",
        "PRIVACY STATUS:",
        "SANITIZED",
    ]

    for expected_text in required_context:

        assert (
            expected_text in request
        ), (
            f"Expected text not found in request: "
            f"{expected_text}"
        )

    print(
        "All required follow-up context "
        "was included in the request."
    )

    # --------------------------------------------------------
    # Step 8: Privacy validation
    # --------------------------------------------------------

    print("\n[7] Privacy validation")
    print("-" * 70)

    assert (
        "raw transaction" in request.lower()
    )

    assert (
        "SANITIZED" in request
    )

    print(
        "Privacy instructions confirmed."
    )

    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print(
        "AI FOLLOW-UP CONTEXT TEST PASSED"
    )
    print("=" * 70)

    print(
        "\nGemini was NOT called."
    )

    print(
        "Only the request/context construction "
        "was tested."
    )


if __name__ == "__main__":
    main()