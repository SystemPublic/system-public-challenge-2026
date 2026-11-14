"""Outcome of moon-full-emergencies, from data/derived/moon/results.json. Usage: python -m analyses.moon.outcome"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from concord import claims

ROOT = Path(__file__).resolve().parents[2]
r = json.loads((ROOT / "data/derived/moon/results.json").read_text())
f = {k: v["full_moon"] for k, v in r.items()}
p = {k: v["placebo_23_day"] for k, v in r.items()}


def s(d):
    return f"{d['rr']:.3f} ({d['lo']:.3f} to {d['hi']:.3f})"


ok = all(v["inside_bounds"] for v in r.values())
refuted = any(v["excludes_one_983"] and v["placebo_includes_one"] for v in r.values())
verdict = "confirmed" if ok and not refuted else ("contested" if refuted else "unsettled")
REC = {
    "id": "moon-full-emergencies",
    "verdict": verdict,
    "city_effect": {"label": "rate ratio of injury crashes in the 3-day full-moon window, New York City 2014-2025",
                    "estimate": f["injury_crashes"]["rr"], "lo": f["injury_crashes"]["lo"], "hi": f["injury_crashes"]["hi"],
                    "scale": "rate ratio", "null": 1, "n": f["injury_crashes"]["n_days"]},
    "graph_effect": {"label": "relative risk of emergency transport for road traffic crashes on full-moon nights (PMID 29990928)",
                     "estimate": 1.042, "lo": 1.021, "hi": 1.063, "scale": "relative risk", "null": 1},
    "all_effects": {k: {"full_moon": f[k], "placebo_23_day": p[k], "full_moon_day_only": r[k]["full_moon_day_only"],
                        "bounds": r[k]["bounds"], "first": r[k]["first"], "last": r[k]["last"]} for k in r},
    "sources": [
        {"kind": "derived", "path": "data/derived/heat/shootings_daily.csv", "note": "NYPD shooting incidents by day with NOAA Central Park weather, built for heat-shootings"},
        {"kind": "derived", "path": "data/derived/health_gaps/ems_daily.csv", "note": "EMS Incident Dispatch Data (76xm-jjuj) by day; source records in data/derived/health_gaps/ems_daily_sources.json"},
        {"kind": "nyc-open-data", "dataset": "h9gi-nx95", "name": "Motor Vehicle Collisions - Crashes", "note": "copy fetched for the turn-restriction claims, crashes to 10 November 2026; held outside the repository"},
        {"kind": "other", "name": "PyEphem full-moon instants", "note": "ephem.next_full_moon, converted to New York dates"},
    ],
    "prediction_scored": f"hit: shootings {s(f['shootings'])}, ambulance incidents {s(f['ems'])}, injury crashes {s(f['injury_crashes'])}; "
                         "each 95% interval is inside its registered bound and inside the predicted range except at the edges of the interval.",
    "settle": "Hour-of-day data would test the one remaining path, moonlight at night: night-time crashes and shootings on clear "
              "full-moon nights against cloudy ones.",
    "research_needed": [{"question": "Do night-time crashes rise on clear full-moon nights?", "data": "crash times (h9gi-nx95) and hourly cloud cover",
                         "design": "full moon by cloud cover interaction, night hours only", "priority": "low"}],
    "figures": [],
    "notes": f"The 23-day placebo gave shootings {s(p['shootings'])}, ambulance incidents {s(p['ems'])} and injury crashes {s(p['injury_crashes'])}, "
             "so the full-moon estimates are no different from a window with no meaning. The injury-crash interval excludes the graph's 1.042 "
             "for crash transports in Japan (PMID 29990928). The graph's homicide finding for Finland (0.85, PMID 30647032) is outside the "
             "shooting interval. Secondary, deciding nothing: the full-moon day alone gave shootings "
             f"{s(r['shootings']['full_moon_day_only'])} and injury crashes {s(r['injury_crashes']['full_moon_day_only'])}. "
             "No referee has read this outcome yet.",
}
if __name__ == "__main__":
    print(claims.outcome(REC), verdict)
