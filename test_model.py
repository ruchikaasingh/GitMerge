
"""
test_model.py
-------------
End-to-end test of the strategy model and conflict resolver.
Tests:
  1. Prediction from dataset row (structured input)
  2. Resolution via raw git conflict text (marker-based parsing)
  3. Strategy application output
"""

import pandas as pd
import joblib
from conflict_resolver import resolve_conflict, parse_git_conflict, apply_strategy

print("=" * 60)
print("TEST 1: Prediction from dataset row")
print("=" * 60)

data = pd.read_csv("training_data.csv")
sample_row = data.iloc[0]

result = resolve_conflict(
    left_code=str(sample_row["left_code"]),
    right_code=str(sample_row["right_code"]),
    conflict_category=str(sample_row.get("conflict_category", "unknown"))
)

print(f"Actual strategy   : {sample_row['resolution_strategy']}")
print(f"Predicted strategy: {result['predicted_strategy']}")
print(f"Confidence        : {result['confidence']:.2%}")
print(f"Token overlap     : {result['token_overlap']:.4f}")
print(f"Auto-resolvable   : {result['is_auto_resolvable']}")
print(f"\nAll probabilities:")
for label, prob in sorted(result['all_probabilities'].items(), key=lambda x: -x[1]):
    bar = "█" * int(prob * 30)
    print(f"  {label:<20} {prob:.2%}  {bar}")

print(f"\nResolved code preview (first 300 chars):")
print(result["resolved_code"][:300])

print()
print("=" * 60)
print("TEST 2: Raw git conflict text parsing")
print("=" * 60)

raw_conflict = """<<<<<<< HEAD
def get_version():
    return "1.0.0"
=======
def get_version():
    return "2.0.0"
>>>>>>> feature/update-version"""

parsed = parse_git_conflict(raw_conflict)
print(f"Markers found : {parsed['is_valid']}")
print(f"Left label    : {parsed['left_label']}")
print(f"Right label   : {parsed['right_label']}")
print(f"Left code     : {parsed['left_code']}")
print(f"Right code    : {parsed['right_code']}")

result2 = resolve_conflict(
    left_code=parsed["left_code"],
    right_code=parsed["right_code"],
    conflict_text=raw_conflict
)
print(f"\nPredicted strategy : {result2['predicted_strategy']}")
print(f"Confidence         : {result2['confidence']:.2%}")
print(f"\nResolved output:")
print(result2["resolved_code"])

print()
print("=" * 60)
print("TEST 3: Strategy application correctness")
print("=" * 60)

left = "version = '1.0.0'"
right = "version = '2.0.0'"

for strategy in ["only left", "only right", "accept both sides", "other"]:
    print(f"\n--- Strategy: {strategy} ---")
    print(apply_strategy(strategy, left, right))

print()
print("=" * 60)
print("TEST 4: Multiple dataset samples")
print("=" * 60)

correct = 0
total = min(20, len(data))
for i in range(total):
    row = data.iloc[i]
    res = resolve_conflict(
        left_code=str(row["left_code"]),
        right_code=str(row["right_code"]),
        conflict_category=str(row.get("conflict_category", "unknown"))
    )
    match = res["predicted_strategy"] == row["resolution_strategy"]
    if match:
        correct += 1
    status = "✓" if match else "✗"
    print(f"  [{status}] Actual: {row['resolution_strategy']:<20} "
          f"Predicted: {res['predicted_strategy']:<20} "
          f"Conf: {res['confidence']:.0%}")

print(f"\nAccuracy on first {total} samples: {correct}/{total} = {correct/total:.1%}")