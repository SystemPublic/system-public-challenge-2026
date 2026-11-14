"""Red-light camera sites and activation dates from Parking Violations Issued (violation code 7),
and a gazetteer of signalized intersections from the LPI dataset (xc4v-ntf4).
Treatment data only: no crash data are read here.
Writes data/derived/street_safety/rlc_sites.json and lpi_gazetteer.json."""
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import socrata as s

PV = {"FY2024": "8zf9-spf8", "FY2025": "m5vz-tzqv", "FY2026": "9mwx-gamw", "FY2027": "pvqr-7yc4"}
BORO = {"MN": "MANHATTAN", "NY": "MANHATTAN", "BK": "BROOKLYN", "K": "BROOKLYN", "QN": "QUEENS", "Q": "QUEENS",
        "BX": "BRONX", "R": "STATEN ISLAND", "ST": "STATEN ISLAND"}

ABBR = [(r"\bAVENUE\b", "AVE"), (r"\bAV\b", "AVE"), (r"\bSTREET\b", "ST"), (r"\bBOULEVARD\b", "BLVD"),
        (r"\bROAD\b", "RD"), (r"\bPARKWAY\b", "PKWY"), (r"\bPLACE\b", "PL"), (r"\bDRIVE\b", "DR"),
        (r"\bEXPRESSWAY\b", "EXPY"), (r"\bEXPWY\b", "EXPY"), (r"\bHIGHWAY\b", "HWY"), (r"\bTURNPIKE\b", "TPKE"),
        (r"\bEAST\b", "E"), (r"\bWEST\b", "W"), (r"\bNORTH\b", "N"), (r"\bSOUTH\b", "S"),
        (r"\bLANE\b", "LN"), (r"\bCOURT\b", "CT"), (r"\bTERRACE\b", "TER"), (r"\bSAINT\b", "ST"),
        (r"\bCONCOURSE\b", "CONC"), (r"\bSQUARE\b", "SQ")]


def norm(x: str) -> str:
    x = (x or "").upper()
    x = re.sub(r"(\d+)(ST|ND|RD|TH)(?=[A-Z])", r"\1\2 ", x)     # 18THAVE -> 18TH AVE
    x = re.sub(r"\bSO\b", "S", x)
    x = re.sub(r"\bSVC ?RD\b|\bSERVICE RD\b|\bSVCRD\b", " ", x)
    x = re.sub(r"\((?:[NSEW]/?B|[NSEW]B)[^)]*\)?", " ", x)       # (E/B), (N/B
    x = re.sub(r"\b(?:[NSEW]B|[NSEW]/B)\b", " ", x)               # leading WB, EB
    x = re.sub(r"\bOFF ?RAMP\b|\bON ?RAMP\b|\bRAMP\b|\bEXIT\b|\bENTRANCE\b", " ", x)
    x = re.sub(r"[^A-Z0-9 ]", " ", x)
    for a, b in ABBR:
        x = re.sub(a, b, x)
    x = re.sub(r"\b(\d+)(ST|ND|RD|TH)\b", r"\1", x)               # 77TH -> 77
    return re.sub(r"\s+", " ", x).strip()


def split_site(street, inter):
    full = f"{street or ''}{inter or ''}"
    if "@" not in full:
        return None
    a, b = full.split("@", 1)
    return norm(a), norm(b)


def main():
    by = {}
    srcs = []
    # Grouped queries on these tables time out on the server (13 Nov 2026), so raw ticket rows are read
    # for sampled days (the 1st and 15th of each month) and counted here. Before June 2025 one
    # month per quarter is sampled, only to mark cameras that existed before the expansion; from June
    # 2025 every month is sampled, so the first month in which each new site issues tickets is known
    # (to within the sampling: an activation after the 15th shows in the next month, which the
    # analysis drops as the activation month).
    import calendar
    FY = lambda y, m: {2023: "8zf9-spf8", 2024: "8zf9-spf8" if m <= 6 else "m5vz-tzqv",
                       2025: "m5vz-tzqv" if m <= 5 else "9mwx-gamw", 2026: "9mwx-gamw" if m <= 5 else "pvqr-7yc4"}[y]
    months = ["2023-09", "2023-12", "2024-03", "2024-05", "2024-08", "2024-11", "2025-02", "2025-05"]
    months += [f"{y}-{m:02d}" for y in (2025, 2026) for m in range(1, 13) if "2025-06" <= f"{y}-{m:02d}" <= "2026-08"]
    for ym in months:
        y, m = int(ym[:4]), int(ym[5:])
        ds = [FY(y, m)]
        if m == 6 and y >= 2024:   # June tickets are split between two fiscal-year tables
            ds = [{2024: "8zf9-spf8", 2025: "m5vz-tzqv", 2026: "9mwx-gamw"}[y], {2024: "m5vz-tzqv", 2025: "9mwx-gamw", 2026: "pvqr-7yc4"}[y]]
        rows = []
        for day, d in [(dd, d) for dd in (1, 15) for d in ds]:
            rr, src = s.query(d, select="street_name, intersecting_street, violation_county",
                              where=f"violation_code='7' and issue_date = '{ym}-{day:02d}T00:00:00'", limit=50000)
            srcs.append(src)
            rows.extend(rr)
        print(ds, ym, len(rows), flush=True)
        for r in rows:
            r["n"] = 1
        for r in rows:
            sp = split_site(r.get("street_name"), r.get("intersecting_street"))
            if not sp or not sp[0] or not sp[1]:
                continue
            boro = BORO.get(r.get("violation_county", ""), r.get("violation_county"))
            key = (boro,) + tuple(sorted(sp))
            e = by.setdefault(key, {"boro": boro, "a": sp[0], "b": sp[1], "first": ym, "last": ym, "months": {}, "raw": set()})
            e["first"] = min(e["first"], ym); e["last"] = max(e["last"], ym)
            e["months"][ym] = e["months"].get(ym, 0) + int(r["n"])
            e["raw"].add(f"{r.get('street_name')}|{r.get('intersecting_street')}")
    sites = []
    for e in by.values():
        e["raw"] = sorted(e["raw"])
        sites.append(e)
    # gazetteer
    g, gsrc = s.query("xc4v-ntf4", select="main_street, cross_stree, install_da, lat, long", limit=50000)
    gaz = [{"a": norm(r.get("main_street")), "b": norm(r.get("cross_stree")), "lat": float(r["lat"]), "lon": float(r["long"]),
            "lpi_installed": (r.get("install_da") or "")[:10]} for r in g if r.get("lat")]
    idx = {}
    for i, r in enumerate(gaz):
        idx.setdefault(tuple(sorted((r["a"], r["b"]))), []).append(i)
    hit = 0
    for e in sites:
        k = tuple(sorted((e["a"], e["b"])))
        if k in idx:
            r = gaz[idx[k][0]]
            e["lat"], e["lon"], e["geo"] = r["lat"], r["lon"], "lpi-gazetteer"
            hit += 1
    out = ROOT / "data/derived/street_safety"
    out.mkdir(parents=True, exist_ok=True)
    (out / "rlc_sites.json").write_text(json.dumps({"sources": srcs, "sites": sites}, indent=1))
    (out / "lpi_gazetteer.json").write_text(json.dumps({"source": gsrc, "rows": gaz}, indent=1))
    print("sites", len(sites), "geocoded via LPI", hit, "LPI rows", len(gaz))


if __name__ == "__main__":
    main()
