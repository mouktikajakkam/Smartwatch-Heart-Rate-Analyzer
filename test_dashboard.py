"""
Focused tests for dashboard module (Person B, Phase 3 Step 2).

Run:  python test_dashboard.py
"""
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pandas as pd
import streamlit as st

import dashboard


def _mock_analysis_result():
    """Build a minimal valid AnalysisResult-like namespace."""
    return SimpleNamespace(
        ok=True,
        error=None,
        clean=pd.DataFrame({
            "timestamp": pd.date_range("2024-01-01", periods=10, freq="1min"),
            "hr_resampled": [70] * 10,
            "hr_smooth": [70] * 10,
            "is_filled": [False] * 10,
            "ma_5min": [70] * 10,
            "ma_30min": [70] * 10,
            "ma_1h": [70] * 10,
        }),
        quality={
            "user_id": "test_user",
            "start": "2024-01-01T00:00:00",
            "end": "2024-01-07T00:00:00",
            "quality_score": 95,
            "quality_label": "Excellent",
            "coverage_pct": 98.5,
            "duration_hours": 168.0,
            "resample_rule": "1 min",
            "warnings": ["Minor gap detected"],
        },
        stats={
            "resting_hr": 60,
            "resting_method": "5th percentile",
            "mean_hr": 72,
            "max_hr": 140,
            "overnight_low_hr": 52,
        },
        context={
            "available": True,
            "intensity_source": "observed",
            "sleep_source": "from file",
            "hr_by_activity": [
                {"activity": "sedentary", "median_hr": 65, "minutes": 500},
                {"activity": "active", "median_hr": 115, "minutes": 60},
            ],
            "elevated_rest_episodes": [],
        },
        interpretation={
            "summary_text": "Heart rate appears healthy.",
            "trend_text": "Slight upward trend on weekend.",
            "alerts": [{"level": "info", "message": "Normal circadian rhythm."}],
            "disclaimer": "Informational only - not a medical device.",
        },
        minutes=pd.DataFrame({
            "minute": pd.date_range("2024-01-01", periods=10, freq="1min"),
            "hr_mean": [70] * 10,
            "activity": [0] * 10,
            "is_asleep": [False] * 10,
        }),
        circadian=pd.DataFrame({
            "hour": list(range(24)),
            "mean_hr": [70] * 24,
            "std_hr": [5] * 24,
        }),
        daily=pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=3),
            "resting_hr": [60, 61, 59],
            "mean_hr": [72, 73, 71],
            "max_hr": [130, 140, 135],
        }),
        peaks=pd.DataFrame({
            "start": ["2024-01-01 10:00"],
            "peak_hr": [140],
            "recovery_drop": [25],
        }),
        anomalies={
            "method": "isolation_forest",
            "contamination": 0.05,
            "n_anomalies": 2,
            "n_windows": 100,
            "context_aware": True,
            "table": [
                {"window_start": "2024-01-01 02:00", "mean": 110, "min": 100, "max": 120, "anomaly_score": 0.85, "is_anomaly": True},
            ],
        },
        clusters={
            "k": 3,
            "profile": [
                {"cluster": 0, "size": 50, "mean_hr": 62, "mean_variability": 2.1},
                {"cluster": 1, "size": 30, "mean_hr": 78, "mean_variability": 4.5},
            ],
            "table": [
                {"mean": 62, "std": 2.1, "cluster": 0},
                {"mean": 78, "std": 4.5, "cluster": 1},
            ],
        },
        activity_model={
            "trained_on": "FitBit public data",
            "classes": ["sedentary", "light", "active"],
            "evaluation": {
                "accuracy": 0.82,
                "baseline_always_sedentary_accuracy": 0.55,
                "balanced_accuracy": 0.76,
                "f1_macro": 0.74,
                "roc_auc_active_vs_rest": 0.89,
                "baseline_hr_threshold": {"accuracy": 0.70, "balanced_accuracy": 0.65, "f1_macro": 0.64},
                "per_class": {"sedentary": {"precision": 0.85, "recall": 0.88, "f1": 0.86}},
                "confusion_matrix": [[50, 5, 2], [8, 30, 4], [1, 3, 20]],
            },
            "used": False,
        },
    )


