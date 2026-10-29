# Technical Dependencies & Coordination Items

This document outlines questions, shared dependencies, and coordination steps between Person B (Frontend) and Person A (Backend).

---

## 1. Technical Dependencies on Person A

### A. Windows Date-Format Compatibility in `hr_backend/synthetic.py`
* **File**: `hr_backend/synthetic.py`, line 90
* **Issue**: Uses Unix `%-m` and `%-d` flags in `strftime`, which outputs ISO dates on Windows systems and breaks `test_pipeline.py` check 11.
* **Action Required by Person A**: Update line 90 to use cross-platform date formatting so pipeline self-tests pass seamlessly on all developer operating systems.

### B. Stable Contract of `analyze()` Output Object
* The frontend relies on the exact keys returned in `result`:
  * `result.clean`: `timestamp`, `hr_smooth`, `ma_30min`, `ma_1h`
  * `result.anomalies`: `table`, `method`, `n_anomalies`, `n_windows`, `context_aware`
  * `result.context`: `hr_by_activity`, `intensity_source`, `sleep_source`, `elevated_rest_episodes`
  * `result.minutes`: `minute`, `hr_mean`, `activity`, `is_asleep`
  * `result.circadian`: `hour`, `mean_hr`
  * `result.daily`: `date`, `resting_hr`, `mean_hr`, `max_hr`
  * `result.peaks`: exertion episodes table
  * `result.clusters`: `k`, `profile`, `table`
  * `result.activity_model`: `evaluation`, `classes`, `trained_on`, `used`
* Any changes to these dictionary fields or column names in future backend updates should be coordinated with Person B.

---

## 2. Questions for Person A & Project Leadership

1. **Workspace Root Consolidation**:
   * The outer `ecg_smart_watch/` directory currently contains 21 duplicate loose files (e.g. `activity_model.py`, `context.py`, `sample_heartrate.csv`) copied out during previous setup.
   * Can we proceed with archiving these loose duplicates so that developers only interact with `hr_backend/`, `sample_data/`, and `models/`?
2. **Git Repository Setup**:
   * Currently, neither the outer folder nor the inner extraction is an isolated Git repository (they reside within the user home directory Git tree).
   * Should we initialize a dedicated Git repository at `Downloads/VIT Downloads/ecg_smart_watch` with a clean `.gitignore` once the cleanup plan is approved?
3. **Phase 4 Visual Feature Roadmap**:
   * With Phase 3 architectural modularization complete (3-tier separation into `app.py`, `dashboard.py`, and `ui_components.py`), the UI is decoupled and ready for feature additions. For a future Phase 4, are there specific advanced visualizations or filters (e.g. multi-participant comparison, live sensor streaming, or custom threshold tuning) your project head prioritizes?

---

## 3. Joint Verification Checklist Before Final Release

- [ ] Person A resolves the Windows date format string in `hr_backend/synthetic.py`.
- [ ] Run complete `test_pipeline.py` to confirm all 16 pipeline checks pass on Windows.
- [ ] Perform live interactive browser walkthrough at `http://localhost:8501`.
- [ ] Test real PDF download button in browser and verify layout of generated PDF.
- [ ] Test real CSV export bundle download in browser and inspect CSV contents.
