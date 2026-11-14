"""How inspection scores change after the fact, across archived copies of the city's table.

Usage: python -m analyses.underlay_drift.history
Exploratory and descriptive: nothing here was registered. Written on 14 November 2026.

Copies: ten Internet Archive captures of the full CSV export (2015 to April 2026, docs/restaurants.md) and the
live table of 12 November 2026. Each consecutive pair of copies is matched on restaurant (CAMIS), inspection
date and inspection type. For inspections in both copies the script counts scores that changed, fell and rose.
For the three most recent pairs it also counts which violation codes were removed, and how often a score fell
by borough, cuisine, first score and number of locations under one name.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
BIG = Path.home() / "opt" / "nyc-concordance"
OUT = ROOT / "data" / "derived" / "underlay_drift" / "history.json"
SOC = {"DBA": "name", "CUISINE_DESCRIPTION": "cuisine", "INSPECTION_DATE": "date", "VIOLATION_CODE": "code", "VIOLATION_DESCRIPTION": "desc", "CRITICAL_FLAG": "critical", "INSPECTION_TYPE": "type"}
COLS = {"CAMIS": "camis", "DBA": "name", "BORO": "boro", "ZIPCODE": "zip", "CUISINE DESCRIPTION": "cuisine", "INSPECTION DATE": "date", "ACTION": "action",
        "VIOLATION CODE": "code", "VIOLATION DESCRIPTION": "desc", "CRITICAL FLAG": "critical", "SCORE": "score", "GRADE": "grade", "INSPECTION TYPE": "type"}


def load(path: Path) -> pd.DataFrame:
    head = pd.read_csv(path, nrows=0)
    names = {**COLS, **SOC}  # the live copy uses the portal's field names
    use = [c for c in head.columns if c.strip().upper() in names]
    d = pd.read_csv(path, usecols=use, dtype=str, low_memory=False)
    d.columns = [names[c.strip().upper()] for c in d.columns]
    d["date"] = pd.to_datetime(d.date.str[:10], errors="coerce", format="mixed").dt.strftime("%Y-%m-%d")
    d = d[d.date.notna() & (d.date != "1900-01-01")]
    d["score"] = pd.to_numeric(d.score, errors="coerce")
    d["key"] = d.camis + "|" + d.date + "|" + d.type.fillna("")
    return d


def inspections(d: pd.DataFrame) -> pd.DataFrame:
    g = d.groupby("key", sort=False)
    out = g.agg(camis=("camis", "first"), name=("name", "first"), boro=("boro", "first"), cuisine=("cuisine", "first"), date=("date", "first"),
                type=("type", "first"), score=("score", "first"), grade=("grade", "first"))
    out["codes"] = g["code"].agg(lambda s: frozenset(x for x in s if isinstance(x, str) and x))
    return out


def rate(df: pd.DataFrame, by: str, min_n: int) -> list[dict]:
    g = df.groupby(by).agg(n=("fell", "size"), fell=("fell", "sum"), mean_drop=("drop", lambda s: float(s[s > 0].mean()) if (s > 0).any() else 0.0))
    g = g[g.n >= min_n]
    g["share"] = g.fell / g.n
    return [{"group": str(k), "n": int(r.n), "fell": int(r.fell), "share": round(float(r.share), 4), "mean_drop": round(float(r.mean_drop), 1)} for k, r in g.sort_values("share", ascending=False).iterrows()]


def main() -> None:
    files = sorted((BIG / "restaurants_wayback").glob("*.csv"))
    copies = [(f.stem[:8], f) for f in files] + [("20261112", BIG / "underlay_publish" / "live_43nn-pn8j_all.csv.gz")]
    res = {"pairs": [], "detail": {}}
    prev_name, prev = None, None
    for name, path in copies:
        cur_raw = load(path)
        cur = inspections(cur_raw)
        desc = cur_raw.dropna(subset=["code"]).drop_duplicates("code").set_index("code")[["desc", "critical"]]
        if prev is not None:
            j = prev.join(cur, how="inner", lsuffix="_a", rsuffix="_b")
            both = j[j.score_a.notna() & j.score_b.notna()].copy()
            both["drop"] = both.score_a - both.score_b
            both["fell"] = both["drop"] > 0
            pair = {"from": prev_name, "to": name, "inspections_in_both": int(len(both)), "changed": int((both["drop"] != 0).sum()), "fell": int((both["drop"] > 0).sum()),
                    "rose": int((both["drop"] < 0).sum()), "median_drop": float(both.loc[both["drop"] > 0, "drop"].median()) if (both["drop"] > 0).any() else None,
                    "restaurants_in_from": int(prev.camis.nunique()), "restaurants_gone": int(len(set(prev.camis) - set(cur.camis)))}
            # recent inspections only: those dated in the 12 months before the earlier capture
            da = pd.to_datetime(both.date_a, errors="coerce")
            cap = pd.Timestamp(prev_name)
            recent = both[(da > cap - pd.Timedelta(days=365)) & (da <= cap)]
            pair.update(recent_in_both=int(len(recent)), recent_changed=int((recent["drop"] != 0).sum()), recent_fell=int((recent["drop"] > 0).sum()), recent_rose=int((recent["drop"] < 0).sum()))
            res["pairs"].append(pair)
            print(pair)
            if name in ("20251115", "20260403", "20261112"):
                r = recent[recent.score_a >= 14].copy()  # inspections with something to contest
                r["band"] = np.where(r.score_a <= 27, "B range (14 to 27)", np.where(r.score_a <= 41, "28 to 41", "42 and over"))
                r["kind"] = np.where(r.type_a.fillna("").str.contains("Re-inspection"), "re-inspection", np.where(r.type_a.fillna("").str.contains("Initial"), "initial inspection", "other"))
                counts = prev.groupby("name").camis.nunique()
                r["chain"] = r.name_a.map(lambda n: "10 or more locations" if counts.get(n, 1) >= 10 else "2 to 9 locations" if counts.get(n, 1) >= 2 else "one location")
                removed = {}
                cited = {}
                for ca, cb in zip(recent.codes_a, recent.codes_b):
                    for c in ca:
                        cited[c] = cited.get(c, 0) + 1
                        if c not in cb:
                            removed[c] = removed.get(c, 0) + 1
                added = sum(len(cb - ca) for ca, cb in zip(recent.codes_a, recent.codes_b))
                codes = [{"code": c, "cited": n, "removed": removed.get(c, 0), "share": round(removed.get(c, 0) / n, 4),
                          "critical": str(desc.critical.get(c, "")), "description": str(desc.desc.get(c, ""))[:150]} for c, n in cited.items() if n >= 200]
                res["detail"][f"{prev_name}_{name}"] = {
                    "base": "inspections dated in the 12 months before the earlier copy, present in both copies",
                    "codes_cited": int(sum(cited.values())), "codes_removed": int(sum(removed.values())), "codes_added": int(added),
                    "by_code": sorted(codes, key=lambda x: -x["share"]),
                    "scored_14_or_more": {"n": int(len(r)), "fell": int(r.fell.sum()), "share": round(float(r.fell.mean()), 4)},
                    "by_borough": rate(r, "boro_a", 300), "by_first_score": rate(r, "band", 100), "by_kind": rate(r, "kind", 100),
                    "by_locations": rate(r, "chain", 100), "by_cuisine": rate(r, "cuisine_a", 300)}
        prev_name, prev = name, cur
    OUT.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
