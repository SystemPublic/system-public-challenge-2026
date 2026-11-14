"""The chain, as arithmetic on a table of 5 weekdays x 4 bands of hours.

    toll(w, b)
      -> vehicle entries      q  = q_taxi + q_other * exp(-k * (toll - toll_now)) * retiming
      -> speed in the zone    v  = v_now * (q / q_now) ** beta
      -> ambulance travel     tt = tt_now * (v / v_now) ** theta
      -> cardiac arrest survivors, odds of survival times exp(-g * (tt - tt_now) / 60)
    in parallel
      -> visits and retail    retail % = e_r * (-c * s * (1 - d) * share of toll-paying entries removed + a * change in log speed)
      -> toll revenue         sum of q_other * toll * phi
      -> injury crashes       (q / q_now) ** x_vol * (v / v_now) ** x_speed

Every symbol is an entry of parameters.json with a value, a low and a high bound, a
source type (a: estimated in this project; b: a finding in the System graph checked
against its abstract; c: an assumption) and a source. `simulate` draws the parameters
(fixed seed) and returns the outputs for one toll schedule as arrays over the draws.
Nothing here is specific to a scenario; scenarios are toll tables (sim/scenarios.py).

The chain composes associations and is not a causal model. Three properties follow from its
form and are stated with every output (sim/__main__.py, NOTES):
  - the speed elasticity beta is drawn from a range that crosses zero, because the evidence
    does not fix its sign, so speed, ambulance time and survivors can move either way and the
    share of draws with an improvement is reported;
  - a higher toll lowers entries in every draw (k is positive by assumption);
  - with exponential demand and one k, any schedule scaled to hold revenue lowers total entries.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PARAMS = ROOT / "data" / "derived" / "simulate" / "parameters.json"
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]
SEED = 20261113
DRAWS = 10000


def load(path: str | Path | None = None) -> dict:
    return json.loads(Path(path or PARAMS).read_text())


def draw(P: dict, n: int = DRAWS, seed: int = SEED) -> dict[str, np.ndarray]:
    """One array of n draws per parameter. 'uniform': flat between lo and hi. 'loguniform': flat in the
    log between lo and hi. 'normal': lo and hi are the 2.5% and 97.5% points. Nothing is truncated, so
    the central value of each parameter is the median of its draws (see `median`).
    The order of the parameters in the file fixes the random stream."""
    rng = np.random.default_rng(seed)
    out = {}
    for name, p in P["parameters"].items():
        if p["dist"] == "uniform":
            x = rng.uniform(p["lo"], p["hi"], n)
        elif p["dist"] == "loguniform":
            x = np.exp(rng.uniform(np.log(p["lo"]), np.log(p["hi"]), n))
        elif p["dist"] == "normal":
            x = rng.normal((p["lo"] + p["hi"]) / 2, (p["hi"] - p["lo"]) / 3.92, n)
        else:
            raise ValueError(f"unknown dist for {name}")
        out[name] = x
    return out


def median(p: dict) -> float:
    """The median of a parameter's distribution, from its bounds."""
    return float(np.sqrt(p["lo"] * p["hi"])) if p["dist"] == "loguniform" else (p["lo"] + p["hi"]) / 2


def central(P: dict) -> dict[str, np.ndarray]:
    return {k: np.array([p["value"]]) for k, p in P["parameters"].items()}


def survivors(arrests, base, g, dmin):
    """Change in survivors when the odds of survival are multiplied by exp(-g) per minute of delay."""
    odds = base / (1 - base) * np.exp(-g * dmin)
    return arrests * (odds / (1 + odds) - base)


def _table(P: dict, key: str) -> np.ndarray:
    """Baseline quantity as an array [weekday, band]."""
    return np.array([[P["baseline"][b][str(w)][key] for b in P["bands"]] for w in range(5)], float)


def toll_now(P: dict) -> np.ndarray:
    return np.array([[P["current_toll"][b] for b in P["bands"]] for _ in range(5)], float)


