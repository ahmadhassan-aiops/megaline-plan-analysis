"""The analysis table: how raw events become one row per customer per month, and an explorer for it."""

import streamlit as st

from lib import data
from lib.ui import cap, footer, header, insight, md, section

STEPS = [
    ("calls_per_month", "Calls per month", "Count of calls for each customer and month.", "calls.groupby(['user_id', 'month']).size()"),
    ("minutes_per_month", "Minutes per month", "Sum of billed minutes (each call rounded up first).",
     "calls.groupby(['user_id', 'month'])['minutes_billed'].sum()"),
    ("messages_per_month", "Texts per month", "Count of text messages for each customer and month.",
     "messages.groupby(['user_id', 'month']).size()"),
    ("internet_per_month", "Data per month", "Sum of MB used in all sessions (sessions are not rounded).",
     "internet.groupby(['user_id', 'month'])['mb_used'].sum()"),
]


def render() -> None:
    m = data.meta()
    um = data.user_month()

    header(
        "Data preparation",
        "The analysis table",
        "Every chart in this app comes from one table with <b>one row per customer per month</b>. It is built in "
        "steps from the raw event logs, the same way as in the notebook.",
    )

    section("Step 1. Four per-month tables")
    md(
        f"The raw logs have one row per event: {m['raw_shapes']['calls'][0]:,} calls, "
        f"{m['raw_shapes']['messages'][0]:,} texts and {m['raw_shapes']['internet'][0]:,} data sessions. "
        "Each is grouped by customer and month:"
    )
    tabs = st.tabs([s[1] for s in STEPS])
    for tab, (name, _, desc, code) in zip(tabs, STEPS):
        with tab:
            cap(desc)
            st.code(code, language="python")
            st.dataframe(data.table(f"step_{name}"), hide_index=True, height=220)

    section("Step 2. Merge them and add the plan")
    miss = m["missing_share_before_fill"]
    md(
        "The four tables are joined on customer and month with an **outer** join, so a month with calls but no "
        "texts still appears. Missing values then mean \"did not use this service that month\" and are set to 0 "
        f"(texts were missing in {miss['messages']:.0%} of months, calls in {miss['calls']:.1%}, data in "
        f"{miss['mb_used']:.1%}). Each row then gets the customer's plan and region from the users table and the "
        "plan's prices from the plans table."
    )
    st.code(
        "user_month = (calls_per_month\n"
        "    .merge(minutes_per_month, on=['user_id', 'month'], how='outer')\n"
        "    .merge(messages_per_month, on=['user_id', 'month'], how='outer')\n"
        "    .merge(internet_per_month, on=['user_id', 'month'], how='outer')\n"
        "    .fillna(0)\n"
        "    .merge(users[['user_id', 'plan', 'region']], on='user_id')\n"
        "    .merge(plans, on='plan'))",
        language="python",
    )

    section("Step 3. Price every month")
    st.code(
        "gb_billed      = ceil(mb_used / 1024)                       # month's total rounded up to whole GB\n"
        "extra_minutes  = max(0, minutes_billed - minutes_included)\n"
        "extra_messages = max(0, messages - messages_included)\n"
        "extra_gb       = max(0, gb_billed - gb_included)\n"
        "revenue = monthly_fee + extra_minutes * usd_per_minute\n"
        "                      + extra_messages * usd_per_message\n"
        "                      + extra_gb * usd_per_gb",
        language="python",
    )

    section("Explore the finished table")
    a, b, c = st.columns(3)
    plan = a.multiselect("Plan", ["surf", "ultimate"], default=["surf", "ultimate"], format_func=data.PLAN_LABEL.get)
    months = b.select_slider("Months", options=list(range(1, 13)), value=(1, 12), format_func=lambda i: data.MONTHS[i - 1])
    over = c.toggle("Only months over the allowance", value=False)
    t = um[um.plan.isin(plan) & um.month.between(*months)]
    if over:
        t = t[t.over_any]
    view = t[["user_id", "month", "plan", "region", "calls", "minutes_billed", "messages", "mb_used", "gb_billed",
              "extra_minutes", "extra_messages", "extra_gb", "fee", "revenue"]]
    st.dataframe(
        view, hide_index=True, height=420,
        column_config={
            "user_id": st.column_config.NumberColumn("Customer", format="%d"),
            "month": st.column_config.NumberColumn("Month", format="%d"),
            "plan": "Plan", "region": "Region", "calls": "Calls",
            "minutes_billed": "Minutes", "messages": "Texts",
            "mb_used": st.column_config.NumberColumn("MB used", format="localized"),
            "gb_billed": "GB billed", "extra_minutes": "Extra min", "extra_messages": "Extra texts",
            "extra_gb": st.column_config.NumberColumn("Extra GB", format="%.0f"),
            "fee": st.column_config.NumberColumn("Fee", format="dollar"),
            "revenue": st.column_config.NumberColumn("Bill", format="dollar"),
        },
    )
    cap(f"{len(view):,} of {len(um):,} customer-months · total billed ${view['revenue'].sum():,.0f}")
    st.download_button("Download this table (CSV)", view.to_csv(index=False).encode(), "megaline_user_month.csv",
                       "text/csv", icon=":material/download:")
    insight(
        "Sort by <b>Bill</b> to find the heaviest Surf users: most of them would pay less on Ultimate, which is the "
        "basis of the upgrade recommendation."
    )

    footer()
