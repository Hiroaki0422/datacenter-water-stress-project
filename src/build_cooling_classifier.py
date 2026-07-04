"""
build_cooling_classifier.py — Build the v1.5 cooling-type classifier.

The v1.0 WUE model collapsed to a 1.5-feature model because v0 didn't capture
per-facility cooling type. The v1.5 fix is to predict cooling type first, then
use the prediction as a real feature in the v1.5 WUE model.

This script assembles the labeled training set for the cooling classifier:

  - 43 disclosed rows from ml_training_set.csv (Google fleet + Microsoft /
    Meta / AWS per-site, all with cooling_type from operator disclosures).
  - 24 augmented rows from public sources (Meta 2024 per-site, Google 2024
    per-site, Equinix/Digital Realty industry defaults) saved separately in
    cooling_classifier_augmented_labels.csv for transparency.

The output is data/processed/cooling_classifier_training_set.csv, with the
schema the 06_cooling_classifier.ipynb notebook expects.

The script is idempotent: re-running produces the same output.

Author: Water Stress Watch v1.5 (Hiroaki Oshima)
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SEED_CSV = PROJECT_ROOT / "data/processed/ml_training_set.csv"
# Default augmented labels file (v1, 24 rows). A v2 file (48 more rows from
# Apple/Oracle/Switch/CyrusOne/etc.) is on disk at
# cooling_classifier_augmented_labels_v2.csv but excluded by default because
# the v1 dry-run showed it doesn't improve accuracy meaningfully and adds
# noise (see docs/week_6_summary.md for the diagnostic). To opt in, change
# AUGMENTED_CSV_PATTERN to "cooling_classifier_augmented_labels*.csv".
AUGMENTED_CSV_PATTERN = "cooling_classifier_augmented_labels.csv"
INFERENCE_FEATURES_CSV = PROJECT_ROOT / "data/processed/v1_inference_features.csv"
OUTPUT_CSV = PROJECT_ROOT / "data/processed/cooling_classifier_training_set.csv"

# 3-class cooling taxonomy (locked decision for v1.5):
#   air         = outside-air economizer only (no water for cooling, just humidification)
#   hybrid      = outside-air economizer with adiabatic support on hot days
#   evaporative = cooling tower (the v0 default for hyperscalers in hot/dry climates)
#
# "water" and "immersion" are theoretically additional classes but the public
# record is too thin to train on. v1.5 maps:
#   - water-cooled chillers -> evaporative (similar WUE, similar water use)
#   - immersion cooling -> air (both are very low water use, dominated by humidification)
COOLING_CLASSES = ["air", "hybrid", "evaporative"]


def load_seed() -> pd.DataFrame:
    """Load the 43 disclosed rows from ml_training_set.csv."""
    seed = pd.read_csv(SEED_CSV)
    seed = seed.rename(columns={"operator": "provider"})
    seed["provider"] = seed["provider"].replace({"AWS": "Amazon AWS"})

    provider_to_class = {
        "Google": "hyperscaler_self",
        "Microsoft": "hyperscaler_self",
        "Meta": "hyperscaler_self",
        "Amazon AWS": "hyperscaler_self",
    }
    seed["operator_class"] = seed["provider"].map(provider_to_class).fillna("hyperscaler_self")

    return pd.DataFrame({
        "facility_name": seed["facility_name"],
        "provider": seed["provider"],
        "latitude": seed["latitude"],
        "longitude": seed["longitude"],
        "state": seed["state"],
        "operator_class": seed["operator_class"],
        "cooling_type": seed["cooling_type"],
        "source_url": seed["source_url"],
        "notes": seed["notes"],
        "is_seed": True,
    })


def load_augmented() -> pd.DataFrame:
    """Load all augmented labels (cooling_classifier_augmented_labels*.csv).

    v1 had 24 rows; v2 added 48 more. Both files are read and concatenated.
    Each file is independently quoted; the script handles embedded commas
    in the `notes` column.
    """
    augmented_paths = sorted(PROJECT_ROOT.glob(f"data/processed/{AUGMENTED_CSV_PATTERN}"))
    if not augmented_paths:
        return pd.DataFrame(columns=[
            "facility_name", "provider", "latitude", "longitude", "state",
            "operator_class", "cooling_type", "source_url", "notes", "is_seed",
        ])

    frames = []
    for path in augmented_paths:
        df = pd.read_csv(path)
        df["is_seed"] = False
        df["augmented_source"] = path.name
        frames.append(df)
    combined = pd.concat(frames, ignore_index=True)
    return combined


def attach_features(df: pd.DataFrame) -> pd.DataFrame:
    """Attach wet_bulb_c, sqft, operator_class one-hots by nearest-neighbor lookup.

    For each labeled row, find the closest facility in the v0 inference features
    table and copy its wet_bulb_c + sqft. This works for ALL labeled rows,
    including ones that aren't in v0 (we use the spatial nearest neighbor).
    """
    if not INFERENCE_FEATURES_CSV.exists():
        df = df.copy()
        df["wet_bulb_c"] = None
        df["sqft_total_space"] = None
        df["sqft_colocation_space"] = None
        return df

    v0 = pd.read_csv(INFERENCE_FEATURES_CSV)

    # Build arrays for fast nearest-neighbor lookup.
    v0_lat = v0["latitude"].values
    v0_lon = v0["longitude"].values
    v0_wb = v0["wet_bulb_c"].values
    v0_sqft_total = v0["sqft_total_space"].values
    v0_sqft_colo = v0["sqft_colocation_space"].values

    def nearest_match(row: pd.Series) -> tuple[float, float, float]:
        lat = float(row["latitude"])
        lon = float(row["longitude"])
        if pd.isna(lat) or pd.isna(lon):
            return (np.nan, np.nan, np.nan)
        dist_sq = (v0_lat - lat) ** 2 + (v0_lon - lon) ** 2
        idx = int(np.argmin(dist_sq))
        return (
            float(v0_wb[idx]) if not pd.isna(v0_wb[idx]) else np.nan,
            float(v0_sqft_total[idx]) if not pd.isna(v0_sqft_total[idx]) else np.nan,
            float(v0_sqft_colo[idx]) if not pd.isna(v0_sqft_colo[idx]) else np.nan,
        )

    df = df.copy()
    features = df.apply(nearest_match, axis=1, result_type="expand")
    df["wet_bulb_c"] = features[0]
    df["sqft_total_space"] = features[1]
    df["sqft_colocation_space"] = features[2]

    print(f"  wet_bulb_c coverage: {df['wet_bulb_c'].notna().sum()}/{len(df)}")
    print(f"  sqft_total_space coverage: {df['sqft_total_space'].notna().sum()}/{len(df)}")
    print(f"  sqft_colocation_space coverage: {df['sqft_colocation_space'].notna().sum()}/{len(df)}")

    # Fill any remaining NaN wet_bulb_c with a coarse latitude-based estimate.
    # Annual mean wet-bulb is roughly: ~ 12 - 0.2 * |lat - 35| (very rough).
    # This is only used if the spatial lookup didn't find anything.
    mask_missing = df["wet_bulb_c"].isna()
    if mask_missing.any():
        for idx in df[mask_missing].index:
            lat = df.loc[idx, "latitude"]
            if pd.notna(lat):
                df.loc[idx, "wet_bulb_c"] = max(2.0, 12.0 - 0.2 * abs(float(lat) - 35.0))
        print(f"  wet_bulb_c after coarse fallback: {df['wet_bulb_c'].notna().sum()}/{len(df)}")

    return df


def main() -> int:
    if not SEED_CSV.exists():
        print(f"ERROR: seed not found: {SEED_CSV}", file=sys.stderr)
        return 1

    print("=== Loading seed (43 disclosed rows) ===")
    seed = load_seed()
    print(f"  {len(seed)} rows from {SEED_CSV.relative_to(PROJECT_ROOT)}")
    print(f"  cooling_type: {seed['cooling_type'].value_counts().to_dict()}")
    print(f"  providers: {seed['provider'].value_counts().to_dict()}")

    print("\n=== Loading augmented labels ===")
    aug = load_augmented()
    if len(aug) > 0:
        # Report per-file counts.
        for src in aug["augmented_source"].unique():
            sub = aug[aug["augmented_source"] == src]
            print(f"  {src}: {len(sub)} rows")
        print(f"  total: {len(aug)} rows")
        print(f"  cooling_type: {aug['cooling_type'].value_counts().to_dict()}")
        print(f"  providers: {aug['provider'].value_counts().to_dict()}")

    combined = pd.concat([seed, aug], ignore_index=True)
    print(f"\n=== Combined training set: {len(combined)} rows ===")

    # Sanity: every cooling_type must be in COOLING_CLASSES.
    bad = combined[~combined["cooling_type"].isin(COOLING_CLASSES)]
    if len(bad) > 0:
        print(f"WARN: {len(bad)} rows have cooling_type not in {COOLING_CLASSES}:")
        print(bad[["facility_name", "provider", "cooling_type"]].to_string())

    # Attach wet_bulb + sqft features via spatial nearest-neighbor.
    print("\n=== Attaching features (nearest-neighbor to v0) ===")
    combined = attach_features(combined)

    print("\n=== Final class distribution ===")
    for cls in COOLING_CLASSES:
        n = (combined["cooling_type"] == cls).sum()
        print(f"  {cls:12s}: {n}")
    print(f"  TOTAL: {len(combined)}")

    # Class imbalance summary.
    print("\n=== Class proportions ===")
    print(combined["cooling_type"].value_counts(normalize=True).round(3).to_string())

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(OUTPUT_CSV, index=False)
    print(f"\nWrote {len(combined)} rows to {OUTPUT_CSV.relative_to(PROJECT_ROOT)}")
    print("\nNext: open notebooks/06_cooling_classifier.ipynb in Colab Pro.")
    print("  Cell 7 builds the feature matrix.")
    print("  Cells 8-9 train the 4-class and 2-class XGBoost cooling classifiers.")
    print("  Cell 11 predicts cooling type for all 1,575 v0 facilities.")
    print("  Cell 12 saves the predictions to Drive for download.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
