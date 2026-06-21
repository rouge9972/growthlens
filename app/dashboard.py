"""
app/dashboard.py
================
GrowthLens dashboard (Streamlit). Run with:

    streamlit run app/dashboard.py

Tabs:
    1. Universe   — ranked, filterable table of all scored companies
    2. Company    — single-company profile with score-attribution chart
    3. Sectors    — sector heatmap of mean readiness by pillar
    4. Macro      — ECB policy-rate overlay (live if online)

Deploys free on Streamlit Community Cloud (see docs/setup_guide.md).
"""
from __future__ import annotations

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from growthlens import config as C
from growthlens.ingestion.synthetic import generate_companies
from growthlens.cleaning.normalize import clean_companies
from growthlens.scoring.ge_readiness import score_companies, explain_score, PILLAR_FUNCS
from growthlens.ingestion.macro_ecb import fetch_policy_rate

st.set_page_config(page_title="GrowthLens", page_icon="📈", layout="wide")


@st.cache_data(show_spinner=False)
def load_scored(n: int, seed: int) -> pd.DataFrame:
    cfg = C.load_scoring_config()
    raw = generate_companies(n=n, seed=seed)
    return score_companies(clean_companies(raw), cfg)


cfg = C.load_scoring_config()

# ---- Sidebar controls ------------------------------------------------------
st.sidebar.title("GrowthLens")
st.sidebar.caption("European growth-stage market intelligence")
n = st.sidebar.slider("Universe size", 50, 500, 200, step=50)
seed = st.sidebar.number_input("Seed", value=42, step=1)
st.sidebar.markdown("---")
st.sidebar.info("Data is **synthetic** unless live connectors are configured. "
                "See the methodology white paper in `docs/`.")

scored = load_scored(n, seed)

tab_uni, tab_co, tab_sect, tab_macro = st.tabs(
    ["🏆 Universe", "🔎 Company", "🗺️ Sectors", "🌍 Macro"]
)

# ---- Tab 1: Universe -------------------------------------------------------
with tab_uni:
    st.subheader("Ranked universe by GE Readiness Score")
    verticals = st.multiselect("Filter verticals", sorted(scored["vertical"].unique()))
    countries = st.multiselect("Filter countries", sorted(scored["country"].unique()))
    view = scored.copy()
    if verticals:
        view = view[view["vertical"].isin(verticals)]
    if countries:
        view = view[view["country"].isin(countries)]

    c1, c2, c3 = st.columns(3)
    c1.metric("Companies", len(view))
    c2.metric("Tier 1 (≥80)", int((view["ge_readiness_score"] >= 80).sum()))
    c3.metric("Median GRS", f"{view['ge_readiness_score'].median():.1f}")

    st.dataframe(
        view[["rank", "name", "vertical", "country", "last_round_stage",
              "months_since_last_round", "ge_readiness_score", "tier"]],
        use_container_width=True, hide_index=True,
    )

# ---- Tab 2: Company profile ------------------------------------------------
with tab_co:
    st.subheader("Company profile")
    pick = st.selectbox("Choose a company", scored["name"].tolist())
    row = scored[scored["name"] == pick].iloc[0]

    a, b, c, d = st.columns(4)
    a.metric("GE Readiness", f"{row['ge_readiness_score']:.1f}")
    b.metric("Rank", f"#{int(row['rank'])}")
    c.metric("Rev growth YoY", f"{row['rev_growth_yoy_pct']:.0f}%")
    d.metric("Months since round", int(row["months_since_last_round"]))

    attribution = explain_score(row, cfg)
    fig = px.bar(
        attribution, x="points", y="pillar", orientation="h",
        title="Score attribution by pillar (points out of 100)",
        text="points",
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=380)
    st.plotly_chart(fig, use_container_width=True)

    st.caption(f"{row['vertical']} · {row['city']}, {row['country']} · "
               f"founded {int(row['founded_year'])} · {row['tier']}")

# ---- Tab 3: Sector heatmap -------------------------------------------------
with tab_sect:
    st.subheader("Sector readiness heatmap (mean pillar sub-score)")
    pillar_cols = [f"pillar_{p}" for p in PILLAR_FUNCS]
    heat = scored.groupby("vertical")[pillar_cols].mean().round(2)
    heat.columns = [c.replace("pillar_", "") for c in heat.columns]
    fig = go.Figure(
        data=go.Heatmap(
            z=heat.values, x=heat.columns, y=heat.index,
            colorscale="Viridis", zmin=0, zmax=1,
            text=heat.values, texttemplate="%{text}",
        )
    )
    fig.update_layout(height=420)
    st.plotly_chart(fig, use_container_width=True)

# ---- Tab 4: Macro overlay --------------------------------------------------
with tab_macro:
    st.subheader("Macro overlay — ECB policy rate")
    with st.spinner("Fetching ECB data (live)…"):
        macro = fetch_policy_rate()
    if macro is None or macro.empty:
        st.warning("ECB data unavailable (offline). The pipeline still runs fully on synthetic data.")
    else:
        fig = px.line(macro, x="date", y="policy_rate",
                      title="ECB main refinancing rate (%)")
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Rising rates compress growth multiples and lengthen raise cycles — "
                   "context for every readiness read above.")

