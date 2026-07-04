"""
build_v1_features.py — Build the v1 inference feature matrix for ML scoring.

Takes the v0 inference table (1,575 rows) and adds the features the v1 XGBoost
model needs to predict per-facility WUE.

Inputs
------
data/processed/us_dc_with_stress.csv
    1,575 rows × 25 columns. v0 inference table (Week 2 deliverable).

Outputs
-------
data/processed/v1_inference_features.csv
    Same 1,575 rows, plus 10-15 added feature columns:
      - operator_class                (str) : one of the v0 heuristic classes
      - is_hyperscaler_self           (bool): one-hot
      - is_colocation_major           (bool): one-hot
      - is_colocation_secondary       (bool): one-hot
      - is_cable_telecom              (bool): one-hot
      - is_edge_micro                 (bool): one-hot
      - is_cdn_isp                    (bool): one-hot
      - is_enterprise_self            (bool): one-hot
      - is_disclosed_mw               (bool): True if est_mw came from disclosure
      - lat_lon_grid_cell             (str)  : coarse 1°×1° grid ID, e.g. "37N-122W"
      - lat_lon_grid_id               (int)  : integer encoding of the above
      - is_hawaii_alaska              (bool) : edge case flag (Hawaii/Alaska)
      - is_water_stressed_state       (bool) : True when state is High or Extremely-High
                                                (this is the v0 stress_stressor_match
                                                 column already; copied for v1 clarity)

The v0 columns are preserved unchanged. The v1 model can use the v0 physics
columns (est_mw, est_liters_per_day, climate_adj) as baselines to compare against.

Methodology
-----------
The v0 → v1 handoff (locked decision 10) specifies the v1 inference formula:
    v1_water_lpd = v0_est_mw × 1000 × 24 × 0.7 × v1_predicted_wue × climate_adj

So at inference time the model predicts WUE (L/kWh), not water L/day. The
features here are what goes into the model. The wet_bulb_c and bws_score are
already in the v0 table — the model uses them as climate / stress signals.

The lat_lon_grid_cell is a coarse regional effect (1°×1° grid → ~100km).
It lets the model learn "this region tends to be dry" without using lat/lon
as continuous inputs (which would cause overfitting at edges).

is_water_stressed_state is a copy of v0's stress_stressor_match, included
for v1 clarity. The model can use it but it should NOT be the dominant feature
(it's the same signal as bws_score, just binarized).

The script is idempotent: re-running produces the same output.

Author: Water Stress Watch v1 (Hiroaki Oshima)
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Import the operator classifier from the v0 power estimation module so the
# v1 feature engineering reuses the same curated dictionary.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from estimate_power import classify_provider, CLASS_DEFAULT_MW  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_CSV = PROJECT_ROOT / "data" / "processed" / "us_dc_with_stress.csv"
OUTPUT_CSV = PROJECT_ROOT / "data" / "processed" / "v1_inference_features.csv"


# Grid cell size in degrees. 1° × 1° ≈ 100 km at the equator.
GRID_SIZE_DEG = 1.0

# Operator classes that become one-hot flags.
ONE_HOT_CLASSES = [
    "hyperscaler_self",
    "colocation_major",
    "colocation_secondary",
    "cable_telecom",
    "edge_micro",
    "cdn_isp",
    "enterprise_self",
]


def lat_lon_to_grid_cell(lat: float, lon: float) -> str:
    """Convert lat/lon to a coarse 1°×1° grid cell ID.

    Examples:
        (37.42, -122.08) -> "37N-122W"
        (-23.55, -46.63) -> "23S-46W"
    """
    if pd.isna(lat) or pd.isna(lon):
        return "unknown"
    # Snap to grid origin.
    lat_snapped = int(np.floor(abs(float(lat)) / GRID_SIZE_DEG) * GRID_SIZE_DEG)
    lon_snapped = int(np.floor(abs(float(lon)) / GRID_SIZE_DEG) * GRID_SIZE_DEG)
    lat_hem = "N" if float(lat) >= 0 else "S"
    lon_hem = "E" if float(lon) >= 0 else "W"
    return f"{lat_snapped:02d}{lat_hem}-{lon_snapped:03d}{lon_hem}"


def main() -> int:
    if not INPUT_CSV.exists():
        print(f"ERROR: input not found: {INPUT_CSV}", file=sys.stderr)
        print("Run src/join_water_stress.py first.", file=sys.stderr)
        return 1

    df = pd.read_csv(INPUT_CSV)
    print(f"Loaded {len(df):,} rows from {INPUT_CSV.relative_to(PROJECT_ROOT)}")

    # ----- Operator classification (one-hots) --------------------------------
    # Use the existing v0 classifier. It returns (class, matched_substring).
    # The mw_source column already encodes this — but we re-classify here so
    # the v1 script is independent of mw_source formatting changes.
    print("\n=== Operator classification ===")
    classification = df["provider"].apply(classify_provider)
    df["operator_class"] = classification.apply(lambda t: t[0])
    print(f"  class distribution:")
    print(f"  {df['operator_class'].value_counts().to_string()}")

    for cls in ONE_HOT_CLASSES:
        col = f"is_{cls}"
        df[col] = (df["operator_class"] == cls)

    df["is_disclosed_mw"] = (df["mw_source"] == "disclosed")

    # ----- Geographic grid cell ---------------------------------------------
    print("\n=== Geographic grid cells ===")
    df["lat_lon_grid_cell"] = [
        lat_lon_to_grid_cell(lat, lon) for lat, lon in zip(df["latitude"], df["longitude"])
    ]
    n_unique = df["lat_lon_grid_cell"].nunique()
    print(f"  unique grid cells: {n_unique}")
    # Encode the cell as a category (so the model can use it as a feature).
    df["lat_lon_grid_id"] = df["lat_lon_grid_cell"].astype("category").cat.codes

    # ----- Edge case: Hawaii / Alaska ---------------------------------------
    df["is_hawaii_alaska"] = df["state"].isin(["HI", "AK"])

    # ----- Water stress flag (copy for v1 clarity) --------------------------
    df["is_water_stressed_state"] = df["stress_stressor_match"].astype(bool)

    # ----- Report the v1 feature summary ------------------------------------
    print("\n=== v1 feature columns added ===")
    new_cols = [
        "operator_class",
        *[f"is_{cls}" for cls in ONE_HOT_CLASSES],
        "is_disclosed_mw",
        "lat_lon_grid_cell",
        "lat_lon_grid_id",
        "is_hawaii_alaska",
        "is_water_stressed_state",
    ]
    for c in new_cols:
        if df[c].dtype == bool:
            print(f"  {c:30s} : True={int(df[c].sum()):,} False={int((~df[c]).sum()):,}")
        else:
            n_unique = df[c].nunique()
            print(f"  {c:30s} : {df[c].dtype} unique={n_unique}")

    print(f"\n  Total columns: {len(df.columns)} (was 25 in v0)")
    print(f"  Added: {len(new_cols)} v1 features")

    # ----- Sanity check: WUE-default baseline can be reproduced --------------
    # The v0 physics formula:
    #   water_lpd = est_mw * 1000 * 24 * 0.7 * 1.8 * 0.7 * climate_adj
    # The v1 inference formula (per handoff decision 10):
    #   v1_water_lpd = v0_est_mw * 1000 * 24 * 0.7 * v1_predicted_wue * climate_adj
    # If v1_predicted_wue == 1.8 * 0.7 = 1.26 (the v0 midpoint), v1 should
    # match v0 exactly. This is the floor the v1 model must beat.
    print("\n=== Baseline check: v0 WUE constant ===")
    if "wue_default" in df.columns:
        implied_wue = (df["est_liters_per_day"] / (df["est_mw"] * 1000 * 24 * 0.7 * df["climate_adj"]))
        print(f"  mean implied WUE from v0 = {implied_wue.mean():.3f} L/kWh")
        print(f"  (this is WUE_DEFAULT * COOLING_PENALTY = 1.8 * 0.7 = 1.26)")
        print(f"  v1 model must beat this floor.")

    # ----- Write output -----------------------------------------------------
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nWrote {len(df):,} rows to {OUTPUT_CSV.relative_to(PROJECT_ROOT)}")
    print("Next: open notebooks/04_ml_training.ipynb in Colab Pro and run cells 1-13.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
