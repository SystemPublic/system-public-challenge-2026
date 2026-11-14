"""Routed contact -> patient travel times and the spec §4.4a eligibility rule.

Input : data/processed/synthetic/contacts.csv (contact lat/lon, naive placeholder columns),
        data/processed/synthetic/patients.csv (home lat/lon),
        data/processed/subway_stations_nyc.geojson (496 MTA GTFS parent stations).
Output: data/processed/synthetic/contacts_routed.csv (one row per contact),
        data/raw/routing/contacts_summary.json (patient-level counts, real vs naive).

Modes
Routing engine: see routing_common.py. ORS Matrix (foot-walking / driving-car) when a usable
ORS key is available, else the public FOSSGIS OSRM servers (routed-foot / routed-car, same
OpenStreetMap road network). The engine actually used is written to the routing_engine column.
Column names keep the "ors" prefix for the routed values whichever engine produced them.

- walk:  routed foot network (contact -> patient home). The engine's own duration assumes an
         adult pace (~5 km/h); we keep it (walk_ors_min) but use an older-adult pace for the rule:
         walk_min = routed walking distance / 0.8 m/s (Western et al. 2025, PMC12682371).
- drive: routed car network. Free-flow duration (no live traffic, no parking time), so it is
         an optimistic lower bound for the Bronx.
- transit_approx: APPROXIMATE, NOT GTFS ROUTING. Walk (straight-line x 1.3 detour at 0.8 m/s)
         to the station nearest the contact + 5 min assumed wait + straight-line distance
         between that station and the station nearest the patient at an assumed 20 km/h
         effective subway speed + walk (same rule) to the patient. Computed only when both
         nearest stations are within 1.5 km straight line and differ; no line connectivity or
         transfer check. ORS has no public-transit profile.

Eligibility (spec §4.4a.5): T_travel <= T_max - p90(patient) - p90(contact), with the
starting budgets T_max = 45 (very high risk), 60 (high), 90 (medium) min and the default
p90 = 15 min each (the same assumption contacts.csv generator A14 used), i.e. travel
allowance 15 / 30 / 60 min. Fastest mode = min over the available modes. Because whether a
contact has a car is unknown, a second set of flags uses walk/transit only (no car).

Run: ~/.local/bin/uv run python scripts/routing_contacts.py
"""
import json, os, statistics
from routing_common import (engine, BUDGETS, MAX_PAIRS, OLDER_WALK_MPS, P90_CONTACT_MIN, P90_PATIENT_MIN,
                            PROCESSED, RAW, STATS, SYN, fmt, haversine_m, ors_matrix, read_csv,
                            write_csv)

DETOUR = 1.3
WAIT_MIN = 5.0
SUBWAY_KMH = 20.0
STATION_MAX_M = 1500
CHUNK = 50  # 50 contacts x <=50 patients = 2,500 pairs < 3,500


def route_pairs(profile, pairs):
    """pairs: list of (cid, (lat,lon) origin, (lat,lon) dest). Returns cid -> (dur_s, dist_m, snap_o, snap_d)."""
    out = {}
    for i in range(0, len(pairs), CHUNK):
        chunk = pairs[i:i + CHUNK]
        locs, src, dst, dest_idx = [], [], [], {}
        for _, o, _d in chunk:
            src.append(len(locs)); locs.append((o[1], o[0]))
        for _, _o, d in chunk:
            if d not in dest_idx:
                dest_idx[d] = len(locs); locs.append((d[1], d[0])); dst.append(dest_idx[d])
        assert len(src) * len(dst) <= MAX_PAIRS
        resp = ors_matrix(profile, locs, src, dst)
        col = {li: j for j, li in enumerate(dst)}
        for row, (cid, o, d) in enumerate(chunk):
            j = col[dest_idx[d]]
            dur = resp["durations"][row][j]
            dis = resp["distances"][row][j]
            so = (resp.get("sources") or [{}] * len(src))[row].get("snapped_distance")
            sd = (resp.get("destinations") or [{}] * len(dst))[j].get("snapped_distance")
            out[cid] = (dur, dis, so, sd)
    return out


