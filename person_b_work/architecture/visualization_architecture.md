# Architecture: Visualization Layer (`visualizations.py`)

## 1. Design Principles
1. **Decoupling from UI**: Functions must never import `streamlit`. They receive plain Python data structures (`pd.DataFrame`, `list`, `np.ndarray`, `bool`) and return a `plotly.graph_objects.Figure` or `None`.
2. **Defensive Against Incomplete Data**: Rather than raising exceptions, every function validates that required columns are present and input DataFrames are non-empty. If data is insufficient, `None` is returned.
3. **Immutability of Caller Data**: Functions that derive temporary columns (such as `activity_scatter`) copy the input DataFrame (`mm = minutes.copy()`) to prevent side-effects on the caller's dataset.
4. **Consistent Visual Language**: A single color map (`ACT_COLORS`) is shared across bar charts, donut charts, and time series scatter plots.

---

## 2. Shared Palette: `ACT_COLORS`

```python
ACT_COLORS = {
    "sedentary": "#94a3b8",   # Slate Gray
    "light":     "#38bdf8",   # Sky Blue
    "active":    "#f97316",   # Vibrant Orange
    "asleep":    "#6366f1",   # Indigo
}
```

---

## 3. Function Inventory & Specifications

### `hr_timeline(clean, anom_df, show_ma=True) -> Optional[go.Figure]`
* **Purpose**: Primary interactive heart rate timeline.
* **Input**:
  * `clean`: DataFrame with `timestamp`, `hr_smooth`, and optional moving average columns (`ma_30min`, `ma_1h`).
  * `anom_df`: Anomaly table DataFrame with `window_start`, `mean`, and boolean `is_anomaly`.
  * `show_ma`: Boolean controlling display of 30-minute and 1-hour moving averages.
* **Rendering**: Uses `Scattergl` for smoothed heart rate and moving averages to optimize rendering performance for large time series. Overlays anomalies as red 'x' markers.

### `hr_histogram(clean) -> Optional[go.Figure]`
* **Purpose**: Distribution of smoothed heart rate readings.
* **Input**: `clean` DataFrame with `hr_smooth` column.
* **Rendering**: `px.histogram` with 40 bins.

### `circadian_trend(circadian) -> Optional[go.Figure]`
* **Purpose**: Diurnal cycle line chart (average heart rate by hour of day).
* **Input**: `circadian` DataFrame with `hour` (0–23) and `mean_hr`.
* **Rendering**: `px.line` with point markers.

### `daily_trend(daily) -> Optional[go.Figure]`
* **Purpose**: Multi-line tracking of daily cardiovascular metrics across the monitoring window.
* **Input**: `daily` DataFrame with `date`, `resting_hr`, `mean_hr`, `max_hr`.
* **Rendering**: `px.line` with markers for each metric series.

### `activity_bar(hr_by_activity) -> Optional[go.Figure]`
* **Purpose**: Bar chart showing median heart rate for each activity category.
* **Input**: `hr_by_activity` DataFrame with `activity` and `median_hr`.
* **Rendering**: `px.bar` colored by `activity` using `ACT_COLORS` with data labels.

### `activity_pie(hr_by_activity) -> Optional[go.Figure]`
* **Purpose**: Donut chart illustrating proportion of time spent in each activity state.
* **Input**: `hr_by_activity` DataFrame with `activity` and `minutes`.
* **Rendering**: `px.pie` with `hole=0.5` colored by `ACT_COLORS`.

### `activity_scatter(minutes) -> Optional[go.Figure]`
* **Purpose**: High-density minute-by-minute heart rate scatter plot colored by activity state (`sedentary`, `light`, `active`, `asleep`).
* **Input**: `minutes` DataFrame with `minute`, `hr_mean`, `activity`, `is_asleep`.
* **Rendering**: `px.scatter` with WebGL rendering (`render_mode="webgl"`) and marker size 3 for smooth rendering of hundreds of thousands of points.

### `anomaly_score_histogram(anom_df) -> Optional[go.Figure]`
* **Purpose**: Distribution of window anomaly scores, stratified by detection status.
* **Input**: `anom_df` DataFrame with `anomaly_score` and `is_anomaly`.
* **Rendering**: `px.histogram` with 40 bins colored by `is_anomaly`.

### `cluster_scatter(cluster_table) -> Optional[go.Figure]`
* **Purpose**: 2D scatter plot of KMeans behavioural groups.
* **Input**: `cluster_table` DataFrame with `mean` (mean HR), `std` (variability), and `cluster` (group ID).
* **Rendering**: `px.scatter` colored by cluster label.

### `confusion_matrix_heatmap(cm, class_names) -> Optional[go.Figure]`
* **Purpose**: Row-normalized confusion matrix heatmap for supervised activity classifier evaluation.
* **Input**:
  * `cm`: 2D list or `np.ndarray` of confusion counts.
  * `class_names`: List of class labels (e.g. `["sedentary", "light", "active"]`).
* **Rendering**: `px.imshow` normalized per row, Blues color scale, formatted with percentage text labels (`.0%`). Safe against division-by-zero for unpopulated classes.
