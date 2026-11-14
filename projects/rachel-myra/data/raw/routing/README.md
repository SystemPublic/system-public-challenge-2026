# Routing (contact travel times, cooling-place matching)

Built 2026-11-14 (overnight, unattended); routing services accessed 2026-11-14. **All people are synthetic**
(data/processed/synthetic). Nothing here is invented: travel times come from road-network routing; every
modelling parameter is listed below with its source or marked as an assumption.

Scripts (run from the repo root, in this order; reruns use the cache and make no network calls):

```bash
~/.local/bin/uv run python scripts/routing_contacts.py   # -> data/processed/synthetic/contacts_routed.csv, contacts_summary.json
~/.local/bin/uv run python scripts/routing_cooling.py    # -> data/processed/synthetic/cooling_match.csv, cooling_summary.json
~/.local/bin/uv run python scripts/routing_story.py      # -> story_patients.md
```

`scripts/routing_common.py` holds the cached matrix client, constants and helpers.

## IMPORTANT: which routing engine was used

The plan was OpenRouteService (ORS). **The `ORS_API_KEY` value in `.env.local` could not be used**: it contains
non-ASCII characters (Cyrillic look-alike letters) and extra text after it, so it is not a valid HTTP header value,
and `source .env.local` does not set it. The first three attempts failed locally before any request was sent. We did
not try to "repair" the key.

**All results in this folder therefore come from the public OSRM servers run by FOSSGIS**
(`https://routing.openstreetmap.de`, `routed-foot` and `routed-car`, OSRM `table` service). It is open-source,
OpenStreetMap-based routing, like ORS. Column names keep an `ors` prefix (e.g. `walk_ors_min`) for the routed values
whatever engine produced them; the `routing_engine` column says which one (`osrm-fossgis` everywhere now).

To switch to ORS: put a clean key in `.env.local` (`ORS_API_KEY=<key>`, ASCII only, nothing after it), delete
`cache/`, and rerun the three scripts. `routing_common.engine()` picks ORS automatically when a usable key exists
(or force it with `ROUTING_ENGINE=ors`). The ORS path (`POST /v2/matrix/{foot-walking|driving-car}`, key in the
`Authorization` header) is written but **untested** because no valid key was available.

### Limits used

| Engine | Limit we kept to | Requests made |
|---|---|---|
| OSRM FOSSGIS | <=100 locations per table request; 1.5 s between requests (their policy asks for <=1 req/s, no heavy use); User-Agent identifies a script | 59 HTTP calls in total: 58 OK + 1 connection reset that was retried. Contacts: 6 foot + 7 car tables (13). Cooling: 15 foot tables per run, run 3 times while fixing filters (45). |
| ORS (not used) | Planned at <=40 req/min (1.6 s gap) and <=3,500 pairs per Matrix request, well inside ~500 Matrix requests/day | 0 sent |

Every call is in `call_log.tsv` (time, engine, profile, pairs, HTTP status, cache file). Every response is in `cache/`
(`<engine>_<profile>_<sha1>.json`, holding the request body and the durations, distances and snap distances). No API key
appears in any file name, cache file or log. Older cooling-run caches (from before the final filters) are kept; they are
valid responses, just unused now. Folder size about 1.2 MB.

## 1. Contacts -> `data/processed/synthetic/contacts_routed.csv` (327 rows, one per contact)

All original contacts.csv columns are kept, then:

| Column | Meaning |
|---|---|
| `walk_ors_dist_km`, `walk_ors_min` | Routed walking distance and the engine's own walking time (adult pace, about 5 km/h) |
| `walk_older_pace_min` | **Used in the rule.** Routed walking distance / 0.8 m/s. Older walkers move at about 0.77-0.9 m/s (Western et al., Age and Ageing 2025, PMC12682371; spec §4.4a). We apply it to every contact as a conservative pace because contact ages are unknown. |
| `drive_ors_dist_km`, `drive_ors_min` | Routed driving, free-flow (no live traffic, no parking, no time to reach the car). An **optimistic** lower bound. |
| `transit_approx_min`, `transit_from_station`, `transit_to_station` | **Approximate, not GTFS routing.** See below. |
| `fastest_mode`, `fastest_min` | Fastest of walk / drive / transit_approx |
| `fastest_nocar_mode`, `fastest_nocar_min` | Fastest of walk / transit_approx (we do not know whether a contact has a car) |
| `travel_allowance_{45,60,90}` | 15 / 30 / 60 min |
| `qualifies_{45,60,90}` | Fastest (any mode) <= allowance |
| `qualifies_nocar_{45,60,90}` | Fastest without a car <= allowance |
| `naive_qualifies_{45,60,90}min_derived` | The naive placeholder (`naive_travel_min`) under the same rule. The 60 and 90 values equal the original `naive_qualifies_60min` / `_90min` columns for all 327 rows (checked); 45 is new. |
| `max_snap_m` | Largest distance from an input point to the routable network (contact or home) |
| `routing_note` | out_of_area: driving only; same-building caveat; snapping >200 m |

**Eligibility rule (spec §4.4a.5):** T_travel <= T_max - p90(patient) - p90(contact). T_max uses the spec's starting
budgets: 45 min (very high risk), 60 min (high), 90 min (medium). p90(patient) = p90(contact) = **15 min**, the same
default response-time assumption contacts.csv generator A14 used (spec §4.4a.4 says to replace it with published p90s
from Pielot et al. 2014/2018 and Mehrotra et al. 2016, then per-person learned p90s). So the travel allowance is
15 / 30 / 60 min.

