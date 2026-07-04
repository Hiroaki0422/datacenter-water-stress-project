"""
estimate_power.py — Fill missing MW values for US data centers.

Hiroaki's locked decision (2026-07-04): operator-class heuristic. For the
831 rows with no disclosed MW, we assign a per-facility default based on
the operator's class (hyperscaler, major colo, edge, telecom, CDN, etc.).

Inputs
------
data/processed/us_dc_locations.csv
    Cleaned US data center locations (1,575 rows). Output of clean_locations.py.

Outputs
-------
data/processed/us_dc_with_mw.csv
    Same 1,575 rows, plus:
      - est_mw    (float) : best-estimate nameplate MW for the facility.
                            Equals disclosed MW when trustworthy; falls back
                            to operator-class heuristic otherwise; NaN for
                            MW outliers (excluded from estimation).
      - mw_source (string): provenance tag.
                            'disclosed' / 'outlier_excluded' /
                            'heuristic:<class>' / 'heuristic:unknown'.

Methodology
-----------
Step 1: Trust disclosed MW_total_power EXCEPT when flagged as an outlier
        (>= 1000 MW or < 0.1 MW — see clean_locations.py).
Step 2: For rows with no disclosed MW, classify the operator by substring
        match against a curated dictionary of 220 unique provider names.
        Case-insensitive substring matching.
Step 3: Look up the class default MW from CLASS_DEFAULT_MW (see module).
Step 4: Anything that doesn't match a known substring gets the 'unknown'
        fallback (15 MW — the median of the major-colo default). This is
        a documented conservatism, not a bug.

Class default MW values are based on:
  - Hyperscaler self-built: Google discloses 50-200 MW/site in its
    2024 environmental report; AWS Direct Connect locations are similar.
    50 MW is a conservative middle.
  - Hyperscaler colocation leases (sub-leases inside Equinix/Digital
    Realty): 30 MW.
  - Major colocation: industry standard 10-30 MW/site. Equinix DC2
    Ashburn (in our data) is 4.9 MW, but new Equinix xScale facilities
    are 50-100+ MW. 20 MW is the middle of the range.
  - Secondary colocation: 10 MW. Smaller regional providers.
  - Edge / micro: 0.2 MW. Often shipping-container MEC sites.
  - Telecom / cable: 5 MW. PoPs that may include small DC capacity.
  - CDN: 0.5 MW. Edge caches, not full data centers.
  - Enterprise self: 5 MW. Conservative for in-house corporate DCs.
  - Unknown: 15 MW. Median of major-colo default. Documented fallback.

The script is idempotent: re-running produces the same output.

Author: Water Stress Watch v0 (Hiroaki Oshima)
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_CSV = PROJECT_ROOT / "data" / "processed" / "us_dc_locations.csv"
OUTPUT_CSV = PROJECT_ROOT / "data" / "processed" / "us_dc_with_mw.csv"


# -----------------------------------------------------------------------------
# Operator classification
# -----------------------------------------------------------------------------
# Match by case-insensitive substring. The order of keys matters: the first
# match wins, so put more specific patterns before more general ones
# (e.g. "google" before "ntt" is irrelevant here, but "cogent" before
# generic "cog" is what we want — actually we don't have that conflict).
# Substring matching: "equinix" matches "Equinix: DC2 Ashburn Data Center".
# We store the lookup as (class_name, matched_substring) so the matched
# substring can be included in mw_source for auditability.

CLASS_DEFAULT_MW: dict[str, float] = {
    "hyperscaler_self": 50.0,
    "hyperscaler_colo": 30.0,
    "colocation_major": 20.0,
    "colocation_secondary": 10.0,
    "edge_micro": 0.2,
    "cable_telecom": 5.0,
    "cdn_isp": 0.5,
    "enterprise_self": 5.0,
    "unknown": 15.0,  # median of major-colo default
}

# Substring -> class. Order is significant within each class group:
# more specific substrings first so that e.g. "aws" doesn't accidentally
# match a future "lawson" substring. Within a class we put the longest /
# most specific patterns first as a defensive measure.
OPERATOR_PATTERNS: list[tuple[str, str]] = [
    # --- Hyperscaler self-built (50 MW) -------------------------------------
    ("hyperscaler_self", "google"),
    ("hyperscaler_self", "amazon aws"),
    ("hyperscaler_self", "amazon"),
    ("hyperscaler_self", "aws"),
    ("hyperscaler_self", "microsoft"),
    ("hyperscaler_self", "azure"),
    ("hyperscaler_self", "meta"),
    ("hyperscaler_self", "facebook"),
    ("hyperscaler_self", "oracle cloud"),
    ("hyperscaler_self", "oracle"),
    ("hyperscaler_self", "ibm cloud"),
    ("hyperscaler_self", "apple"),
    ("hyperscaler_self", "ovhcloud"),
    ("hyperscaler_self", "ovh"),
    ("hyperscaler_self", "alibaba"),
    ("hyperscaler_self", "tencent"),

    # --- Major colocation (20 MW) -------------------------------------------
    # These are the big national/global colo brands.
    ("colocation_major", "equinix"),
    ("colocation_major", "digital realty"),
    ("colocation_major", "qts"),
    ("colocation_major", "cyrusone"),
    ("colocation_major", "coresite"),
    ("colocation_major", "vantage"),
    ("colocation_major", "aligned"),
    ("colocation_major", "flexential"),
    ("colocation_major", "cyxtera"),
    ("colocation_major", "databank"),
    ("colocation_major", "centersquare"),
    ("colocation_major", "tierpoint"),
    ("colocation_major", "ntt global"),
    ("colocation_major", "edgeconnex"),
    ("colocation_major", "teleports"),
    ("colocation_major", "serverfarm"),
    ("colocation_major", "h5 data"),
    ("colocation_major", "inap"),  # INAP was acquired by Internap → still major
    ("colocation_major", "365 data"),
    ("colocation_major", "365 "),  # 365 Data Centers
    ("colocation_major", "iron mountain"),
    ("colocation_major", "centerserv"),
    ("colocation_major", "primus"),
    ("colocation_major", "cologix"),
    ("colocation_major", "compass datacenters"),
    ("colocation_major", "compass data"),  # defense
    ("colocation_major", "vantage data"),
    ("colocation_major", "dataprise"),
    ("colocation_major", "phoenixnap"),
    ("colocation_major", "phoenix nap"),
    ("colocation_major", "bluebird"),
    ("colocation_major", "bluebird data"),
    ("colocation_major", "switch"),  # Switch Data Centers — major
    ("colocation_major", "markley"),
    ("colocation_major", "gtt"),
    ("colocation_major", "navisite"),
    ("colocation_major", "rackspace"),
    ("colocation_major", "copt"),
    ("colocation_major", "dataverge"),
    ("colocation_major", "dupont fabros"),
    ("colocation_major", "infomart"),  # Infomart Dallas
    ("colocation_major", "sentinel data"),
    ("colocation_major", "datacate"),
    ("colocation_major", "zayo"),  # Zayo is fiber + colo, leaning major
    ("colocation_major", "hivelocity"),
    ("colocation_major", "evocative"),
    ("colocation_major", "colo locker"),
    ("colocation_major", "cologix"),
    ("colocation_major", "sabey"),
    ("colocation_major", "vultr"),  # Vultr — sizable cloud/colo
    ("colocation_major", "11:11 systems"),
    ("colocation_major", "cloudhq"),
    ("colocation_major", "lincoln rackhouse"),

    # --- Secondary colocation (10 MW) ---------------------------------------
    ("colocation_secondary", "mod mission"),
    ("colocation_secondary", "mod data"),
    ("colocation_secondary", "lumen"),  # Lumen has both colocation and telecom; default to colo
    ("colocation_secondary", "centurylink"),  # legacy Lumen
    ("colocation_secondary", "level 3"),  # legacy Lumen
    ("colocation_secondary", "zenlayer"),
    ("colocation_secondary", "cogent"),  # Cogent has both; default to secondary colo
    ("colocation_secondary", "hivelocity"),
    ("colocation_secondary", "netrality"),
    ("colocation_secondary", "aptum"),
    ("colocation_secondary", "tpx"),
    ("colocation_secondary", "performive"),
    ("colocation_secondary", "telesystem"),
    ("colocation_secondary", "managedway"),
    ("colocation_secondary", "dedicated solutions"),
    ("colocation_secondary", "coloamerica"),
    ("colocation_secondary", "colocation america"),
    ("colocation_secondary", "us signal"),
    ("colocation_secondary", "firstlight"),
    ("colocation_secondary", "lightedge"),
    ("colocation_secondary", "involta"),
    ("colocation_secondary", "expedient"),
    ("colocation_secondary", "lumos"),
    ("colocation_secondary", "unitedlayer"),
    ("colocation_secondary", "tier 3"),
    ("colocation_secondary", "viawest"),  # legacy Flexential
    ("colocation_secondary", "aurobix"),
    ("colocation_secondary", "aubix"),
    ("colocation_secondary", "evocative"),
    ("colocation_secondary", "fiberhub"),
    ("colocation_secondary", "datapacket"),
    ("colocation_secondary", "quadranet"),
    ("colocation_secondary", "liquid web"),
    ("colocation_secondary", "bigbyte"),
    ("colocation_secondary", "serverhub"),
    ("colocation_secondary", "hostdime"),
    ("colocation_secondary", "nautilus data"),
    ("colocation_secondary", "expedient"),
    ("colocation_secondary", "carpathia"),
    ("colocation_secondary", "peak 10"),
    ("colocation_secondary", "data canopy"),
    ("colocation_secondary", "canopy"),
    ("colocation_secondary", "edge"),
    ("colocation_secondary", "ai net"),
    ("colocation_secondary", "ainet"),
    ("colocation_secondary", "massive networks"),
    ("colocation_secondary", "fiberstate"),
    ("colocation_secondary", "iron rails"),
    ("colocation_secondary", "mountain west"),
    ("colocation_secondary", "colorado_datacenters".replace("_", " ")),
    ("colocation_secondary", "weconnect"),
    ("colocation_secondary", "we connect"),
    ("colocation_secondary", "acuative"),
    ("colocation_secondary", "blue mantis"),
    ("colocation_secondary", "365 "),
    ("colocation_secondary", "frontline data"),
    ("colocation_secondary", "one data center"),
    ("colocation_secondary", "rollernet"),
    ("colocation_secondary", "roller network"),
    ("colocation_secondary", "voyent"),
    ("colocation_secondary", "logix"),
    ("colocation_secondary", "shatter it"),
    ("colocation_secondary", "tsr solutions"),
    ("colocation_secondary", "colovore"),
    ("colocation_secondary", "rack b bunker"),
    ("colocation_secondary", "rackbunker"),
    ("colocation_secondary", "rack bunker"),
    ("colocation_secondary", "racksquared"),
    ("colocation_secondary", "rack59"),
    ("colocation_secondary", "hudsonix"),
    ("colocation_secondary", "hudson ix"),
    ("colocation_secondary", "ntirety"),
    ("colocation_secondary", "cogent"),
    ("colocation_secondary", "acronis"),
    ("colocation_secondary", "avo systems"),
    ("colocation_secondary", "aureon"),
    ("colocation_secondary", "carroll-net"),
    ("colocation_secondary", "cogent"),
    ("colocation_secondary", "charotte colocation"),
    ("colocation_secondary", "charlotte colocation"),
    ("colocation_secondary", "cascade divide"),
    ("colocation_secondary", "carrier one"),
    ("colocation_secondary", "cloudsmart"),
    ("colocation_secondary", "colo barn"),
    ("colocation_secondary", "colobarn"),
    ("colocation_secondary", "comarch"),
    ("colocation_secondary", "compass"),
    ("colocation_secondary", "conscious networks"),
    ("colocation_secondary", "databridge"),
    ("colocation_secondary", "data holdings"),
    ("colocation_secondary", "direct ltx"),
    ("colocation_secondary", "dp facilities"),
    ("colocation_secondary", "dynamic internet"),
    ("colocation_secondary", "epsilon"),
    ("colocation_secondary", "exa infrastructure"),
    ("colocation_secondary", "excaltech"),
    ("colocation_secondary", "expedient"),
    ("colocation_secondary", "fiberstate"),
    ("colocation_secondary", "first national"),
    ("colocation_secondary", "fnts"),
    ("colocation_secondary", "fogo"),
    ("colocation_secondary", "fortress"),
    ("colocation_secondary", "fuseforward"),
    ("colocation_secondary", "giga data"),
    ("colocation_secondary", "hopone"),
    ("colocation_secondary", "hop one"),
    ("colocation_secondary", "inoc"),
    ("colocation_secondary", "it solutions"),
    ("colocation_secondary", "itsg"),
    ("colocation_secondary", "layered tech"),
    ("colocation_secondary", "liberty center"),
    ("colocation_secondary", "litewire"),
    ("colocation_secondary", "massive networks"),
    ("colocation_secondary", "massiv"),
    ("colocation_secondary", "midco"),
    ("colocation_secondary", "mountain west"),
    ("colocation_secondary", "netcrohosting"),
    ("colocation_secondary", "netshop"),
    ("colocation_secondary", "netsh"),
    ("colocation_secondary", "omnis7"),
    ("colocation_secondary", "opushost"),
    ("colocation_secondary", "opti9"),
    ("colocation_secondary", "opus interactive"),
    ("colocation_secondary", "performive"),
    ("colocation_secondary", "phonex"),
    ("colocation_secondary", "premisys"),
    ("colocation_secondary", "prime data"),
    ("colocation_secondary", "provision data"),
    ("colocation_secondary", "quonix"),
    ("colocation_secondary", "radiusdc"),
    ("colocation_secondary", "radius dc"),
    ("colocation_secondary", "sba edge"),
    ("colocation_secondary", "sentinel data"),
    ("colocation_secondary", "serverhub"),
    ("colocation_secondary", "servermania"),
    ("colocation_secondary", "simple helix"),
    ("colocation_secondary", "solv"),
    ("colocation_secondary", "synoptek"),
    ("colocation_secondary", "tec"),
    ("colocation_secondary", "thin-nology"),
    ("colocation_secondary", "thinnology"),
    ("colocation_secondary", "telefonica"),
    ("colocation_secondary", "trg datacenters"),
    ("colocation_secondary", "turnkey"),
    ("colocation_secondary", "us secure"),
    ("colocation_secondary", "voonami"),
    ("colocation_secondary", "watch communications"),
    ("colocation_secondary", "whitelabel"),
    ("colocation_secondary", "xyvest"),
    ("colocation_secondary", "360 tcs"),
    ("colocation_secondary", "910telecom"),
    ("colocation_secondary", "binary net"),
    ("colocation_secondary", "carroll"),
    ("colocation_secondary", "apotech"),
    ("colocation_secondary", "aventus"),
    ("colocation_secondary", "datafarm"),
    ("colocation_secondary", "en-us"),
    ("colocation_secondary", "fibertown"),
    ("colocation_secondary", "lytt"),
    ("colocation_secondary", "media temple"),
    ("colocation_secondary", "navisite"),
    ("colocation_secondary", "navgalo"),
    ("colocation_secondary", "navegalo"),
    ("colocation_secondary", "netrat"),
    ("colocation_secondary", "tier"),
    ("colocation_secondary", "tele"),
    ("colocation_secondary", "acronis"),
    ("colocation_secondary", "auros"),
    ("colocation_secondary", "prim"),
    ("colocation_secondary", "enzu"),
    ("colocation_secondary", "cbre"),
    ("colocation_secondary", "cybernest"),
    ("colocation_secondary", "limestone"),
    ("colocation_secondary", "centrilogic"),
    ("colocation_secondary", "mosaic data"),
    ("colocation_secondary", "krypt"),
    ("colocation_secondary", "24shells"),
    ("colocation_secondary", "netdepot"),
    ("colocation_secondary", "cato digital"),
    ("colocation_secondary", "bytegrid"),
    ("colocation_secondary", "xfernet"),
    ("colocation_secondary", "neutron colocation"),
    ("colocation_secondary", "lunavi"),
    ("colocation_secondary", "otava"),
    ("colocation_secondary", "dynascale"),
    ("colocation_secondary", "psychz"),
    ("colocation_secondary", "breezehost"),
    ("colocation_secondary", "data foundry"),
    ("colocation_secondary", "wowrack"),
    ("colocation_secondary", "volico"),
    ("colocation_secondary", "nyi"),
    ("colocation_secondary", "deft"),
    ("colocation_secondary", "prov.net"),
    ("colocation_secondary", "vazata"),
    ("colocation_secondary", "voxility"),
    ("colocation_secondary", "itel networks"),
    ("colocation_secondary", "itel"),
    ("colocation_secondary", "leaseweb"),
    ("colocation_secondary", "latitude.sh"),
    ("colocation_secondary", "dastor"),
    ("colocation_secondary", "hydra"),
    ("colocation_secondary", "netriver"),
    ("colocation_secondary", "dsm"),

    # --- Edge / micro (0.2 MW) ----------------------------------------------
    ("edge_micro", "american tower"),
    ("edge_micro", "edge presence"),
    ("edge_micro", "edgepresence"),
    ("edge_micro", "compass data"),  # smaller Compass edge sites
    ("edge_micro", "dartpoints"),
    ("edge_micro", "dart points"),
    ("edge_micro", "pointone"),
    ("edge_micro", "point one"),
    ("edge_micro", "vapor io"),
    ("edge_micro", "vaporio"),
    ("edge_micro", "ubiquity"),
    ("edge_micro", "ubiq"),
    ("edge_micro", "edge"),  # generic "Edge" — broad but reasonable fallback before telecom
    ("edge_micro", "micro"),
    ("edge_micro", "node"),

    # --- Cable / telecom (5 MW) ---------------------------------------------
    ("cable_telecom", "comcast"),
    ("cable_telecom", "charter"),
    ("cable_telecom", "cox"),
    ("cable_telecom", "at&t"),
    ("cable_telecom", "att "),
    ("cable_telecom", "verizon"),
    ("cable_telecom", "lumen"),  # already matched above as secondary colo; won't reach here
    ("cable_telecom", "china telecom"),
    ("cable_telecom", "cogent"),  # same — already matched
    ("cable_telecom", "telefonica"),
    ("cable_telecom", "centurylink"),
    ("cable_telecom", "sprint"),
    ("cable_telecom", "t-mobile"),
    ("cable_telecom", "tmobile"),
    ("cable_telecom", "vodafone"),
    ("cable_telecom", "orange"),
    ("cable_telecom", "bt "),
    ("cable_telecom", "deutsche telekom"),
    ("cable_telecom", "telia"),
    ("cable_telecom", "telstra"),
    ("cable_telecom", "singtel"),
    ("cable_telecom", "pccw"),
    ("cable_telecom", "telus"),
    ("cable_telecom", "rogers"),
    ("cable_telecom", "bell"),
    ("cable_telecom", "shaw"),
    ("cable_telecom", "videotron"),
    ("cable_telecom", "cogeco"),
    ("cable_telecom", "eastlink"),
    ("cable_telecom", "zayo"),  # already matched above
    ("cable_telecom", "windstream"),
    ("cable_telecom", "frontier"),
    ("cable_telecom", "consolidated"),
    ("cable_telecom", "mediacom"),
    ("cable_telecom", "cable one"),
    ("cable_telecom", "sparklight"),
    ("cable_telecom", "wave"),
    ("cable_telecom", "rcn"),
    ("cable_telecom", "atlantic"),
    ("cable_telecom", "grande"),
    ("cable_telecom", "atlantic broadband"),
    ("cable_telecom", "gtt"),
    ("cable_telecom", "tata"),
    ("cable_telecom", "tata communications"),
    ("cable_telecom", "orange"),
    ("cable_telecom", "globe"),
    ("cable_telecom", "kddi"),
    ("cable_telecom", "ntt communications"),
    ("cable_telecom", "ntt"),
    ("cable_telecom", "iij"),
    ("cable_telecom", "korea telecom"),
    ("cable_telecom", "kt "),
    ("cable_telecom", "lgu"),
    ("cable_telecom", "sk broadband"),
    ("cable_telecom", "sify"),
    ("cable_telecom", "reliance"),
    ("cable_telecom", "bharti"),
    ("cable_telecom", "airtel"),
    ("cable_telecom", "mtn"),
    ("cable_telecom", "saf"),
    ("cable_telecom", "cell"),
    ("cable_telecom", "comms"),
    ("cable_telecom", "c-spire"),
    ("cable_telecom", "cspire"),
    ("cable_telecom", "everstream"),
    ("cable_telecom", "hurricane electric"),

    # --- CDN (0.5 MW) -------------------------------------------------------
    ("cdn_isp", "cloudflare"),
    ("cdn_isp", "fastly"),
    ("cdn_isp", "akamai"),
    ("cdn_isp", "stackpath"),
    ("cdn_isp", "highwinds"),
    ("cdn_isp", "limelight"),
    ("cdn_isp", "edgio"),
    ("cdn_isp", "cdn"),
    ("cdn_isp", "cache"),

    # --- Enterprise self (5 MW) ---------------------------------------------
    ("enterprise_self", "wells fargo"),
    ("enterprise_self", "jpmorgan"),
    ("enterprise_self", "bank of america"),
    ("enterprise_self", "citibank"),
    ("enterprise_self", "goldman"),
    ("enterprise_self", "morgan stanley"),
    ("enterprise_self", "verizon self"),
    ("enterprise_self", "at&t self"),
    ("enterprise_self", "cisco"),
    ("enterprise_self", "sap"),
    ("enterprise_self", "salesforce"),
    ("enterprise_self", "workday"),
    ("enterprise_self", "intuit"),
    ("enterprise_self", "fannie"),
    ("enterprise_self", "freddie"),
    ("enterprise_self", "allstate"),
    ("enterprise_self", "state farm"),
    ("enterprise_self", "ge "),
    ("enterprise_self", "general electric"),
    ("enterprise_self", "boeing"),
    ("enterprise_self", "lockheed"),
    ("enterprise_self", "northrop"),
    ("enterprise_self", "raytheon"),
    ("enterprise_self", "general dynamics"),
    ("enterprise_self", "hertz"),
    ("enterprise_self", "enterprise"),
]


def classify_provider(provider: str) -> tuple[str, str]:
    """Return (class, matched_substring) for a provider name.

    Substring match is case-insensitive. First match wins.
    """
    if not isinstance(provider, str) or not provider:
        return ("unknown", "")
    p = provider.lower()
    for cls, substring in OPERATOR_PATTERNS:
        if substring in p:
            return (cls, substring)
    return ("unknown", "")


def estimate_mw_for_row(row: pd.Series) -> tuple[float, str]:
    """Decide est_mw and mw_source for a single row."""
    disclosed = row.get("MW_total_power")
    flagged = bool(row.get("mw_flagged_outlier", False))

    if pd.notna(disclosed) and not flagged:
        return (float(disclosed), "disclosed")
    if flagged:
        return (np.nan, "outlier_excluded")

    # No disclosed MW and not flagged — fall back to heuristic.
    cls, matched = classify_provider(row.get("provider", ""))
    est = CLASS_DEFAULT_MW[cls]
    if cls == "unknown":
        source = "heuristic:unknown"
    else:
        # Auditability: include the substring that triggered the class.
        source = f"heuristic:{cls}"
    return (est, source)


def main() -> int:
    if not INPUT_CSV.exists():
        print(f"ERROR: input not found: {INPUT_CSV}", file=sys.stderr)
        print("Run src/clean_locations.py first.", file=sys.stderr)
        return 1

    df = pd.read_csv(INPUT_CSV)
    print(f"Loaded {len(df):,} rows from {INPUT_CSV.relative_to(PROJECT_ROOT)}")

    # Apply estimation row-by-row.
    results = df.apply(estimate_mw_for_row, axis=1, result_type="expand")
    results.columns = ["est_mw", "mw_source"]
    df["est_mw"] = results["est_mw"]
    df["mw_source"] = results["mw_source"]

    # ----- Console report ---------------------------------------------------
    print("\n=== Rows by mw_source ===")
    src_counts = df["mw_source"].apply(lambda s: s.split(":")[0]).value_counts()
    print(src_counts.to_string())

    print("\n=== Sum of est_mw (MW) by class ===")
    df_class = df.copy()
    df_class["_class"] = df_class["mw_source"].apply(
        lambda s: s.split(":", 1)[1] if ":" in s else s
    )
    # group disclosed + heuristic together by class label
    def normalize_class(s: str) -> str:
        if s.startswith("heuristic:"):
            return s.split(":", 1)[1]
        if s == "outlier_excluded":
            return "(excluded)"
        return s  # "disclosed"
    df_class["_class"] = df_class["mw_source"].apply(normalize_class)
    by_class = (
        df_class.dropna(subset=["est_mw"])
        .groupby("_class")
        .agg(rows=("est_mw", "size"), total_mw=("est_mw", "sum"), median_mw=("est_mw", "median"))
        .sort_values("total_mw", ascending=False)
    )
    print(by_class.to_string())

    print("\n=== Top 10 providers still classified as 'unknown' ===")
    unknown_mask = df["mw_source"] == "heuristic:unknown"
    unknown_by_provider = (
        df[unknown_mask]
        .groupby("provider")
        .size()
        .sort_values(ascending=False)
        .head(10)
    )
    if len(unknown_by_provider) == 0:
        print("(none — full coverage)")
    else:
        print(unknown_by_provider.to_string())

    # ----- Write output -----------------------------------------------------
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nWrote {len(df):,} rows to {OUTPUT_CSV.relative_to(PROJECT_ROOT)}")
    print(
        f"  est_mw coverage: {df['est_mw'].notna().sum():,} / {len(df):,} "
        f"({df['est_mw'].notna().mean() * 100:.1f}%)"
    )
    print(
        f"  total estimated US DC capacity: "
        f"{df['est_mw'].sum():,.0f} MW"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
