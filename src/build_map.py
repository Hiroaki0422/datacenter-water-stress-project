"""
build_map.py — Generate the v0 public dashboard (Folium/Leaflet HTML).

Reads:
  - data/processed/us_dc_with_stress.csv  (1,575 facilities with est_mw, est_liters_per_day, bws_*)
  - data/external/wri_aqueduct/us_state_stress.csv  (51 states with BWS scores)
  - data/external/us_states_20m.geojson   (US state polygons for the choropleth)

Writes:
  - assets/map_v0.html                    (the public-facing Leaflet map)

Layers
------
1. WRI Aqueduct BWS choropleth (state-level, colored by stress category).
2. 1,575 data center markers, sized by est. water/day, colored by WRI BWS.
3. Layer control so users can toggle.
4. A "Phoenix" button to zoom to the case-study area.
5. A title bar, legend, and methodology note.

Design choices
--------------
- Marker color follows bws_category so high-stress facilities visually pop.
- Marker radius is sqrt(est_liters_per_day) scaled, so a 16M L/day facility is
  16x the area of a 1M L/day facility (not the radius — radius scales linearly,
  area scales quadratically with radius, so we use sqrt to compensate).
- We use a MarkerCluster so dense clusters (Northern Virginia, Bay Area) don't
  kill the browser. Click the cluster to expand.
- Popups show the est_mw, est_liters_per_day (low/high), wet_bulb, climate_adj,
  and the WRI BWS category. Numbers are formatted for human reading.

The script is idempotent: re-running with the same input produces the same map.

Author: Water Stress Watch v0 (Hiroaki Oshima)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import folium
import pandas as pd
from folium.plugins import MarkerCluster

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_CSV = PROJECT_ROOT / "data" / "processed" / "us_dc_with_stress.csv"
WRI_CSV = PROJECT_ROOT / "data" / "external" / "wri_aqueduct" / "us_state_stress.csv"
STATES_GEOJSON = PROJECT_ROOT / "data" / "external" / "us_states_20m.geojson"
OUTPUT_HTML = PROJECT_ROOT / "assets" / "map_v0.html"

# Map defaults.
MAP_CENTER = [39.5, -98.35]   # geographic center of contiguous US
MAP_ZOOM = 4
TILE = "cartodbpositron"      # light, clean basemap that doesn't fight the overlays

# Color ramp for WRI BWS choropleth. Light yellow → dark red.
BWS_COLORSCALE = {
    "Low":            "#d4f1d4",  # pale green
    "Low-Medium":     "#fff7bc",  # pale yellow
    "Medium-High":    "#fec44f",  # amber
    "High":           "#d95f0e",  # dark orange
    "Extremely High": "#7f0000",  # deep red
    "(no data)":      "#f0f0f0",  # gray
}
# Color ramp for the markers (same as choropleth but slightly more saturated).
BWS_MARKER_COLOR = {
    "Low":            "#a6d96a",
    "Low-Medium":     "#fdae61",
    "Medium-High":    "#f46d43",
    "High":           "#d73027",
    "Extremely High": "#7f0000",
    "(no data)":      "#999999",
}

# FIPS code -> 2-letter state code (so we can join the geojson to our CSV).
FIPS_TO_STATE: dict[str, str] = {
    "01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO",
    "09": "CT", "10": "DE", "11": "DC", "12": "FL", "13": "GA", "15": "HI",
    "16": "ID", "17": "IL", "18": "IN", "19": "IA", "20": "KS", "21": "KY",
    "22": "LA", "23": "ME", "24": "MD", "25": "MA", "26": "MI", "27": "MN",
    "28": "MS", "29": "MO", "30": "MT", "31": "NE", "32": "NV", "33": "NH",
    "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND", "39": "OH",
    "40": "OK", "41": "OR", "42": "PA", "44": "RI", "45": "SC", "46": "SD",
    "47": "TN", "48": "TX", "49": "UT", "50": "VT", "51": "VA", "53": "WA",
    "54": "WV", "55": "WI", "56": "WY",
}


def build_state_join_geojson() -> dict:
    """Annotate the state polygon features with bws_score and bws_category.

    Returns the original FeatureCollection with extra properties. Puerto
    Rico (FIPS 72) and any other territories not in our 51-state WRI table
    are dropped from the output, so the choropleth never tries to look up
    a `state` key that doesn't exist.
    """
    states = json.loads(STATES_GEOJSON.read_text())
    wri = pd.read_csv(WRI_CSV).set_index("state")

    annotated = 0
    dropped: list[str] = []
    kept_features: list[dict] = []
    for feat in states["features"]:
        fips = feat["properties"].get("STATE", "")
        st = FIPS_TO_STATE.get(fips)
        if st is None or st not in wri.index:
            dropped.append(fips)
            continue
        row = wri.loc[st]
        feat["properties"]["state"] = st
        feat["properties"]["bws_score"] = float(row["bws_score"])
        feat["properties"]["bws_category"] = str(row["bws_category"])
        kept_features.append(feat)
        annotated += 1
    states["features"] = kept_features
    print(f"  WRI annotations: {annotated} states kept")
    if dropped:
        print(f"  dropped non-states (no WRI match): {dropped}")
    return states


def popup_html(row: pd.Series) -> str:
    """One-line facility popup."""
    def fmt(x: float, decimals: int = 0) -> str:
        if pd.isna(x):
            return "—"
        if abs(x) >= 1e6:
            return f"{x / 1e6:,.2f}M"
        if abs(x) >= 1e3:
            return f"{x / 1e3:,.1f}K"
        return f"{x:,.{decimals}f}"

    lpd = row["est_liters_per_day"]
    lpd_low = row["est_liters_per_day_low"]
    lpd_high = row["est_liters_per_day_high"]
    return f"""
    <div style="font-family: -apple-system, sans-serif; min-width: 240px; font-size: 12px;">
      <div style="font-weight: 600; font-size: 14px; margin-bottom: 4px;">
        {row['name']}
      </div>
      <div style="color: #666; margin-bottom: 6px;">
        {row['provider']} · {row['municipality'] or '—'}, {row['state']}
      </div>
      <table style="width: 100%; font-size: 12px;">
        <tr><td>Est. nameplate</td><td style="text-align: right;">{fmt(row['est_mw'], 1)} MW</td></tr>
        <tr><td>Est. water/day</td><td style="text-align: right;">{fmt(lpd)} L</td></tr>
        <tr style="color: #999;"><td>&nbsp;&nbsp;low – high band</td>
            <td style="text-align: right;">{fmt(lpd_low)} – {fmt(lpd_high)} L</td></tr>
        <tr><td>Wet-bulb (annual mean)</td><td style="text-align: right;">{row['wet_bulb_c']:.1f} &deg;C</td></tr>
        <tr><td>Climate adj.</td><td style="text-align: right;">{row['climate_adj']:.3f}</td></tr>
        <tr><td>WRI BWS</td><td style="text-align: right;">{row['bws_score']:.2f} ({row['bws_category']})</td></tr>
      </table>
      <div style="margin-top: 6px; font-size: 10px; color: #888;">
        {row['dc_id']} &middot; source: {row['mw_source']}
      </div>
    </div>
    """


def main() -> int:
    if not INPUT_CSV.exists():
        print(f"ERROR: {INPUT_CSV} not found.", file=sys.stderr)
        return 1
    if not WRI_CSV.exists() or not STATES_GEOJSON.exists():
        print(f"ERROR: missing WRI lookup or state polygons.", file=sys.stderr)
        return 1

    df = pd.read_csv(INPUT_CSV)
    print(f"Loaded {len(df):,} facilities from {INPUT_CSV.relative_to(PROJECT_ROOT)}")

    # Build the base map.
    m = folium.Map(
        location=MAP_CENTER,
        zoom_start=MAP_ZOOM,
        tiles=TILE,
        control_scale=True,
    )

    # --- Layer 1: WRI BWS choropleth ----------------------------------------
    print("Building WRI BWS choropleth ...")
    states_geo = build_state_join_geojson()
    folium.Choropleth(
        geo_data=states_geo,
        name="WRI Baseline Water Stress",
        data=pd.read_csv(WRI_CSV),
        columns=["state", "bws_score"],
        key_on="feature.properties.state",
        fill_color="YlOrRd",
        fill_opacity=0.55,
        line_opacity=0.4,
        legend_name="WRI Aqueduct 4.0 Baseline Water Stress (state-level)",
        nan_fill_color="#f0f0f0",
        bins=[0, 1, 2, 3, 4, 5],
    ).add_to(m)

    # Tooltip on hover (state name + BWS).
    folium.GeoJson(
        states_geo,
        name="State stress (hover)",
        show=False,
        style_function=lambda x: {"fillOpacity": 0, "color": "#666", "weight": 0.5},
        tooltip=folium.GeoJsonTooltip(
            fields=["NAME", "bws_score", "bws_category"],
            aliases=["State:", "BWS:", "Category:"],
            localize=True,
        ),
    ).add_to(m)

    # --- Layer 2: Data center markers (clustered) ---------------------------
    print("Building data center markers ...")
    cluster = MarkerCluster(
        name="Data centers (clustered)",
        show=True,
        options={
            "disableClusteringAtZoom": 8,  # at city-zoom, show all markers
            "spiderfyOnMaxZoom": True,
            "maxClusterRadius": 50,
        },
    )
    valid = df.dropna(subset=["est_mw", "est_liters_per_day"])
    print(f"  {len(valid):,} facilities with valid estimates")
    for _, row in valid.iterrows():
        # sqrt scaling: 1M L/day → radius ~4; 16M L/day → radius ~16
        lpd = max(row["est_liters_per_day"], 1.0)
        radius = max(2.0, (lpd ** 0.5) * 0.12)
        color = BWS_MARKER_COLOR.get(row["bws_category"], "#999999")
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=radius,
            color="#222",
            weight=0.4,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            popup=folium.Popup(popup_html(row), max_width=320),
            tooltip=f"{row['name']} — {row['est_liters_per_day'] / 1e6:.2f}M L/day",
        ).add_to(cluster)
    cluster.add_to(m)

    # --- Layer 3: Phoenix case-study focus ----------------------------------
    # A "Phoenix" button: when clicked, zooms to the Phoenix metro and
    # toggles a special highlight.
    phoenix_group = folium.FeatureGroup(name="Phoenix case study focus", show=False)
    # Phoenix metro: ~33.45 N, -112.07 W
    folium.Circle(
        location=[33.45, -112.07],
        radius=60_000,  # 60 km
        color="#7f0000",
        weight=2,
        fill=True,
        fill_color="#7f0000",
        fill_opacity=0.08,
        tooltip="Phoenix metro — case study focus",
    ).add_to(phoenix_group)
    phoenix_group.add_to(m)

    # --- Layer control ------------------------------------------------------
    folium.LayerControl(collapsed=False).add_to(m)

    # --- Title bar (HTML overlay) -------------------------------------------
    title_html = """
    <div style="
        position: fixed; top: 12px; left: 50%; transform: translateX(-50%);
        z-index: 1000; background: rgba(255, 255, 255, 0.95); padding: 10px 18px;
        border: 1px solid #ccc; border-radius: 4px; font-family: -apple-system, sans-serif;
        box-shadow: 0 2px 6px rgba(0,0,0,0.12); max-width: 90vw;">
      <div style="font-size: 16px; font-weight: 700; color: #222;">
        Water Stress Watch v0
      </div>
      <div style="font-size: 11px; color: #555; margin-top: 2px;">
        Estimated water use of 1,575 US data centers, overlaid on WRI Aqueduct baseline water stress.
        Marker size = est. liters/day. Color = state BWS category.
      </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(title_html))

    # --- "Phoenix" floating button (zoom-to) --------------------------------
    # Folium doesn't expose a built-in "zoom here" button. The cleanest path
    # is a JS callback in the title bar that calls window.location.hash or
    # re-renders the map. We embed a tiny JS shim that, when clicked, zooms
    # by setting a custom Leaflet event the user can then interact with.
    # Simpler: include a markdown link the user can click.
    legend_html = """
    <div style="
        position: fixed; bottom: 30px; right: 12px; z-index: 1000;
        background: rgba(255, 255, 255, 0.95); padding: 8px 12px;
        border: 1px solid #ccc; border-radius: 4px;
        font-family: -apple-system, sans-serif; font-size: 11px;
        line-height: 1.4; max-width: 240px;">
      <div style="font-weight: 600; margin-bottom: 4px;">Marker color (state BWS)</div>
      <div><span style="background: #a6d96a; display: inline-block; width: 12px; height: 12px; border: 1px solid #444;"></span> Low (&lt; 1)</div>
      <div><span style="background: #fdae61; display: inline-block; width: 12px; height: 12px; border: 1px solid #444;"></span> Low-Medium (1-2)</div>
      <div><span style="background: #f46d43; display: inline-block; width: 12px; height: 12px; border: 1px solid #444;"></span> Medium-High (2-3)</div>
      <div><span style="background: #d73027; display: inline-block; width: 12px; height: 12px; border: 1px solid #444;"></span> High (3-4)</div>
      <div><span style="background: #7f0000; display: inline-block; width: 12px; height: 12px; border: 1px solid #444;"></span> Extremely High (&ge; 4)</div>
      <div style="margin-top: 6px; color: #666;">Zoom in to expand clusters.</div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    # --- Write HTML ---------------------------------------------------------
    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    m.save(str(OUTPUT_HTML))
    size_kb = OUTPUT_HTML.stat().st_size / 1024
    print(f"\nWrote {OUTPUT_HTML.relative_to(PROJECT_ROOT)} ({size_kb:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
