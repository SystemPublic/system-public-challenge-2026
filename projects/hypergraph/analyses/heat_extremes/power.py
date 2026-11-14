"""Can the registered test fail? Day counts by temperature and the precision of the contrast.

Reads each city's temperatures, calendar and overall mean daily count only. It does not
read any count by temperature. Counts are simulated from the calendar and a stated truth,
the registered model is fitted, and the standard error of the primary contrast and the
verdict the registered rule would give are recorded.

Run: ~/.venvs/nyc-concordance/bin/python -m analyses.heat_extremes.power
Writes data/derived/heat_extremes/power.json
"""
import json

import numpy as np

from analyses.heat_extremes import model as m

SEED, NSIM, ALPHAS = 20261113, 60, (0.05, 0.15)
TRUTHS = {"downturn_0.95": 0.95, "flat_1.00": 1.00, "linear_1.06": 1.06}
SLOPE = np.log(1.05) / 5  # 5% per 5 C below 35 C, the low end of the published slopes


def simulate(d, rr_hot, alpha, rng):
    t = d["TMAX"].values
    lin = SLOPE * (np.minimum(t, 33.5) - 20)
    # above 35 C the log rate moves in a straight line from its value at 33.5 C to log(rr_hot) at the mean of the >=38 days
    t38 = t[t >= 38].mean() if (t >= 38).any() else 40.0
    extra = np.where(t > 33.5, np.log(rr_hot) * np.clip((t - 33.5) / (t38 - 33.5), 0, None), 0.0)
    mu = np.exp(lin + extra)
    mu = mu * d["n"].mean() / mu.mean()
    return rng.negative_binomial(1 / alpha, 1 / (1 + alpha * mu))


def main():
    rng = np.random.default_rng(SEED)
    out = {"seed": SEED, "nsim": NSIM, "cities": {}, "pooled": {}}
    frames = {}
    for c in m.CITIES:
        d = m.load(c)
        frames[c] = d
        out["cities"][c] = {**m.day_counts(d), "mean_daily_count": float(d["n"].mean())}
        print(c, out["cities"][c])
    q = [c for c in m.CITIES if out["cities"][c]["d38p"] >= m.MIN_DAYS and out["cities"][c]["d32_35"] >= m.MIN_DAYS]
    out["qualifying"] = q
    for alpha in ALPHAS:
        for name, truth in TRUTHS.items():
            ses = {c: [] for c in q}
            verdicts = {"confirmed": 0, "contested": 0, "unsettled": 0}
            pse = []
            for _ in range(NSIM):
                ests = []
                for c in q:
                    d = frames[c].copy()
                    d["n"] = simulate(d, truth, alpha, rng)
                    e = m.primary(d, alpha=alpha)
                    ses[c].append(e["se"])
                    ests.append(e)
                p = m.pool(ests)["random"]
                pse.append(p["se"])
                verdicts["confirmed" if p["hi"] < 1 else "contested" if p["lo"] > 1 else "unsettled"] += 1
            key = f"alpha{alpha}_{name}"
            out["pooled"][key] = {"se_by_city": {c: float(np.mean(v)) for c, v in ses.items()}, "pooled_random_se": float(np.mean(pse)),
                                  "verdict_share": {k: v / NSIM for k, v in verdicts.items()}}
            print(key, out["pooled"][key])
    se = max(v["pooled_random_se"] for v in out["pooled"].values())
    out["D_downturn_vs_linear"] = float((np.log(1.06 / 0.95) / se) ** 2)
    out["D_downturn_vs_flat"] = float((np.log(1 / 0.95) / se) ** 2)
    out["D_linear_vs_flat"] = float((np.log(1.06) / se) ** 2)
    print({k: v for k, v in out.items() if k.startswith("D_")})
    (m.DER / "power.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
