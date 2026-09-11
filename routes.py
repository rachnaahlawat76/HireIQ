from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import text
from pathlib import Path
import shutil
import uuid

from app.db.database import get_db
from app.db.models import User, Interview, Question, Candidate, Response
from app.tasks.celery_app import process_response_task


router = APIRouter(
    prefix="/api",
    tags=["HireIQ"]
)


# ---------------------------------------------------------
# 1. API HEALTH CHECK
# ---------------------------------------------------------

@router.get("/health")
def health_check():
    return {
        "status": "success",
        "service": "HireIQ API",
        "message": "API is running"
    }


# ---------------------------------------------------------
# 2. DATABASE HEALTH CHECK
# ---------------------------------------------------------

@router.get("/database-health")
def database_health(db: Session = Depends(get_db)):

    try:
        db.execute(text("SELECT 1"))

        return {
            "status": "success",
            "database": "PostgreSQL",
            "message": "Database connection successful"
        }

    except Exception as error:

        return {
            "status": "error",
            "message": str(error)
        }


# ---------------------------------------------------------
# 3. GET ALL INTERVIEWS
# ---------------------------------------------------------

@router.get("/interviews")
def get_interviews(db: Session = Depends(get_db)):

    interviews = db.query(Interview).all()

    return {
        "status": "success",
        "count": len(interviews),
        "interviews": [
            {
                "id": interview.id,
                "title": interview.title,
                "description": interview.description,
                "job_role": interview.job_role,
                "status": interview.status
            }
            for interview in interviews
        ]
    }


# ---------------------------------------------------------
# 4. GET QUESTIONS FOR AN INTERVIEW
# ---------------------------------------------------------

@router.get("/interviews/{interview_id}/questions")
def get_questions(
    interview_id: int,
    db: Session = Depends(get_db)
):

    questions = (
        db.query(Question)
        .filter(Question.interview_id == interview_id)
        .order_by(Question.order_index)
        .all()
    )

    return {
        "status": "success",
        "interview_id": interview_id,
        "count": len(questions),
        "questions": [
            {
                "id": question.id,
                "question_text": question.question_text,
                "category": question.category,
                "difficulty": question.difficulty,
                "order_index": question.order_index
            }
            for question in questions
        ]
    }


# ---------------------------------------------------------
# 5. CREATE CANDIDATE
# ---------------------------------------------------------

@router.post("/candidates")
def create_candidate(
    name: str = Form(...),
    email: str = Form(...),
    interview_id: int = Form(...),
    db: Session = Depends(get_db)
):

    interview = (
        db.query(Interview)
        .filter(Interview.id == interview_id)
        .first()
    )

    if not interview:
        raise HTTPException(
            status_code=404,
            detail="Interview not found"
        )

    candidate = Candidate(
        name=name,
        email=email,
        interview_id=interview_id,
        status="started"
    )

    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    return {
        "status": "success",
        "message": "Candidate created successfully",
        "candidate": {
            "id": candidate.id,
            "name": candidate.name,
            "email": candidate.email,
            "interview_id": candidate.interview_id,
            "status": candidate.status
        }
    }


# ---------------------------------------------------------
# 6. AUDIO UPLOAD
# ---------------------------------------------------------

@router.post("/responses/upload")
async def upload_response(
    candidate_id: int = Form(...),
    question_id: int = Form(...),
    audio: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    # Check candidate
    candidate = (
        db.query(Candidate)
        .filter(Candidate.id == candidate_id)
        .first()
    )

    if not candidate:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found"
        )

    # Check question
    question = (
        db.query(Question)
        .filter(Question.id == question_id)
        .first()
    )

    if not question:
        raise HTTPException(
            status_code=404,
            detail="Question not found"
        )

    # Create uploads directory
    upload_directory = Path("uploads")
    upload_directory.mkdir(
        parents=True,
        exist_ok=True
    )

    # Generate unique filename
    extension = Path(audio.filename).suffix or ".webm"

    filename = f"{uuid.uuid4()}{extension}"

    file_path = upload_directory / filename

    # Save audio file
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(audio.file, buffer)

    # Save response in database
    response = Response(
        candidate_id=candidate_id,
        question_id=question_id,
        audio_url=str(file_path),
        transcript=None
    )

    db.add(response)
    db.commit()
    db.refresh(response)

    # Send response to Celery
    task = process_response_task.delay(response.id)

    return {
        "status": "success",
        "message": "Audio uploaded successfully",
        "response_id": response.id,
        "task_id": task.id,
        "processing": "queued"
    }


# ---------------------------------------------------------
# 7. GET RESPONSE
# ---------------------------------------------------------

@router.get("/responses/{response_id}")
def get_response(
    response_id: int,
    db: Session = Depends(get_db)
):

    response = (
        db.query(Response)
        .filter(Response.id == response_id)
        .first()
    )

    if not response:
        raise HTTPException(
            status_code=404,
            detail="Response not found"
        )

    return {
        "status": "success",
        "response": {
            "id": response.id,
            "candidate_id": response.candidate_id,
            "question_id": response.question_id,
            "audio_url": response.audio_url,
            "transcript": response.transcript
        }
    }


# ---------------------------------------------------------
# 8. CELERY TASK STATUS
# ---------------------------------------------------------

@router.get("/tasks/{task_id}")
def get_task_status(task_id: str):

    from app.tasks.celery_app import celery_app

    result = celery_app.AsyncResult(task_id)

    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.ready() else None
    }