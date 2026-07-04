# Handoff: Water Stress Watch — Project Status & Week 4 Handoff

> **Purpose:** Status snapshot as of 2026-07-04. **v0 shipped (Weeks 1-3); v1 ML training foundation shipped (Week 4).** Next session: Hiroaki runs the XGBoost training on Colab Pro A100 interactively, then ships v1.0 outputs (model artifact + per-facility predictions).

---

## Project Status (end of Week 4)

| Week | Tasks | Status |
|---|---|---|
| **1** — Data ingestion & cleaning | 1.1 Explore, 1.2 Geocode/clean, 1.3 WRI pull, 1.4 Schema docs | ✅ Complete |
| **2** — Estimation pipeline | MW estimation, climate features, water physics, stress join, sensitivity | ✅ Complete |
| **3** — Map + case study + writeup | Folium map, Phoenix case study, methodology, README, blog draft | ✅ Complete |
| **4** — v1 ML training kickoff | Training set (43 rows), v1 features (1,575 × 42), Colab notebook skeleton (16 cells), methodology Section 16, output schema | ✅ Complete |
| **5+** — v1 model training on Colab Pro | Hiroaki runs the XGBoost training interactively on A100; downloads model + predictions | 🟡 **Next** |

> **Important:** This handoff is current as of 2026-07-04. Earlier handoff versions (e.g. `handoff_week_2.md`) describe their respective weeks and are still on disk for reference, but the next session should start from `docs/handoff_week_4.md`.

---

## Project Path & Owner

- **Path:** `/root/project/datacenter_water_stress/`
- **Owner:** Hiroaki Oshima (founder building AI startup in Japan, ex-CV data engineer, Berkeley DS, has Colab Pro)
- **License:** MIT (code), CC-BY 4.0 (data, docs, methodology), WRI Aqueduct CC-BY 4.0 (water stress data)

## What v0 Built (Weeks 1-3)

*See "What Weeks 1-3 Built" below — v0 is shipped.*

### Shipped data outputs (in `data/`)

| File | Rows | What it is |
|---|---|---|
| `processed/us_dc_locations.csv` | 1,575 | Cleaned US data centers. 100% have lat/lon, 100% have state code, 47% have disclosed MW. |
| `processed/us_dc_with_mw.csv` | 1,575 | + `est_mw`, `mw_source` columns (operator-class heuristic, 0 unknowns) |
| `processed/us_dc_with_climate.csv` | 1,575 | + `wet_bulb_c`, `climate_adj` from Open-Meteo (100% coverage) |
| `processed/us_dc_with_water.csv` | 1,575 | + `est_liters_per_day` and ±50% uncertainty bands |
| `processed/us_dc_with_stress.csv` | 1,575 | **v0 final.** + WRI BWS join (`bws_score`, `bws_category`, `stress_stressor_match`). 100% join coverage. |
| `external/wri_aqueduct/us_state_stress.csv` | 51 | WRI Aqueduct 4.0 BWS for 50 states + DC, weight=Tot filter |
| `external/wri_aqueduct/aqueduct40_us_province_bws.json` | 51 | Cached raw WRI pull (one row per state) |
| `external/us_states_20m.geojson` | 51 | US Census 1:500k state polygons |
| `external/open_meteo/batch_000.json` ... `batch_015.json` | 16 | Cached Open-Meteo wet-bulb responses (one per ~100-facility batch) |
| `raw/orimadros_datacenters.csv` | 1,605 | Source data (MIT, untouched) |
| `raw/orimadros_scraped.csv` | 2,059 | Raw scrape backup (not used in v0) |
| `raw/atlas_datacenters.csv` / `.geojson` | 18,110 / 6,131 | Atlas global reference (All Rights Reserved — not for v0 use) |

### Shipped code (in `src/`)

All scripts are idempotent. Re-running with the same input produces the same output.

