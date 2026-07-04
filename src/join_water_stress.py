"""
join_water_stress.py — Join WRI Aqueduct state-level water stress.

For every facility in us_dc_with_water.csv, attach the WRI Baseline Water
Stress (BWS) score and category for the facility's state, and flag
facilities in High or Extremely High stress states.

The "stress_stressor_match" boolean marks facilities in water-stressed
regions — the politically salient subset. This is the column the v0
dashboard's "show me the worst" toggle filters on.

Inputs
------
data/processed/us_dc_with_water.csv
    1,575 rows with est_mw, est_liters_per_day, climate_adj.

data/external/wri_aqueduct/us_state_stress.csv
    51 rows (50 states + DC) with bws_score, bws_category.

Outputs
-------
data/processed/us_dc_with_stress.csv
    Same 1,575 rows plus:
      - bws_score (float) : 0-5 WRI BWS for the facility's state.
      - bws_category (string) : WRI category (Low / Low-Medium / Medium-High / High / Extremely High).
      - stress_stressor_match (bool) : True when category is High or Extremely High.

The script is idempotent.

Author: Water Stress Watch v0 (Hiroaki Oshima)
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_CSV = PROJECT_ROOT / "data" / "processed" / "us_dc_with_water.csv"
WRI_CSV = PROJECT_ROOT / "data" / "external" / "wri_aqueduct" / "us_state_stress.csv"
OUTPUT_CSV = PROJECT_ROOT / "data" / "processed" / "us_dc_with_stress.csv"

HIGH_STRESS_CATEGORIES = {"High", "Extremely High"}


def main() -> int:
    if not INPUT_CSV.exists():
        print(f"ERROR: input not found: {INPUT_CSV}", file=sys.stderr)
        print("Run src/estimate_water.py first.", file=sys.stderr)
        return 1
    if not WRI_CSV.exists():
        print(f"ERROR: WRI lookup not found: {WRI_CSV}", file=sys.stderr)
        print("Run src/build_wri_stress_lookup.py first.", file=sys.stderr)
        return 1

    df = pd.read_csv(INPUT_CSV)
    wri = pd.read_csv(WRI_CSV)
    print(f"Loaded {len(df):,} facility rows from {INPUT_CSV.relative_to(PROJECT_ROOT)}")
    print(f"Loaded {len(wri):,} state rows from {WRI_CSV.relative_to(PROJECT_ROOT)}")

    # Drop the redundant state_name/source_note/n_subregions columns from wri
    # (we keep only the columns we want to add).
    wri_join = wri[["state", "bws_score", "bws_category"]].copy()

    df = df.merge(wri_join, on="state", how="left")
    df["stress_stressor_match"] = df["bws_category"].isin(HIGH_STRESS_CATEGORIES)

    # ----- Console report ---------------------------------------------------
    matched = df["bws_score"].notna().sum()
    print(f"\n=== WRI stress join coverage ===")
    print(f"  matched       : {matched:,} / {len(df):,}")
    print(f"  unmatched     : {len(df) - matched:,}")
    if matched < len(df):
        print(f"  unmatched states: {df.loc[df['bws_score'].isna(), 'state'].unique()}")

    print(f"\n=== High / Extremely High stress facilities ===")
    hi = df[df["stress_stressor_match"]]
    print(f"  count         : {len(hi):,}")
    print(f"  est L/day     : {hi['est_liters_per_day'].sum() / 1e9:.3f} billion")
    print(f"  est MW        : {hi['est_mw'].sum():,.0f}")

    print(f"\n=== 'Double jeopardy': top 5 states by facilities * est water/day ===")
    by_state = (
        df.dropna(subset=["est_liters_per_day"])
        .groupby("state")
        .agg(
            facilities=("dc_id", "count"),
            total_mw=("est_mw", "sum"),
            total_lpd=("est_liters_per_day", "sum"),
            bws_score=("bws_score", "first"),
            bws_category=("bws_category", "first"),
        )
    )
    by_state["facilities_x_lpd_millions"] = (
        by_state["facilities"] * by_state["total_lpd"] / 1e6
    )
    print(
        by_state.sort_values("facilities_x_lpd_millions", ascending=False)
        .head(5)
        .to_string()
    )

    print(f"\n=== Arizona case study preview (Week 3 deep-dive target) ===")
    az = df[df["state"] == "AZ"]
    print(f"  facilities    : {len(az):,}")
    print(f"  total est MW  : {az['est_mw'].sum():,.0f}")
    print(f"  total L/day   : {az['est_liters_per_day'].sum() / 1e6:,.1f} million L/day")
    print(f"  total L/year  : {az['est_liters_per_day'].sum() * 365 / 1e9:,.2f} billion L/year")
    if not az.empty:
        print(f"  BWS category  : {az['bws_category'].iloc[0]} ({az['bws_score'].iloc[0]})")
        print(f"  top 3 operators (by est L/day):")
        top_op = (
            az.groupby("provider")
            .agg(fac=("dc_id", "count"), lpd=("est_liters_per_day", "sum"))
            .sort_values("lpd", ascending=False)
            .head(3)
        )
        print(top_op.to_string())

    # ----- Write output -----------------------------------------------------
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nWrote {len(df):,} rows to {OUTPUT_CSV.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
