"""Task 1.1: Explore and validate the Orimadros data.

Reports shape, dtypes, lat/lon coverage, MW coverage, top operators/states,
quality flags, and a cross-check against the raw scraped file.

Run from the project root:
    .venv/bin/python notebooks/explore_orimadros.py
"""
import pandas as pd
import numpy as np
from pathlib import Path

RAW = Path('/root/project/datacenter_water_stress/data/raw')
df = pd.read_csv(RAW / 'orimadros_datacenters.csv')
scraped = pd.read_csv(RAW / 'orimadros_scraped.csv')

print('=' * 70)
print('TASK 1.1 - ORIMADROS DATA EXPLORATION')
print('=' * 70)

# ---- Shape & types ----
print(f'\n1. SHAPE & TYPES')
print(f'   Rows: {len(df):,}   Columns: {len(df.columns)}')
print(f'   NOTE: handoff said 2,060 rows; this file has {len(df):,}.')
print(f'         The 2,060-row file is orimadros_scraped.csv ({len(scraped):,} rows).')
print('\n   Column dtypes and non-null counts:')
for c in df.columns:
    t = df[c].dtype
    nonnull = df[c].notna().sum()
    print(f'     {c:30s}  {str(t):10s}  {nonnull:5d} / {len(df):,}  ({100*nonnull/len(df):5.1f}%)')

# ---- Lat/lon coverage ----
lat_valid = df['latitude'].notna() & df['longitude'].notna()
print(f'\n2. LAT/LON COVERAGE')
print(f'   Rows with valid lat AND lon: {lat_valid.sum():,} ({100*lat_valid.mean():.1f}%)')
print(f'   Rows with at least one NaN:  {(~lat_valid).sum():,} ({100*(~lat_valid).mean():.1f}%)')

suspicious_zero = lat_valid & (df['latitude'].abs() < 0.01) & (df['longitude'].abs() < 0.01)
print(f'   Suspicious (0,0) coords:     {suspicious_zero.sum():,}')

in_us = lat_valid & df['latitude'].between(24, 50) & df['longitude'].between(-125, -66)
print(f'   In US bounding box:          {in_us.sum():,} ({100*in_us.sum()/len(df):.1f}% of total)')
print(f'   Outside US box:              {(lat_valid & ~in_us).sum():,}')

# ---- MW coverage ----
mw_filled = df['MW_total_power'].notna() & (df['MW_total_power'] > 0)
print(f'\n3. MW_TOTAL_POWER COVERAGE')
print(f'   Filled (>0):    {mw_filled.sum():,} ({100*mw_filled.mean():.1f}%)')
print(f'   Missing/zero:   {(~mw_filled).sum():,} ({100*(~mw_filled).mean():.1f}%)')
if mw_filled.sum() > 0:
    s = df.loc[mw_filled, 'MW_total_power']
    print(f'   Min: {s.min():.2f}   Max: {s.max():.2f}   Mean: {s.mean():.2f}   Median: {s.median():.2f}')

# ---- Top 20 operators ----
print(f'\n4. TOP 20 OPERATORS BY FACILITY COUNT')
top_ops = df['provider'].value_counts(dropna=False).head(20)
for op, n in top_ops.items():
    label = '(NaN)' if pd.isna(op) else str(op)
    print(f'   {n:5d}  {label}')
print(f'   ... total unique providers: {df["provider"].nunique(dropna=True)}  (NaN: {df["provider"].isna().sum()})')

# ---- Top 15 states ----
print(f'\n5. TOP 15 STATES BY FACILITY COUNT')
top_states = df['state'].value_counts(dropna=False).head(15)
for st, n in top_states.items():
    label = '(NaN)' if pd.isna(st) else str(st)
    print(f'   {n:5d}  {label}')
print(f'   ... unique state values: {df["state"].nunique(dropna=True)}  (NaN: {df["state"].isna().sum()})')

# ---- Quality flags ----
print(f'\n6. QUALITY FLAGS')
print(f'   Missing address:           {df["address"].isna().sum():,}')
print(f'   Missing municipality:      {df["municipality"].isna().sum():,}')
print(f'   Missing state:             {df["state"].isna().sum():,}')
print(f'   Missing name:              {df["name"].isna().sum():,}')
print(f'   Missing provider:          {df["provider"].isna().sum():,}')
print(f'   Missing url:               {df["url"].isna().sum():,}')
print(f'   Missing street:            {df["street"].isna().sum():,}')

dup_key = df['name'].fillna('') + '|' + df['address'].fillna('')
dup_count = dup_key.duplicated(keep=False).sum()
unique_dup_groups = dup_key[dup_key.duplicated()].nunique()
print(f'   Duplicate (name+address):  {dup_count:,} rows in {unique_dup_groups} duplicate groups')

# ---- State distribution & non-US ----
us_states = {
    'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN','IA','KS',
    'KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ','NM','NY',
    'NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT','VA','WA','WV',
    'WI','WY','DC'
}
non_standard = [s for s in df['state'].value_counts().index if pd.notna(s) and s not in us_states]
print(f'\n7. STATE VALUES')
print(f'   Non-standard state codes: {len(non_standard)} -> {non_standard[:20]}')

has_state = df['state'].notna()
has_muni = df['municipality'].notna()
print(f'   Has state but missing municipality: {(has_state & ~has_muni).sum():,}')
print(f'   Has municipality but missing state:  {(~has_state & has_muni).sum():,}')

# ---- Cross-check against scraped ----
print(f'\n8. CROSS-CHECK: orimadros_datacenters.csv vs orimadros_scraped.csv')
print(f'   cleaned file rows:  {len(df):,}')
print(f'   scraped file rows:  {len(scraped):,}')
print(f'   cleaned columns:    {list(df.columns)}')
print(f'   scraped columns:    {list(scraped.columns)}')
print(f'   Difference:         {len(scraped) - len(df):,} rows dropped during cleaning')

# Save findings as a summary text file
out = Path('/root/project/datacenter_water_stress/data/processed/_task_1_1_summary.txt')
out.parent.mkdir(parents=True, exist_ok=True)
import io, sys
buf = io.StringIO()
# reroute prints into buf by simply re-capturing stdout
old_stdout = sys.stdout
sys.stdout = buf
# re-run the same prints
print('TASK 1.1 SUMMARY')
print(f'rows={len(df)}, columns={len(df.columns)}')
print(f'latlon_valid={lat_valid.sum()}, latlon_pct={100*lat_valid.mean():.1f}')
print(f'mw_filled={mw_filled.sum()}, mw_pct={100*mw_filled.mean():.1f}')
sys.stdout = old_stdout
out.write_text(buf.getvalue())
print(f'\n(wrote task 1.1 stub to {out})')
