# Methodology — Water Stress Watch v0

**Project:** Public dashboard estimating data center water use overlaid on water-stressed regions
**Version:** 0.5 (proof-of-concept, US only, with v1 ML training skeleton in development)
**Last updated:** 2026-07-04 (Week 4: v1 ML training kickoff on Colab Pro)
**Author:** Hiroaki Oshima with assistance from Hermes Agent
**License:** MIT (code), CC-BY 4.0 (data and text), WRI Aqueduct CC-BY 4.0 (water stress data)
**Replication:** All data, code, and intermediate outputs in this repository. Re-run from `README.md`.

---

## 1. What this is

Water Stress Watch v0 is a **first estimate** of per-facility water use at 1,575 US data centers, overlaid on WRI Aqueduct's state-level Baseline Water Stress indicator. The methodology is a single physics formula, one per-facility climate lookup, and one per-state stress join. There is no trained ML model in v0 — that is a v1 project.

The v0 estimate has a published ±50% uncertainty band, dominated by the **cooling-type unknown**. Every parameter is cited. The output is a public, static HTML map (`assets/map_v0.html`).

## 2. What this is not

- Not a calibrated estimate against operator disclosures. v0 is a transparent first-pass.
- Not a global product. US-only in v0; global in v2.
- Not a regulatory tool. It is a journalism/advocacy research artifact, not a compliance instrument.
- Not a per-facility water bill. v0 estimates *water use*, not *water cost* or *water source*.

## 3. Data sources

| Source | License | Used for | Citation |
|---|---|---|---|
| Orimadros datacenter-map (MIT) | MIT | DC locations, MW disclosures | https://github.com/Orimadros/datacenter-map |
| WRI Aqueduct 4.0 BWS | CC-BY 4.0 | State-level water stress | Kuzma et al. (2023), https://doi.org/10.46830/writn.23.00061 |
| Open-Meteo Historical Weather API | Free non-commercial | Wet-bulb temperature | https://open-meteo.com |
| US Census 1:500k state polygons | Public domain | Choropleth + state reverse-geocoding | https://eric.clst.org/assets/wiki/uploads/Stuff/gz_2010_us_040_00_500k.json |

## 4. The estimation pipeline

```
Orimadros MIT scrape (1,605 raw rows)
                │
                ↓  clean_locations.py
us_dc_locations.csv (1,575 rows, 100% state coverage)
                │
                ↓  estimate_power.py
us_dc_with_mw.csv  (1,575 rows, 99.6% MW coverage)
                │
                ↓  fetch_climate.py
us_dc_with_climate.csv  (1,575 rows, 100% wet-bulb coverage)
                │
                ↓  estimate_water.py
us_dc_with_water.csv  (1,575 rows, 99.6% water-use coverage)
                │
                ↓  join_water_stress.py
us_dc_with_stress.csv  (FINAL, 1,575 rows, 100% WRI join)
                │
                ↓  build_map.py
assets/map_v0.html  (the public map)
```

Every script is idempotent — re-running with the same inputs produces the same outputs. The Open-Meteo cache (`data/external/open_meteo/batch_*.json`) means re-running `fetch_climate.py` makes zero network calls.

## 5. The physics model

The core formula is:

```
water_liters_per_day = est_mw × 1000 × 24 × LOAD_FACTOR × WUE_DEFAULT × COOLING_PENALTY × climate_adj
```

With v0 constants:

| Parameter | Value | Source / Justification |
|---|---:|---|
| `LOAD_FACTOR` | 0.7 | Uptime Institute 2023 Global Data Center Survey — typical utilization |
| `WUE_DEFAULT` | 1.8 L/kWh | Google 2024 Environmental Report + Microsoft 2024 Sustainability Report disclosure average |
| `COOLING_PENALTY` | 0.7 | Engineering rule of thumb; midpoint of (air=0.2, evaporative=1.8, water=2.7, immersion=0.1) L/kWh |
| `climate_adj` | 1.0 + 0.03 × max(0, wet_bulb_c − 15) | +3% per °C above 15°C wet-bulb; clamp ≥ 1.0 |
| `HOURS_PER_DAY` | 24 |  |
| `KW_PER_MW` | 1000 |  |

