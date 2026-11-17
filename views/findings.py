"""Landing page: the business question, the answer, and what to do about it."""

import streamlit as st

from lib import charts, data
from lib.ui import cap, finding, footer, header, method_card, recommendations, spotlight_box


def _bill(plan, minutes: int, texts: int, gb: int) -> dict[str, float]:
    """One month's bill under Megaline's rules (minutes and GB already rounded up)."""
    return {
        "Monthly fee": float(plan["usd_monthly_pay"]),
        "Extra data": max(0, gb - plan["gb_per_month_included"]) * plan["usd_per_gb"],
        "Extra minutes": max(0, minutes - plan["minutes_included"]) * plan["usd_per_minute"],
        "Extra texts": max(0, texts - plan["messages_included"]) * plan["usd_per_message"],
    }


def _calculator(um) -> None:
    pl = data.plans()
    box = spotlight_box(
        "Which plan is cheaper for you?",
        "Move the sliders to a month of usage. The bars show what each plan would charge, split into the fee and "
        "the extras. They start at a <b>typical Surf customer</b>: their 15 GB runs out, and data does the rest.",
    )
    with box:
        a, b, c = st.columns(3)
        gb = a.slider("Data (GB, rounded up)", 0, 50, 17, key="calc_gb")
        minutes = b.slider("Call minutes (rounded up)", 0, 1500, 425, step=5, key="calc_min")
        texts = c.slider("Text messages", 0, 300, 24, key="calc_txt")
        bills = {name: _bill(pl.loc[key], minutes, texts, gb) for key, name in data.PLAN_LABEL.items()}
        parts = {k: [round(bills[p][k], 2) for p in bills] for k in bills["Surf"]}
        fig = charts.stacked_bars(list(bills), parts, colors=[charts.QUIET, charts.BLUE, charts.ORANGE, charts.AQUA],
                                  hover_fmt=",.2f", unit="", ytitle="Bill for the month ($)", height=330)
        fig.update_traces(hovertemplate="<b>%{x}</b><br>%{fullData.name}: $%{y:,.2f}<extra></extra>")
        totals = {p: sum(v.values()) for p, v in bills.items()}
        for p, t in totals.items():
            fig.add_annotation(x=p, y=t, text=f"<b>${t:,.2f}</b>", showarrow=False, yshift=14,
                               font=dict(size=15, color=charts.INK))
        fig.update_yaxes(range=[0, max(totals.values()) * 1.18], tickprefix="$")
        left, right = st.columns([3, 2], gap="large", vertical_alignment="center")
        with left:
            st.plotly_chart(fig, theme=None, config=charts.CONFIG, key="calc_fig")
        with right:
            cheap = min(totals, key=totals.get)
            gap = abs(totals["Surf"] - totals["Ultimate"])
            share = ((um.plan == "surf") & (um.revenue > totals["Ultimate"])).sum() / (um.plan == "surf").sum()
            st.metric("Cheaper plan for this month", cheap if gap >= 0.01 else "Same price",
                      delta=f"saves ${gap:,.2f}" if gap >= 0.01 else None, border=True)
            st.metric("Surf months in 2018 that cost more than Ultimate", f"{share:.0%}", border=True,
                      help="Share of real Surf customer-months whose bill was above $70.")


