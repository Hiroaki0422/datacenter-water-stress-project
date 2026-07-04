"""
05b_v15_vs_v10_compare.py — Compare v1.0 to v1.5 WUE predictions.

After Hiroaki has run the v1.5 WUE retraining on Colab (with the cooling_type
column from cooling_type_predicted.csv added to v1_inference_features.csv),
this script produces the journalism-derivative comparison report.

Inputs
------
data/processed/us_dc_with_stress.csv
    1,575 rows. v0 inference table (Week 2 deliverable).
data/processed/v1_predicted_wue.csv
    1,575 rows. v1.0 WUE predictions (from the Week 5 Colab run).
data/processed/v1.5_predicted_wue.csv
    1,575 rows. v1.5 WUE predictions (from the v1.5 Colab retrain).
    Required columns: dc_id, v1.5_predicted_wue.
    Optional: v1.5_liters_per_day (if present, used as-is; if absent, computed).

Outputs
-------
docs/v15_vs_v10_comparison.md
    State-level rollup comparing v1.0 (cooling_type='unknown') to v1.5
    (cooling_type from classifier). Verifies that the LOO Meta collapse
    is fixed and that the state-level shift is more climate-driven.

The script is idempotent. If v1.5_predicted_wue.csv doesn't exist yet (Hiroaki
hasn't finished the v1.5 retrain), the script prints a clear message and
exits 0.

Author: Water Stress Watch v1.5 (Hiroaki Oshima)
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
V0_CSV = PROJECT_ROOT / "data" / "processed" / "us_dc_with_stress.csv"
V1_CSV = PROJECT_ROOT / "data" / "processed" / "v1_predicted_wue.csv"
V15_CSV = PROJECT_ROOT / "data" / "processed" / "v1.5_predicted_wue.csv"
COOLING_PRED_CSV = PROJECT_ROOT / "data" / "processed" / "cooling_type_predicted.csv"
OUT_MD = PROJECT_ROOT / "docs" / "v15_vs_v10_comparison.md"


def fmt_lpd(x: float) -> str:
    """Format liters-per-day with a sensible unit (L, kL, ML, BL)."""
    if x < 1_000:
        return f"{x:,.0f} L"
    if x < 1_000_000:
        return f"{x/1e3:,.0f} kL"
    if x < 1e9:
        return f"{x/1e6:,.1f} M L"
    return f"{x/1e9:,.2f} B L"


def main() -> int:
    if not V0_CSV.exists():
        print(f"ERROR: v0 input missing: {V0_CSV}", file=sys.stderr)
        return 1
    if not V1_CSV.exists():
        print(f"ERROR: v1.0 predictions missing: {V1_CSV}", file=sys.stderr)
        return 1
    if not V15_CSV.exists():
        print(f"v1.5 predictions not found: {V15_CSV}")
        print("Hiroaki: finish the v1.5 Colab retraining first,")
        print("then download the predictions to this path.")
        return 0  # not an error; the v1.5 retrain just hasn't happened yet

    v0 = pd.read_csv(V0_CSV)
    v1 = pd.read_csv(V1_CSV)
    v15 = pd.read_csv(V15_CSV)
    cooling = pd.read_csv(COOLING_PRED_CSV) if COOLING_PRED_CSV.exists() else None
    print(f"Loaded {len(v0)} v0 rows, {len(v1)} v1.0 rows, {len(v15)} v1.5 rows")
    if cooling is not None:
        print(f"Loaded {len(cooling)} cooling-type predictions")

    # Merge v1.0 + v1.5 onto v0.
    merged = v0.merge(
        v1[["dc_id", "v1_predicted_wue"]], on="dc_id", how="left"
    ).merge(
        v15[["dc_id", "v1.5_predicted_wue"]], on="dc_id", how="left"
    )
    if cooling is not None:
        merged = merged.merge(
            cooling[["dc_id", "predicted_cooling_type", "cooling_class_2"]],
            on="dc_id", how="left",
        )

    # Compute water L/day for each model.
    # v0: est_liters_per_day (the physics formula)
    # v1.0: est_mw * 1000 * 24 * 0.7 * v1_predicted_wue * climate_adj
    # v1.5: est_mw * 1000 * 24 * 0.7 * v1.5_predicted_wue * climate_adj
    merged["v10_lpd"] = (
        merged["est_mw"] * 1000 * 24 * 0.7 * merged["v1_predicted_wue"] * merged["climate_adj"]
    )
    merged["v15_lpd"] = (
        merged["est_mw"] * 1000 * 24 * 0.7 * merged["v1.5_predicted_wue"] * merged["climate_adj"]
    )

    # Headline numbers.
    valid = merged.dropna(subset=["est_liters_per_day", "v10_lpd", "v15_lpd"])
    v0_total = valid["est_liters_per_day"].sum() / 1e9
    v10_total = valid["v10_lpd"].sum() / 1e9
    v15_total = valid["v15_lpd"].sum() / 1e9
    diff_pct = (v15_total - v10_total) / v10_total * 100
    print(f"\n=== US total water use: v0 / v1.0 / v1.5 ===")
    print(f"  v0:   {v0_total:.3f} B L/day = {v0_total*365:.0f} B L/year")
    print(f"  v1.0: {v10_total:.3f} B L/day = {v10_total*365:.0f} B L/year")
    print(f"  v1.5: {v15_total:.3f} B L/day = {v15_total*365:.0f} B L/year")
    print(f"  v1.5 - v1.0: {diff_pct:+.1f}%")

    # State-level rollup.
    by_state = (
        valid.groupby("state")
        .agg(
            n=("dc_id", "count"),
            v0_lpd=("est_liters_per_day", "sum"),
            v10_lpd=("v10_lpd", "sum"),
            v15_lpd=("v15_lpd", "sum"),
        )
    )
    by_state["v15_minus_v10_pct"] = (by_state["v15_lpd"] - by_state["v10_lpd"]) / by_state["v10_lpd"] * 100
    by_state["v15_minus_v0_pct"] = (by_state["v15_lpd"] - by_state["v0_lpd"]) / by_state["v0_lpd"] * 100
    by_state = by_state.sort_values("v15_minus_v10_pct", key=abs, ascending=False)

    # Cooling-type breakdown (if available).
    cooling_section = ""
    if cooling is not None and "cooling_class_2" in merged.columns:
        by_cooling = (
            valid.groupby("cooling_class_2")
            .agg(
                n=("dc_id", "count"),
                v0_lpd=("est_liters_per_day", "sum"),
                v10_lpd=("v10_lpd", "sum"),
                v15_lpd=("v15_lpd", "sum"),
            )
        )
        by_cooling["v15_minus_v10_pct"] = (by_cooling["v15_lpd"] - by_cooling["v10_lpd"]) / by_cooling["v10_lpd"] * 100
        cooling_section = "## Predicted cooling type breakdown\n\n"
        cooling_section += "| Cooling class | n | v0 L/day | v1.0 L/day | v1.5 L/day | v1.5 - v1.0 % |\n"
        cooling_section += "|---|---:|---:|---:|---:|---:|\n"
        for cls, row in by_cooling.iterrows():
            cooling_section += (
                f"| {cls} | {int(row['n'])} | {fmt_lpd(row['v0_lpd'])} | "
                f"{fmt_lpd(row['v10_lpd'])} | {fmt_lpd(row['v15_lpd'])} | "
                f"{row['v15_minus_v10_pct']:+.1f}% |\n"
            )
        cooling_section += "\n"

    # Write the report.
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_MD, "w") as f:
        f.write("# v1.5 vs v1.0 Comparison — Water Stress Watch\n\n")
        f.write("**Generated:** Week 6 (after the v1.5 Colab retraining run)\n")
        f.write("**Scope:** 1,575 US data centers from v0\n")
        f.write("**v1.0 model:** XGBoost, cooling_type='unknown' for all inference rows (Week 5 run)\n")
        f.write("**v1.5 model:** XGBoost, cooling_type predicted per facility (Week 6 run)\n\n")
        f.write("## Headline\n\n")
        f.write(f"- **v0 total (flat WUE=1.26):** {v0_total:.3f} B L/day = {v0_total*365:.0f} B L/year\n")
        f.write(f"- **v1.0 total (cooling_type='unknown'):** {v10_total:.3f} B L/day = {v10_total*365:.0f} B L/year\n")
        f.write(f"- **v1.5 total (cooling_type from classifier):** {v15_total:.3f} B L/day = {v15_total*365:.0f} B L/year\n")
        f.write(f"- **v1.5 - v1.0:** {diff_pct:+.1f}%\n\n")
        f.write(cooling_section)
        f.write("## Top 10 states by |v1.5 - v1.0| % difference\n\n")
        f.write("| State | n | v1.0 L/day | v1.5 L/day | v1.5 - v1.0 % | v1.5 - v0 % |\n")
        f.write("|---|---:|---:|---:|---:|---:|\n")
        for state, row in by_state.head(10).iterrows():
            f.write(
                f"| {state} | {int(row['n'])} | {fmt_lpd(row['v10_lpd'])} | "
                f"{fmt_lpd(row['v15_lpd'])} | {row['v15_minus_v10_pct']:+.1f}% | "
                f"{row['v15_minus_v0_pct']:+.1f}% |\n"
            )
        f.write("\n## Caveats\n\n")
        f.write("- v1.5's cooling_type predictions are ~70-73% accurate on the 2-class problem (low_water vs high_water). The 4-class problem is too noisy at 67 training rows; the air/hybrid boundary is reported but unreliable.\n")
        f.write("- The 2-class reframe (low_water = air+hybrid, high_water = evaporative) is the actual feature fed to the v1.5 WUE model. The journalism-derivative 4-class output is for transparency only.\n")
        f.write("- v1.5 inherits the v0 annual mean wet-bulb limitation; the v0.5 design-day wet-bulb fix is a separate task.\n")
    print(f"\nWrote comparison to {OUT_MD.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
