"""
Dashboard module for Smartwatch Heart-Rate Analyzer.

Encapsulates tab-rendering logic for the seven application tabs:
1. Overview (data quality, key metrics, automated interpretation)
2. Activity & Sleep (exercise breakdown, timeline scatter, still episodes)
3. Visualizations (HR timeline with moving averages, distribution, diurnal & daily trends)
4. Machine Learning (unusual-window detection, KMeans behavior clustering)
5. Model & Evaluation (supervised activity model metrics, anomaly benchmark runner)
6. Report & Export (PDF and CSV bundle generation)
7. About (project objective mapping, limitations, clinical disclaimer)
"""
from typing import Any, Dict, List, Optional, Sequence

import numpy as np
import pandas as pd
import streamlit as st

from hr_backend.evaluation import evaluate_anomaly_detection
from hr_backend.pipeline import get_activity_model
from hr_backend.report import build_csv_bundle, build_pdf
from ui_components import (
    render_alerts,
    render_chart,
    render_data_table,
    render_metric_row,
)
from visualizations import (
    activity_bar,
    activity_pie,
    activity_scatter,
    anomaly_score_histogram,
    circadian_trend,
    cluster_scatter,
    confusion_matrix_heatmap,
    daily_trend,
    hr_histogram,
    hr_timeline,
)

TAB_TITLES: List[str] = [
    "Overview",
    "Activity & Sleep",
    "Visualizations",
    "Machine Learning",
    "Model & Evaluation",
    "Report & Export",
    "About",
]


# =========================================================================== #
# 1. Overview Tab
# =========================================================================== #
def render_tab_overview(result: Any) -> None:
    """Render Tab 0: Data quality, key stats, alerts, and automated interpretation."""
    q, s = result.quality, result.stats
    it = result.interpretation

    if q.get("user_id"):
        st.caption(f"Participant {q['user_id']}  |  {q['start'][:16]} to {q['end'][:16]}")

    st.subheader("Data quality")
    render_metric_row([
        {"label": "Quality", "value": f"{q['quality_score']}/100", "delta": q.get("quality_label")},
        {"label": "Coverage", "value": f"{q['coverage_pct']}%"},
        {"label": "Duration", "value": f"{q['duration_hours']/24:.1f} days"},
        {"label": "Sampling grid", "value": q["resample_rule"]},
    ])
    render_alerts(q.get("warnings", []), default_level="warning", icon="⚠️")

    st.subheader("Key numbers")
    render_metric_row([
        {"label": "Resting HR", "value": f"{s['resting_hr']} bpm", "help": s.get("resting_method")},
        {"label": "Average HR", "value": f"{s['mean_hr']} bpm"},
        {"label": "Peak HR (99th pct)", "value": f"{s['max_hr']} bpm"},
        {"label": "Lowest during sleep", "value": f"{s.get('overnight_low_hr', 'n/a')} bpm"},
    ])

    st.subheader("What this means")
    st.write(it["summary_text"])
    if it.get("trend_text"):
        st.write(it["trend_text"])
    render_alerts(it.get("alerts", []))
    st.caption(it["disclaimer"])


# =========================================================================== #
# 2. Activity & Sleep Tab
# =========================================================================== #
def render_tab_activity_sleep(result: Any) -> None:
    """Render Tab 1: Activity breakdown, sleep info, scatter plot, and still episodes."""
    s, c = result.stats, result.context
    minutes = result.minutes

    if not c.get("available"):
        st.info("No activity context available for this recording.")
        return

    src = {"observed": "from your activity file", "estimated": "estimated by the trained model"}
    st.caption(
        f"Activity: {src.get(c['intensity_source'], c['intensity_source'])}  |  "
        f"Sleep: {c['sleep_source']}"
    )

    by = pd.DataFrame(c.get("hr_by_activity", []))
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Heart rate by activity")
        fig = activity_bar(by)
        render_chart(fig, fallback_msg="No activity data available.")
    with c2:
        st.subheader("Where the time went")
        fig = activity_pie(by)
        render_chart(fig, fallback_msg="No activity distribution available.")

    st.subheader("Heart rate coloured by activity")
    fig = activity_scatter(minutes)
    render_chart(fig, fallback_msg="No per-minute activity data available.")

    st.subheader("High heart rate while still")
    eps = c.get("elevated_rest_episodes", [])
    if eps:
        threshold = max(100, (s["resting_hr"] or 0) + 30)
        st.write(
            f"Periods of 10+ minutes where heart rate stayed above "
            f"{threshold:.0f} bpm while sitting still and awake:"
        )
        render_data_table(eps, width="stretch", hide_index=True)
    else:
        st.success("No sustained periods of high heart rate while still. ")