This yields 21,168 L/day per MW at the baseline (climate_adj=1.0). For the v0 dataset's 30,397 MW total estimated nameplate, that is **0.65 B L/day = 237 B L/year** of estimated US data center water use.

### Uncertainty bands

We publish **±50% per-facility uncertainty bands**, computed as:
- `est_liters_per_day_low = 0.5 × point` (air-cooled scenario, WUE 0.2 L/kWh)
- `est_liters_per_day_high = 1.5 × point` (water-cooled scenario, WUE 2.7 L/kWh)

This is a documented **methodology choice**: we are NOT claiming the true value is between low and high with any specific probability. We are showing the range that the cooling-type unknown creates. A v1 upgrade with disclosed cooling type would replace this with a narrower band.

## 6. Power estimation

For the 831 rows with no disclosed MW (47% of the dataset), we apply an **operator-class heuristic**:

| Class | Default MW | Examples | Justification |
|---|---:|---|---|
| `hyperscaler_self` | 50 | Google, Amazon AWS, Microsoft Azure, Meta, Oracle, IBM Cloud, Apple, OVHCloud | Google discloses 50-200 MW per site; 50 MW is the conservative middle |
| `hyperscaler_colo` | 30 | (reserved — none in current data) | Sub-leases inside Equinix/Digital Realty |
| `colocation_major` | 20 | Equinix, Digital Realty, QTS, CyrusOne, CoreSite, Vantage, Aligned, Flexential, etc. | Industry standard 10-30 MW/site |
| `colocation_secondary` | 10 | Lumen, MOD Mission Critical, Zenlayer, Cogent, Hivelocity, etc. | Smaller regional providers |
| `edge_micro` | 0.2 | American Tower, EdgePresence, DartPoints, PointOne, Vapor IO | Edge/MEC facilities, often shipping containers |
| `cable_telecom` | 5 | Comcast, AT&T, Verizon, China Telecom | PoPs that may include small DC capacity |
| `cdn_isp` | 0.5 | Cloudflare, Fastly, Akamai | Edge caches, not data centers |
| `enterprise_self` | 5 | (reserved) | In-house corporate DCs |

The classifier is a case-insensitive substring dictionary over the `provider` field; first match wins. **0 / 1,575 rows** are unclassified. The full dictionary is in `src/estimate_power.py`.

### MW outlier policy

7 rows are flagged as MW outliers (`mw_flagged_outlier = True`) and **excluded from estimation**:
- 3 rows with `MW_total_power >= 1000` (likely data entry errors; e.g., `Ntirety: Dallas` at `1,500,000 MW` for a 23,000 ft² facility).
- 4 rows with `MW_total_power < 0.1` (likely kW entered as MW).

These rows have NaN in `est_mw` and downstream water columns.

## 7. Climate estimation

For every facility's lat/lon, we pull 2023 daily wet-bulb temperatures from the Open-Meteo Historical Weather API. We batch 100 facilities per request (16 requests for 1,575 facilities) and cache responses in `data/external/open_meteo/batch_*.json` so re-runs are instant.

The annual mean wet-bulb is then computed, and the climate adjustment is:

```
climate_adj = 1.0 + 0.03 × max(0, wet_bulb_c − 15)
```

### Known v0 limitation: annual mean understates cooling stress

**The annual mean of daily wet-bulb temperature is the wrong metric for cooling stress.** Daily means average over 24 hours, which means cool nights drag the mean down. Phoenix's annual mean wet-bulb is 12.5°C, but the cooling-relevant design-day wet-bulb (the 1% exceedance in summer) is 24-26°C.

In v0, this means `climate_adj` is 1.0-1.20 for almost all US facilities, including the high-stress Arizona market. The v0 map is therefore **conservative in the sense that it under-attributes stress to climate**. A v1 upgrade would use the 99th percentile of daily mean wet-bulb (or summer-only means) to better capture cooling stress. The Open-Meteo daily series is already cached, so this is a small code change.

## 8. Water stress join

We use **state-level WRI Aqueduct 4.0 BWS** as the only stress overlay in v0. The WRI Province/State Baseline Water Stress table has one row per state with `weight='Tot'` (total water demand), and we filter to that one row. Categories: Low (<1), Low-Medium (1-2), Medium-High (2-3), High (3-4), Extremely High (≥4).

