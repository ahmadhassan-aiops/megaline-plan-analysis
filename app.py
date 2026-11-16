"""
Megaline: which prepaid plan brings in more money? An interactive presentation of
Ahmad Hassan's analysis. All data ships with the app (data/, built by build_data.py).
"""

import streamlit as st

st.set_page_config(
    page_title="Megaline plan revenue | Ahmad Hassan",
    page_icon=":material/smartphone:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from lib.ui import inject_css  # noqa: E402
from nav import PAGES  # noqa: E402

inject_css()
st.navigation(PAGES, position="top").run()
