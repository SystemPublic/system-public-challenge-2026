"""Trends in detected violations, 2012-2026, from ten Internet Archive copies of the 43nn-pn8j
export (wayback_fetch.py) plus the live table. Descriptive; no claim is registered.

For each copy: one row per inspection visit (CAMIS, date, type), with critical-violation rows,
score and grade. Measures by inspection year, for Cycle Inspection / Initial Inspection:
  crit   mean critical violation rows per initial inspection
  shareA share of A among visits graded A, B or C (any cycle inspection; grades are given at the
         initial inspection when the score is 0-13 and otherwise at re-inspection)
The pooled series takes, for each year Y, the copy captured closest after the end of Y (so the
least survivorship-filtered copy that holds the whole year). Survivorship is measured by comparing
the same inspection year in copies captured later: restaurants that closed in between drop out.
Outputs data/derived/restaurants/trends_by_copy.csv, trends_pooled.csv; figure trends.png.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import warnings
warnings.simplefilter("ignore")

import common as c

WB = Path.home() / "opt" / "nyc-concordance" / "restaurants_wayback"
COLS = ["CAMIS", "BORO", "INSPECTION DATE", "CRITICAL FLAG", "SCORE", "GRADE", "INSPECTION TYPE", "VIOLATION CODE"]


def visits_from_csv(f: Path) -> pd.DataFrame:
    d = pd.read_csv(f, usecols=COLS, dtype=str)
    d = d.rename(columns=dict(zip(COLS, ["camis", "boro", "date", "crit", "score", "grade", "itype", "code"])))
    d["date"] = pd.to_datetime(d.date, format="%m/%d/%Y", errors="coerce")
    d = d[d.date.dt.year >= 2005]
    d["is_crit"] = d.crit.fillna("").str.upper().isin(["CRITICAL", "Y", "C"])  # 2021 copy codes C critical, G general
    d["score"] = pd.to_numeric(d.score, errors="coerce")
    g = d.groupby(["camis", "date", "itype"], dropna=False).agg(boro=("boro", "first"), n_crit=("is_crit", "sum"),
                                                                score=("score", "max"), grade=("grade", "max")).reset_index()
    g["boro"] = g.boro.str.title()
    return g


def visits_live() -> pd.DataFrame:
    df, src = c.inspections("inspection_date > '2005-01-01'", "live_all")
    df = df.rename(columns={"inspection_date": "date"})
    return df[["camis", "date", "itype", "boro", "n_crit", "score", "grade"]], src


def measures(v: pd.DataFrame, boro: str | None) -> pd.DataFrame:
    if boro:
        v = v[v.boro == boro]
    v = v.assign(year=v.date.dt.year)
    ci = v[v.itype == "Cycle Inspection / Initial Inspection"]
    gr = v[v.itype.fillna("").str.startswith("Cycle Inspection") & v.grade.isin(["A", "B", "C"])]
    out = pd.DataFrame({"n_initial": ci.groupby("year").size(), "crit": ci.groupby("year").n_crit.mean(),
                        "score_initial": ci.groupby("year").score.mean(),
                        "n_graded": gr.groupby("year").size(), "shareA": gr.groupby("year").grade.apply(lambda s: (s == "A").mean()),
                        "restaurants": v.groupby("year").camis.nunique()})
    return out


def main():
    rows = []
    sources = []
    copies = {}
    for f in sorted(WB.glob("*.csv")):
        ts = f.stem
        copies[ts] = visits_from_csv(f)
        sources.append({"kind": "internet-archive", "url": f"https://web.archive.org/web/{ts}id_/https://data.cityofnewyork.us/api/views/43nn-pn8j/rows.csv?accessType=DOWNLOAD",
                        "captured": ts, "bytes": f.stat().st_size})
    live, src = visits_live()
    copies["20261113000000"] = live
    sources.append(src)
    for ts, v in copies.items():
        for boro in (None, "Manhattan"):
            m = measures(v, boro)
            m["copy"] = ts
            m["area"] = boro or "NYC"
            rows.append(m.reset_index())
    t = pd.concat(rows)
    t["cap"] = pd.to_datetime(t["copy"].str[:8])
    t = t[t.year <= t.cap.dt.year]
    t["full_year"] = t.year < t.cap.dt.year
    t["lag_years"] = (t.cap - pd.to_datetime(t.year.astype(str) + "-12-31")).dt.days / 365.25
    t.round(4).to_csv(c.DER / "trends_by_copy.csv", index=False)
    # pooled: the earliest copy captured after the end of the year, with at least 500 initial inspections
    ok = t[t.full_year & (t.n_initial >= 1000)]
    pooled = ok.sort_values("lag_years").groupby(["area", "year"]).head(1).sort_values(["area", "year"])
    pooled.round(4).to_csv(c.DER / "trends_pooled.csv", index=False)
    c.write_json("trends_sources.json", sources)

    # survivorship: same year, later copies, relative to the pooled (earliest) copy
    base = pooled.set_index(["area", "year"])[["crit", "shareA", "n_initial", "restaurants"]]
    s = ok.join(base, on=["area", "year"], rsuffix="_base")
    s["d_crit"] = s.crit - s.crit_base
    s["d_shareA"] = s.shareA - s.shareA_base
    s["kept_initial"] = s.n_initial / s.n_initial_base
    s.round(4).to_csv(c.DER / "survivorship.csv", index=False)

    fig, ax = plt.subplots(1, 3, figsize=(15, 4.4))
    for area, col in (("NYC", "#1f4e79"), ("Manhattan", "#c0504d")):
        p = pooled[pooled.area == area]
        ax[0].plot(p.year, p.crit, "o-", color=col, label=f"{area}, earliest copy after year end")
        ax[1].plot(p.year, p.shareA, "o-", color=col, label=area)
        lv = t[(t["copy"] == "20261113000000") & (t.area == area) & t.year.between(2022, 2025)]
        ax[0].plot(lv.year, lv.crit, "x--", color=col, alpha=0.6, label=f"{area}, live table Nov 2026")
        ax[1].plot(lv.year, lv.shareA, "x--", color=col, alpha=0.6)
    ax[0].set_title("Critical violations per initial cycle inspection")
    ax[1].set_title("Share of A among A/B/C cycle grades")
    ax[0].legend(fontsize=7)
    for a in ax[:2]:
        a.set_xlabel("inspection year")
        a.axvspan(2020, 2021.5, color="0.9", zorder=0)
    ss = s[(s.area == "NYC") & (s.lag_years > 0.2) & (s.lag_years < 3.0) & ~s["copy"].astype(str).str.startswith("20210529")]
    sc = ax[2].scatter(ss.lag_years, ss.kept_initial, c=ss.year, cmap="viridis", s=18)
    ax[2].set_xlabel("years between end of inspection year and capture")
    ax[2].set_ylabel("initial inspections kept, relative to earliest copy")
    ax[2].set_title("Survivorship: inspections of a year that remain\n(copies within 3 years; the table keeps about 3 years)", fontsize=9)
    fig.colorbar(sc, ax=ax[2], label="inspection year")
    path = c.save_fig(fig, "trends.png")
    print(pooled[["area", "year", "copy", "n_initial", "crit", "shareA"]].to_string())
    print(s[(s.area == "NYC")][["year", "copy", "lag_years", "kept_initial", "d_crit", "d_shareA"]].round(3).to_string())
    print(path)


if __name__ == "__main__":
    main()
