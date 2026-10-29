"""
Smartwatch Heart-Rate Analyzer - deployable Streamlit application.

Implements the Swastome project objectives end to end:
  1 preprocessing & quality      2 visualization dashboard
  3 ML: anomaly detection, clustering, supervised activity model
  4 automated interpretation     5 configurable UI + downloadable reports
  6 reproducible deployment (Streamlit Community Cloud / Hugging Face Spaces)

Run locally:  streamlit run app.py
"""
from pathlib import Path

import pandas as pd
import streamlit as st

from dashboard import render_dashboard
from hr_backend import analyze, fitbit
from hr_backend.synthetic import generate

st.set_page_config(page_title="Smartwatch HR Analyzer", page_icon="❤️", layout="wide")

SAMPLE_DIR = Path(__file__).parent / "sample_data"

st.title("❤️ Smartwatch Heart-Rate Analyzer")
st.caption(
    "Upload a smartwatch heart-rate export for preprocessing, visualization, activity- and "
    "sleep-aware analysis, anomaly detection and a plain-language report. "
    "Informational only - not a medical device."
)


# --------------------------------------------------------------------------- #
# data helpers
# --------------------------------------------------------------------------- #
@st.cache_data(show_spinner=False)
def load_sample(with_context: bool):
    hr = pd.read_csv(SAMPLE_DIR / "sample_heartrate.csv")
    if not with_context:
        return hr, {}
    return hr, {
        "intensity": fitbit.load_intensity([SAMPLE_DIR / "sample_minuteIntensitiesNarrow.csv"]),
        "steps": fitbit.load_steps([SAMPLE_DIR / "sample_minuteStepsNarrow.csv"]),
        "sleep": fitbit.load_sleep([SAMPLE_DIR / "sample_minuteSleep.csv"]),
    }


@st.cache_data(show_spinner="Analyzing...")
def run_analysis(hr, ctx, user_id, window, method, contamination, k_choice, age, ctx_anom):
    return analyze(
        hr, user_id=user_id,
        intensity_df=ctx.get("intensity"), steps_df=ctx.get("steps"), sleep_df=ctx.get("sleep"),
        window=window, anomaly_method=method, contamination=contamination,
        n_clusters=None if k_choice == "auto" else int(k_choice),
        age=int(age) if age else None, context_aware_anomalies=ctx_anom,
    )


# --------------------------------------------------------------------------- #
# sidebar (Objective 5: configurable parameters)
# --------------------------------------------------------------------------- #
hr_df, ctx_frames, load_err = None, {}, None
with st.sidebar:
    st.header("1. Data")
    source = st.radio("Source", [
        "Sample: 7 days with activity & sleep",
        "Sample: heart rate only",
        "Upload my files",
        "Synthetic (generated)",
    ], help="Samples are one real, anonymised participant from the FitBit Fitness Tracker Data. "
            "'Heart rate only' shows how the trained model estimates activity when no activity file exists.")

    if source.startswith("Sample: 7"):
        hr_df, ctx_frames = load_sample(True)
    elif source.startswith("Sample: heart"):
        hr_df, ctx_frames = load_sample(False)
    elif source.startswith("Synthetic"):
        hr_df = generate(days=4)
    else:
        up = st.file_uploader("Heart-rate CSV (required)", type="csv",
                              help="Fitbit heartrate_seconds_merged.csv, or any CSV with a timestamp and a BPM column.")
        extras = st.file_uploader(
            "Optional: activity / steps / sleep CSVs", type="csv", accept_multiple_files=True,
            help="Fitbit minuteIntensitiesNarrow, minuteStepsNarrow and minuteSleep files. "
                 "Detected automatically from their columns.")
        if up is not None:
            try:
                hr_df = pd.read_csv(up)
            except Exception as e:
                load_err = f"Could not read heart-rate CSV: {e}"
        if extras:
            comp = fitbit.read_companions([pd.read_csv(f) for f in extras])
            ctx_frames = {k: v for k, v in comp.items() if k != "unknown" and v is not None}
            st.caption("Detected: " + (", ".join(ctx_frames) or "nothing usable")
                       + (f" ({comp['unknown']} file(s) not recognised)" if comp["unknown"] else ""))

    user_id = None
    if hr_df is not None and "Id" in hr_df.columns and hr_df["Id"].nunique() > 1:
        counts = hr_df["Id"].value_counts()
        user_id = st.selectbox("Participant", counts.index.tolist(),
                               format_func=lambda i: f"{i} ({counts[i]:,} readings)")

    st.header("2. Settings")
    window = st.selectbox("Analysis window", ["5min", "10min", "30min"], index=1)
    method = st.selectbox("Anomaly method", ["isolation_forest", "lof"],
                          format_func={"isolation_forest": "Isolation Forest", "lof": "Local Outlier Factor"}.get)
    contamination = st.slider("Expected anomaly fraction", 0.01, 0.20, 0.05, 0.01)
    ctx_anom = st.checkbox("Activity-aware anomaly detection", value=True,
                           help="Judge heart rate relative to what is normal for the activity level, "
                                "so workouts are not flagged just for being high.")
    k_choice = st.selectbox("Clusters", ["auto", 2, 3, 4, 5])
    age = st.number_input("Age (optional, for max-HR %)", 0, 120, 0)
    run = st.button("Run analysis", type="primary", width="stretch")

if run:
    if load_err:
        st.error(load_err); st.stop()
    if hr_df is None:
        st.info("Upload a heart-rate CSV in the sidebar first."); st.stop()
    st.session_state["res"] = run_analysis(hr_df, ctx_frames, user_id, window, method,
                                           contamination, k_choice, age, ctx_anom)
    st.session_state["ctx_frames"] = ctx_frames
    st.session_state["uid"] = user_id
    st.session_state["src"] = source

if "res" not in st.session_state:
    st.info("Choose a data source and press **Run analysis** in the sidebar. "
            "Try the 7-day sample first to see every feature.")
    st.stop()

result = st.session_state["res"]
if not result.ok:
    st.error(f"Analysis failed: {result.error}"); st.stop()

tabs = st.tabs([
    "Overview",
    "Activity & Sleep",
    "Visualizations",
    "Machine Learning",
    "Model & Evaluation",
    "Report & Export",
    "About",
])

render_dashboard(
    tabs=tabs,
    result=result,
    window=window,
    context_frames=st.session_state.get("ctx_frames"),
)

