"""retimed-daytime-burglary: residential burglaries beginning 08:00-17:59, Monday and Friday against midweek."""
import datetime as dt, json, sys
from pathlib import Path
import numpy as np, pandas as pd, geopandas as gpd
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib
from concord import socrata

RES = "('RESIDENCE - APT. HOUSE','RESIDENCE-HOUSE','RESIDENCE - PUBLIC HOUSING')"
SRC = []
D = dt.date


def records(ds, lo, hi):
    rows, src = socrata.query_all(ds, select="cmplnt_num, cmplnt_fr_dt, cmplnt_fr_tm, cmplnt_to_dt, crm_atpt_cptd_cd, prem_typ_desc, latitude, longitude",
                                  where=f"cmplnt_fr_dt between '{lo}T00:00:00' and '{hi}T23:59:59' and ky_cd=107 and prem_typ_desc in {RES} "
                                        "and date_extract_dow(cmplnt_fr_dt) between 1 and 5 and cmplnt_fr_tm >= '08:00:00' and cmplnt_fr_tm < '18:00:00'",
                                  order="cmplnt_num")
    SRC.append(src)
    return pd.DataFrame(rows)


def to_panel(df):
    return df.groupby(["unit", "date"], as_index=False).size().rename(columns={"size": "n"})


def run(P0, P1, w0, w1, g, B=2000):
    units = sorted(set(P0.unit) | set(P1.unit))
    A0, A1 = lib.week_arrays(P0, units, w0), lib.week_arrays(P1, units, w1)
    u = np.array(units)
    groups = {"all": np.ones(len(u), bool), "hi": np.isin(u, g["sending_hi"]), "lo": np.isin(u, g["sending_lo"]), "cbd": np.isin(u, g["cbd_cds"])}
    r = lib.estimate(A0, A1, np.zeros(len(u)), groups, B=B)
    r.pop("slope", None); r.pop("mean_Y", None)
    r["counts"] = {k: [float(A0[0][m].sum() + A0[1][m].sum()), float(A1[0][m].sum() + A1[1][m].sum())] for k, m in groups.items()}
    r["mf_twt_ratio"] = {k: [float((A[0][m].sum() / 2) / (A[1][m].sum() / 3)) for A in (A0, A1)] for k, m in groups.items()}
    return r


if __name__ == "__main__":
    g = json.load(open(lib.OUT / "exposure_groups.json"))
    df = pd.concat([records("qgea-i56i", "2015-01-01", "2025-12-31"), records("5uac-w243", "2026-01-01", "2026-09-30")], ignore_index=True)
    df = df.drop_duplicates("cmplnt_num")
    df["date"] = df.cmplnt_fr_dt.str[:10]
    df["lat"] = pd.to_numeric(df.latitude, errors="coerce"); df["lon"] = pd.to_numeric(df.longitude, errors="coerce")
    cds = gpd.read_file(lib.ROOT / "data/cache/boundaries/5crt-au7u.geojson")[["boro_cd", "geometry"]]
    pts = gpd.GeoDataFrame(df[["cmplnt_num"]], geometry=gpd.points_from_xy(df.lon, df.lat), crs=cds.crs)
    j = gpd.sjoin(pts[df.lat.notna().values & (df.lat != 0).values], cds, how="left", predicate="within").drop_duplicates("cmplnt_num")
    df = df.merge(j[["cmplnt_num", "boro_cd"]], on="cmplnt_num", how="left")
    df["unit"] = pd.to_numeric(df.boro_cd, errors="coerce").fillna(0).astype(int)
    wk = lib.retained_weeks
    W = {"base": wk(D(2015, 1, 1), D(2019, 12, 31)), "rec": wk(D(2023, 1, 1), D(2026, 9, 30)),
         "b1719": wk(D(2017, 1, 1), D(2019, 12, 31)), "p1": wk(D(2015, 1, 1), D(2017, 12, 31)), "p2": wk(D(2018, 1, 1), D(2019, 12, 31))}
    out = {"n_records": len(df), "n_without_district": int((df.unit == 0).sum())}
    P = to_panel(df)
    out["primary"] = run(P, P, W["base"], W["rec"], g)
    out["placebo_2015_17_vs_2018_19"] = run(P, P, W["p1"], W["p2"], g, B=1000)
    out["sens_baseline_2017_19"] = run(P, P, W["b1719"], W["rec"], g, B=1000)
    same = df[df.cmplnt_to_dt.fillna("").str[:10] == df.date]
    out["sens_same_day_end"] = run(to_panel(same), to_panel(same), W["base"], W["rec"], g, B=1000)
    comp = df[df.crm_atpt_cptd_cd == "COMPLETED"]
    out["sens_completed_only"] = run(to_panel(comp), to_panel(comp), W["base"], W["rec"], g, B=1000)
    # weekday index and Monday, Friday separately
    df["d"] = pd.to_datetime(df.date).dt.date
    idx = {}
    for k in ("base", "rec"):
        days = {w + dt.timedelta(i): i for w in W[k] for i in range(5)}
        t = df[df.d.isin(days)].groupby(df.d.map(days)).size()
        idx[k] = {"counts": t.tolist(), "index": (t / t[[1, 2, 3]].mean()).round(4).tolist()}
    out["weekday_index"] = idx
    out["by_day"] = {n: float(np.log(idx["rec"]["index"][i] / idx["base"]["index"][i])) for n, i in (("Mon", 0), ("Fri", 4))}
    # year by year MF/TWT ratio
    yr = {}
    for y in range(2015, 2027):
        days = {w + dt.timedelta(i): i for w in wk(D(y, 1, 1), D(y, 12, 31) if y < 2026 else D(2026, 9, 30)) for i in range(5)}
        t = df[df.d.isin(days)].groupby(df.d.map(days)).size()
        yr[y] = {"n": int(t.sum()), "mf_twt": float(t[[0, 4]].mean() / t[[1, 2, 3]].mean())}
    out["by_year"] = yr
    json.dump(out, open(lib.OUT / "burglary_results.json", "w"), indent=1)
    json.dump(SRC, open(lib.OUT / "burglary_sources.json", "w"), indent=1)
    f = lambda x: f"{x['estimate']:.4f} ({x['lo']:.4f} to {x['hi']:.4f}) se {x['se']:.4f}"
    print(out["n_records"], out["n_without_district"], out["weekday_index"], out["by_day"])
    for k in ("primary", "placebo_2015_17_vs_2018_19", "sens_baseline_2017_19", "sens_same_day_end", "sens_completed_only"):
        r = out[k]; print(k, r["counts"]["all"], "all", f(r["Y_all"]), "| hi", f(r["Y_hi"]), "| lo", f(r["Y_lo"]), "| hi-lo", f(r["hi_minus_lo"]), "| cbd", f(r["Y_cbd"]))
    print({y: (v["n"], round(v["mf_twt"], 3)) for y, v in yr.items()})
