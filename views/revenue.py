"""Revenue: what each plan earns per customer, where it comes from, and totals over the year."""

import streamlit as st

from lib import charts, data
from lib.ui import cap, chart, footer, header, insight, section


def render() -> None:
    m = data.meta()
    um = data.user_month()
    r = m["revenue"]

    header(
        "Revenue",
        "Where the money comes from",
        "Each customer's bill for a month is the plan fee plus any extra minutes, texts or gigabytes beyond the "
        "allowance. Surf: $20 for 500 minutes, 50 texts, 15 GB, then $0.03 a minute, $0.03 a text, $10 a GB. "
        "Ultimate: $70 for 3,000 minutes, 1,000 texts, 30 GB, then $0.01, $0.01 and $7.",
    )

    c = st.columns(4)
    c[0].metric("Surf, average month", f"${r['surf']['mean']:.2f}", border=True)
    c[1].metric("Surf, median month", f"${r['surf']['median']:.2f}", border=True)
    c[2].metric("Ultimate, average month", f"${r['ultimate']['mean']:.2f}", border=True)
    c[3].metric("Ultimate, median month", f"${r['ultimate']['median']:.2f}", border=True)

    section("What customers paid in a month", "Distribution of monthly bills by plan.")
    fig = charts.histograms(data.by_plan(um, "revenue"), bin_size=10, start=0, xtitle="Monthly bill ($)", unit="")
    charts.vline(fig, 70, "Ultimate fee $70")
    fig.update_xaxes(range=[0, 260], tickprefix="$")
    chart(fig)
    cap(f"Bills above $260 ({(um['revenue'] > 260).sum()} months, up to ${um['revenue'].max():,.0f}) are off the right edge.")
    s = um[um.plan == "surf"]
    insight(
        f"Ultimate bills are almost all exactly $70. Surf bills <b>spread from $20 to several hundred dollars</b>: half of Surf "
        f"months cost ${r['surf']['median']:.0f} or less, but a long tail of heavy data users pushes the average to "
        f"${r['surf']['mean']:.0f}. <b>{(s['revenue'] > 70).mean():.0%}</b> of Surf months cost more than Ultimate would have."
    )

    left, right = st.columns(2, gap="large")
    with left:
        section("Surf revenue by source", "Share of all Surf revenue in 2018.")
        parts = {
            "Monthly fees": s["fee"].sum(), "Extra data": s["over_data_usd"].sum(),
            "Extra minutes": s["over_minutes_usd"].sum(), "Extra texts": s["over_messages_usd"].sum(),
        }
        tot = sum(parts.values())
        names = list(parts)
        vals = [v / tot for v in parts.values()]
        chart(charts.bars(
            names, vals, horizontal=True, highlight=[n == "Extra data" for n in names],
            customdata=[[v] for v in parts.values()],
            hover="<b>%{y}</b><br>%{x:.0%} of Surf revenue ($%{customdata[0]:,.0f})",
            text=[f"{v:.0%}" for v in vals],
        ).update_xaxes(tickformat=".0%", range=[0, 0.8]))
        insight(
            f"Extra data is <b>{parts['Extra data'] / tot:.0%}</b> of Surf revenue, twice the fees. Extra minutes and "
            "texts barely matter."
        )
    with right:
        section("Average bill through the year", "Per customer, by month.")
        avg = um.groupby(["month", "plan"])["revenue"].mean().unstack()
        chart(charts.lines(
            [data.MONTHS[i - 1] for i in avg.index], {data.PLAN_LABEL[p]: avg[p].round(2) for p in data.PLANS},
            hover_fmt="$,.2f", ytitle="Average monthly bill ($)",
        ).update_yaxes(tickprefix="$"))
        insight(
            "Ultimate stays flat at about $70-75. Surf climbs as the year goes on and usage grows, reaching "
            f"${avg.loc[12, 'surf']:.0f} in December, close to Ultimate."
        )

    section("Total revenue", "All bills in 2018, by plan.")
    tot_m = um.groupby(["month", "plan"])["revenue"].sum().unstack()
    chart(charts.grouped_bars(
        [data.MONTHS[i - 1] for i in tot_m.index], {data.PLAN_LABEL[p]: tot_m[p].round(0) for p in data.PLANS},
        hover_fmt="$,.0f", ytitle="Revenue in the month ($)",
    ).update_yaxes(tickprefix="$"))
    insight(
        f"Over the year Surf brought in <b>${r['surf']['total']:,.0f}</b> and Ultimate <b>${r['ultimate']['total']:,.0f}</b>. "
        f"Surf's total is larger only because it has {m['users_by_plan']['surf']} customers against "
        f"{m['users_by_plan']['ultimate']}; per customer, Ultimate is worth more."
    )

    footer()
