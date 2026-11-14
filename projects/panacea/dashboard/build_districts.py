#!/usr/bin/env python3
"""Build web/data/districts.json: UHF42 district geometry + values for every
measure the web dashboard draws district heatmaps for — the bridge measures
plus the city-check measures behind each confirmation pair's ρ.

Reads insights/out/bridges.csv and web/data/bundle.json (confirmation chk
measures) for the measure ids; downloads the two needed Underlay bulk files
into nyc_open_data/data/ (gitignored cache, re-download per
nyc_open_data/README.md); exports, per measure, the first-seen UHF42
observation per district — exactly the pivot semantics
(pivot_table(aggfunc="first")) the city ρ was computed with, so each map
shows the same values the ρ summarizes. Time period and reliability flag
ride along per value. Spearman parity is asserted for every bridge row and
every ρ-bearing confirmation pair.

Run: python3 -I dashboard/build_districts.py   (first run downloads ~150 MB)
"""
import gzip
import json
import subprocess
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent.parent
NYC = BASE / "nyc_open_data" / "data"
WEB = BASE / "web" / "data"
BRIDGES = BASE / "insights" / "out" / "bridges.csv"
API = "https://www.underlay.org/api/collections/nyc"
VERSIONS = {"environment-health": "v1.0.0", "geographies": "v1.0.0"}
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) spg-dashboard-build"


def log(msg):
    print(msg, flush=True)


def ensure_bulk(slug):
    """Download <slug>.v1.0.0.records.ndjson.gz into the cache if missing."""
    d = NYC / slug
    d.mkdir(parents=True, exist_ok=True)
    f = d / f"{slug}.v1.0.0.records.ndjson.gz"
    if f.exists() and f.stat().st_size > 0:
        log(f"  cached: {f.name} ({f.stat().st_size / 1e6:.0f} MB)")
        return f
    url = f"{API}/{slug}/versions/{VERSIONS[slug]}/records.ndjson.gz"
    log(f"  downloading {slug} ...")
    subprocess.run(["curl", "-L", "--fail", "--silent", "--show-error",
                    "--user-agent", UA, "-o", str(f), url], check=True)
    log(f"  done: {f.name} ({f.stat().st_size / 1e6:.0f} MB)")
    return f


def round_geom(coords, nd=4):
    """Round coordinates and normalize Polygon/MultiPolygon geometry to
    polygons -> rings -> [lon, lat] (always three nesting levels)."""

    def rd(c):
        if isinstance(c[0], (int, float)):               # one [lon, lat]
            return [round(c[0], nd), round(c[1], nd)]
        return [rd(p) for p in c]

    out = rd(coords)
    if isinstance(out[0][0][0], (int, float)):           # Polygon: wrap to MultiPolygon
        out = [out]
    return out


# ---------------------------------------------------------------- needed measures
bridges = pd.read_csv(BRIDGES)
# the same 12 rows build_dashboard.py ships: non-modeled, |rho| desc, stable
obs = bridges[~(bridges.modeled1 | bridges.modeled2)]
obs = obs.reindex(obs.city_spearman_uhf42.abs().sort_values(
    ascending=False, kind="stable").index)
bridges = obs.head(12).reset_index(drop=True)
measures = set(bridges.measure1) | set(bridges.measure2)
n_bridge_measures = len(measures)

# the confirmation pairs' city-check measures (web/data/bundle.json, built by
# build_dashboard.py) — the row-popup correlation maps draw these
bundle = json.loads((WEB / "bundle.json").read_text())
rho_pairs = []                      # ([m1, m2], rho) for parity assertions
for r in bundle["confirmations"]:
    if not r["chk"]:
        continue
    m = [c[len("ehdp:"):] if c.startswith("ehdp:") else c for c in r["chk"]]
    measures.update(m)
    if r["rho"] is not None:
        rho_pairs.append((m, r["rho"]))
measures = sorted(measures)
log(f"Measures: {n_bridge_measures} bridge + "
    f"{len(measures) - n_bridge_measures} confirmation-check = {len(measures)} "
    f"({len(rho_pairs)} rho pairs to parity-check)")

