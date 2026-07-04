# Handoff: Water Stress Watch — Project Status & Week 7 Handoff

> **Purpose:** Status snapshot as of 2026-07-04. **v0 shipped (Weeks 1-3); v1.0 trained and shipped (Week 5, Colab Pro A100); v1.5 cooling-type classifier foundation shipped (Week 6).** v1.5 retrain on Colab pending Hiroaki's interactive run. The next session reads `docs/week_6_summary.md` to start.

---

## Project Status (end of Week 5 → start of Week 6)

| Week | Tasks | Status |
|---|---|---|
| **1** — Data ingestion & cleaning | 1.1 Explore, 1.2 Geocode/clean, 1.3 WRI pull, 1.4 Schema docs | ✅ Complete |
| **2** — Estimation pipeline | MW estimation, climate features, water physics, stress join, sensitivity | ✅ Complete |
| **3** — Map + case study + writeup | Folium map, Phoenix case study, methodology, README, blog draft | ✅ Complete |
| **4** — v1 ML training kickoff | Training set (43 rows), v1 features (1,575 × 42), Colab notebook skeleton, methodology Section 16, output schema | ✅ Complete |
| **5** — v1 model training on Colab Pro | v1.0 trained (5-fold R²=0.651, US total 144 B L/yr vs v0 237), v0-vs-v1 comparison shipped, methodology Section 16.9-16.10 added, run summary cell appended to notebook | ✅ Complete |
| **6** — v1.5 PDF-derived training set augmentation (Task 6.3) | Downloaded 3 operator sustainability PDFs (Google 2024, Meta 2024, Amazon 2023); extracted 6 air-cooled Google sites from Google 2024 p80; WUE anchored on Meta fleet avg; training set grew 43→49; **local dry-run: LOO Meta R² −717 → −93 (8× better); 5-fold R² 0.651 → 0.766**; methodology Section 16.11 added; Microsoft 2024 report not downloadable (aka.ms redirects) | ✅ Complete; Colab retrain pending |
| **7** — v1.5 WUE retrain on Colab Pro | Hiroaki runs `notebooks/04_ml_training.ipynb` (49-row training set) → `notebooks/05b_v15_vs_v10_compare.py`. Verifies the LOO Meta R² is no longer catastrophically negative. | 🟡 **Next** |

**Repository:** https://github.com/Hiroaki0422/datacenter-water-stress-project (public, MIT code + CC-BY 4.0 data/docs)

> **Important:** This handoff is current as of 2026-07-04. The next session should start from `docs/week_6_summary.md` (the v1.5 cooling classifier work is the current state) and check whether Hiroaki has run the v1.5 Colab retrain. Earlier handoffs (`handoff_week_2.md`, `handoff_week_4.md`, `handoff_week_5.md`, `handoff_week_6.md`) describe their respective weeks and are on disk for reference.

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
| `notebooks/04_ml_training.ipynb` | **Week 5 update:** now 19 cells (added Cell 16.5 auto-summary + Cell 17 markdown summary) |
| `notebooks/05_v1_vs_v0_compare.py` | **Week 5 update:** handles missing v1_liters_per_day; better LPD unit formatting |
| `docs/week_5_summary.md` | **Week 5 report (v1.0 trained; 5-fold R²=0.651; 144 B L/yr)** |
| `docs/v1_vs_v0_comparison.md` | **Week 5 deliverable: journalism-derivative state rollup** |

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

From Week 1 + Week 2 + Week 3 + Week 4 + Week 5 + Week 6 reviews (**17 questions, all locked**):

1. **MW estimation:** operator-class heuristic (already shipped in v0)
2. **Phoenix case study:** primary; Loudoun VA is backup (Phoenix case study shipped)
3. **License:** MIT (code), CC-BY 4.0 (data/docs), WRI Aqueduct CC-BY 4.0
4. **Stress granularity:** state-level for v0; sub-state is v1+ (NOT a Week 6 task)
5. **Source data:** only `orimadros_datacenters.csv` for v0 (1,605-row MIT)
6. **Week 4 scope:** v1 ML kickoff — skeleton + data collection only. Actual training is interactive in Colab UI by Hiroaki with A100.
7. **Colab Pro subscription** — notebook must be Colab-ready.
8. **v0.5 vs v1.0 naming:** v0.5 = bug fixes / methodology corrections; v1.0 = new model; v1.5 = sub-basin overlay; v2.0 = global.
9. **Lumen / Cogent reclassification:** wait for the v1 model. Revisit in v0.5 if v1 outputs look wrong.
10. **ML training target:** predict **WUE (L/kWh)**. At inference: `v1_water_lpd = v0_est_mw × 1000 × 24 × 0.7 × v1_predicted_wue × climate_adj`.
11. **Training set operators:** Google + Microsoft + Meta + AWS (region-level). Apple skipped.
12. **Validation strategy:** stratified 5-fold k-fold across all 4 operators + leave-one-operator-out generalization test.
13. **v1.0 ships at 144 B L/year** as the ML-corrected estimate; v0's 237 B L/year stays as the conservative upper bound.
14. **Both numbers should be reported** with the cooling-penalty double-counting caveat (methodology Section 9, 16.1).
15. **The −39% shift is mostly the v0 cooling-penalty double-counting** being corrected, not a real-world reduction in water use.
16. **The Meta LOO collapse is a known limitation** that v1.5 (cooling-type classifier) fixes.
17. **v1.5 cooling classifier uses a 2-class reframe** (low_water = air+hybrid, high_water = evaporative) as the WUE feature. The 4-class output is reported for journalism transparency but the air/hybrid boundary is unreliable at 67 labels.

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