def simulate(P: dict, toll: np.ndarray, th: dict[str, np.ndarray], days: float | None = None) -> dict[str, np.ndarray]:
    """Outputs for a toll table [weekday, band] in dollars (passenger-car rate), one value per draw.
    `days` is the number of days a year on which each weekday row applies (default: weeks_per_year)."""
    C = P["constants"]
    wk = C["weeks_per_year"] if days is None else days
    t0 = toll_now(P)
    q0, qx0 = _table(P, "entries"), _table(P, "entries_tlc")
    qo0 = q0 - qx0                                    # entries that pay the entry toll
    v0, tt0, arr = _table(P, "speed_mph"), _table(P, "ems_lt_travel_s"), _table(P, "ems_arrest_per_day")
    lt = _table(P, "ems_lt_per_day")
    day = np.array([b != "night" for b in P["bands"]])  # the 05:00-20:59 bands
    T, T0 = toll[None, :, :], t0[None, :, :]
    col = lambda name: th[name][:, None, None]

    # toll -> entries: own-price response, then retiming toward cheaper cells with the total held fixed
    qo = qo0[None] * np.exp(-col("k_toll") * (T - T0))
    tbar = (qo * T).sum((1, 2), keepdims=True) / qo.sum((1, 2), keepdims=True)
    r = np.exp(-col("k_shift") * (T - tbar))
    r0 = np.exp(-col("k_shift") * (T0 - (qo0 * t0).sum() / qo0.sum()))  # retiming already present in the baseline
    qo2 = qo * r / r0
    qo2 = qo2 * qo.sum((1, 2), keepdims=True) / qo2.sum((1, 2), keepdims=True)
    q = qo2 + qx0[None]
    # entries -> speed -> ambulance travel time
    v = v0[None] * (q / q0[None]) ** col("beta_speed")
    tt = tt0[None] * (v / v0[None]) ** col("theta_ems")
    dmin = (tt - tt0[None]) / 60.0
    surv = survivors(arr[None], col("base_survival"), col("surv_per_min"), dmin)
    # revenue, visits, crashes
    rev = (qo2 * T).sum((1, 2)) * th["charge_factor"] * wk / 1e6
    removed = 1.0 - qo2[:, :, day].sum((1, 2)) / qo0[:, day].sum()
    wv = (q0 * day[None, :])[None]
    dlnv = (np.log(v / v0[None]) * wv).sum((1, 2)) / wv.sum()
    visits = -th["car_share"] * (1 - th["diversion"]) * removed + th["amenity"] * dlnv
    retail = th["retail_per_visit"] * (-th["car_share"] * th["spend_ratio"] * (1 - th["diversion"]) * removed
                                       + th["amenity"] * dlnv)
    crash_rel = ((q / q0[None]) ** col("crash_volume") * (v / v0[None]) ** col("crash_speed") * q0[None]).sum((1, 2)) / q0.sum()
    w_all = q0[None]
    return {
        "entries_per_day": q.sum((1, 2)) / 5.0,
        "entries_pct": 100 * (q.sum((1, 2)) / q0.sum() - 1),
        "speed_mph": np.exp((np.log(v) * wv).sum((1, 2)) / wv.sum()),
        "speed_pct": 100 * (np.exp(dlnv) - 1),
        "speed_pct_by_weekday": 100 * (np.exp((np.log(v / v0[None]) * wv).sum(2) / wv.sum(2)) - 1),
        "entries_pct_by_weekday": 100 * (q.sum(2) / q0.sum(1)[None] - 1),
        "revenue_musd": rev,
        "ambulance_s": ((tt - tt0[None]) * lt[None]).sum((1, 2)) / lt.sum(),
        "ambulance_mean_s": (tt * lt[None]).sum((1, 2)) / lt.sum(),
        "arrest_survivors": surv.sum((1, 2)) * wk,
        "visits_pct": 100 * visits,
        "retail_pct": 100 * retail,
        "crashes_pct": 100 * (crash_rel - 1),
        "_w": w_all.sum() * np.ones(len(th["k_toll"])),
    }


def summarise(x: np.ndarray, better: int | None = None) -> dict:
    """Median, 95% interval and the share of draws above zero. `better` is +1 or -1 when a rise or a
    fall of the output is an improvement; p_improve is then the share of draws on that side of zero."""
    lo, med, hi = np.quantile(x, [0.025, 0.5, 0.975])
    out = {"median": float(med), "lo": float(lo), "hi": float(hi), "p_positive": float((x > 0).mean())}
    if better is not None:
        out["p_improve"] = float((x * better > 0).mean())
    return out
