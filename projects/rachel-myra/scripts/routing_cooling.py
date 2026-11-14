"""Nearest 3 indoor cooling places per synthetic patient, by routed walking time (spec §4.4 item 3).

Input : data/processed/synthetic/patients.csv (home lat/lon, age),
        data/processed/synthetic/questionnaire.csv (mobility_step_free_needed, q5_can_reach_cool_place),
        data/processed/cooling_places_nyc.geojson (place agent output: Cool Options, rec centers,
        libraries, OSM community centres / malls / department stores),
        data/processed/replay_heatwave_hourly.csv (to pick the reference heat day).
Output: data/processed/synthetic/cooling_match.csv (3 rows per patient, rank 1-3),
        data/raw/routing/cooling_summary.json.

Method
1. Candidate places: indoor only (outdoor spray showers and pools are excluded; they are also
   CLOSED for the season in the source), with a street address (the text must include one;
   mostly drops OSM shops/community centres without addr:* tags).
2. Reference day: the replay day with the highest heat index in replay_heatwave_hourly.csv
   (2025-06-23, a Monday). Hours are read for that weekday: Cool Options / rec-center per-day
   strings ("8a-4p", "06:00-19:00", "CLOSED") and OSM opening_hours (simple day/time rules
   only; anything with months, holidays or other syntax is treated as unknown).
   A place is dropped when its hours are KNOWN and it is closed that day, closes by 11:00, or
   opens after 11:00 (the text says "get there before 11 AM"). Unknown hours are kept and marked.
3. Step-free: Cool Options `accessible` (Yes/No) or OSM `wheelchair` (yes/limited/no); other
   sources have no accessibility data -> "unknown". For patients who need step-free access
   (questionnaire mobility_step_free_needed=true) places marked "no" are dropped; "limited"
   and "unknown" are kept and marked. This is the building entrance only, not the route
   (no kerb/step data on the walking route is used).
   Age: Cool Options places with age_restriction=Yes (all are NYC Aging older adult centers,
   named "OLDER ADULTS ONLY") are offered only to patients aged 60+ (NYC Aging's older-adult
   age; verify the exact rule per site).
4. Prefilter the 15 nearest eligible places per patient by straight line, then route
   patient home -> place on the foot network (routing_common.ors_matrix; ORS foot-walking or
   the OSRM foot fallback) and keep the 3 shortest by walking time.
5. Walking pace: patients aged 65+, or needing step-free access, or answering q5
   "with_help"/"no" use 0.8 m/s on the routed distance (Western et al. 2025, PMC12682371);
   others use the engine's own foot duration (~5 km/h).
6. leave_by = 11:00 minus walk minutes (walk rounded up to the minute). If the place opens later
   than leave_by + walk would arrive, earliest_leave = opening time minus walk minutes.

Run: ~/.local/bin/uv run python scripts/routing_cooling.py
"""
import csv, datetime as dt, json, math, os, re, statistics
from routing_common import (OLDER_WALK_MPS, PROCESSED, RAW, STATS, SYN, engine, fmt, haversine_m,
                            ors_matrix, read_csv, write_csv)

K_PREFILTER = 15
MAX_DEST = 80
MAX_SRC = 20
ARRIVE_BY = 11 * 60
OLDER_ONLY_AGE = 60  # Cool Options age_restriction=Yes = NYC Aging older adult centers ("OLDER ADULTS ONLY"); 60+ assumed
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
OSM_DAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]


def ref_day():
    best = None
    with open(os.path.join(PROCESSED, "replay_heatwave_hourly.csv")) as fh:
        for r in csv.DictReader(fh):
            if r["heat_index_f"]:
                hi = float(r["heat_index_f"])
                if best is None or hi > best[0]:
                    best = (hi, r["date_local"])
    d = dt.date.fromisoformat(best[1])
    return d, DAYS[d.weekday()], best[0]


