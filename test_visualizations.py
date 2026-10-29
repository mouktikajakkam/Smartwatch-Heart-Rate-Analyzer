"""
Focused tests for the visualization module (Person B, Phase 1).

Run:  python test_visualizations.py
"""
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from visualizations import (
    hr_timeline, hr_histogram, circadian_trend, daily_trend,
    activity_bar, activity_pie, activity_scatter,
    anomaly_score_histogram, cluster_scatter, confusion_matrix_heatmap,
    ACT_COLORS,
)


# ---------------------------------------------------------------------------
# Minimal test-data factories
# ---------------------------------------------------------------------------
def _clean_df(n=100):
    """Minimal cleaned heart-rate DataFrame."""
    ts = pd.date_range("2024-01-01", periods=n, freq="1min")
    rng = np.random.default_rng(0)
    hr = 70 + rng.normal(0, 5, n)
    return pd.DataFrame({
        "timestamp": ts,
        "hr_resampled": hr,
        "hr_smooth": hr,
        "is_filled": False,
        "ma_5min": hr,
        "ma_30min": hr,
        "ma_1h": hr,
    })


def _anom_df(n=20):
    """Minimal anomaly-table DataFrame."""
    ts = pd.date_range("2024-01-01", periods=n, freq="10min")
    rng = np.random.default_rng(1)
    return pd.DataFrame({
        "window_start": ts,
        "mean": 70 + rng.normal(0, 5, n),
        "min": 60 + rng.normal(0, 3, n),
        "max": 80 + rng.normal(0, 3, n),
        "std": rng.uniform(1, 5, n),
        "anomaly_score": rng.uniform(0, 1, n),
        "is_anomaly": [i < 3 for i in range(n)],
    })


def _circadian_df():
    """Minimal circadian-profile DataFrame."""
    return pd.DataFrame({
        "hour": list(range(24)),
        "mean_hr": [65 + 5 * np.sin(h / 24 * 2 * np.pi) for h in range(24)],
        "std_hr": [3.0] * 24,
        "n": [100] * 24,
    })


def _daily_df(n=5):
    """Minimal daily-summary DataFrame."""
    dates = pd.date_range("2024-01-01", periods=n).date
    return pd.DataFrame({
        "date": list(dates),
        "mean_hr": [72, 74, 71, 73, 70],
        "min_hr": [55, 58, 54, 56, 53],
        "max_hr": [120, 115, 118, 125, 112],
        "resting_hr": [62, 64, 61, 63, 60],
        "std_hr": [10, 9, 11, 10, 8],
        "n_samples": [1440] * n,
    })


def _activity_df():
    """Minimal hr_by_activity DataFrame."""
    return pd.DataFrame([
        {"activity": "sedentary", "minutes": 600, "pct": 50, "mean_hr": 68, "median_hr": 67},
        {"activity": "light", "minutes": 300, "pct": 25, "mean_hr": 82, "median_hr": 80},
        {"activity": "active", "minutes": 120, "pct": 10, "mean_hr": 120, "median_hr": 118},
        {"activity": "asleep", "minutes": 180, "pct": 15, "mean_hr": 58, "median_hr": 57},
    ])


def _minutes_df(n=200):
    """Minimal per-minute DataFrame with activity context."""
    ts = pd.date_range("2024-01-01", periods=n, freq="1min")
    rng = np.random.default_rng(2)
    return pd.DataFrame({
        "minute": ts,
        "hr_mean": 70 + rng.normal(0, 8, n),
        "hr_std": rng.uniform(0, 3, n),
        "activity": rng.choice([0, 1, 2], n),
        "is_asleep": [i < 30 for i in range(n)],
    })


def _cluster_table_df(n=30):
    """Minimal cluster-table DataFrame."""
    rng = np.random.default_rng(3)
    return pd.DataFrame({
        "mean": 70 + rng.normal(0, 10, n),
        "std": rng.uniform(1, 8, n),
        "cluster": rng.choice([0, 1, 2], n),
    })


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------
ok = True


def check(name, cond, detail=""):
    global ok
    ok &= bool(cond)
    print(f"[{'PASS' if cond else 'FAIL'}] {name} {detail}")


def is_fig(obj):
    return isinstance(obj, go.Figure)


# ---- hr_timeline ----
fig = hr_timeline(_clean_df(), _anom_df(), show_ma=True)
check("hr_timeline returns Figure", is_fig(fig))

fig = hr_timeline(_clean_df(), _anom_df(), show_ma=False)
check("hr_timeline without MA returns Figure", is_fig(fig))

