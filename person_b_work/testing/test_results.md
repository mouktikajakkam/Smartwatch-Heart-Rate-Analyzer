# Test Results & Validation Summary

This document separates **cryptographically confirmed baseline facts** from **test execution results** across all testing levels for Person B's work.

---

## 1. Cryptographic Baseline Integrity (SHA-256)
* **Date Executed**: 2026-10-29
* **Verification Method**: Automated SHA-256 hash comparison against original baseline extraction (`Smartwatch_HR_App-main/Smartwatch_HR_App-main`).
* **Findings**:
  * **18 critical files matched** the baseline extraction identically (100% match):
    * All 12 Python files in `hr_backend/`
    * Both model files in `hr_backend/models/` (`activity_model.joblib`, `activity_model.json`)
    * All 4 datasets in `sample_data/`
    * `requirements.txt`
    * `.streamlit/config.toml`
  * **0 baseline files** are missing or corrupted.
  * **Only 1 file differs by design**: `app.py` (Outer: 6,381 bytes, SHA-256: `7045414861FABC772BF1C5ED1956CC46391537A5D3C247EF173B9B86CECADE54`), reflecting the modularization into `dashboard.py` and `ui_components.py`.
  * **Person B Modules**: `visualizations.py`, `ui_components.py`, `dashboard.py`, and test suites (`test_visualizations.py`, `test_ui_components.py`, `test_dashboard.py`).

---

## 2. Compilation Verification
* **Command**: `python -m py_compile app.py dashboard.py ui_components.py visualizations.py`
* **Status**: ✅ **PASSED (Exit code 0)**
* **Detail**: Zero syntax, import, or typing errors across all four modules.

---

## 3. Visualization Unit Testing: `test_visualizations.py`
* **Command**: `python test_visualizations.py`
* **Status**: ✅ **ALL 31 CHECKS PASSED**
* **Detailed Breakdown**:
  * `hr_timeline`: Figure generation, moving-averages toggle on/off, empty anomalies handling, empty clean DataFrame guard (returns `None`).
  * `hr_histogram`: Figure generation, empty DataFrame guard, missing `hr_smooth` column guard.
  * `circadian_trend`: Figure generation, empty DataFrame guard.
  * `daily_trend`: Figure generation, empty DataFrame guard.
  * `activity_bar`: Figure generation, empty DataFrame guard.
  * `activity_pie`: Figure generation, empty DataFrame guard.
  * `activity_scatter`: Figure generation, empty DataFrame guard, missing `activity` column guard.
  * `anomaly_score_histogram`: Figure generation, empty DataFrame guard.
  * `cluster_scatter`: Figure generation, empty DataFrame guard, missing `cluster` column guard.
  * `confusion_matrix_heatmap`: List input parsing, NumPy ndarray parsing, empty input guard, zero-sum row safety (prevents division by zero).
  * `NaN` Handling: Verified for `hr_timeline` and `hr_histogram`.
  * DataFrame Immutability: Verified that `activity_scatter` does not mutate caller DataFrame columns.
  * Palette Validation: Verified that `ACT_COLORS` contains all expected keys (`sedentary`, `light`, `active`, `asleep`).

---

## 4. Reusable UI Component Testing: `test_ui_components.py`
* **Command**: `python test_ui_components.py`
* **Status**: ✅ **ALL 17 CHECKS PASSED**
* **Detailed Breakdown**:
  * `render_chart`: Valid figure rendering, `None` fallback handling with custom messages, kwargs passthrough.
  * `render_metric_row`: Dict specification parsing, tuple specification parsing (2-, 3-, 4-element), custom column counts, empty input no-op.
  * `render_alerts`: Severity levels (`attention`, `warning`, `info`, `error`, `success`), string lists with custom icons (`icon="⚠️"`), single strings, empty list no-op.
  * `render_data_table`: DataFrame rendering with titles and captions, list-of-dicts conversion, numeric decimal rounding, `hide_index=False` support, empty-state messages.

