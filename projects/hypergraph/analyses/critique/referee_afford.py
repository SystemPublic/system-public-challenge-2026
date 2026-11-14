"""Referee re-estimation for afford-gentrification-prevalence and afford-poor-count-shift.
Written by the blind referee, not the registrant.

Run from the repository root:
    ~/.venvs/nyc-concordance/bin/python analyses/critique/referee_afford.py

It reads data/derived/affordability/furman_panel.csv only, rebuilds the area table with its own code
(it does not import analyses/affordability/gentrification_test.py), recomputes the deciding numbers and
runs variants the registrant did not run. It prints its results and writes no file.
"""
from __future__ import annotations

import itertools
import math
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "data/derived/affordability/furman_panel.csv"
CITY = "606"
END = ["2022", "2023", "2024"]
MID = ["2005", "2006", "2007"]


def panel():
    p = pd.read_csv(PANEL, dtype={"region_id": str, "year": str})
    return p[p.region_type.isin(["Sub-Borough Area", "City"])].copy()


def avg(p, col, years):
    return p[p.year.isin(years)].groupby("region_id")[col].mean()


def wilson(k, n, z=1.959964):
    ph = k / n
    d = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / d
    h = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def welch(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    va = a.var(ddof=1) / len(a); vb = b.var(ddof=1) / len(b)
    se = math.sqrt(va + vb); d = a.mean() - b.mean()
    df = (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1))
    t = stats.t.ppf(0.975, df)
    return d, d - t * se, d + t * se, se, df


def fmt(w):
    return f"{w[0]:+.3f} ({w[1]:+.3f} to {w[2]:+.3f}), se {w[3]:.3f}, df {w[4]:.1f}"


def build(p, end=END, base=("2000",), sel=("2000",), n_low=22):
    """Area table: growth from `base` to `end`; low-start group chosen on rent in `sel`."""
    names = p.drop_duplicates("region_id").set_index("region_id").region_name
    t = pd.DataFrame({"name": names})
    r0, r1 = avg(p, "rent_gross_med_adj", list(base)), avg(p, "rent_gross_med_adj", end)
    c0, c1 = avg(p, "pop_edu_collp_pct", list(base)), avg(p, "pop_edu_collp_pct", end)
    t["rent_sel"] = avg(p, "rent_gross_med_adj", list(sel))
    t["rent0"], t["rent1"], t["coll0"], t["coll1"] = r0, r1, c0, c1
    t["rg"] = r1 / r0 - 1
    t["cc"] = c1 - c0
    t["poor0"] = avg(p, "pop_pov_pct", ["2000"]) / 100 * avg(p, "pop_num", ["2000"])
    t["pov0"] = avg(p, "pop_pov_pct", ["2000"]); t["pov1"] = avg(p, "pop_pov_pct", end)
    t["pop0"] = avg(p, "pop_num", ["2000"]); t["pop1"] = avg(p, "pop_num", end)
    t["poor1"] = t.pov1 / 100 * t.pop1
    # the registrant's end count is mean(rate) x mean(pop); also the mean of annual products
    q = p[p.year.isin(end)].assign(poor=lambda d: d.pop_pov_pct / 100 * d.pop_num)
    t["poor1_annual"] = q.groupby("region_id").poor.mean()
    t["dlpoor"] = np.log(t.poor1 / t.poor0)
    city = t.loc[CITY]
    s = t.drop(index=CITY).copy()
    s["rank_sel"] = s.rent_sel.rank(method="min")
    s["low"] = s.rank_sel <= n_low
    s["rank0"] = s.rent0.rank(); s["rank1"] = s.rent1.rank()
    s["gent"] = (s.rg > city.rg) & (s.cc > city.cc)
    return s, city


def rho_ci(x, y):
    r = stats.spearmanr(x, y).statistic; n = len(x)
    z = math.atanh(r); se = math.sqrt(1.06 / (n - 3))
    return r, math.tanh(z - 1.959964 * se), math.tanh(z + 1.959964 * se)


def head(s):
    print("\n" + "=" * 100 + "\n" + s + "\n" + "=" * 100)


