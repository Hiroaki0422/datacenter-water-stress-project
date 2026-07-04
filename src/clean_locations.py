"""Clean the Orimadros data into the v0 source of truth.

Real cleaning tasks (the data already has lat/lon for all rows):
  1. Reverse-derive state from address for missing-state rows (regex).
  2. Normalize full state names and city-misplaced-in-state values to 2-letter codes.
  3. Reverse-geocode lat/lon via US-states polygon lookup for any remaining NaN states.
  4. Flag coords that don't match the cleaned state.
  5. Deduplicate name+address duplicate rows.
  6. Mark MW outliers (>=1000 MW, <0.1 MW) for review.

Output: data/processed/us_dc_locations.csv
"""
import json
import re
import pandas as pd
import numpy as np
from pathlib import Path
from shapely.geometry import shape, Point

RAW = Path('/root/project/datacenter_water_stress/data/raw')
EXT = Path('/root/project/datacenter_water_stress/data/external')
OUT = Path('/root/project/datacenter_water_stress/data/processed/us_dc_locations.csv')

# Load US states polygons once
with open(EXT / 'us_states_20m.geojson') as f:
    STATES_GEOJSON = json.load(f)
STATE_POLYGONS = []
for feat in STATES_GEOJSON['features']:
    name = feat['properties']['NAME']
    # Map full state name to 2-letter code
    STATE_POLYGONS.append((name, shape(feat['geometry'])))

# Build reverse-lookup: state-name -> 2-letter code (canonical)
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
    'West Virginia':'WV','Wisconsin':'WI','Wyoming':'WY','District of Columbia':'DC',
    'Puerto Rico':'PR',
}
US_STATES_50_DC = set(NAME_TO_CODE.values())

def state_from_coords(lat, lon):
    """Reverse-geocode: return 2-letter state code from a (lat, lon) point."""
    if pd.isna(lat) or pd.isna(lon):
        return np.nan
    pt = Point(lon, lat)
    for name, poly in STATE_POLYGONS:
        if poly.contains(pt):
            return NAME_TO_CODE.get(name, np.nan)
    return np.nan

df = pd.read_csv(RAW / 'orimadros_datacenters.csv')

print(f'Input rows: {len(df):,}')
n0 = len(df)

# ---------- 1. Drop the legacy index column ----------
if 'Unnamed: 0' in df.columns:
    df = df.drop(columns=['Unnamed: 0'])

# ---------- 2. State normalization ----------
# Map of full state names -> 2-letter codes
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
    'West Virginia':'WV','Wisconsin':'WI','Wyoming':'WY','District of Columbia':'DC',
    'Loudoun County':'VA',  # data quirk
}

# Cities that were misfiled in the state column - map to actual state code
CITY_TO_STATE = {
    'San Jose':'CA','Cincinnati':'OH','Philadelphia':'PA','Dallas':'TX',
    'Salt Lake':'UT','Buffalo':'NY','Tucson':'AZ',
}

US_STATES_50_DC = set(NAME_TO_CODE.values())

def normalize_state(row):
    s = row['state']
    if pd.isna(s):
        # Try to recover from address
        addr = row.get('address', '')
        if isinstance(addr, str):
            m = re.search(r',\s*([A-Z]{2})\s*\d*\s*$', addr)
            if m: return m.group(1)
            m = re.search(r',\s*([A-Z]{2}),\s*USA', addr)
            if m: return m.group(1)
            # Try full state name
            for name, code in NAME_TO_CODE.items():
                if f', {name},' in addr or f', {name} ' in addr:
                    return code
        return np.nan
    s = str(s).strip()
    if s in US_STATES_50_DC:
        return s
    # Disambiguate 'Washington' first - it could mean DC or WA state.
    # Use the address to disambiguate (Washington, DC vs Lynnwood, Washington).
    if s == 'Washington':
        addr = row.get('address', '')
        if isinstance(addr, str) and 'Washington, DC' in addr:
            return 'DC'
        return 'WA'
    if s in NAME_TO_CODE:
        return NAME_TO_CODE[s]
    if s in CITY_TO_STATE:
        return CITY_TO_STATE[s]
    return np.nan  # unresolvable

