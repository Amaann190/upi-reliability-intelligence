
import pandas as pd

# Load the original dataset
df = pd.read_csv("data/raw/Remitter_Banks.csv")

# Standardize dates and remove extra spaces
df["Date"] = pd.to_datetime(df["Date"])
df["UPI_Remitter_Banks"] = (
    df["UPI_Remitter_Banks"].str.strip()
)

# -----------------------------------------
# INVESTIGATION 1: Duplicate bank-months
# -----------------------------------------

print("\n=== DUPLICATE BANK-MONTH RECORDS ===")

duplicates = df[
    df.duplicated(
        subset=["UPI_Remitter_Banks", "Date"],
        keep=False
    )
]

duplicates = duplicates.sort_values(
    ["UPI_Remitter_Banks", "Date"]
)

print(duplicates.to_string(index=False))

# -----------------------------------------
# INVESTIGATION 2: Debit reversal rates
# -----------------------------------------

print("\n=== INVALID DEBIT REVERSAL VALUES ===")

column = "Debit_Reversal_Success_percent"

invalid = df[
    (df[column] < 0) | (df[column] > 1)
]

print("Invalid records:", len(invalid))

print("Minimum value:", df[column].min())
print("Maximum value:", df[column].max())

print("\nExamples of invalid values:")

print(
    invalid[
        [
            "UPI_Remitter_Banks",
            "Date",
            column,
            "Total_Debit_Reversal_Count_In_Million"
        ]
    ].sort_values(
        column, ascending=False
    ).head(15).to_string(index=False)
)

# -----------------------------------------
# INVESTIGATION 3: Zero reversal counts
# -----------------------------------------

print("\n=== ZERO DEBIT REVERSAL COUNTS ===")

zero_reversals = df[
    df["Total_Debit_Reversal_Count_In_Million"] == 0
]

print("Records with zero reversal count:", len(zero_reversals))

print(
    "Of these, records with nonzero success rate:",
    (zero_reversals[column] != 0).sum()
)
