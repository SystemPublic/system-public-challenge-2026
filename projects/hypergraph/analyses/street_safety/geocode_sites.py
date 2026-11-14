"""Attach coordinates to red-light camera intersections (rlc_sites.json) from the OSM intersection
gazetteer, then the LPI gazetteer; add boroughs to the LPI gazetteer. No crash data are read.
Writes data/derived/street_safety/rlc_sites_geo.json and updates lpi_gazetteer.json with 'boro'."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "analyses/street_safety"))
from osm_intersections import boroughs, boro_of  # noqa: E402

DER = ROOT / "data/derived/street_safety"


def variants(x):
    v = {x}
    for a, b in ((" AVE S", " AVE"), (" BLVD S", " BLVD"), (" BLVD N", " BLVD"), (" RD S", " RD"), (" RD N", " RD")):
        if x.endswith(a):
            v.add(x[: -len(a)] + b)
    if x.startswith("AVE ") and len(x) <= 6:
        v.add(x)
    return v


def main():
    sd = json.loads((DER / "rlc_sites.json").read_text())
    osm = json.loads((DER / "osm_intersections.json").read_text())["pairs"]
    gz = json.loads((DER / "lpi_gazetteer.json").read_text())
    polys = boroughs()
    for r in gz["rows"]:
        if "boro" not in r:
            r["boro"] = boro_of(r["lat"], r["lon"], polys)
    (DER / "lpi_gazetteer.json").write_text(json.dumps(gz, indent=1))
    lpi = {}
    for r in gz["rows"]:
        lpi.setdefault((r["boro"],) + tuple(sorted((r["a"], r["b"]))), r)
    n_osm = n_lpi = 0
    for s in sd["sites"]:
        hit = None
        for a in variants(s["a"]):
            for b in variants(s["b"]):
                k = "|".join(sorted((a, b)))
                for c in osm.get(k, []):
                    if c.get("boro") == s["boro"]:
                        hit = (c, "osm"); break
                if hit: break
                r = lpi.get((s["boro"],) + tuple(sorted((a, b))))
                if r:
                    hit = (r, "lpi-gazetteer"); break
            if hit: break
        if hit:
            s["lat"], s["lon"], s["geo"] = hit[0]["lat"], hit[0]["lon"], hit[1]
            n_osm += hit[1] == "osm"; n_lpi += hit[1] != "osm"
        else:
            s["lat"] = s["lon"] = None; s["geo"] = None
    # merge sites that geocode to within 60 m of each other (approaches of one intersection)
    sd["geocode"] = {"osm": n_osm, "lpi": n_lpi, "none": sum(1 for s in sd["sites"] if s["lat"] is None)}
    (DER / "rlc_sites_geo.json").write_text(json.dumps(sd, indent=1))
    print(sd["geocode"], "of", len(sd["sites"]))


if __name__ == "__main__":
    main()