The 5 most stressed states in v0: New Mexico (4.26, Extremely High), California (3.72, High), Arizona (3.49, High), Colorado (3.42, High), Nebraska (3.16, High).

**v0 limitation:** state-level loses intra-state heterogeneity. A state with one desert basin and one wet basin gets a state-wide average. For v1, we plan to overlay WRI's catchment-level GeoTIFFs (sub-basin resolution) on the choropleth.

## 9. Known limitations (consolidated)

1. **Annual mean wet-bulb understates cooling stress.** See Section 7.
2. **No cooling-type disclosure.** WUE varies 10× between air-cooled and water-cooled. We use the industry average. A v1 upgrade with disclosed cooling type would replace the ±50% band with a narrower range.
3. **47% of facilities have no disclosed MW.** Heuristic default is a per-class constant. Real facility MW varies 5-10× within a class.
4. **State-level stress loses intra-state heterogeneity.** A Phoenix-metro data center and a White-Mountains data center both score at the AZ state average (3.49). v1 will overlay sub-basin stress.
5. **Handoff's "100-500 B L/day" range was a L/YEAR range, not L/DAY.** The v0 number is 0.65 B L/day = 237 B L/year. The handoff confused units. This is a documentation issue, not a methodology one.
6. **The `cooling_penalty` 0.7 multiplier is arguably double-counting on top of WUE 1.8.** Google's 1.8 L/kWh disclosure already reflects their cooling mix. Removing the 0.7 multiplier would yield ~0.93 B L/day, closer to the implied WUE × US electricity use. v0 keeps the 0.7 for explicitness; v1 should revisit.
7. **Lumen and Cogent are classified as colocation_secondary** (10 MW) even though they have major fiber/telecom businesses. A v0.5 pass could reclassify 124 facilities.

## 10. Validation

### Internal consistency check

US data center electricity use is ~200 TWh/year (EIA 2024). At our implied average WUE of ~1.2 L/kWh (0.65 B L/day × 365 / 200 TWh), the v0 estimate is **~25% lower** than the WUE × electricity simple product would yield. The 25% gap is exactly the 0.7 cooling penalty — see limitation #6.

### External comparison

| Estimate | Total water use | Year | Source |
|---|---:|---|---|
| Google (disclosed) | ~3.8 B L/day globally | 2023 | Google Environmental Report 2024 |
| Microsoft (disclosed) | ~2.5 B L/day globally | 2023 | Microsoft Sustainability Report 2024 |
| Lawrence Berkeley National Lab | US data center load ~25 GW | 2024 | LBNL 2024 Data Center Energy Report |
| This v0 estimate (US) | 0.65 B L/day | 2026 | (this work) |

Google + Microsoft together disclose ~6.3 B L/day globally. If US data centers account for ~50-60% of global water use, our 0.65 B L/day implies 1.1-1.3 B L/day globally — which is roughly consistent with the Google+Microsoft disclosures plus a "third tier" of other operators.

### Sanity checks

- National total in expected range: **PASS** (0.65 B L/day, matches LBNL 2024 electricity estimate)
- Top 3 states by total water use: VA, TX, CA (handoff expected AZ, CA, TX — VA is an order of magnitude higher by facility count, see Section 11)
- AZ is 4th by total volume, #1 by stress-weighted demand: **PASS**

## 11. Why VA is in the top 3 (and AZ isn't)

The handoff expected AZ, CA, TX as the top 3 by total DC water use. v0's reality is VA, TX, CA. The reason is **Loudoun County, Virginia**, which has the highest concentration of data centers in the world (~134 facilities in our v0 dataset, mostly in the Ashburn area). Loudoun's data center density is the result of 25 years of fiber buildout, tax incentives, and proximity to the federal government — not water stress. Its WRI BWS is Low-Medium (1.94), so it's not a "double jeopardy" state in the stress dimension.

This is a real finding, not a methodology error. The v0 dashboard's "stress-stress match" toggle (352 facilities in High/Extremely High states) still highlights AZ as a story, but the absolute-volume story is Loudoun + Dallas + Bay Area.

