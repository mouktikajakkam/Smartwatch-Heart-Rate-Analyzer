"""
Tests for reusable UI components (Person B, Phase 3 Step 1).

Run:  python test_ui_components.py
"""
import sys
import unittest
from unittest.mock import MagicMock, call, patch

import pandas as pd
import plotly.graph_objects as go

import ui_components


class TestRenderChart(unittest.TestCase):
    """Test render_chart behavior for valid figures and fallbacks."""

    @patch("ui_components.st")
    def test_render_chart_valid_figure(self, mock_st):
        fig = go.Figure(data=go.Scatter(x=[1, 2], y=[3, 4]))
        ui_components.render_chart(fig)

        mock_st.plotly_chart.assert_called_once_with(fig, width="stretch")
        mock_st.info.assert_not_called()

    @patch("ui_components.st")
    def test_render_chart_none_figure(self, mock_st):
        ui_components.render_chart(None, fallback_msg="No timeline available.")

        mock_st.plotly_chart.assert_not_called()
        mock_st.info.assert_called_once_with("No timeline available.")

    @patch("ui_components.st")
    def test_render_chart_default_fallback(self, mock_st):
        ui_components.render_chart(None)

        mock_st.plotly_chart.assert_not_called()
        mock_st.info.assert_called_once_with("No data available.")

    @patch("ui_components.st")
    def test_render_chart_kwargs_passthrough(self, mock_st):
        fig = go.Figure()
        ui_components.render_chart(fig, width="auto", key="test_chart")

        mock_st.plotly_chart.assert_called_once_with(fig, width="auto", key="test_chart")


class TestRenderMetricRow(unittest.TestCase):
    """Test render_metric_row with dict and tuple specifications."""

    @patch("ui_components.st")
    def test_render_metric_row_dicts(self, mock_st):
        col1, col2 = MagicMock(), MagicMock()
        mock_st.columns.return_value = [col1, col2]

        items = [
            {"label": "Quality", "value": "85/100", "delta": "Good"},
            {"label": "Resting HR", "value": "62 bpm", "help": "Calculated lowest 5th percentile"},
        ]
        ui_components.render_metric_row(items)

        mock_st.columns.assert_called_once_with(2)
        col1.metric.assert_called_once_with(label="Quality", value="85/100", delta="Good", help=None)
        col2.metric.assert_called_once_with(label="Resting HR", value="62 bpm", delta=None, help="Calculated lowest 5th percentile")

    @patch("ui_components.st")
    def test_render_metric_row_tuples(self, mock_st):
        col1, col2, col3, col4 = MagicMock(), MagicMock(), MagicMock(), MagicMock()
        mock_st.columns.return_value = [col1, col2, col3, col4]

        items = [
            ("Accuracy", "88%"),
            ("Coverage", "95%", "+2%"),
            ("F1", "0.85", None, "Macro-averaged F1 score"),
            ("PR-AUC", "0.91", "Best", "Area under PR curve"),
        ]
        ui_components.render_metric_row(items)

        mock_st.columns.assert_called_once_with(4)
        col1.metric.assert_called_once_with(label="Accuracy", value="88%", delta=None, help=None)
        col2.metric.assert_called_once_with(label="Coverage", value="95%", delta="+2%", help=None)
        col3.metric.assert_called_once_with(label="F1", value="0.85", delta=None, help="Macro-averaged F1 score")
        col4.metric.assert_called_once_with(label="PR-AUC", value="0.91", delta="Best", help="Area under PR curve")

    @patch("ui_components.st")
    def test_render_metric_row_custom_column_count(self, mock_st):
        cols = [MagicMock() for _ in range(5)]
        mock_st.columns.return_value = cols

        items = [("M1", 10), ("M2", 20)]
        ui_components.render_metric_row(items, num_columns=5)

        mock_st.columns.assert_called_once_with(5)

    @patch("ui_components.st")
    def test_render_metric_row_empty(self, mock_st):
        ui_components.render_metric_row([])
        mock_st.columns.assert_not_called()


