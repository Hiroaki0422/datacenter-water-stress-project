"""Build state-level water stress lookup from WRI Aqueduct 4.0 sub-national data.

Pulls the WRI Aqueduct Province/State Baseline Water Stress indicator from
the WRI Resource Watch CartoDB endpoint, filters to USA, and area-weight
aggregates to one row per US state.

Output: data/external/wri_aqueduct/us_state_stress.csv

Source: WRI Aqueduct 4.0 Country & Province Rankings
  https://www.wri.org/data/aqueduct-data
  (License: Creative Commons Attribution 4.0)
  Underlying data exposed via WRI Resource Watch:
    https://wri-rw.carto.com/tables/aqueduct_results_v01_province_v03/public
"""
import json
import urllib.request
import urllib.parse
import pandas as pd
import numpy as np
from pathlib import Path

EXT = Path('/root/project/datacenter_water_stress/data/external')
WRI_DIR = EXT / 'wri_aqueduct'
OUT = WRI_DIR / 'us_state_stress.csv'
RAW_OUT = WRI_DIR / 'aqueduct40_us_province_bws.json'

CARTO_URL = 'https://wri-rw.carto.com/api/v2/sql'

NAME_TO_CODE = {
    'Alabama':'AL','Alaska':'AK','Arizona':'AZ','Arkansas':'AR','California':'CA',
    'Colorado':'CO','Connecticut':'CT','Delaware':'DE','Florida':'FL','Georgia':'GA',
    'Hawaii':'HI','Idaho':'ID','Illinois':'IL','Indiana':'IN','Iowa':'IA',
    'Kansas':'KS','Kentucky':'KY','Louisiana':'LA','Maine':'ME','Maryland':'MD',
    'Massachusetts':'MA','Michigan':'MI','Minnesota':'MN','Mississippi':'MS',
    'Missouri':'MO','Montana':'MT','Nebraska':'NE','Nevada':'NV','New Hampshire':'NH',
    'New Jersey':'NJ','New Mexico':'NM','New York':'NY','North Carolina':'NC',
    'North Dakota':'ND','Ohio':'OH','Oklahoma':'OK','Oregon':'OR','Pennsylvania':'PA',
    'Rhode Island':'RI','South Carolina':'SC','South Dakota':'SD','Tennessee':'TN',
    'Texas':'TX','Utah':'UT','Vermont':'VT','Virginia':'VA','Washington':'WA',
    'West Virginia':'WV','Wisconsin':'WI','Wyoming':'WY',
    'District of Columbia':'DC',
}

# WRI BWS category thresholds (from their methodology):
#   Low < 1, Low-Medium 1-2, Medium-High 2-3, High 3-4, Extremely High >= 4
# (Aqueduct scores use the 0-5 scale.)
def bws_to_category(score):
    if pd.isna(score): return np.nan
    if score < 1: return 'Low'
    if score < 2: return 'Low-Medium'
    if score < 3: return 'Medium-High'
    if score < 4: return 'High'
    return 'Extremely High'

def fetch_us_bws():
    """Pull all US BWS sub-national rows from WRI Resource Watch CartoDB.
    Filters to indicator_name='bws' AND weight='Tot' (total water demand)
    to get exactly 51 rows — one per US state + DC.
    See WRI methodology: Kuzma et al. (2023) Aqueduct 4.0.
    """
    WRI_DIR.mkdir(parents=True, exist_ok=True)
    if RAW_OUT.exists():
        # If the cached file was pulled with the older broader query,
        # force a refresh so the weight='Tot' filter takes effect.
        # Bump this version if the query changes again.
        import os
        if os.environ.get('WRI_FORCE_REFRESH'):
            print(f'WRI_FORCE_REFRESH set, ignoring cache')
        else:
            # Quick sanity check: does cached data have only 51 rows?
            cached = json.load(open(RAW_OUT))
            cached_rows = cached.get('rows', [])
            if len(cached_rows) == 51:
                print(f'Reading cached {RAW_OUT} (51 rows)')
                return cached
            print(f'Cache has {len(cached_rows)} rows (expected 51); re-pulling')

    q = ("SELECT gid_0, name_1, indicator_name, weight, score, label, "
         "sum_weights, sum_weighted_indicator "
         "FROM aqueduct_results_v01_province_v03 "
         "WHERE gid_0='USA' AND indicator_name='bws' AND weight='Tot'")
    url = f'{CARTO_URL}?q={urllib.parse.quote(q)}'
    print(f'Fetching {url[:120]}...')
    with urllib.request.urlopen(url, timeout=60) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    with open(RAW_OUT, 'w') as f:
        json.dump(data, f, indent=2)
    print(f'Cached raw pull to {RAW_OUT}')
    return data

def main():
    payload = fetch_us_bws()
    rows = payload.get('rows', [])
    print(f'Total US sub-national BWS rows: {len(rows)}')
    assert len(rows) == 51, f'Expected 51 rows, got {len(rows)} — query may be wrong'

    df = pd.DataFrame(rows)
    df = df.dropna(subset=['score'])
    print(f'Distinct US states/regions: {df["name_1"].nunique()}')

    # With weight='Tot', WRI gives us exactly 51 rows, one per state+DC.
    # No aggregation needed.
    out_rows = []
    for full_name, code in NAME_TO_CODE.items():
        sub = df[df['name_1'].astype(str).str.strip() == full_name]
        if len(sub) == 0:
            out_rows.append({
                'state': code, 'state_name': full_name,
                'bws_score': np.nan, 'bws_category': np.nan,
                'source_note': 'No WRI sub-national entry; use country-level fallback',
                'n_subregions': 0,
            })
            continue
        bws = float(sub['score'].iloc[0])
        out_rows.append({
            'state': code, 'state_name': full_name,
            'bws_score': round(bws, 3),
            'bws_category': bws_to_category(bws),
            'source_note': f'WRI BWS weight=Tot (total water demand)',
            'n_subregions': int(len(sub)),
        })

    out = pd.DataFrame(out_rows).sort_values('bws_score', ascending=False)
    out.to_csv(OUT, index=False)
    print(f'\nWrote {len(out)} states -> {OUT}')

    # Quick print
    print('\nMost-stressed 10 states (WRI BWS, weight=Tot):')
    print(out.head(10)[['state','state_name','bws_score','bws_category']].to_string(index=False))
    print('\nLeast-stressed 10 states (WRI BWS, weight=Tot):')
    print(out.dropna(subset=['bws_score']).tail(10)[['state','state_name','bws_score','bws_category']].to_string(index=False))

if __name__ == '__main__':
    main()
