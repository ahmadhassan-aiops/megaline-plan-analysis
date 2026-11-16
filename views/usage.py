"""How customers use their plan: minutes, texts and data per customer per month (notebook Q1-Q4, Internet)."""

import streamlit as st

from lib import charts, data
from lib.ui import chart, footer, header, insight, note, section


def render() -> None:
    um = data.user_month()
    p = data.plans()

    header(
        "Customer behaviour",
        "How customers use their plan",
        "Every figure here is <b>per customer per month</b>. Surf has twice as many customers as Ultimate, so "
        "comparing plan totals would mostly measure the number of customers, not how they behave.",
    )

    service = st.segmented_control(
        "Service", ["Call minutes", "Text messages", "Data (GB)"], default="Call minutes",
        key="service", label_visibility="collapsed",
    ) or "Call minutes"
    col, unit, allow = {
        "Call minutes": ("minutes_billed", " min", "minutes_included"),
        "Text messages": ("messages", " texts", "messages_included"),
        "Data (GB)": ("gb_billed", " GB", "gb_per_month_included"),
    }[service]

    section(f"{service}: the monthly distribution", "How much each customer used in a month, by plan.")
    fig = charts.histograms(data.by_plan(um, col), bins=40, xtitle=f"{service} in a month", unit=unit)
    surf_allow = float(p.loc["surf", allow])
    charts.vline(fig, surf_allow, f"Surf includes {surf_allow:,.0f}{unit}")
    chart(fig, key=f"hist_{col}")
    g = um.groupby("plan")[col]
    over = (um.loc[um.plan == "surf", col] > surf_allow).mean()
    ult_allow = float(p.loc["ultimate", allow])
    over_u = (um.loc[um.plan == "ultimate", col] > ult_allow).mean()
    ult_text = (f"Ultimate's allowance of {ult_allow:,.0f}{unit} is never reached." if over_u == 0 else
                f"Ultimate's {ult_allow:,.0f}{unit} is exceeded in only {over_u:.0%} of months.")
    insight(
        f"The two plans' distributions <b>sit on top of each other</b>: a typical month is "
        f"{g.median()['surf']:,.0f}{unit} on Surf and {g.median()['ultimate']:,.0f}{unit} on Ultimate. "
        f"<b>{over:.0%}</b> of Surf months go past Surf's allowance (dotted line). {ult_text}"
    )

    left, right = st.columns(2, gap="large")
    with left:
        section("Average per customer, month by month", "Q1 and Q2. Do the plans differ through the year?")
        avg = um.groupby(["month", "plan"])[col].mean().unstack()
        chart(charts.lines(
            [data.MONTHS[m - 1] for m in avg.index],
            {data.PLAN_LABEL[c]: avg[c].round(1) for c in data.PLANS},
            hover_fmt=",.1f", unit=unit, ytitle=f"Average {service.lower()} per customer",
        ), key=f"trend_{col}")
    with right:
        section("Spread across customers", "Q3. Mean and variance of monthly usage per plan.")
        stats = um.groupby("plan")[col].agg(["mean", "median", "var", "std"]).rename(index=data.PLAN_LABEL)
        st.dataframe(
            stats.rename(columns={"mean": "Mean", "median": "Median", "var": "Variance", "std": "Std. deviation"}),
            column_config={c: st.column_config.NumberColumn(format="%.1f") for c in ["Mean", "Median", "Variance", "Std. deviation"]},
        )
        chart(charts.boxes(data.by_plan(um, col), ytitle=f"{service} in a month", height=300), key=f"box_{col}")
    insight(
        "Averages climb through the year on both plans, mostly because a customer's <b>first month is a partial "
        "month</b> (they join part-way through it), and early in the year many active customers are new. Month by "
        "month the plans stay close; the spread inside each plan is far larger than the gap between them."
    )

    section("Call lengths", "Each call is billed in whole minutes, rounded up.")
    cm = data.table("call_minutes")
    chart(charts.histograms(data.by_plan(cm, "minutes_billed"), bin_size=1, start=-0.5,
                            xtitle="Billed minutes per call", unit=" min"), key="call_len")
    zero = data.meta()["zero_length_calls_share"]
    insight(
        f"Most calls bill at 1 to 12 minutes, the same on both plans. <b>{zero:.0%}</b> of calls last 0 seconds "
        "(missed or unanswered calls); they are kept and cost nothing."
    )
    note(
        "The first version of the analysis rounded call minutes <b>down</b> (it converted to whole numbers before rounding up), "
        "so every call billed a little short. This app rounds each call <b>up</b>, as Megaline bills."
    )

    footer()