---

## 5. Dashboard View Testing: `test_dashboard.py`
* **Command**: `python test_dashboard.py`
* **Status**: ✅ **ALL 8 CHECKS PASSED**
* **Detailed Breakdown**:
  * `render_tab_overview`: Verified rendering of Data Quality and Key Numbers metrics rows, warnings, and interpretation text.
  * `render_tab_activity_sleep`: Verified rendering of activity breakdown bar, pie chart, scatter plot, and still episodes table.
  * `render_tab_visualizations`: Verified timeline with MA checkbox toggle, histogram, circadian trend, daily trend, and exertion recovery table.
  * `render_tab_machine_learning`: Verified unusual-window explanation, anomaly score histogram, top-50 anomalies table, and cluster scatter.
  * `render_tab_model_evaluation`: Verified supervised model metrics, baseline table, confusion matrix heatmap, and benchmark button.
  * `render_tab_report_export`: Verified PDF report download button and CSV bundle export download buttons.
  * `render_tab_about`: Verified objectives table, limitations, and medical disclaimer.
  * `render_dashboard`: Verified coordinated rendering of all 7 tabs in order using tab context managers.

---

## 6. Headless Application Testing: `test_app.py`
* **Command**: `python test_app.py`
* **Framework**: Streamlit `AppTest` (headless simulation)
* **Status**: ✅ **ALL 3 SCENARIOS PASSED**
* **Observed Metrics**:
  * **Scenario 1 ("Sample: 7 days with activity & sleep")**:
    * `exception=False`, `errors=[]`
    * Output: 12 metrics, 5 dataframes, 5 infos.
    * Anomaly benchmark button execution: `exception=False`, metrics: `Recall=0.59`, `Precision=0.38`, `F1=0.46`, `ROC-AUC=0.93`, `PR-AUC=0.40`.
  * **Scenario 2 ("Sample: heart rate only")**:
    * `exception=False`, `errors=[]`
    * Output: 12 metrics, 5 dataframes, 6 infos.
  * **Scenario 3 ("Synthetic (generated)")**:
    * `exception=False`, `errors=[]`
    * Output: 12 metrics, 5 dataframes, 6 infos.

---

## 7. Backend Pipeline Testing: `test_pipeline.py`
* **Command**: `python test_pipeline.py`
* **Status**: ⚠️ **PARTIAL (First 10 checks passed; failed on check 11)**
* **Checks Passed Prior to Failure**:
  1. `activity model loads (LOPO accuracy 0.813)`
  2. `sample + context analyses`
  3. `activity observed`
  4. `sleep observed`
  5. `context-aware anomalies`
  6. `resting HR plausible (57.7 bpm)`
  7. `disclaimer present`
  8. `HR-only analyses`
  9. `activity estimated by model`
  10. `HR-only resting close to observed (54.5 vs 57.7)`
* **Failure Point**: Line 54 in `test_pipeline.py` raises `ValueError: time data '2024-04-12 00:00:00' doesn't match format '%m/%d/%Y %I:%M:%S %p'`.
* **Root Cause**: Backend file `hr_backend/synthetic.py:90` utilizes Unix-only `%-m/%-d` flags in `strftime`. On Windows, this is unparsed, outputting ISO strings. This is a Person A backend responsibility and was left untouched.

---

## 8. Pending Verification Tasks

> [!IMPORTANT]
> The following items have not yet been independently verified through actual rendered observation and remain pending:
> 1. **Interactive Browser Verification**: Visual verification of font styling, layout spacing, tooltips, and interactive Plotly hover cards across all 7 tabs in a live browser.
> 2. **File Downloads**: Real browser validation of clicking `⬇️ Download PDF report` and receiving a valid, non-corrupt PDF, as well as CSV bundle downloads.
> 3. **Manual Upload Testing**: Manual file drag-and-drop through the sidebar file uploader with a non-sample CSV.
