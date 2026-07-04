# Handoff: Water Stress Watch v0 — Week 2 Estimation Pipeline

> **Purpose:** Self-contained prompt for a fresh Hermes session to execute **Week 2** of the Water Stress Watch project without any prior context. Read this file once, then act.

---

## TL;DR — What to Build This Week

Five scripts, one notebook, one output CSV. Goal: every facility in `us_dc_locations.csv` gets an estimated `(MW, liters_per_day, climate_adj, wri_stress)`. Output: `data/processed/us_dc_with_stress.csv`.

```
data/processed/us_dc_locations.csv  (1,575 rows, from Week 1)
                │
                ↓
src/estimate_power.py        → fill missing MW via operator-class heuristic
src/fetch_climate.py         → pull wet-bulb temp from Open-Meteo (cached)
src/estimate_water.py        → apply physics: L/day = MW × 1000 × 24 × 0.7 × WUE × climate_adj
src/join_water_stress.py     → join WRI state-level stress
                │
                ↓
data/processed/us_dc_with_stress.csv  (1,575 rows, the Week 2 deliverable)
notebooks/03_physics_model.ipynb      (sanity check + sensitivity analysis)
```

---

## Project Path & Owner

- **Path:** `/root/project/datacenter_water_stress/`
- **Owner:** Hiroaki Oshima (founder building AI startup in Japan, ex-CV data engineer, Berkeley DS)

## Read These Before You Start

1. `docs/v0_plan.md` — the original v0 plan (physics formula, file layout, Week 2/3 outline)
2. `docs/week_1_summary.md` — what got built in Week 1 (data quality, WRI rankings, locked decisions)
3. `docs/data_dictionary.md` — column definitions for `us_dc_locations.csv` and `us_state_stress.csv`
4. `docs/handoff_new_session.md` — overall project status (do not read the earlier wrong handoff if you find one)

**You have full latitude on implementation choices** (libraries, function signatures, output formats, etc.) — document them in the script docstrings and in `data_dictionary.md` updates. If a task is ambiguous, make a reasonable choice and document it.

---

## Hiroaki's Locked Decisions (do not revisit)

1. **MW estimation policy:** **operator-class heuristic** for the 831 rows missing disclosed MW.
2. **Phoenix case study:** primary; Loudoun VA is backup. Do not start Phoenix research until Week 3.
3. **License:** WRI Aqueduct CC-BY 4.0. Cite Kuzma et al. (2023) in any methodology.
4. **Stress granularity:** **state-level for v0.** Do NOT pull GeoTIFFs or do basin polygon joins.
5. **Source data:** use only `orimadros_datacenters.csv` (the cleaned 1,605-row file). Do not use `orimadros_scraped.csv`, `atlas_datacenters.csv`, or `atlas_datacenters.geojson` for v0.

---

## Week 2 Tasks (in order)

### Task 2.1: `src/estimate_power.py` — fill missing MW

