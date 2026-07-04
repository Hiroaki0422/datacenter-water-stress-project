# Water Stress Watch — v0 Plan

**Project:** Public dashboard estimating data center water use overlaid on water-stressed regions
**Owner:** Hiroaki Oshima
**Target v0 ship:** 3 weeks (proof-of-concept, US-only)
**Path:** `/root/project/datacenter_water_stress/`

---

## Mission

Give the public a way to see where data centers compete with communities for scarce water — answering *"where do they sit, how much do they take, and is the region stressed?"*

---

## Scope (v0)

**In scope (v0):**
- US data centers only
- Static web map (HTML + Leaflet) — no live API yet
- Physics-based water use estimate (no trained ML model)
- WRI Aqueduct baseline water stress overlay
- 1 case study (Phoenix, AZ — the textbook example)
- Methodology writeup

**Out of scope (v0):**
- Trained ML model (v1)
- Global coverage beyond US (v2)
- Live API / alerts (v2)
- Per-facility water disclosure data (deferred — none exists publicly)
- Time-series forecasting (v2)

---

## v0 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      DATA SOURCES (v0)                       │
│  ├─ Orimadros/datacenter-map (MIT) → 2,060 US DCs           │
│  ├─ WRI Aqueduct → baseline water stress raster             │
│  └─ Open-Meteo → climate features (wet-bulb temp)           │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                    PROCESSING (Python)                       │
│  1. Clean DC locations → unified table                       │
│  2. Estimate MW (heuristic by operator class)                │
│  3. Estimate water use:                                     │
│     WUE × MW × 24h × climate_adj                            │
│  4. Spatial join: DC lat/lon → WRI Aqueduct stress          │
│  5. Output: enriched CSV/GeoJSON                            │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                   VISUALIZATION (Leaflet)                    │
│  ├─ Map: 2,060 data centers, colored by est. water/day     │
│  ├─ Overlay: WRI Aqueduct water stress choropleth          │
│  ├─ Click pin: facility detail panel                        │
│  └─ Toggle: stress layer, drought layer, climate layer     │
└─────────────────────────────────────────────────────────────┘
```

---

## File Layout

```
datacenter_water_stress/
├── README.md                       # project intro
├── docs/
│   └── v0_plan.md                  # this file
├── data/
│   ├── raw/
│   │   ├── atlas_datacenters.csv           # 18,110 global (not for v0 use)
│   │   ├── atlas_datacenters.geojson       # 6,131 with GPS
│   │   ├── orimadros_datacenters.csv       # 2,060 US, MIT, primary v0 source
│   │   └── orimadros_scraped.csv           # raw scrape, backup
│   ├── processed/
│   │   ├── us_dc_locations.csv             # cleaned + geocoded
│   │   ├── us_dc_water_estimates.csv       # with est. liters/day
│   │   └── us_dc_with_stress.csv           # joined with WRI stress
│   └── external/
│       └── wri_aqueduct/                   # downloaded water stress rasters
├── src/
│   ├── ingest_orimadros.py        # 1. load & clean Orimadros data
│   ├── estimate_power.py          # 2. estimate MW per facility
│   ├── estimate_water.py          # 3. compute water use
│   ├── fetch_climate.py           # 4. pull Open-Meteo climate features
│   ├── join_water_stress.py       # 5. spatial join with WRI
│   └── build_map.py               # 6. generate Leaflet map
├── models/                        # v0 uses heuristics, v1 stores ML models here
├── notebooks/
│   ├── 01_explore_orimadros.ipynb
│   ├── 02_explore_water_stress.ipynb
│   ├── 03_physics_model.ipynb
│   └── 04_ml_training.ipynb       # v1 — train on Colab
├── case_studies/
│   └── phoenix_az.md              # Phoenix is the textbook example
├── assets/
│   ├── map_v0.html                # output: the public map
│   └── screenshots/
└── methodology.md                 # citable writeup of the approach
```

---

## Step-by-Step (3 weeks)

### Week 1 — Data Ingestion & Cleaning
- [x] Create project folder structure
- [x] Download Orimadros MIT data into `data/raw/`
- [x] Download ATLAS reference data (for v2+)
- [ ] Build `src/ingest_orimadros.py` — dedupe, normalize state names, validate lat/lon
- [ ] Build `notebooks/01_explore_orimadros.ipynb` — understand coverage gaps
- [ ] Pull WRI Aqueduct baseline water stress raster (download, clip to US)
- [ ] Document schema decisions in `docs/data_dictionary.md`

**Done when:** `data/processed/us_dc_locations.csv` has 2,000+ clean rows with valid lat/lon, state, operator, MW.

### Week 2 — Estimation Pipeline
- [ ] Build `src/estimate_power.py` — heuristic MW estimator (operator class → size)
  - Tier-1 hyperscalers (AWS/Azure/GCP/Meta): known MW from press releases
  - Colocation (Equinix, Digital Realty): average ~10-30 MW per facility
  - Edge/enterprise: ~1-5 MW
- [ ] Build `src/fetch_climate.py` — pull wet-bulb temp for each lat/lon via Open-Meteo
- [ ] Build `src/estimate_water.py` — physics model:
  ```
  WUE_default = 1.8 L/kWh       # industry average
  WUE_air_cooled = 0.2 L/kWh
  WUE_evaporative = 1.8 L/kWh
  WUE_water_cooled = 2.7 L/kWh
  WUE_immersion = 0.1 L/kWh
  
  climate_adj = 1 + 0.03 * (wet_bulb_avg - 15)
  
  water_liters_per_day = MW * 1000 * 24 * 0.7 * WUE * climate_adj
  ```
  - Cooling type: assume `unknown` → use 0.7 multiplier (conservative between air and evaporative)
- [ ] Build `src/join_water_stress.py` — spatial join DC locations to WRI raster
- [ ] Build `notebooks/03_physics_model.ipynb` — sanity check, sensitivity analysis
- [ ] Output: `data/processed/us_dc_with_stress.csv`

**Done when:** Every DC has `(est_mw, est_liters_per_day, wri_stress, climate_adj)` columns.

### Week 3 — Map, Case Study, Writeup
- [ ] Build `src/build_map.py` — Folium/Leaflet map with all overlays
- [ ] Write `case_studies/phoenix_az.md` — narrative: 100+ DCs in the desert, Colorado River cuts, competing users
- [ ] Write `methodology.md` — the model, its assumptions, known limitations, citation-ready
- [ ] Write `README.md` — public-facing project intro
- [ ] Output: `assets/map_v0.html` — the shippable artifact
- [ ] One blog-post draft: "What 2,000 data centers are doing to US water"

**Done when:** Map loads, case study is publishable, methodology is defensible.

---

## The Water-Use Physics Model (v0)

**Baseline formula:**
```
water_liters_per_day = capacity_MW × 1000 × 24h × load_factor × WUE × climate_adj
```

**Defaults (v0):**
| Parameter | Value | Source |
|---|---|---|
| `load_factor` | 0.7 | Industry avg (Uptime Institute) |
| `WUE` | 1.8 L/kWh | Google/Microsoft disclosure avg |
| `climate_adj` | 1.0 baseline, +3% per °C above 15°C wet-bulb | Engineering rule of thumb |
| Cooling type | unknown → 0.7× multiplier | Conservative; v0 disclosure is too sparse |

**Why this is honest:** No calibration against training data in v0. v0 is a *first estimate* with published uncertainty bounds. Calibration with Google/MS/Meta data happens in v1.

**Uncertainty range to publish:** ±50% per facility (cooling type is the biggest unknown).

---

## v1 Preview (After v0 Ships, 4–6 Weeks)

| Component | What | Where |
|---|---|---|
| ML water-use model | XGBoost trained on Google/MS/Meta disclosed WUE (~100 points) | Colab notebook → `models/water_estimator_v1.pkl` |
| Cooling type classifier | Operator + region + age → cooling tech (5 classes) | Colab |
| Hyperparameter tuning | Optuna sweep on validation set | Colab |
| Validate against | US Drought Monitor, local news reports of DC water use | Local |
| Replace physics defaults | With ML-corrected estimates, uncertainty quantiles | Deploy |

**Colab plan:**
- Notebook: `notebooks/04_ml_training.ipynb`
- Colab Pro: use A100 for tuning
- Data: training set assembled from public sustainability reports (Google 30, Microsoft 60, Meta 15)
- Feature engineering: 30+ features (operator embedding, climate, region, age, etc.)
- Validation: 5-fold CV, hold out Microsoft as test
- Output: model artifact + feature importance + SHAP values for explainability

---

## v0 Success Criteria

| Criterion | How to Verify |
|---|---|
| Map loads, all 2,000+ DCs visible | Open `assets/map_v0.html` |
| Each DC has est. liters/day | Inspect `data/processed/us_dc_with_stress.csv` |
| Phoenix case study tells a real story | Read `case_studies/phoenix_az.md`, count the teeth-grinding facts |
| Methodology is cite-able | External reader can replicate from `methodology.md` |
| Project README makes mission clear | Anyone landing on GitHub understands what this is and why |

## v0 Non-Goals (Explicit)

- No real-time data (v0 is static snapshot)
- No login, no API, no database
- No global coverage (US only in v0)
- No trained ML (deferred to v1)
- No mobile-optimized (desktop browser only)
- No press outreach (deferred to v1 ship)

---

## Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Orimadros data has gaps / stale | Document coverage; show uncertainty band |
| WRI Aqueduct download is huge | Use pre-clipped US version; cache in `data/external/` |
| Wet-bulb temp Open-Meteo quota exceeded | Cache per-DC result, don't re-pull on each build |
| Cooling type assumption is the biggest source of error | Acknowledge in methodology; v1 fix is ML classifier |
| Civic tone accidentally feels preachy | Write like FracTracker / journalism, not activist pamphlet |

---

## Open Questions (Defer to v1+)

- How to add Japan / EU without Atlas license fee?
- How to handle corporate-owned vs colocation transparency?
- How to track proposed (not-yet-built) facilities?
- How to incorporate local drought feeds (NOAA, JMA)?

---

## Files Created So Far

- [x] `/root/project/datacenter_water_stress/` (folder + subdirs)
- [x] `data/raw/atlas_datacenters.csv` (1.7 MB, 18,110 global, reference)
- [x] `data/raw/atlas_datacenters.geojson` (1.6 MB, 6,131 with GPS)
- [x] `data/raw/orimadros_datacenters.csv` (374 KB, 2,060 US, MIT, primary v0)
- [x] `data/raw/orimadros_scraped.csv` (467 KB, raw scrape backup)
- [x] `docs/v0_plan.md` (this file)