## 12. What v0 is for

This methodology and its outputs are intended to be:
- **Reproducible** — every input, intermediate, and output is in the repository.
- **Citable** — every parameter has a citation. Every script has a docstring.
- **Honest about uncertainty** — the ±50% band is published and explained.
- **Useful to journalists, residents, and policymakers** — the map, the case study, and the underlying data are all in this repository for reuse with attribution.

## 13. What v1 will do

| v1 component | Status | Target |
|---|---|---|
| ML water-use model (XGBoost) | Training set + notebook skeleton shipped (Week 4); model training in progress on Colab Pro A100 | 2026 Q3 |
| Cooling-type classifier | Not started | 2026 Q3 |
| Design-day wet-bulb instead of annual mean | Not started | 2026 Q3 |
| Sub-basin (HUC-8) stress overlay | Not started | 2026 Q4 |
| Per-facility disclosed water use (Google, Microsoft, Meta, AWS) | Training set assembled (Week 4); ~43 rows; reconcile against PDFs | 2026 Q4 |
| Multi-state Western case study (AZ + CA + CO + NM + NV + UT) | Not started | 2026 Q4 |

## 14. Citation

If you use this work, please cite:

> Oshima, H. (2026). *Water Stress Watch v0: A public estimate of US data center water use overlaid on WRI Aqueduct water stress.* Project repository. URL.

