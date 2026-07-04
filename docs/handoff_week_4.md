# Handoff: Water Stress Watch v0 → v1 Kickoff (Week 4)

> **Purpose:** Self-contained prompt for a fresh Hermes session to start **Week 4 — v1 ML training kickoff on Colab Pro.** Read this file once, then act. v0 is shipped (data + map + case study + methodology); this session is the first slice of v1.

---

## TL;DR — What to Build This Week

Build the **v1 ML training foundation** on Colab Pro. This is *not* a fully-trained v1 model — it's the **skeleton + data collection pipeline** that Hiroaki will use to train the model interactively in Colab. Specifically:

1. A Colab-ready notebook skeleton at `notebooks/04_ml_training.ipynb` covering the data loading, feature engineering, model architecture, validation, and explainability sections — but with the actual training cells left for Hiroaki to run with the A100.
2. The **training-set extraction pipeline** that pulls disclosed WUE/water data from Google / Microsoft / Meta / **AWS** public sustainability reports into a `data/processed/ml_training_set.csv`. This is the part that can and should be done on the local machine.
3. The **inference data** (`data/processed/us_dc_with_stress.csv`) ready as a feature matrix for the model to score at deployment time. This already exists from Week 2; just verify it has the columns the v1 model needs.
4. A short **methodology addendum** (`methodology_v1.md` or appended to `methodology.md`) covering what v1 changes, why the ML model is needed, and how to interpret its output.

**Out of scope for Week 4** (deferred):
- The actual XGBoost model training run (Hiroaki does this in Colab interactively with A100)
- Optuna hyperparameter sweep
- Cooling-type classifier (separate model; Week 5+)
- Sub-basin (HUC-8) stress overlay
- Replacing the v0 map with v1 output

---

## Project Path & Owner

- **Path:** `/root/project/datacenter_water_stress/`
- **Owner:** Hiroaki Oshima (founder building AI startup in Japan, ex-CV data engineer, Berkeley DS, has Colab Pro subscription)
- **Repo license:** MIT (code), CC-BY 4.0 (data, docs, methodology)

## What's Already Done (v0 Shipped, 2026-07-04)

