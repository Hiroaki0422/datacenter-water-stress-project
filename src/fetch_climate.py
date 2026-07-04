"""
fetch_climate.py — Pull annual mean wet-bulb temperature from Open-Meteo.

For every facility in us_dc_with_mw.csv, fetch daily wet-bulb temperatures
for 2023 from the Open-Meteo Historical API, then average them to get an
annual mean. Add a `wet_bulb_c` column and a `climate_adj` column to the
table.

Why wet-bulb (not dry-bulb): Data center cooling is most efficient when
outdoor wet-bulb temperature is low — this is why Microsoft puts DCs in
cold places like Quincy WA or Dublin. WUE scales with wet-bulb. Open-Meteo
provides it directly via `wet_bulb_temperature_2m_mean`.

Open-Meteo endpoint
-------------------
GET https://archive-api.open-meteo.com/v1/archive
    ?latitude={lat}&longitude={lon}
    &start_date=2023-01-01&end_date=2023-12-31
    &daily=wet_bulb_temperature_2m_mean
    &timezone=UTC

Multiple lat/lon pairs are accepted as comma-separated lists, so we batch
~100 facilities per request. 1,575 / 100 = ~16 requests total.

Climate adjustment
------------------
climate_adj = 1.0 + 0.03 * max(0, wet_bulb_c - 15)
  - 15 C wet-bulb: 1.0 (baseline)
  - 25 C wet-bulb: 1.30 (+30% water)
  - 30 C wet-bulb: 1.45 (+45% water)
  - < 15 C: clamped to 1.0 (cold climates don't get a discount in v0)

Inputs
------
data/processed/us_dc_with_mw.csv
    1,575 rows with lat/lon (from estimate_power.py).

Outputs
-------
data/processed/us_dc_with_climate.csv
    Same 1,575 rows plus:
      - wet_bulb_c (float) : annual mean wet-bulb temperature (C).
      - climate_adj (float): 1.0 + 0.03 * max(0, wet_bulb_c - 15).

Cache
-----
data/external/open_meteo/batch_{i:03d}.json
    Per-batch raw Open-Meteo response, so re-runs are instant.

The script is idempotent: re-running with a populated cache makes zero
network calls.

Author: Water Stress Watch v0 (Hiroaki Oshima)
"""

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_CSV = PROJECT_ROOT / "data" / "processed" / "us_dc_with_mw.csv"
OUTPUT_CSV = PROJECT_ROOT / "data" / "processed" / "us_dc_with_climate.csv"
CACHE_DIR = PROJECT_ROOT / "data" / "external" / "open_meteo"

OPEN_METEO_URL = "https://archive-api.open-meteo.com/v1/archive"
START_DATE = "2023-01-01"
END_DATE = "2023-12-31"
BATCH_SIZE = 100  # ~16 requests for 1,575 facilities
REQUEST_TIMEOUT = 60  # seconds
MAX_RETRIES = 6
INTER_REQUEST_SLEEP_S = 6  # Open-Meteo is rate-limited; ~10 req/min sustained
RATE_LIMIT_BACKOFF_S = 30  # extra sleep when we hit a 429


def fetch_batch(
    lats: list[float], lons: list[float], cache_path: Path
) -> list[dict] | None:
    """Fetch one batch of facilities from Open-Meteo, with cache + retries.

    Returns the parsed list of per-location dicts, or None on persistent failure.
    """
    if cache_path.exists():
        return json.loads(cache_path.read_text())

    params = {
        "latitude": ",".join(str(x) for x in lats),
        "longitude": ",".join(str(x) for x in lons),
        "start_date": START_DATE,
        "end_date": END_DATE,
        "daily": "wet_bulb_temperature_2m_mean",
        "timezone": "UTC",
    }
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = requests.get(OPEN_METEO_URL, params=params, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            payload = r.json()
            break
        except requests.HTTPError as e:
            status = getattr(r, "status_code", None)
            print(f"  ! attempt {attempt} HTTP {status}: {e}", file=sys.stderr)
            if status == 429:
                # Rate limited — back off substantially.
                time.sleep(RATE_LIMIT_BACKOFF_S)
            else:
                time.sleep(2 ** attempt)
        except (requests.RequestException, json.JSONDecodeError, ValueError) as e:
            print(f"  ! attempt {attempt} failed: {e}", file=sys.stderr)
            time.sleep(2 ** attempt)
    else:
        return None

    # Open-Meteo returns a list (one element per location) when multiple
    # coordinates are requested. Single-coord calls return a dict. Normalise.
    if isinstance(payload, dict):
        payload = [payload]

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(payload))
    return payload


def compute_annual_mean_wet_bulb(per_location: dict) -> float | None:
    """Pull the daily series and return the mean, ignoring nulls."""
    daily = per_location.get("daily") or {}
    series = daily.get("wet_bulb_temperature_2m_mean") or []
    vals = [v for v in series if v is not None]
    if not vals:
        return None
    return float(np.mean(vals))


