
from pathlib import Path
import sqlite3

import pandas as pd
import plotly.express as px
import streamlit as st


# ==========================================
# 1. CONFIGURE THE DASHBOARD
# ==========================================

st.set_page_config(
    page_title="UPI Reliability Intelligence",
    page_icon="📊",
    layout="wide"
)

st.title("UPI Reliability Intelligence")
st.caption(
    "Historical bank performance analysis | "
    "2022–2024 | Third-party NPCI-derived data"
)


# ==========================================
# 2. LOAD OUR SQLITE DATA
# ==========================================

db_path = (
    Path(__file__).resolve().parent
    / "data"
    / "processed"
    / "upi_reliability.db"
)

if not db_path.exists():
    st.error(
        "Database missing. Run build_database.py first."
    )
    st.stop()

with sqlite3.connect(db_path) as connection:
    df = pd.read_sql_query(
        "SELECT * FROM bank_monthly",
        connection
    )

df["report_month"] = pd.to_datetime(
    df["report_month"]
)

df["month_label"] = (
    df["report_month"].dt.strftime("%Y-%m")
)

df["technical_decline_pct"] = (
    df["technical_decline_rate"] * 100
)

df["estimated_declines_million"] = (
    df["volume_million"]
    * df["technical_decline_rate"]
)


# ==========================================
# 3. CREATE SIDEBAR FILTERS
# ==========================================

st.sidebar.header("Analysis Filters")

months = sorted(
    df["month_label"].unique(),
    reverse=True
)

selected_month = st.sidebar.selectbox(
    "Select reporting month",
    months
)

minimum_volume = st.sidebar.slider(
    "Minimum volume (million transactions)",
    min_value=0,
    max_value=100,
    value=1,
    step=1
)

threshold_pct = st.sidebar.slider(
    "Technical decline review threshold (%)",
    min_value=0.0,
    max_value=10.0,
    value=3.0,
    step=0.1
)


# ==========================================
# 4. FILTER THE DATA
# ==========================================

monthly = df[
    (df["month_label"] == selected_month)
    & (df["volume_million"] >= minimum_volume)
].copy()

if monthly.empty:
    st.warning("No banks match these filters.")
    st.stop()

monthly["review_flag"] = (
    monthly["technical_decline_pct"] >= threshold_pct
)


# ==========================================
# 5. CALCULATE FINANCIAL KPIS
# ==========================================

total_volume = monthly["volume_million"].sum()

weighted_approval = (
    (
        monthly["approved_rate"]
        * monthly["volume_million"]
    ).sum()
    / total_volume
    * 100
) if total_volume > 0 else 0

weighted_td = (
    (
        monthly["technical_decline_rate"]
        * monthly["volume_million"]
    ).sum()
    / total_volume
    * 100
) if total_volume > 0 else 0

st.subheader(f"Performance Overview — {selected_month}")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Banks Analyzed",
    len(monthly)
)

col2.metric(
    "Reported Volume",
    f"{total_volume:,.2f}M"
)

col3.metric(
    "Weighted Approval",
    f"{weighted_approval:.2f}%"
)

col4.metric(
    "Weighted Technical Declines",
    f"{weighted_td:.2f}%"
)

st.caption(
    "Metrics cover selected remitter-bank observations "
    "and are not nationwide UPI statistics."
)


# ==========================================
# 6. BANK RELIABILITY RANKINGS
# ==========================================

st.subheader("Bank Reliability Rankings")

left, right = st.columns(2)

top_rate = monthly.nlargest(
    10, "technical_decline_pct"
).sort_values("technical_decline_pct")

fig_rate = px.bar(
    top_rate,
    x="technical_decline_pct",
    y="bank_name",
    orientation="h",
    title="Highest Technical Decline Rates",
    labels={
        "technical_decline_pct": "Technical Declines (%)",
        "bank_name": "Bank"
    }
)

left.plotly_chart(fig_rate, width="stretch")

top_impact = monthly.nlargest(
    10, "estimated_declines_million"
).sort_values("estimated_declines_million")

fig_impact = px.bar(
    top_impact,
    x="estimated_declines_million",
    y="bank_name",
    orientation="h",
    title="Estimated Technical Decline Volume",
    labels={
        "estimated_declines_million":
            "Estimated Declines (Million)",
        "bank_name": "Bank"
    }
)

right.plotly_chart(fig_impact, width="stretch")


# ==========================================
# 7. HISTORICAL BANK TREND
# ==========================================

st.subheader("Historical Bank Performance")

selected_bank = st.selectbox(
    "Choose a bank to investigate",
    sorted(df["bank_name"].unique())
)

history = df[
    df["bank_name"] == selected_bank
].sort_values("report_month")

fig_history = px.line(
    history,
    x="report_month",
    y="technical_decline_pct",
    markers=True,
    title=f"Technical Decline Trend — {selected_bank}",
    labels={
        "report_month": "Reporting Month",
        "technical_decline_pct": "Technical Declines (%)"
    }
)

st.plotly_chart(fig_history, width="stretch")

st.caption(
    "Missing bank-month observations are not estimated."
)


# ==========================================
# 8. INVESTIGATION FLAGS
# ==========================================

st.subheader("Banks Flagged for Review")

flagged = monthly[
    monthly["review_flag"]
].sort_values(
    "technical_decline_pct",
    ascending=False
)

st.write(
    f"{len(flagged)} banks exceed or equal "
    f"the selected {threshold_pct:.1f}% threshold."
)

if flagged.empty:
    st.success("No banks exceed the chosen threshold.")
else:
    st.dataframe(
        flagged[
            [
                "bank_name",
                "technical_decline_pct",
                "volume_million",
                "estimated_declines_million"
            ]
        ].rename(columns={
            "bank_name": "Bank",
            "technical_decline_pct": "Technical Declines (%)",
            "volume_million": "Reported Volume (M)",
            "estimated_declines_million":
                "Estimated Technical Declines (M)"
        }).round(2),
        hide_index=True
    )

st.info(
    "Review flags are rule-based indicators, "
    "not confirmed payment outages."
)


# ==========================================
# 9. COMPLETE DATA TABLE
# ==========================================

with st.expander("View all selected bank records"):
    st.dataframe(
        monthly.sort_values(
            "technical_decline_pct",
            ascending=False
        ),
        hide_index=True
    )


# ==========================================
# 10. DATA LIMITATIONS
# ==========================================

st.divider()

st.caption(
    "Source: historical third-party NPCI-derived "
    "remitter-bank dataset (2022–2024). "
    "Six conflicting bank-month rows were quarantined. "
    "48 August 2022 reversal rates were provisionally "
    "rescaled. Results are not real-time, and estimated "
    "decline counts use rounded source figures."
)
