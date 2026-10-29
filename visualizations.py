"""
Reusable Plotly chart functions for the Smartwatch Heart-Rate Analyzer.

Person B — Visualization layer (Phase 1).

Each function accepts the necessary data as arguments and returns a Plotly
Figure object (or None when the input data is empty / insufficient).
No Streamlit imports — chart creation is decoupled from rendering so
functions are independently testable.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Shared activity-level colour palette.
ACT_COLORS = {
    "sedentary": "#94a3b8",
    "light": "#38bdf8",
    "active": "#f97316",
    "asleep": "#6366f1",
}


# --------------------------------------------------------------------------- #
# Visualizations tab
# --------------------------------------------------------------------------- #

def hr_timeline(
    clean: pd.DataFrame,
    anom_df: pd.DataFrame,
    show_ma: bool = True,
) -> Optional[go.Figure]:
    """Heart-rate timeline with optional moving averages and anomaly markers."""
    if clean.empty:
        return None
    fig = go.Figure()
    fig.add_trace(go.Scattergl(
        x=clean["timestamp"], y=clean["hr_smooth"], mode="lines",
        name="HR (smoothed)", line=dict(width=1),
    ))
    if show_ma:
        for col, nm in [("ma_30min", "30-min avg"), ("ma_1h", "1-hour avg")]:
            if col in clean.columns:
                fig.add_trace(go.Scattergl(
                    x=clean["timestamp"], y=clean[col], mode="lines",
                    name=nm, line=dict(width=1.5),
                ))
    if not anom_df.empty and "is_anomaly" in anom_df.columns:
        fl = anom_df[anom_df["is_anomaly"]]
        if not fl.empty:
            fig.add_trace(go.Scatter(
                x=fl["window_start"], y=fl["mean"], mode="markers",
                name="unusual window",
                marker=dict(color="red", size=8, symbol="x"),
            ))
    fig.update_layout(
        height=380, margin=dict(t=10),
        yaxis_title="bpm", legend=dict(orientation="h"),
    )
    return fig


def hr_histogram(clean: pd.DataFrame) -> Optional[go.Figure]:
    """Heart-rate distribution histogram."""
    if clean.empty or "hr_smooth" not in clean.columns:
        return None
    fig = px.histogram(clean, x="hr_smooth", nbins=40, labels={"hr_smooth": "bpm"})
    fig.update_layout(height=300, margin=dict(t=10))
    return fig


def circadian_trend(circadian: pd.DataFrame) -> Optional[go.Figure]:
    """Average heart rate by hour of day."""
    if circadian.empty:
        return None
    fig = px.line(
        circadian, x="hour", y="mean_hr", markers=True,
        labels={"mean_hr": "avg bpm", "hour": "hour of day"},
    )
    fig.update_layout(height=300, margin=dict(t=10))
    return fig


def daily_trend(daily: pd.DataFrame) -> Optional[go.Figure]:
    """Daily resting, mean, and max heart-rate trend lines."""
    if daily.empty:
        return None
    fig = px.line(
        daily, x="date", y=["resting_hr", "mean_hr", "max_hr"], markers=True,
    )
    fig.update_layout(height=300, margin=dict(t=10), yaxis_title="bpm")
    return fig


# --------------------------------------------------------------------------- #
# Activity & Sleep tab
# --------------------------------------------------------------------------- #

def activity_bar(hr_by_activity: pd.DataFrame) -> Optional[go.Figure]:
    """Median heart rate by activity level (bar chart)."""
    if hr_by_activity.empty:
        return None
    fig = px.bar(
        hr_by_activity, x="activity", y="median_hr", color="activity",
        color_discrete_map=ACT_COLORS, text="median_hr",
        labels={"median_hr": "median bpm", "activity": ""},
    )
    fig.update_layout(height=320, showlegend=False, margin=dict(t=10))
    return fig


def activity_pie(hr_by_activity: pd.DataFrame) -> Optional[go.Figure]:
    """Time distribution by activity level (donut chart)."""
    if hr_by_activity.empty:
        return None
    fig = px.pie(
        hr_by_activity, names="activity", values="minutes", color="activity",
        color_discrete_map=ACT_COLORS, hole=0.5,
    )
    fig.update_layout(height=320, margin=dict(t=10))
    return fig


def activity_scatter(minutes: pd.DataFrame) -> Optional[go.Figure]:
    """Heart rate coloured by activity state (scatter plot).

    Derives a 'state' label from the 'activity' and 'is_asleep' columns
    without mutating the original DataFrame.
    """
    if minutes.empty or "activity" not in minutes.columns:
        return None
    mm = minutes.copy()
    names = {0: "sedentary", 1: "light", 2: "active"}
    mm["state"] = np.where(mm["is_asleep"], "asleep", mm["activity"].map(names))
    fig = px.scatter(
        mm, x="minute", y="hr_mean", color="state",
        color_discrete_map=ACT_COLORS,
        render_mode="webgl", labels={"hr_mean": "bpm", "minute": ""},
    )
    fig.update_traces(marker=dict(size=3))
    fig.update_layout(height=380, margin=dict(t=10), legend=dict(orientation="h"))
    return fig


# --------------------------------------------------------------------------- #
# Machine Learning tab
# --------------------------------------------------------------------------- #

def anomaly_score_histogram(anom_df: pd.DataFrame) -> Optional[go.Figure]:
    """Distribution of anomaly scores, coloured by anomaly flag."""
    if anom_df.empty:
        return None
    fig = px.histogram(
        anom_df, x="anomaly_score", color="is_anomaly", nbins=40,
        labels={"anomaly_score": "how unusual (higher = more)"},
    )
    fig.update_layout(height=260, margin=dict(t=10))
    return fig


def cluster_scatter(cluster_table: pd.DataFrame) -> Optional[go.Figure]:
    """Cluster scatter plot (window mean HR vs variability)."""
    if cluster_table.empty or "cluster" not in cluster_table.columns:
        return None
    fig = px.scatter(
        cluster_table, x="mean", y="std",
        color=cluster_table["cluster"].astype(str),
        labels={
            "mean": "window mean HR",
            "std": "window variability",
            "color": "group",
        },
    )
    fig.update_layout(height=320, margin=dict(t=10))
    return fig


# --------------------------------------------------------------------------- #
# Model & Evaluation tab
# --------------------------------------------------------------------------- #

def confusion_matrix_heatmap(
    cm: list | np.ndarray,
    class_names: list[str],
) -> Optional[go.Figure]:
    """Row-normalised confusion-matrix heatmap."""
    cm_arr = np.asarray(cm)
    if cm_arr.size == 0:
        return None
    # Guard against rows that sum to zero (no samples for a class).
    row_sums = cm_arr.sum(axis=1, keepdims=True)
    row_sums = np.where(row_sums == 0, 1, row_sums)
    cmn = cm_arr / row_sums
    fig = px.imshow(
        cmn, x=class_names, y=class_names, text_auto=".0%",
        color_continuous_scale="Blues",
        labels=dict(x="predicted", y="actual"),
    )
    fig.update_layout(height=330, margin=dict(t=10), coloraxis_showscale=False)
    return fig