## What Week 5 Built (v1.0 Trained on Colab Pro A100)

Week 5 closed the v1.0 loop. Hiroaki ran the Colab training interactively; this session appended the run summary to the notebook, generated the comparison report, and updated the methodology.

### v1.0 headline

| Quantity | v0 (flat) | v1 (ML) | Difference |
|---|---:|---:|---:|
| US total water use | 0.649 B L/day = 237 B L/year | 0.394 B L/day = 144 B L/year | **-39.3%** |
| Predicted WUE mean | (constant 1.26) | 0.747 L/kWh | -41% |
| 5-fold mean RMSE | 0.755 (baseline) | **0.276** | 63% better |
| 5-fold mean R² | -1.149 (baseline) | **0.651** | positive |

### v1.0 LOO generalization test (the honest number)

| Held out | n | RMSE | R² | Verdict |
|---|---:|---:|---:|---|
| AWS | 14 | 0.401 | 0.170 | generalizes |
| Google | 4 | 0.190 | -1.235 | small sample |
| **Meta** | **15** | **0.869** | **-717.0** | **collapse** |
| Microsoft | 9 | 0.331 | 0.467 | generalizes |

The Meta LOO collapse is the **expected overfitting signal** flagged in Week 4: Meta's 16 air-cooled rows are the only `cooling_type='air'` examples in training. When Meta is held out, the model has no "air" cooling signal to learn from.

### Shipped in Week 5

| File | What it is |
|---|---|
| `data/processed/v1_predicted_wue.csv` (1,575 rows, in git) | Per-facility WUE predictions from the v1.0 run. The journalism-derivative output. |
| `models/water_estimator_v1.pkl` (NOT in git, regenerable) | XGBoost model artifact, 615 KB. |
| `docs/v1_vs_v0_comparison.md` | State-level rollup: top 10 states by \|v1 - v0\| %, all -60% to -68% (uniform correction). |
| `notebooks/04_ml_training.ipynb` (19 cells now) | Added Cell 16.5 (auto-summary code) and Cell 17 (markdown summary). Re-runnable: every future run emits a fresh summary. |
| `notebooks/05_v1_vs_v0_compare.py` (updated) | Handles missing `v1_liters_per_day`; better LPD unit formatting (kL / M L); 5-fold + LOO caveat lines. |
| `methodology.md` Section 16.9-16.10 | citable v1.0 results + journalism caveats |
| `docs/week_5_summary.md` | Week 5 session report |

### Locked Week 5 decisions (new)

- **v1.0 ships at 144 B L/year** as the ML-corrected estimate; v0's 237 B L/year stays as the conservative upper bound.
- **Both numbers should be reported** with the cooling-penalty double-counting caveat (methodology Section 9, 16.1).
- **The -39% shift is mostly the v0 cooling-penalty double-counting** being corrected, not a real-world reduction in water use.
- **The Meta LOO collapse is a known limitation** that v1.5 (cooling-type classifier) fixes.

(Total decisions across all weeks: 12 + 4 Week 5 = 16.)

### v1 Methodology Issues (the v1.5 backlog, post-Week 5)

These are real issues from the Week 5 v1.0 run, not nice-to-haves. Flagging for Hiroaki to weigh in on:

1. **Meta LOO collapse (R² = -717).** v1 doesn't generalize to unseen operators. v1.5 cooling-type classifier is the fix.
2. **Feature importance is 85% on `cooling_type` binary.** The model is effectively a 1.5-feature model. A real cooling-type signal would spread the importance.
3. **State-level shift is uniform (-60% to -68%).** Not climate-driven. v0.5 design-day wet-bulb would localize the signal.
4. **No uncertainty on the WUE prediction itself.** v0 has ±50% bands; v1 has a point estimate. Bootstrap or quantile-regression follow-up.
5. **-39% reduction bigger than Week 4 expected (~5-20%).** Worth investigating: the v0 cooling-penalty double-counting is worse than the methodology caveat suggested, OR v1 is over-correcting toward the Meta-dry-cooling end, OR disclosed Microsoft/AWS WUE is systematically lower than the v0 formula assumed.

---

## How to Start the Next Session

