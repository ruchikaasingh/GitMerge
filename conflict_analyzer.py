
import joblib
import pandas as pd


model = joblib.load("risk_model.pkl")


def analyze_conflict(conflict_text):
    if not conflict_text.strip():
        return {
            "conflict_type": "unknown",
            "risk_level": "unknown",
            "features": [],
            "message": "No conflict text provided."
        }

    text = conflict_text.lower()
    features = []

    has_start = "<<<<<<<" in conflict_text
    has_separator = "=======" in conflict_text
    has_end = ">>>>>>>" in conflict_text

    conflict_markers = int(
        has_start and has_separator and has_end
    )

    line_count = len(conflict_text.splitlines())

    if conflict_markers:
        conflict_type = "textual"
        features.append("git_conflict_markers_detected")
    else:
        conflict_type = "unrecognized"

    features.append(f"line_count:{line_count}")

    risk_keywords = [
        "security",
        "authentication",
        "authorization",
        "permission",
        "delete"
    ]

    detected_keywords = []

    for keyword in risk_keywords:
        if keyword in text:
            detected_keywords.append(keyword)
            features.append(f"keyword:{keyword}")

    security_keyword = int(len(detected_keywords) > 0)

    sample = pd.DataFrame(
        [[conflict_markers, line_count, security_keyword]],
        columns=[
            "conflict_markers",
            "line_count",
            "security_keyword"
        ]
    )

    risk_level = model.predict(sample)[0]

    return {
        "conflict_type": conflict_type,
        "risk_level": risk_level,
        "features": features,
        "message": "Conflict analysis completed using the ML model."
    }