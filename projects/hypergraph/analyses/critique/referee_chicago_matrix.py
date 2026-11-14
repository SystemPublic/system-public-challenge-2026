"""Blind referee re-estimate for claim transfer-chicago-concordance-matrix.

Written without reading the registrant's write-ups. Reads only the indicator tables and the literature signs,
and recomputes the deciding quantities with its own code (ranks, residuals on poverty, Pearson of residuals).
Community-area boundaries are fetched from the Chicago Data Portal (dataset igwz-8jzy) into the system
temporary folder when absent; nothing is written into the repository.

    python analyses/critique/referee_chicago_matrix.py
"""
import json
import tempfile
import urllib.request
from math import comb
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
NY = ROOT / "data" / "derived" / "graph" / "concordance"
CH = ROOT / "data" / "derived" / "round5" / "chicago_matrix"
TMP = Path(tempfile.gettempdir()) / "referee_chicago_matrix"
EXPO = ["pm25", "ozone", "traffic"]
SEED = 77042
DRAWS = 2000


def rank(t):
    return t.rank()


def resid(y, Z):
    """Residual of y on the columns of Z (with intercept); rows with a missing value give NaN."""
    Z = np.column_stack([np.ones(len(y))] + [np.asarray(z, float) for z in Z])
    ok = ~np.isnan(y) & ~np.isnan(Z).any(axis=1)
    out = np.full(len(y), np.nan)
    b = np.linalg.lstsq(Z[ok], y[ok], rcond=None)[0]
    out[ok] = y[ok] - Z[ok] @ b
    return out


def pcor(t, a, b, controls=("poverty",)):
    """Spearman partial correlation: ranks, residuals on the controls' ranks, Pearson of the residuals."""
    R = rank(t)
    x, y = R[a].to_numpy(float), R[b].to_numpy(float)
    cs = [c for c in controls if c not in (a, b)]
    if cs:
        Z = [R[c].to_numpy(float) if c in R else t[c].rank().to_numpy(float) for c in cs]
        x, y = resid(x, Z), resid(y, Z)
    ok = ~np.isnan(x) & ~np.isnan(y)
    return float(np.corrcoef(x[ok], y[ok])[0, 1])


def deciding(t, pairs, controls=("poverty",)):
    return np.array([pcor(t, a, b, controls) for a, b in pairs])


def raw(t, pairs):
    return np.array([pcor(t, a, b, ()) for a, b in pairs])


def qualifying(t):
    L = pd.read_csv(NY / "literature_signs.csv")
    L = L[(L["qualifies"] == True) & L["a"].isin(t.columns) & L["b"].isin(t.columns)]  # noqa: E712
    return L.reset_index(drop=True)


def geometry():
    TMP.mkdir(parents=True, exist_ok=True)
    f = TMP / "chicago_community_areas.geojson"
    if not f.exists():
        req = urllib.request.Request("https://data.cityofchicago.org/resource/igwz-8jzy.geojson?$limit=200",
                                     headers={"User-Agent": "research-script/1.0"})
        f.write_bytes(urllib.request.urlopen(req, timeout=120).read())
    g = gpd.read_file(f)
    g["id"] = g["area_numbe"].astype(int)
    g = g.set_index("id").sort_index().to_crs(26971)  # Illinois East, metres
    u = gpd.read_file(ROOT / "data" / "raw" / "ehdp" / "UHF42.geojson")
    u = u[u["GEOCODE"].notna()]
    u["id"] = u["GEOCODE"].astype(int)
    u = u.set_index("id").sort_index().to_crs(32118)  # New York Long Island, metres
    return g, u


def contiguity(g):
    n = len(g)
    W = np.zeros((n, n))
    geo = list(g.geometry.buffer(30))
    for i in range(n):
        for j in range(i + 1, n):
            if geo[i].intersects(geo[j]):
                W[i, j] = W[j, i] = 1
    return W


def moran(x, W):
    ok = ~np.isnan(x)
    z = x[ok] - x[ok].mean()
    w = W[np.ix_(ok, ok)]
    return float(len(z) / w.sum() * (z @ w @ z) / (z @ z))


def n_eff(x, y, D, bins=12):
    """Clifford-Richardson effective sample size for the correlation of x and y (both already residualised)."""
    ok = ~np.isnan(x) & ~np.isnan(y)
    x, y, D = x[ok], y[ok], D[np.ix_(ok, ok)]
    n = len(x)
    x, y = (x - x.mean()) / x.std(), (y - y.mean()) / y.std()
    iu = np.triu_indices(n, 1)
    d = D[iu]
    edges = np.quantile(d, np.linspace(0, 1, bins + 1))
    k = np.clip(np.searchsorted(edges, d, side="right") - 1, 0, bins - 1)
    px, py = x[iu[0]] * x[iu[1]], y[iu[0]] * y[iu[1]]
    s = n * 1.0  # distance zero: variance one for each
    for b in range(bins):
        m = k == b
        s += 2 * m.sum() * px[m].mean() * py[m].mean()
    var_r = s / n ** 2
    return float(1 + 1 / var_r) if var_r > 0 else float("inf")


