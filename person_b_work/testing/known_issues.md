# Known Issues & Environmental Constraints

This document records technical issues, cross-platform limitations, and environmental constraints identified during the project audit and testing.

---

## 1. Backend: Windows Date Format Specifier in `hr_backend/synthetic.py`

* **Component**: Backend (`hr_backend/synthetic.py`, line 90)
* **Owner**: **Person A (Pipeline / Backend)**
* **Severity**: Medium (Impacts Windows testing of synthetic data parsing)
* **Description**:
  In `synthetic.py`, the synthetic generator attempts to format timestamp strings in Fitbit export style using:
  ```python
  df["Time"] = df["Time"].dt.strftime("%-m/%-d/%Y %-I:%M:%S %p")
  ```
* **Impact**:
  * On Unix/Linux, `%-m` and `%-d` strip leading zeros from month and day.
  * On Windows C-runtime, the `-` flag is invalid. Python on Windows ignores it or outputs the default ISO format (`2024-04-12 00:00:00`).
  * Consequently, `test_pipeline.py` (line 54) crashes when attempting to parse the generated column with explicit format `"%m/%d/%Y %I:%M:%S %p"`.
* **Recommended Fix for Person A**:
  Use platform-independent date formatting or standard `strftime` without leading-zero strip flags, e.g.:
  ```python
  import sys
  flag = "%#" if sys.platform == "win32" else "%-"
  df["Time"] = df["Time"].dt.strftime(f"{flag}m/{flag}d/%Y {flag}I:%M:%S %p")
  ```
  *Note: Per strict project guidelines, Person B did not modify this file.*

---

## 2. Workspace: Outer Directory Redundant Duplicate Files

* **Component**: Workspace File Organization
* **Owner**: Joint / Person B
* **Severity**: Low (Functional redundancy, risk of editing wrong copy)
* **Description**:
  During earlier troubleshooting, the contents of `hr_backend/`, `sample_data/`, and `models/` were copied directly into the outer root directory.
* **Audit Confirmation**:
  * 21 files at the outer root duplicate identical files inside their respective subdirectories (`hr_backend/`, `sample_data/`, `models/`).
  * `app.py` properly imports from `from hr_backend import analyze, fitbit`, reading exclusively from the package directory.
* **Recommendation**:
  After approval, archive or clean up these 21 loose root copies to ensure developers and Git only track the canonical subfolders.

---

## 3. Environment: Subagent Headless Browser Network Restriction

* **Component**: Automated Subagent Browser Inspection
* **Owner**: Environment / Tooling
* **Severity**: Low (Workaround available via manual browser testing)
* **Description**:
  When launching an automated browser subagent to visit `http://localhost:8501`, the internal sandbox Playwright instance encountered `net::ERR_ABORTED`.
* **Resolution**:
  The Streamlit server is active and responding locally (`HTTP/1.1 200 OK`). Interactive verification should be conducted directly in the host browser.