def climate_adj_from_wb(wb_c: float | None) -> float:
    """1.0 + 0.03 * max(0, wb - 15). Clamp to >= 1.0."""
    if wb_c is None or (isinstance(wb_c, float) and math.isnan(wb_c)):
        return np.nan
    return 1.0 + 0.03 * max(0.0, wb_c - 15.0)


def main() -> int:
    if not INPUT_CSV.exists():
        print(f"ERROR: input not found: {INPUT_CSV}", file=sys.stderr)
        print("Run src/estimate_power.py first.", file=sys.stderr)
        return 1

    df = pd.read_csv(INPUT_CSV)
    print(f"Loaded {len(df):,} rows from {INPUT_CSV.relative_to(PROJECT_ROOT)}")

    # Allocate wet_bulb_c and climate_adj.
    wb = np.full(len(df), np.nan, dtype=float)
    failed_indices: list[int] = []
    network_calls = 0
    cache_hits = 0

    n = len(df)
    for batch_start in range(0, n, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, n)
        batch_df = df.iloc[batch_start:batch_end]
        lats = batch_df["latitude"].tolist()
        lons = batch_df["longitude"].tolist()
        cache_path = CACHE_DIR / f"batch_{batch_start // BATCH_SIZE:03d}.json"

        if cache_path.exists():
            cache_hits += 1
        else:
            network_calls += 1
            print(
                f"  batch {batch_start // BATCH_SIZE:03d} "
                f"(rows {batch_start}-{batch_end - 1}): "
                f"{len(lats)} facilities ..."
            )
            # Pace network calls so we don't blow past the free-tier rate limit.
            if batch_start > 0 and cache_hits == 0 and network_calls > 1:
                time.sleep(INTER_REQUEST_SLEEP_S)

        payload = fetch_batch(lats, lons, cache_path)
        if payload is None:
            print(
                f"  ! batch {batch_start // BATCH_SIZE:03d} failed permanently; "
                f"rows will be NaN.",
                file=sys.stderr,
            )
            failed_indices.extend(range(batch_start, batch_end))
            continue

        if len(payload) != len(lats):
            print(
                f"  ! batch returned {len(payload)} results for {len(lats)} requests; "
                f"using whatever came back.",
                file=sys.stderr,
            )

        for i, loc in enumerate(payload):
            target_idx = batch_start + i
            if target_idx >= n:
                break
            mean_wb = compute_annual_mean_wet_bulb(loc)
            if mean_wb is None:
                failed_indices.append(target_idx)
            else:
                wb[target_idx] = mean_wb

    df["wet_bulb_c"] = wb
    df["climate_adj"] = [climate_adj_from_wb(x) for x in wb]

    # ----- Console report ---------------------------------------------------
    valid = df["wet_bulb_c"].dropna()
    print("\n=== Annual mean wet-bulb distribution (Celsius) ===")
    print(f"  n           : {len(valid):,} / {len(df):,}")
    print(f"  min         : {valid.min():.2f}")
    print(f"  median      : {valid.median():.2f}")
    print(f"  mean        : {valid.mean():.2f}")
    print(f"  max         : {valid.max():.2f}")

    print("\n=== Climate adjustment distribution ===")
    ca = df["climate_adj"].dropna()
    print(f"  min         : {ca.min():.3f}")
    print(f"  median      : {ca.median():.3f}")
    print(f"  max         : {ca.max():.3f}")

    print("\n=== Facilities with wet_bulb_c > 25 (climate-stressed) ===")
    hot = df[df["wet_bulb_c"] > 25].sort_values("wet_bulb_c", ascending=False)
    if len(hot) == 0:
        print("  (none)")
    else:
        print(
            hot[["dc_id", "name", "state", "wet_bulb_c", "climate_adj"]]
            .head(20)
            .to_string(index=False)
        )
        print(f"  ... and {max(0, len(hot) - 20)} more")

    print("\n=== Network activity ===")
    print(f"  cache hits  : {cache_hits}")
    print(f"  network calls: {network_calls}")

    if failed_indices:
        print(
            f"\nWARNING: {len(failed_indices)} facilities could not be fetched "
            f"even after {MAX_RETRIES} retries. They will have NaN wet_bulb_c.",
            file=sys.stderr,
        )

    # ----- Write output -----------------------------------------------------
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nWrote {len(df):,} rows to {OUTPUT_CSV.relative_to(PROJECT_ROOT)}")
    print(
        f"  wet_bulb_c coverage: {df['wet_bulb_c'].notna().sum():,} / {len(df):,} "
        f"({df['wet_bulb_c'].notna().mean() * 100:.1f}%)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
