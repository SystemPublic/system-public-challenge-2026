"""Coffee shops: density by NTA, chains and independents, what density goes with, and timing against rents.

Coffee shops are establishments with cuisine "Coffee/Tea" and at least one inspection in the DOHMH table
(43nn-pn8j). Dunkin' is mostly coded "Donuts" by the city and is therefore mostly outside this set.
A chain is a name that, after cleaning, has five or more establishments in the whole restaurant table.
Neighbourhood measures come from acs_nta.py. Associations are Spearman correlations across NTAs with at
least 5,000 residents, with bootstrap 95% intervals (2,000 resamples, seed 20261113).
Timing uses Census ZIP Code Business Patterns counts of snack and nonalcoholic beverage bars (NAICS
722515) and the Zillow Observed Rent Index by ZIP code. All of this is exploratory; nothing was registered.
Output data/derived/explore/coffee_nta.csv, coffee_summary.json.
"""
from __future__ import annotations

import json
import re

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy.stats import spearmanr

from common import OUT, RAW, ntas, pluto, tract_table

SEED = 20261113
DROP = {"COFFEE", "COMPANY", "CO", "ROASTERS", "ROASTER", "ROASTING", "CAFE", "THE", "NYC", "INC", "LLC", "SHOP", "BAR", "AND", "ESPRESSO"}
TEA = re.compile(r"\bTEA\b|BOBA|MATCHA|\bCHA\b|HEYTEA|TIGER SUGAR|MILKY|\bTEAS\b|TEAHOUSE|YI FANG|MOGE|XING FU TANG")


def clean(name: str) -> str:
    s = re.sub(r"[^A-Z0-9 ]", "", str(name).upper().replace("&", " AND "))
    s = re.sub(r"\b\d+\b", " ", s)
    toks = [t for t in s.split() if t not in DROP]
    k = " ".join(toks)
    for pre in ("STARBUCKS", "DUNKIN", "BLANK STREET", "JOE", "GREGORYS", "BLUE BOTTLE", "PRET"):
        if k.startswith(pre) and (pre != "JOE" or k in ("JOE", "JOE PRO SHOP", "JOE AND JUICE") or str(name).upper().startswith("JOE COFFEE")):
            return pre
    return k


def boot_spearman(x, y, rng, n=2000):
    x, y = np.asarray(x, float), np.asarray(y, float)
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    r = spearmanr(x, y)[0]
    idx = rng.integers(0, len(x), (n, len(x)))
    bs = [spearmanr(x[i], y[i])[0] for i in idx]
    return {"rho": float(r), "lo": float(np.percentile(bs, 2.5)), "hi": float(np.percentile(bs, 97.5)), "n": int(len(x))}