# ---------------------------------------------------------------- EHDP stream
ehdp = ensure_bulk("environment-health")
tp_label = {}                       # "timeperiod:N" -> label
vals = {m: {} for m in measures}    # measure -> district id -> first-seen obs
n_obs = 0
log("Streaming EHDP records (Observation + TimePeriod)...")
with gzip.open(ehdp, "rt") as fh:
    for line in fh:
        if '"type":"TimePeriod"' in line:
            d = json.loads(line)
            tp_label[d["id"]] = d["data"].get("label", d["id"])
            continue
        if '"type":"Observation"' not in line:
            continue
        d = json.loads(line)["data"]
        if d.get("geoType") != "UHF42" or d["measureId"] not in vals:
            continue
        v = d.get("value")
        if not isinstance(v, (int, float)):
            continue
        slot = vals[d["measureId"]].get(d["geographyId"])
        if slot is None:                # first-seen, matches aggfunc="first"
            n_obs += 1
            vals[d["measureId"]][d["geographyId"]] = {
                "v": v, "tp": d.get("timePeriodId", ""),
                "rel": d.get("reliability", ""),
            }
log(f"  {n_obs} UHF42 observations kept across {len(measures)} measures")

# ---------------------------------------------------------------- geography stream
geo_f = ensure_bulk("geographies")
districts = {}                      # record id -> district dict
log("Streaming geography records (Geography)...")
with gzip.open(geo_f, "rt") as fh:
    for line in fh:
        if '"type":"Geography"' not in line:
            continue
        d = json.loads(line)
        g = d["data"]
        if g.get("geoType") != "UHF42":
            continue
        districts[d["id"]] = {
            "id": d["id"],
            "name": g.get("name"),
            "lat": g.get("latitude"), "lon": g.get("longitude"),
            "polys": round_geom(g["geometry"]["coordinates"]),
        }
log(f"  {len(districts)} UHF42 districts")
assert len(districts) == 42, f"expected 42 UHF42 districts, got {len(districts)}"

missing = []
for m in measures:
    n = len(set(vals[m]) & set(districts))
    if n < 25:
        missing.append((m, n))
assert not missing, f"measures with too few districts: {missing}"

# ---------------------------------------------------------------- verify + write
# Spearman on exported values must reproduce bridges.csv ρ (pivot parity)
piv = {m: pd.Series({g: rec["v"] for g, rec in vals[m].items()})
       for m in measures}
checked = 0
for _, r in bridges.iterrows():
    j = pd.concat([piv[r.measure1], piv[r.measure2]],
                  axis=1, keys=["a", "b"]).dropna()
    if len(j) < 25:
        continue
    rho = j.a.corr(j.b, method="spearman")
    # bridges.csv stores ρ rounded to 3 decimals
    assert round(rho, 3) == round(float(r.city_spearman_uhf42), 3), \
        f"rho mismatch {r.measure1} x {r.measure2}: {rho} vs {r.city_spearman_uhf42}"
    checked += 1
log(f"  Spearman parity verified for {checked}/{len(bridges)} bridge rows")

# confirmation pairs: exported values must reproduce the bundle's ρ, since the
# popup maps render exactly these values next to that ρ
pair_checked = 0
for chk, rho in rho_pairs:
    j = pd.concat([piv[chk[0]], piv[chk[1]]],
                  axis=1, keys=["a", "b"]).dropna()
    assert len(j) >= 25, f"too few districts for {chk}: {len(j)}"
    rho2 = j.a.corr(j.b, method="spearman")
    assert round(rho2, 3) == round(rho, 3), \
        f"rho mismatch {chk[0]} x {chk[1]}: {rho2} vs {rho}"
    pair_checked += 1
log(f"  Spearman parity verified for {pair_checked}/{len(rho_pairs)} "
    f"confirmation pairs")

# TimePeriod records stream after Observations — map labels now that the
# index is complete
for m in vals:
    for rec in vals[m].values():
        rec["tp"] = tp_label.get(rec["tp"], "")
n_unlabeled = sum(1 for m in vals for rec in vals[m].values() if not rec["tp"])
log(f"  {n_unlabeled} values without a time-period label")

out = {
    "districts": [districts[k] for k in sorted(districts)],
    "values": vals,
}
WEB.mkdir(parents=True, exist_ok=True)
dest = WEB / "districts.json"
dest.write_text(json.dumps(out, separators=(",", ":")))
log(f"Done: {dest} ({dest.stat().st_size / 1e3:.0f} KB), "
    f"{len(tp_label)} time periods indexed")