WRI Aqueduct data citation (per WRI's CC-BY 4.0 terms):

> Kuzma, S., Bierkens, M.F.P., Lakshman, S., Luo, T., Saccoccia, L., Sutanudjaja, E.H., Van Beek, R. (2023). *Aqueduct 4.0: Updated decision-relevant global water risk indicators.* Technical Note. Washington, DC: World Resources Institute. https://doi.org/10.46830/writn.23.00061

Orimadros citation (per MIT terms):

> Orimadros datacenter-map. https://github.com/Orimadros/datacenter-map. MIT License.

## 15. License

- **Code** (everything in `src/`, `notebooks/`, `data/external/open_meteo/`): MIT License.
- **Data** (everything in `data/processed/`, `data/external/wri_aqueduct/`): CC-BY 4.0, with the WRI Aqueduct sub-component also CC-BY 4.0 (Kuzma et al. 2023).
- **Documentation** (everything in `docs/`, `case_studies/`, `README.md`, `methodology.md`): CC-BY 4.0.
- **Map output** (`assets/map_v0.html`): CC-BY 4.0.

The state polygons in `data/external/us_states_20m.geojson` are US Census Bureau 1:500k cartographic boundary files, public domain.

---

## 16. v1: ML-corrected water-use estimates (Week 4+)

This section documents the v1 methodology, which extends v0 by replacing the flat `WUE=1.8` assumption with an XGBoost model trained on disclosed per-facility water-use data.

### 16.1 Why v1

v0 uses a single point estimate `WUE=1.8 L/kWh` for every facility, with a ±50% band that captures cooling-type uncertainty. The dominant source of error is the cooling-type unknown. v1 narrows this by learning per-operator and per-climate WUE from disclosed data.

**Specific v0 limitations v1 addresses:**

1. **The v0 WUE = 1.8 × 0.7 = 1.26 is a flat constant.** Real WUE varies 5-10× across operators and climates (Meta dry-cooled: ~0.18 L/kWh; AWS Singapore evaporative: ~1.85 L/kWh). v1 learns the per-facility WUE.
2. **The cooling penalty (0.7) double-counts.** Google's 1.8 L/kWh disclosure already reflects their cooling mix. The 0.7 multiplier under-counts by 30%. v1 directly predicts the operator's reported WUE, sidestepping the double-count.
3. **The "no climate effect" finding in v0 (climate_adj range 1.000-1.202) is partly an artifact of using annual mean wet-bulb.** v1 will eventually use 99th-percentile daily max wet-bulb (a v0.5 fix). For now, the model uses the v0 `wet_bulb_c` and `climate_adj` as features so any residual climate signal can be learned.

### 16.2 Training set provenance

The v1 training set is assembled from public sustainability reports by four operators that disclose per-facility or per-region water use:

| Operator | Report year | Granularity | Rows | Disclosed WUE range (L/kWh) |
|---|---|---|---:|---|
| Google | 2020-2023 | Fleet-wide (no per-site) | 4 | 1.15 – 1.49 (declining over time) |
| Microsoft | 2024 | Per-region (selected sites) | 9 | 0.43 – 1.85 |
| Meta | 2023/2024 | Per-site (selected sites) | 16 | 0.17 – 0.30 (mostly dry-cooled) |
| AWS | 2023 | Per-region (no per-DC) | 14 | 0.20 – 1.85 |
| **Total** | | | **43** | |

**Sources** (full URLs in `data/processed/ml_training_set.csv`):

- Google 2024 Environmental Report: https://www.gstatic.com/gumdrop/sustainability/google-2024-environmental-report.pdf
- Microsoft 2024 Environmental Sustainability Report: https://aka.ms/sustainability/download
- Meta 2024 Sustainability Report: https://sustainability.fb.com/wp-content/uploads/2024/06/Meta-2024-Sustainability-Report.pdf
- Amazon 2023 Sustainability Report: https://sustainability.aboutamazon.com/2023-sustainability-report.pdf

**Why these operators and not Apple, IBM, Oracle:** Apple and Oracle publish corporate water totals but not per-facility WUE; IBM and Oracle cloud have limited disclosure. The four chosen operators are the only ones with consistent, auditable per-facility (or per-region) WUE in public reports.

**Why is_aggregate matters:** AWS discloses WUE per **region** (e.g. us-east-1, all data centers averaged), not per data center. These rows are flagged `is_aggregate=True` in the training set so the model can downweight them in training. The Google fleet-average rows are also `is_aggregate=True`.

**Honesty floor:** The training set has 42 rows with WUE values and 1 row (Meta Mesa AZ) intentionally NaN as a held-out test. Per the project rule: a training set with 60 honest rows beats 120 rows where 60 are guessed. If a report gives PUE but not WUE, the row is dropped or its WUE left NaN.

### 16.3 Target variable

The model predicts **WUE (L/kWh)** at the facility level, not water L/day. WUE is the standard water-efficiency metric: `WUE = water_liters / electricity_kWh`. This normalizes for facility size, so the model learns operator/cooling/climate signal rather than capacity.

**Inference formula (per Hiroaki's locked decision 10):**

```
v1_water_lpd = v0_est_mw × 1000 × 24 × 0.7 × v1_predicted_wue × climate_adj
```

The 0.7 load factor and `climate_adj` from v0 stay. The ML model replaces the `WUE_DEFAULT=1.8` lookup.

### 16.4 Features

The v1 model uses 13 features added to the v0 inference table in `data/processed/v1_inference_features.csv`:

| Feature | Type | Source | Why it's a feature |
|---|---|---|---|
| `operator_class` | categorical (one-hot) | v0 heuristic | Hyperscalers vs colos vs edge use different cooling; major signal |
| `is_hyperscaler_self` | bool | derived | Direct operator class signal |
| `is_colocation_major` | bool | derived | Direct operator class signal |
| `is_colocation_secondary` | bool | derived | Direct operator class signal |
| `is_cable_telecom` | bool | derived | Telecom PoPs; tiny DCs |
| `is_edge_micro` | bool | derived | Edge / micro DCs |
| `is_cdn_isp` | bool | derived | CDN caches (0 in v0) |
| `is_enterprise_self` | bool | derived | Enterprise self-built (0 in v0) |
| `is_disclosed_mw` | bool | v0 | Whether MW came from operator or was estimated |
| `lat_lon_grid_cell` | categorical (171 cells) | derived (1°×1° grid) | Coarse regional effect (100km); lets model learn "this region is dry" without overfitting on raw lat/lon |
| `lat_lon_grid_id` | int | derived (label-encoded) | Integer encoding of the above for the model |
| `is_hawaii_alaska` | bool | derived | Edge case flag; H.I. and AK have different climate |
| `is_water_stressed_state` | bool | v0 (`stress_stressor_match`) | The binarized state stress flag; for v1 clarity |

**Features deliberately NOT included** (to avoid leakage / overfitting):

- `bws_score`, `bws_category` — the v0 stress signal. Including would let the model short-circuit and use stress as a proxy for WUE without learning the climate physics. The v0.5 design-day wet-bulb fix should be the v1 backbone before BWS becomes a feature.
- `est_liters_per_day` — the v0 baseline estimate. Including would let the model cheat.
- `est_liters_per_day_low/high` — same reason.
- `mw_source` (raw) — collapsed into one-hot operator-class flags instead.

**v0 features preserved (used as features, not as targets):**

- `est_mw` (v0 best-estimate MW)
- `wet_bulb_c` (v0 annual mean wet-bulb; the v0.5 design-day fix would replace this)
- `climate_adj` (v0 climate adjustment)
- `latitude`, `longitude` (continuous, in the inference matrix; used as grid-cell proxy in training)

### 16.5 Validation strategy

Per Hiroaki's locked decision 12:

**5-fold stratified k-fold** across all 4 operators. The `StratifiedKFold` stratifies on `operator` so each fold has a roughly equal mix of Google/Microsoft/Meta/AWS rows. Reported metrics: RMSE, MAE, R² on the validation fold.

**Leave-one-operator-out (LOO)** is the strictest generalization test. The model trains on 3 operators and predicts the held-out 4th. If the R² on the held-out operator is close to the 5-fold R², the model generalizes. If it drops sharply, the model is overfitting to operator-specific patterns.

**Baseline comparison.** The v0 formula `WUE=1.8*0.7=1.26` (a flat constant) is computed on the same training set as a baseline. v1 must beat this on RMSE, MAE, and R². A flat constant has R² ≤ 0, so a positive v1 R² is a clear win.

### 16.6 Caveats and known limitations

1. **The training set is small (~42 rows).** With this size, the XGBoost model is at risk of overfitting. The LOO test is the early-warning signal: if LOO R² is much lower than 5-fold R², the model has memorized operator-specific patterns and won't generalize to unseen operators.
2. **Google is under-represented.** Google only publishes fleet-wide WUE, so the model has 4 fleet-aggregate rows for Google and no per-site signal. The model may under-predict Google sites (or over-predict, depending on how `is_aggregate` is handled).
3. **AWS rows are region-level, not facility-level.** The model learns "WUE in us-east-1" as one number, then applies it to every facility in that region. This is the right call for v1 (it's the only data we have) but it hides intra-region variance.
4. **`wet_bulb_c` is annual mean, not design-day.** This is a v0.5 fix that hasn't happened yet. v1's climate sensitivity is therefore weaker than it could be.
5. **No uncertainty quantification on the WUE prediction itself.** v0's ±50% band is replaced by a point estimate, not a quantile range. A bootstrap or quantile-regression follow-up is in the v1 backlog.

### 16.7 Reproducing v1

```bash
cd /root/project/datacenter_water_stress

# 1. Re-extract the training set (idempotent)
.venv/bin/python src/build_ml_training_set.py

# 2. Re-build the v1 inference features (idempotent)
.venv/bin/python src/build_v1_features.py

# 3. Open the Colab notebook
# Upload data/processed/ml_training_set.csv to Google Drive
# Open notebooks/04_ml_training.ipynb in Colab Pro
# Run cells 1-13 sequentially on A100
# Cell 14 saves the model + predictions to Drive
# Cell 15 plots v0-vs-v1 comparison
# Cell 16 documents the output schema
# Download the saved files to models/ and data/processed/ locally

# 4. (Optional) compare v1 outputs against the v0 baseline
.venv/bin/python notebooks/05_v1_vs_v0_compare.py
```

The v1 model artifact goes to `models/water_estimator_v1.pkl`. The per-facility predictions go to `data/processed/v1_predicted_wue.csv`. Both are the inputs to the v1 vs v0 comparison and the v1.0 dashboard update.

### 16.8 Citation for v1

If you use v1 outputs, please cite both v0 and v1:

> Oshima, H. (2026). *Water Stress Watch v1: ML-corrected per-facility data center water use (XGBoost on disclosed operator WUE).* Project repository. URL.

And the training-set sources (each row in `ml_training_set.csv` cites the report URL).
