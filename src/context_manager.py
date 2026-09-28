from typing import Optional, Dict, Any, List

from src.chat_history import (
    get_conversation,
    get_messages,
    get_conversation_analyses,
)


# ============================================================
# CONTEXT MANAGER
# ============================================================

def load_conversation_context(
    conversation_id: str,
) -> Optional[Dict[str, Any]]:
    """
    Load the available context for a conversation.

    The context includes:
        - Conversation metadata
        - Previous messages
        - Previous analyses

    This function does NOT send anything to an AI model.
    It only retrieves and structures data from Chat History.
    """

    if not conversation_id:
        raise ValueError("conversation_id cannot be empty.")

    # --------------------------------------------------------
    # Load conversation
    # --------------------------------------------------------

    conversation = get_conversation(conversation_id)

    if conversation is None:
        return None

    # --------------------------------------------------------
    # Load messages
    # --------------------------------------------------------

    messages = get_messages(conversation_id)

    # --------------------------------------------------------
    # Load analyses
    # --------------------------------------------------------

    analyses = get_conversation_analyses(
        conversation_id
    )

    # --------------------------------------------------------
    # Build context
    # --------------------------------------------------------

    context = {
        "conversation": conversation,
        "messages": messages,
        "analyses": analyses,
    }

    return context


# ============================================================
# RECENT MESSAGES
# ============================================================

def get_recent_messages(
    conversation_id: str,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    Return the most recent messages from a conversation.

    The messages are returned in chronological order.
    """

    if not conversation_id:
        raise ValueError("conversation_id cannot be empty.")

    if limit <= 0:
        raise ValueError("limit must be greater than zero.")

    messages = get_messages(conversation_id)

    return messages[-limit:]


# ============================================================
# PREVIOUS ANALYSIS
# ============================================================

def get_latest_analysis(
    conversation_id: str,
) -> Optional[Dict[str, Any]]:
    """
    Return the latest analysis associated with a conversation.

    If no analysis exists, return None.
    """

    if not conversation_id:
        raise ValueError("conversation_id cannot be empty.")

    analyses = get_conversation_analyses(
        conversation_id
    )

    if not analyses:
        return None

    return analyses[-1]


# ============================================================
# RELEVANT CONTEXT
# ============================================================

def get_relevant_context(
    conversation_id: str,
    message_limit: int = 10,
) -> Optional[Dict[str, Any]]:
    """
    Build the relevant context required for a follow-up BI question.

    The current Phase 2 implementation is intentionally
    rule-based.

    It includes:
        - Conversation metadata
        - Recent messages
        - Latest previous analysis

    It does NOT use:
        - AI
        - Embeddings
        - Vector databases
        - RAG
        - Raw transaction data

    This keeps the context small, predictable, and privacy-safe.
    """

    if not conversation_id:
        raise ValueError("conversation_id cannot be empty.")

    if message_limit <= 0:
        raise ValueError(
            "message_limit must be greater than zero."
        )

    # --------------------------------------------------------
    # Load conversation
    # --------------------------------------------------------

    conversation = get_conversation(
        conversation_id
    )

    if conversation is None:
        return None

    # --------------------------------------------------------
    # Load recent messages
    # --------------------------------------------------------

    recent_messages = get_recent_messages(
        conversation_id=conversation_id,
        limit=message_limit,
    )

    # --------------------------------------------------------
    # Load latest analysis
    # --------------------------------------------------------

    latest_analysis = get_latest_analysis(
        conversation_id
    )

    # --------------------------------------------------------
    # Build relevant context
    # --------------------------------------------------------

    relevant_context = {
        "conversation": conversation,
        "recent_messages": recent_messages,
        "previous_analysis": latest_analysis,
    }

    return relevant_context


# ============================================================
# CONTEXT SUMMARY
# ============================================================

def build_context_summary(
    conversation_id: str,
    message_limit: int = 10,
) -> Optional[Dict[str, Any]]:
    """
    Build a lightweight context summary.

    This includes:
        - Conversation metadata
        - Recent messages
        - All previous analyses

    No raw transaction data is loaded or exposed here.
    """

    context = load_conversation_context(
        conversation_id
    )

    if context is None:
        return None

    recent_messages = get_recent_messages(
        conversation_id=conversation_id,
        limit=message_limit,
    )

    return {
        "conversation": context["conversation"],
        "recent_messages": recent_messages,
        "analyses": context["analyses"],
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    TEST_CONVERSATION_ID = (
        "e20e6393-443b-4759-9477-6529463c3f7b"
    )

    print("=" * 70)
    print("CONTEXT MANAGER TEST")
    print("=" * 70)

    # --------------------------------------------------------
    # Test 1: Full Conversation Context
    # --------------------------------------------------------

    print("\n[1] Conversation Context")
    print("-" * 70)

    context = load_conversation_context(
        TEST_CONVERSATION_ID
    )

    if context is None:
        print("Conversation not found.")
        raise SystemExit(1)

    print("Conversation:")
    print(context["conversation"])

    print("\nMessages:")

    for message in context["messages"]:
        print(
            f"{message['role']}: "
            f"{message['content']}"
        )

    print("\nAnalyses:")

    for analysis in context["analyses"]:
        print(
            f"Analysis ID: "
            f"{analysis['analysis_id']}"
        )

    # --------------------------------------------------------
    # Test 2: Latest Analysis
    # --------------------------------------------------------

    print("\n[2] Latest Analysis")
    print("-" * 70)

    latest_analysis = get_latest_analysis(
        TEST_CONVERSATION_ID
    )

    print(latest_analysis)

    # --------------------------------------------------------
    # Test 3: Relevant Context
    # --------------------------------------------------------

    print("\n[3] Relevant Context")
    print("-" * 70)

    relevant_context = get_relevant_context(
        conversation_id=TEST_CONVERSATION_ID,
        message_limit=10,
    )

    print(relevant_context)

    # --------------------------------------------------------
    # Test 4: Context Summary
    # --------------------------------------------------------

    print("\n[4] Context Summary")
    print("-" * 70)

    summary = build_context_summary(
        conversation_id=TEST_CONVERSATION_ID,
        message_limit=10,
    )

    print(summary)

    print("\n" + "=" * 70)
    print("CONTEXT MANAGER TEST COMPLETED")
    print("=" * 70)