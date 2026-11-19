"""Data & method: source tables, cleaning and enrichment, billing rules, limits."""

import pandas as pd
import streamlit as st

from lib import data
from lib.site import NOTEBOOK_URL
from lib.ui import footer, header, md, section


def render() -> None:
    m = data.meta()
    rs = m["raw_shapes"]
    r = m["revenue"]

    header(
        "Data & method",
        "How the analysis was done",
        "The data, the preparation steps, the billing rules and the limits of the "
        f'study. The full Python work is in the <a href="{NOTEBOOK_URL}" target="_blank">notebook</a>.',
    )

    section("The data")
    md(
        "Five tables for 500 Megaline customers in 2018. Megaline is a fictional operator used as a training case; "
        "the customers are anonymised, and their names are not used here."
    )
    st.table(pd.DataFrame([
        ("users", "Customer: age, city, plan, sign-up and churn date", *rs["users"]),
        ("calls", "One row per call: date and duration in minutes", *rs["calls"]),
        ("messages", "One row per text message: date", *rs["messages"]),
        ("internet", "One row per data session: date and MB used", *rs["internet"]),
        ("plans", "The two plans' fees, allowances and extra charges", *rs["plans"]),
    ], columns=["Table", "What it holds", "Rows", "Columns"]).assign(Rows=lambda d: d["Rows"].map("{:,}".format)),
        hide_index=True, border="horizontal")
    with st.expander("Look at the raw data (50 random rows per table)"):
        tabs = st.tabs(["Users", "Calls", "Messages", "Internet", "Plans"])
        for tab, name in zip(tabs, ["users", "calls", "messages", "internet", "plans"]):
            with tab:
                st.dataframe(data.table(f"sample_{name}"), hide_index=True, height=300)

    section("Preparation")
    st.table(pd.DataFrame([
        ("Dates", "Text in all date columns", "Converted to dates; the month extracted for grouping"),
        ("City", "\"City, ST MSA\" in one column", "Split into city and region, needed for the regional test"),
        ("Churn date", f"Empty for most customers ({m['churned_users']} churned in 2018)",
         "Kept empty: it means the customer is still active"),
        ("Zero-length calls", f"{m['zero_length_calls']:,} calls ({m['zero_length_calls_share']:.0%}) last 0 minutes",
         "Kept: missed calls are real events and cost nothing"),
        ("Months without a service", "No texts in 21% of customer-months, for example",
         "Set to 0 after merging: the customer simply did not use it"),
        ("Customer names", "First and last name columns", "Dropped: not needed for the analysis"),
    ], columns=["Item", "What was found", "How it was handled"]), hide_index=True, border="horizontal")

    section("Billing rules")
    st.table(pd.DataFrame([
        ("Call minutes", "Each call rounded up to the next whole minute: 2.3 minutes bills as 3"),
        ("Data", "Sessions summed per month; the month's total rounded up to whole GB, extra data charged per GB"),
        ("Texts", "Counted per month against the allowance"),
    ], columns=["Item", "How it is billed"]), hide_index=True, border="horizontal")
    md(
        f"Average monthly bill: **${r['surf']['mean']:.2f}** on Surf and **${r['ultimate']['mean']:.2f}** on Ultimate.\n\n"
        "**Comparing plans fairly.** Surf has twice as many customers as Ultimate, so plan totals mostly reflect "
        "customer numbers. The charts compare the average per customer per month, and the regional hypothesis test "
        "is also run with each customer counted once (see Hypothesis tests)."
    )

    section("Limits of this data")
    md(
        "- **500 customers, one year.** Enough to compare plans, thin for regions: New York-New Jersey has 79 customers.\n"
        "- **Customers choose their plan.** Ultimate customers might differ in ways the data does not show, so "
        "\"moving people to Ultimate\" would not automatically produce the Ultimate average.\n"
        "- **Revenue only counts usage months.** A month with no calls, texts or data at all does not appear, "
        "although the customer would still pay the fee.\n"
        "- **Descriptive, not causal.** The recommendations are hypotheses to test."
    )

    section("How this app is built")
    md(
        "Python, pandas, SciPy and Plotly in a Streamlit app. `build_data.py` reads the five raw CSVs (about 9 MB) "
        "once, builds the analysis table and saves it with a few small summaries as Parquet files (about 0.3 MB) "
        f"that ship with the app. Data built on {m['built']}."
    )

    footer()