# =========================================================================== #
# 3. Visualizations Tab
# =========================================================================== #
def render_tab_visualizations(result: Any) -> None:
    """Render Tab 2: HR timeline, distribution histogram, circadian & daily trends, exertion table."""
    clean = result.clean
    anom = pd.DataFrame(result.anomalies.get("table", []))

    st.subheader("Heart-rate timeline")
    show_ma = st.checkbox("Show moving averages", value=True)
    fig = hr_timeline(clean, anom, show_ma=show_ma)
    render_chart(fig, fallback_msg="No heart-rate time series available.")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Distribution")
        fig = hr_histogram(clean)
        render_chart(fig, fallback_msg="No distribution data available.")
    with c2:
        st.subheader("Average by hour of day")
        fig = circadian_trend(result.circadian)
        render_chart(fig, fallback_msg="No circadian pattern data available.")

    st.subheader("Daily trend")
    fig = daily_trend(result.daily)
    render_chart(fig, fallback_msg="No daily trend data available.")

    st.subheader("Exercise episodes and recovery")
    if not result.peaks.empty:
        render_data_table(
            result.peaks,
            caption="Recovery = bpm drop in the 1-2 minutes after the peak. A bigger drop usually means better fitness.",
            hide_index=True,
        )
    else:
        st.write("No sustained exertion episodes detected.")


# =========================================================================== #
# 4. Machine Learning Tab
# =========================================================================== #
def render_tab_machine_learning(result: Any, window: str = "10min") -> None:
    """Render Tab 3: Unusual-pattern anomaly detection, score histogram, and behavior clustering."""
    a = result.anomalies
    anom = pd.DataFrame(a.get("table", []))

    st.subheader("Unusual-pattern detection")
    method_name = "Isolation Forest" if a.get("method") == "isolation_forest" else "Local Outlier Factor"
    context_desc = (
        "Each window was judged against what is normal *for its activity level and sleep*, so workouts are not flagged just for being high."
        if a.get("context_aware")
        else "Windows were judged on heart-rate shape only."
    )
    st.write(
        f"**{method_name}** split the recording into {window} windows and flagged "
        f"**{a['n_anomalies']} of {a['n_windows']}** as unusual. {context_desc}"
    )

    fig = anomaly_score_histogram(anom)
    render_chart(fig)

    if not anom.empty:
        show = ["window_start", "mean", "min", "max"] + [
            x for x in ["mean_activity", "expected_hr", "residual_mean"] if x in anom
        ] + ["anomaly_score"]
        anom_table = anom[anom["is_anomaly"]][show].sort_values("anomaly_score", ascending=False).head(50)
        render_data_table(anom_table, width="stretch", hide_index=True, round_decimals=2)

    st.subheader("Behaviour groups (clustering)")
    cl = result.clusters
    st.write(
        f"KMeans grouped the windows into **{cl['k']}** patterns, numbered from lowest to highest heart rate:"
    )
    render_data_table(cl.get("profile", []), width="stretch", hide_index=True)

    ct = pd.DataFrame(cl.get("table", []))
    fig = cluster_scatter(ct)
    render_chart(fig)


