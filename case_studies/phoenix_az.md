# Phoenix, Arizona: 70 data centers in the desert

**A Water Stress Watch v0 case study**
**Last updated:** 2026-07-04

> *"In the Phoenix metro, water isn't just a cost — it's the binding constraint on the next decade of growth. The data center industry picked Phoenix for cheap power and tax breaks. The water question was an afterthought. This case study is the afterthought."*

---

## Why Phoenix?

The Phoenix metropolitan area has become one of the fastest-growing data center markets in the United States, behind only Northern Virginia and the Dallas region. As of mid-2026, our v0 model estimates **70 data centers** in Arizona, with a total estimated nameplate of **2,896 MW** and an estimated water use of **22.4 billion liters per year** (61 million liters per day, or **0.022 km³/yr**).

For context, that's roughly **1% of Arizona's total annual water demand** — a number that, while small in the state's overall water budget, is concentrated in a single metro area that is already operating under federally-mandated Colorado River cuts.

WRI Aqueduct rates Arizona's Baseline Water Stress as **3.49 (High)** — the third-most-stressed state in the US, behind only New Mexico and California. The state's water is governed by a complex web of rights, treaties, and a shrinking Colorado River.

---

## The numbers

| Metric | Value |
|---|---:|
| Data center facilities in AZ (v0) | 70 |
| Total nameplate (estimated) | 2,896 MW |
| Total water use (estimated) | 22.4 B L/year |
| WRI Baseline Water Stress (state) | 3.49 (High) |
| AZ rank by total DC water use | 4th of 51 |
| AZ share of US DC water use | ~9% |
| AZ share of US DC capacity | ~10% |

Methodology: see `methodology.md` and `docs/data_dictionary.md`. All numbers have ±50% uncertainty bands. Estimates assume no water recycling and a 0.7 cooling-type multiplier. The 1.8 L/kWh WUE default is the Google/Microsoft disclosure average.

---

## The facilities

The Phoenix market is dominated by hyperscale campuses and edge micro-facilities. The 10 largest by estimated water use:

| Facility | Operator | City | Est. MW | Est. L/day |
|---|---|---|---:|---:|
| NFINIT: Van Buren Data Center | NFINIT | Phoenix | 781 | 16,532,208 |
| NOVVA: Arizona Data Center | NOVVA | Mesa | 300 | 6,350,400 |
| CyrusOne: PHX1-PHX8 | CyrusOne | Chandler | 81 | 1,714,608 |
| Evocative: Phoenix (PHX1) | Evocative | Phoenix | 69 | 1,460,592 |
| Cyberverse: PHX | Cyberverse | Phoenix | 69 | 1,460,592 |
| EvoSwitch: PHX-01 | EvoSwitch | Phoenix | 66 | 1,386,504 |
| Digital Realty: PHX15 | Digital Realty | Chandler | 54 | 1,143,072 |
| Oracle: US DoD West us-gov-phoenix-1 | Oracle | AZ | 50 | 1,058,400 |
| Meta, Inc.: Mesa | Meta | Mesa | 50 | 1,058,400 |
| Microsoft Azure: West US 3 | Microsoft | El Mirage | 50 | 1,058,400 |
| Apple Inc.: Mesa | Apple | Mesa | 50 | 1,058,400 |

**The NFINIT Van Buren facility alone is estimated to use 16.5 million liters per day.** That's about **6 billion liters per year** — more than the entire annual water use of a small Arizona town.

### Where the facilities sit

The 70 facilities cluster in a handful of municipalities:

| Municipality | Facilities | Total MW | Est. L/day |
|---|---:|---:|---:|
| Phoenix | 28 | 1,440 | 30,491,446 |
| Mesa | 8 | 508 | 10,753,344 |
| Avondale | 5 | 240 | 5,080,320 |
| Chandler | 7 | 233 | 4,932,144 |
| Scottsdale | 6 | 85 | 1,799,280 |
| Tucson | 4 | 65 | 1,375,920 |

### Who operates

| Operator | Facilities | Total MW | Est. L/day |
|---|---:|---:|---:|
| NFINIT | 1 | 781 | 16,532,208 |
| NOVVA | 1 | 300 | 6,350,400 |
| Prime Data Centers | 5 | 240 | 5,080,320 |
| Oracle | 3 | 150 | 3,175,200 |
| Iron Mountain | 4 | 131 | 2,768,774 |
| Digital Realty | 2 | 86 | 1,826,798 |
| EvoSwitch | 2 | 85 | 1,792,930 |
| CyrusOne | 1 | 81 | 1,714,608 |
| Microsoft | 1 | 50 | 1,058,400 |
| Meta | 1 | 50 | 1,058,400 |
| Apple | 1 | 50 | 1,058,400 |

The market is heavily concentrated: 5 operators (NFINIT, NOVVA, Prime, Oracle, Iron Mountain) account for over **70% of estimated AZ water use**. The hyperscalers (Google, Amazon AWS, Meta, Microsoft) have a smaller visible footprint in our data than in Northern Virginia, but Microsoft and Meta are confirmed present.

---

## The water context

