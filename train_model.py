
import pandas as pd
import numpy as np
import joblib

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

# Import from shared module so joblib can deserialize the pkl anywhere
from features import StructuralFeatureExtractor


# -------------------------------------------------------------------
# Load prepared dataset
# -------------------------------------------------------------------
data = pd.read_csv("training_data.csv")

# Combine both sides of the conflict for text features
data["conflict_text"] = (
    data["left_code"].fillna("") + "\n" + data["right_code"].fillna("")
)

# Fill structural features in case they are missing
for col in ["left_line_count", "right_line_count", "token_overlap"]:
    if col not in data.columns:
        data[col] = 0

X = data[[
    "conflict_text",
    "conflict_category",
    "left_line_count",
    "right_line_count",
    "token_overlap"
]]
y = data["resolution_strategy"]

print("Class distribution:")
print(y.value_counts())

# -------------------------------------------------------------------
# Feature engineering
# Word-level TF-IDF: captures function/variable names
# Char n-gram TF-IDF: robust to code style differences & typos
# One-Hot: conflict category
# Structural: line counts + token overlap
# -------------------------------------------------------------------
preprocessor = ColumnTransformer(
    transformers=[
        (
            "word_tfidf",
            TfidfVectorizer(
                max_features=3000,
                ngram_range=(1, 2),
                analyzer="word",
                sublinear_tf=True
            ),
            "conflict_text"
        ),
        (
            "char_tfidf",
            TfidfVectorizer(
                max_features=2000,
                ngram_range=(3, 5),
                analyzer="char_wb",
                sublinear_tf=True
            ),
            "conflict_text"
        ),
        (
            "category",
            OneHotEncoder(handle_unknown="ignore"),
            ["conflict_category"]
        ),
        (
            "structural",
            StructuralFeatureExtractor(
                ["left_line_count", "right_line_count", "token_overlap"]
            ),
            ["left_line_count", "right_line_count", "token_overlap"]
        )
    ]
)

# -------------------------------------------------------------------
# Random Forest: handles small datasets better than Logistic Regression
# -------------------------------------------------------------------
model = Pipeline([
    ("features", preprocessor),
    ("classifier", RandomForestClassifier(
        n_estimators=300,
        max_depth=None,
        min_samples_leaf=2,
        class_weight="balanced",   # handles class imbalance
        random_state=42,
        n_jobs=-1
    ))
])

# -------------------------------------------------------------------
# Evaluation: stratified split + cross-validation
# -------------------------------------------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

model.fit(X_train, y_train)
predictions = model.predict(X_test)

print("\n=== Held-out Test Set Evaluation ===")
print("Test accuracy:", round(accuracy_score(y_test, predictions), 3))
print("\nClassification report:")
print(classification_report(y_test, predictions, zero_division=0))

# Cross-validation for a more robust accuracy estimate
cv_scores = cross_val_score(model, X, y, cv=5, scoring="accuracy")
print(f"\n=== 5-Fold Cross-Validation ===")
print(f"Mean accuracy : {cv_scores.mean():.3f}")
print(f"Std deviation : {cv_scores.std():.3f}")
print(f"Per-fold      : {[round(s, 3) for s in cv_scores]}")

# -------------------------------------------------------------------
# Train final model on ALL available data, then save
# -------------------------------------------------------------------
model.fit(X, y)
joblib.dump(model, "strategy_model.pkl")

print("\nFinal model saved as strategy_model.pkl")
print("Total training records:", len(data))
print("Classes learned:", list(model.classes_))