def _columns_side_effect(spec):
    count = spec if isinstance(spec, int) else len(spec)
    return [MagicMock() for _ in range(count)]


class TestDashboardModule(unittest.TestCase):
    """Test suite verifying each tab renderer and the master orchestrator."""

    def setUp(self):
        self.res = _mock_analysis_result()

    @patch("dashboard.st")
    def test_render_tab_overview(self, mock_st):
        mock_st.columns.side_effect = _columns_side_effect
        dashboard.render_tab_overview(self.res)
        mock_st.subheader.assert_any_call("Data quality")
        mock_st.subheader.assert_any_call("Key numbers")
        mock_st.subheader.assert_any_call("What this means")

    @patch("dashboard.st")
    def test_render_tab_activity_sleep(self, mock_st):
        mock_st.columns.side_effect = _columns_side_effect
        dashboard.render_tab_activity_sleep(self.res)
        mock_st.subheader.assert_any_call("Heart rate by activity")
        mock_st.subheader.assert_any_call("Where the time went")
        mock_st.subheader.assert_any_call("Heart rate coloured by activity")

    @patch("dashboard.st")
    def test_render_tab_visualizations(self, mock_st):
        mock_st.columns.side_effect = _columns_side_effect
        dashboard.render_tab_visualizations(self.res)
        mock_st.subheader.assert_any_call("Heart-rate timeline")
        mock_st.subheader.assert_any_call("Distribution")
        mock_st.subheader.assert_any_call("Daily trend")

    @patch("dashboard.st")
    def test_render_tab_machine_learning(self, mock_st):
        mock_st.columns.side_effect = _columns_side_effect
        dashboard.render_tab_machine_learning(self.res, window="10min")
        mock_st.subheader.assert_any_call("Unusual-pattern detection")
        mock_st.subheader.assert_any_call("Behaviour groups (clustering)")

    @patch("dashboard.st")
    def test_render_tab_model_evaluation(self, mock_st):
        mock_st.columns.side_effect = _columns_side_effect
        mock_st.button.return_value = False
        dashboard.render_tab_model_evaluation(self.res, window="10min")
        mock_st.subheader.assert_any_call("Supervised activity model")
        mock_st.subheader.assert_any_call("Anomaly-detector benchmark")

    @patch("dashboard.st")
    @patch("dashboard.build_pdf")
    @patch("dashboard.build_csv_bundle")
    def test_render_tab_report_export(self, mock_csv, mock_pdf, mock_st):
        mock_st.columns.side_effect = _columns_side_effect
        mock_pdf.return_value = b"%PDF-1.4"
        mock_csv.return_value = {"summary.csv": "col1,col2\n1,2"}
        dashboard.render_tab_report_export(self.res)

        mock_st.subheader.assert_any_call("Downloadable report")
        mock_st.download_button.assert_called()

    @patch("dashboard.st")
    def test_render_tab_about(self, mock_st):
        mock_st.columns.side_effect = _columns_side_effect
        dashboard.render_tab_about(self.res)
        mock_st.subheader.assert_any_call("How it maps to the project objectives")
        mock_st.subheader.assert_any_call("Limitations")

    @patch("dashboard.st")
    def test_render_dashboard_orchestrator(self, mock_st):
        mock_st.columns.side_effect = _columns_side_effect
        mock_tabs = [MagicMock() for _ in range(7)]
        dashboard.render_dashboard(tabs=mock_tabs, result=self.res, window="10min")
        for tab in mock_tabs:
            tab.__enter__.assert_called_once()
            tab.__exit__.assert_called_once()


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
