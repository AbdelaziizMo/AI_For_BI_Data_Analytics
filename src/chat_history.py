import sqlite3
from pathlib import Path
from datetime import datetime, timezone

import uuid
import json


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "chat_history.db"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    """
    Create and return a SQLite database connection.
    """

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)

    # Allows accessing columns by name if needed later
    connection.row_factory = sqlite3.Row

    # Enable foreign key constraints
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


# ============================================================
# CONVERSATION OPERATIONS
# ============================================================

def create_conversation(title="New BI Analysis"):
    """
    Create a new conversation and return its conversation ID.
    """

    conversation_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO conversations (
                conversation_id,
                title,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                conversation_id,
                title,
                now,
                now,
            ),
        )

        connection.commit()

        return conversation_id

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def conversation_exists(conversation_id):
    """
    Check whether a conversation exists.

    Returns:
        bool: True if conversation exists, otherwise False.
    """

    if not conversation_id:
        return False

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT 1
            FROM conversations
            WHERE conversation_id = ?
            LIMIT 1
            """,
            (conversation_id,),
        )

        return cursor.fetchone() is not None

    finally:
        connection.close()


def delete_conversation(conversation_id):
    """
    Delete one conversation and all related messages/analyses.
    """

    if not conversation_id:
        return False

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # Make sure the conversation exists
        cursor.execute(
            """
            SELECT 1
            FROM conversations
            WHERE conversation_id = ?
            LIMIT 1
            """,
            (conversation_id,),
        )

        if cursor.fetchone() is None:
            return False

        # Delete related messages first
        cursor.execute(
            """
            DELETE FROM messages
            WHERE conversation_id = ?
            """,
            (conversation_id,),
        )

        # Delete related analyses
        cursor.execute(
            """
            DELETE FROM analyses
            WHERE conversation_id = ?
            """,
            (conversation_id,),
        )

        # Delete conversation
        cursor.execute(
            """
            DELETE FROM conversations
            WHERE conversation_id = ?
            """,
            (conversation_id,),
        )

        connection.commit()

        return True

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def update_conversation_title(conversation_id, title):
    """
    Update the title of an existing conversation.
    """

    if not conversation_id:
        raise ValueError(
            "conversation_id cannot be empty."
        )

    if not title or not title.strip():
        raise ValueError(
            "Conversation title cannot be empty."
        )

    now = datetime.now(timezone.utc).isoformat()

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE conversations
            SET
                title = ?,
                updated_at = ?
            WHERE conversation_id = ?
            """,
            (
                title.strip(),
                now,
                conversation_id,
            ),
        )

        if cursor.rowcount == 0:
            raise ValueError(
                f"Conversation not found: {conversation_id}"
            )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_conversation(conversation_id):
    """
    Retrieve a conversation by its ID.

    Args:
        conversation_id (str): UUID of the conversation.

    Returns:
        dict | None: Conversation data or None if not found.
    """

    if not conversation_id:
        return None

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                conversation_id,
                title,
                created_at,
                updated_at
            FROM conversations
            WHERE conversation_id = ?
            """,
            (conversation_id,),
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return {
            "conversation_id": row[0],
            "title": row[1],
            "created_at": row[2],
            "updated_at": row[3],
        }

    finally:
        connection.close()


def get_conversations():
    """
    Retrieve all conversations.

    Results are ordered from newest to oldest.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                conversation_id,
                title,
                created_at,
                updated_at
            FROM conversations
            ORDER BY updated_at DESC
            """
        )

        rows = cursor.fetchall()

        conversations = []

        for row in rows:

            conversations.append(
                {
                    "conversation_id": row[0],
                    "title": row[1],
                    "created_at": row[2],
                    "updated_at": row[3],
                }
            )

        return conversations

    finally:
        connection.close()


# ============================================================
# MESSAGE OPERATIONS
# ============================================================

def add_message(conversation_id, role, content):
    """
    Add a message to an existing conversation.

    Args:
        conversation_id (str): UUID of the conversation.
        role (str): Message role - user, assistant, or system.
        content (str): Message content.

    Returns:
        str: UUID of the created message.
    """

    if not conversation_id:
        raise ValueError(
            "conversation_id cannot be empty."
        )

    if role not in (
        "user",
        "assistant",
        "system",
    ):
        raise ValueError(
            "Invalid role. Use: user, assistant, or system."
        )

    if not content or not content.strip():
        raise ValueError(
            "Message content cannot be empty."
        )

    message_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # ----------------------------------------------------
        # Insert message
        # ----------------------------------------------------

        cursor.execute(
            """
            INSERT INTO messages (
                message_id,
                conversation_id,
                role,
                content,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                message_id,
                conversation_id,
                role,
                content,
                now,
            ),
        )

        # ----------------------------------------------------
        # Update conversation timestamp
        # ----------------------------------------------------

        cursor.execute(
            """
            UPDATE conversations
            SET updated_at = ?
            WHERE conversation_id = ?
            """,
            (
                now,
                conversation_id,
            ),
        )

        # Make sure conversation actually exists
        if cursor.rowcount == 0:
            raise ValueError(
                f"Conversation not found: {conversation_id}"
            )

        connection.commit()

        return message_id

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_messages(conversation_id):
    """
    Retrieve all messages belonging to a conversation.

    Args:
        conversation_id (str): UUID of the conversation.

    Returns:
        list[dict]: Messages ordered by creation time.
    """

    if not conversation_id:
        return []

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                message_id,
                conversation_id,
                role,
                content,
                created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY created_at ASC
            """,
            (conversation_id,),
        )

        rows = cursor.fetchall()

        messages = []

        for row in rows:

            messages.append(
                {
                    "message_id": row[0],
                    "conversation_id": row[1],
                    "role": row[2],
                    "content": row[3],
                    "created_at": row[4],
                }
            )

        return messages

    finally:
        connection.close()


# ============================================================
# ANALYSIS OPERATIONS
# ============================================================

def add_analysis(
    conversation_id,
    business_question,
    analysis_plan=None,
    report_path=None,
):
    """
    Store an AI/BI analysis linked to a conversation.

    Args:
        conversation_id (str): UUID of the conversation.
        business_question (str): User's business question.
        analysis_plan:
            dict/list/str/None containing the analysis plan.
        report_path (str | None): Path to generated report.

    Returns:
        str: UUID of the created analysis.
    """

    if not conversation_id:
        raise ValueError(
            "conversation_id cannot be empty."
        )

    if not business_question or not business_question.strip():
        raise ValueError(
            "Business question cannot be empty."
        )

    analysis_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    # --------------------------------------------------------
    # Serialize analysis_plan before storing in SQLite
    # --------------------------------------------------------

    if analysis_plan is not None:

        if isinstance(
            analysis_plan,
            (dict, list)
        ):
            analysis_plan = json.dumps(
                analysis_plan,
                ensure_ascii=False,
            )

        elif not isinstance(
            analysis_plan,
            str
        ):
            analysis_plan = json.dumps(
                analysis_plan,
                ensure_ascii=False,
            )

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO analyses (
                analysis_id,
                conversation_id,
                business_question,
                analysis_plan,
                report_path,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                analysis_id,
                conversation_id,
                business_question,
                analysis_plan,
                report_path,
                now,
            ),
        )

        # ----------------------------------------------------
        # Update conversation timestamp
        # ----------------------------------------------------

        cursor.execute(
            """
            UPDATE conversations
            SET updated_at = ?
            WHERE conversation_id = ?
            """,
            (
                now,
                conversation_id,
            ),
        )

        if cursor.rowcount == 0:
            raise ValueError(
                f"Conversation not found: {conversation_id}"
            )

        connection.commit()

        return analysis_id

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def update_analysis_report_path(
    analysis_id: str,
    report_path: str,
):
    """
    Update the generated report path for an existing analysis.
    """

    if not analysis_id:
        raise ValueError(
            "analysis_id cannot be empty."
        )

    if not report_path:
        raise ValueError(
            "report_path cannot be empty."
        )

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE analyses
            SET report_path = ?
            WHERE analysis_id = ?
            """,
            (
                report_path,
                analysis_id,
            ),
        )

        if cursor.rowcount == 0:
            raise ValueError(
                f"Analysis not found: {analysis_id}"
            )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_conversation_analyses(
    conversation_id: str,
):
    """
    Retrieve all analyses associated with a conversation.

    Results are ordered from oldest to newest.
    """

    if not conversation_id:
        raise ValueError(
            "conversation_id cannot be empty."
        )

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                analysis_id,
                conversation_id,
                business_question,
                analysis_plan,
                report_path,
                created_at
            FROM analyses
            WHERE conversation_id = ?
            ORDER BY created_at ASC
            """,
            (conversation_id,),
        )

        rows = cursor.fetchall()

        analyses = []

        for row in rows:

            analysis_plan = row[3]

            if analysis_plan:

                try:
                    analysis_plan = json.loads(
                        analysis_plan
                    )

                except (
                    json.JSONDecodeError,
                    TypeError,
                ):
                    pass

            analyses.append(
                {
                    "analysis_id": row[0],
                    "conversation_id": row[1],
                    "business_question": row[2],
                    "analysis_plan": analysis_plan,
                    "report_path": row[4],
                    "created_at": row[5],
                }
            )

        return analyses

    finally:
        connection.close()


def get_analysis(analysis_id):
    """
    Retrieve an analysis by its ID.

    Args:
        analysis_id (str): UUID of the analysis.

    Returns:
        dict | None: Analysis data or None if not found.
    """

    if not analysis_id:
        return None

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                analysis_id,
                conversation_id,
                business_question,
                analysis_plan,
                report_path,
                created_at
            FROM analyses
            WHERE analysis_id = ?
            """,
            (analysis_id,),
        )

        row = cursor.fetchone()

        if row is None:
            return None

        analysis_plan = None

        if row[3]:

            try:
                analysis_plan = json.loads(
                    row[3]
                )

            except (
                json.JSONDecodeError,
                TypeError,
            ):
                analysis_plan = row[3]

        return {
            "analysis_id": row[0],
            "conversation_id": row[1],
            "business_question": row[2],
            "analysis_plan": analysis_plan,
            "report_path": row[4],
            "created_at": row[5],
        }

    finally:
        connection.close()


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database():
    """
    Create the Chat History database and required tables.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # ----------------------------------------------------
        # Conversations
        # ----------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                conversation_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        # ----------------------------------------------------
        # Messages
        # ----------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                message_id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,

                FOREIGN KEY (conversation_id)
                    REFERENCES conversations(conversation_id)
                    ON DELETE CASCADE
            )
            """
        )

        # ----------------------------------------------------
        # Analyses
        # ----------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS analyses (
                analysis_id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                business_question TEXT NOT NULL,
                analysis_plan TEXT,
                report_path TEXT,
                created_at TEXT NOT NULL,

                FOREIGN KEY (conversation_id)
                    REFERENCES conversations(conversation_id)
                    ON DELETE CASCADE
            )
            """
        )

        connection.commit()

        print("=" * 60)
        print("CHAT HISTORY DATABASE INITIALIZED")
        print("=" * 60)
        print(f"Database: {DB_PATH}")
        print()
        print("Tables:")
        print("  - conversations")
        print("  - messages")
        print("  - analyses")
        print("=" * 60)

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    initialize_database()

    print()
    print("=" * 60)
    print("CHAT HISTORY MODULE READY")
    print("=" * 60)
    print()
    print("No demo conversation was created.")
    print("The application will create conversations")
    print("when the user sends the first message.")
    print("=" * 60)