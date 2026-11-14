"""Shootings inside the toll zone at night after hot days, 2015-2024 (descriptive, for the hot-night illustration).

Zone = precincts 1, 5, 6, 7, 9, 10, 13, 14, 17, 18. Night = 21:00-04:59, assigned to the day whose evening it follows.
Hot day = Central Park maximum at or above 30 C. Writes data/derived/simulate/zone_shootings.json.
"""
import json
from pathlib import Path

import pandas as pd

from concord import socrata

ROOT = Path(__file__).resolve().parents[2]


def main():
    rows, src = socrata.query(
        "833y-fsy8", select="occur_date, occur_time, statistical_murder_flag",
        where="occur_date >= '2015-01-01T00:00:00' and occur_date < '2025-01-01T00:00:00' and precinct in (1,5,6,7,9,10,13,14,17,18)",
        limit=5000)
    d = pd.DataFrame(rows)
    d["date"] = pd.to_datetime(d.occur_date.str[:10])
    d["h"] = d.occur_time.str.split(":").str[0].astype(int)
    d["night"] = (d.h >= 21) | (d.h < 5)
    d["day"] = d.date.where(d.h >= 5, d.date - pd.Timedelta(days=1))
    e = pd.read_csv(ROOT / "data/derived/bridges/ems_daily.csv", parse_dates=["date"])[["date", "TMAX"]]
    e = e[(e.date >= "2015-01-01") & (e.date < "2025-01-01")]
    m = d.merge(e, left_on="day", right_on="date", how="left")
    hot = m.TMAX >= 30
    n_hot = int((e.TMAX >= 30).sum())
    out = {"source": {k: src.get(k) for k in ("dataset", "name", "url", "rows_updated_at", "query", "fetched")},
           "years": 10, "zone_shootings": len(m), "zone_night_shootings": int(m.night.sum()),
           "zone_night_shootings_after_hot_day": int((m.night & hot).sum()), "hot_days": n_hot, "days": len(e),
           "night_fatal_share": float((m[m.night].statistical_murder_flag.astype(str).str.lower() == "true").mean()),
           "per_hot_night": float((m.night & hot).sum() / n_hot),
           "per_other_night": float((m.night & ~hot).sum() / (len(e) - n_hot))}
    (ROOT / "data/derived/simulate/zone_shootings.json").write_text(json.dumps(out, indent=1))
    print({k: v for k, v in out.items() if k != "source"})


if __name__ == "__main__":
    main()