# =========================================================================== #
# 5. Model & Evaluation Tab
# =========================================================================== #
def render_tab_model_evaluation(
    result: Any,
    window: str = "10min",
    context_frames: Optional[Dict[str, Any]] = None,
) -> None:
    """Render Tab 4: Supervised model performance metrics, baselines, and interactive benchmark."""
    clean, q = result.clean, result.quality

    st.subheader("Supervised activity model")
    am = result.activity_model
    if not am:
        st.warning("Activity model file not found - heart-rate-only uploads will skip activity estimation.")
    else:
        ev = am["evaluation"]
        st.write(
            "Predicts each minute's activity level (**sedentary / light / active**) from heart rate alone. "
            f"Trained on {am['trained_on']} using real Fitbit activity labels. Scores below come from "
            "**leave-participants-out** testing: the model is always tested on people it never saw."
        )

        render_metric_row([
            {"label": "Accuracy", "value": f"{ev['accuracy']:.0%}", "delta": f"+{(ev['accuracy']-ev['baseline_always_sedentary_accuracy'])*100:.0f} pts vs guessing"},
            {"label": "Balanced accuracy", "value": f"{ev['balanced_accuracy']:.0%}"},
            {"label": "Macro F1", "value": f"{ev['f1_macro']:.2f}"},
            {"label": "ROC-AUC (active vs rest)", "value": f"{ev['roc_auc_active_vs_rest']:.2f}"},
        ])

        base = pd.DataFrame([
            {"model": "Always guess 'sedentary'", "accuracy": ev["baseline_always_sedentary_accuracy"], "balanced accuracy": 0.333, "macro F1": None},
            {"model": "Heart-rate threshold rule", "accuracy": ev["baseline_hr_threshold"]["accuracy"], "balanced accuracy": ev["baseline_hr_threshold"]["balanced_accuracy"], "macro F1": ev["baseline_hr_threshold"]["f1_macro"]},
            {"model": "This model", "accuracy": ev["accuracy"], "balanced accuracy": ev["balanced_accuracy"], "macro F1": ev["f1_macro"]},
        ])

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Compared with simple baselines**")
            render_data_table(base, width="stretch", hide_index=True)
            st.markdown("**Per class**")
            render_data_table(pd.DataFrame(ev["per_class"]).T, width="stretch", hide_index=False)
        with c2:
            st.markdown("**Confusion matrix** (rows = truth, % of each row)")
            fig = confusion_matrix_heatmap(ev["confusion_matrix"], am["classes"])
            render_chart(fig, fallback_msg="No confusion matrix available.")

        if am.get("used"):
            st.info("This analysis used the model's estimates because no activity file was provided.")

    st.subheader("Anomaly-detector benchmark")
    st.write(
        "The dataset has no doctor-confirmed anomaly labels, so we hide known fake problems (spikes, "
        "dropouts, long stretches of raised heart rate) in this real recording and check how many the "
        "detector finds. Treat it as a quality check on the method, not a medical validation."
    )

    if st.button("Run benchmark on this recording"):
        with st.spinner("Hiding anomalies and scoring (about 30 s)..."):
            cf = context_frames if context_frames is not None else (st.session_state.get("ctx_frames") or None)
            model = get_activity_model() if (not cf or "intensity" not in cf) else None
            ctx_on = result.anomalies.get("context_aware", False)
            evals = [
                evaluate_anomaly_detection(
                    clean[["timestamp", "hr_resampled", "hr_smooth", "is_filled"]],
                    method=result.anomalies["method"],
                    contamination=result.anomalies["contamination"],
                    window=window,
                    seed=sd,
                    context_frames=cf if ctx_on else None,
                    user_id=q.get("user_id"),
                    activity_model=model if ctx_on else None,
                )
                for sd in range(3)
            ]

        m = lambda k: float(np.nanmean([getattr(e, k) for e in evals]))
        render_metric_row([
            ("Recall", f"{m('recall'):.2f}", None, "Share of hidden problems that were found"),
            ("Precision", f"{m('precision'):.2f}", None, "Share of flags that were hidden problems"),
            ("F1", f"{m('f1'):.2f}"),
            ("ROC-AUC", f"{m('roc_auc'):.2f}", None, "0.5 = coin flip, 1.0 = perfect ranking"),
            ("PR-AUC", f"{m('pr_auc'):.2f}"),
        ])
        st.caption(
            "Precision is limited by design: the detector flags a fixed share of windows, and real "
            "recordings contain genuine unusual moments that were not on the hidden list."
        )


