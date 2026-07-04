# Water Stress Watch

> A public estimate of US data center water use, overlaid on water-stressed regions.

[![License: MIT](https://img.shields.io/badge/code-MIT-blue.svg)](LICENSE)
[![License: CC-BY 4.0](https://img.shields.io/badge/data-CC--BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![WRI Aqueduct: CC-BY 4.0](https://img.shields.io/badge/WRI_Aqueduct-CC--BY%204.0-green.svg)](https://creativecommons.org/licenses/by/4.0/)
[![v0 status](https://img.shields.io/badge/status-v0%20(proof%20of%20concept)-yellow.svg)](docs/week_2_summary.md)

---

## What this is

Data center operators have dashboards. The public has nothing.

**Water Stress Watch** is a public-interest research project that estimates where the 1,575 known US data centers sit, how much water they use, and whether the surrounding region is water-stressed. The output is a single static HTML map that anyone can open, scrutinize, and use as the basis for journalism, advocacy, or research.

This is the **v0 (proof-of-concept)** release. The methodology is a single physics formula with a published ±50% uncertainty band. The output is reproducible from the data and code in this repository. There is no trained ML model in v0; that is a v1 project on Colab Pro.

**The v0 estimate:** US data centers use approximately **237 billion liters of water per year** (0.65 B L/day). 22% of facilities (352 of 1,575) are in states rated High or Extremely High water stress by WRI Aqueduct.

## What's in this repository

```
datacenter_water_stress/
├── README.md                       # this file
├── methodology.md                  # citable methodology writeup
├── docs/
│   ├── v0_plan.md                  # original v0 plan
│   ├── data_dictionary.md          # column-by-column schema for all datasets
│   ├── week_1_summary.md           # Week 1 (data cleaning) report
│   ├── week_2_summary.md           # Week 2 (estimation pipeline) report
│   └── handoff_*.md                # session handoff docs
├── data/
│   ├── raw/                        # Orimadros MIT scrape + ATLAS reference
│   ├── processed/                  # v0 outputs: us_dc_with_stress.csv (FINAL)
│   └── external/
│       ├── wri_aqueduct/           # WRI BWS data + raw API response
│       ├── us_states_20m.geojson   # US state polygons (Census, public domain)
│       └── open_meteo/             # cached Open-Meteo API responses
├── src/
│   ├── clean_locations.py          # Week 1: state normalization + dedup
│   ├── build_wri_stress_lookup.py  # Week 1: WRI pull + state-level aggregation
│   ├── estimate_power.py           # Week 2: operator-class MW heuristic
│   ├── fetch_climate.py            # Week 2: Open-Meteo wet-bulb pull (cached)
│   ├── estimate_water.py           # Week 2: physics formula
│   ├── join_water_stress.py        # Week 2: WRI state-level join
│   └── build_map.py                # Week 3: Folium/Leaflet map
├── notebooks/
│   ├── 03_physics_model.py         # Week 2: sanity check + sensitivity
│   └── explore_orimadros_*.py      # Week 1: data exploration
├── case_studies/
│   └── phoenix_az.md               # Week 3: Phoenix AZ narrative
├── assets/
│   └── map_v0.html                 # Week 3: the public map (FINAL)
└── requirements.txt
```

## How to use this

**Just want the map?** Open [`assets/map_v0.html`](assets/map_v0.html) in any modern browser. Click the WRI choropleth to see state-level stress; click a data center marker to see its estimated water use and stress context.

**Want the data?** `data/processed/us_dc_with_stress.csv` has 1,575 rows × 25 columns. See [`docs/data_dictionary.md`](docs/data_dictionary.md) for the schema.

**Want to replicate from scratch?** Run:

```bash
git clone <this-repo>
cd datacenter_water_stress
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Week 1
python src/clean_locations.py
python src/build_wri_stress_lookup.py

# Week 2
python src/estimate_power.py
python src/fetch_climate.py
python src/estimate_water.py
python src/join_water_stress.py

# Sanity check
python notebooks/03_physics_model.py

# Week 3: the public map
python src/build_map.py
# → opens at assets/map_v0.html
```

Total runtime: ~5 minutes cold, ~30 seconds warm (Open-Meteo is cached).

**Want to verify a specific number?** Every estimate in this README, the case study, and the methodology is traceable to a script in `src/` and a row in `data/processed/`. The `notebooks/03_physics_model.py` script emits a full summary.

## Methodology in one paragraph

For every US data center in the Orimadros MIT scrape, we apply `L/day = MW × 1000 × 24 × 0.7 × 1.8 × 0.7 × climate_adj`, where MW is either disclosed or estimated by operator class, the `0.7 × 0.7` is load factor × cooling-type penalty, the `1.8` is the Google/Microsoft WUE disclosure average, and `climate_adj = 1.0 + 0.03 × max(0, wet_bulb − 15)` with wet-bulb pulled from Open-Meteo for the facility's lat/lon. State-level WRI BWS is joined on the `state` column. Every parameter is cited in `methodology.md`. The v0 estimate has a published ±50% uncertainty band per facility, dominated by the cooling-type unknown.

## Headline findings

| | |
|---|---|
| US data center water use (v0 estimate) | **237 B L/year** (0.65 B L/day) |
| US data center nameplate (estimated) | **30,397 MW** |
| Implied average WUE (sanity check) | 1.18 L/kWh |
| Facilities in High/Extremely-High WRI states | **352 (22%)** |
| Top 3 states by total est. L/day | **VA, TX, CA** (Loudoun dominates) |
| #1 in stress-weighted demand | **AZ** (BWS 3.49, 22 B L/year) |
| Source disclosure: WRI Aqueduct CC-BY 4.0 | Kuzma et al. (2023), DOI 10.46830/writn.23.00061 |

## What this project is not

- **Not a commercial tool.** The map is free and the data is CC-BY 4.0.
- **Not a calibrated model.** v0 is a first estimate with ±50% uncertainty. v1 will use an ML model trained on operator disclosures.
- **Not a real-time system.** v0 is a static snapshot. The Orimadros data is from 2024; the climate is 2023; the WRI stress is the 2023 Aqueduct release.
- **Not a regulatory instrument.** This is a journalism/advocacy research artifact. It is not intended for compliance, billing, or policy enforcement.
- **Not a complete census.** v0 has 1,575 facilities. The actual number of US data centers is higher; some are private, some are not in the Orimadros scrape, some are telecom PoPs we classify as small.

## Who is this for

- **Journalists** writing about data center environmental impact. The map, the case study, and the underlying data are reusable with attribution.
- **Residents and community advocates** in data center host regions. The stress overlay answers "is my region water-stressed and how many data centers are nearby?"
- **Researchers** in data center sustainability, water resources, or environmental policy. Every estimate is reproducible.
- **Policymakers** evaluating disclosure requirements or water-rights policy. The transparency gap (no per-facility disclosure) is the most actionable finding.

## Why I'm doing this

I'm a data scientist who works in AI infrastructure. I see the asymmetry: operators have precise per-facility data on power and water; the public has nothing. The v0 release is a first attempt to close that gap, with all assumptions published.

I am not anti-AI or anti-data-center. I am pro-transparency. The next decade of data center growth is a real policy question, and the people who have to live next to these facilities deserve better than silence.

## What's next

- **v0.5 (this summer):** design-day wet-bulb instead of annual mean; Lumen/Cogent reclassification pass; data refresh.
- **v1 (2026 Q3, on Colab Pro):** XGBoost model trained on Google/Microsoft/Meta disclosed WUE; cooling-type classifier; narrower uncertainty bands.
- **v1.5 (2026 Q4):** sub-basin (HUC-8) stress overlay; multi-state Western case study.
- **v2 (2027):** global coverage; per-facility disclosed water use (as it becomes available).

## License

- **Code** (in `src/`, `notebooks/`): MIT.
- **Data and documentation** (in `data/`, `docs/`, `case_studies/`, `README.md`, `methodology.md`): CC-BY 4.0.
- **WRI Aqueduct data** (sub-component of `data/external/wri_aqueduct/`): CC-BY 4.0 (Kuzma et al. 2023).
- **State polygons** (`data/external/us_states_20m.geojson`): public domain (US Census Bureau).

If you use this work, please cite the project (see `methodology.md` Section 14 for the citation format).

## Acknowledgments

- **WRI Aqueduct 4.0** for the public water stress data (Kuzma et al. 2023).
- **Orimadros** for the MIT-licensed datacenter location scrape.
- **Open-Meteo** for the free historical weather API.
- **US Census Bureau** for the public-domain state polygon file.
- The FracTracker, Climate Central, and other civic-data journalism projects that set the tone this work tries to match.

— Hiroaki Oshima