**Transit approximation:** walk from the contact to the nearest MTA subway station (straight line x 1.3 detour, 0.8 m/s)
+ 5 min wait (assumption) + straight-line distance between that station and the station nearest the patient at
20 km/h (assumption: an effective door-to-platform subway speed including stops and some detour; not measured) + walk
from that station to the patient (same rule). Only computed when both stations are within 1.5 km and differ. It does not
check that the two stations share a line, transfers, service at that hour or elevator access. Stations:
`data/processed/subway_stations_nyc.geojson` (MTA GTFS static, 496 parent stations). Buses are not modelled. It never
came out as the fastest mode; it matters only in the no-car flags.

Walking for the 31 `out_of_area` contacts (40-100+ km away) was not routed: only driving. Patient-level counts are in
`contacts_summary.json`.

### Result (300 patients, 50 with no contact on file)

| Budget (allowance) | No qualifying contact: routed, any mode | Routed, no car | Naive placeholder | Patients whose status changed (routed any mode vs naive) |
|---|---|---|---|---|
| 45 min (15) | 100 | 234 | 232 | 132 (all gained a contact) |
| 60 min (30) | 75 | 186 | 154 | 79 (all gained) |
| 90 min (60) | 65 | 120 | 92 | 27 (all gained) |

Reading it: the naive placeholder sits between the two routed views. If contacts drive, free-flow driving makes almost
everyone in the Bronx/NYC reachable (driving was fastest for 311 of 327 contacts; median routed fastest time = 0.28 x the
naive time). Without a car, routed walking at 0.8 m/s plus the rough subway estimate is stricter than the naive rule,
so more patients lack a qualifying contact than the placeholder said. The truth for a real patient depends on whether
the contact drives, so the app should ask at sign-up ("How would you get there?") and use the matching column.

## 2. Cooling places -> `data/processed/synthetic/cooling_match.csv` (900 rows = 3 per patient)

Source places: `data/processed/cooling_places_nyc.geojson` (1,868 features from the place agent; see
`data/raw/place/README.md`).

1. **Candidates:** indoor only (852 outdoor spray showers / pools dropped; they are closed for the season anyway) with a
   street address (141 dropped; the text must give one), and not known to be closed at 11 AM (32 dropped). 843 left.
2. **Reference day:** the replay day with the highest heat index in `data/processed/replay_heatwave_hourly.csv`:
   **2025-06-23, a Monday** (105.7 F). Hours are read for Monday from the Cool Options / rec center per-day strings or OSM
   `opening_hours` (simple day/time rules; anything else = unknown). A place is dropped only when its hours are known and
   it is not open at 11:00. Unknown hours are kept and marked `hours_status=unknown`.
3. **Age:** Cool Options places with `age_restriction=Yes` (the NYC Aging older adult centers, named "OLDER ADULTS ONLY")
   are offered only to patients aged 60+. The 60 cut-off is our assumption from NYC Aging's older-adult focus; verify.
4. **Step-free:** Cool Options `accessible` (Yes/No) or OSM `wheelchair` (yes/limited/no) -> `step_free_status`;
   anything else is `unknown`. For the 69 patients who need step-free access, places marked `no` are excluded; `limited`
   and `unknown` stay, marked. This is about the building entrance only; the walking route's kerbs and steps are not
   checked.
5. **Routing:** 15 nearest candidates per patient by straight line, then routed foot network from the home point; keep the
   3 shortest by walking time.
6. **Pace:** 0.8 m/s on the routed distance for patients aged 65+, needing step-free access, or answering q5 "with help"
   / "no" (spec §4.4a, Western et al. 2025); everyone else uses the engine's adult walking time (`walk_min_routing_default`
   is kept for all).
7. **Leave-by:** `leave_by` = 11:00 minus walk minutes (rounded up), so they arrive before 11 AM. `earliest_leave` =
   opening time minus walk minutes, when hours are known. `text_line` is a draft English text line.

### Result

- **Median walk to the nearest cooling place: 9.3 min** (all 300 patients); 10.7 min for patients on the older-adult pace;
  90th percentile 18.4 min; 50 patients over 15 min, 1 over 30 min.
- Nearest place type: official cooling center 236, department store 32, library 14, rec center 11, community centre 7.
- Step-free status of the nearest place: yes 241, unknown 59. Of the 69 step-free patients, 58 have a confirmed step-free
  nearest place.
- Hours of the nearest place on the reference day: known 277, unknown 23.

## 3. Story patients -> `story_patients.md`

Short routing summary for S01-S10 (contacts table with routed vs naive, verdict, top 3 cooling places with leave-by).

## Caveats

- **Engine:** OSRM FOSSGIS, not ORS (see above). Both use OpenStreetMap; numbers would differ slightly under ORS.
- **No time of day:** driving is free-flow; spec §4.4a wants travel time "at that time of day". Real midday Bronx driving
  plus parking will be slower. Walking times ignore heat (people walk slower in heat) and stairs (a 6th-floor walk-up adds
  minutes for S01).
- **Same-building contacts (44):** the routed time is street-to-street snapping between two nearby points, not the real
  trip (stairs or elevator). Treat them as qualifying.
- **Contact points are synthetic bearing-plus-distance offsets** (generator A12); 31 contacts sit >200 m from the
  nearest road (water, park, rail yard), flagged in `routing_note`.
- **Transit is an approximation**, labelled everywhere. Real MTA GTFS routing (e.g. OpenTripPlanner or r5 with
  `data/raw/place/gtfs/gtfs_subway.zip` plus bus feeds) is the follow-up.
- **Cooling centers open only on activated heat-emergency days**; hours are the 2026-season finder values. Library hours
  for NYPL/BPL branches that are not cooling centers often come only from OSM or are unknown. Rec centers usually need a
  membership (noted). Check open status on the day.
- **Step-free** is entrance accessibility from the source, not a full route check; 59 nearest places have no data.
- Synthetic homes are random points inside ZIP polygons, not addresses.
