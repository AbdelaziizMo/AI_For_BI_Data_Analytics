from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.pipeline import run_pipeline
from src.chat_history import (
    get_analysis,
    get_conversations,
    get_conversation,
    get_messages,
    get_conversation_analyses,
    delete_conversation,
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = BASE_DIR / "web"
OUTPUT_DIR = BASE_DIR / "output"

REPORT_FILE = OUTPUT_DIR / "ai_business_report.md"
PDF_REPORT_FILE = OUTPUT_DIR / "ai_business_report_final.pdf"


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="Week 10 AI BI Analyst",
    description="AI-powered Business Intelligence Analysis API",
    version="1.0.0",
)


# ============================================================
# STATIC FILES
# ============================================================

app.mount(
    "/static",
    StaticFiles(directory=str(WEB_DIR)),
    name="static",
)


# ============================================================
# REQUEST MODELS
# ============================================================

class ChatRequest(BaseModel):
    question: str
    conversation_id: str | None = None


# ============================================================
# FRONTEND
# ============================================================

@app.get("/", include_in_schema=False)
async def serve_frontend():
    """
    Serve the main frontend page.
    """

    index_file = WEB_DIR / "index.html"

    if not index_file.exists():
        raise HTTPException(
            status_code=404,
            detail="Frontend index.html not found.",
        )

    return FileResponse(index_file)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/api/health")
async def health_check():

    return {
        "success": True,
        "status": "online",
        "service": "Week 10 AI BI Analyst",
    }


# ============================================================
# CHAT
# ============================================================

@app.post("/api/chat")
async def chat(request: ChatRequest):

    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    try:

        # ====================================================
        # IMPORTANT:
        # pipeline.run_pipeline() expects:
        #
        # business_question
        #
        # NOT:
        #
        # question
        # ====================================================

        result = run_pipeline(
            business_question=question,
            conversation_id=request.conversation_id,
        )

        conversation_id = result["conversation_id"]

        # ----------------------------------------------------
        # Load full report
        # ----------------------------------------------------

        answer = result.get("answer", "")

        if REPORT_FILE.exists():

            try:

                answer = REPORT_FILE.read_text(
                    encoding="utf-8"
                )

            except Exception:

                pass

        # ----------------------------------------------------
        # Load conversation
        # ----------------------------------------------------

        conversation = get_conversation(
            conversation_id
        )

        # ----------------------------------------------------
        # Load analyses
        # ----------------------------------------------------

        analyses = get_conversation_analyses(
            conversation_id
        )

        # ----------------------------------------------------
        # Successful response
        # ----------------------------------------------------

        return {
            "success": True,
            "conversation_id": conversation_id,
            "conversation": conversation,
            "analysis_id": result.get("analysis_id"),
            "analyses": analyses,
            "follow_up": result.get("follow_up"),
            "report_path": result.get("report_path"),
            "answer": answer,
            "message": "Analysis completed successfully.",
            "fallback": False,
        }

    except Exception as exc:

        error_message = str(exc)

        print()
        print("=" * 70)
        print("API CHAT ERROR")
        print("=" * 70)
        print(error_message)
        print("=" * 70)

        # ----------------------------------------------------
        # Gemini quota
        # ----------------------------------------------------

        if (
            "429" in error_message
            or "RESOURCE_EXHAUSTED" in error_message
            or "Quota exceeded" in error_message
        ):

            raise HTTPException(
                status_code=429,
                detail=(
                    "Gemini API quota has been exceeded. "
                    "Please try again later."
                ),
            )

        # ----------------------------------------------------
        # Gemini temporarily unavailable
        # ----------------------------------------------------

        if (
            "503" in error_message
            or "UNAVAILABLE" in error_message
            or "high demand" in error_message
        ):

            raise HTTPException(
                status_code=503,
                detail=(
                    "Gemini is temporarily unavailable "
                    "due to high demand. Please try again."
                ),
            )

        # ----------------------------------------------------
        # General error
        # ----------------------------------------------------

        raise HTTPException(
            status_code=500,
            detail=error_message,
        )


# ============================================================
# CONVERSATIONS
# ============================================================

@app.get("/api/conversations")
async def conversations():

    try:

        items = get_conversations()

        return {
            "success": True,
            "conversations": items,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


# ============================================================
# SINGLE CONVERSATION
# ============================================================

@app.get("/api/conversations/{conversation_id}")
async def conversation(conversation_id: str):

    try:

        item = get_conversation(
            conversation_id
        )

        if not item:

            raise HTTPException(
                status_code=404,
                detail="Conversation not found.",
            )

        messages = get_messages(
            conversation_id
        )

        analyses = get_conversation_analyses(
            conversation_id
        )

        return {
            "success": True,
            "conversation": item,
            "messages": messages,
            "analyses": analyses,
        }

    except HTTPException:

        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


# ============================================================
# ANALYSIS
# ============================================================

@app.get("/api/analyses/{analysis_id}")
async def analysis(analysis_id: str):

    try:

        item = get_analysis(
            analysis_id
        )

        if not item:

            raise HTTPException(
                status_code=404,
                detail="Analysis not found.",
            )

        return {
            "success": True,
            "analysis": item,
        }

    except HTTPException:

        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


# ============================================================
# PDF REPORT
# ============================================================

@app.get("/api/reports/{analysis_id}")
async def report(analysis_id: str):

    try:

        analysis_data = get_analysis(
            analysis_id
        )

        if not analysis_data:

            raise HTTPException(
                status_code=404,
                detail="Analysis not found.",
            )

        report_path = analysis_data.get(
            "report_path"
        )

        if not report_path:

            raise HTTPException(
                status_code=404,
                detail="Report path not available.",
            )

        # ----------------------------------------------------
        # Resolve report path safely
        # ----------------------------------------------------

        report_file = BASE_DIR / report_path

        if not report_file.exists():

            # Fallback to the standard PDF
            if PDF_REPORT_FILE.exists():

                report_file = PDF_REPORT_FILE

            else:

                raise HTTPException(
                    status_code=404,
                    detail="PDF report file not found.",
                )

        return FileResponse(
            path=report_file,
            media_type="application/pdf",
            filename="ai_business_report_final.pdf",
        )

    except HTTPException:

        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )

@app.delete("/api/conversations/{conversation_id}")
async def delete_chat(conversation_id: str):

    try:

        deleted = delete_conversation(
            conversation_id
        )

        if not deleted:

            raise HTTPException(
                status_code=404,
                detail="Conversation not found."
            )

        return {
            "success": True,
            "conversation_id": conversation_id,
            "message": "Conversation deleted successfully."
        }

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )