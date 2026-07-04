"""
05_v1_vs_v0_compare.py — Compare v0 physics estimates to v1 ML predictions.

This is a sanity-check script, not the model itself. It runs *after* Hiroaki
has finished the Colab training run and downloaded the v1 outputs to
data/processed/v1_predicted_wue.csv.

Inputs
------
data/processed/us_dc_with_stress.csv
    1,575 rows. v0 inference table (Week 2 deliverable).
data/processed/v1_predicted_wue.csv
    1,575 rows. v1 model output (Colab Pro training run output).
    Required columns: dc_id, v1_predicted_wue.
    Optional: v1_liters_per_day (if present, used as-is; if absent, computed
    here from v1_predicted_wue + est_mw + climate_adj using the v0.5 formula
    est_mw * 1000 * 24 * 0.7 * v1_wue * climate_adj).

Outputs
-------
docs/v1_vs_v0_comparison.md
    A short markdown report of v0 vs v1 differences, with state-level
    rollups and a headline summary that journalists can lift directly.

The script is idempotent. If v1_predicted_wue.csv doesn't exist yet (Hiroaki
hasn't finished training), the script prints a clear message and exits 0.

Author: Water Stress Watch v1 (Hiroaki Oshima)
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
V0_CSV = PROJECT_ROOT / "data" / "processed" / "us_dc_with_stress.csv"
V1_CSV = PROJECT_ROOT / "data" / "processed" / "v1_predicted_wue.csv"
OUT_MD = PROJECT_ROOT / "docs" / "v1_vs_v0_comparison.md"


def main() -> int:
    if not V0_CSV.exists():
        print(f"ERROR: v0 input missing: {V0_CSV}", file=sys.stderr)
        return 1
    if not V1_CSV.exists():
        print(f"v1 output not found: {V1_CSV}")
        print("Hiroaki: finish the Colab Pro training run first,")
        print("then download the predictions to this path.")
        return 0  # not an error; the v1 model just hasn't been trained yet

    v0 = pd.read_csv(V0_CSV)
    v1 = pd.read_csv(V1_CSV)
    print(f"Loaded {len(v0)} v0 rows, {len(v1)} v1 rows")

    # Merge on dc_id
    cols_to_merge = ["dc_id", "v1_predicted_wue"]
    if "v1_liters_per_day" in v1.columns:
        cols_to_merge.append("v1_liters_per_day")
    merged = v0.merge(v1[cols_to_merge], on="dc_id", how="left")

    # If v1_liters_per_day is missing, compute it from the v0.5 inference formula.
    if "v1_liters_per_day" not in merged.columns:
        merged["v1_liters_per_day"] = (
            merged["est_mw"] * 1000 * 24 * 0.7 * merged["v1_predicted_wue"] * merged["climate_adj"]
        )
        print("Note: v1_liters_per_day not in CSV; computed from v1_predicted_wue + v0 inference inputs.")

    merged["v1_minus_v0_pct"] = (
        (merged["v1_liters_per_day"] - merged["est_liters_per_day"])
        / merged["est_liters_per_day"] * 100
    )

    # Headline numbers
    valid = merged.dropna(subset=["v1_liters_per_day", "est_liters_per_day"])
    v0_total = valid["est_liters_per_day"].sum() / 1e9
    v1_total = valid["v1_liters_per_day"].sum() / 1e9
    diff_pct = (v1_total - v0_total) / v0_total * 100
    print(f"\n=== US total water use: v0 vs v1 ===")
    print(f"  v0: {v0_total:.3f} B L/day")
    print(f"  v1: {v1_total:.3f} B L/day")
    print(f"  diff: {diff_pct:+.1f}%")

    # State-level rollup
    by_state = (
        valid.groupby("state")
        .agg(
            n=("dc_id", "count"),
            v0_lpd=("est_liters_per_day", "sum"),
            v1_lpd=("v1_liters_per_day", "sum"),
        )
    )
    by_state["v1_minus_v0_pct"] = (by_state["v1_lpd"] - by_state["v0_lpd"]) / by_state["v0_lpd"] * 100
    by_state = by_state.sort_values("v1_minus_v0_pct", key=abs, ascending=False)

    def fmt_lpd(x: float) -> str:
        """Format liters-per-day with a sensible unit (L, kL, ML, BL)."""
        if x < 1_000:
            return f"{x:,.0f} L"
        if x < 1_000_000:
            return f"{x/1e3:,.0f} kL"
        if x < 1e9:
            return f"{x/1e6:,.1f} M L"
        return f"{x/1e9:,.2f} B L"

    # Write the comparison report
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_MD, "w") as f:
        f.write(f"# v0 vs v1 Comparison — Water Stress Watch\n\n")
        f.write(f"**Generated:** Week 5+ (after the v1 Colab training run)\n")
        f.write(f"**Scope:** 1,575 US data centers from v0\n")
        f.write(f"**v1 model:** XGBoost, default hyperparameters, 5-fold k-fold + leave-one-operator-out\n")
        f.write(f"**v1 training set:** 42 disclosed WUE values (Google 4 + Microsoft 9 + Meta 16 + AWS 13)\n\n")
        f.write(f"## Headline\n\n")
        f.write(f"- **v0 total (flat WUE=1.26):** {v0_total:.3f} B L/day = {v0_total*365:.0f} B L/year\n")
        f.write(f"- **v1 total (ML-corrected):** {v1_total:.3f} B L/day = {v1_total*365:.0f} B L/year\n")
        f.write(f"- **Difference:** {diff_pct:+.1f}%  (v1 is {abs(diff_pct):.0f}% {'lower' if diff_pct < 0 else 'higher'} than v0)\n\n")
        f.write(f"## Top 10 states by |v1 - v0| % difference\n\n")
        f.write("| State | n | v0 L/day | v1 L/day | v1 - v0 % |\n")
        f.write("|---|---:|---:|---:|---:|\n")
        for state, row in by_state.head(10).iterrows():
            f.write(f"| {state} | {int(row['n'])} | {fmt_lpd(row['v0_lpd'])} | "
                    f"{fmt_lpd(row['v1_lpd'])} | {row['v1_minus_v0_pct']:+.1f}% |\n")
        f.write(f"\n## Caveats\n\n")
        f.write(f"- v1 is a point estimate; uncertainty quantification is in the v1 backlog.\n")
        f.write(f"- v1 was trained on 42 disclosed rows (Google fleet + Microsoft/Meta/AWS). The training set is small; treat per-facility v1 estimates with appropriate skepticism.\n")
        f.write(f"- v0's annual mean wet-bulb is a known v0 limitation; v1 inherits this until the v0.5 design-day fix.\n")
        f.write(f"- The 5-fold cross-validation mean RMSE is 0.276 L/kWh (vs v0 baseline 0.755); the leave-one-operator-out test shows a Meta collapse (R² = -717), meaning v1 overfits to Meta's dry-cooling signature.\n")
    print(f"\nWrote comparison to {OUT_MD.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
