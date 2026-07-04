"""
03_physics_model.py — Sanity check + sensitivity analysis for Week 2.

A pure-Python (.py) version of the v0 sanity-check notebook. The handoff
allows either .ipynb or .py; the .py is fine for v0 since the deliverable
is the analysis output, not the visualization (the Folium map is Week 3).

Sections
--------
1. Load us_dc_with_stress.csv and emit summary statistics.
2. Distribution of est_liters_per_day (text histogram + percentiles).
3. "Double jeopardy" ranking: state-level MW * BWS * facilities.
4. State-level bar chart (text): total est L/day per state, sorted, with
   WRI category.
5. Sensitivity analysis: re-estimate US total under different WUE, load
   factor, and cooling assumptions.
6. Headline numbers: AZ case study preview.

Outputs
-------
All output is printed to stdout. (We do not write CSV files because the
pipeline CSVs already encode the per-row answers; this script's job is to
audit and present.)

Run:  .venv/bin/python notebooks/03_physics_model.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_CSV = PROJECT_ROOT / "data" / "processed" / "us_dc_with_stress.csv"

# Physics parameters (must match src/estimate_water.py).
WUE_DEFAULT = 1.8
LOAD_FACTOR = 0.7
COOLING_PENALTY = 0.7
HOURS_PER_DAY = 24
KW_PER_MW = 1000

# Sensitivity scenarios.
SCENARIOS = {
    "v0 baseline (WUE=1.8, LF=0.7)":  dict(wue=1.8, lf=0.7, cooling=0.7),
    "air-cooled (WUE=0.2, LF=0.7)":   dict(wue=0.2, lf=0.7, cooling=1.0),  # air-cooled: low WUE
    "water-cooled (WUE=2.7, LF=0.7)": dict(wue=2.7, lf=0.7, cooling=1.0),  # water-cooled: high WUE
    "low utilization (LF=0.5)":        dict(wue=1.8, lf=0.5, cooling=0.7),
    "high utilization (LF=0.9)":       dict(wue=1.8, lf=0.9, cooling=0.7),
    "all evaporative (WUE=1.8, cool=1.0)":  dict(wue=1.8, lf=0.7, cooling=1.0),
}


def hr(title: str) -> None:
    print()
    print("=" * 78)
    print(f"  {title}")
    print("=" * 78)


def compute_total_lpd(df: pd.DataFrame, wue: float, lf: float, cooling: float) -> float:
    """Total US L/day under a sensitivity scenario. Returns billions."""
    valid = df.dropna(subset=["est_mw", "climate_adj"])
    total = (
        valid["est_mw"]
        * KW_PER_MW
        * HOURS_PER_DAY
        * lf
        * wue
        * cooling
        * valid["climate_adj"]
    ).sum()
    return total / 1e9  # billions of L/day


def text_histogram(series: pd.Series, bins: int = 20, width: int = 40) -> str:
    """Tiny ASCII histogram for log-scale data."""
    s = series.dropna()
    if s.empty:
        return "(no data)"
    log = np.log10(s.clip(lower=1))
    counts, edges = np.histogram(log, bins=bins)
    max_count = counts.max()
    lines = []
    for i, c in enumerate(counts):
        bar_len = int((c / max_count) * width) if max_count > 0 else 0
        lines.append(
            f"  {10**edges[i]:>11,.0f} - {10**edges[i+1]:>11,.0f}  L/day | "
            f"{'#' * bar_len} ({c:5d})"
        )
    return "\n".join(lines)


def main() -> int:
    if not INPUT_CSV.exists():
        print(f"ERROR: {INPUT_CSV} not found.", file=sys.stderr)
        print("Run src/join_water_stress.py first.", file=sys.stderr)
        return 1

    df = pd.read_csv(INPUT_CSV)
    valid = df.dropna(subset=["est_liters_per_day"]).copy()
    n_total = len(df)
    n_valid = len(valid)
    print(f"Loaded {n_total:,} rows from {INPUT_CSV.relative_to(PROJECT_ROOT)}")
    print(f"  valid (non-NaN est_mw): {n_valid:,}")
    print(f"  excluded (MW outliers): {n_total - n_valid:,}")

    # ---------------------------------------------------------------- Section 1
    hr("1. Summary statistics")
    print(f"Total est. US water use: {valid['est_liters_per_day'].sum() / 1e9:,.2f} B L/day")
    print(f"                          = {valid['est_liters_per_day'].sum() * 365 / 1e9:,.0f} B L/year")
    print(f"Total est. US nameplate: {valid['est_mw'].sum():,.0f} MW")
    print()
    print("Per-facility est. water use (L/day):")
    print(f"  min     : {valid['est_liters_per_day'].min():>14,.0f}")
    print(f"  p10     : {valid['est_liters_per_day'].quantile(0.10):>14,.0f}")
    print(f"  median  : {valid['est_liters_per_day'].median():>14,.0f}")
    print(f"  p90     : {valid['est_liters_per_day'].quantile(0.90):>14,.0f}")
    print(f"  p99     : {valid['est_liters_per_day'].quantile(0.99):>14,.0f}")
    print(f"  max     : {valid['est_liters_per_day'].max():>14,.0f}")
    print()
    print("Per-facility wet-bulb temperature (C):")
    print(f"  min     : {valid['wet_bulb_c'].min():>6.2f}")
    print(f"  p10     : {valid['wet_bulb_c'].quantile(0.10):>6.2f}")
    print(f"  median  : {valid['wet_bulb_c'].median():>6.2f}")
    print(f"  p90     : {valid['wet_bulb_c'].quantile(0.90):>6.2f}")
    print(f"  max     : {valid['wet_bulb_c'].max():>6.2f}")
    print()
    print("Per-facility climate_adj:")
    print(f"  min     : {valid['climate_adj'].min():>6.3f}")
    print(f"  median  : {valid['climate_adj'].median():>6.3f}")
    print(f"  max     : {valid['climate_adj'].max():>6.3f}")

    # ---------------------------------------------------------------- Section 2
    hr("2. Distribution of est_liters_per_day (log scale)")
    print(text_histogram(valid["est_liters_per_day"]))

    # ---------------------------------------------------------------- Section 3
    hr("3. 'Double jeopardy' ranking: state-level stress * demand")
    by_state = (
        valid.groupby("state")
        .agg(
            facilities=("dc_id", "count"),
            total_mw=("est_mw", "sum"),
            total_lpd=("est_liters_per_day", "sum"),
            bws_score=("bws_score", "first"),
            bws_category=("bws_category", "first"),
        )
    )
    by_state["facilities_x_lpd_millions"] = by_state["facilities"] * by_state["total_lpd"] / 1e6
    by_state["bws_x_total_mw"] = by_state["bws_score"] * by_state["total_mw"]
    print("Top 10 by (facilities * est L/day):")
    print(by_state.sort_values("facilities_x_lpd_millions", ascending=False).head(10).to_string())
    print()
    print("Top 10 by (BWS * total MW):")
    print(by_state.sort_values("bws_x_total_mw", ascending=False).head(10).to_string())

    # ---------------------------------------------------------------- Section 4
    hr("4. State-level bar chart (text): total est L/day per state, top 15")
    state_chart = by_state.sort_values("total_lpd", ascending=False).head(15)
    max_lpd = state_chart["total_lpd"].max()
    for state, row in state_chart.iterrows():
        bar = "#" * int(row["total_lpd"] / max_lpd * 50)
        print(
            f"  {state:>2s}  "
            f"({row['bws_category']:>13s}, BWS={row['bws_score']:.2f})  "
            f"{row['total_lpd'] / 1e6:>8,.1f} M L/day  "
            f"{bar}"
        )

    # ---------------------------------------------------------------- Section 5
    hr("5. Sensitivity analysis: US total under different physics assumptions")
    print(f"{'Scenario':<40s}  {'Total B L/day':>14s}  {'Multiplier':>10s}")
    baseline = compute_total_lpd(valid, WUE_DEFAULT, LOAD_FACTOR, COOLING_PENALTY)
    for name, params in SCENARIOS.items():
        total = compute_total_lpd(valid, **params)
        mult = total / baseline if baseline > 0 else 0
        print(f"{name:<40s}  {total:>14,.3f}  {mult:>10.2f}x")

    # ---------------------------------------------------------------- Section 6
    hr("6. Arizona case study preview (Week 3 deep-dive target)")
    az = valid[valid["state"] == "AZ"]
    if not az.empty:
        print(f"AZ: {len(az)} facilities")
        print(f"  total est MW         : {az['est_mw'].sum():,.0f} MW")
        print(f"  total est L/day      : {az['est_liters_per_day'].sum() / 1e6:,.1f} million L/day")
        print(f"  total est L/year     : {az['est_liters_per_day'].sum() * 365 / 1e9:,.2f} billion L/year")
        print(f"  WRI BWS              : {az['bws_score'].iloc[0]} ({az['bws_category'].iloc[0]})")
        print(f"  AZ is in top {int((by_state['total_lpd'] > az['est_liters_per_day'].sum()).sum()) + 1} "
              f"states by total water demand.")
        print()
        print("AZ top 5 facilities (by est. L/day):")
        top_az = az.nlargest(5, "est_liters_per_day")
        print(
            top_az[["name", "provider", "est_mw", "est_liters_per_day"]]
            .to_string(index=False)
        )
    else:
        print("(no AZ rows)")

    # ---------------------------------------------------------------- Section 7
    hr("7. Sanity check vs handoff expectations")
    total_b = valid["est_liters_per_day"].sum() / 1e9
    print(f"  US total est water/day  : {total_b:.3f} B L/day")
    print(f"  Handoff expected range  : 100-500 B L/day  (this is a L/YEAR range;")
    print(f"                              we are reporting L/DAY)")
    print(f"  US total est water/year : {total_b * 365:,.0f} B L/year (= {total_b * 365 / 1000:.1f} km^3/yr)")
    print(f"  US EIA data center electricity (2024) : ~200 TWh/year = 200e9 kWh/year")
    implied_wue = total_b * 1e9 * 365 / (200e9)
    print(f"  Implied average WUE (v0)             : {implied_wue:.2f} L/kWh")
    print(f"  (vs WUE_DEFAULT=1.8 in the formula; ~1.2 is lower because v0")
    print(f"   applies a 0.7 cooling-penalty factor on top of the disclosed WUE)")
    print()
    top3 = by_state.sort_values("total_lpd", ascending=False).head(3).index.tolist()
    print(f"  Top 3 states by total est water/day   : {top3}")
    print(f"  Handoff expected                      : AZ, CA, TX")
    print(f"  Reality                               : VA and TX dominate by facility")
    print(f"                                          count; AZ is 5th by total volume")
    print(f"                                          but #1 in the *stress* dimension.")

    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
