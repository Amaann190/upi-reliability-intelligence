
from pathlib import Path
import pandas as pd

# ==========================================
# 1. READ THE ORIGINAL DATASET
# ==========================================

raw_file = Path("data/raw/Remitter_Banks.csv")
output_folder = Path("data/processed")

output_folder.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(raw_file)

original_count = len(df)

print("Original records:", original_count)


# ==========================================
# 2. STANDARDIZE DATES AND BANK NAMES
# ==========================================

df["Date"] = pd.to_datetime(
    df["Date"],
    errors="coerce"
)

df["UPI_Remitter_Banks"] = (
    df["UPI_Remitter_Banks"].str.strip()
)

if df["Date"].isna().any():
    raise ValueError("Invalid dates found. Review required.")


# ==========================================
# 3. INSPECT AND NORMALIZE REVERSAL RATES
# ==========================================

column = "Debit_Reversal_Success_percent"

# Preserve original values for auditing.
df["Reversal_Rate_Original"] = df[column]

# Identify records stored above 1 (100%).
needs_conversion = df[column] > 1

# Print affected months.
affected_months = sorted(
    df.loc[needs_conversion, "Date"]
      .dt.strftime("%Y-%m")
      .unique()
      .tolist()
)

print("Months with reversal-rate issues:", affected_months)

# This rule is specific to the suspected August
# 2022 unit inconsistency. Do not silently
# normalize unexpected records.
if needs_conversion.any():
    if affected_months != ["2022-08"]:
        raise ValueError(
            "Unexpected affected months. "
            "Verify source values before conversion."
        )

    if (df.loc[needs_conversion, column] > 100).any():
        raise ValueError(
            "Reversal rate exceeds 100%. Review required."
        )

# Record which values were changed.
df["Reversal_Rate_Rescaled"] = needs_conversion

# Convert 0-100 percentages to 0-1 proportions.
df.loc[needs_conversion, column] = (
    df.loc[needs_conversion, column] / 100
)

print("Reversal rates rescaled:", needs_conversion.sum())


# ==========================================
# 4. VALIDATE THE CLEANED PERCENTAGES
# ==========================================

rate_columns = [
    "Approved_percent",
    "Bank_Decline_percent",
    "Technical_Decline_percent",
    "Debit_Reversal_Success_percent"
]

for rate in rate_columns:
    if df[rate].isna().any():
        raise ValueError(f"Missing rate: {rate}")

    if not df[rate].between(0, 1).all():
        raise ValueError(f"Invalid rate: {rate}")

outcome_total = (
    df["Approved_percent"]
    + df["Bank_Decline_percent"]
    + df["Technical_Decline_percent"]
)

if ((outcome_total - 1).abs() > 0.01).any():
    raise ValueError("Transaction outcome totals are inconsistent.")

if (df["Total_Volume_In_Million"] < 0).any():
    raise ValueError("Negative transaction volume found.")


# ==========================================
# 5. QUARANTINE CONFLICTING BANK-MONTHS
# ==========================================

bank_month = ["UPI_Remitter_Banks", "Date"]

duplicate_mask = df.duplicated(
    subset=bank_month,
    keep=False
)

conflicts = df.loc[duplicate_mask].copy()
clean_df = df.loc[~duplicate_mask].copy()

# Sort chronologically for future trend analysis.
clean_df = clean_df.sort_values(
    ["UPI_Remitter_Banks", "Date"]
)

# ==========================================
# 6. EXPORT THE RESULTS
# ==========================================

clean_file = output_folder / "remitter_banks_clean.csv"

conflict_file = (
    output_folder / "conflicting_bank_months.csv"
)

clean_df.to_csv(clean_file, index=False)
conflicts.to_csv(conflict_file, index=False)

print("\n=== CLEANING SUMMARY ===")
print("Original records:", original_count)
print("Conflicting rows quarantined:", len(conflicts))
print("Clean records:", len(clean_df))
print("Unique banks:", clean_df["UPI_Remitter_Banks"].nunique())

print("\nClean dataset saved to:", clean_file)
print("Conflicts saved to:", conflict_file)
