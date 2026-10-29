
from pathlib import Path
import sqlite3

import pandas as pd
import pytest


# Locate our database
DB_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "processed"
    / "upi_reliability.db"
)


# A helper function to read our data
def load_data():
    assert DB_PATH.exists(), "Database does not exist"

    with sqlite3.connect(DB_PATH) as connection:
        df = pd.read_sql_query(
            "SELECT * FROM bank_monthly",
            connection
        )

    return df


# TEST 1: Verify database record count
def test_record_count():
    df = load_data()

    assert len(df) == 1744


# TEST 2: Verify unique bank-month records
def test_no_duplicate_bank_months():
    df = load_data()

    duplicates = df.duplicated(
        ["bank_name", "report_month"]
    )

    assert duplicates.sum() == 0


# TEST 3: Check percentage values
def test_percentage_ranges():
    df = load_data()

    columns = [
        "approved_rate",
        "bank_decline_rate",
        "technical_decline_rate",
        "reversal_success_rate"
    ]

    for column in columns:
        assert df[column].notna().all()
        assert df[column].between(0, 1).all()


# TEST 4: Check November 2024 KPIs
def test_november_2024_metrics():
    df = load_data()

    monthly = df[
        (df["report_month"] == "2024-11-01")
        & (df["volume_million"] >= 1)
    ]

    total_volume = monthly["volume_million"].sum()

    weighted_approval = (
        (
            monthly["approved_rate"]
            * monthly["volume_million"]
        ).sum()
        / total_volume
        * 100
    )

    weighted_td = (
        (
            monthly["technical_decline_rate"]
            * monthly["volume_million"]
        ).sum()
        / total_volume
        * 100
    )

    assert len(monthly) == 50

    assert total_volume == pytest.approx(
        16219.87, abs=0.01
    )

    assert weighted_approval == pytest.approx(
        92.16, abs=0.01
    )

    assert weighted_td == pytest.approx(
        0.47, abs=0.01
    )


# TEST 5: Check review flag count
def test_reliability_flags():
    df = load_data()

    monthly = df[
        (df["report_month"] == "2024-11-01")
        & (df["volume_million"] >= 1)
    ]

    flagged = (
        monthly["technical_decline_rate"] >= 0.03
    )

    assert flagged.sum() == 5
