"""Decompose monthly movement across the eligible bank population."""
from pathlib import Path
import pandas as pd

DATA = Path(__file__).resolve().parent / "data/processed"

def main():
    frame = pd.read_csv(DATA / "remitter_banks_clean.csv").rename(columns={
        "UPI_Remitter_Banks":"Bank", "Date":"Month", "Total_Volume_In_Million":"Volume",
        "Technical_Decline_percent":"Rate"})
    frame.Month = pd.to_datetime(frame.Month)
    below_cutoff = set(zip(frame.loc[frame.Volume < 1, "Bank"], frame.loc[frame.Volume < 1, "Month"]))
    conflicts = pd.read_csv(DATA / "conflicting_bank_months.csv", parse_dates=["Date"])
    quarantined = set(zip(conflicts.UPI_Remitter_Banks, conflicts.Date))
    frame = frame.loc[frame.Volume >= 1, ["Bank","Month","Volume","Rate"]].copy()
    frame["Weight"] = frame.Volume / frame.groupby("Month").Volume.transform("sum")
    prior = frame.copy()
    prior.Month += pd.offsets.MonthBegin(1)
    joined = frame.merge(prior,on=["Month","Bank"],how="outer",suffixes=(""," prior"),indicator=True)
    months = set(frame.Month)
    joined = joined[joined.Month.isin(months) & (joined.Month-pd.offsets.MonthBegin(1)).isin(months)].copy()
    def coverage(row):
        if row["_merge"] == "both":
            return "Both months"
        prior_missing = row["_merge"] == "left_only"
        missing_month = row.Month - pd.offsets.MonthBegin(1) if prior_missing else row.Month
        key = (row.Bank, missing_month)
        reason = "quarantined" if key in quarantined else "below cutoff" if key in below_cutoff else "absent from source"
        return ("Prior month" if prior_missing else "Current month") + " - " + reason

    joined["Coverage"] = joined.apply(coverage, axis=1)
    joined["Rate change pp"] = 100*(joined.Rate-joined["Rate prior"])
    joined["Volume change M"] = joined.Volume.fillna(0)-joined["Volume prior"].fillna(0)
    joined["Contribution pp"] = 100*((joined.Weight*joined.Rate).fillna(0)-(joined["Weight prior"]*joined["Rate prior"]).fillna(0))
    joined["Rate effect pp"] = (joined["Rate change pp"]*(joined.Weight+joined["Weight prior"])/2).fillna(0)
    joined["Mix and coverage pp"] = joined["Contribution pp"]-joined["Rate effect pp"]
    weighted = (frame.Weight*frame.Rate).groupby(frame.Month).sum()
    actual = joined.groupby("Month")["Contribution pp"].sum()
    expected = (weighted-weighted.rename(index=lambda d:d+pd.offsets.MonthBegin(1))).dropna()*100
    assert (actual-expected.loc[actual.index]).abs().max()<1e-9
    joined.drop(columns=["_merge"]).sort_values(["Month","Bank"]).to_csv(DATA/"monthly_drivers.csv",index=False)
    print(len(actual), "monthly comparisons reconciled")
if __name__ == "__main__":
    main()
