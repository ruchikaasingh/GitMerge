
"""
features.py
-----------
Shared feature engineering components used by both train_model.py and
conflict_resolver.py. Keeping them in one place ensures the pickled model
can always deserialize correctly (joblib looks up the class by module path).
"""

import re
from sklearn.base import BaseEstimator, TransformerMixin


class StructuralFeatureExtractor(BaseEstimator, TransformerMixin):
    """
    Pulls pre-computed numeric columns out of a DataFrame for use
    inside a sklearn ColumnTransformer pipeline.
    """

    def __init__(self, columns):
        self.columns = columns

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return X[self.columns].values.astype(float)


# ---------------------------------------------------------------------------
# Shared token utilities (used by both prepare_dataset and conflict_resolver)
# ---------------------------------------------------------------------------

def tokenize(text: str) -> set:
    """Simple identifier tokenizer for code text."""
    return set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text.lower()))


def token_overlap(left: str, right: str) -> float:
    """Jaccard similarity between token sets of left and right code."""
    left_t = tokenize(left)
    right_t = tokenize(right)
    if not left_t and not right_t:
        return 0.0
    union = len(left_t | right_t)
    return round(len(left_t & right_t) / union, 4) if union > 0 else 0.0