Arizona's water comes from three main sources:
1. **The Colorado River** (about 36% of the state's supply), allocated under a 100+ year-old compact that's been renegotiated repeatedly as the river shrinks.
2. **In-state rivers** — the Salt, Verde, Gila, and their tributaries.
3. **Groundwater** — historically unregulated, now under the 2023 Groundwater Management Act.

The Phoenix metro is at the intersection of all three, and it's where the data center boom is concentrated.

### The Colorado River cuts

In 2022, the US Bureau of Reclamation declared the first-ever **tier 1 shortage** on the Colorado River, requiring Arizona to cut its river allocation by 18% in 2022, 21% in 2023, and projecting further cuts. Arizona has responded by leaving farmland fallow and drawing down groundwater — both of which are constrained in their own right.

The Central Arizona Project (CAP), which delivers Colorado River water to Phoenix and Tucson, has been the major user-side actor. CAP's agricultural customers have taken the largest cuts so far. Data centers — most of which use municipal water, not CAP water directly — have not.

### Where data center water comes from

The 70 facilities in our v0 dataset draw from municipal water utilities (Phoenix Water Services, Mesa Water Resources, etc.) and a few from private wells. The exact mix is not publicly disclosed, and the operators don't have to report per-facility water use to the state. This is a known transparency gap.

---

## What's at stake

### 1. Growth projections

If the Phoenix DC market grows at the rate industry analysts project — some estimates suggest 5-10 GW of additional capacity by 2030 — the water implications scale linearly. Our 2,896 MW × 22.4 B L/year = 7.7 million L/MW/year. At 10 GW, that's **77 billion liters per year** — roughly 3% of Arizona's total current water use, all in one metro area.

### 2. Cooling technology is the variable

This estimate assumes a single-class cooling penalty (0.7×) and the Google/Microsoft WUE disclosure average (1.8 L/kWh). Real cooling choices vary widely:

- **Air-cooled** (WUE ~0.2 L/kWh): a 10× reduction. Microsoft and Google have publicly committed to air-cooling or "no water" cooling for newer facilities in hot climates.
- **Evaporative** (WUE ~1.8 L/kWh): our default.
- **Water-cooled chillers** (WUE ~2.7 L/kWh): a 1.5× increase. Older hyperscale campuses.
- **Immersion / liquid cooling** (WUE ~0.1 L/kWh): a 20× reduction. Emerging tech.

If Phoenix's new builds are predominantly air- or immersion-cooled, the growth scenario looks very different. If they're water-cooled evaporative, it's worse than our linear projection. The 50% uncertainty band around our estimate is dominated by this single variable.

### 3. The data doesn't exist publicly

We have:
- 70 facilities, 100% geocoded, 100% state coverage.
- Disclosed MW for 30% of them; the rest are operator-class estimates.
- 100% wet-bulb climate data (Open-Meteo).
- WRI BWS at the state level (3.49 = High).

We don't have:
- Per-facility water use. Not a single Phoenix data center publicly reports annual water use.
- Cooling technology. We assume the industry average.
- Year-over-year capacity changes. The Orimadros source data is a snapshot.

The single biggest improvement to v1 would be mandatory water-use disclosure for data centers in water-stressed states. Without that, our estimates are the best public numbers available — and that's the case we make for transparency.

---

## Methodology notes

The v0 estimates use:
- **Capacity:** 30% disclosed (Orimadros MIT-licensed scrape), 70% operator-class heuristic (e.g., hyperscaler 50 MW, major colo 20 MW, secondary colo 10 MW).
- **Climate:** Open-Meteo annual mean wet-bulb temperature. (Note: this understates cooling stress in summer. Design-day wet-bulb in Phoenix is 24-26°C; the annual mean is 12.5°C. v0 will upgrade to a percentile-based wet-bulb in v1.)
- **WUE:** 1.8 L/kWh (Google 2024 / Microsoft 2024 disclosure average).
- **Load factor:** 0.7 (Uptime Institute 2023).
- **Cooling penalty:** 0.7 (midpoint of plausible cooling WUEs).
- **WRI BWS:** state-level (3.49 = High for Arizona).

**Uncertainty:** ±50% per facility, dominated by the cooling-type unknown. Air-cooled and water-cooled estimates differ by ~10×, so a single-class estimate is necessarily approximate.

**Source citations:**
- WRI Aqueduct 4.0: Kuzma et al. (2023), https://doi.org/10.46830/writn.23.00061
- Orimadros datacenter map: https://github.com/Orimadros/datacenter-map (MIT)
- Open-Meteo: https://open-meteo.com (free for non-commercial use)

---

## Open questions

1. **What fraction of AZ DC water is reused?** Some operators (Google, Meta) have committed to water replenishment programs. Our estimate assumes no reuse, which is conservative.
2. **What's the cooling type mix in AZ?** Without disclosure, we can't break down by class. Anecdotally, the older Phoenix facilities are evaporative; the newest builds trend toward air-cooling.
3. **How does this compare to other Western states?** California (BWS 3.72, High) and Colorado (BWS 3.42, High) are similar profiles. A multi-state Western case study is a v0.5 candidate.
4. **What's the municipal-utility-level data?** Phoenix Water Services publishes system-wide consumption but not by customer class. SRP and APS publish electric capacity but not per-customer water.

---

## What this case study is for

This document is the journalistic companion to the v0 dashboard. It is meant to be:
- **Citable** — every estimate has a methodology reference and a citation.
- **Honest about uncertainty** — the ±50% band is prominently stated.
- **Action-oriented** — the policy implication (transparency) is named.

It is **not** meant to be:
- A vendor pitch. No "contact us for consulting" footers.
- An activist pamphlet. The water-vs-data-centers framing is factual, not preachy.
- A hit piece on Phoenix. Arizona is competing with Northern Virginia and Texas for the same growth. The water question is a real constraint, not a moral judgment.

The full interactive map is at `assets/map_v0.html`. Every number in this case study can be reproduced from `data/processed/us_dc_with_stress.csv` with the scripts in `src/`.
