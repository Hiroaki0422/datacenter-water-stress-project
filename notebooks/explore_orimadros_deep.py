"""Task 1.1 deep dive: outliers, non-US rows, non-standard states, duplicates."""
import pandas as pd
import numpy as np
from pathlib import Path

RAW = Path('/root/project/datacenter_water_stress/data/raw')
df = pd.read_csv(RAW / 'orimadros_datacenters.csv')

print('MW_TOTAL_POWER - outlier check')
mw = df['MW_total_power'].dropna()
print(f'  > 1000 MW: {(mw > 1000).sum()} rows')
print(f'  >  500 MW: {(mw > 500).sum()} rows')
print(f'  >  200 MW: {(mw > 200).sum()} rows')
print(f'  >  100 MW: {(mw > 100).sum()} rows')
print(f'  >   50 MW: {(mw > 50).sum()} rows')
print(f'  1-50 MW:    {((mw > 1) & (mw <= 50)).sum()} rows')
print(f'  < 1 MW:     {(mw < 1).sum()} rows')
print()
print('Top 10 MW values (likely unit-bug candidates):')
print(df.nlargest(10, 'MW_total_power')[['name', 'MW_total_power', 'sqft_total_space', 'state']].to_string())
print()
print('Smallest 10 MW values:')
print(df.nsmallest(10, 'MW_total_power')[['name', 'MW_total_power', 'sqft_total_space', 'state']].to_string())

print()
print('Rows outside US bbox:')
us = df['latitude'].between(24, 50) & df['longitude'].between(-125, -66)
print(df.loc[~us, ['name', 'address', 'state', 'latitude', 'longitude']].to_string())

print()
us_states = {
    'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN','IA','KS',
    'KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ','NM','NY',
    'NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT','VA','WA','WV',
    'WI','WY','DC'
}
non_std = df[~df['state'].isin(us_states) & df['state'].notna()]
print('All non-standard state values and counts:')
print(non_std['state'].value_counts().to_string())

print()
print(f'Missing-state rows: {df["state"].isna().sum()}')
print('Sample missing-state rows:')
print(df[df['state'].isna()].head(15)[['name', 'address', 'municipality', 'state', 'latitude', 'longitude']].to_string())

print()
dup_key = df['name'].fillna('') + '|' + df['address'].fillna('')
dups = df[dup_key.duplicated(keep=False)].sort_values('name')
print(f'Duplicate rows (first 12):')
print(dups[['name', 'address', 'state', 'MW_total_power']].head(12).to_string())

# Check if "missing state" rows actually have state hidden in address
print()
print('Reverse-deriving state from address for missing-state rows:')
miss = df[df['state'].isna()].copy()
# US state abbreviations usually appear near end of address string
def extract_state(addr):
    if not isinstance(addr, str): return None
    # Look for ", XX, USA" or ", XX " near end
    import re
    m = re.search(r',\s*([A-Z]{2})\s*\d*\s*$', addr)
    if m: return m.group(1)
    m = re.search(r',\s*([A-Z]{2}),\s*USA', addr)
    if m: return m.group(1)
    return None
miss['derived_state'] = miss['address'].apply(extract_state)
print(f'Derived state for {miss["derived_state"].notna().sum()} of {len(miss)} missing-state rows.')
print(miss[['name', 'address', 'derived_state']].head(20).to_string())