Read these in this order to get full context (don't re-run the pipelines):

1. `docs/v0_plan.md` — the original v0 plan, including the **v1 preview section** (lines 179-195) which is the v1 spec
2. `docs/week_2_summary.md` — what got built in Week 2 (estimation pipeline, methodology issues found)
3. `docs/data_dictionary.md` — column definitions for all 6 v0 datasets
4. `case_studies/phoenix_az.md` — the Phoenix case study (good example of how Hiroaki wants narrative content)
5. `methodology.md` — the v0 methodology writeup (15 sections, 7 citations)
6. `README.md` — public intro

**Week 3 work is also done** but is lighter on methodology; you can skip `case_studies/blog_draft.md` if context is tight.

**v0 deliverables on disk:**
- `data/processed/us_dc_with_stress.csv` — **1,575 rows × 25 columns** (the v0 inference table; v1 will score this through the trained model)
- `data/processed/us_dc_locations.csv` — 1,575 rows, cleaned
- `assets/map_v0.html` — the v0 public map (8.4 MB)
- All scripts in `src/` — idempotent, no need to re-run

## Hiroaki's Locked Decisions (do not revisit without asking)

From Week 1 + Week 2 reviews (5 questions, all locked):

1. **MW estimation policy:** operator-class heuristic (already shipped in v0)
2. **Phoenix case study:** primary; Loudoun VA is backup (Phoenix case study is shipped)
3. **License:** WRI Aqueduct CC-BY 4.0; cite Kuzma et al. (2023) in any methodology
4. **Stress granularity:** state-level for v0; sub-state is v1+ (NOT a Week 4 task)
5. **Source data:** only `orimadros_datacenters.csv` for v0 (1,605-row MIT)

From Week 4 review (5 questions, all locked):

6. **Week 4 scope:** v1 ML kickoff on Colab Pro. Skeleton + data collection only. Actual model training is interactive in Colab UI by Hiroaki.
7. **Colab Pro subscription** — use A100 for tuning when training runs. Notebook must be Colab-ready (clean `pip install` cell at top, drive paths, GPU mount).
8. **v0.5 vs v1.0 naming:** v0.5 = bug fixes / methodology corrections; v1.0 = new model; v1.5 = sub-basin overlay; v2.0 = global.
9. **Lumen / Cogent reclassification:** wait for the v1 model. If v1 outputs look wrong for these operators, revisit in v0.5.
10. **ML training target:** predict **WUE** (L/kWh). At inference: `v1_water_lpd = v0_est_mw × 1000 × 24 × 0.7 × v1_predicted_wue × climate_adj`. The 0.7 load factor and climate_adj from v0 stay; ML replaces the WUE lookup.
11. **Training set operators:** Google + Microsoft + Meta + **AWS**. AWS rows are region-level (flagged `is_aggregate=True`); Apple skipped (less water disclosure).
12. **Validation strategy:** stratified k-fold across all 4 operators (5-fold) + leave-one-operator-out generalization test.

(Full reasoning in the "Hiroaki's Decisions" section near the bottom of this document.)

## Week 4 Tasks (in order)

### Task 4.1: Extract the ML training set from public sustainability reports

The v0 physics model uses a single WUE_DEFAULT=1.8 L/kWh. The v1 ML model needs to learn from real disclosed per-facility WUE values. The training set is small (~100 points) and comes from four operators that actually disclose:

- **Google:** 2024 Environmental Report has 25-30 data center entries with location, PUE, WUE, water source, and renewable energy %. Per-region aggregates may need to be disaggregated.
- **Microsoft:** 2024 Sustainability Report has 60+ data center entries with location, water use (m³/year), and water source. WUE is computed as L/kWh from disclosed water + electricity.
- **Meta:** 2023 Sustainability Report has 15 data center entries with location, water use, and WUE.
- **Amazon AWS:** Sustainability reports disclose WUE per **region** (e.g., us-east-1), not per data center. AWS rows in the training set are flagged in the `notes` column as region-level averages; the model learns from them but with reduced weight (or via a separate "is_aggregate" flag in features).

**This is the most research-heavy task.** Expect to spend 1-2 hours downloading PDFs, scraping tables, and reconciling. Target: ~100 rows total (Google 30 + Microsoft 60 + Meta 15 + AWS 10-20 region rows). If you can extract 80+ with reasonable confidence, that's the floor for v1 to work.

**Inputs:**
- Public sustainability reports (web search for "Google 2024 environmental report PDF", "Microsoft 2024 sustainability report PDF", "Meta 2023 sustainability report PDF", "AWS sustainability report PDF region WUE"). Direct URLs change yearly; check the operators' sustainability pages.
- For WUE calculation, you also need **per-facility annual electricity use** (MWh), which is in the same reports or in utility filings. For AWS, electricity may be at region level; the WUE comes from region-level water / region-level electricity.

**Output:** `data/processed/ml_training_set.csv` with at minimum these columns:
- `operator` (Google / Microsoft / Meta / AWS)
- `facility_name` (or "us-east-1 region" for AWS)
- `latitude`, `longitude` (geocode from the address; for AWS rows, use the region's representative centroid)
- `wue_disclosed` (L/kWh) — what the operator reports, or compute from disclosed water + electricity
- `annual_water_m3` (m³/year, from the report; verify the unit)
- `annual_electricity_mwh` (MWh/year, from the report; verify the unit)
- `is_aggregate` (bool, True for AWS region-level rows; lets the model weight them differently)
- `cooling_type` if disclosed (free-air / water-cooled / evaporative / unknown)
- `report_year` (most recent report available; cite which)
- `source_url` (which report / page)
- `notes` (any caveats: "regional aggregate, not per-facility", "WUE computed from water/electricity", etc.)

**Validation:**
- Google 2024 fleet-wide WUE should be ~1.0-1.5 L/kWh. Microsoft ~1.0 L/kWh. Meta ~0.5-0.8 L/kWh (mostly dry-cooling). AWS region WUE varies widely by climate (Ireland ~0, Virginia ~1.0, arid regions ~2.0+). If your extracted values are wildly off, re-check unit conversions.
- A facility in Arizona should have higher WUE than the same operator's facility in Ireland. If it doesn't, double-check.

**Code style:** Put the extraction logic in `src/build_ml_training_set.py` (idempotent, like every other src script). Comments in the script should reference which report each row came from so future audits are possible.

### Task 4.2: Build the v1 inference feature matrix

The model needs to score all 1,575 v0 facilities at inference time. Take `data/processed/us_dc_with_stress.csv` and add the features the v1 model will need beyond what v0 has. The v0 plan calls for "30+ features" but the minimum viable set is:

- All v0 columns preserved (do NOT drop the physics estimates — v1 will use them as a baseline to compare against)
- `operator_class` (one-hot or label-encoded; the same OPERATOR_CLASS dictionary from `src/estimate_power.py` — import it)
- `state_bws_score` (already there as `bws_score`)
- `wet_bulb_c` (already there)
- `climate_adj` (already there)
- `sqft_total_space` if available (47% missing → handle as NaN, not zero)
- `miles_to_nearest_airport` (98% coverage)
- `is_hyperscaler_self`, `is_colocation_major`, `is_colocation_secondary` (one-hot flags from operator class)
- `latitude`, `longitude` (keep; the model can learn regional effects)
- `lat_lon_grid_cell` (a coarse grid cell, e.g. 1°×1° box ID, for a regional feature)
- `cooling_type_imputed` (v0 default: 'unknown' for all; v1 will later train a classifier)
- `report_year` (constant for now; future re-trains can update)

**Output:** `data/processed/v1_inference_features.csv` with the same 1,575 rows, plus 10-15 added feature columns.

**Code style:** New script `src/build_v1_features.py`. Idempotent.

### Task 4.3: Colab-ready notebook skeleton

`notebooks/04_ml_training.ipynb` — this is the deliverable Hiroaki will open in Colab and run interactively. It should be **Jupyter notebook format (not .py)** because Colab UI is the consumption mode. Structure:

```python
# Cell 1: Title and overview
# Cell 2: pip install (xgboost, scikit-learn, optuna, shap, pandas, numpy)
# Cell 3: Imports
# Cell 4: Mount Google Drive (for persistence)
# Cell 5: Load training set from data/processed/ml_training_set.csv
#          (Hiroaki will need to upload this CSV to Drive first, or sync from this repo)
# Cell 6: Load v1 inference features
# Cell 7: Feature engineering (one-hot encoding, missing-value handling, train/test split)
#          - Stratified k-fold across all 4 operators (5-fold CV)
#          - "Leave-one-operator-out" generalization test: train on 3 operators, test on the 4th
#          - Use `is_aggregate` flag to downweight AWS region-level rows in training
# Cell 8: Baseline: physics model on the same training set
#          (compare the v0 formula's WUE=1.8 prediction against disclosed WUE; this is the floor)
# Cell 9: XGBoost model (default hyperparameters; Hiroaki tunes)
# Cell 10: Validation (RMSE, MAE, R² on the 5-fold CV + leave-one-operator-out)
# Cell 11: Feature importance (XGBoost built-in)
# Cell 12: SHAP values (using shap library)
# Cell 13: Predictions on v1 inference features (1,575 facilities)
# Cell 14: Save model artifact (joblib) + predictions CSV
#          (Hiroaki downloads these to /root/project/datacenter_water_stress/models/ when done)
# Cell 15: Comparison plot: v0 physics WUE=1.8 vs v1 ML on a state-aggregate basis
# Cell 16: v1 water L/day = v0_est_mw × 1000 × 24 × 0.7 × v1_predicted_wue × climate_adj
#          (apply the inference formula to all 1,575 v0 facilities; this is the v1 output)
```

**Important:** Each cell should be small, runnable independently, and have a comment block explaining what it does. The cell titles (H1 in Colab) should be meaningful so Hiroaki can navigate the notebook.

**Don't actually run the training cells.** The skeleton should be executable up to the point of "model.fit()" but the training itself is Hiroaki's job in the Colab UI with A100. Add a clear `# TODO: run with A100` comment to the training cell.

### Task 4.4: v1 methodology addendum

Append to `methodology.md` (don't replace) a new section:

> ## 16. v1: ML-corrected water-use estimates (Week 4+)
>
> [Document what v1 changes vs v0, the training set composition, the validation strategy, and how to interpret the model output. Include the v0 physics formula as a baseline that v1 must beat.]

Or, if Hiroaki prefers a separate file, write `methodology_v1.md` that references the v0 methodology. **Default to appending** to keep one source of truth.

The addendum should include:
- **Why v1:** the v0 ±50% uncertainty band is dominated by the cooling-type unknown; ML can narrow it by learning per-operator WUE from disclosed data.
- **Training set provenance:** Google 2024 + Microsoft 2024 + Meta 2023 + AWS region disclosures, ~100 points total. AWS rows are region-level (flagged with `is_aggregate=True`).
- **Target variable:** WUE (L/kWh), the standard water-efficiency metric. Inference: `v1_water_lpd = v0_est_mw × 1000 × 24 × 0.7 × v1_predicted_wue × climate_adj`.
- **Features:** list the 10-15 features in `v1_inference_features.csv` with one-line rationale for each.
- **Validation metrics:** RMSE, MAE, R² on stratified 5-fold CV + leave-one-operator-out generalization test.
- **Caveat:** the model is only as good as the training set. With ~100 points (and some at region level), overfitting is the main risk. The XGBoost built-in feature importance + SHAP values are how Hiroaki will spot this.

### Task 4.5: Optional but recommended — model output schema

Define what the v1 model outputs at inference time. A small `src/v1_output_schema.py` or a docstring in `notebooks/04_ml_training.ipynb` documenting:

For each of 1,575 v0 facilities, the v1 model should produce:
- `est_liters_per_day_v1` (point estimate)
- `est_liters_per_day_v1_low` (10th percentile, from quantile regression or a bootstrap)
- `est_liters_per_day_v1_high` (90th percentile)
- `v1_uncertainty_band_width_lpd` (high − low; the headline improvement vs v0's flat ±50%)
- `v1_minus_v0_pct` (the % difference between v1 and v0 estimates; this is what journalists will want)

This isn't the model — it's the schema. It tells Hiroaki what to save from his training run so the v1 results can be merged back into the v0 dataset.

---

## Week 4 Done When

- [ ] `data/processed/ml_training_set.csv` exists with ≥ 80 rows from Google / Microsoft / Meta / AWS public disclosures, with `wue_disclosed` and provenance columns (AWS rows flagged as `is_aggregate=True`)
- [ ] `src/build_ml_training_set.py` is idempotent and has comments citing each report URL
- [ ] `data/processed/v1_inference_features.csv` exists with the 1,575 v0 facilities + 10-15 added features
- [ ] `src/build_v1_features.py` is idempotent
- [ ] `notebooks/04_ml_training.ipynb` exists with the 15-cell skeleton, executable up to the training cell
- [ ] `methodology.md` has Section 16 (v1 ML addendum) appended
- [ ] The v0 → v1 output schema is documented (in the notebook or a separate file)
- [ ] A short session report in `docs/week_4_summary.md` listing what got built, what's open, and any questions for Hiroaki

## Tones & Principles (Same as v0)

- **Civic, not preachy.** Write like FracTracker — journalism/advocacy hybrid.
- **Cite everything.** The training set is the v1 foundation; every row must trace to a public report.
- **Honest about uncertainty.** v0 has ±50%; v1 should narrow this but it should not pretend to be exact. The validation metrics and SHAP values are the honesty tools.
- **Build the public's counter-infrastructure.** v1 is a refinement of the v0 transparency goal, not a pivot to ML research.

## Out of Scope for Week 4 (Do Not Do)

- Actual model training run (Hiroaki does this in Colab UI with A100)
- Optuna hyperparameter sweep (Week 5+)
- Cooling-type classifier (separate model; Week 5+)
- Sub-basin (HUC-8) stress overlay (Week 5+)
- v0.5 polish items: design-day wet-bulb fix, Lumen/Cogent reclassification (deferred; could be Week 4.5 or a side-quest)
- Replacing the v0 map with v1 output (deferred until v1 model is trained and validated)
- Press / publicity / GitHub repo description cleanup (separate workstream)
- Real-time data, API, database (v2)

## Reproducing Week 4 from scratch

```bash
cd /root/project/datacenter_water_stress

test -d .venv || python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# v0 is already built — don't re-run unless you need to
# .venv/bin/python src/clean_locations.py
# .venv/bin/python src/build_wri_stress_lookup.py
# .venv/bin/python src/estimate_power.py
# .venv/bin/python src/fetch_climate.py
# .venv/bin/python src/estimate_water.py
# .venv/bin/python src/join_water_stress.py
# .venv/bin/python src/build_map.py

# Week 4
.venv/bin/python src/build_ml_training_set.py    # → ml_training_set.csv
.venv/bin/python src/build_v1_features.py         # → v1_inference_features.csv
# notebooks/04_ml_training.ipynb is hand-edited, not generated

# Then Hiroaki opens the notebook in Colab Pro, runs cells 1-13,
# saves model + predictions to Drive, downloads to local models/

# Optional: regenerate v1 features against the v0 inference table
# if the v0 input has been updated
```

The two new scripts must be idempotent (re-running with the same input produces the same output). The notebook is hand-edited and tracked in git.

## Hiroaki's Decisions (resolved 2026-07-04)

**Use these; do not revisit without explicit instruction.** These are the locked decisions that came up in the Week 3 review.

1. **v0.5 vs v1.0 naming:** ✅ **v0.5.** The design-day wet-bulb fix is a v0.5 patch, not v1.0. v1.0 stays as "ML-corrected estimates." Going forward: v0.5 = bug fixes / methodology corrections; v1.0 = new model; v1.5 = sub-basin overlay; v2.0 = global.
2. **Lumen / Cogent reclassification:** ✅ **Wait for the v1 model.** The v1 ML will learn the per-operator WUE from disclosed data, so manual reclassification is less important. If v1 outputs look wrong for Lumen/Cogent, revisit in v0.5.
3. **ML training target:** ✅ **Predict WUE** (L/kWh). WUE is `water_liters / electricity_kWh` — a normalized efficiency metric. The model learns operator/cooling signal, not facility size. At inference: `v1_water_lpd = v0_est_mw × 1000 × 24 × 0.7 × v1_predicted_wue × climate_adj`. The 0.7 load factor and climate_adj from v0 stay; ML replaces the WUE lookup.
4. **Training set target:** ✅ **Add AWS if feasible.** v0 plan's Google (30) + Microsoft (60) + Meta (15) + **AWS** (region-level, not per-facility, but useful). AWS discloses WUE per region in their sustainability reports, not per data center. Treat AWS rows as having WUE at region resolution (e.g., "us-east-1, all facilities averaged") and flag them in the `notes` column. Apple is not worth it (less water disclosure).
5. **Validation strategy:** ✅ **Stratified k-fold across all four operators**, with one operator held out as a generalization test. 5-fold CV for the main model; leave one operator out (rotating) for the "how well does this generalize" test.

---

## How to Start This Session

1. Read this entire document.
2. Read `docs/v0_plan.md` Section "v1 Preview" (lines 179-195) — that's the v1 spec.
3. Read `docs/week_2_summary.md` — the methodology issues found (1, 2, 3) are why v1 exists.
4. Read `docs/data_dictionary.md` — the v0 schema you'll be extending.
5. Confirm venv exists (`ls .venv/bin/python`); if not, `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`.
6. Begin Task 4.1 (build_ml_training_set.py). This is the research-heavy task; do it first so the rest can reference the schema.
7. Work through Tasks 4.1 → 4.5 sequentially.
8. End of session: print a summary report of what got built, what's open, and any questions for Hiroaki.

**If a task is ambiguous, use the v0 plan's defaults.** The user has full latitude; the methodology must be defensible to a journalist or peer reviewer, not to an internal stakeholder.

**Important for the ML training set task (4.1):** Do not hallucinate WUE values. If a report says "PUE 1.10" but doesn't disclose WUE, leave the WUE column NaN and put a note. A training set with 60 honest rows beats 120 rows where 60 are guessed.
