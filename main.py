
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from conflict_resolver import resolve_conflict, parse_git_conflict, analyze_conflict

app = FastAPI(
    title="Adaptive Merge Resolution",
    description=(
        "Adaptive Git Merge Conflict Resolution API. "
        "Predicts resolution strategy from conflict code and generates resolved output."
    ),
    version="2.0.0"
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
            "GET  /health": "Health check"
        }
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


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