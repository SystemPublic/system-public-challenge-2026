"""Download crash points (h9gi-nx95) and left-turn vehicle collision ids (bm4k-52h4) to
~/opt/nyc-concordance/turn_restrictions/ (outside Dropbox; about 150 MB). Paged SoQL, ordered by
collision_id. Writes a source record for each to data/derived/turn_restrictions/fetch_sources.json.
Run only after the registrations (claims/registered/turn-*.json) were committed."""
import csv, io, json, sys, time
from pathlib import Path
import requests
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import socrata as s

OPT = Path.home() / "opt/nyc-concordance/turn_restrictions"
DOM = "https://data.cityofnewyork.us/resource"
PAGE = 100000


def pull_offset(ds, select, where, fname):
    """Page by $offset ordered on the system row id (:id); used for the vehicles table, where ordering
    on collision_id with a filter on pre_crash timed out."""
    f = OPT / fname
    if f.exists():
        return
    tmp = f.with_suffix(".part")
    off, header = 0, None
    with tmp.open("w") as out:
        while True:
            params = {"$select": select, "$where": where, "$order": ":id", "$limit": 50000, "$offset": off}
            for i in range(6):
                try:
                    r = requests.get(f"{DOM}/{ds}.csv", params=params, timeout=600)
                    r.raise_for_status()
                    break
                except requests.RequestException:
                    time.sleep(5 * (i + 1))
            else:
                raise RuntimeError("fetch failed")
            lines = r.text.splitlines()
            if header is None:
                header = lines[0]
                out.write(header + "\n")
            body = lines[1:]
            if body:
                out.write("\n".join(body) + "\n")
            off += len(body)
            print(fname, off, flush=True)
            if len(body) < 50000:
                break
    tmp.rename(f)


def pull(ds, select, where, fname):
    OPT.mkdir(parents=True, exist_ok=True)
    f = OPT / fname
    if f.exists():
        return
    tmp = f.with_suffix(".part")
    last, n, header = "", 0, None
    with tmp.open("w") as out:
        while True:
            params = {"$select": select, "$where": f"({where}) and collision_id > '{last}'",
                      "$order": "collision_id", "$limit": PAGE}
            for i in range(6):
                try:
                    r = requests.get(f"{DOM}/{ds}.csv", params=params, timeout=600)
                    r.raise_for_status()
                    break
                except requests.RequestException:
                    time.sleep(5 * (i + 1))
            else:
                raise RuntimeError("fetch failed")
            lines = r.text.splitlines()
            if header is None:
                header = lines[0]
                out.write(header + "\n")
            body = lines[1:]
            if not body:
                break
            out.write("\n".join(body) + "\n")
            n += len(body)
            idx = next(csv.reader([header])).index("collision_id")
            last = next(csv.reader([body[-1]]))[idx]  # collision_id is text; paging is lexicographic
            print(fname, n, flush=True)
            if len(body) < PAGE:
                break
    tmp.rename(f)


def main():
    q = {
        "crashes": ("h9gi-nx95", "collision_id, crash_date, latitude, longitude, number_of_pedestrians_injured, "
                    "number_of_pedestrians_killed, number_of_persons_injured, number_of_persons_killed",
                    "crash_date >= '2014-01-01T00:00:00' and latitude > 40.4 and latitude < 41.0", "crashes.csv"),
        "left_vehicles": ("bm4k-52h4", "collision_id, crash_date, pre_crash",
                          "pre_crash = 'Making Left Turn'", "left_vehicles.csv"),
    }
    srcs = {}
    for k, (ds, sel, wh, fn) in q.items():
        (pull_offset if k == "left_vehicles" else pull)(ds, sel, wh, fn)
        paging = "paged by $offset on :id" if k == "left_vehicles" else "paged by collision_id"
        rec = s.source_record(ds, {"$select": sel, "$where": wh + f" ({paging})", "format": "csv"})
        rec["local_file"] = f"~/opt/nyc-concordance/turn_restrictions/{fn}"
        with (OPT / fn).open() as fh:
            rec["n_rows"] = sum(1 for _ in fh) - 1
        srcs[k] = rec
    (ROOT / "data/derived/turn_restrictions/fetch_sources.json").write_text(json.dumps(srcs, indent=1))
    print(json.dumps({k: v["n_rows"] for k, v in srcs.items()}))


if __name__ == "__main__":
    main()
