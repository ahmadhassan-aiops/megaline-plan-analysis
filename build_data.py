"""
Offline build step: raw Megaline CSVs (about 9 MB) -> the small tables the app ships with.

    python build_data.py "W:/Portfolio Projects/1. Data-analysis-with-python-Projects/Megaline Analysis"

It reproduces the notebook's pipeline of analytical dataframes:

    calls, messages, internet (one row per event)
      -> calls_per_month, minutes_per_month, messages_per_month, internet_per_month (one row per user and month)
      -> user_month (the four tables merged, with the user's plan)
      -> monthly revenue per user

and applies Megaline's billing rules:
  * every call is rounded UP to the next whole minute (a 2.3 min call bills as 3);
  * web sessions are not rounded; the month's total is rounded UP to whole GB, and extra data is charged per GB;
  * a month with no calls/texts/data for a user counts as 0 of that service.

The notebook's original revenue (calls rounded down, data billed per MB) is kept as `revenue_notebook`
for reference.
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

DEFAULT_RAW = Path("W:/Portfolio Projects/1. Data-analysis-with-python-Projects/Megaline Analysis")
OUT = Path(__file__).parent / "data"
NYNJ = "NY-NJ-PA MSA"


def main(raw: Path) -> None:
    OUT.mkdir(exist_ok=True)
    calls = pd.read_csv(raw / "megaline_calls.csv", parse_dates=["call_date"])
    internet = pd.read_csv(raw / "megaline_internet.csv", parse_dates=["session_date"])
    messages = pd.read_csv(raw / "megaline_messages.csv", parse_dates=["message_date"])
    plans = pd.read_csv(raw / "megaline_plans.csv")
    users = pd.read_csv(raw / "megaline_users.csv", parse_dates=["reg_date", "churn_date"])

    raw_shapes = {n: list(d.shape) for n, d in
                  {"calls": calls, "internet": internet, "messages": messages, "plans": plans, "users": users}.items()}

    # ── Users: no names in the app; split "City, ST MSA" into city and region ──
    users = users.drop(columns=["first_name", "last_name"])
    parts = users["city"].str.split(",", n=1, expand=True)
    users["city"] = parts[0].str.strip()
    users["region"] = parts[1].str.strip()
    users["nynj"] = users["region"] == NYNJ

    # ── Event tables ─────────────────────────────────────────────────────────
    calls["month"] = calls["call_date"].dt.month
    calls["minutes_billed"] = np.ceil(calls["duration"]).astype(int)        # Megaline rule
    calls["minutes_notebook"] = calls["duration"].astype(int)               # notebook: truncated
    zero_calls = int((calls["duration"] == 0).sum())
    internet["month"] = internet["session_date"].dt.month
    internet["mb_notebook"] = np.ceil(internet["mb_used"])                 # notebook: each session rounded up
    messages["month"] = messages["message_date"].dt.month

    # ── The analytical dataframes (one row per user and month) ──────────────
    calls_per_month = calls.groupby(["user_id", "month"]).size().rename("calls").reset_index()
    minutes_per_month = (calls.groupby(["user_id", "month"])[["minutes_billed", "minutes_notebook"]].sum()
                         .reset_index())
    messages_per_month = messages.groupby(["user_id", "month"]).size().rename("messages").reset_index()
    internet_per_month = internet.groupby(["user_id", "month"])[["mb_used", "mb_notebook"]].sum().reset_index()
    for name, t in {"calls_per_month": calls_per_month, "minutes_per_month": minutes_per_month,
                    "messages_per_month": messages_per_month, "internet_per_month": internet_per_month}.items():
        t.head(200).to_parquet(OUT / f"step_{name}.parquet", index=False)

    um = (calls_per_month
          .merge(minutes_per_month, on=["user_id", "month"], how="outer")
          .merge(messages_per_month, on=["user_id", "month"], how="outer")
          .merge(internet_per_month, on=["user_id", "month"], how="outer"))
    missing_share = um[["calls", "messages", "mb_used"]].isna().mean().round(4).to_dict()
    um = um.fillna(0)
    um = um.merge(users[["user_id", "plan", "region", "nynj", "age"]], on="user_id", how="left")
    um = um.merge(plans.rename(columns={"plan_name": "plan"}), on="plan", how="left")

    um["gb_billed"] = np.ceil(um["mb_used"] / 1024).astype(int)              # Megaline rule
    gb_incl = um["mb_per_month_included"] / 1024
    um["extra_minutes"] = (um["minutes_billed"] - um["minutes_included"]).clip(lower=0)
    um["extra_messages"] = (um["messages"] - um["messages_included"]).clip(lower=0)
    um["extra_gb"] = (um["gb_billed"] - gb_incl).clip(lower=0)
    um["fee"] = um["usd_monthly_pay"].astype(float)
    um["over_minutes_usd"] = um["extra_minutes"] * um["usd_per_minute"]
    um["over_messages_usd"] = um["extra_messages"] * um["usd_per_message"]
    um["over_data_usd"] = um["extra_gb"] * um["usd_per_gb"]
    um["revenue"] = um["fee"] + um["over_minutes_usd"] + um["over_messages_usd"] + um["over_data_usd"]
    # The notebook's version, for comparison only
    um["revenue_notebook"] = (
        um["fee"]
        + (um["minutes_notebook"] - um["minutes_included"]).clip(lower=0) * um["usd_per_minute"]
        + um["extra_messages"] * um["usd_per_message"]
        + ((um["mb_notebook"] - um["mb_per_month_included"]) / 1024).clip(lower=0) * um["usd_per_gb"]
    )
    um["over_any"] = (um["revenue"] > um["fee"])

    keep = ["user_id", "month", "plan", "region", "nynj", "age", "calls", "minutes_billed", "messages", "mb_used",
            "gb_billed", "extra_minutes", "extra_messages", "extra_gb", "fee", "over_minutes_usd",
            "over_messages_usd", "over_data_usd", "revenue", "revenue_notebook", "over_any"]
    um = um[keep].sort_values(["user_id", "month"]).reset_index(drop=True)
    for c in ["calls", "minutes_billed", "messages", "extra_minutes", "extra_messages"]:
        um[c] = um[c].astype(int)
    um.to_parquet(OUT / "user_month.parquet", index=False)

    users[["user_id", "age", "city", "region", "plan", "reg_date", "churn_date"]].to_parquet(OUT / "users.parquet", index=False)
    plans.to_parquet(OUT / "plans.parquet", index=False)
    (calls.groupby(["month"]).size().rename("calls").reset_index()
     .to_parquet(OUT / "calls_by_month.parquet", index=False))
    # Per-call minutes for the call-length chart (small: one int per call)
    calls.merge(users[["user_id", "plan"]], on="user_id")[["plan", "minutes_billed"]].astype({"minutes_billed": "int16"}) \
        .to_parquet(OUT / "call_minutes.parquet", index=False)
    for name, df in {"calls": calls[["id", "user_id", "call_date", "duration"]],
                     "internet": internet[["id", "user_id", "session_date", "mb_used"]],
                     "messages": messages[["id", "user_id", "message_date"]],
                     "users": users[["user_id", "age", "city", "region", "plan", "reg_date", "churn_date"]],
                     "plans": plans}.items():
        df.sample(min(50, len(df)), random_state=7).to_parquet(OUT / f"sample_{name}.parquet", index=False)

    # ── Headline numbers and tests ───────────────────────────────────────────
    s, u = um[um.plan == "surf"], um[um.plan == "ultimate"]
    t1 = stats.ttest_ind(u["revenue"], s["revenue"], equal_var=False)
    ny, rest = um[um.nynj], um[~um.nynj]
    t2 = stats.ttest_ind(ny["revenue"], rest["revenue"], equal_var=False)
    nb1 = stats.ttest_ind(u["revenue_notebook"], s["revenue_notebook"], equal_var=False)
    nb2 = stats.ttest_ind(ny["revenue_notebook"], rest["revenue_notebook"], equal_var=False)
    cust = um.groupby(["user_id", "plan", "nynj"], as_index=False)["revenue"].mean()
    c1 = stats.ttest_ind(cust.loc[cust.plan == "ultimate", "revenue"], cust.loc[cust.plan == "surf", "revenue"],
                         equal_var=False)
    c2 = stats.ttest_ind(cust.loc[cust.nynj, "revenue"], cust.loc[~cust.nynj, "revenue"], equal_var=False)
    meta = {
        "built": date.today().isoformat(),
        "raw_shapes": raw_shapes,
        "users": int(len(users)),
        "users_by_plan": users["plan"].value_counts().to_dict(),
        "user_months": int(len(um)),
        "user_months_by_plan": um["plan"].value_counts().to_dict(),
        "missing_share_before_fill": missing_share,
        "zero_length_calls": zero_calls,
        "zero_length_calls_share": zero_calls / len(calls),
        "churned_users": int(users["churn_date"].notna().sum()),
        "revenue": {p: {"mean": float(g["revenue"].mean()), "median": float(g["revenue"].median()),
                        "total": float(g["revenue"].sum()), "over_share": float(g["over_any"].mean()),
                        "mean_notebook": float(g["revenue_notebook"].mean())}
                    for p, g in um.groupby("plan")},
        "tests": {
            "plans": {"t": float(t1.statistic), "p": float(t1.pvalue), "t_notebook": float(nb1.statistic),
                      "p_notebook": float(nb1.pvalue), "p_customer": float(c1.pvalue)},
            "nynj": {"t": float(t2.statistic), "p": float(t2.pvalue), "t_notebook": float(nb2.statistic),
                     "p_notebook": float(nb2.pvalue), "p_customer": float(c2.pvalue), "mean_nynj": float(ny["revenue"].mean()),
                     "mean_rest": float(rest["revenue"].mean()), "n_nynj": int(len(ny)), "n_rest": int(len(rest))},
        },
    }
    (OUT / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    total = sum(p.stat().st_size for p in OUT.iterdir())
    print(f"Wrote {len(list(OUT.iterdir()))} files ({total / 1e6:.2f} MB)")
    print(json.dumps({k: v for k, v in meta.items() if k != "raw_shapes"}, indent=2))


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_RAW)
