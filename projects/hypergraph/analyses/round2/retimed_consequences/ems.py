"""retimed-ems-presence: daytime EMS incidents by community district, Monday and Friday against midweek."""
import datetime as dt, json, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib
from concord import socrata

SRC = []
CBD = "('101','102','103','104','105','106')"


def panel(lo, hi):
    rows, src = socrata.query("76xm-jjuj", select="date_trunc_ymd(incident_datetime) as d, communitydistrict as cd, count(*) as n",
                              where=f"incident_datetime between '{lo}T00:00:00' and '{hi}T23:59:59' and date_extract_hh(incident_datetime) between 6 and 19",
                              group="d, cd", order="d, cd", limit=50000)
    assert len(rows) < 50000
    SRC.append(src)
    p = pd.DataFrame(rows).dropna(subset=["cd"])
    p["unit"] = p.cd.astype(int); p["n"] = p.n.astype(int); p["date"] = p.d.str[:10]
    return p[["unit", "date", "n"]]


def detail(lo, hi):
    """By date, hour and severity group, for the secondary analyses; unit is the district."""
    rows, src = socrata.query_all("76xm-jjuj", select="date_trunc_ymd(incident_datetime) as d, communitydistrict as cd, "
                                  "case(date_extract_hh(incident_datetime) < 10, 'am', date_extract_hh(incident_datetime) < 16, 'mid', true, 'pm') as band, "
                                  "case(initial_severity_level_code in ('1','2','3'), 'high', true, 'low') as sev, count(*) as n",
                                  where=f"incident_datetime between '{lo}T00:00:00' and '{hi}T23:59:59' and date_extract_hh(incident_datetime) between 6 and 19",
                                  group="d, cd, band, sev", order="d, cd, band, sev")
    SRC.append(src)
    p = pd.DataFrame(rows).dropna(subset=["cd"])
    p["unit"] = p.cd.astype(int); p["n"] = p.n.astype(int); p["date"] = p.d.str[:10]
    return p


def run(P0, P1, w0, w1, ex, B=2000):
    units = ex.community_district.tolist()
    cbd = (ex.cbd_share_entries > 0.5).values
    A0, A1 = lib.week_arrays(P0, units, w0), lib.week_arrays(P1, units, w1)
    r = lib.estimate(A0, A1, ex.E_day.values, {"cbd": cbd, "rest": ~cbd}, B=B)
    r["daily_cbd"] = [float((A[0][cbd].sum() + A[1][cbd].sum()) / (5 * A[0].shape[1])) for A in (A0, A1)]
    r["daily_rest"] = [float((A[0][~cbd].sum() + A[1][~cbd].sum()) / (5 * A[0].shape[1])) for A in (A0, A1)]
    return r, (A0, A1, cbd)


if __name__ == "__main__":
    ex = pd.read_csv(lib.OUT / "exposure_community_district.csv")
    ex = ex[ex.community_district % 100 <= 18].reset_index(drop=True)
    g = json.load(open(lib.OUT / "exposure_groups.json"))
    dE = g["g_ems_day"]["cbd"] - g["g_ems_day"]["rest"]
    D = dt.date
    yr = {y: panel(f"{y}-01-01", f"{y}-12-31") for y in (2016, 2017, 2018, 2019)}
    rec = pd.concat([panel("2024-10-01", "2025-09-30"), panel("2025-10-01", "2026-09-30")])
    base = pd.concat([yr[2018], yr[2019]])
    wk = lambda a, b: lib.retained_weeks(a, b)
    w_base = wk(D(2018, 1, 1), D(2019, 12, 31)); w_rec = wk(D(2024, 10, 1), D(2026, 9, 30))
    out = {"dE": dE}
    out["primary"], (A0, A1, cbd) = run(base, rec, w_base, w_rec, ex)
    C = out["primary"]["cbd_minus_rest"]
    out["elasticity"] = {"estimate": C["estimate"] / dE, "lo": C["hi"] / dE, "hi": C["lo"] / dE}
    out["placebo_2016_17_vs_2018_19"], _ = run(pd.concat([yr[2016], yr[2017]]), base, wk(D(2016, 1, 1), D(2017, 12, 31)), w_base, ex)
    out["sens_2019_vs_last12m"], _ = run(yr[2019], rec, wk(D(2019, 1, 1), D(2019, 12, 31)), wk(D(2025, 10, 1), D(2026, 9, 30)), ex)
    # Monday and Friday separately (pooled groups)
    def day_split(P, weeks):
        p = P.copy(); p["date"] = pd.to_datetime(p.date).dt.date
        days = {w + dt.timedelta(i): i for w in weeks for i in range(5)}
        p = p[p.date.isin(days) & p.unit.isin(ex.community_district)]
        p["dow"] = p.date.map(days); p["cbd"] = p.unit.isin([101, 102, 103, 104, 105, 106])
        t = p.groupby(["cbd", "dow"]).n.sum().unstack() / len(weeks)
        return t
    t0, t1 = day_split(base, w_base), day_split(rec, w_rec)
    out["by_day"] = {}
    for name, dcol in (("Mon", 0), ("Fri", 4)):
        f = lambda t, c: np.log(t.loc[c, dcol] / t.loc[c, [1, 2, 3]].mean())
        out["by_day"][name] = {"Y_cbd": float(f(t1, True) - f(t0, True)), "Y_rest": float(f(t1, False) - f(t0, False))}
    out["weekday_index"] = {k: {("cbd" if c else "rest"): (t.loc[c] / t.loc[c, [1, 2, 3]].mean()).round(4).tolist() for c in (True, False)} for k, t in (("baseline", t0), ("recent", t1))}
    # secondary: hour bands and severity
    try:
        d0 = pd.concat([detail("2018-01-01", "2018-12-31"), detail("2019-01-01", "2019-12-31")])
        d1 = pd.concat([detail("2024-10-01", "2025-09-30"), detail("2025-10-01", "2026-09-30")])
        out["secondary"] = {}
        for key, f in (("hours_06_09", lambda d: d[d.band == "am"]), ("hours_10_15", lambda d: d[d.band == "mid"]), ("hours_16_19", lambda d: d[d.band == "pm"]),
                       ("high_severity", lambda d: d[d.sev == "high"])):
            a = f(d0).groupby(["unit", "date"], as_index=False).n.sum(); b = f(d1).groupby(["unit", "date"], as_index=False).n.sum()
            out["secondary"][key], _ = run(a, b, w_base, w_rec, ex, B=1000)
    except Exception as e:  # report what could not be done
        out["secondary_error"] = repr(e)
    Yu = lib._r(*A1) - lib._r(*A0)
    ex.assign(Y=Yu, cbd=cbd).to_csv(lib.OUT / "ems_by_district.csv", index=False)
    json.dump(out, open(lib.OUT / "ems_results.json", "w"), indent=1)
    json.dump(SRC, open(lib.OUT / "ems_sources.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "secondary"}, indent=1)[:5000])