def _t(s):
    """'8a' '8:30a' '12p' '06:00' -> minutes after midnight."""
    s = s.strip().lower()
    m = re.fullmatch(r"(\d{1,2})(?::(\d{2}))?\s*([ap])m?", s)
    if m:
        h, mi = int(m.group(1)) % 12, int(m.group(2) or 0)
        return h * 60 + mi + (720 if m.group(3) == "p" else 0)
    m = re.fullmatch(r"(\d{1,2}):(\d{2})", s)
    if m:
        return int(m.group(1)) * 60 + int(m.group(2))
    raise ValueError(s)


def _intervals(txt):
    out = []
    for part in txt.split(","):
        a, b = part.split("-")
        out.append((_t(a), _t(b)))
    return out


def hours_for_day(props, day):
    """Returns ('known', [(open,close),...] or []) or ('unknown', None), plus the raw text for that day."""
    h = props.get("hours")
    if isinstance(h, dict) and h:
        v = h.get(day)
        if v is None:
            return "known", [], "not listed (closed)"
        if v.strip().upper() == "CLOSED":
            return "known", [], "CLOSED"
        try:
            return "known", _intervals(v), v
        except Exception:
            return "unknown", None, v
    oh = props.get("opening_hours")
    if oh:
        if oh.strip() == "24/7":
            return "known", [(0, 1440)], "24/7"
        idx = DAYS.index(day)
        result, matched = None, False
        try:
            for rule in [re.sub(r"\s*,\s*", ",", r.strip()) for r in oh.split(";") if r.strip()]:
                m = re.fullmatch(r"((?:(?:Mo|Tu|We|Th|Fr|Sa|Su)(?:-(?:Mo|Tu|We|Th|Fr|Sa|Su))?,?)+)?\s*(.*)", rule)
                dpart, tpart = m.group(1), m.group(2).strip()
                if dpart:
                    days = set()
                    for seg in dpart.strip(",").split(","):
                        if "-" in seg:
                            a, b = seg.split("-")
                            i, j = OSM_DAYS.index(a), OSM_DAYS.index(b)
                            rng = range(i, j + 1) if i <= j else list(range(i, 7)) + list(range(0, j + 1))
                            days.update(rng)
                        else:
                            days.add(OSM_DAYS.index(seg))
                else:
                    days = set(range(7))
                if idx not in days:
                    continue
                if tpart.lower() in ("off", "closed"):
                    result, matched = [], True
                else:
                    result, matched = _intervals(tpart), True  # later rules override earlier ones
            if matched:
                return "known", result, oh
            return "known", [], oh + " (day not listed)"
        except Exception:
            return "unknown", None, oh
    return "unknown", None, ""


def hhmm(m):
    m = int(m) % 1440
    return f"{m // 60:02d}:{m % 60:02d}"


def step_free(props):
    a = props.get("accessible")
    if a:
        return "yes" if a.strip().lower() == "yes" else "no"
    w = props.get("wheelchair")
    if w in ("yes", "limited", "no"):
        return w
    return "unknown"