def main():
    patients = {p["patient_id"]: p for p in read_csv("patients.csv")}
    contacts = read_csv("contacts.csv")
    stations = json.load(open(os.path.join(PROCESSED, "subway_stations_nyc.geojson")))["features"]
    st = [(f["properties"]["stop_name"], f["properties"].get("routes", ""),
           f["geometry"]["coordinates"][1], f["geometry"]["coordinates"][0]) for f in stations]

    def nearest_station(lat, lon):
        return min(((haversine_m(lat, lon, s[2], s[3]), s) for s in st), key=lambda t: t[0])

    pairs = []
    for c in contacts:
        p = patients[c["patient_id"]]
        pairs.append((c["contact_id"], (float(c["lat"]), float(c["lon"])),
                      (float(p["home_lat"]), float(p["home_lon"]))))
    # Walking only makes sense inside NYC; out_of_area contacts (31, 40-100+ km) get driving only.
    walk_pairs = [x for x, c in zip(pairs, contacts) if c["location_type"] != "out_of_area"]
    walk = route_pairs("foot-walking", walk_pairs)
    drive = route_pairs("driving-car", pairs)

    rows = []
    for (cid, o, d), c in zip(pairs, contacts):
        r = dict(c)
        w = walk.get(cid)
        dr = drive.get(cid)
        r["walk_ors_dist_km"] = fmt(w[1] / 1000, 3) if w and w[1] is not None else ""
        r["walk_ors_min"] = fmt(w[0] / 60) if w and w[0] is not None else ""
        walk_min = (w[1] / OLDER_WALK_MPS / 60) if w and w[1] is not None else None
        r["walk_older_pace_min"] = fmt(walk_min)
        drive_min = (dr[0] / 60) if dr and dr[0] is not None else None
        r["drive_ors_dist_km"] = fmt(dr[1] / 1000, 3) if dr and dr[1] is not None else ""
        r["drive_ors_min"] = fmt(drive_min)
        snaps = [x for x in ((w[2], w[3]) if w else ()) + ((dr[2], dr[3]) if dr else ()) if x is not None]
        r["max_snap_m"] = fmt(max(snaps), 0) if snaps else ""
        # transit approximation
        transit_min = None
        if c["location_type"] != "out_of_area":
            da, sa = nearest_station(*o)
            db, sb = nearest_station(*d)
            if da <= STATION_MAX_M and db <= STATION_MAX_M and sa != sb:
                ride_m = haversine_m(sa[2], sa[3], sb[2], sb[3])
                transit_min = ((da + db) * DETOUR / OLDER_WALK_MPS / 60 + WAIT_MIN
                               + ride_m / 1000 / SUBWAY_KMH * 60)
                r["transit_from_station"] = f"{sa[0]} ({sa[1]})"
                r["transit_to_station"] = f"{sb[0]} ({sb[1]})"
        r["transit_approx_min"] = fmt(transit_min)
        modes = {"walk": walk_min, "drive": drive_min, "transit_approx": transit_min}
        avail = {k: v for k, v in modes.items() if v is not None}
        nocar = {k: v for k, v in avail.items() if k != "drive"}
        if avail:
            m = min(avail, key=avail.get)
            r["fastest_mode"], r["fastest_min"] = m, fmt(avail[m])
        if nocar:
            m = min(nocar, key=nocar.get)
            r["fastest_nocar_mode"], r["fastest_nocar_min"] = m, fmt(nocar[m])
        for b in BUDGETS:
            allow = b - P90_PATIENT_MIN - P90_CONTACT_MIN
            r[f"travel_allowance_{b}"] = allow
            r[f"qualifies_{b}"] = str(bool(avail) and min(avail.values()) <= allow).lower()
            r[f"qualifies_nocar_{b}"] = str(bool(nocar) and min(nocar.values()) <= allow).lower()
            r[f"naive_qualifies_{b}min_derived"] = str(float(c["naive_travel_min"]) <= allow).lower()
        r["routing_engine"] = engine()
        r["routing_note"] = ("out_of_area: driving only" if c["location_type"] == "out_of_area" else "")
        if r["max_snap_m"] != "" and float(r["max_snap_m"]) > 200:
            r["routing_note"] = (r["routing_note"] + "; " if r["routing_note"] else "") + \
                "point snapped >200 m to the road network (contact location may be in water/park)"
        if c["location_type"] == "same_building":
            r["routing_note"] = "; ".join(x for x in (r["routing_note"],
                "same building: routed time is street-to-street snapping, real trip is stairs/elevator") if x)
        if not avail:
            r["routing_note"] = "; ".join(x for x in (r["routing_note"], "no route found") if x)
        rows.append(r)

    fields = list(contacts[0].keys()) + [
        "walk_ors_dist_km", "walk_ors_min", "walk_older_pace_min", "drive_ors_dist_km", "drive_ors_min",
        "transit_approx_min", "transit_from_station", "transit_to_station", "fastest_mode", "fastest_min",
        "fastest_nocar_mode", "fastest_nocar_min"]
    for b in BUDGETS:
        fields += [f"travel_allowance_{b}", f"qualifies_{b}", f"qualifies_nocar_{b}",
                   f"naive_qualifies_{b}min_derived"]
    fields += ["max_snap_m", "routing_engine", "routing_note"]
    write_csv(os.path.join(SYN, "contacts_routed.csv"), rows, fields)

    # patient-level summary
    by_p = {pid: [] for pid in patients}
    for r in rows:
        by_p[r["patient_id"]].append(r)
    summ = {"patients": len(patients), "contacts": len(rows),
            "patients_with_zero_contacts": sum(1 for v in by_p.values() if not v),
            "assumption_p90_patient_min": P90_PATIENT_MIN, "assumption_p90_contact_min": P90_CONTACT_MIN,
            "budgets": {}}
    for b in BUDGETS:
        real = {pid: any(x[f"qualifies_{b}"] == "true" for x in v) for pid, v in by_p.items()}
        nocar = {pid: any(x[f"qualifies_nocar_{b}"] == "true" for x in v) for pid, v in by_p.items()}
        naive = {pid: any(x[f"naive_qualifies_{b}min_derived"] == "true" for x in v) for pid, v in by_p.items()}
        summ["budgets"][b] = {
            "travel_allowance_min": b - P90_PATIENT_MIN - P90_CONTACT_MIN,
            "no_qualifying_contact_real": sum(not x for x in real.values()),
            "no_qualifying_contact_real_nocar": sum(not x for x in nocar.values()),
            "no_qualifying_contact_naive": sum(not x for x in naive.values()),
            "patients_status_changed": sum(real[p] != naive[p] for p in patients),
            "lost_qualifying_contact": sum(naive[p] and not real[p] for p in patients),
            "gained_qualifying_contact": sum(real[p] and not naive[p] for p in patients),
            "contacts_qualifying_real": sum(x[f"qualifies_{b}"] == "true" for x in rows),
            "contacts_qualifying_naive": sum(x[f"naive_qualifies_{b}min_derived"] == "true" for x in rows),
        }
    # sanity: derived naive flags vs the original columns
    for b in (60, 90):
        summ[f"naive_derived_matches_original_{b}"] = all(
            r[f"naive_qualifies_{b}min_derived"] == r[f"naive_qualifies_{b}min"] for r in rows)
    ratios = [float(r["fastest_min"]) / float(r["naive_travel_min"]) for r in rows
              if r.get("fastest_min") not in ("", None) and float(r["naive_travel_min"]) > 0]
    summ["median_ratio_real_fastest_to_naive"] = round(statistics.median(ratios), 2)
    summ["fastest_mode_counts"] = {m: sum(1 for r in rows if r.get("fastest_mode") == m)
                                   for m in ("walk", "drive", "transit_approx")}
    summ["contacts_snapped_over_200m"] = sum(1 for r in rows if "snapped" in r["routing_note"])
    summ["routing_engine"] = engine()
    summ["requests"] = dict(STATS)
    with open(os.path.join(RAW, "contacts_summary.json"), "w") as fh:
        json.dump(summ, fh, indent=2)
    print(json.dumps(summ, indent=2))


if __name__ == "__main__":
    main()