def main():
    p = panel()
    s, city = build(p)
    low = s[s.low]
    G = list(low.index[low.gent]); N = list(low.index[~low.gent])

    head("1. Reproduction of the deciding numbers")
    k = int(low.gent.sum())
    s2, city2 = build(p, base=MID)
    k2 = int(s2[s2.low].gent.sum())
    print("n areas", len(s), "| n low", int(s.low.sum()), "| k", k, "Wilson", [round(x, 3) for x in wilson(k, 22)], "| k2", k2)
    print("Spearman rent growth x college change, 55 areas:", [round(x, 3) for x in rho_ci(s.rg, s.cc)])
    print("city rent growth %.3f, college change %.2f points" % (city.rg, city.cc))
    print("gentrified:", sorted(low.name[G]))
    w = welch(low.dlpoor[G], low.dlpoor[N])
    print("poor count, Welch gentrified minus other:", fmt(w))
    print("t = %.2f, two-sided p = %.3f" % (w[0] / w[3], 2 * stats.t.sf(abs(w[0] / w[3]), w[4])))
    print("z against the best guess -0.25: %.2f ; against 0: %.2f" % ((w[0] + 0.25) / w[3], w[0] / w[3]))

    head("2. Coverage of the panel: years with values for the deciding columns")
    for col in ["rent_gross_med_adj", "pop_edu_collp_pct", "pop_pov_pct", "pop_num"]:
        yrs = sorted(p[p[col].notna() & (p.region_id != CITY) & (p.year.str.len() == 4)].groupby("year").size().items())
        print(col, [(y, n) for y, n in yrs])

    head("3. The leak: the faulty --simulate run rebuilt, and how much it reveals")
    def sim(seed):
        q = p.copy(); rng = np.random.default_rng(seed); m = q.year != "2000"
        for c in q.columns[4:]:
            q.loc[m, c] = q.loc[m, c] * rng.lognormal(0.3, 0.3, int(m.sum()))
        a, _ = build(q); b, _ = build(q, base=MID)
        la = a[a.low]
        return int(la.gent.sum()), int(b[b.low].gent.sum()), stats.spearmanr(a.rg, a.cc).statistic, set(la.name[la.gent])
    k_s, k2_s, r_s, set_s = sim(0)
    q0 = p.copy(); rng0 = np.random.default_rng(0); m0 = q0.year != "2000"
    for c in q0.columns[4:]:
        q0.loc[m0, c] = q0.loc[m0, c] * rng0.lognormal(0.3, 0.3, int(m0.sum()))
    a0, _ = build(q0); l0 = a0[a0.low]
    print("seed 0, second claim's contrast in the same simulated run (the registration says this part was not read):",
          fmt(welch(l0.dlpoor[l0.gent], l0.dlpoor[~l0.gent])))
    print("seed 0: k", k_s, "k2", k2_s, "rho %.2f" % r_s, sorted(set_s))
    true = set(low.name[G])
    res = [sim(i) for i in range(1, 401)]
    ks = np.array([r[0] for r in res]); rs = np.array([r[2] for r in res])
    ov = np.array([len(r[3] & true) for r in res])
    print("400 other seeds: simulated k mean %.1f, 2.5%% %d, 97.5%% %d; rho mean %.2f (%.2f to %.2f)" % (ks.mean(), *np.percentile(ks, [2.5, 97.5]), rs.mean(), *np.percentile(rs, [2.5, 97.5])))
    print("true gentrified areas among the simulated set: mean %.1f of a simulated k of %.1f" % (ov.mean(), ks.mean()))
    print("share of seeds with simulated k in 4..11: %.2f ; <=1: %.3f ; >=12: %.3f" % (((ks >= 4) & (ks <= 11)).mean(), (ks <= 1).mean(), (ks >= 12).mean()))
    print("noise sd of log rent growth from three annual draws: %.2f ; real sd of log(1+rent growth) over 55 areas: %.2f" % (0.3 / math.sqrt(3), np.log1p(s.rg).std()))
    print("real sd of college change: %.1f points; noise sd on an end share of 30%%: about %.1f points" % (s.cc.std(), 30 * 1.35 * 0.3 / math.sqrt(3)))

    head("4. Margins: how far each low-start area is from each threshold")
    m = low.assign(rent_margin=(low.rg - city.rg) * 100, coll_margin=low.cc - city.cc, rank_move=low.rank1 - low.rank0)
    print(m.sort_values("rg", ascending=False)[["name", "rent0", "rg", "rent_margin", "cc", "coll_margin", "rank0", "rank1", "gent"]].round(2).to_string())

    head("5. Does 8 of 22 depend on the threshold choices?")
    rows = []
    def count(tab, cty, rent_rule, coll_rule, grp):
        g = rent_rule(tab, cty) & coll_rule(tab, cty)
        return int(g[grp].sum()), int(g[~grp].sum())
    rent_rules = {
        "above city": lambda t, c: t.rg > c.rg,
        "above median area": lambda t, c: t.rg > t.rg.median(),
        "city + 5 points": lambda t, c: t.rg > c.rg + 0.05,
        "city + 10 points": lambda t, c: t.rg > c.rg + 0.10,
        "city - 5 points": lambda t, c: t.rg > c.rg - 0.05,
        "dollar rise above city": lambda t, c: (t.rent1 - t.rent0) > (c.rent1 - c.rent0),
        "rank up 5 or more": lambda t, c: (t.rank1 - t.rank0) >= 5,
    }
    coll_rules = {
        "above city": lambda t, c: t.cc > c.cc,
        "above median area": lambda t, c: t.cc > t.cc.median(),
        "city + 3 points": lambda t, c: t.cc > c.cc + 3,
        "city - 3 points": lambda t, c: t.cc > c.cc - 3,
        "relative growth above city": lambda t, c: (t.coll1 / t.coll0) > (c.coll1 / c.coll0),
    }
    print("rent rule x college rule (end 2022-2024, 22 low-start): k among low / k among other 33")
    out = pd.DataFrame(index=rent_rules, columns=coll_rules)
    for a, ra in rent_rules.items():
        for b, cb in coll_rules.items():
            kl, ko = count(s, city, ra, cb, s.low)
            out.loc[a, b] = f"{kl}/{ko}"
    print(out.to_string())
    print("\nsize of the low-start group (registered rule otherwise): n_low -> k, reading window 18%-50% of n")
    for n_low in [11, 14, 16, 18, 20, 22, 24, 27, 28]:
        a, _ = build(p, n_low=n_low); la = a[a.low]
        b, _ = build(p, base=MID, n_low=n_low)
        kk = int(la.gent.sum())
        print(f"  n_low {n_low}: k {kk} ({kk / n_low:.0%}), Wilson {wilson(kk, n_low)[0]:.2f} to {wilson(kk, n_low)[1]:.2f}, k2 {int(b[b.low].gent.sum())}")
    print("\nend period (registered rule otherwise): k, k other 33, rho")
    for e in [["2015", "2016", "2017"], ["2017", "2018", "2019"], ["2018", "2019", "2021"], ["2019", "2021", "2022"], ["2021"], ["2022"], ["2023"], ["2024"], ["2022", "2023"], ["2023", "2024"], END]:
        a, c = build(p, end=e); la = a[a.low]
        r = rho_ci(a.rg, a.cc)
        print(f"  {'-'.join(e):16s} k {int(la.gent.sum())}, other33 {int(a[~a.low].gent.sum())}, rho {r[0]:.2f} ({r[1]:.2f} to {r[2]:.2f}); differs from registered set: {sorted(set(la.name[la.gent]) ^ true)}")
    print("\nlow start defined on household income 2000, and on rent AND income:")
    inc = avg(p, "hh_inc_med_adj", ["2000"]).drop(CITY)
    li = inc.rank(method="min") <= 22
    print("  income: k", int(s.gent[li].sum()), "| both rent and income low: n", int((li & s.low).sum()), "k", int(s.gent[li & s.low].sum()))

    head("6. Is the low-start group different from the rest? (the claim's 'minority' has no comparison in the reading)")
    ko = int(s[~s.low].gent.sum())
    print("low-start %d of 22 (%.0f%%), other %d of 33 (%.0f%%)" % (k, 100 * k / 22, ko, 100 * ko / 33))
    print("Fisher exact two-sided p:", round(stats.fisher_exact([[k, 22 - k], [ko, 33 - ko]])[1], 3))
    print("areas of 55 above city on rent growth:", int((s.rg > city.rg).sum()), "| on college change:", int((s.cc > city.cc).sum()),
          "| both:", int(s.gent.sum()), "| expected both if independent: %.1f" % ((s.rg > city.rg).mean() * (s.cc > city.cc).mean() * 55))
    print("median area rent growth %.3f against city %.3f ; median college change %.1f against city %.1f" % (s.rg.median(), city.rg, s.cc.median(), city.cc))
    print("Spearman within the 22 low-start:", [round(x, 2) for x in rho_ci(low.rg, low.cc)], "| within the other 33:", [round(x, 2) for x in rho_ci(s[~s.low].rg, s[~s.low].cc)])
    # is the city median a moving-composition quantity? city growth against population-weighted mean area growth
    print("population-weighted mean of area rent growth: %.3f" % np.average(s.rg, weights=s.pop0))

    head("7. Regression to the mean in rent among low-start areas")
    print("Spearman of 2000 rent with rent growth 2000 to end, all 55: %.2f ; within low-start 22: %.2f" % (stats.spearmanr(s.rent0, s.rg).statistic, stats.spearmanr(low.rent0, low.rg).statistic))
    print("Spearman of 2000 rent with rent growth from 2005-07 to end (k2 baseline), all 55: %.2f" % stats.spearmanr(s2.rent_sel, s2.rg).statistic)
    print("low-start above city on rent growth from 2000: %d of 22 ; other: %d of 33" % ((low.rg > city.rg).sum(), (s[~s.low].rg > city.rg).sum()))
    print("low-start above city on rent growth from 2005-07: %d of 22 ; other: %d of 33" % ((s2[s2.low].rg > city2.rg).sum(), (s2[~s2.low].rg > city2.rg).sum()))
    a, c = build(p, base=MID, sel=MID); la = a[a.low]
    print("selection AND baseline on 2005-07 (no 2000 value used): k", int(la.gent.sum()), sorted(la.name[la.gent]))
    a, c = build(p, base=MID, sel=("2000",)); la = a[a.low]
    print("k2 set:", sorted(la.name[la.gent]), "| differs from k set:", sorted(set(la.name[la.gent]) ^ true))
    a, c = build(p, base=("2008", "2009", "2010"), sel=("2000",)); la = a[a.low]
    print("baseline 2008-10, selection 2000: k", int(la.gent.sum()), sorted(la.name[la.gent]))
    # rank persistence: ranks 2000 to 2005-07 against 2005-07 to end
    mid_rank = avg(p, "rent_gross_med_adj", MID).drop(CITY).rank()
    print("rank change 2000 to 2005-07 against rank change 2005-07 to end, low-start: Spearman %.2f (negative would indicate reversion of a 2000 error)" %
          stats.spearmanr((mid_rank - s.rank0)[s.low], (s.rank1 - mid_rank)[s.low]).statistic)
    print("low-start areas: mean rank change %.1f ; number rising in rank %d, falling %d" % ((low.rank1 - low.rank0).mean(), ((low.rank1 - low.rank0) > 0).sum(), ((low.rank1 - low.rank0) < 0).sum()))

    head("8. The 2022 boundary change")
    pop = p[p.year.str.len() == 4].pivot(index="region_id", columns="year", values="pop_num").drop(index=CITY)
    for a_, b_ in [("2011", "2012"), ("2017", "2018"), ("2018", "2019"), ("2021", "2022"), ("2022", "2023"), ("2023", "2024")]:
        j = np.log(pop[b_] / pop[a_])
        print(f"  {a_}->{b_}: areas with |change| > 8%: {int((j.abs() > 0.08).sum())} of 55; among 22 low-start {int((j[s.low].abs() > 0.08).sum())}; sd of log change {j.std():.3f}")
    j = np.log(pop["2022"] / pop["2021"])
    for col in ["rent_gross_med_adj", "pop_edu_collp_pct", "pop_pov_pct"]:
        v = p[p.year.str.len() == 4].pivot(index="region_id", columns="year", values=col)
        rel = (v.drop(index=CITY).sub(v.loc[CITY], axis=1) if col != "rent_gross_med_adj" else np.log(v.drop(index=CITY).div(v.loc[CITY], axis=1)))
        d22 = rel["2022"] - rel["2021"]; d19 = rel["2019"] - rel["2018"]; d18 = rel["2018"] - rel["2017"]
        print(f"  {col}: sd of one-year change relative to city: 2017->18 {d18.std():.3f}, 2018->19 {d19.std():.3f}, 2021->22 {d22.std():.3f}; corr of 2021->22 change with population jump {stats.spearmanr(d22, j).statistic:.2f}")
    print("  population jump 2021->22, gentrified:", {s.name[i]: round(float(np.expm1(j[i]) * 100)) for i in G})
    print("  population jump 2021->22, other low-start:", {s.name[i]: round(float(np.expm1(j[i]) * 100)) for i in N})

    head("9. Poor count: variants")
    def contrast(end, groups=None, y="count"):
        a, c = build(p, end=end)
        g, n = groups if groups else (list(a.index[a.low & a.gent]), list(a.index[a.low & ~a.gent]))
        if y == "count": v = a.dlpoor
        elif y == "annual": v = np.log(a.poor1_annual / a.poor0)
        elif y == "rate": v = a.pov1 - a.pov0
        elif y == "pop": v = np.log(a.pop1 / a.pop0)
        elif y == "lograte": v = np.log(a.pov1 / a.pov0)
        return welch(v[g], v[n]), v
    print("registered groups (8 and 14) throughout unless stated")
    for e in [END, ["2022"], ["2023"], ["2024"], ["2022", "2023"], ["2023", "2024"], ["2017", "2018", "2019"], ["2018", "2019", "2021"], ["2015", "2016", "2017"], ["2019"], ["2021"]]:
        w, _ = contrast(e, (G, N))
        print(f"  end {'-'.join(e):16s} log poor count {fmt(w)}")
    print("  end 2022-2024, mean of annual counts instead of mean rate x mean population:", fmt(contrast(END, (G, N), "annual")[0]))
    print("  end 2022-2024, log population change:", fmt(contrast(END, (G, N), "pop")[0]))
    print("  end 2022-2024, log poverty rate change:", fmt(contrast(END, (G, N), "lograte")[0]))
    print("  end 2022-2024, poverty rate change in points:", fmt(contrast(END, (G, N), "rate")[0]))
    print("  end 2017-2019, log population change:", fmt(contrast(["2017", "2018", "2019"], (G, N), "pop")[0]))
    v = low.dlpoor
    print("\n  per-area log change in poor count, 2000 to 2022-2024 and to 2017-2019:")
    a19, _ = build(p, end=["2017", "2018", "2019"])
    tab = pd.DataFrame({"name": low.name, "gent": low.gent, "to_2022_24": v, "to_2017_19": a19.dlpoor[low.index], "pop_jump_21_22": j[low.index],
                        "pov0": low.pov0, "pov1": low.pov1}).sort_values(["gent", "to_2022_24"])
    print(tab.round(3).to_string())
    print("  sd within groups, 2022-24: gent %.3f other %.3f ; 2017-19: gent %.3f other %.3f" % (v[G].std(), v[N].std(), a19.dlpoor[G].std(), a19.dlpoor[N].std()))
    print("  correlation of the 2017-19 and 2022-24 log changes across the 22: %.2f" % stats.pearsonr(v, a19.dlpoor[low.index])[0])
    print("  correlation of (2022-24 minus 2017-19 log change) with the 2021->22 population jump: %.2f" % stats.pearsonr(v - a19.dlpoor[low.index], j[low.index])[0])

    print("\n  other tests on the registered contrast:")
    print("   pooled-variance t interval:", fmt((lambda a, b: (lambda d, se, df: (d, d - stats.t.ppf(.975, df) * se, d + stats.t.ppf(.975, df) * se, se, df))(
        a.mean() - b.mean(), math.sqrt(((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) / (len(a) + len(b) - 2) * (1 / len(a) + 1 / len(b))), len(a) + len(b) - 2))(v[G].values, v[N].values)))
    print("   Mann-Whitney two-sided p: %.3f" % stats.mannwhitneyu(v[G], v[N]).pvalue)
    obs = v[G].mean() - v[N].mean(); vals = v.values; idx = range(22)
    rng = np.random.default_rng(20261113); cnt = 0; B = 100000
    for _ in range(B):
        pm = rng.permutation(22); d = vals[pm[:8]].mean() - vals[pm[8:]].mean()
        cnt += abs(d) >= abs(obs) - 1e-12
    print("   permutation two-sided p (100,000 draws): %.3f" % (cnt / B))
    print("   leave one area out, upper limit of the Welch interval:")
    worst = []
    for i in low.index:
        g = [x for x in G if x != i]; n = [x for x in N if x != i]
        ww = welch(v[g], v[n]); worst.append((ww[2], low.name[i], "gent" if i in G else "other", ww[0]))
    worst.sort(reverse=True)
    for u, nm, grp, d in worst[:8]:
        print(f"     without {nm} ({grp}): diff {d:+.3f}, upper {u:+.3f}")
    print("     number of the 22 single removals that put the upper limit at or above 0: %d" % sum(u >= 0 for u, *_ in worst))
    print("   one area at a time moved to the other group (areas within 10 points of the rent threshold that meet the college condition):")
    near = [i for i in low.index if abs(low.rg[i] - city.rg) < 0.10]
    print("     near threshold:", {low.name[i]: (round(float((low.rg[i] - city.rg) * 100), 1), bool(low.gent[i])) for i in near})
    for r in [1]:
        for combo in itertools.combinations(near, r):
            if not all(low.cc[i] > city.cc for i in combo): continue
            g = [x for x in G if x not in combo] + [x for x in combo if x not in G]
            n = [x for x in low.index if x not in g]
            if len(g) < 3: continue
            ww = welch(v[g], v[n])
            print(f"     flip {[low.name[i] for i in combo]}: n {len(g)}/{len(n)}, {fmt(ww)}")
    print("   groups under other definitions, end 2022-2024:")
    for label, g in [("rent condition only", list(low.index[low.rg > city.rg])), ("college condition only", list(low.index[low.cc > city.cc])),
                     ("rank up 5 or more and college above city", list(low.index[((low.rank1 - low.rank0) >= 5) & (low.cc > city.cc)])),
                     ("k2 definition (baseline 2005-07)", list(s2.index[s2.low & s2.gent]))]:
        n = [x for x in low.index if x not in g]
        print(f"     {label}: n {len(g)}/{len(n)}, {fmt(welch(v[g], v[n]))}")
    print("   continuous version, slope of log poor-count change on rent growth and on college change over the 22:")
    for xname, x in [("rent growth", low.rg), ("college change (per 10 points)", low.cc / 10)]:
        lr = stats.linregress(x, v); tq = stats.t.ppf(.975, 20)
        print(f"     {xname}: {lr.slope:+.3f} ({lr.slope - tq * lr.stderr:+.3f} to {lr.slope + tq * lr.stderr:+.3f}), Spearman {stats.spearmanr(x, v).statistic:+.2f}")

    head("10. What a falling poor count can show")
    for label, idx_ in [("gentrified 8", G), ("other low-start 14", N), ("other 33", list(s.index[~s.low]))]:
        a = s.loc[idx_]
        nonpoor0 = a.pop0.sum() - a.poor0.sum(); nonpoor1 = a.pop1.sum() - a.poor1.sum()
        print(f"  {label}: poor {a.poor0.sum():,.0f} -> {a.poor1.sum():,.0f} ({a.poor1.sum() / a.poor0.sum() - 1:+.1%}); non-poor {nonpoor0:,.0f} -> {nonpoor1:,.0f} ({nonpoor1 / nonpoor0 - 1:+.1%}); "
              f"population {a.pop1.sum() / a.pop0.sum() - 1:+.1%}; poverty rate {100 * a.poor0.sum() / a.pop0.sum():.1f} -> {100 * a.poor1.sum() / a.pop1.sum():.1f}")
    print("  city row: poverty rate %.1f -> %.1f, population %.0f -> %.0f" % (city.pov0, city.pov1, city.pop0, city.pop1))
    print("  2000 poverty rate, gentrified mean %.1f, other low-start mean %.1f ; Spearman of 2000 poverty rate with log change in poor count over the 22: %.2f" %
          (low.pov0[G].mean(), low.pov0[N].mean(), stats.spearmanr(low.pov0, v).statistic))
    lr = np.linalg.lstsq(np.column_stack([np.ones(22), low.gent.astype(float), low.pov0]), v, rcond=None)
    X = np.column_stack([np.ones(22), low.gent.astype(float), low.pov0]); beta = lr[0]; resid = v - X @ beta
    cov = np.linalg.inv(X.T @ X) * (resid @ resid) / 19; se = math.sqrt(cov[1, 1]); tq = stats.t.ppf(.975, 19)
    print("  contrast adjusted for the 2000 poverty rate (OLS): %+.3f (%+.3f to %+.3f)" % (beta[1], beta[1] - tq * se, beta[1] + tq * se))
    print("  borough (first digit of the area code: 1 Manhattan, 2 Bronx, 3 Brooklyn, 4 Queens), gentrified / other low-start:")
    boro = pd.Series(low.index.str[0], index=low.index)
    for bb in sorted(boro.unique()):
        ii = boro.index[boro == bb]; gg = [i for i in ii if i in G]; nn = [i for i in ii if i in N]
        print(f"    borough {bb}: {len(gg)} / {len(nn)}; mean log change {v[gg].mean() if gg else float('nan'):+.3f} / {v[nn].mean() if nn else float('nan'):+.3f}"
              f"; to 2017-19 {a19.dlpoor[gg].mean() if gg else float('nan'):+.3f} / {a19.dlpoor[nn].mean() if nn else float('nan'):+.3f}")
    for lab, yy in [("2022-24", v), ("2017-19", a19.dlpoor[low.index])]:
        Xb = np.column_stack([low.gent.astype(float)] + [(boro == bb).astype(float) for bb in sorted(boro.unique())])
        bt = np.linalg.lstsq(Xb, yy.values, rcond=None)[0]; rs = yy.values - Xb @ bt; dfb = 22 - Xb.shape[1]
        seb = math.sqrt((np.linalg.inv(Xb.T @ Xb) * (rs @ rs) / dfb)[0, 0]); tqb = stats.t.ppf(.975, dfb)
        print(f"    contrast within borough (OLS with borough terms), end {lab}: {bt[0]:+.3f} ({bt[0] - tqb * seb:+.3f} to {bt[0] + tqb * seb:+.3f}), df {dfb}")
    nb = [i for i in N if i[0] != "2"]
    print("    without the seven Bronx areas (8 against 7):", fmt(welch(v[G], v[nb])), "| to 2017-19:", fmt(welch(a19.dlpoor[G], a19.dlpoor[nb])))
    print("  leave one area out with the end period 2017-2019: largest upper limit %+.3f" % max(
        welch(a19.dlpoor[[x for x in G if x != i]], a19.dlpoor[[x for x in N if x != i]])[2] for i in low.index))
    print("  timing: log change in poor count by period, registered groups")
    for (b0, b1, lab) in [(["2000"], MID, "2000 to 2005-07"), (MID, ["2010", "2011", "2012"], "2005-07 to 2010-12"), (["2010", "2011", "2012"], ["2017", "2018", "2019"], "2010-12 to 2017-19"), (["2017", "2018", "2019"], END, "2017-19 to 2022-24")]:
        c0 = avg(p, "pop_pov_pct", b0) * avg(p, "pop_num", b0); c1 = avg(p, "pop_pov_pct", b1) * avg(p, "pop_num", b1)
        d = np.log(c1 / c0)
        print(f"    {lab}: {fmt(welch(d[G], d[N]))}")


if __name__ == "__main__":
    main()
