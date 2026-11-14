"""Build the static site in viz/: export claims, wrap data for file:// use, check links.

Usage:
  ~/.venvs/nyc-concordance/bin/python tools/build_site.py            # export, wrap, check
  ~/.venvs/nyc-concordance/bin/python tools/build_site.py --fixture  # also rewrite the fixture
  ~/.venvs/nyc-concordance/bin/python tools/build_site.py --check    # only check links

Steps:
  1. `python -m concord.claims export` writes viz/data/claims.json from
     claims/registered/ and claims/outcomes/.
  2. Each JSON data file the pages read is also written as a small .js file
     that assigns it to a global (window.CONCORD_CLAIMS, window.CONCORD_GRAPHS).
     Browsers refuse fetch() on file:// pages, but they load <script src>, so the
     pages work both when opened from the folder and when served.
  3. Every relative src and href in viz/*.html is resolved against the file
     system. External URLs must be on cdnjs.cloudflare.com with an exact
     version. A link that passes through a symbolic link, an absolute path or a
     missing file fails the build.

The fixture (viz/data/claims.fixture.json) holds six invented claims that
follow the schema in concord/claims.py and cover every verdict. It exists to
test the display. The dashboard shows it only when no real claims exist, or
when asked with ?fixture=1, and always under a banner saying it is invented.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VIZ = ROOT / "viz"
DATA = VIZ / "data"
PY = sys.executable
sys.path.insert(0, str(ROOT))

CDN = re.compile(r"^https://cdnjs\.cloudflare\.com/ajax/libs/[\w.-]+/\d+(\.\d+)+/")


# --------------------------------------------------------------------------- fixture

def _fixture_claims() -> list[dict]:
    from concord import claims as C

    soc = lambda ds, name, upd, q: {"kind": "nyc-open-data", "dataset": ds, "name": name,  # noqa: E731
                                    "url": f"https://data.cityofnewyork.us/d/{ds}", "rows_updated_at": upd,
                                    "query": q, "fetched": "2026-11-12T18:02:11-0500"}
    noaa = {"kind": "noaa-ghcnd", "station": "USW00094728", "dataset": "GHCN-Daily v3 (NCEI), doi:10.7289/V5D21VHZ",
            "url": "https://www.ncei.noaa.gov/pub/data/ghcn/daily/by_station/USW00094728.csv.gz",
            "last_modified": "Thu, 12 Nov 2026 07:41:03 GMT", "fetched": "2026-11-12T18:05:40-0500"}
    sysg = lambda rel, n: {"kind": "sysgraph", "relationship_id": rel, "num_findings": n,  # noqa: E731
                           "api": "https://public-api.system.com v1.0",
                           "dataset_version": "Dataverse v2.1, doi:10.7910/DVN/7V6JDO", "fetched": "2026-11-12T16:20:00-0500"}

    specs = [
        dict(
            reg=dict(id="fixture-trees-surface-heat", kind="confirmation",
                     statement="FIXTURE. Census tracts with more street-tree canopy have lower summer surface temperature.",
                     graph_evidence=[{"relationship_id": "lHLIKbfnYp|mUxSLRMwIy", "concepts": ["street trees", "surface temperature"],
                                      "n_findings": 4, "n_studies": 3, "direction": "-",
                                      "summary": "Invented summary for the fixture.", "pubmed_ids": [31000001, 31000002]}],
                     literature=[], prior=0.7, registrant="fixture",
                     prediction={"direction": "-", "magnitude": "0.3 to 1.5 C cooler per 10 percentage points of canopy",
                                 "support_if": "tract slope below zero with 95% interval excluding zero",
                                 "refute_if": "slope above zero with interval excluding zero"},
                     plan="Invented plan.", alternatives=["income gradient", "distance to water"]),
            out=dict(verdict="confirmed",
                     city_effect={"label": "Surface temperature per 10 pp canopy", "estimate": -0.8, "lo": -1.1, "hi": -0.5,
                                  "scale": "C per 10 pp canopy", "null": 0, "n": 2165},
                     graph_effect={"label": "Correlation of canopy and surface temperature (pooled)", "estimate": -0.45,
                                   "lo": -0.6, "hi": -0.3, "scale": "pearson r", "null": 0},
                     sources=[soc("uvpi-gqnh", "2015 Street Tree Census - Tree Data", "2017-10-04T19:02:13Z",
                                  {"select": "boroct2010, count(tree_id)", "group": "boroct2010"}), sysg("lHLIKbfnYp|mUxSLRMwIy", 4)],
                     prediction_scored="hit: slope negative and inside the registered range",
                     settle="Nothing for the direction; the size depends on the satellite overpass time.",
                     research_needed=[{"question": "Does the cooling hold at street level at night?", "data": "street-level air temperature sensors",
                                       "design": "sensor network across canopy gradient", "priority": "medium"}],
                     notes="Invented outcome for the fixture.")),
        dict(
            reg=dict(id="fixture-heat-ed-visits", kind="confirmation",
                     statement="FIXTURE. Hot days raise emergency-department visits for heat illness in New York City.",
                     graph_evidence=[{"relationship_id": "mUxSLRMwIy|EDvisitXX", "concepts": ["air temperature", "emergency department visits"],
                                      "n_findings": 12, "n_studies": 7, "direction": "+",
                                      "summary": "Invented summary for the fixture.", "pubmed_ids": [31000003]}],
                     literature=[], prior=0.6, registrant="fixture",
                     prediction={"direction": "+", "magnitude": "IRR 1.05 to 1.20 per 5 C",
                                 "support_if": "IRR above 1 with interval excluding 1", "refute_if": "IRR below 1 with interval excluding 1"},
                     plan="Invented plan.", alternatives=["holiday weeks", "reporting changes"]),
            out=dict(verdict="unsettled",
                     city_effect={"label": "ED visits per 5 C daily maximum", "estimate": 1.09, "lo": 0.97, "hi": 1.22,
                                  "scale": "IRR per 5 C", "null": 1, "n": 1840},
                     graph_effect={"label": "Pooled relative risk from graph associations", "estimate": 1.12, "lo": 1.06, "hi": 1.19,
                                   "scale": "IRR per 5 C", "null": 1},
                     sources=[noaa, soc("2nwg-uqyg", "Syndromic surveillance ED visits (invented id)", "2026-11-09T14:00:00Z",
                                        {"select": "date, sum(visits)", "where": "syndrome='heat'", "group": "date"}),
                              sysg("mUxSLRMwIy|EDvisitXX", 12)],
                     prediction_scored="partial: direction as predicted, interval includes 1",
                     settle="Daily counts by ZIP code over more summers would narrow the interval.",
                     research_needed=[{"question": "Who is affected on hot days?", "data": "individual-level ED records with home address",
                                       "design": "case-crossover", "priority": "high"},
                                      {"question": "Is indoor heat the pathway?", "data": "indoor temperature sensors in homes",
                                       "design": "longitudinal panel", "priority": "medium"}],
                     notes="Invented outcome for the fixture.")),
        dict(
            reg=dict(id="fixture-trees-heat-ed-bridge", kind="bridge",
                     statement="FIXTURE. More street trees mean fewer heat emergency visits, through lower local temperature.",
                     graph_evidence=[], literature=[], prior=0.35, registrant="fixture",
                     chain=["fixture-trees-surface-heat", "fixture-heat-ed-visits"],
                     prediction={"direction": "-", "magnitude": "IRR 0.90 to 0.99 per 10 pp canopy",
                                 "support_if": "each link has the right sign", "refute_if": "a link has the wrong sign with interval excluding the null"},
                     plan="Invented plan.", alternatives=["canopy tracks income, and income tracks air conditioning"]),
            out=dict(verdict="bridged",
                     city_effect={"label": "Composed: ED visits per 10 pp canopy", "estimate": 0.96, "lo": 0.90, "hi": 1.02,
                                  "scale": "IRR per 10 pp canopy", "null": 1},
                     graph_effect=None,
                     sources=[noaa],
                     prediction_scored="partial: path composed with the right signs; composed interval includes 1",
                     settle="The weak link is the second: surface temperature is not the air temperature people breathe.",
                     research_needed=[{"question": "Does canopy change the air temperature people are exposed to?",
                                       "data": "street-level air temperature sensors", "design": "paired sensors on shaded and open blocks",
                                       "priority": "high"},
                                      {"question": "Does income explain both canopy and visits?", "data": "individual-level income and AC ownership",
                                       "design": "instrument for canopy (planting programme timing)", "priority": "high"}],
                     notes="Invented outcome for the fixture.")),
        dict(
            reg=dict(id="fixture-heat-shootings", kind="confirmation",
                     statement="FIXTURE. Shootings rise on hotter days in New York City.",
                     graph_evidence=[{"relationship_id": "mUxSLRMwIy|X7hfhwez9f", "concepts": ["air temperature", "gun violence"],
                                      "n_findings": 5, "n_studies": 4, "direction": "+",
                                      "summary": "Invented summary for the fixture.", "pubmed_ids": [31000004, 31000005]}],
                     literature=[], prior=0.55, registrant="fixture",
                     prediction={"direction": "+", "magnitude": "IRR 1.02 to 1.10 per 5 C",
                                 "support_if": "IRR above 1, interval excluding 1", "refute_if": "IRR below 1, interval excluding 1"},
                     plan="Invented plan.", alternatives=["summer school holidays", "daylight hours"]),
            out=dict(verdict="unsettled",
                     city_effect={"label": "Shooting incidents per 5 C daily maximum", "estimate": 0.99, "lo": 0.91, "hi": 1.08,
                                  "scale": "IRR per 5 C", "null": 1, "n": 4380},
                     graph_effect={"label": "Range of graph associations", "estimate": 1.05, "lo": 1.02, "hi": 1.08,
                                   "scale": "IRR per 5 C", "null": 1},
                     sources=[noaa, soc("833y-fsy8", "NYPD Shooting Incident Data (Historic)", "2026-04-23T15:10:02Z",
                                        {"select": "occur_date, count(*)", "group": "occur_date"}), sysg("mUxSLRMwIy|X7hfhwez9f", 5)],
                     prediction_scored="miss: estimate at the null with a wide interval",
                     settle="Season and daylight are confounded with heat; an instrument or within-week design is needed.",
                     research_needed=[{"question": "Is it heat or the summer calendar?", "data": "hourly incident times",
                                       "design": "within-week comparison of unseasonal hot days", "priority": "medium"}],
                     notes="Invented outcome for the fixture.")),
        dict(
            reg=dict(id="fixture-greenspace-asthma", kind="conflict",
                     statement="FIXTURE. Unlike the literature, asthma hospitalisation is higher where tree density is higher in NYC.",
                     graph_evidence=[{"relationship_id": "lHLIKbfnYp|EAshH_Ko3h", "concepts": ["green space", "asthma"],
                                      "n_findings": 9, "n_studies": 6, "direction": "-",
                                      "summary": "Invented summary for the fixture.", "pubmed_ids": [31000006]}],
                     literature=[], prior=0.3, registrant="fixture",
                     prediction={"direction": "+", "magnitude": "rate ratio 1.02 to 1.20 per IQR of tree density",
                                 "support_if": "rate ratio above 1 with interval excluding 1",
                                 "refute_if": "rate ratio below 1 with interval excluding 1"},
                     plan="Invented plan.", alternatives=["pollen", "traffic corridors are also tree-lined"]),
            out=dict(verdict="contested",
                     city_effect={"label": "Asthma hospitalisation per IQR tree density", "estimate": 1.12, "lo": 1.04, "hi": 1.21,
                                  "scale": "rate ratio per IQR", "null": 1, "n": 188},
                     graph_effect={"label": "Pooled odds ratio from graph associations", "estimate": 0.85, "lo": 0.76, "hi": 0.95,
                                   "scale": "odds ratio", "null": 1},
                     sources=[soc("uvpi-gqnh", "2015 Street Tree Census - Tree Data", "2017-10-04T19:02:13Z",
                                  {"select": "zipcode, count(tree_id)", "group": "zipcode"}), sysg("lHLIKbfnYp|EAshH_Ko3h", 9)],
                     prediction_scored="hit: the city data run against the research direction, as registered",
                     settle="Species-level pollen data and individual exposure would separate pollen from green space.",
                     research_needed=[{"question": "Is pollen from particular species the cause?", "data": "species-level pollen sensor data",
                                       "design": "time series across pollen seasons", "priority": "high"},
                                      {"question": "Are tree-lined streets also traffic corridors?", "data": "traffic counts by street segment",
                                       "design": "spatial adjustment", "priority": "medium"}],
                     notes="Invented outcome for the fixture.")),
        dict(
            reg=dict(id="fixture-construction-noise", kind="confirmation",
                     statement="FIXTURE. Construction-noise complaints follow active building permits by community district.",
                     graph_evidence=[{"relationship_id": "36gde7OoEQ|constrXX", "concepts": ["noise pollution", "construction"],
                                      "n_findings": 1, "n_studies": 1, "direction": "+",
                                      "summary": "Invented summary for the fixture.", "pubmed_ids": []}],
                     literature=[], prior=0.5, registrant="fixture",
                     prediction={"direction": "+", "magnitude": "correlation 0.3 to 0.7 across districts",
                                 "support_if": "r above 0 with interval excluding 0", "refute_if": "r below 0 with interval excluding 0"},
                     plan="Invented plan.", alternatives=["complaint propensity differs by district"]),
            out=dict(verdict="no_test",
                     city_effect=None, graph_effect=None,
                     sources=[soc("erm2-nwe9", "311 Service Requests from 2010 to Present", "2026-11-12T09:12:44Z",
                                  {"select": "count(*)", "where": "complaint_type='Noise - Street/Sidewalk'"})],
                     prediction_scored="not scored: the permit data could not be joined at the needed resolution",
                     settle="A permit table with start and end dates by location is needed.",
                     research_needed=[{"question": "Where is construction actually active?", "data": "aerial photographs compared over time",
                                       "design": "image differencing against permits", "priority": "high"}],
                     notes="Invented outcome for the fixture.")),
    ]
    times = ["2026-11-12T16:%02d:00-0500", "2026-11-12T19:%02d:00-0500"]
    out = []
    for i, s in enumerate(specs):
        r = dict(s["reg"])
        r["registered_at"] = times[0] % (10 + i)
        r["sha256"] = C._hash(r)
        o = dict(s["out"])
        o["id"] = r["id"]
        o["figures"] = []
        o["registration_sha256"] = r["sha256"]
        o["decided_at"] = times[1] % (10 + i)
        o["stance"] = C.stance(o.get("city_effect"), r["prediction"]["direction"])
        r["outcome"] = o
        r["hash_ok"] = True
        r["fixture"] = True
        out.append(r)
    return out


def write_fixture() -> Path:
    p = DATA / "claims.fixture.json"
    DATA.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"fixture": True,
                             "notice": "FIXTURE: invented claims for testing the dashboard. These are not findings.",
                             "generated": "fixture", "claims": _fixture_claims()}, indent=1, ensure_ascii=False))
    return p


# --------------------------------------------------------------------------- wrap

def wrap(json_path: Path, js_path: Path, target: str, key: str | None = None):
    d = json.loads(json_path.read_text())
    body = json.dumps(d, ensure_ascii=False, separators=(",", ":"))
    if key is None:
        js = f"window.{target}={body};\n"
    else:
        js = f"window.{target}=window.{target}||{{}};window.{target}[{json.dumps(key)}]={body};\n"
    js_path.write_text(js)


def build_data():
    r = subprocess.run([PY, "-m", "concord.claims", "export"], cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"claims export failed:\n{r.stderr}")
    claims = DATA / "claims.json"
    n = len(json.loads(claims.read_text())["claims"])
    print(f"exported {n} claims -> {claims.relative_to(ROOT)}")
    wrap(claims, DATA / "claims.js", "CONCORD_CLAIMS")
    fx = DATA / "claims.fixture.json"
    if not fx.exists():
        write_fixture()
    wrap(fx, DATA / "claims.fixture.js", "CONCORD_FIXTURE")
    gdir = DATA / "graph"
    if gdir.exists():
        for f in sorted(gdir.glob("*.json")):
            key = "index" if f.name == "index.json" else f.stem
            wrap(f, f.with_suffix(".js"), "CONCORD_GRAPHS", key)
        print(f"wrapped {len(list(gdir.glob('*.json')))} graph files")


# --------------------------------------------------------------------------- check

class Refs(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []

    def handle_starttag(self, tag, attrs):
        for k, v in attrs:
            if k in ("src", "href") and v is not None:
                self.refs.append((tag, k, v))


def _no_symlink(base: Path, target: Path) -> bool:
    p = target
    while True:
        if p.is_symlink():
            return False
        if p == base or p.parent == p:
            return True
        p = p.parent


def check() -> int:
    bad = 0
    for page in sorted(VIZ.glob("*.html")):
        text = page.read_text()
        if re.search(r"(/Users/|/Volumes/|file:///)", text):
            print(f"FAIL {page.name}: absolute path in page")
            bad += 1
        parser = Refs()
        parser.feed(text)
        # src attributes set from script, e.g. "data/graph/x.js", are checked through the index
        for tag, attr, v in parser.refs:
            if v.startswith(("#", "mailto:", "javascript:")) or v == "":
                continue
            if v.startswith(("http://", "https://", "//")):
                if tag == "script" or (tag == "link" and attr == "href" and v.endswith(".css")):
                    if not CDN.match(v):
                        print(f"FAIL {page.name}: {tag} {attr}={v} is not a pinned cdnjs URL")
                        bad += 1
                continue
            if v.startswith("/"):
                print(f"FAIL {page.name}: root-absolute {attr}={v}")
                bad += 1
                continue
            path = v.split("#")[0].split("?")[0]
            t = (page.parent / path)
            if not t.exists():
                print(f"FAIL {page.name}: {attr}={v} does not exist")
                bad += 1
            elif not _no_symlink(VIZ, t):
                print(f"FAIL {page.name}: {attr}={v} passes through a symbolic link")
                bad += 1
    idx = DATA / "graph" / "index.json"
    if idx.exists():
        for it in json.loads(idx.read_text())["subgraphs"]:
            js = VIZ / it["file"].replace(".json", ".js")
            if not js.exists():
                print(f"FAIL explorer data {it['file']}: no .js wrapper")
                bad += 1
    for f in DATA.rglob("*"):
        if f.is_file() and f.suffix in (".js", ".json") and re.search(r"/Users/|/Volumes/", f.read_text()):
            print(f"FAIL {f.relative_to(ROOT)}: absolute path in data")
            bad += 1
    print("links ok" if not bad else f"{bad} problems")
    return bad


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fixture", action="store_true", help="rewrite viz/data/claims.fixture.json")
    ap.add_argument("--check", action="store_true", help="only check links")
    a = ap.parse_args(argv)
    if a.fixture:
        print(f"wrote {write_fixture().relative_to(ROOT)}")
    if not a.check:
        build_data()
    sys.exit(1 if check() else 0)


if __name__ == "__main__":
    main()