df['state'] = df.apply(normalize_state, axis=1)

# ---------- 2b. Reverse-derive state from lat/lon for remaining NaNs ----------
# For rows where state still can't be inferred from text, do a real polygon
# point-in-polygon lookup against US state borders.
mask = df['state'].isna() & df['latitude'].notna() & df['longitude'].notna()
if mask.sum() > 0:
    df.loc[mask, 'state'] = df.loc[mask].apply(
        lambda r: state_from_coords(r['latitude'], r['longitude']), axis=1
    )

# ---------- 3. State coverage report ----------
state_after = df['state'].notna().sum()
print(f'State recovered: {state_after:,} / {len(df):,} ({100*state_after/len(df):.1f}%)')
print(f'Still-missing state: {df["state"].isna().sum()}')

if df['state'].isna().sum() > 0:
    print('Remaining missing-state rows (will review):')
    print(df[df['state'].isna()][['name','address','municipality','latitude','longitude']].head(20).to_string())

# ---------- 4. Validate coords match cleaned state ----------
# Use the polygon lookup to verify the lat/lon actually falls in the claimed state.
# Flag mismatches — these are data errors worth investigating.
us_mainland = df['latitude'].between(24, 50) & df['longitude'].between(-125, -66)
hawaii = df['latitude'].between(19, 22) & df['longitude'].between(-161, -154)
alaska = df['latitude'].between(51, 72) & df['longitude'].between(-180, -130)
in_us = us_mainland | hawaii | alaska
print(f'In US bbox (incl. HI/AK): {in_us.sum():,} / {len(df):,} ({100*in_us.sum()/len(df):.1f}%)')

df['state_from_coords'] = df.apply(
    lambda r: state_from_coords(r['latitude'], r['longitude']) if pd.notna(r['latitude']) else np.nan,
    axis=1
)
df['coord_state_mismatch'] = (
    df['state'].notna() & df['state_from_coords'].notna() & (df['state'] != df['state_from_coords'])
)
mismatches = df['coord_state_mismatch'].sum()
print(f'Coords/state mismatches: {mismatches:,}')

# ---------- 5. Mark MW outliers for review ----------
df['mw_flagged_outlier'] = (
    (df['MW_total_power'].notna() & (df['MW_total_power'] >= 1000)) |  # implausibly large
    (df['MW_total_power'].notna() & (df['MW_total_power'] < 0.1))      # implausibly small
)
print(f'MW outliers flagged: {df["mw_flagged_outlier"].sum()}')

# ---------- 6. Deduplicate by name+address ----------
before = len(df)
df = df.drop_duplicates(subset=['name','address'], keep='first')
after = len(df)
print(f'After dedup: {after:,} (dropped {before - after} duplicate rows)')

# ---------- 7. Add a clean_id column for stable referencing ----------
df = df.reset_index(drop=True)
df.insert(0, 'dc_id', [f'DC-{i:05d}' for i in range(len(df))])

# ---------- 8. Reorder columns for readability ----------
col_order = [
    'dc_id','name','provider','address','municipality','state',
    'latitude','longitude','state_from_coords','coord_state_mismatch',
    'MW_total_power','mw_flagged_outlier',
    'miles_to_nearest_airport',
    'sqft_colocation_space','sqft_total_space','url','number','street',
]
df = df[[c for c in col_order if c in df.columns]]

# ---------- Save ----------
OUT.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT, index=False)
print(f'\nWrote {len(df):,} rows -> {OUT}')

# Final summary
print('\n' + '='*70)
print('CLEANED DATA SUMMARY')
print('='*70)
print(f'Removed: {n0 - len(df)} rows ({n0} -> {len(df)})')
print(f'Rows with valid state: {df["state"].notna().sum():,} ({100*df["state"].notna().mean():.1f}%)')
print(f'Rows with valid lat/lon: {df["latitude"].notna().sum():,}')
print(f'Rows with MW > 0: {(df["MW_total_power"].fillna(0) > 0).sum():,}')
print(f'Unique states: {df["state"].nunique()}')
print(f'Top 5 states: {df["state"].value_counts().head(5).to_dict()}')
