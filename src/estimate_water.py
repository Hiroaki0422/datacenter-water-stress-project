"""
estimate_water.py — Apply the physics model to estimate per-facility water use.

For every facility in us_dc_with_climate.csv with a non-NaN est_mw, compute
the daily water use via the v0 physics formula:

    water_liters_per_day = est_mw * 1000 * 24 * LOAD_FACTOR * WUE * COOLING_PENALTY * climate_adj

where:
  - LOAD_FACTOR = 0.7      (Uptime Institute 2023)
  - WUE         = 1.8 L/kWh (Google/Microsoft disclosure average)
  - COOLING_PEN = 0.7      (midpoint of air/evap/water/immersion cooling WUE)
  - climate_adj = 1.0 + 0.03 * max(0, wet_bulb_c - 15)

Uncertainty:
  - est_liters_per_day_low  = point * 0.5  (air cooling, WUE 0.2 L/kWh)
  - est_liters_per_day_high = point * 1.5  (water cooling, WUE 2.7 L/kWh)

For rows with est_mw = NaN (MW outliers excluded), the water columns are
also NaN.

Inputs
------
data/processed/us_dc_with_climate.csv
    1,575 rows with est_mw, wet_bulb_c, climate_adj.

Outputs
-------
data/processed/us_dc_with_water.csv
    Same 1,575 rows plus:
      - est_liters_per_day         (float) : point estimate of daily water use.
      - est_liters_per_day_low     (float) : 50% of point estimate.
      - est_liters_per_day_high    (float) : 150% of point estimate.
      - wue_default (float)        : 1.8 (the WUE used, for traceability).

The script is idempotent: re-running with the same input produces identical output.

Author: Water Stress Watch v0 (Hiroaki Oshima)
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_CSV = PROJECT_ROOT / "data" / "processed" / "us_dc_with_climate.csv"
OUTPUT_CSV = PROJECT_ROOT / "data" / "processed" / "us_dc_with_water.csv"

# Physics parameters (citations in the module docstring).
WUE_DEFAULT = 1.8         # L/kWh — Google 2024 / Microsoft 2024 disclosure average
LOAD_FACTOR = 0.7         # typical utilization — Uptime Institute 2023
COOLING_PENALTY = 0.7     # midpoint of air (0.2) / evap (1.8) / water (2.7) / immersion (0.1)
UNCERTAINTY_LOW = 0.5     # air-cooled scenario
UNCERTAINTY_HIGH = 1.5    # water-cooled scenario
HOURS_PER_DAY = 24
KW_PER_MW = 1000


def compute_water_liters_per_day(est_mw: float, climate_adj: float) -> float:
    """The v0 physics formula. Returns NaN if est_mw is NaN."""
    if pd.isna(est_mw) or pd.isna(climate_adj):
        return np.nan
    return (
        est_mw
        * KW_PER_MW
        * HOURS_PER_DAY
        * LOAD_FACTOR
        * WUE_DEFAULT
        * COOLING_PENALTY
        * climate_adj
    )


def main() -> int:
    if not INPUT_CSV.exists():
        print(f"ERROR: input not found: {INPUT_CSV}", file=sys.stderr)
        print("Run src/fetch_climate.py first.", file=sys.stderr)
        return 1

    df = pd.read_csv(INPUT_CSV)
    print(f"Loaded {len(df):,} rows from {INPUT_CSV.relative_to(PROJECT_ROOT)}")

    # Apply the physics model row-by-row.
    df["est_liters_per_day"] = [
        compute_water_liters_per_day(m, ca)
        for m, ca in zip(df["est_mw"], df["climate_adj"])
    ]
    df["est_liters_per_day_low"] = df["est_liters_per_day"] * UNCERTAINTY_LOW
    df["est_liters_per_day_high"] = df["est_liters_per_day"] * UNCERTAINTY_HIGH
    df["wue_default"] = WUE_DEFAULT

    # ----- Console report ---------------------------------------------------
    valid = df["est_liters_per_day"].dropna()
    n_valid = len(valid)
    n_total = len(df)
    print(f"\n=== Water-use estimates ===")
    print(f"  n_valid   : {n_valid:,} / {n_total:,}")
    print(f"  n_nan     : {n_total - n_valid:,}  (excluded MW outliers)")
    if n_valid > 0:
        total_billions = valid.sum() / 1e9
        print(f"  total US est water/day : {total_billions:,.1f} billion L/day")
        print(f"  total US est water/yr  : {total_billions * 365 / 1000:,.1f} billion L/year (= km^3/yr)")
        print(f"  median  est L/day      : {valid.median():,.0f}")
        print(f"  p90     est L/day      : {valid.quantile(0.90):,.0f}")
        print(f"  max     est L/day      : {valid.max():,.0f}")

    print("\n=== Top 10 facilities by est. water/day ===")
    top = df.dropna(subset=["est_liters_per_day"]).nlargest(
        10, "est_liters_per_day"
    )
    print(
        top[["dc_id", "name", "provider", "state", "est_mw", "climate_adj", "est_liters_per_day"]]
        .to_string(index=False)
    )

    print("\n=== Top 10 states by total est. water/day ===")
    by_state = (
        df.dropna(subset=["est_liters_per_day"])
        .groupby("state")
        .agg(
            facilities=("dc_id", "count"),
            total_mw=("est_mw", "sum"),
            total_lpd=("est_liters_per_day", "sum"),
        )
        .sort_values("total_lpd", ascending=False)
        .head(10)
    )
    by_state["total_lpd_billions"] = by_state["total_lpd"] / 1e9
    print(by_state.to_string())

    # ----- Sanity check vs. handoff expectation -----------------------------
    print("\n=== Sanity check ===")
    if n_valid > 0:
        total_b = valid.sum() / 1e9
        if 100 <= total_b <= 500:
            print(f"  PASS: US total = {total_b:.0f} B L/day is in 100-500 range")
        else:
            print(
                f"  WARN: US total = {total_b:.0f} B L/day is OUTSIDE expected 100-500 range"
            )
        top3 = by_state.head(3).index.tolist()
        if {"AZ", "CA", "TX"}.issubset(set(top3)):
            print(f"  PASS: AZ, CA, TX are all in the top 3 ({top3})")
        elif "CA" in top3 and "TX" in top3:
            print(f"  PARTIAL: top 3 = {top3}; expected AZ, CA, TX")
        else:
            print(f"  WARN: top 3 = {top3}; expected AZ, CA, TX")

    # ----- Write output -----------------------------------------------------
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nWrote {len(df):,} rows to {OUTPUT_CSV.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
