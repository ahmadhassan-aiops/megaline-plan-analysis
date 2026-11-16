"""Page registry, shared by app.py and pages that link to other pages."""

import streamlit as st

from views import findings, method, revenue, table, tests, usage

FINDINGS = st.Page(findings.render, title="Key findings", icon=":material/insights:", url_path="findings", default=True)
USAGE = st.Page(usage.render, title="How customers use their plan", icon=":material/data_usage:", url_path="usage")
REVENUE = st.Page(revenue.render, title="Revenue", icon=":material/payments:", url_path="revenue")
TESTS = st.Page(tests.render, title="Hypothesis tests", icon=":material/science:", url_path="tests")
TABLE = st.Page(table.render, title="The analysis table", icon=":material/table_view:", url_path="table")
METHOD = st.Page(method.render, title="Data & method", icon=":material/dataset:", url_path="method")

PAGES = [FINDINGS, USAGE, REVENUE, TESTS, TABLE, METHOD]
