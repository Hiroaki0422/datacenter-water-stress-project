"""
v1_output_schema.py — Schema for the v1 model output.

Documents the columns the v1 model produces when applied to all 1,575 v0
facilities. The model is trained in `notebooks/04_ml_training.ipynb` on
Colab Pro; the output is a per-facility DataFrame that is merged back into
the v0 dataset.

Output columns (one row per facility, 1,575 rows total):

  Identifier columns (passthrough from v0)
  ----------------------------------------
    dc_id                       str    : v0 stable identifier (FK to us_dc_with_stress.csv)
    name                        str    : facility name
    provider                    str    : operator name
    state                       str    : 2-letter state code
    latitude, longitude         float  : facility coordinates

  v0 baseline (passthrough; the v1 model must beat this on accuracy)
  ------------------------------------------------------------------
    est_mw                      float  : v0 best-estimate nameplate MW
    est_liters_per_day          float  : v0 physics estimate (the floor)
    wet_bulb_c                  float  : v0 annual mean wet-bulb
    climate_adj                 float  : v0 climate adjustment multiplier
    bws_score, bws_category     float/str : WRI Aqueduct state stress (analysis only)

  v1 ML output (added by the trained model)
  -----------------------------------------
    v1_predicted_wue            float  : v1 XGBoost predicted WUE (L/kWh)
    v1_liters_per_day           float  : est_mw * 1000 * 24 * 0.7 * v1_wue * climate_adj
    v1_minus_v0_pct             float  : (v1_lpd - est_liters_per_day) / est_liters_per_day * 100
                                           (the journalism headline — "v1 says X% different from v0")

  v1 uncertainty (optional; the v1 model in Week 4 outputs a point estimate
  only. Bootstrap or quantile-regression to add these is in the v1 backlog.)
  ------------------------------------------------------------------
    v1_liters_per_day_low       float  : 10th percentile (planned; not in Week 4)
    v1_liters_per_day_high      float  : 90th percentile (planned; not in Week 4)
    v1_uncertainty_band_width   float  : high - low (planned; not in Week 4)

How to merge v1 outputs back into v0
------------------------------------
After the Colab run, the v1 predictions CSV is in
`data/processed/v1_predicted_wue.csv`. Merge it into the v0 inference table
with:

    import pandas as pd
    v0 = pd.read_csv("data/processed/us_dc_with_stress.csv")
    v1 = pd.read_csv("data/processed/v1_predicted_wue.csv")
    merged = v0.merge(
        v1[["dc_id", "v1_predicted_wue", "v1_liters_per_day", "v1_minus_v0_pct"]],
        on="dc_id", how="left",
    )

Author: Water Stress Watch v1 (Hiroaki Oshima)
"""

# The 16 columns the v1 model output is expected to have. Kept as a list so
# it can be used as a pd.DataFrame column ordering at write time.
V1_OUTPUT_COLUMNS: list[str] = [
    # Identifiers
    "dc_id",
    "name",
    "provider",
    "state",
    "latitude",
    "longitude",
    # v0 baseline
    "est_mw",
    "est_liters_per_day",
    "wet_bulb_c",
    "climate_adj",
    "bws_score",
    "bws_category",
    # v1 ML output
    "v1_predicted_wue",
    "v1_liters_per_day",
    "v1_minus_v0_pct",
    # Optional uncertainty (planned, not in Week 4 output)
    "v1_liters_per_day_low",
    "v1_liters_per_day_high",
    "v1_uncertainty_band_width",
]


def print_schema() -> None:
    """Print the v1 output schema as a readable reference."""
    print("v1 output schema (one row per facility, 1,575 rows total):")
    print("=" * 70)
    for col in V1_OUTPUT_COLUMNS:
        # Mark the columns that the v1 ML model adds (vs v0 passthrough).
        if col.startswith("v1_"):
            print(f"  + {col:30s}  (v1 ML output)")
        else:
            print(f"    {col:30s}  (v0 passthrough)")
    print()
    print("v1 inference formula (from handoff decision 10):")
    print("    v1_lpd = v0_est_mw * 1000 * 24 * 0.7 * v1_wue * climate_adj")
    print()
    print("v1 must beat v0 (est_liters_per_day) on the v0.5 design-day inputs.")
    print("See docs/methodology.md Section 16 for full methodology.")


if __name__ == "__main__":
    print_schema()