- `src/clean_locations.py` — Week 1: state normalization + polygon reverse-geocode + dedup + MW outlier flag
- `src/build_wri_stress_lookup.py` — Week 1: WRI pull + state-level aggregation
- `src/estimate_power.py` — Week 2: operator-class MW heuristic, 220 providers, 0 unknowns
- `src/fetch_climate.py` — Week 2: Open-Meteo wet-bulb pull (cached, 100 facilities/batch, 6s inter-request sleep)
- `src/estimate_water.py` — Week 2: physics formula `L/day = MW × 21,168 × climate_adj` + ±50% uncertainty bands
- `src/join_water_stress.py` — Week 2: WRI state-level join (100% coverage)
- `src/build_map.py` — Week 3: Folium/Leaflet map, choropleth + 1,568 clustered markers + Phoenix focus

### Shipped documentation (in `docs/`)

- `docs/v0_plan.md` — the original v0 plan (read for full context, including the **v1 preview section** lines 179-195)
- `docs/data_dictionary.md` — column-by-column schema for every output (~18 KB, all 6 datasets)
- `docs/week_1_summary.md` — Week 1 report
- `docs/week_2_summary.md` — Week 2 report (with the 3 methodology issues that motivated v1)
- `methodology.md` — the citable methodology writeup (15 sections, 7 citations, license)
- `README.md` — public intro (9 KB)
- `case_studies/phoenix_az.md` — narrative case study (10 KB)
- `case_studies/blog_draft.md` — blog post draft (7 KB)
| `notebooks/03_physics_model.py` | Week 2 sanity check + sensitivity (7 sections) |
| `docs/week_4_summary.md` | Week 4 report (v1 ML training foundation) |
| `notebooks/04_ml_training.ipynb` | Week 4 Colab notebook skeleton (16 cells; train in Colab Pro) |
| `notebooks/05_v1_vs_v0_compare.py` | Week 4 v0-vs-v1 comparison script (handles "v1 not trained yet") |

### Shippable artifact (in `assets/`)

- `assets/map_v0.html` — **8.4 MB Folium/Leaflet map.** Open in any modern browser.

## v0 Headline Numbers (load-bearing for journalism)