class TestRenderAlerts(unittest.TestCase):
    """Test render_alerts across severity levels and message types."""

    @patch("ui_components.st")
    def test_render_alerts_dict_levels(self, mock_st):
        alerts = [
            {"level": "attention", "message": "High HR sustained at rest."},
            {"level": "info", "message": "Circadian dip normal."},
            {"level": "warning", "message": "Battery low."},
            {"level": "error", "message": "Sensor disconnected."},
            {"level": "success", "message": "All checks passed."},
        ]
        ui_components.render_alerts(alerts)

        self.assertEqual(mock_st.warning.call_count, 2)
        mock_st.warning.assert_has_calls([
            call("High HR sustained at rest."),
            call("Battery low."),
        ])
        mock_st.info.assert_called_once_with("Circadian dip normal.")
        mock_st.error.assert_called_once_with("Sensor disconnected.")
        mock_st.success.assert_called_once_with("All checks passed.")

    @patch("ui_components.st")
    def test_render_alerts_string_list_with_icon(self, mock_st):
        warnings = [
            "Missing 10 minutes of sensor data.",
            "Sample frequency irregular.",
        ]
        ui_components.render_alerts(warnings, default_level="warning", icon="⚠️")

        self.assertEqual(mock_st.warning.call_count, 2)
        mock_st.warning.assert_has_calls([
            call("Missing 10 minutes of sensor data.", icon="⚠️"),
            call("Sample frequency irregular.", icon="⚠️"),
        ])

    @patch("ui_components.st")
    def test_render_alerts_single_string(self, mock_st):
        ui_components.render_alerts("Single notice message")
        mock_st.info.assert_called_once_with("Single notice message")

    @patch("ui_components.st")
    def test_render_alerts_empty(self, mock_st):
        ui_components.render_alerts([])
        mock_st.info.assert_not_called()
        mock_st.warning.assert_not_called()


class TestRenderDataTable(unittest.TestCase):
    """Test render_data_table for DataFrames, empty states, and captions."""

    @patch("ui_components.st")
    def test_render_data_table_valid_dataframe(self, mock_st):
        df = pd.DataFrame({"col1": [1.1234, 2.5678], "col2": [3, 4]})
        ui_components.render_data_table(
            df,
            title="Sample Results",
            caption="Table caption text",
            round_decimals=2,
        )

        mock_st.subheader.assert_called_once_with("Sample Results")
        mock_st.caption.assert_called_once_with("Table caption text")
        mock_st.dataframe.assert_called_once()
        called_df = mock_st.dataframe.call_args[0][0]
        self.assertEqual(called_df["col1"].tolist(), [1.12, 2.57])
        self.assertEqual(mock_st.dataframe.call_args[1]["width"], "stretch")
        self.assertEqual(mock_st.dataframe.call_args[1]["hide_index"], True)

    @patch("ui_components.st")
    def test_render_data_table_empty_dataframe(self, mock_st):
        empty_df = pd.DataFrame()
        ui_components.render_data_table(empty_df, empty_msg="No episodes detected.")

        mock_st.dataframe.assert_not_called()
        mock_st.info.assert_called_once_with("No episodes detected.")

    @patch("ui_components.st")
    def test_render_data_table_none_df(self, mock_st):
        ui_components.render_data_table(None, empty_msg="No data available.")

        mock_st.dataframe.assert_not_called()
        mock_st.info.assert_called_once_with("No data available.")

    @patch("ui_components.st")
    def test_render_data_table_list_of_dicts(self, mock_st):
        data = [{"start": "10:00", "bpm": 110}]
        ui_components.render_data_table(data)

        mock_st.dataframe.assert_called_once()
        self.assertEqual(len(mock_st.dataframe.call_args[0][0]), 1)

    @patch("ui_components.st")
    def test_render_data_table_hide_index_false(self, mock_st):
        df = pd.DataFrame({"precision": [0.9]}, index=["active"])
        ui_components.render_data_table(df, hide_index=False)

        mock_st.dataframe.assert_called_once()
        self.assertEqual(mock_st.dataframe.call_args[1]["hide_index"], False)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