def main():
    rday, wday, hi = ref_day()
    pts = read_csv("patients.csv")
    q = {r["patient_id"]: r for r in read_csv("questionnaire.csv")}
    feats = json.load(open(os.path.join(PROCESSED, "cooling_places_nyc.geojson")))["features"]
    places = []
    dropped = {"outdoor": 0, "no_address": 0, "closed_or_after_11": 0}
    for f in feats:
        p = f["properties"]
        if not p.get("indoor"):
            dropped["outdoor"] += 1
            continue
        if not (p.get("address") or "").strip():
            dropped["no_address"] += 1  # the morning text must carry an address (spec §4.4 item 3)
            continue
        status, iv, raw = hours_for_day(p, wday)
        opens = closes = None
        if status == "known":
            # the interval that covers or follows the arrival window
            useful = [(a, b) for a, b in iv if a <= ARRIVE_BY and b > ARRIVE_BY]
            if not useful:
                dropped["closed_or_after_11"] += 1
                continue
            opens, closes = useful[0]
        places.append({"props": p, "lat": f["geometry"]["coordinates"][1], "lon": f["geometry"]["coordinates"][0],
                       "hours_status": status, "hours_raw": raw, "opens": opens, "closes": closes,
                       "step_free": step_free(p),
                       "older_only": str(p.get("age_restriction", "")).lower() == "yes"})

    # per-patient prefilter
    cand = {}
    info = {}
    for pt in pts:
        pid = pt["patient_id"]
        qq = q[pid]
        sf_need = qq["mobility_step_free_needed"] == "true"
        age = int(pt["age"])
        slow = age >= 65 or sf_need or qq["q5_can_reach_cool_place"] in ("with_help", "no")
        info[pid] = {"sf_need": sf_need, "slow": slow, "age": age, "q5": qq["q5_can_reach_cool_place"]}
        lat, lon = float(pt["home_lat"]), float(pt["home_lon"])
        el = [i for i, pl in enumerate(places) if not (sf_need and pl["step_free"] == "no")
              and not (age < OLDER_ONLY_AGE and pl["older_only"])]
        el.sort(key=lambda i: haversine_m(lat, lon, places[i]["lat"], places[i]["lon"]))
        cand[pid] = el[:K_PREFILTER]

    # group patients (sorted spatially) so each request has <=20 sources and <=80 destinations
    order = sorted(pts, key=lambda p: (round(float(p["home_lat"]), 2), float(p["home_lon"])))
    groups, cur, cur_u = [], [], set()
    for pt in order:
        u = cur_u | set(cand[pt["patient_id"]])
        if cur and (len(cur) >= MAX_SRC or len(u) > MAX_DEST):
            groups.append((cur, cur_u)); cur, u = [], set(cand[pt["patient_id"]])
        cur.append(pt); cur_u = u
    if cur:
        groups.append((cur, cur_u))

    routed = {}  # (pid, place_idx) -> (dur_s, dist_m, snap)
    for grp, uni in groups:
        uni = sorted(uni)
        locs = [(float(p["home_lon"]), float(p["home_lat"])) for p in grp] + [(places[i]["lon"], places[i]["lat"]) for i in uni]
        src = list(range(len(grp)))
        dst = list(range(len(grp), len(locs)))
        resp = ors_matrix("foot-walking", locs, src, dst)
        for si, p in enumerate(grp):
            for dj, i in enumerate(uni):
                routed[(p["patient_id"], i)] = (resp["durations"][si][dj], resp["distances"][si][dj],
                                                resp["destinations"][dj].get("snapped_distance"))

    rows, nearest = [], []
    for pt in pts:
        pid = pt["patient_id"]
        inf = info[pid]
        scored = []
        for i in cand[pid]:
            dur, dis, snap = routed[(pid, i)]
            if dur is None or dis is None:
                continue
            wmin = dis / OLDER_WALK_MPS / 60 if inf["slow"] else dur / 60
            scored.append((wmin, i, dis, dur, snap))
        scored.sort()
        for rank, (wmin, i, dis, dur, snap) in enumerate(scored[:3], 1):
            pl = places[i]; p = pl["props"]
            leave_by = ARRIVE_BY - math.ceil(wmin)
            earliest = (pl["opens"] - math.ceil(wmin)) if pl["opens"] is not None else None
            notes = []
            if inf["q5"] == "no":
                notes.append("patient says they cannot reach a cool place: needs escort or ride")
            elif inf["q5"] == "with_help":
                notes.append("patient needs help to get there")
            if wmin > 30:
                notes.append("walk over 30 min: offer a ride or transit")
            if pl["older_only"]:
                notes.append("older adults only (60+)")
            if p.get("membership_required"):
                notes.append(p["membership_required"])
            if p.get("coord_precision"):
                notes.append("location precision " + p["coord_precision"])
            if p.get("official_cooling_center"):
                notes.append("official cooling center: opens only on activated heat days; verify that day")
            if snap is not None and snap > 200:
                notes.append(f"place point is {int(snap)} m from the nearest walkable way")
            rows.append({
                "patient_id": pid, "synthetic": "true", "story_patient": pt["story_patient"], "age": inf["age"],
                "step_free_needed": str(inf["sf_need"]).lower(), "q5_can_reach_cool_place": inf["q5"],
                "walk_pace": "older-adult 0.8 m/s" if inf["slow"] else "routing default (~5 km/h)",
                "rank": rank, "place_name": p.get("name", ""), "place_type": p.get("category", ""),
                "official_cooling_center": str(bool(p.get("official_cooling_center"))).lower(),
                "operator": p.get("operator", ""), "address": p.get("address", ""), "zip": p.get("zip", ""),
                "borough": p.get("borough", ""), "phone": p.get("phone", ""),
                "place_lat": pl["lat"], "place_lon": pl["lon"], "place_source": p.get("source", ""),
                "place_source_id": p.get("source_id", ""),
                "walk_dist_km": fmt(dis / 1000, 3), "walk_min": fmt(wmin), "walk_min_routing_default": fmt(dur / 60),
                "straight_line_m": fmt(haversine_m(float(pt["home_lat"]), float(pt["home_lon"]), pl["lat"], pl["lon"]), 0),
                "step_free_status": pl["step_free"],
                "ref_day": f"{rday.isoformat()} ({wday})",
                "hours_status": pl["hours_status"], "hours_ref_day_raw": pl["hours_raw"],
                "opens_ref_day": hhmm(pl["opens"]) if pl["opens"] is not None else "",
                "closes_ref_day": hhmm(pl["closes"]) if pl["closes"] is not None else "",
                "hours_url": p.get("hours_url", ""),
                "leave_by": hhmm(leave_by),
                "earliest_leave": hhmm(earliest) if earliest is not None and earliest > 0 else "",
                "text_line": (f"{p.get('name','')}" + (f", {p['address']}" if p.get("address") else "")
                              + f": about {math.ceil(wmin)} min walk. Leave by {hhmm(leave_by)} to get there before 11 AM."),
                "routing_engine": engine(), "notes": "; ".join(notes)})
            if rank == 1:
                nearest.append(wmin)

    fields = list(rows[0].keys())
    write_csv(os.path.join(SYN, "cooling_match.csv"), rows, fields)
    r1 = [r for r in rows if r["rank"] == 1]
    older = [float(r["walk_min"]) for r in r1 if r["walk_pace"].startswith("older")]
    summ = {
        "ref_day": rday.isoformat(), "ref_weekday": wday, "ref_day_max_heat_index_f": hi,
        "places_in_file": len(feats), "indoor_candidates_after_hours_filter": len(places), "dropped": dropped,
        "patients": len(pts), "patients_matched_3": sum(1 for p in pts if sum(1 for r in rows if r["patient_id"] == p["patient_id"]) == 3),
        "median_walk_min_nearest": round(statistics.median(nearest), 1),
        "median_walk_min_nearest_older_pace_patients": round(statistics.median(older), 1) if older else None,
        "p90_walk_min_nearest": round(sorted(nearest)[int(0.9 * (len(nearest) - 1))], 1),
        "nearest_over_15_min": sum(1 for x in nearest if x > 15),
        "nearest_over_30_min": sum(1 for x in nearest if x > 30),
        "nearest_place_type_counts": {},
        "nearest_step_free_status_counts": {},
        "nearest_hours_status_counts": {},
        "routing_engine": engine(), "requests": dict(STATS), "matrix_groups": len(groups),
    }
    for r in r1:
        for k, col in (("nearest_place_type_counts", "place_type"), ("nearest_step_free_status_counts", "step_free_status"),
                       ("nearest_hours_status_counts", "hours_status")):
            summ[k][r[col]] = summ[k].get(r[col], 0) + 1
    sfp = [r for r in r1 if r["step_free_needed"] == "true"]
    summ["step_free_patients"] = len(sfp)
    summ["step_free_patients_nearest_confirmed_step_free"] = sum(1 for r in sfp if r["step_free_status"] == "yes")
    with open(os.path.join(RAW, "cooling_summary.json"), "w") as fh:
        json.dump(summ, fh, indent=2)
    print(json.dumps(summ, indent=2))


if __name__ == "__main__":
    main()