# =========================================================================== #
# 6. Report & Export Tab
# =========================================================================== #
def render_tab_report_export(result: Any) -> None:
    """Render Tab 5: PDF download button and CSV data bundles."""
    q = result.quality
    st.subheader("Downloadable report")
    try:
        pdf = build_pdf(result, subject=f"Participant {q.get('user_id') or ''}".strip())
        st.download_button(
            "⬇️ Download PDF report",
            pdf,
            "heart_rate_report.pdf",
            "application/pdf",
            type="primary",
        )
    except Exception as e:
        st.error(f"PDF generation failed: {e}")

    st.markdown("**CSV exports**")
    for name, data in build_csv_bundle(result).items():
        st.download_button(f"⬇️ {name}", data, name, "text/csv", key=name)


# =========================================================================== #
# 7. About Tab
# =========================================================================== #
def render_tab_about(result: Any) -> None:
    """Render Tab 6: Mapping of project objectives, limitations, and clinical disclaimer."""
    st.subheader("How it maps to the project objectives")
    st.markdown("""
| Objective | Where in the app |
|---|---|
| 1 Preprocessing | cleaning, resampling, smoothing, quality score (Overview) |
| 2 Visualization | timeline, histogram, moving averages, hour-of-day, daily trend, recovery (Visualizations, Activity & Sleep) |
| 3 Machine learning | Isolation Forest / LOF anomalies, KMeans clustering, supervised activity model with accuracy / precision / recall / F1 / ROC-AUC (Machine Learning, Model & Evaluation) |
| 4 Interpretation | resting HR, sleep HR, peak, variability, alerts, plain-language summary (Overview) |
| 5 Configurable UI + reports | sidebar settings, PDF + CSV export |
| 6 Deployment | Streamlit Community Cloud / Hugging Face Spaces |
""")

    st.subheader("Limitations")
    st.markdown("""
- **Not a medical device** and not a diagnosis.
- **Variability (HRV) is an approximation** from BPM; true HRV needs beat-to-beat data.
- **Without a sleep file**, sleep is assumed to be 00:00-06:00.
- **Activity estimates** from heart rate alone are about 81% accurate on new people; light activity is the hardest class.
- **Anomaly accuracy** is measured with hidden fake anomalies, because the public data has no clinical labels.
- Training data: 15 adults, 2016, one device type - results may differ for other watches and populations.
""")
    st.caption(result.interpretation["disclaimer"])


# =========================================================================== #
# Master Dashboard Orchestrator
# =========================================================================== #
def render_dashboard(
    tabs: Optional[Sequence[Any]] = None,
    result: Any = None,
    window: str = "10min",
    context_frames: Optional[Dict[str, Any]] = None,
) -> None:
    """Coordinate rendering of all seven dashboard tabs in order.

    Args:
        tabs: Optional sequence of 7 tab context managers (from st.tabs). If None, st.tabs is created.
        result: AnalysisResult object returned by hr_backend.analyze.
        window: Selected time window string for anomaly detection (defaults to '10min').
        context_frames: Optional companion DataFrames dictionary (intensity, steps, sleep).
    """
    if result is None:
        st.error("No analysis results provided to render.")
        return

    if tabs is None:
        tabs = st.tabs(TAB_TITLES)

    with tabs[0]:
        render_tab_overview(result)

    with tabs[1]:
        render_tab_activity_sleep(result)

    with tabs[2]:
        render_tab_visualizations(result)

    with tabs[3]:
        render_tab_machine_learning(result, window=window)

    with tabs[4]:
        render_tab_model_evaluation(result, window=window, context_frames=context_frames)

    with tabs[5]:
        render_tab_report_export(result)

    with tabs[6]:
        render_tab_about(result)