**Input:** `data/processed/us_dc_locations.csv` (1,575 rows; 744 have MW, 831 don't)
**Output:** Same DataFrame plus an `est_mw` column and an `mw_source` column.

For each row, the logic is:

```python
if MW_total_power > 0 and not mw_flagged_outlier:
    est_mw = MW_total_power
    mw_source = 'disclosed'
elif mw_flagged_outlier:
    est_mw = np.nan  # exclude from estimation; flag in methodology
    mw_source = 'outlier_excluded'
else:
    est_mw = heuristic_for(provider)  # see below
    mw_source = f'heuristic:{class}'
```

**Operator-class heuristic** — build a lookup dict `OPERATOR_CLASS` and a class-to-MW dict `CLASS_DEFAULT_MW`. The classes:

| Class | Examples | Default MW per facility | Source/justification |
|---|---|---|---|
| `hyperscaler_self` | Google, Amazon AWS, Microsoft Azure, Meta, Oracle Cloud, IBM Cloud | 50 MW | Google discloses ~50-200 MW per site; AWS Direct Connect locations are similar. Conservative middle. |
| `hyperscaler_colo` | Google colocation leases, Meta colocation leases | 30 MW | Sub-leases inside Equinix/Digital Realty |
| `colocation_major` | Equinix, Digital Realty, QTS, CyrusOne, CoreSite, Vantage, Aligned, Flexential, Cyxtera, DataBank, Centersquare, TierPoint, NTT Global, EdgeConneX, Teleports, ServerFarm, H5, INAP | 20 MW | Industry standard; Equinix Ashburn DC2 (in our data) is 4.9 MW but new Equinix xScale facilities are 50-100+ MW |
| `colocation_secondary` | 365 Data Centers, Lumen (formerly CenturyLink), MOD Mission Critical, Zayo, Cogent, Hivelocity, H5, Netrality | 10 MW | Smaller regional providers |
| `edge_micro` | American Tower, EdgePresence, Compass Datacenters, DartPoints, PointOne, Vapor IO, Ubiquity | 0.2 MW | Edge/MEC facilities, often shipping containers |
| `cable_telecom` | Comcast, Charter, Cox, AT&T, Verizon, Lumen, China Telecom, Cogent (as telecom), Telefonica | 5 MW | PoPs that may include small DC; conservative |
| `cdn_isp` | Cloudflare, Fastly, Akamai, StackPath, Highwinds | 0.5 MW | Edge caches, not data centers |
| `enterprise_self` | Corporate in-house DCs (rare in this dataset) | 5 MW | Lookup by name keyword |
| `unknown` | Anything not matched | 15 MW | Median of major-colo default; document the fallback |

**Build the lookup** as a Python dict. Use case-insensitive substring matching on `provider`. For multi-class operators (e.g. Lumen has both colocation and telecom), use the dominant class but document the ambiguity in `mw_source` as `heuristic:colocation_major (Lumen also operates as telecom)`.

**For each operator not in the dict**, search the operator name for known substrings (e.g. `if 'equinix' in provider.lower(): class = 'colocation_major'`). Add a fallback to `unknown`. Aim to classify all 220 unique providers.

**Output to console:**
- Count of rows by `mw_source`
- Sum of `est_mw` by class
- Top 10 operators still classified as `unknown` (to verify coverage)

**Output to file:** `data/processed/us_dc_with_mw.csv` (1,575 rows, includes `est_mw`, `mw_source`, original cols).

### Task 2.2: `src/fetch_climate.py` — wet-bulb temperature from Open-Meteo

**Input:** `data/processed/us_dc_with_mw.csv` (1,575 rows, with lat/lon)
**Output:** Same DataFrame plus a `wet_bulb_c` column and a `climate_adj` column.

**Why wet-bulb and not dry-bulb:** Data center cooling is most efficient when outdoor wet-bulb temperature is low (this is why Microsoft puts DCs in cold places like Quincy WA or Dublin). WUE scales with wet-bulb. Open-Meteo provides it directly.

**Open-Meteo endpoint:**
```
https://archive-api.open-meteo.com/v1/archive
  ?latitude={lat}&longitude={lon}
  &start_date=2023-01-01&end_date=2023-12-31
  &daily=wet_bulb_temperature_2m_mean
  &timezone=America/New_York
```

This gives you one full year of daily wet-bulb means. Average them to get annual mean wet-bulb.

**Performance:** 1,575 requests at Open-Meteo's free tier. Open-Meteo is free for non-commercial use, no API key, ~10,000 req/day limit. We stay under that. Still, **cache every response** to `data/external/open_meteo/dc_{dc_id}.json` so re-runs are instant.

**Batch the requests:** Open-Meteo supports a comma-separated list of lat/lon pairs in a single call. Use that. The response is an array of arrays — one per coordinate. This lets you pull 100 facilities per request and finish in ~16 requests total.

**Climate adjustment formula (from the v0 plan):**
```python
climate_adj = 1.0 + 0.03 * max(0, wet_bulb_c - 15)
```
- At 15°C wet-bulb: 1.0 (baseline)
- At 25°C wet-bulb: 1.30 (+30% water)
- At 30°C wet-bulb: 1.45 (+45% water)
- Below 15°C: clamped to 1.0 (cold climates don't get a discount in v0)

**Expected results:** Phoenix ~22°C, Miami ~25°C, Seattle ~10°C, Maine ~10°C, Dallas ~21°C, Atlanta ~19°C, etc. These are intuitive.

**Output to console:** Distribution of `wet_bulb_c` (min, median, max, mean). List of facilities with `wet_bulb_c > 25` (the most stressed climate-wise).

**Output to file:** `data/processed/us_dc_with_climate.csv` (1,575 rows, adds `wet_bulb_c`, `climate_adj`).

### Task 2.3: `src/estimate_water.py` — physics model

**Input:** `data/processed/us_dc_with_climate.csv` (1,575 rows, with `est_mw`, `wet_bulb_c`, `climate_adj`)
**Output:** Same DataFrame plus `est_liters_per_day`, `wue_default`, and uncertainty columns.

**Physics formula (from the v0 plan):**
```python
WUE_DEFAULT = 1.8  # L/kWh, industry avg (Google/Microsoft disclosure avg)
LOAD_FACTOR = 0.7  # typical utilization
COOLING_PENALTY = 0.7  # unknown cooling type -> conservative

water_liters_per_day = est_mw * 1000 * 24 * LOAD_FACTOR * WUE_DEFAULT * COOLING_PENALTY * climate_adj
```

**Document every parameter** with a citation in the script docstring:
- WUE 1.8 L/kWh: Google 2024 environmental report average across data centers; Microsoft sustainability report similar
- LOAD_FACTOR 0.7: Uptime Institute 2023 global data center survey
- COOLING_PENALTY 0.7: Engineering rule of thumb; air-cooled = 0.2 L/kWh, evaporative = 1.8 L/kWh, water-cooled = 2.7 L/kWh, immersion = 0.1 L/kWh; 0.7 is the midpoint of these
- climate_adj: per v0 plan

**Uncertainty columns:**
- `est_liters_per_day_low` = `est_liters_per_day * 0.5` (cooling type air instead of unknown)
- `est_liters_per_day_high` = `est_liters_per_day * 1.5` (cooling type water-cooled)
- These give the ±50% band per the v0 plan

**Skip rows where `est_mw` is NaN** (the outliers we excluded). For those, output NaN in the water columns and flag with `mw_source='outlier_excluded'`.

**Output to console:**
- Total estimated water use across all US data centers (sum of `est_liters_per_day`)
- Top 10 facilities by est. water/day (likely hyperscalers in Arizona/Texas)
- Top 10 states by total est. water/day
- Distribution of `est_liters_per_day` (median, 90th percentile, max)

**Sanity check:** the US total should be in the **hundreds of billions of liters per day** range. Google alone discloses ~1 billion liters/day across all its DCs globally; the US has more than 1,500 facilities. So 100-500 billion L/day nationally is reasonable.

**Output to file:** `data/processed/us_dc_with_water.csv` (1,575 rows, adds `est_liters_per_day`, `est_liters_per_day_low`, `est_liters_per_day_high`).

### Task 2.4: `src/join_water_stress.py` — WRI state-level stress

**Input:** `data/processed/us_dc_with_water.csv` (1,575 rows, with state) + `data/external/wri_aqueduct/us_state_stress.csv` (51 rows)
**Output:** Same DataFrame plus `bws_score`, `bws_category`, and `stress_stressor_match` (a flag for facilities in High/Extremely High stress regions).

**Logic:**
```python
df = df.merge(wri, on='state', how='left')
df['stress_stressor_match'] = df['bws_category'].isin(['High', 'Extremely High'])
```

**Output to console:**
- Count of facilities in High/Extremely High stress states (the politically salient set)
- Top 5 states by (facility count × est water/day) — the "double jeopardy" of high stress AND high demand
- For Arizona specifically: count of facilities, total est. water/day, avg MW — Phoenix case study preview

**Output to file:** `data/processed/us_dc_with_stress.csv` (1,575 rows, the final Week 2 deliverable). This is the file that goes into the Week 3 Folium map.

### Task 2.5: `notebooks/03_physics_model.ipynb` — sanity check & sensitivity

A Jupyter notebook (or .py script that produces equivalent output) that does:

1. **Load** `us_dc_with_stress.csv` and produce the summary statistics
2. **Distribution plot** of `est_liters_per_day` (log scale — most DCs are small, a few are huge)
3. **Map preview** (static, matplotlib): scatter of facilities by lat/lon, color = `est_liters_per_day`
4. **State-level bar chart**: total est. water/day per state, stacked by WRI stress category
5. **Sensitivity analysis**:
   - What if WUE is 1.0 instead of 1.8? (air-cooled scenario)
   - What if WUE is 2.7? (water-cooled scenario)
   - What if load factor is 0.5 or 0.9?
   - Plot the resulting national total for each scenario
6. **"Double jeopardy" ranking**: states sorted by (facility count × WRI BWS × median est. water/day per facility). Top 5 should be AZ, CA, TX, VA, possibly CO or NE.

**Output:** `notebooks/03_physics_model.ipynb` (or `notebooks/03_physics_model.py` if .ipynb is hard to author without a running Jupyter server — the .py is fine for v0).

---

## Week 2 Done When

- [ ] `data/processed/us_dc_with_mw.csv` exists with `est_mw` for all rows that have valid operator classification
- [ ] `data/processed/us_dc_with_climate.csv` exists with `wet_bulb_c` and `climate_adj` for all rows (Open-Meteo cache populated)
- [ ] `data/processed/us_dc_with_water.csv` exists with `est_liters_per_day` and uncertainty bounds
- [ ] `data/processed/us_dc_with_stress.csv` exists with WRI state-level `bws_score`, `bws_category`, `stress_stressor_match` joined
- [ ] `notebooks/03_physics_model.ipynb` (or .py) covers the 6 sanity-check sections above
- [ ] Sanity-check passes: national total in 100-500B L/day range; AZ, CA, TX top 3 by total water use
- [ ] `docs/data_dictionary.md` is updated with the new columns (`est_mw`, `mw_source`, `wet_bulb_c`, `climate_adj`, `est_liters_per_day`, `est_liters_per_day_low/high`, `bws_score`, `bws_category`, `stress_stressor_match`)
- [ ] `docs/week_2_summary.md` is written — a 1-page report of what got built, key numbers, and open questions

---

## Tones & Principles

- **Civic, not preachy.** Write like FracTracker (https://www.fractracker.org/) — journalism/advocacy hybrid. Not a vendor pitch, not an activist pamphlet.
- **Cite everything.** Every assumption, every parameter, every MW value. The user is going to publish this.
- **Honest about uncertainty.** v0 estimates have ±50% bands. The methodology must say so, plainly. Cooling type is the biggest unknown.
- **Build the public's counter-infrastructure.** Operators have dashboards; the public has nothing. This is for the people who have to live next to these facilities.

---

## Out of Scope for v0 (Do Not Do)

- ML training (v1, on Colab Pro)
- Global coverage beyond US (v2)
- Real-time data, API, database
- Mobile optimization
- Press outreach
- Login / user accounts
- Sub-state stress overlay (v1)
- Phoenix case study research (Week 3)
- Folium map (Week 3)

---

## How to Start This Session

1. Read this entire document
2. Read `docs/v0_plan.md` for full context
3. Read `docs/week_1_summary.md` for what Week 1 produced
4. Read `docs/data_dictionary.md` to know the input columns
5. Check `.venv` exists (`ls /root/project/datacenter_water_stress/.venv/bin/python`); if not, create it
6. Begin Task 2.1 (estimate_power.py) — no need to ask permission, just go
7. Work through Tasks 2.1 → 2.5 sequentially
8. End of session: print a summary report of what was built, what's next, and any open questions for Hiroaki

**If a task is ambiguous, make a reasonable choice and document it.** The user has full latitude; the methodology must be defensible to a journalist or peer reviewer, not to an internal stakeholder.

---

## Reproducing Week 2 from scratch

```bash
cd /root/project/datacenter_water_stress

# Make sure venv is set up
test -d .venv || python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Run Week 1 first (idempotent)
.venv/bin/python src/clean_locations.py
.venv/bin/python src/build_wri_stress_lookup.py

# Run Week 2 pipeline
.venv/bin/python src/estimate_power.py        # → us_dc_with_mw.csv
.venv/bin/python src/fetch_climate.py         # → us_dc_with_climate.csv
.venv/bin/python src/estimate_water.py        # → us_dc_with_water.csv
.venv/bin/python src/join_water_stress.py     # → us_dc_with_stress.csv (final Week 2 deliverable)

# Open the sanity-check notebook
.venv/bin/python -m jupyterlab notebooks/03_physics_model.ipynb
# or
.venv/bin/python notebooks/03_physics_model.py
```

All Week 2 scripts are idempotent. Re-running with the same inputs produces the same outputs. The Open-Meteo cache (`data/external/open_meteo/*.json`) means re-running `fetch_climate.py` makes zero network calls.
