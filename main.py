
import os

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Optional
from sqlalchemy.exc import SQLAlchemyError

from backend.database import check_database, get_db
from backend.models import ConflictReview, to_review_dict
from backend.schemas import ReviewCreate
from conflict_resolver import resolve_conflict, parse_git_conflict

app = FastAPI(
    title="Adaptive Merge Resolution",
    description=(
        "Adaptive Git Merge Conflict Resolution API. "
        "Predicts resolution strategy from conflict code and generates resolved output."
    ),
    version="2.0.0"
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class RawConflictRequest(BaseModel):
    """
    For submitting a raw git conflict block (with <<<<<<< ======= >>>>>>> markers).
    Optionally specify the conflict category if known.
    """
    conflict_text: str
    conflict_category: Optional[str] = "unknown"


class StructuredConflictRequest(BaseModel):
    """
    For submitting pre-parsed left and right code separately.
    This is the preferred input format for programmatic use.
    """
    left_code: str
    right_code: str
    conflict_category: Optional[str] = "unknown"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "Adaptive Merge Resolution API is running!",
        "version": "2.0.0",
        "status": "success",
        "endpoints": {
            "POST /analyze": "Submit raw git conflict text for resolution",
            "POST /predict": "Submit left_code + right_code for resolution",
            "GET  /health": "API and database health check",
            "GET  /api/reviews": "List recent review decisions",
            "POST /api/reviews": "Save a review decision"
        }
    }


@app.get("/health")
def health_check():
    if not os.getenv("DATABASE_URL"):
        return {"status": "healthy", "database": "not_configured"}
    try:
        check_database()
    except (SQLAlchemyError, RuntimeError):
        # Conflict prediction remains usable when the optional history DB is down.
        return {"status": "degraded", "database": "unavailable"}
    return {"status": "healthy", "database": "connected"}


@app.get("/api/reviews")
def list_reviews(session: Session | None = Depends(get_db)):
    if session is None:
        raise HTTPException(status_code=503, detail="Review history requires DATABASE_URL.")
    try:
        reviews = session.scalars(
            select(ConflictReview)
            .order_by(ConflictReview.created_at.desc())
            .limit(50)
        ).all()
        return [to_review_dict(review) for review in reviews]
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="Review history requires DATABASE_URL.") from exc
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Review history is unavailable.") from exc


@app.post("/api/reviews", status_code=201)
def save_review(request: ReviewCreate, session: Session | None = Depends(get_db)):
    if session is None:
        raise HTTPException(status_code=503, detail="Saving review decisions requires DATABASE_URL.")
    try:
        review = ConflictReview(**request.model_dump())
        session.add(review)
        session.commit()
        session.refresh(review)
        return to_review_dict(review)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="Saving review decisions requires DATABASE_URL.") from exc
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Could not save review decision.") from exc


@app.post("/analyze")
def analyze(request: RawConflictRequest):
    """
    Accept a raw git conflict block (<<<<<<< ... ======= ... >>>>>>>).
    Parses left/right code, predicts strategy, and returns resolved output.
    """
    if not request.conflict_text.strip():
        raise HTTPException(
            status_code=400,
            detail="conflict_text cannot be empty."
        )

    parsed = parse_git_conflict(request.conflict_text)
    result = resolve_conflict(
        left_code=parsed["left_code"],
        right_code=parsed["right_code"],
        conflict_category=request.conflict_category or "unknown",
        conflict_text=request.conflict_text
    )

    result["parsed_markers"] = {
        "left_label": parsed.get("left_label", ""),
        "right_label": parsed.get("right_label", ""),
        "markers_found": parsed["is_valid"]
    }
    return result


@app.post("/predict")
def predict(request: StructuredConflictRequest):
    """
    Accept pre-parsed left_code and right_code separately.
    Predicts strategy and returns resolved output.
    Preferred endpoint for programmatic / batch use.
    """
    if not request.left_code.strip() and not request.right_code.strip():
        raise HTTPException(
            status_code=400,
            detail="At least one of left_code or right_code must be non-empty."
        )

    result = resolve_conflict(
        left_code=request.left_code,
        right_code=request.right_code,
        conflict_category=request.conflict_category or "unknown"
    )
    return result