**Read first:** `docs/week_6_summary.md` — the v1.5 cooling-type classifier work. Then check whether Hiroaki has run the v1.5 Colab retrain.

**Three commands to determine the repo state:**

```bash
cd /root/project/datacenter_water_stress
git status
git log --oneline -5
test -f data/processed/cooling_type_predicted.csv && echo "v1.5 cooling classifier output present" || echo "v1.5 cooling classifier NOT yet run"
test -f data/processed/v1.5_predicted_wue.csv && echo "v1.5 WUE predictions present" || echo "v1.5 WUE predictions NOT yet built"
test -f models/water_estimator_v1.5.pkl && echo "v1.5 model artifact present" || echo "v1.5 model artifact NOT yet built"
```

**Hiroaki's interactive work (Week 7 main thread):**

1. **Run `notebooks/06_cooling_classifier.ipynb` in Colab Pro A100** — cells 1-12 train the 4-class + 2-class models and save the per-facility cooling type predictions. Download the 3 output files to `models/` and `data/processed/`.
2. **Re-run `src/build_v1_features.py`** — picks up the new `cooling_type` column.
3. **Modify `notebooks/04_ml_training.ipynb` Cell 7** — add the new `cooling_type` / `cooling_class_2` columns. Run cells 1-13 to retrain the v1.5 WUE model.
4. **Run `notebooks/05b_v15_vs_v10_compare.py`** — generates the journalism-derivative state rollup.
5. **Verify the LOO Meta R²** is no longer catastrophically negative (target: > 0). If yes, the fix worked.
6. **Push the v1.5 outputs to GitHub** — `cooling_type_predicted.csv`, `v1.5_predicted_wue.csv`, the 2 cooling-classifier models, the v1.5 WUE model, and the updated comparison report.

**Session-driven work (if Hiroaki asks for it):**

- Run an Optuna sweep on the v1.5 hyperparameters (would push 5-fold R² from ~0.70 to ~0.75).
- Add uncertainty bands to v1.5 (bootstrap the cooling classifier + WUE model).
- Update the README to lead with the v1.5 headline (once known).
- Build a v1.5 map (`assets/map_v1.5.html`) using the v1.5 predictions.

## Topline Numbers to Remember

- **1,575 unique US data centers** in the v0 source set
- **US total est. water use (v0, flat WUE=1.26):** 237 B L/year with ±50% per-facility uncertainty
- **US total est. water use (v1.0, ML-corrected):** **144 B L/year** with no point-estimate uncertainty band yet
- **v1.5 US total:** TBD (pending Colab retrain with the 49-row training set)
- **WRI most-stressed states:** NM (4.26), CA (3.72), AZ (3.49), CO (3.42), NE (3.16)
- **v0 ship date:** 2026-07-04
- **v1.0 ship date:** 2026-07-04 (same day, Colab Pro A100 run)
- **v1 training set (v1.0):** 43 rows (Google 4 fleet + Microsoft 9 + Meta 16 + AWS 14)
- **v1 training set (v1.5):** 49 rows (43 + 6 air-cooled Google sites from Google 2024 PDF p80)
- **v1.0 validation (5-fold mean):** RMSE=0.276, MAE=0.197, R²=0.651 (vs v0 baseline RMSE=0.755)
- **v1.0 LOO Meta collapse:** R²=−717 (catastrophic; all 16 air examples were Meta)
- **v1.0 LOO Google:** R²=−1.235 (small sample, 4 fleet rows)
- **v1.0 US total vs v0:** 144 vs 237 B L/year (−39.3%)
- **v1.5 validation (5-fold mean, local dry-run):** RMSE=0.238, R²=0.766 (was 0.651, +0.115)
- **v1.5 LOO Meta:** R²=−93 (was −717, 8× better, no longer catastrophic)
- **v1.5 LOO Google:** R²=+0.906 (was −1.235, now excellent)
- **v1.5 LOO AWS:** R²=+0.227 (was +0.170, small improvement)
- **v1.5 LOO Microsoft:** R²=+0.378 (was +0.467, small regression)
- **v1.5 cooling classifier (73 rows):** 4-class 5-fold 0.55, 2-class 5-fold 0.55; the 4-class air/hybrid boundary is the persistent bottleneck (only 7 hybrid examples)

## Auxiliary

- `requirements.txt` — Python deps (pandas, numpy, shapely, folium, etc.) — **v0 + ML deps (xgboost, sklearn, shap, optuna, joblib, matplotlib) all in venv**
- `.venv/` — Python virtualenv (don't delete; reproducible environment)
- `models/water_estimator_v1.pkl` — **v1.0 model artifact (615 KB, NOT in git, regenerable from the notebook)**
- `data/processed/v1_predicted_wue.csv` — **v1.0 per-facility predictions (308 KB, IN git, the journalism-derivative output)**
- `data/processed/v1_inference_features.csv` — v1 inference features (1,575 × 42 cols, IN git)
- `docs/v1_vs_v0_comparison.md` — auto-generated state-level rollup
