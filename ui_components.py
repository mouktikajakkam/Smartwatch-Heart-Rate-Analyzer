"""
Reusable UI components for the Smartwatch Heart-Rate Analyzer.

Provides standardized presentation helpers for:
- Defensive chart rendering with fallback messages
- Metric rows with uniform column layouts
- Severity-aware alerts and warning lists
- Data tables with captions, headers, and empty-state handling
"""
from typing import Any, Dict, List, Optional, Sequence, Union

import pandas as pd
import streamlit as st


def render_chart(
    fig: Any,
    fallback_msg: str = "No data available.",
    width: str = "stretch",
    **kwargs: Any,
) -> None:
    """Render a Plotly figure with safe fallback to st.info when None or empty.

    Args:
        fig: A Plotly Figure object, or None if data was missing or empty.
        fallback_msg: Informational text displayed when fig is None.
        width: Plotly chart width option (defaults to 'stretch').
        **kwargs: Additional keyword arguments passed to st.plotly_chart.
    """
    if fig is not None:
        st.plotly_chart(fig, width=width, **kwargs)
    else:
        st.info(fallback_msg)


def render_metric_row(
    items: Sequence[Union[Dict[str, Any], Sequence[Any]]],
    num_columns: Optional[int] = None,
) -> None:
    """Render a responsive row of Streamlit KPI metrics across columns.

    Args:
        items: List of metric descriptors. Each item can be:
            - A dict: {'label': str, 'value': str|num, 'delta': str|num (opt), 'help': str (opt)}
            - A tuple: (label, value) or (label, value, delta) or (label, value, delta, help)
        num_columns: Optional column count override. Defaults to len(items).
    """
    if not items:
        return

    n = num_columns if (num_columns and num_columns > 0) else len(items)
    cols = st.columns(n)

    for i, item in enumerate(items):
        col = cols[i % n]
        if isinstance(item, dict):
            col.metric(
                label=item["label"],
                value=item["value"],
                delta=item.get("delta"),
                help=item.get("help"),
            )
        elif isinstance(item, (list, tuple)):
            label = item[0]
            val = item[1]
            delta = item[2] if len(item) > 2 else None
            help_text = item[3] if len(item) > 3 else None
            col.metric(label=label, value=val, delta=delta, help=help_text)


def render_alerts(
    alerts: Union[str, Dict[str, Any], Sequence[Union[str, Dict[str, Any]]]],
    default_level: str = "info",
    icon: Optional[str] = None,
) -> None:
    """Render alert callouts with severity matching and optional icons.

    Args:
        alerts: A single message string, an alert dict, or a list of messages/dicts.
            Alert dicts should contain 'message' and optionally 'level' and 'icon'.
        default_level: Level to use if not specified ('attention', 'warning', 'info', 'error', 'success').
        icon: Optional default emoji/icon to display.
    """
    if not alerts:
        return

    if isinstance(alerts, (str, dict)):
        alert_list = [alerts]
    else:
        alert_list = list(alerts)

    for item in alert_list:
        if isinstance(item, dict):
            msg = item.get("message", "")
            level = item.get("level", default_level)
            alert_icon = item.get("icon", icon)
        else:
            msg = str(item)
            level = default_level
            alert_icon = icon

        level_str = str(level).lower()
        kwargs: Dict[str, Any] = {"icon": alert_icon} if alert_icon else {}

        if level_str in ("attention", "warning", "warn"):
            st.warning(msg, **kwargs)
        elif level_str in ("error", "danger", "critical"):
            st.error(msg, **kwargs)
        elif level_str in ("success", "ok"):
            st.success(msg, **kwargs)
        else:
            st.info(msg, **kwargs)


def render_data_table(
    df: Optional[Union[pd.DataFrame, List[Dict[str, Any]]]],
    title: Optional[str] = None,
    caption: Optional[str] = None,
    empty_msg: Optional[str] = None,
    width: str = "stretch",
    hide_index: bool = True,
    round_decimals: Optional[int] = None,
) -> None:
    """Render a DataFrame with optional title, caption, index visibility, and empty-state handling.

    Args:
        df: Pandas DataFrame or list of row dicts.
        title: Optional subheader rendered before the table.
        caption: Optional caption text rendered below the table.
        empty_msg: Optional info message rendered if df is empty or None.
        width: Display width for st.dataframe (defaults to 'stretch').
        hide_index: Whether to hide the dataframe index (defaults to True).
        round_decimals: Optional decimal precision for rounding numeric columns.
    """
    if title:
        st.subheader(title)

    if df is None:
        if empty_msg:
            st.info(empty_msg)
        return

    if isinstance(df, list):
        if not df:
            if empty_msg:
                st.info(empty_msg)
            return
        df = pd.DataFrame(df)

    if isinstance(df, pd.DataFrame) and df.empty:
        if empty_msg:
            st.info(empty_msg)
        return

    data = df
    if round_decimals is not None and isinstance(data, pd.DataFrame):
        data = data.round(round_decimals)

    st.dataframe(data, width=width, hide_index=hide_index)

    if caption:
        st.caption(caption)