fig = hr_timeline(_clean_df(), pd.DataFrame())
check("hr_timeline with empty anomalies returns Figure", is_fig(fig))

fig = hr_timeline(pd.DataFrame(), pd.DataFrame())
check("hr_timeline with empty clean returns None", fig is None)

# ---- hr_histogram ----
fig = hr_histogram(_clean_df())
check("hr_histogram returns Figure", is_fig(fig))

fig = hr_histogram(pd.DataFrame())
check("hr_histogram with empty data returns None", fig is None)

fig = hr_histogram(pd.DataFrame({"other_col": [1, 2]}))
check("hr_histogram without hr_smooth col returns None", fig is None)

# ---- circadian_trend ----
fig = circadian_trend(_circadian_df())
check("circadian_trend returns Figure", is_fig(fig))

fig = circadian_trend(pd.DataFrame())
check("circadian_trend with empty data returns None", fig is None)

# ---- daily_trend ----
fig = daily_trend(_daily_df())
check("daily_trend returns Figure", is_fig(fig))

fig = daily_trend(pd.DataFrame())
check("daily_trend with empty data returns None", fig is None)

# ---- activity_bar ----
fig = activity_bar(_activity_df())
check("activity_bar returns Figure", is_fig(fig))

fig = activity_bar(pd.DataFrame())
check("activity_bar with empty data returns None", fig is None)

# ---- activity_pie ----
fig = activity_pie(_activity_df())
check("activity_pie returns Figure", is_fig(fig))

fig = activity_pie(pd.DataFrame())
check("activity_pie with empty data returns None", fig is None)

# ---- activity_scatter ----
fig = activity_scatter(_minutes_df())
check("activity_scatter returns Figure", is_fig(fig))

fig = activity_scatter(pd.DataFrame())
check("activity_scatter with empty data returns None", fig is None)

no_act = _minutes_df().drop(columns=["activity"])
fig = activity_scatter(no_act)
check("activity_scatter without activity col returns None", fig is None)

# ---- anomaly_score_histogram ----
fig = anomaly_score_histogram(_anom_df())
check("anomaly_score_histogram returns Figure", is_fig(fig))

fig = anomaly_score_histogram(pd.DataFrame())
check("anomaly_score_histogram with empty data returns None", fig is None)

# ---- cluster_scatter ----
fig = cluster_scatter(_cluster_table_df())
check("cluster_scatter returns Figure", is_fig(fig))

fig = cluster_scatter(pd.DataFrame())
check("cluster_scatter with empty data returns None", fig is None)

no_cl = _cluster_table_df().drop(columns=["cluster"])
fig = cluster_scatter(no_cl)
check("cluster_scatter without cluster col returns None", fig is None)

# ---- confusion_matrix_heatmap ----
cm = [[50, 5, 1], [3, 40, 7], [0, 2, 30]]
fig = confusion_matrix_heatmap(cm, ["sedentary", "light", "active"])
check("confusion_matrix_heatmap (list input) returns Figure", is_fig(fig))

fig = confusion_matrix_heatmap(np.array(cm), ["sedentary", "light", "active"])
check("confusion_matrix_heatmap (ndarray input) returns Figure", is_fig(fig))

fig = confusion_matrix_heatmap([], [])
check("confusion_matrix_heatmap with empty data returns None", fig is None)

# zero-row: a class with no samples should not crash
cm_zero = [[0, 0, 0], [3, 40, 7], [0, 2, 30]]
fig = confusion_matrix_heatmap(cm_zero, ["a", "b", "c"])
check("confusion_matrix_heatmap with zero-sum row doesn't crash", is_fig(fig))

# ---- NaN handling ----
clean_nan = _clean_df()
clean_nan.loc[0:10, "hr_smooth"] = np.nan
fig = hr_timeline(clean_nan, _anom_df())
check("hr_timeline handles NaN in hr_smooth", is_fig(fig))

fig = hr_histogram(clean_nan)
check("hr_histogram handles NaN in hr_smooth", is_fig(fig))

# ---- DataFrame not mutated ----
orig_minutes = _minutes_df()
cols_before = set(orig_minutes.columns)
_ = activity_scatter(orig_minutes)
check("activity_scatter does not mutate input DataFrame",
      set(orig_minutes.columns) == cols_before)

# ---- ACT_COLORS ----
check("ACT_COLORS has all expected keys",
      set(ACT_COLORS) == {"sedentary", "light", "active", "asleep"})

print(f"\n{'ALL CHECKS PASSED' if ok else 'SOME CHECKS FAILED'}")
raise SystemExit(0 if ok else 1)
