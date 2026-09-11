from celery import Celery
from pathlib import Path
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import SessionLocal
from app.db.models import Response
from app.services.whisper_service import transcribe_audio


# ---------------------------------------------------------
# CELERY CONFIGURATION
# ---------------------------------------------------------

celery_app = Celery(
    "hireiq",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True
)


# ---------------------------------------------------------
# TEST TASK
# ---------------------------------------------------------

@celery_app.task
def test_task():
    return {
        "status": "success",
        "message": "HireIQ Celery worker is working"
    }


# ---------------------------------------------------------
# PROCESS INTERVIEW RESPONSE
# ---------------------------------------------------------

@celery_app.task
def process_response_task(response_id: int):

    db: Session = SessionLocal()

    try:

        # -------------------------------------------------
        # FIND RESPONSE
        # -------------------------------------------------

        response = (
            db.query(Response)
            .filter(Response.id == response_id)
            .first()
        )

        if not response:
            return {
                "success": False,
                "message": "Response not found"
            }

        # -------------------------------------------------
        # CHECK AUDIO FILE
        # -------------------------------------------------

        audio_path = Path(response.audio_url)

        if not audio_path.exists():
            return {
                "success": False,
                "message": "Audio file not found"
            }

        print(f"Processing audio: {audio_path}")

        # -------------------------------------------------
        # WHISPER TRANSCRIPTION
        # -------------------------------------------------

        transcript = transcribe_audio(
            str(audio_path)
        )

        print(f"Transcript: {transcript}")

        # -------------------------------------------------
        # SAVE TRANSCRIPT
        # -------------------------------------------------

        response.transcript = transcript

        db.commit()
        db.refresh(response)

        # -------------------------------------------------
        # RETURN RESULT
        # -------------------------------------------------

        return {
            "success": True,
            "response_id": response_id,
            "transcript": transcript,
            "message": "Response transcribed successfully"
        }

    except Exception as error:

        db.rollback()

        print(f"Processing error: {str(error)}")

        return {
            "success": False,
            "message": str(error)
        }

    finally:

        db.close()