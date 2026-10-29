
from pathlib import Path
import sqlite3
import pandas as pd

# ==========================================
# STEP 1: LOCATE OUR FILES
# ==========================================

csv_path = Path(
    "data/processed/remitter_banks_clean.csv"
)

db_path = Path(
    "data/processed/upi_reliability.db"
)

# ==========================================
# STEP 2: READ THE CLEAN DATASET
# ==========================================

df = pd.read_csv(csv_path)

print("Records loaded:", len(df))

# ==========================================
# STEP 3: RENAME COLUMNS
# ==========================================

df = df.rename(columns={
    "UPI_Remitter_Banks": "bank_name",
    "Date": "report_month",
    "Approved_percent": "approved_rate",
    "Bank_Decline_percent": "bank_decline_rate",
    "Technical_Decline_percent": "technical_decline_rate",
    "Debit_Reversal_Success_percent": "reversal_success_rate",
    "Total_Debit_Reversal_Count_In_Million":
        "reversal_count_million",
    "Total_Volume_In_Million": "volume_million",
    "Reversal_Rate_Original": "reversal_rate_original",
    "Reversal_Rate_Rescaled": "reversal_rate_rescaled"
})

# Store dates consistently as YYYY-MM-DD
df["report_month"] = pd.to_datetime(
    df["report_month"]
).dt.strftime("%Y-%m-%d")

# Convert True/False flags to 1/0
df["reversal_rate_rescaled"] = (
    df["reversal_rate_rescaled"].astype(int)
)

# Safety check: one observation per bank and month
if df.duplicated(
    ["bank_name", "report_month"]
).any():
    raise ValueError("Duplicate bank-month records found!")

# ==========================================
# STEP 4: CREATE THE SQLITE DATABASE
# ==========================================

with sqlite3.connect(db_path) as connection:

    df.to_sql(
        name="bank_monthly",
        con=connection,
        if_exists="replace",
        index=False
    )

    count = connection.execute(
        "SELECT COUNT(*) FROM bank_monthly"
    ).fetchone()[0]

    print("Records stored in SQLite:", count)

    # ======================================
    # STEP 5: RUN OUR FIRST SQL QUERY
    # ======================================

    query = """
        SELECT
            bank_name,
            report_month,
            volume_million,
            ROUND(
                technical_decline_rate * 100, 2
            ) AS technical_decline_pct

        FROM bank_monthly

        WHERE report_month = (
            SELECT MAX(report_month)
            FROM bank_monthly
        )

        AND volume_million >= 1

        ORDER BY technical_decline_rate DESC

        LIMIT 5
    """

    results = pd.read_sql_query(
        query, connection
    )

    print("\n=== TOP 5 TECHNICAL DECLINE RATES ===")
    print(results.to_string(index=False))

print("\nDatabase created at:", db_path)