def main():
    rng = np.random.default_rng(SEED)
    r = pd.read_csv(OUT / "restaurants_nta.csv", dtype={"camis": str})
    r["key"] = r.dba.map(clean)
    size = r[r.inspected].groupby("key").size()
    r["chain"] = (r.key.map(size).fillna(0) >= 5) & (r.key.str.len() > 0)
    c = r[(r.cuisine_description == "Coffee/Tea") & r.inspected].copy()
    c["tea"] = c.dba.fillna("").str.upper().str.contains(TEA)
    S = {"coffee_tea_establishments": len(c), "chain": int(c.chain.sum()), "independent": int((~c.chain).sum()),
         "tea_named": int(c.tea.sum()), "new_since_sep_2024": int(c.new.sum()),
         "new_chain": int((c.new & c.chain).sum()), "new_independent": int((c.new & ~c.chain).sum()),
         "top_chains": c[c.chain].key.value_counts().head(15).to_dict(),
         "dunkin_all_cuisines": int((r.key == "DUNKIN").sum()), "dunkin_in_coffee_tea": int((c.key == "DUNKIN").sum())}

    a = pd.read_csv(OUT / "acs_nta.csv").set_index("nta")
    g = ntas().set_index("nta")
    T = pd.DataFrame({"coffee": c.groupby("nta").size(), "chain": c[c.chain].groupby("nta").size(),
                      "independent": c[~c.chain].groupby("nta").size(), "coffee_new": c[c.new].groupby("nta").size()})
    T = a.join(T).fillna({"coffee": 0, "chain": 0, "independent": 0, "coffee_new": 0})
    T["km2"] = g.km2.reindex(T.index)
    T["name"] = g.name.reindex(T.index)
    T["density"] = T["pop"] / T.km2
    for k in ("coffee", "chain", "independent"):
        T[k + "_per_10k"] = 1e4 * T[k] / T["pop"].replace(0, np.nan)
        T[k + "_per_km2"] = T[k] / T.km2
    T["chain_share"] = T.chain / T.coffee.replace(0, np.nan)
    T.to_csv(OUT / "coffee_nta.csv")
    R = T[T["pop"] >= 5000]
    S["n_nta"] = len(R)
    S["city_per_10k"] = float(1e4 * R.coffee.sum() / R["pop"].sum())
    S["nta_with_none"] = int((R.coffee == 0).sum())
    S["top_per_10k"] = R.sort_values("coffee_per_10k", ascending=False).head(12)[["name", "coffee", "chain", "independent", "coffee_per_10k"]].to_dict("records")
    S["top_independent_per_10k"] = R.sort_values("independent_per_10k", ascending=False).head(12)[["name", "independent", "independent_per_10k", "chain_share"]].to_dict("records")
    S["highest_chain_share"] = R[R.coffee >= 12].sort_values("chain_share", ascending=False).head(8)[["name", "coffee", "chain_share"]].to_dict("records")
    S["lowest_chain_share"] = R[R.coffee >= 12].sort_values("chain_share").head(8)[["name", "coffee", "chain_share"]].to_dict("records")
    S["none"] = R[R.coffee == 0].sort_values("pop", ascending=False).head(12)[["name", "pop"]].to_dict("records")
    cov = ["income", "rent22", "d_logrent", "ba_share", "share_25_34", "share_65", "arts_share22", "poverty", "nhw_share22", "d_nhw", "density"]
    S["spearman"] = {y: {x: boot_spearman(R[x], R[y], rng) for x in cov} for y in ("coffee_per_10k", "independent_per_10k", "chain_per_10k")}
    Z = R.dropna(subset=["income", "rent22", "d_logrent", "ba_share", "share_25_34"]).copy()
    for x in ("income", "rent22", "d_logrent", "ba_share", "share_25_34", "density"):
        Z["z_" + x] = (Z[x] - Z[x].mean()) / Z[x].std()
    Z["y"] = np.log1p(Z.coffee_per_10k)
    m = smf.ols("y ~ z_ba_share + z_share_25_34 + z_rent22 + z_d_logrent + z_density", Z).fit(cov_type="HC3")
    ci = m.conf_int()
    S["ols_log1p_per_10k"] = {k: {"b": float(m.params[k]), "lo": float(ci.loc[k, 0]), "hi": float(ci.loc[k, 1])} for k in m.params.index if k != "Intercept"}
    S["ols_n"], S["ols_r2"] = int(m.nobs), float(m.rsquared)

    # time: ZBP by year, city and borough
    z = pd.read_csv(OUT / "zbp_extract.csv", dtype={"zip": str})
    p = pluto()
    zb = p[p.zipcode.notna()].groupby(p.zipcode.str[:5]).boro.agg(lambda s: s.mode().iloc[0])
    z["boro"] = z.zip.map(zb)
    sb = z[(z.series == "snack_beverage") & z.boro.notna()]
    S["zbp_snack_beverage_by_year"] = {int(k): int(v) for k, v in sb.groupby("year").est.sum().items()}
    S["zbp_by_boro_2012_2019_2023"] = {b: {int(y): int(v) for y, v in g2.groupby("year").est.sum().reindex([2012, 2019, 2023]).items()}
                                         for b, g2 in sb.groupby("boro")}

    # timing against rent (ZIP codes; ZORI from 2015)
    zo = pd.read_csv(RAW / "zori" / "zip_zori.csv", dtype={"RegionName": str})
    zo = zo[zo.State == "NY"].set_index(zo.RegionName[zo.State == "NY"].str.zfill(5))
    months = [c for c in zo.columns if re.match(r"\d{4}-\d{2}-\d{2}", c)]
    rent = zo[months].T
    rent.index = pd.to_datetime(rent.index)
    rent = rent.groupby(rent.index.year).mean().T          # zip x year
    cof = sb.pivot_table(index="zip", columns="year", values="est", aggfunc="sum")
    S["zori_first_year"] = int(rent.columns.min())
    tim = {}
    for a0, a1, a2 in ((2015, 2017, 2019), (2015, 2019, 2023), (2016, 2018, 2020)):
        zs = [q for q in cof.index if q in rent.index and all(pd.notna(cof.loc[q, y]) for y in (a0, a1, a2))
              and all(pd.notna(rent.loc[q, y]) for y in (a0, a1, a2))]
        d = pd.DataFrame({"dc1": np.log(cof.loc[zs, a1] / cof.loc[zs, a0]), "dc2": np.log(cof.loc[zs, a2] / cof.loc[zs, a1]),
                          "dr1": np.log(rent.loc[zs, a1] / rent.loc[zs, a0]), "dr2": np.log(rent.loc[zs, a2] / rent.loc[zs, a1]),
                          "lc": np.log(cof.loc[zs, a0]), "lr": np.log(rent.loc[zs, a0])})
        m1 = smf.ols("dr2 ~ dc1 + dr1 + lr + lc", d).fit(cov_type="HC3")
        m2 = smf.ols("dc2 ~ dr1 + dc1 + lr + lc", d).fit(cov_type="HC3")
        tim[f"{a0}-{a1}-{a2}"] = {
            "n_zip": len(d),
            "coffee_then_rent": boot_spearman(d.dc1, d.dr2, rng), "rent_then_coffee": boot_spearman(d.dr1, d.dc2, rng),
            "same_period": boot_spearman(d.dc1, d.dr1, rng),
            "ols_rent_on_earlier_coffee": {"b": float(m1.params["dc1"]), "lo": float(m1.conf_int().loc["dc1", 0]), "hi": float(m1.conf_int().loc["dc1", 1])},
            "ols_coffee_on_earlier_rent": {"b": float(m2.params["dr1"]), "lo": float(m2.conf_int().loc["dr1", 0]), "hi": float(m2.conf_int().loc["dr1", 1])}}
    S["timing"] = tim
    # longer window: ACS tract rents (2008-2012 and 2018-2022) moved to ZIP codes through PLUTO lots
    # (each tract goes to the ZIP code that holds most of its lots), against ZBP counts in 2003, 2011, 2019, 2023.
    tz = p[p.zipcode.notna() & p.bct2020.notna()].groupby("bct2020").zipcode.agg(lambda s: s.str[:5].mode().iloc[0])
    tt = tract_table().copy()
    tt["zip"] = tt.boroct2020.map(tz)
    tt = tt[tt.zip.notna() & (tt["pop"] > 0)]

    def wm(g2, col):
        m = g2[col].notna()
        return np.average(g2.loc[m, col], weights=g2.loc[m, "pop"]) if m.any() else np.nan

    Zr = pd.DataFrame({"pop": tt.groupby("zip")["pop"].sum(), "rent12": tt.groupby("zip").apply(lambda g2: wm(g2, "rent12")),
                       "rent22": tt.groupby("zip").apply(lambda g2: wm(g2, "rent22"))})
    Zr = Zr[(Zr["pop"] >= 5000) & Zr.rent12.notna() & Zr.rent22.notna()]
    cz = cof.reindex(Zr.index)
    for y in (2003, 2011):
        cz[y] = cz[y].fillna(0)              # no withholding before 2017: absent means none
    Zr["c03"], Zr["c11"], Zr["c19"], Zr["c23"] = cz[2003], cz[2011], cz[2019], cz[2023]
    Zr["d_before"] = 1e4 * (Zr.c11 - Zr.c03) / Zr["pop"]
    Zr["d_during"] = 1e4 * (Zr.c19 - Zr.c11) / Zr["pop"]
    Zr["d_after"] = 1e4 * (Zr.c23 - Zr.c19) / Zr["pop"]
    Zr["dlr"] = np.log(Zr.rent22 / Zr.rent12)
    Zr["lr12"] = np.log(Zr.rent12)
    L = {"n_zip": len(Zr), "coffee_2003_11_then_rent_2010_20": boot_spearman(Zr.d_before, Zr.dlr, rng),
         "coffee_2011_19_with_rent_2010_20": boot_spearman(Zr.d_during, Zr.dlr, rng),
         "rent_2010_20_then_coffee_2019_23": boot_spearman(Zr.dlr, Zr.d_after, rng)}
    m3 = smf.ols("dlr ~ d_before + lr12", Zr).fit(cov_type="HC3")
    L["ols_rent_change_on_earlier_coffee_change"] = {"b": float(m3.params["d_before"]), "lo": float(m3.conf_int().loc["d_before", 0]),
                                                     "hi": float(m3.conf_int().loc["d_before", 1]), "n": int(m3.nobs),
                                                     "unit": "log rent change per added outlet per 10,000 residents"}
    Za = Zr.dropna(subset=["d_after"])
    m4 = smf.ols("d_after ~ dlr + lr12 + d_during", Za).fit(cov_type="HC3")
    L["ols_later_coffee_change_on_rent_change"] = {"b": float(m4.params["dlr"]), "lo": float(m4.conf_int().loc["dlr", 0]),
                                                   "hi": float(m4.conf_int().loc["dlr", 1]), "n": int(m4.nobs),
                                                   "unit": "outlets per 10,000 residents per unit of log rent change"}
    S["timing_long"] = L
    Zr.to_csv(OUT / "coffee_zip_timing.csv")
    (OUT / "coffee_summary.json").write_text(json.dumps(S, indent=1, default=float))
    print(json.dumps(S, indent=1, default=float))


if __name__ == "__main__":
    main()
