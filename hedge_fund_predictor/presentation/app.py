"""
Streamlit Web Dashboard for Hedge Fund Position Predictor (v6).

Launch with:
    streamlit run hedge_fund_predictor/presentation/app.py
"""

import sys
from pathlib import Path

# Add project root to path if running directly
root_dir = Path(__file__).resolve().parents[2]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import pandas as pd
import streamlit as st

from hedge_fund_predictor.config.entity_groups import ENTITY_GROUPS
from hedge_fund_predictor.config.sector_etfs import GICS_SECTOR_ETFS, THEME_ETFS
from hedge_fund_predictor.storage.db_manager import DatabaseManager
from hedge_fund_predictor.analytics_engine.E1_adaptive_drift import AdaptiveDriftEngine
from hedge_fund_predictor.analytics_engine.E5_conviction_consensus import ConvictionConsensusEngine
from hedge_fund_predictor.analytics_engine.E7_cftc_positioning import CFTCPositioningEngine
from hedge_fund_predictor.meta_ensemble.stacking_ensemble import StackingMetaEnsemble

# ── Streamlit Page Configuration ──────────────────────────────────────────
st.set_page_config(
    page_title="Hedge Fund Position Predictor v6",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for polished, premium look
st.markdown(
    """
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e222d; padding: 15px; border-radius: 10px; }
    div[data-testid="stMarkdownContainer"] h1 { color: #4F8BF9; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🏛️ Hedge Fund Position Predictor (v6 Ultimate Quant)")
st.caption("100% Free Data • 14 Channels • 11 Engines • Multi-Timeframe Fusion • GNN Herding")

# ── Sidebar Filters ────────────────────────────────────────────────────────
st.sidebar.header("🕹️ Control Panel")

selected_fund_key = st.sidebar.selectbox(
    "Select Hedge Fund Manager",
    options=list(ENTITY_GROUPS.keys()),
    format_func=lambda k: k.replace("_", " ").title(),
)

fund_cfg = ENTITY_GROUPS[selected_fund_key]
cik = fund_cfg.hedge_fund_ciks[0]

st.sidebar.markdown(f"**Strategy**: `{fund_cfg.strategy}`")
st.sidebar.markdown(f"**Primary CIK**: `{cik}`")
if fund_cfg.public_vehicle:
    st.sidebar.markdown(f"**Listed Vehicle**: `{fund_cfg.public_vehicle}`")

st.sidebar.divider()
lookback_q = st.sidebar.slider("Lookback Window (Quarters)", 1, 8, 4)

# ── Header Metrics ─────────────────────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)
m1.metric("Selected Manager", selected_fund_key.replace("_", " ").title())
m2.metric("Strategy", fund_cfg.strategy.upper().replace("_", " "))
m3.metric("Data Channels Active", "14 Channels")
m4.metric("Engine Ensemble", "11 Layer Stacking")

# ── Tabs ───────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Fund Position Estimates",
    "🌐 Conviction & Crowding",
    "🔮 Futures & Macro Tilts",
    "🛡️ Short Position Monitor",
    "🧪 Model Diagnostics",
])

# DB Instance
db = DatabaseManager()

with tab1:
    st.subheader(f"Estimated Current Portfolio: {selected_fund_key.replace('_', ' ').title()}")

    col_left, col_right = st.columns([2, 1])

    with col_left:
        # Run Engine 1 Adaptive Drift
        e1 = AdaptiveDriftEngine(db_manager=db)
        positions = e1.estimate_current_positions(cik=cik, strategy=fund_cfg.strategy)

        if not positions.empty:
            st.dataframe(
                positions[[
                    "cusip", "issuer", "value_current", "weight_raw",
                    "confidence", "days_since_filing"
                ]].style.format({
                    "value_current": "${:,.0f}k",
                    "weight_raw": "{:.2%}",
                    "confidence": "{:.1f}%",
                }),
                use_container_width=True,
            )
        else:
            st.info("No DB positions loaded yet. Run `python -m hedge_fund_predictor` to ingest DERA data.")

    with col_right:
        st.markdown("### 🏆 Top Conviction Names")
        if not positions.empty:
            top3 = positions.head(3)
            for idx, r in top3.iterrows():
                st.success(f"**{r.get('issuer', 'UNKNOWN')}**: {r['weight_raw']:.1%} estimated weight")

with tab2:
    st.subheader("Conviction & Crowding Analysis (Engine 5)")
    st.markdown("Identifies **Hidden Alpha** (High Conviction + Low Consensus) vs **Crowding Risk**.")

    e5 = ConvictionConsensusEngine(db_manager=db)
    analysis = e5.analyze()

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 🟢 Hidden Alpha Opportunities")
        hidden = analysis.get("hidden_alpha", pd.DataFrame())
        if not hidden.empty:
            st.dataframe(hidden[["cusip", "issuer", "consensus", "max_weight"]], use_container_width=True)
        else:
            st.write("No hidden alpha signals currently detected.")

    with c2:
        st.markdown("#### 🔴 Crowded Positions (Forced Selling Risk)")
        crowd = analysis.get("crowding_alerts", pd.DataFrame())
        if not crowd.empty:
            st.dataframe(crowd[["cusip", "issuer", "consensus", "n_holders"]], use_container_width=True)
        else:
            st.write("No severe crowding alerts in current universe.")

with tab3:
    st.subheader("CFTC Futures & Commodities Macro Tilts (Engine 7)")
    e7 = CFTCPositioningEngine(db_manager=db)
    tilts = e7.map_cot_to_gics_sectors(fund_cfg.strategy)

    if not tilts.empty:
        st.dataframe(tilts, use_container_width=True)
    else:
        st.info("Download CFTC data using the main pipeline to view live macro tilts.")

with tab4:
    st.subheader("Short Position & Regulatory Risk Monitor (EU/UK + OCC GEX)")
    st.info("Tracks European FCA/AMF short disclosures + OCC Put Open Interest surges for directional short estimates.")

with tab5:
    st.subheader("Model Diagnostic & Architecture Summary")
    st.markdown(
        """
        - **Data Ingestion**: SEC DERA Bulk 13F, 13D/13G, Form 4, CFTC COT, yfinance, Fama-French 5
        - **11 Engines**: E1 (Drift), E2 (Kalman RBSA), E3 (Bayesian), E4 (Options Delta), E5 (Crowding), E6 (NLP), E7 (CFTC), E8 (Meta/Return Gap), E9 (GNN Herding), E10 (Insider Corr), E11 (SEC Scrutiny)
        - **Ensemble Layer**: Ridge Stacking Meta-Ensemble with 5-Horizon Half-Life Decay
        """
    )
