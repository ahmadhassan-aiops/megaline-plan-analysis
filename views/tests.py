"""Hypothesis tests: Surf vs Ultimate revenue, and New York-New Jersey vs everywhere else."""

import numpy as np
import pandas as pd
import streamlit as st
from scipy import stats

from lib import charts, data
from lib.ui import esc, chart, footer, header, insight, md, note, section


def money(v: float, signed: bool = False) -> str:
    sign = ("+" if v > 0 else "−" if v < 0 else "") if signed else ("−" if v < 0 else "")
    return f"{sign}${abs(v):,.2f}"


def _welch_ci(a: pd.Series, b: pd.Series, level: float = 0.95) -> tuple[float, float, float]:
    """Difference in means (a - b) with a Welch confidence interval."""
    va, vb, na, nb = a.var(ddof=1), b.var(ddof=1), len(a), len(b)
    se = np.sqrt(va / na + vb / nb)
    df = (va / na + vb / nb) ** 2 / ((va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1))
    d = a.mean() - b.mean()
    h = stats.t.ppf(0.5 + level / 2, df) * se
    return d, d - h, d + h


def _test(a: pd.Series, b: pd.Series, names: tuple[str, str], alpha: float, h0: str, h1: str) -> None:
    t = stats.ttest_ind(a, b, equal_var=False)
    mw = stats.mannwhitneyu(a, b)
    d, lo, hi = _welch_ci(a, b, 1 - alpha)
    c = st.columns(4)
    c[0].metric(f"{names[0]} average", f"${a.mean():.2f}", border=True)
    c[1].metric(f"{names[1]} average", f"${b.mean():.2f}", border=True)
    c[2].metric("Difference", money(d, True), border=True,
                help=esc(f"{1 - alpha:.0%} confidence interval: {money(lo, True)} to {money(hi, True)}"))
    c[3].metric("p-value (Welch's t-test)", f"{t.pvalue:.2g}", border=True)
    md(f"- **H₀ (null):** {h0}\n- **H₁ (alternative):** {h1}")
    reject = t.pvalue < alpha
    verdict = (f"<b>Reject H₀.</b> At α = {alpha:g} the difference is statistically significant (p = {t.pvalue:.2g})."
               if reject else
               f"<b>Do not reject H₀.</b> At α = {alpha:g} the data does not show a significant difference "
               f"(p = {t.pvalue:.2g}).")
    insight(
        f"{verdict} The {1 - alpha:.0%} confidence interval for the difference is <b>{money(lo, True)} to {money(hi, True)}</b> "
        f"per customer-month. A rank-based check that does not assume normal data (Mann-Whitney U) gives "
        f"p = {mw.pvalue:.2g}, {'agreeing' if (mw.pvalue < alpha) == reject else 'disagreeing'}."
    )
    chart(charts.boxes({names[0]: a, names[1]: b}, ytitle="Monthly bill ($)", horizontal=True, height=240))


def render() -> None:
    m = data.meta()
    um = data.user_month()

    header(
        "Statistics",
        "Hypothesis tests",
        "Two questions from the business, tested on the monthly bills. Change the significance level to see how "
        "strict the test is, and how each bill is counted to see which conclusion holds up.",
    )
    a, b = st.columns(2)
    alpha = a.select_slider("Significance level (α)", options=[0.01, 0.05, 0.10], value=0.05, key="alpha",
                            help="The chance of calling a difference real when it is just noise that you accept.")
    unit = b.segmented_control(
        "Count each", ["Customer-month", "Customer"], default="Customer-month", key="unit",
        help="Customer-month: every monthly bill is one observation (the original approach). "
             "Customer: each customer's average bill is one observation, so heavy users with 12 months "
             "don't count 12 times.",
    ) or "Customer-month"
    if unit == "Customer":
        um = um.groupby(["user_id", "plan", "nynj"], as_index=False)["revenue"].mean()

    section("1. Do Surf and Ultimate customers bring in different revenue?")
    _test(
        um.loc[um.plan == "ultimate", "revenue"], um.loc[um.plan == "surf", "revenue"], ("Ultimate", "Surf"), alpha,
        "Average monthly revenue is the same for Ultimate and Surf customers.",
        "Average monthly revenue differs between the plans.",
    )

    section("2. Do customers in New York-New Jersey bring in different revenue from the rest?")
    _test(
        um.loc[um.nynj, "revenue"], um.loc[~um.nynj, "revenue"], ("NY-NJ", "Other regions"), alpha,
        "Average monthly revenue is the same in the New York-Newark-Jersey City area and elsewhere.",
        "Average monthly revenue differs between the New York-New Jersey area and other regions.",
    )

    t = m["tests"]
    section("Why these tests")
    md(
        "- **Welch's t-test** compares two averages without assuming the groups have the same spread. That matters "
        "here: Surf bills vary about five times more than Ultimate bills.\n"
        "- The groups are independent (different customers), and with hundreds of customer-months per group the "
        "average is reliable even though bills are skewed. The **Mann-Whitney U** test is shown as a check that "
        "makes no assumption about the shape of the data.\n"
        "- **Months from the same customer are not independent.** A customer contributes up to 12 bills, so "
        "counting every month treats one person as up to 12 observations. Switch *Count each* to **Customer** to "
        "test each customer's average bill instead."
    )
    insight(
        "<b>The plan difference is robust</b>: it is highly significant either way. <b>The New York-New Jersey "
        "difference is not</b>: it is significant only when every month is counted separately "
        f"(p = {t['nynj']['p']:.3f}); per customer, p = {t['nynj']['p_customer']:.2f}. The honest conclusion is that this data gives "
        "no reliable evidence that the region pays differently."
    )
    note(
        "The first version of the analysis counted every month and reached both conclusions with slightly different numbers "
        f"(plans: p = {t['plans']['p_notebook']:.1g}; NY-NJ: p = {t['nynj']['p_notebook']:.3f}), because its bills "
        "rounded call minutes down and charged data per MB. With Megaline's real billing rules the plan result "
        "holds; the regional result does not survive counting each customer once."
    )

    footer()
