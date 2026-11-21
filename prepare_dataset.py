
import pandas as pd
from features import token_overlap

# Load the real dataset
df = pd.read_excel(
    "ConflictBench.xlsx",
    sheet_name="Paper_Textual_Conflict"
)

# Keep only valid conflicts
df = df[df.iloc[:, 7] == 1].copy()

# Extract input features
left_code = df.iloc[:, 8].fillna("").astype(str)
right_code = df.iloc[:, 9].fillna("").astype(str)
category = (
    df.iloc[:, 12]
    .fillna("unknown")
    .astype(str)
    .str.split("\n")
    .str[0]
    .str.strip()
)

# Extract and normalize resolution strategies
strategy = (
    df.iloc[:, 13]
    .fillna("")
    .astype(str)
    .str.strip()
    .str.lower()
)


def normalize_strategy(value):
    if value == "only left":
        return "only left"
    elif value == "only right":
        return "only right"
    elif value == "accept both sides":
        return "accept both sides"
    else:
        return "other"


# Compute structural features
left_line_counts = left_code.apply(lambda x: len(x.splitlines()))
right_line_counts = right_code.apply(lambda x: len(x.splitlines()))
overlap_scores = [
    token_overlap(l, r)
    for l, r in zip(left_code, right_code)
]

# Prepare the training dataset
training_data = pd.DataFrame({
    "left_code": left_code.values,
    "right_code": right_code.values,
    "conflict_category": category.values,
    "resolution_strategy": strategy.apply(normalize_strategy).values,
    "left_line_count": left_line_counts.values,
    "right_line_count": right_line_counts.values,
    "token_overlap": overlap_scores
})

training_data.to_csv("training_data.csv", index=False)

print("Dataset prepared successfully!")
print("Total valid records:", len(training_data))
print("\nStrategy distribution:")
print(training_data["resolution_strategy"].value_counts())
print("\nCategory distribution:")
print(training_data["conflict_category"].value_counts())
print("\nNew structural features (sample):")
print(training_data[["left_line_count", "right_line_count", "token_overlap"]].head())
print("\nSaved as training_data.csv")
print("\nLEFT code sample:")
print(repr(training_data["left_code"].iloc[0][:200]))
print("\nRIGHT code sample:")
print(repr(training_data["right_code"].iloc[0][:200]))