def binom_tail(k, n, p=0.5):
    return sum(comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))


def main():
    rng = np.random.default_rng(SEED)
    tc = pd.read_csv(CH / "chicago_indicators_ca77.csv", index_col=0)
    tn = pd.read_csv(NY / "city_indicators_uhf42.csv", index_col=0)
    out = {}

    # ---- 1. reproduce the counts
    Lc, Ln = qualifying(tc), qualifying(tn)
    both = sorted(set(zip(Lc["a"], Lc["b"])) & set(zip(Ln["a"], Ln["b"])))
    Lb = Lc[[p in set(both) for p in zip(Lc["a"], Lc["b"])]].reset_index(drop=True)
    pairs = list(zip(Lb["a"], Lb["b"]))
    s = Lb["lit_sign"].to_numpy(float)
    air = np.array([bool(set(p) & set(EXPO)) for p in pairs])
    dc, dn = deciding(tc, pairs), deciding(tn, pairs)
    rc, rn = raw(tc, pairs), raw(tn, pairs)
    out["counts"] = {
        "chicago_qualifying": len(Lc), "pairs_in_both": len(pairs), "literature_positive": int((s > 0).sum()),
        "air_pairs": int(air.sum()), "air_literature_positive": int((s[air] > 0).sum()),
        "chicago_all": int((np.sign(dc) == s).sum()), "new_york_all": int((np.sign(dn) == s).sum()),
        "chicago_air_deciding": int((np.sign(dc[air]) == s[air]).sum()), "new_york_air_deciding": int((np.sign(dn[air]) == s[air]).sum()),
        "chicago_air_raw": int((np.sign(rc[air]) == s[air]).sum()), "new_york_air_raw": int((np.sign(rn[air]) == s[air]).sum()),
        "chicago_always_positive_all": int((dc > 0).sum()), "new_york_always_positive_all": int((dn > 0).sum()),
    }
    ap = [p for p, m in zip(pairs, air) if m]
    table = pd.DataFrame({"a": [p[0] for p in ap], "b": [p[1] for p in ap], "chi_raw": rc[air], "chi_dec": dc[air],
                          "ny_raw": rn[air], "ny_dec": dn[air]})
    table["exposure"] = [next(e for e in EXPO if e in p) for p in ap]
    out["by_exposure"] = {e: {"n": int((table.exposure == e).sum()), "chicago": int(((table.exposure == e) & (table.chi_dec > 0)).sum()),
                              "new_york": int(((table.exposure == e) & (table.ny_dec > 0)).sum())} for e in EXPO}

    # ---- 2. bootstrap of areas (own draws), air share in each city and pair-level sign stability
    def boot(t, n_draws):
        res = np.empty((n_draws, len(ap)))
        pp = np.empty(n_draws)
        for i in range(n_draws):
            tb = t.iloc[rng.integers(0, len(t), len(t))].reset_index(drop=True)
            res[i] = deciding(tb, ap)
            pp[i] = pcor(tb, "pm25", "poverty", ())
        return res, pp
    bc, ppc = boot(tc, DRAWS)
    bn, ppn = boot(tn, DRAWS)
    sc, sn = (bc > 0).mean(axis=1), (bn > 0).mean(axis=1)
    q = lambda x: [round(float(np.quantile(x, .025)), 3), round(float(np.quantile(x, .975)), 3)]  # noqa: E731
    out["bootstrap"] = {"chicago_air_share_ci95": q(sc), "new_york_air_share_ci95": q(sn), "difference_ci95": q(sc - sn),
                        "share_of_draws_chicago_at_or_below_0.370": float((sc <= 10 / 27).mean()),
                        "share_of_draws_chicago_below_0.60": float((sc < 0.6).mean()),
                        "share_of_draws_difference_le_0": float((sc - sn <= 0).mean()),
                        "chicago_boot_mean_share": float(sc.mean())}
    table["chi_boot_p_positive"] = (bc > 0).mean(axis=0)
    table["chi_p_two_sided_n77"] = [2 * stats.t.sf(abs(r) * np.sqrt((77 - 3) / (1 - r * r)), 77 - 3) for r in table.chi_dec]
    out["pm25_poverty"] = {"chicago_spearman": pcor(tc, "pm25", "poverty", ()), "chicago_ci95": q(ppc),
                           "new_york_spearman": pcor(tn, "pm25", "poverty", ()), "new_york_ci95": q(ppn)}
    out["pm25_density"] = {"chicago_spearman": pcor(tc, "pm25", "pop_density", ()), "new_york_spearman": pcor(tn, "pm25", "pop_density", ())}
    out["exposure_ranges"] = {e: {"chicago": [float(tc[e].min()), float(tc[e].max()), float(tc[e].std() / tc[e].mean())],
                                  "new_york": [float(tn[e].min()), float(tn[e].max()), float(tn[e].std() / tn[e].mean())]} for e in EXPO}
    out["exposure_intercorrelation_chicago"] = {f"{a}-{b}": pcor(tc, a, b, ()) for a, b in (("pm25", "ozone"), ("pm25", "traffic"), ("ozone", "traffic"))}

    # ---- 3. size thresholds and significance
    cd = table.chi_dec.to_numpy()
    nd = table.ny_dec.to_numpy()
    out["size"] = {
        "chicago_agreeing_abs_below_0.1": int(((cd > 0) & (np.abs(cd) < 0.1)).sum()),
        "chicago_abs_ge_0.1": [int(((cd > 0) & (np.abs(cd) >= 0.1)).sum()), int((np.abs(cd) >= 0.1).sum())],
        "new_york_abs_ge_0.1": [int(((nd > 0) & (np.abs(nd) >= 0.1)).sum()), int((np.abs(nd) >= 0.1).sum())],
        "chicago_abs_ge_0.2": [int(((cd > 0) & (np.abs(cd) >= 0.2)).sum()), int((np.abs(cd) >= 0.2).sum())],
        "new_york_abs_ge_0.2": [int(((nd > 0) & (np.abs(nd) >= 0.2)).sum()), int((np.abs(nd) >= 0.2).sum())],
        "chicago_p_below_0.05_positive": int(((table.chi_p_two_sided_n77 < 0.05) & (cd > 0)).sum()),
        "chicago_p_below_0.05_negative": int(((table.chi_p_two_sided_n77 < 0.05) & (cd < 0)).sum()),
        "chicago_boot_sign_stable_95_positive": int((table.chi_boot_p_positive >= 0.95).sum()),
        "chicago_boot_sign_stable_95_negative": int((table.chi_boot_p_positive <= 0.05).sum()),
    }

    # ---- 4. chance: binomial, Fisher, and an exposure-shuffle null on the fifteen pairs
    k = out["counts"]["chicago_air_deciding"]
    kn = out["counts"]["new_york_air_deciding"]
    n = len(ap)
    fisher = stats.fisher_exact([[k, n - k], [kn, n - kn]])
    null = []
    for _ in range(DRAWS):
        tp = tc.copy()
        perm = rng.permutation(len(tc))
        for e in EXPO:  # the three exposures moved together, so their mutual correlation is kept
            tp[e] = tc[e].to_numpy()[perm]
        null.append(int((deciding(tp, ap) > 0).sum()))
    null = np.array(null)
    out["chance"] = {"binomial_one_sided_12_of_15_vs_half": binom_tail(k, n), "binomial_two_sided": min(1.0, 2 * binom_tail(k, n)),
                     "binomial_vs_0.370": binom_tail(k, n, 10 / 27),
                     "fisher_two_sided_12_vs_6_of_15": float(fisher[1]),
                     "exposure_shuffle_null": {"mean": float(null.mean()), "sd": float(null.std()), "q025": float(np.quantile(null, .025)),
                                               "q975": float(np.quantile(null, .975)), "p_ge_obs": float((np.sum(null >= k) + 1) / (DRAWS + 1)),
                                               "p_le_3": float((null <= 3).mean()), "p_ge_12_or_le_3": float(((null >= k) | (null <= n - k)).mean())}}

    # ---- 5. variants
    var = {}
    var["without_pm25"] = {"n": int((table.exposure != "pm25").sum()), "chicago": int(((table.exposure != "pm25") & (cd > 0)).sum()),
                           "new_york": int(((table.exposure != "pm25") & (nd > 0)).sum())}
    for name, ctl in (("poverty_and_density", ("poverty", "pop_density")), ("poverty_and_foreign_born", ("poverty", "foreign_born")),
                      ("poverty_and_high_school", ("poverty", "high_school")), ("poverty_and_unemployment", ("poverty", "unemployment"))):
        var[name] = {"chicago": int((deciding(tc, ap, ctl) > 0).sum()), "new_york": int((deciding(tn, ap, ctl) > 0).sum())}
    jack = [int((deciding(tc.drop(index=i), ap) > 0).sum()) for i in tc.index]
    var["leave_one_area_out_chicago"] = [min(jack), max(jack)]
    out["variants"] = var

    # ---- 6. space
    g, u = geometry()
    g, u = g.loc[tc.index], u.loc[tn.index]
    sp = {}
    for city, t, geo in (("chicago", tc, g), ("new_york", tn, u)):
        cen = geo.geometry.centroid
        xy = np.column_stack([cen.x.to_numpy(), cen.y.to_numpy()])
        D = np.sqrt(((xy[:, None, :] - xy[None, :, :]) ** 2).sum(-1))
        W = contiguity(geo)
        R = rank(t)
        pov = R["poverty"].to_numpy(float)
        info = {"mean_neighbours": float(W.sum(1).mean()), "moran_I": {}, "plane_R2": {}}
        for e in EXPO + ["poverty", "premature_death", "obesity", "diabetes", "low_birthweight", "asthma_adult"]:
            v = t[e].to_numpy(float)
            info["moran_I"][e] = round(moran(v, W), 3)
            ok = ~np.isnan(v)
            r = resid(v, [xy[:, 0], xy[:, 1]])
            info["plane_R2"][e] = round(float(1 - np.nanvar(r[ok]) / np.var(v[ok])), 3)
        ne = {}
        for a, b in ap:
            x, y = resid(R[a].to_numpy(float), [pov]), resid(R[b].to_numpy(float), [pov])
            ne[f"{a}|{b}"] = round(n_eff(x, y, D), 1)
        info["n_eff_clifford_richardson"] = ne
        x, y = R["pm25"].to_numpy(float), pov
        info["n_eff_pm25_poverty"] = round(n_eff(x, y, D), 1)
        # deciding correlations with the centroid coordinates added to poverty
        tt = t.copy()
        tt["_x"], tt["_y"] = xy[:, 0], xy[:, 1]
        dxy = deciding(tt, ap, ("poverty", "_x", "_y"))
        info["agree_poverty_and_coordinates"] = int((dxy > 0).sum())
        info["deciding_poverty_and_coordinates"] = {f"{a}|{b}": round(float(v), 3) for (a, b), v in zip(ap, dxy)}
        # a plane tilted in every compass direction in place of PM2.5: how many of the PM2.5 pairs come out positive
        pm_pairs = [(a, b) for a, b in ap if "pm25" in (a, b)]
        cnt = []
        for th in np.deg2rad(np.arange(0, 360, 5)):
            tt["pm25"] = xy[:, 0] * np.cos(th) + xy[:, 1] * np.sin(th)
            cnt.append(int((deciding(tt, pm_pairs) > 0).sum()))
        cnt = np.array(cnt)
        info["tilted_plane_in_place_of_pm25"] = {"n_pairs": len(pm_pairs), "share_of_directions_ge_5": float((cnt >= 5).mean()),
                                                 "share_of_directions_le_1": float((cnt <= 1).mean()),
                                                 "share_of_directions_2_to_4": float(((cnt >= 2) & (cnt <= 4)).mean())}
        # direction of the PM2.5 gradient (compass bearing of increase) and its rank correlation with the best plane
        v = t["pm25"].to_numpy(float)
        b = np.linalg.lstsq(np.column_stack([np.ones(len(v)), xy]), v, rcond=None)[0]
        info["pm25_gradient_bearing_deg"] = round(float(np.rad2deg(np.arctan2(b[1], b[2])) % 360), 0)
        sp[city] = info
    # PM2.5 pairs' significance at the effective sample size
    adj = {}
    for (a, b), r in zip(ap, cd):
        ne = sp["chicago"]["n_eff_clifford_richardson"][f"{a}|{b}"]
        df = max(ne - 3, 1)
        adj[f"{a}|{b}"] = round(float(2 * stats.t.sf(abs(r) * np.sqrt(df / (1 - r * r)), df)), 3)
    sp["chicago"]["p_at_effective_n"] = adj
    r = out["pm25_poverty"]["chicago_spearman"]
    df = max(sp["chicago"]["n_eff_pm25_poverty"] - 2, 1)
    sp["chicago"]["pm25_poverty_p_at_effective_n"] = round(float(2 * stats.t.sf(abs(r) * np.sqrt(df / (1 - r * r)), df)), 3)
    out["space"] = sp
    out["table"] = table.round(3).to_dict(orient="records")
    print(json.dumps(out, indent=1))
    print(table.round(3).to_string())


if __name__ == "__main__":
    main()
