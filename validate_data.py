
import pandas as pd

# Read the original dataset
df = pd.read_csv("data/raw/Remitter_Banks.csv")

# Convert the Date column from text to real dates
df["Date"] = pd.to_datetime(
    df["Date"],
    errors="coerce"
)

# Remove accidental spaces from bank names
df["UPI_Remitter_Banks"] = (
    df["UPI_Remitter_Banks"].str.strip()
)

print("\n=== DATASET COVERAGE ===")

print("Earliest date:", df["Date"].min())
print("Latest date:", df["Date"].max())

print("Unique banks:", df["UPI_Remitter_Banks"].nunique())

print("Unique months:", df["Date"].nunique())

print("\n=== BANK-MONTH DUPLICATES ===")

duplicates = df.duplicated(
    subset=["UPI_Remitter_Banks", "Date"]
)

print("Duplicate bank-month records:", duplicates.sum())

print("\n=== DATE VALIDATION ===")

print("Invalid dates:", df["Date"].isna().sum())

print("\n=== PERCENTAGE VALIDATION ===")

percentage_columns = [
    "Approved_percent",
    "Bank_Decline_percent",
    "Technical_Decline_percent",
    "Debit_Reversal_Success_percent"
]

for column in percentage_columns:
    invalid = (
        (df[column] < 0) |
        (df[column] > 1)
    )

    print(column, "- invalid values:", invalid.sum())

# Approval + business declines + technical declines
# should be close to 1 (100%).
df["Outcome_Total"] = (
    df["Approved_percent"]
    + df["Bank_Decline_percent"]
    + df["Technical_Decline_percent"]
)

# A tolerance of 0.01 represents one percentage point.
invalid_totals = (
    (df["Outcome_Total"] - 1).abs() > 0.01
)

print(
    "\nRows where outcome percentages "
    "do not sum close to 100%:",
    invalid_totals.sum()
)

print("\n=== TRANSACTION VOLUME VALIDATION ===")

print(
    "Negative transaction volumes:",
    (df["Total_Volume_In_Million"] < 0).sum()
)

print("\n=== TOP 5 TECHNICAL DECLINE RATES ===")

columns = [
    "UPI_Remitter_Banks",
    "Date",
    "Technical_Decline_percent"
]

print(
    df.nlargest(
        5, "Technical_Decline_percent"
    )[columns].to_string(index=False)
)
