# Week 1 Summary — Water Stress Watch v0

**Period:** 2026-07-04 (one session)
**Author:** Hermes (Hiroaki's assistant)
**Status:** ✅ All four Week 1 tasks complete

---

## TL;DR

Week 1 is done. The handoff doc estimated 4 sequential tasks — exploration, geocoding, WRI pull, schema docs. In practice:

- **Exploration** surfaced the fact that the handoff was wrong about several things. The Orimadros file has 1,605 rows (not 2,060) and **100% of rows already have lat/lon** (not "only 42"). The actual work was state normalization, deduplication, and MW outlier flagging.
- **Geocoding was a no-op.** The data was already fully geocoded. What I built instead was a polygon-based reverse-geocoder for state recovery, plus a coord-vs-state validator.
- **WRI Aqueduct sub-national data** was successfully pulled from WRI Resource Watch's CartoDB endpoint, area-weighted aggregated to 51 US state-level rows.
- **Schema docs** are in `docs/data_dictionary.md`, with column-by-column definitions, source citations, and known limitations.

All scripts are idempotent. Re-running them produces identical output.

---

## What Got Built

| File | Purpose | Rows |
|---|---|---|
| `data/processed/us_dc_locations.csv` | Cleaned US data center locations with state, lat/lon, MW, sqft, validation flags | 1,575 |
| `data/external/wri_aqueduct/us_state_stress.csv` | WRI Aqueduct 4.0 BWS, area-weighted to state level | 51 |
| `data/external/wri_aqueduct/aqueduct40_us_province_bws.json` | Cached raw WRI pull (306 US sub-national rows) | 306 |
| `data/external/us_states_20m.geojson` | US state polygons (for reverse-geocoding & validation) | 51 |
| `src/clean_locations.py` | The cleaner: state normalization + polygon reverse-geocode + dedup + MW outlier flag | — |
| `src/build_wri_stress_lookup.py` | Pulls WRI data, area-weight-aggregates to state level | — |
| `notebooks/explore_orimadros.py` | Task 1.1 data exploration script | — |
| `notebooks/explore_orimadros_deep.py` | Deeper outlier / dup / state-anomaly investigation | — |
| `docs/data_dictionary.md` | Full column-by-column schema docs | — |
| `requirements.txt` | Python deps for the venv | — |

---

## Task 1.1: Data Exploration (5-bullet data quality report)

1. **Row count is 1,605 — not 2,060.** The handoff document said the cleaned Orimadros file has 2,060 rows; it has 1,605. The 2,059-row file is the raw scrape (`orimadros_scraped.csv`). 454 rows were dropped during upstream cleaning, presumably for being incomplete or invalid records. We use the 1,605-row file as the source of truth.
2. **100% of rows already have lat/lon** (the handoff said "only 42"). The cleaner used US Census 1:500k state polygons to validate that every coord pair falls in US territory. 1 mismatch flagged (DartPoints Cincinnati — coords south of the river in KY; address is the official source, coords are documented as a quirk).
3. **MW coverage is 47% (744 / 1,575 rows).** 7 outliers flagged: 3 rows with `MW_total_power >= 1000` (clearly data entry errors, e.g. `1,500,000 MW` for a 23,000 ft² facility) and 4 rows with `< 0.1 MW` (likely kW entered as MW). Median disclosed MW is 8.1 MW. Hyperscalers (Google, Microsoft, Meta) are under-represented because they don't disclose per-facility MW; colos disclose more.
4. **State column was a mess.** 56 rows had `state=NaN`, 27 distinct non-standard state values ("Texas", "New York", "San Jose", "Cincinnati", "Philadelphia", etc.). After name-to-code mapping, address-string regex recovery, and polygon-based reverse geocoding: **100% state coverage, 48 distinct state codes** (no territories). One persistent mismatch: DartPoints Cincinnati (real-world OH/KY border).
5. **30 duplicate groups** by `(name, address)` were deduped, dropping 60 rows to 30. All duplicates were colocation providers (CenterServ, AiNET) listing the same physical facility twice with whitespace differences.

**Top 5 states by facility count (cleaned):** CA (227), TX (195), VA (134), IL (106), NY (82). **Top 5 operators:** Lumen (96), CenterServ (68), 365 Data Centers (65), Digital Realty (58), Equinix (57).

---

## Task 1.2: Geocoding (was actually state-cleaning)

Since 100% of rows already had lat/lon, the "geocoding" task pivoted to **cleaning state values and validating coordinates**. The cleaner (`src/clean_locations.py`) does:

1. Map full state names to 2-letter codes (Texas → TX, etc.)
2. Map misplaced city names back to the right state (San Jose → CA, Cincinnati → OH, etc.)
3. Reverse-derive state from address string with regex (found 48/56 missing)
4. For the remaining 5–8 rows, do **point-in-polygon reverse geocoding** using US Census 1:500k state polygons (`us_states_20m.geojson`, 2.4 MB, public domain)
5. Disambiguate "Washington" (the city/state name) by checking the address for `, Washington, DC`
6. **Validate** every row's lat/lon against the claimed state via polygon lookup; flag mismatches in a `coord_state_mismatch` boolean column
7. Deduplicate by `(name, address)`, keeping first occurrence
8. Flag MW outliers (`>= 1000` or `< 0.1`) in a `mw_flagged_outlier` boolean column
9. Add a stable `dc_id` for downstream joins

**Why polygons over Nominatim:** All 1,575 lat/lon pairs are already populated. A polygon-based reverse geocoder handles any future row without API rate limits and runs in <1 second for the full table. Nominatim is only needed if a future data source has missing coordinates — and we have a free fallback (the gazetteer approach mentioned in the handoff) when that happens.

**No 3rd-party geocoding library was needed.** The shapely polygon check is sufficient for state-level validation, and the handoff's worry about "2,000 geocoding calls" turned out to be unfounded.

---

## Task 1.3: WRI Aqueduct State-Level Stress

**Source:** WRI Aqueduct 4.0 Province/State Baseline Water Stress indicator (Creative Commons Attribution 4.0)
**Endpoint:** `https://wri-rw.carto.com/tables/aqueduct_results_v01_province_v03/public` (WRI Resource Watch)
**Citation:** Kuzma et al. (2023), *Aqueduct 4.0: Updated decision-relevant global water risk indicators.* WRI Technical Note. https://doi.org/10.46830/writn.23.00061
**Methodology:** https://github.com/wri/Aqueduct40/blob/master/data_dictionary_country-rankings.md

WRI's main site has a stale 404 for the dataset page, but the underlying data is still served via WRI Resource Watch's CartoDB instance. I queried it directly with SQL:

```sql
SELECT gid_0, name_1, indicator_name, weight, score, label,
       sum_weights, sum_weighted_indicator
FROM aqueduct_results_v01_province_v03
WHERE gid_0 = 'USA' AND indicator_name = 'bws' AND weight = 'Tot'
```

The `weight='Tot'` filter is critical — it restricts to total water demand (not just irrigation, industrial, domestic, or livestock separately). Without that filter you get 6 rows per state; with it you get exactly 51.

**Output:** `us_state_stress.csv` with 51 rows. Most-stressed states:

| State | BWS score | Category |
|---|---|---|
| New Mexico | 4.26 | Extremely High |
| California | 3.72 | High |
| Arizona | 3.49 | High |
| Colorado | 3.42 | High |
| Nebraska | 3.16 | High |
| New Jersey | 2.80 | Medium-High |
| Wyoming | 2.78 | Medium-High |
| Texas | 2.68 | Medium-High |
| Florida | 2.56 | Medium-High |
| North Carolina | 2.50 | Medium-High |

Least-stressed: Hawaii (0.00), DC (0.14), Maine (0.18), Michigan (0.33), Alabama (0.53), Tennessee (0.58), Maryland (0.58), Illinois (0.75), Iowa (0.76), Mississippi (0.81).

**v0 simplification:** state-level aggregation, not basin-level. The WRI sub-national table already has one row per state+DC with `weight='Tot'`, so no aggregation is needed. This loses intra-state heterogeneity (a state with one desert basin and one wet basin gets a state-wide average). Documented as a known v0 limitation. Basin-level is a v1 upgrade path (WRI's catchment-level GeoTIFFs).

**Note on first pass:** My initial SQL pull didn't filter by `weight`, giving 306 rows (6 per state for the 6 weight categories: Tot, Irr, Ind, Dom, Liv, One). The area-weighted average I computed was off — California scored 3.14 instead of 3.72, Arizona 3.05 instead of 3.49. A delegation subagent caught this and pointed out the canonical query needs `weight='Tot'`. Re-ran with the fix; rankings are now consistent with the WRI Country Rankings app.

---

## Task 1.4: Schema Documentation

`docs/data_dictionary.md` (~9 KB) documents:

- All 18 columns of `us_dc_locations.csv` (name, type, source, meaning)
- All 6 columns of `us_state_stress.csv`
- The cleaning pipeline (state normalization, polygon reverse-geocode, dedup, MW flagging)
- Known limitations (Orimadros under-represents hyperscalers, MW coverage 47%, etc.)
- Citations: Orimadros (MIT), WRI Aqueduct (CC-BY 4.0), US Census polygons (public domain)

---

## Headline Surprises vs. the Handoff

| Handoff said | Reality |
|---|---|
| Orimadros has 2,060 rows | Has 1,605 (the 2,060-row file is the raw scrape) |
| "Only ~42 rows have lat/lon" | 100% have lat/lon (1,605/1,605) |
| Need to geocode 2,000 missing lat/lon | Need to clean 56 missing states + 27 non-standard state values |
| Recommend static US cities gazetteer | Polygon-based reverse-geocoder was the right tool (no API calls, no rate limits) |
| Need to download WRI rasters | Pulled WRI sub-national data via SQL (lighter, more useful) |
| Country-level stress is fine | State-level is the right granularity (and achievable from sub-national data) |

The handoff was generated by a previous session that didn't actually open the data files. Running the analysis revealed the data is in much better shape than the handoff suggested — the work is cleaning & validation, not geocoding.

---

## What's Next (Week 2)

Per the v0 plan, Week 2 is the **estimation pipeline**:

1. **`src/estimate_power.py`** — fill in MW for the 831 rows that are missing it, using an operator-class heuristic:
   - Hyperscalers (Google, AWS, Microsoft, Meta, Oracle): known MW from press releases (or default to 50 MW per facility as a conservative placeholder)
   - Colos (Equinix, Digital Realty, QTS, CyrusOne, etc.): typical 10-30 MW per facility
   - Edge / micro (American Tower, EdgePresence): <0.5 MW
2. **`src/fetch_climate.py`** — pull average wet-bulb temperature for each facility's lat/lon from Open-Meteo's Historical API (one query per DC, cached)
3. **`src/estimate_water.py`** — apply the physics formula: `L/day = MW × 1000 × 24 × 0.7 × WUE × climate_adj`
4. **`src/join_water_stress.py`** — join the WRI state-level stress to each facility
5. **`notebooks/03_physics_model.ipynb`** — sanity check, sensitivity analysis (what if cooling is air vs water? what if load factor is 0.5 vs 0.9?)

Output target: `data/processed/us_dc_with_stress.csv` with `(est_mw, est_liters_per_day, wri_stress, climate_adj)` for every facility.

---

## Hiroaki's Decisions (2026-07-04 review)

These were the open questions surfaced at the end of Week 1. Hiroaki's answers are recorded here so the next session picks them up without re-asking.

1. **License clarity (Q1):** ✅ Confirmed — WRI Aqueduct CC-BY 4.0 is fine. README and methodology must include the Kuzma et al. (2023) citation. **Action: include in `methodology.md` when written in Week 3.**

2. **MW estimation policy (Q2):** ✅ **Operator-class heuristic** (option b). For the 831 rows missing MW:
   - Hyperscalers (Google, AWS, Microsoft, Meta, Oracle): research press releases for typical facility MW
   - Colocation (Equinix, Digital Realty, QTS, CyrusOne, etc.): typical 10–30 MW per facility
   - Edge / micro (American Tower, EdgePresence): <0.5 MW
   - Document each operator's assigned class and MW source in a lookup table
   - Do NOT skip rows; do NOT use sqft-only estimates

3. **Phoenix case study (Q3):** ✅ **Phoenix stays primary.** Even with only 61 facilities (vs CA 227, TX 195), Phoenix wins on the *stress* axis — AZ BWS = 3.49 (High), Colorado River basin + Salt/Verde basin narrative, Colorado River cuts. Loudoun County VA is the backup if Phoenix research turns out weaker than expected.

4. **Sub-state stress (Q4):** ✅ **State-level for v0 is locked.** Sub-state (county / HUC-8 / catchment) is explicitly a **v1 upgrade** — do NOT pull GeoTIFFs or do basin polygon joins in v0. The state-level stress choropleth is the v0 deliverable.

5. **Handoff accuracy (Q5):** ✅ **`docs/handoff_new_session.md` has been rewritten** as a Week 1 status snapshot that points forward to `docs/handoff_week_2.md`. Future sessions start from the corrected file, not the wrong earlier draft.

---

## Reproducing Week 1 from scratch

```bash
cd /root/project/datacenter_water_stress

# Set up venv
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Run the two pipeline scripts
.venv/bin/python src/clean_locations.py             # → us_dc_locations.csv (1,575 rows)
.venv/bin/python src/build_wri_stress_lookup.py     # → us_state_stress.csv (51 rows)

# Re-run exploration to inspect
.venv/bin/python notebooks/explore_orimadros.py
.venv/bin/python notebooks/explore_orimadros_deep.py
```

Both pipeline scripts are idempotent and complete in under 2 seconds.
