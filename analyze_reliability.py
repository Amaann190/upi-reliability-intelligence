
from pathlib import Path
import sqlite3
import pandas as pd

# ==========================================
# STEP 1: CONNECT TO THE DATABASE
# ==========================================

db_path = Path("data/processed/upi_reliability.db")

if not db_path.exists():
    raise FileNotFoundError("Run build_database.py first.")

with sqlite3.connect(db_path) as connection:

    # Find the latest month in our database.
    latest_month = connection.execute(
        "SELECT MAX(report_month) FROM bank_monthly"
    ).fetchone()[0]

    # Read records for that month.
    # Include only banks with at least 1 million
    # transactions in the selected month.
    query = """
        SELECT
            bank_name,
            report_month,
            volume_million,
            approved_rate,
            bank_decline_rate,
            technical_decline_rate

        FROM bank_monthly

        WHERE report_month = ?
          AND volume_million >= 1
    """

    df = pd.read_sql_query(
        query,
        connection,
        params=(latest_month,)
    )

if df.empty:
    raise ValueError("No eligible bank records found.")

print("\n=== ANALYSIS PERIOD ===")
print("Month:", latest_month)
print("Banks analyzed:", len(df))


# ==========================================
# STEP 2: CALCULATE WEIGHTED RATES
# ==========================================

total_volume = df["volume_million"].sum()

weighted_approval = (
    (df["approved_rate"] * df["volume_million"]).sum()
    / total_volume
)

weighted_technical_decline = (
    (
        df["technical_decline_rate"]
        * df["volume_million"]
    ).sum()
    / total_volume
)

print("\n=== AGGREGATED PERFORMANCE ===")
print("Total eligible volume (million):",
      round(total_volume, 2))

print("Weighted approval rate:",
      round(weighted_approval * 100, 2), "%")

print("Weighted technical decline rate:",
      round(weighted_technical_decline * 100, 2), "%")


# ==========================================
# STEP 3: ESTIMATE TECHNICAL DECLINE VOLUME
# ==========================================

df["estimated_technical_declines_million"] = (
    df["volume_million"]
    * df["technical_decline_rate"]
)

df["technical_decline_pct"] = (
    df["technical_decline_rate"] * 100
)


# ==========================================
# STEP 4: FLAG BANKS FOR INVESTIGATION
# ==========================================

# Illustrative analyst review threshold: 3%.
# This is not an official NPCI standard.
review_threshold = 0.03

df["review_flag"] = (
    df["technical_decline_rate"] >= review_threshold
)


# ==========================================
# STEP 5: RANK BANKS BY FAILURE RATE
# ==========================================

print("\n=== TOP 5 BY TECHNICAL DECLINE RATE ===")

rate_ranking = df.sort_values(
    "technical_decline_rate",
    ascending=False
)

print(
    rate_ranking[
        [
            "bank_name",
            "technical_decline_pct",
            "volume_million"
        ]
    ].head(5).round(2).to_string(index=False)
)


# ==========================================
# STEP 6: RANK BY ESTIMATED DECLINE COUNT
# ==========================================

print("\n=== TOP 5 BY ESTIMATED TECHNICAL DECLINES ===")

volume_ranking = df.sort_values(
    "estimated_technical_declines_million",
    ascending=False
)

print(
    volume_ranking[
        [
            "bank_name",
            "estimated_technical_declines_million",
            "technical_decline_pct"
        ]
    ].head(5).round(2).to_string(index=False)
)


# ==========================================
# STEP 7: EXPORT DASHBOARD DATA
# ==========================================

output = Path("data/processed/reliability_metrics.csv")
output.parent.mkdir(parents=True, exist_ok=True)

df.to_csv(output, index=False)

print("\nBanks flagged for review:",
      int(df["review_flag"].sum()))

print("Analytics exported to:", output)
