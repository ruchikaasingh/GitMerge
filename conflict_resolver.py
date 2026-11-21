
"""
conflict_resolver.py
--------------------
Core resolution engine for the Adaptive Merge Resolution system.

Responsibilities:
  1. Parse raw git conflict markers to extract left/right code sections.
  2. Load the trained strategy_model.pkl.
  3. Predict the resolution strategy from actual code content.
  4. Apply the predicted strategy to generate a resolved code candidate.
  5. Return structured results including confidence scores.
"""

import re
import joblib
import pandas as pd

from features import token_overlap as _token_overlap


# ---------------------------------------------------------------------------
# Load the trained strategy model once at import time
# ---------------------------------------------------------------------------
_model = None


def _get_model():
    global _model
    if _model is None:
        _model = joblib.load("strategy_model.pkl")
    return _model


# ---------------------------------------------------------------------------
# Git conflict marker parser
# ---------------------------------------------------------------------------
def parse_git_conflict(conflict_text: str) -> dict:
    """
    Parse a raw git conflict block into its components.

    Expected format:
        <<<<<<< HEAD (or branch name)
        <left side code>
        =======
        <right side code>
        >>>>>>> <other branch>

    Returns a dict with:
        left_code   : str
        right_code  : str
        left_label  : str  (branch name from <<<<<<< line)
        right_label : str  (branch name from >>>>>>> line)
        is_valid    : bool
    """
    pattern = re.compile(
        r"<{7}\s*(.+?)\n(.*?)\n={7}\n(.*?)\n>{7}\s*(.+)",
        re.DOTALL
    )
    match = pattern.search(conflict_text)

    if match:
        return {
            "left_label": match.group(1).strip(),
            "left_code": match.group(2).strip(),
            "right_code": match.group(3).strip(),
            "right_label": match.group(4).strip(),
            "is_valid": True
        }

    # Try a looser parse: just split on ======= if markers are present
    has_start = "<<<<<<<<" in conflict_text or "<<<<<<<" in conflict_text
    has_sep = "=======" in conflict_text
    has_end = ">>>>>>>" in conflict_text

    if has_start and has_sep and has_end:
        parts = re.split(r"={7}", conflict_text, maxsplit=1)
        left_raw = re.split(r"<{7}.*\n", parts[0], maxsplit=1)
        right_raw = re.split(r"\n>{7}", parts[1], maxsplit=1)

        return {
            "left_label": "HEAD",
            "left_code": (left_raw[-1] if len(left_raw) > 1 else parts[0]).strip(),
            "right_code": (right_raw[0] if right_raw else parts[1]).strip(),
            "right_label": "incoming",
            "is_valid": True
        }

    return {
        "left_label": "",
        "left_code": conflict_text.strip(),
        "right_code": "",
        "right_label": "",
        "is_valid": False
    }



# ---------------------------------------------------------------------------
# Strategy application: turn a predicted label into resolved code
# ---------------------------------------------------------------------------
def apply_strategy(strategy: str, left_code: str, right_code: str) -> str:
    """
    Apply the predicted resolution strategy to produce a resolved code string.

    Strategies:
        only left        — use left_code as-is
        only right       — use right_code as-is
        accept both sides— concatenate left then right
        other            — present both with a clear comment (manual review needed)
    """
    if strategy == "only left":
        return left_code

    elif strategy == "only right":
        return right_code

    elif strategy == "accept both sides":
        # Combine both, separated by a blank line
        separator = "\n\n"
        return left_code + separator + right_code

    else:  # "other" — cannot auto-resolve, flag for manual review
        return (
            "# ⚠️  AUTO-RESOLUTION NOT POSSIBLE — manual review required\n"
            "# Strategy: other (custom merge needed)\n"
            "#\n"
            "# --- LEFT SIDE ---\n"
            + "\n".join(f"# {line}" for line in left_code.splitlines())
            + "\n#\n# --- RIGHT SIDE ---\n"
            + "\n".join(f"# {line}" for line in right_code.splitlines())
        )


# ---------------------------------------------------------------------------
# Main resolution function — called by the FastAPI endpoints
# ---------------------------------------------------------------------------
def resolve_conflict(
    left_code: str,
    right_code: str,
    conflict_category: str = "unknown",
    conflict_text: str = None
) -> dict:
    """
    Predict the resolution strategy and generate a resolved code candidate.

    Parameters
    ----------
    left_code          : Code from the left/HEAD side of the conflict.
    right_code         : Code from the right/incoming side.
    conflict_category  : Conflict category (e.g., 'U vs. U', 'D vs. U').
                         Defaults to 'unknown' if not provided.
    conflict_text      : Optional raw git conflict block. If provided and
                         left_code/right_code are empty, they are parsed
                         from this text automatically.

    Returns
    -------
    dict with:
        predicted_strategy : str
        confidence         : float  (probability of predicted class)
        all_probabilities  : dict   {strategy: probability}
        resolved_code      : str
        left_code          : str
        right_code         : str
        conflict_category  : str
        token_overlap      : float
        is_auto_resolvable : bool
        message            : str
    """
    # If raw conflict text is provided and codes are missing, parse it
    if conflict_text and not left_code.strip() and not right_code.strip():
        parsed = parse_git_conflict(conflict_text)
        left_code = parsed["left_code"]
        right_code = parsed["right_code"]

    if not left_code.strip() and not right_code.strip():
        return {
            "predicted_strategy": None,
            "confidence": 0.0,
            "all_probabilities": {},
            "resolved_code": "",
            "left_code": left_code,
            "right_code": right_code,
            "conflict_category": conflict_category,
            "token_overlap": 0.0,
            "is_auto_resolvable": False,
            "message": "No conflict code provided. Please supply left_code and right_code."
        }

    # Build feature row — must match the schema used in train_model.py
    overlap = _token_overlap(left_code, right_code)
    left_lines = len(left_code.splitlines())
    right_lines = len(right_code.splitlines())

    sample = pd.DataFrame([{
        "conflict_text": left_code + "\n" + right_code,
        "conflict_category": conflict_category,
        "left_line_count": left_lines,
        "right_line_count": right_lines,
        "token_overlap": overlap
    }])

    model = _get_model()
    predicted_strategy = model.predict(sample)[0]
    probabilities = model.predict_proba(sample)[0]
    prob_dict = {
        label: round(float(prob), 4)
        for label, prob in zip(model.classes_, probabilities)
    }
    confidence = round(float(max(probabilities)), 4)

    resolved_code = apply_strategy(predicted_strategy, left_code, right_code)
    is_auto_resolvable = predicted_strategy != "other"

    return {
        "predicted_strategy": predicted_strategy,
        "confidence": confidence,
        "all_probabilities": prob_dict,
        "resolved_code": resolved_code,
        "left_code": left_code,
        "right_code": right_code,
        "conflict_category": conflict_category,
        "token_overlap": overlap,
        "is_auto_resolvable": is_auto_resolvable,
        "message": (
            "Resolution generated successfully."
            if is_auto_resolvable
            else "Strategy is 'other' — auto-resolution not possible. Manual review needed."
        )
    }


