"""Loads the pre-computed tables in data/ (built by build_data.py)."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

DATA = Path(__file__).resolve().parent.parent / "data"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
PLANS = ["surf", "ultimate"]
PLAN_LABEL = {"surf": "Surf", "ultimate": "Ultimate"}


@st.cache_data
def meta() -> dict:
    return json.loads((DATA / "meta.json").read_text(encoding="utf-8"))


@st.cache_data
def table(name: str) -> pd.DataFrame:
    return pd.read_parquet(DATA / f"{name}.parquet")


@st.cache_data
def user_month() -> pd.DataFrame:
    return table("user_month")


@st.cache_data
def plans() -> pd.DataFrame:
    p = table("plans").set_index("plan_name")
    p["gb_per_month_included"] = p["mb_per_month_included"] / 1024
    return p


def by_plan(df: pd.DataFrame, col: str) -> dict[str, pd.Series]:
    """{'Surf': values, 'Ultimate': values} in fixed order, so colours never swap."""
    return {PLAN_LABEL[p]: df.loc[df["plan"] == p, col] for p in PLANS}
