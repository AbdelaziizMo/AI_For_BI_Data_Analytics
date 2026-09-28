from typing import Dict, Any, Optional


# ============================================================
# FOLLOW-UP QUESTION RESOLVER
# ============================================================

# Words / phrases that commonly indicate that the user
# is referring to something from the previous analysis.
FOLLOW_UP_PATTERNS = [
    "it",
    "its",
    "this",
    "that",
    "these",
    "those",
    "the spike",
    "the service",
    "the services",
    "the revenue",
    "the transactions",
    "the volume",
    "the result",
    "the results",
    "the analysis",
    "the previous",
    "above",
    "earlier",
    "before",
    "previous analysis",
    "previous result",
    "same period",
    "same service",
]


# ============================================================
# FOLLOW-UP DETECTION
# ============================================================

def is_follow_up_question(
    question: str,
    relevant_context: Optional[Dict[str, Any]],
) -> bool:
    """
    Determine whether a question is likely a follow-up
    to an existing analysis.

    This is intentionally rule-based.

    It does NOT:
        - use AI
        - use embeddings
        - use vector databases
        - use RAG
    """

    if not question or not question.strip():
        return False

    if not relevant_context:
        return False

    previous_analysis = relevant_context.get(
        "previous_analysis"
    )

    if not previous_analysis:
        return False

    normalized_question = (
        question.strip().lower()
    )

    # --------------------------------------------------------
    # Explicit contextual references
    # --------------------------------------------------------

    for pattern in FOLLOW_UP_PATTERNS:

        if pattern in normalized_question:
            return True

    # --------------------------------------------------------
    # Short questions are often follow-ups.
    #
    # Example:
    # "What caused it?"
    # "Why?"
    # "Which service?"
    # "What about July 12?"
    # --------------------------------------------------------

    words = normalized_question.split()

    if len(words) <= 8:
        return True

    return False


# ============================================================
# RESOLVE QUESTION
# ============================================================

def resolve_follow_up_question(
    current_question: str,
    relevant_context: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Resolve the current question against the available
    conversation context.

    The resolver does NOT rewrite the user's question.

    Instead, it packages:
        - Current question
        - Follow-up status
        - Previous business question
        - Previous analysis ID
        - Previous analysis plan
        - Previous report path

    This structured result can later be passed to
    the AI Business Analyst.
    """

    if not current_question:
        raise ValueError(
            "current_question cannot be empty."
        )

    if relevant_context is None:
        return {
            "is_follow_up": False,
            "current_question": current_question,
            "previous_analysis": None,
            "context_available": False,
        }

    previous_analysis = relevant_context.get(
        "previous_analysis"
    )

    follow_up = is_follow_up_question(
        question=current_question,
        relevant_context=relevant_context,
    )

    # --------------------------------------------------------
    # No previous analysis
    # --------------------------------------------------------

    if previous_analysis is None:

        return {
            "is_follow_up": False,
            "current_question": current_question,
            "previous_analysis": None,
            "context_available": False,
        }

    # --------------------------------------------------------
    # Build resolved context
    # --------------------------------------------------------

    resolved_context = {
        "previous_business_question": (
            previous_analysis.get(
                "business_question"
            )
        ),
        "previous_analysis_id": (
            previous_analysis.get(
                "analysis_id"
            )
        ),
        "previous_analysis_plan": (
            previous_analysis.get(
                "analysis_plan"
            )
        ),
        "previous_report_path": (
            previous_analysis.get(
                "report_path"
            )
        ),
    }

    return {
        "is_follow_up": follow_up,
        "current_question": current_question,
        "context_available": True,
        "previous_analysis": resolved_context,
    }


# ============================================================
# BUILD AI CONTEXT
# ============================================================

def build_follow_up_context(
    current_question: str,
    relevant_context: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Build a compact context package for the next AI layer.

    This function does not send anything to an AI model.

    It only prepares structured context.
    """

    resolved = resolve_follow_up_question(
        current_question=current_question,
        relevant_context=relevant_context,
    )

    ai_context = {
        "current_question": (
            resolved["current_question"]
        ),
        "is_follow_up": (
            resolved["is_follow_up"]
        ),
        "context_available": (
            resolved["context_available"]
        ),
    }

    previous_analysis = resolved.get(
        "previous_analysis"
    )

    if previous_analysis:

        ai_context[
            "previous_business_question"
        ] = previous_analysis.get(
            "previous_business_question"
        )

        ai_context[
            "previous_analysis_id"
        ] = previous_analysis.get(
            "previous_analysis_id"
        )

        ai_context[
            "previous_analysis_plan"
        ] = previous_analysis.get(
            "previous_analysis_plan"
        )

        ai_context[
            "previous_report_path"
        ] = previous_analysis.get(
            "previous_report_path"
        )

    return ai_context


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    from src.context_manager import (
        get_relevant_context,
    )

    TEST_CONVERSATION_ID = (
        "e20e6393-443b-4759-9477-6529463c3f7b"
    )

    TEST_QUESTION = (
        "What caused the biggest revenue spike?"
    )

    print("=" * 70)
    print("FOLLOW-UP QUESTION RESOLVER TEST")
    print("=" * 70)

    # --------------------------------------------------------
    # Load context
    # --------------------------------------------------------

    print("\n[1] Loading conversation context")
    print("-" * 70)

    relevant_context = get_relevant_context(
        conversation_id=TEST_CONVERSATION_ID,
        message_limit=10,
    )

    if relevant_context is None:

        print("Conversation not found.")

        raise SystemExit(1)

    print("Context loaded successfully.")

    # --------------------------------------------------------
    # Resolve question
    # --------------------------------------------------------

    print("\n[2] Resolving follow-up question")
    print("-" * 70)

    print(
        f"Question: {TEST_QUESTION}"
    )

    resolved = resolve_follow_up_question(
        current_question=TEST_QUESTION,
        relevant_context=relevant_context,
    )

    print("\nResolved Result:")
    print(resolved)

    # --------------------------------------------------------
    # Build AI context
    # --------------------------------------------------------

    print("\n[3] Building AI context")
    print("-" * 70)

    ai_context = build_follow_up_context(
        current_question=TEST_QUESTION,
        relevant_context=relevant_context,
    )

    print(ai_context)

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    print("\n[4] Validation")
    print("-" * 70)

    assert (
        resolved["context_available"]
        is True
    )

    assert (
        resolved["is_follow_up"]
        is True
    )

    assert (
        resolved["previous_analysis"]
        is not None
    )

    assert (
        resolved["previous_analysis"][
            "previous_analysis_id"
        ]
        == "d74398ea-103c-44cd-9cfd-036f6c33de0e"
    )

    assert (
        ai_context["is_follow_up"]
        is True
    )

    print(
        "All follow-up resolver tests passed."
    )

    print("\n" + "=" * 70)
    print(
        "FOLLOW-UP QUESTION RESOLVER TEST COMPLETED"
    )
    print("=" * 70)