def render() -> None:
    from nav import METHOD, REVENUE, TESTS, USAGE

    m = data.meta()
    um = data.user_month()
    r = m["revenue"]
    s = um[um.plan == "surf"]
    g = um.groupby("plan")[["minutes_billed", "gb_billed"]].mean()
    data_share = s["over_data_usd"].sum() / s["revenue"].sum()
    pricier = (s["revenue"] > 70).mean()
    t = m["tests"]

    header(
        "Data analysis · statistics · Python",
        "Which Megaline plan brings in more money?",
        "Megaline sells two prepaid plans: <b>Surf</b> ($20 a month, pay for extras) and <b>Ultimate</b> ($70, "
        f"generous allowances). Using {m['users']} customers' calls, texts and data for 2018, I worked out what each "
        "customer paid every month and tested which plan earns more, so the commercial team knows where to put its "
        "advertising budget.",
        chips=[("code", "Python, pandas"), ("functions", "SciPy t-tests"), ("payments", "Billing rules"),
               ("calendar_month", "2018, 12 months")],
    )

    c = st.columns(4)
    c[0].metric("Customers", m["users"], border=True)
    c[1].metric("Customer-months billed", f"{m['user_months']:,}", border=True)
    c[2].metric("Surf, average per month", f"${r['surf']['mean']:.2f}", border=True)
    c[3].metric("Ultimate, average per month", f"${r['ultimate']['mean']:.2f}", border=True)

    _calculator(um)

    st.subheader("Key findings", anchor=False)
    a = st.columns(3)
    finding(
        a[0], f"${r['ultimate']['mean'] - r['surf']['mean']:.2f}", "more per customer each month on Ultimate",
        "Ultimate earns more per customer",
        f"${r['ultimate']['mean']:.2f} against ${r['surf']['mean']:.2f}, and the difference is statistically "
        f"significant (p &lt; 0.001). Ultimate revenue is also steady: almost everyone pays exactly $70.",
        TESTS, "The hypothesis tests", card_icon="workspace_premium",
    )
    finding(
        a[1], f"{r['surf']['over_share']:.0%}", "of Surf months go over the allowance",
        "Surf customers pay for extras, mostly data",
        f"Surf's 15 GB runs out for most people. Extra data alone is <b>{data_share:.0%}</b> of all Surf revenue, "
        "far more than the $20 fees.",
        REVENUE, "Where the money comes from", card_icon="data_usage",
    )
    finding(
        a[2], f"{g.loc['surf', 'minutes_billed']:.0f} vs {g.loc['ultimate', 'minutes_billed']:.0f}",
        "average minutes a month, Surf vs Ultimate",
        "Both plans' customers use the same",
        f"Calls, texts and data (about {g['gb_billed'].mean():.0f} GB a month) are nearly identical. Ultimate customers "
        "do not use more; they pay for peace of mind.",
        USAGE, "How customers use their plan", card_icon="equalizer",
    )
    b = st.columns(3)
    finding(
        b[0], f"{pricier:.0%}", "of Surf months cost the customer more than $70",
        "Many Surf customers would save on Ultimate",
        "For them, Ultimate is the cheaper plan. Offering the switch costs Megaline a little per month but removes "
        "a reason to leave.",
        REVENUE, "Revenue by plan", card_icon="swap_vert",
    )
    finding(
        b[1], f"${r['surf']['total'] / 1000:.0f}k vs ${r['ultimate']['total'] / 1000:.0f}k", "total revenue in 2018, Surf vs Ultimate",
        "Surf still brings in more in total",
        f"Two thirds of customers are on Surf ({m['users_by_plan']['surf']} of {m['users']}), so its total is bigger even "
        "though each customer pays less.",
        REVENUE, "Totals and trends", card_icon="account_balance",
    )
    finding(
        b[2], "No reliable gap", f"between New York-New Jersey (${t['nynj']['mean_nynj']:.2f}) and elsewhere (${t['nynj']['mean_rest']:.2f})",
        "Region does not change what customers pay",
        f"Counting every month, the $5 gap looks significant (p = {t['nynj']['p']:.3f}). Counting each customer once, "
        f"it is not (p = {t['nynj']['p_customer']:.2f}). The first result came from treating one person's 12 bills as 12 people.",
        TESTS, "The hypothesis tests", card_icon="map",
    )

    st.subheader("What I would recommend", anchor=False)
    recommendations([
        ("campaign", "Put more of the budget behind Ultimate",
         "Each customer is worth more, and the revenue is predictable."),
        ("upgrade", "Offer heavy Surf users an upgrade",
         "Customers who keep paying over $70 save money on Ultimate and are less likely to leave; Megaline keeps a "
         "$70 customer instead of risking losing them."),
        ("sim_card_download", "Consider a mid-size data add-on",
         "Data overage is most of Surf's revenue, and the <b>15 GB</b> allowance is where customers feel the pinch."),
        ("location_off", "Don't price regions differently",
         "Once each customer is counted once, New York-New Jersey shows no reliable difference."),
    ])
    cap(
        "One year of data from 500 customers. The recommendations are hypotheses to test, for example with a pilot "
        "upgrade offer."
    )
    method_card("<b>How this was done.</b> Calls, texts and data sessions were summed per customer and month into "
                "analytical tables, merged, and priced with Megaline's billing rules. Two corrections to the original "
                "notebook (rounding of call minutes and of data) are explained on the methods page.",
                METHOD, tools=["pandas", "SciPy", "Welch's t-test", "Billing model"])

    footer()
