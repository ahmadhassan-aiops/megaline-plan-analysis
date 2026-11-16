"""Landing page: the business question, the answer, and what to do about it."""

import streamlit as st

from lib import data
from lib.ui import cap, finding, footer, header, md


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
    )

    c = st.columns(4)
    c[0].metric("Customers", m["users"], border=True)
    c[1].metric("Customer-months billed", f"{m['user_months']:,}", border=True)
    c[2].metric("Surf, average per month", f"${r['surf']['mean']:.2f}", border=True)
    c[3].metric("Ultimate, average per month", f"${r['ultimate']['mean']:.2f}", border=True)

    st.subheader("Key findings", anchor=False)
    a = st.columns(3)
    finding(
        a[0], f"${r['ultimate']['mean'] - r['surf']['mean']:.2f}", "more per customer each month on Ultimate",
        "Ultimate earns more per customer",
        f"${r['ultimate']['mean']:.2f} against ${r['surf']['mean']:.2f}, and the difference is statistically "
        f"significant (p &lt; 0.001). Ultimate revenue is also steady: almost everyone pays exactly $70.",
        TESTS, "The hypothesis tests",
    )
    finding(
        a[1], f"{r['surf']['over_share']:.0%}", "of Surf months go over the allowance",
        "Surf customers pay for extras, mostly data",
        f"Surf's 15 GB runs out for most people. Extra data alone is <b>{data_share:.0%}</b> of all Surf revenue, "
        "far more than the $20 fees.",
        REVENUE, "Where the money comes from",
    )
    finding(
        a[2], f"{g.loc['surf', 'minutes_billed']:.0f} vs {g.loc['ultimate', 'minutes_billed']:.0f}",
        "average minutes a month, Surf vs Ultimate",
        "Both plans' customers use the same",
        f"Calls, texts and data (about {g['gb_billed'].mean():.0f} GB a month) are nearly identical. Ultimate customers "
        "do not use more; they pay for peace of mind.",
        USAGE, "How customers use their plan",
    )
    b = st.columns(3)
    finding(
        b[0], f"{pricier:.0%}", "of Surf months cost the customer more than $70",
        "Many Surf customers would save on Ultimate",
        "For them, Ultimate is the cheaper plan. Offering the switch costs Megaline a little per month but removes "
        "a reason to leave.",
        REVENUE, "Revenue by plan",
    )
    finding(
        b[1], f"${r['surf']['total'] / 1000:.0f}k vs ${r['ultimate']['total'] / 1000:.0f}k", "total revenue in 2018, Surf vs Ultimate",
        "Surf still brings in more in total",
        f"Two thirds of customers are on Surf ({m['users_by_plan']['surf']} of {m['users']}), so its total is bigger even "
        "though each customer pays less.",
        REVENUE, "Totals and trends",
    )
    finding(
        b[2], "No reliable gap", f"between New York-New Jersey (${t['nynj']['mean_nynj']:.2f}) and elsewhere (${t['nynj']['mean_rest']:.2f})",
        "Region does not change what customers pay",
        f"Counting every month, the $5 gap looks significant (p = {t['nynj']['p']:.3f}). Counting each customer once, "
        f"it is not (p = {t['nynj']['p_customer']:.2f}). The first result came from treating one person's 12 bills as 12 people.",
        TESTS, "The hypothesis tests",
    )

    st.subheader("What I would recommend", anchor=False)
    md(
        "1. **Put more of the advertising budget behind Ultimate.** Each customer is worth more, and the revenue is "
        "predictable.\n"
        "2. **Offer Surf customers who keep paying over $70 an upgrade to Ultimate.** They save money and are less "
        "likely to leave; Megaline keeps a $70 customer instead of risking losing them.\n"
        "3. **Consider a mid-size Surf data add-on.** Data overage is most of Surf's revenue, and the 15 GB allowance "
        "is where customers feel the pinch.\n"
        "4. **Don't price New York-New Jersey differently.** Once each customer is counted once, there is no reliable "
        "difference between regions."
    )
    cap(
        "One year of data from 500 customers. The recommendations are hypotheses to test, for example with a pilot "
        "upgrade offer."
    )
    with st.container(border=True):
        md(
            "**How this was done.** Calls, texts and data sessions were summed per customer and month into "
            "analytical tables, merged, and priced with Megaline's billing rules. Two corrections to the original "
            "notebook (rounding of call minutes and of data) are explained on the methods page."
        )
        st.page_link(METHOD, label="Data & method", icon=":material/arrow_forward:")

    footer()