- **US data center water use: 237 B L/year** (0.65 B L/day), with ±50% per-facility uncertainty band
- **Total US DC nameplate: 30,397 MW** (44% disclosed, 56% operator-class heuristic, 7 outliers excluded)
- **Implied WUE: 1.18 L/kWh** (vs 1.8 default; 0.7 cooling-penalty is double-counting — see v1 backlog)
- **352 facilities (22%) in High/Extremely-High WRI states**
- **Top 3 by total L/day: VA → TX → CA** (Loudoun's 134 facilities dominates)
- **AZ is 4th by volume, #1 by stress-weighted demand** (BWS 3.49, 22.4 B L/year, 70 facilities)

## v0 Methodology Issues (the v1 backlog)

These three issues from Week 2 are the main reason v1 exists:

1. **Annual mean wet-bulb understates cooling stress.** Phoenix = 12.5°C annual mean; design-day wet-bulb is ~25°C. v0's `climate_adj` is therefore ~1.0 for almost everywhere, including AZ. v1 should use 99th-pct daily max wet-bulb instead.
2. **WUE × cooling_penalty is double-counting.** Google's 1.8 L/kWh disclosure already reflects their cooling mix. The 0.7 multiplier under-counts by 30%. v1 ML will learn the right per-facility WUE directly.
3. **Handoff's "100-500 B L/day" range was a L/YEAR range, not L/DAY.** Documentation issue, not methodology.

## Hiroaki's Locked Decisions (do not revisit)

From Week 1 + Week 2 + Week 3 + Week 4 reviews (12 questions, all locked):

1. **MW estimation:** operator-class heuristic (already shipped in v0)
2. **Phoenix case study:** primary; Loudoun VA is backup (Phoenix case study shipped)
3. **License:** WRI Aqueduct CC-BY 4.0; cite Kuzma et al. (2023) in any methodology
4. **Stress granularity:** state-level for v0; sub-state is v1+ (NOT a Week 4 task)
5. **Source data:** only `orimadros_datacenters.csv` for v0 (1,605-row MIT)
6. **Week 4 scope:** v1 ML kickoff on Colab Pro. Skeleton + data collection only. Actual model training is interactive in Colab UI by Hiroaki with A100.
7. **Colab Pro subscription** — notebook must be Colab-ready.
8. **v0.5 vs v1.0 naming:** v0.5 = bug fixes / methodology corrections; v1.0 = new model; v1.5 = sub-basin overlay; v2.0 = global.
9. **Lumen / Cogent reclassification:** wait for the v1 model. Revisit in v0.5 if v1 outputs look wrong.
10. **ML training target:** predict **WUE** (L/kWh). At inference: `v1_water_lpd = v0_est_mw × 1000 × 24 × 0.7 × v1_predicted_wue × climate_adj`.
11. **Training set operators:** Google + Microsoft + Meta + **AWS** (region-level). Apple skipped.
12. **Validation strategy:** stratified k-fold across all 4 operators (5-fold) + leave-one-operator-out generalization test.

(Full reasoning in `docs/handoff_week_4.md`.)

## What Week 4 Built (v1 ML Training Foundation)

Week 4 shipped the **data + notebook skeleton** for v1. The actual model training is Hiroaki's interactive work in Colab Pro A100; this session produced the inputs.

### Shipped in Week 4

| File | Rows / Cells | What it is |
|---|---|---|
| `data/processed/ml_training_set.csv` | 43 rows × 14 cols | Per-facility / per-region WUE from Google / Microsoft / Meta / AWS disclosures. 42 with WUE + 1 intentional NaN (Meta Mesa AZ held-out test). 20 rows flagged `is_aggregate=True` (AWS region + Google fleet). |
| `data/processed/v1_inference_features.csv` | 1,575 rows × 42 cols | v0 inference table + 13 v1 features (operator one-hots, lat_lon_grid_cell, is_water_stressed_state, etc.). This is what the v1 model scores. |
| `src/build_ml_training_set.py` | — | Idempotent. Assembles the training set from operator disclosures. Each row cites its report URL. |
| `src/build_v1_features.py` | — | Idempotent. Reuses v0's `classify_provider` from `estimate_power.py` for one-hot encoding. |
| `src/v1_output_schema.py` | — | 18-column schema doc for the v1 model output. |
| `notebooks/04_ml_training.ipynb` | 16 cells | Colab Pro notebook. Cells 1-13 load data + train + predict; Cell 14 saves to Drive; Cell 15 plots v0-vs-v1; Cell 16 documents the schema. |
| `notebooks/05_v1_vs_v0_compare.py` | — | After Colab training: merge v1 predictions into v0, generate `docs/v1_vs_v0_comparison.md`. |
| `methodology.md` Section 16 | 130 lines | v1 addendum: why v1, training set provenance, features, validation, caveats, reproduction. |
| `docs/week_4_summary.md` | — | Week 4 report (what got built, open questions, surprises). |

### v0 baseline floor for v1 to beat

On the v0 training set (the 42 disclosed WUE values), the flat constant `WUE = 1.8 × 0.7 = 1.26 L/kWh` produces **RMSE = 0.755 L/kWh, MAE = 0.661 L/kWh, R² = -1.149** (negative because the flat constant is biased high — disclosed WUE mean is 0.71). v1 must beat this on all three metrics.

### How Hiroaki trains v1 on Colab Pro

1. Upload `data/processed/ml_training_set.csv` and `data/processed/v1_inference_features.csv` to Google Drive (`MyDrive/water_stress_watch_v1/`).
2. Open `notebooks/04_ml_training.ipynb` in Colab Pro with A100.
3. Run cells 1-13. Cell 14 saves the model + predictions. Cell 15 plots the comparison. Cell 16 documents the output schema.
4. Download the three saved files back to `models/water_estimator_v1.pkl` and `data/processed/v1_predicted_wue.csv`.
5. Run `.venv/bin/python notebooks/05_v1_vs_v0_compare.py` to generate the comparison report.

### Locked Week 4 decisions (5 new, all in `docs/handoff_week_4.md`)

- v0.5 = bug fixes / methodology corrections; v1.0 = new model
- Lumen / Cogent reclassification: wait for v1
- ML target: predict WUE (L/kWh), not L/day
- Training set: Google + Microsoft + Meta + AWS (region-level)
- Validation: stratified 5-fold k-fold + leave-one-operator-out

(Total decisions across all weeks: 12.)

### Open questions for Week 5+ (with defaults)

1. **Reconcile against actual PDFs.** The seeded WUE values are based on the well-documented public record but should be verified against the Google 2024 + Microsoft 2024 + Meta 2024 + Amazon 2023 PDFs. *Default: trust the seeded values for the first training run; refine before v1.0 release.*
2. **Optuna sweep timing.** *Default: start as soon as Cell 10 shows reasonable 5-fold R² (≥ 0.5), in parallel with Hiroaki's other work.*
3. **v0.5 design-day wet-bulb fix.** *Default: do the v0.5 fix before the v1.0 release, not before the first training run.*
4. **`is_aggregate=True` downweighting.** *Default: implement sample_weight=0.5 in Cell 7 if Hiroaki wants; not blocking.*

### v1 Methodology Issues (the v1 backlog)

These are real issues from Week 4, not nice-to-haves. Flagging for Hiroaki to weigh in on:

1. **Training set is small (42 rows).** The XGBoost model is at risk of overfitting. The LOO test in Cell 10 is the early-warning signal.
2. **Google is under-represented (4 fleet rows, no per-site).** The model has 1 number to learn Google from.
3. **AWS region-level rows hide intra-region variance.** Every facility in us-east-1 gets the same WUE prediction. This is the right call given the data, but Loudoun's 134 facilities will all get the same number.
4. **`wet_bulb_c` is annual mean, not design-day.** v1 inherits the v0 climate weakness until the v0.5 fix.
5. **No uncertainty on the WUE prediction itself.** v0 has ±50% bands; v1 has a point estimate. A bootstrap or quantile-regression follow-up would add `v1_liters_per_day_low/high` columns.

---

## How to Start the Next Session

**Hiroaki's interactive work (Week 5+):**

1. Open `docs/handoff_week_4.md` for the Week 4 spec.
2. Open `notebooks/04_ml_training.ipynb` in Colab Pro A100.
3. Run cells 1-13 sequentially.
4. After training, download the saved files back to local.
5. Run `notebooks/05_v1_vs_v0_compare.py` to generate the comparison.

**Session-driven work (if Hiroaki asks for it):**

- Reconcile training set WUE values against the actual PDFs (open question 1).
- Run the Optuna sweep once Cell 10 shows reasonable 5-fold R² (open question 2).
- Implement the v0.5 design-day wet-bulb fix (open question 3) — this is a v0.5 patch, not a v1 thing.

## Topline Numbers to Remember

- **1,575 unique US data centers** in the v0 source set
- **US total est. water use: 237 B L/year** with ±50% per-facility uncertainty
- **WRI most-stressed states:** NM (4.26), CA (3.72), AZ (3.49), CO (3.42), NE (3.16)
- **v0 ship date:** 2026-07-04
- **v1 training set:** 43 rows (Google 4 fleet + Microsoft 9 + Meta 16 + AWS 14)
- **v1 ML target:** WUE (L/kWh); v0 baseline RMSE on this set is 0.755 L/kWh (flat 1.26)
- **v1 ship date:** Pending Hiroaki's Colab Pro A100 training run

## Auxiliary

- `requirements.txt` — Python deps (pandas, numpy, shapely, folium, etc.) — **v0 + ML deps (xgboost, sklearn, shap, optuna, joblib, matplotlib) all in venv**
- `.venv/` — Python virtualenv (don't delete; reproducible environment)
- `models/` — empty; `water_estimator_v1.pkl` lands here after Hiroaki's Colab run
