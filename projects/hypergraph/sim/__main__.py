"""Command line of the toll-schedule simulator.

  python -m sim params                      list parameters with intervals and sources
  python -m sim scenarios                   run the scenario set; writes data/derived/simulate/scenarios.json
  python -m sim run --peak 6,12,12,12,6 [--pm 13.5] [--night 2.25]
                                            one schedule against the current one (peak toll Mon..Fri)
  python -m sim sensitivity                 which parameter each output depends on most
  python -m sim export-js                   write viz/data/simulate_params.js for the browser page
  python -m sim check                       central values are medians; the congestion file is the one the
                                            parameters were built from; the browser file equals parameters.json
Options: --params FILE  --draws N  --seed N
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

from sim import model, scenarios

OUTPUTS = [("entries_pct", "vehicle entries, %"), ("speed_pct", "speed 05:00-21:00, %"), ("revenue_musd", "weekday revenue, $ million a year"),
           ("ambulance_s", "ambulance travel time, seconds"), ("arrest_survivors", "cardiac-arrest survivors a year"),
           ("retail_pct", "retail and restaurant activity, %"), ("crashes_pct", "injury crashes, %")]
DER = model.ROOT / "data" / "derived" / "simulate"
# +1: a rise is an improvement; -1: a fall is; None: neither direction is called an improvement
BETTER = {"entries_pct": None, "speed_pct": 1, "revenue_musd": 1, "ambulance_s": -1, "arrest_survivors": 1,
          "retail_pct": 1, "crashes_pct": -1}
READING = {
    "entries_pct": "Sign by assumption: the toll response is positive in every draw, and a schedule scaled to hold revenue "
                   "lowers entries by construction. The size follows from the assumed response per dollar.",
    "revenue_musd": "Informative, given the assumed toll response and the assumed revenue per entry. For a schedule scaled to "
                    "hold revenue it is zero at the central values by construction.",
    "speed_pct": "Sign not determined: it follows the entries-to-speed elasticity, whose range crosses zero. p_improve is the "
                 "share of draws in which that elasticity has the sign that helps, and it is the same for every schedule that "
                 "lowers entries.",
    "ambulance_s": "Sign not determined, for the same reason as speed.",
    "arrest_survivors": "Sign not determined, for the same reason as speed. An illustration of the arithmetic, not a forecast.",
    "retail_pct": "Sign not determined: assumed losses from deterred car visitors against an amenity term of either sign.",
    "crashes_pct": "Sign not determined: fewer entries lower crashes and higher speed raises them, both by assumed exponents.",
}
NOTES = [
    "The simulator composes associations and is not a causal model of New York.",
    "The entries-to-speed elasticity is estimated from day-to-day variation of about 3% in entries, which is confounded with "
    "activity in the zone, and is applied here to toll-induced changes in non-taxi entries. One value is used in every band of "
    "hours. Its range crosses zero because the evidence does not fix its sign (sim-crz-holdout-2026, contested).",
    "Speed, ambulance time and survivors therefore take either sign. Their p_improve is the probability, under the stated "
    "range, that the elasticity is negative; it says nothing about one schedule against another.",
    "A higher toll lowers entries in every draw, because the toll response is positive by assumption.",
    "Schedules scaled to hold revenue lower total entries by construction: with exponential demand and one toll response, "
    "revenue is concave in the toll, so any pattern that spreads tolls needs a higher traffic-weighted mean toll. Opposite "
    "patterns (Tuesday to Thursday high, Monday and Friday high) both lower entries for this reason.",
    "Scaled schedules hold weekday revenue at the central parameter values only; the daytime tolls alone are scaled.",
    "The parameters are drawn independently of one another.",
    "Baselines are 2025 means. Taxi speed in the zone was about 7% lower and ambulance travel time about 11% higher in "
    "January to June 2026, for reasons the chain does not contain, so outputs are given as changes and not as levels.",
    "Informative columns: revenue, and entries as a statement of the assumed toll response. The outputs whose 95% interval "
    "excludes zero for some schedule are listed under intervals_excluding_zero; with the parameter file of 13 November 2026 "
    "they are entries and revenue only.",
]


def compare(P, toll, th, base=None):
    """Each output of `toll` minus the same output of the current schedule, draw by draw."""
    base = base or model.simulate(P, model.toll_now(P), th)
    s = model.simulate(P, toll, th)
    diff = {}
    for k, _ in OUTPUTS:
        diff[k] = s[k] - base[k] if k not in ("entries_pct", "speed_pct", "retail_pct", "crashes_pct", "ambulance_s", "arrest_survivors") else s[k]
    diff["speed_pct_by_weekday"] = s["speed_pct_by_weekday"]
    diff["entries_pct_by_weekday"] = s["entries_pct_by_weekday"]
    return diff, s, base


def sensitivity(th, y):
    """Squared Spearman correlation of each parameter with an output, as a share of their sum."""
    if np.std(y) == 0:
        return {}
    r2 = {k: float(spearmanr(v, y)[0] ** 2) for k, v in th.items()}
    tot = sum(r2.values()) or 1.0
    return dict(sorted(((k, v / tot) for k, v in r2.items()), key=lambda kv: -kv[1]))


def hot_night(P, th):
    """Illustration: the overnight toll rises from $2.25 to $9 on weekday nights after a day of 30 C or more.
    The night-band baselines are weekday means, so the count of nights is hot weekdays a year and the zone's
    hot-night shootings are scaled by the same share. No retiming, because a hot night is known only on the day."""
    C = P["constants"]
    n = len(th["k_toll"])
    nights = C["hot_weekdays_per_year"]
    t0 = P["current_toll"]["night"]
    q0 = model._table(P, "entries")[:, 0].mean()
    qo0 = q0 - model._table(P, "entries_tlc")[:, 0].mean()
    v0 = model._table(P, "speed_mph")[:, 0].mean()
    tt0 = model._table(P, "ems_lt_travel_s")[:, 0].mean()
    keep = np.exp(-th["k_toll"] * (9.0 - t0))
    q = q0 + qo0 * (keep - 1)
    v = v0 * (q / q0) ** th["beta_speed"]
    tt = tt0 * (v / v0) ** th["theta_ems"]
    dmin = (tt - tt0) / 60.0
    g = C["gunshot_survival_per_min"]
    per_min = np.random.default_rng(model.SEED + 1).uniform(g["lo"], g["hi"], n)
    shots = C["zone_hot_night_shootings_per_year"] * nights / C["hot_days_per_year"]
    arrests = model._table(P, "ems_arrest_per_day")[:, 0].mean() * nights
    return {
        "night_entries_pct": (100 * (q / q0 - 1), None), "night_speed_pct": (100 * (v / v0 - 1), 1), "ambulance_s": (tt - tt0, -1),
        "revenue_musd": (qo0 * (keep * 9.0 - t0) * th["charge_factor"] * nights / 1e6, 1),
        "shooting_deaths_averted": (shots * C["zone_night_shooting_fatal_share"] * (1 - np.exp(per_min * dmin)), 1),
        "arrest_survivors": (model.survivors(arrests, th["base_survival"], th["surv_per_min"], dmin), 1),
        "entries_paying_the_higher_toll_per_hot_night": (qo0 * keep, None),
    }


def run_scenarios(P, n, seed):
    th = model.draw(P, n, seed)
    S = scenarios.build(P)
    base = model.simulate(P, model.toll_now(P), th)
    pv = {k: float((v > 0).mean()) for k, v in th.items() if P["parameters"][k]["lo"] < 0 < P["parameters"][k]["hi"]}
    out = {"draws": n, "seed": seed, "notes": NOTES, "reading": READING,
           "p_improve": "Share of draws on the better side of zero: higher speed, revenue, survivors and retail activity; "
                        "lower ambulance time and crashes. Not given for entries.",
           "share_of_draws_positive_for_parameters_whose_range_crosses_zero": pv,
           "baseline_period": "non-holiday weekdays, 6 January to 23 December 2025", "baseline_caveat": P.get("baseline_caveat"),
           "baseline": {k: model.summarise(base[k]) for k in ("entries_per_day", "speed_mph", "revenue_musd", "ambulance_mean_s")},
           "scenarios": {}, "outputs": dict(OUTPUTS)}
    c = model.central(P)
    diffs = {}
    for name, s in S.items():
        if name == "current":
            continue
        d, _, _ = compare(P, s["toll"], th, base)
        diffs[name] = d
        dc, _, _ = compare(P, s["toll"], c)
        out["scenarios"][name] = {
            "label": s["label"], "toll": s["toll"].tolist(), "factor": s.get("factor"),
            "revenue_held": name.endswith("_rn"),
            "vs_current": {k: model.summarise(d[k], BETTER[k]) for k, _ in OUTPUTS},
            "central": {k: float(dc[k][0]) for k, _ in OUTPUTS},
            "speed_pct_by_weekday": [model.summarise(d["speed_pct_by_weekday"][:, w]) for w in range(5)],
            "entries_pct_by_weekday": [model.summarise(d["entries_pct_by_weekday"][:, w]) for w in range(5)],
            "sensitivity": {k: dict(list(sensitivity(th, d[k]).items())[:4]) for k, _ in OUTPUTS},
        }
    # can the scenarios be ranked? probability, over draws, that the row beats the column
    names = list(diffs)
    rank = {}
    for k, better in (("speed_pct", 1), ("revenue_musd", 1), ("ambulance_s", -1), ("arrest_survivors", 1), ("retail_pct", 1), ("crashes_pct", -1)):
        rank[k] = {a: {b: float(((diffs[a][k] - diffs[b][k]) * better > 0).mean()) for b in names if b != a} for a in names}
    out["p_row_beats_column"] = rank
    out["intervals_excluding_zero"] = sorted({k for sc in out["scenarios"].values() for k, v in sc["vs_current"].items()
                                              if v["lo"] > 0 or v["hi"] < 0})
    out["p_row_beats_column_note"] = ("For speed, ambulance time and survivors these shares follow the sign of the entries-to-speed "
                                      "elasticity and the sign of the entries change, which is fixed by assumption. They are not a "
                                      "ranking of schedules.")
    hn = hot_night(P, th)
    out["hot_night"] = {"label": f"Overnight toll $9 instead of ${P['current_toll']['night']:g} on the "
                                 f"{P['constants']['hot_weekdays_per_year']:g} weekday nights a year after a day of 30 C or more",
                        "note": "Deaths averted and survivors are below 0.05 a year in every draw and are zero for practical purposes.",
                        "vs_current": {k: model.summarise(v, b) for k, (v, b) in hn.items()}}
    return out


def fmt(s, nd=1):
    p = f"  P(improvement) {s['p_improve']:.2f}" if "p_improve" in s else ""
    return f"{s['median']:+.{nd}f} ({s['lo']:+.{nd}f} to {s['hi']:+.{nd}f}){p}"


def check(P):
    """Three consistency checks; returns the list of failures."""
    bad = []
    for k, p in P["parameters"].items():
        if abs(p["value"] - model.median(p)) > 1e-12:
            bad.append(f"{k}: central value {p['value']} is not the median {model.median(p)}")
        if "min" in p or "max" in p:
            bad.append(f"{k}: truncated")
    th = model.draw(P)
    for k, p in P["parameters"].items():
        lo, med, hi = np.quantile(th[k], [0.025, 0.5, 0.975])
        w = p["hi"] - p["lo"]
        want = (p["lo"], p["hi"]) if p["dist"] == "normal" else (None, None)
        if abs(med - p["value"]) > 0.02 * w or (want[0] is not None and (abs(lo - want[0]) > 0.03 * w or abs(hi - want[1]) > 0.03 * w)):
            bad.append(f"{k}: draws {lo:.4f}, {med:.4f}, {hi:.4f} do not match {p['lo']:.4f}, {p['value']:.4f}, {p['hi']:.4f}")
    cf = P["meta"]["congestion_file"]
    now = hashlib.sha256((model.ROOT / cf["path"]).read_bytes()).hexdigest()
    if now != cf["sha256"]:
        bad.append(f"{cf['path']} has changed since parameters.json was built; run analyses/simulate/build_parameters.py")
    js = (model.ROOT / "viz" / "data" / "simulate_params.js").read_text()
    if json.loads(js[js.index("{"):js.rindex("}") + 1]) != P:
        bad.append("viz/data/simulate_params.js differs from parameters.json; run python -m sim export-js")
    return bad


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["params", "scenarios", "run", "sensitivity", "export-js", "check"])
    ap.add_argument("--params")
    ap.add_argument("--draws", type=int, default=model.DRAWS)
    ap.add_argument("--seed", type=int, default=model.SEED)
    ap.add_argument("--peak", help="peak toll Mon..Fri, comma separated")
    ap.add_argument("--pm", type=float, help="toll 16:00-21:00 on all weekdays")
    ap.add_argument("--night", type=float)
    a = ap.parse_args()
    P = model.load(a.params)
    if a.cmd == "params":
        for k, p in P["parameters"].items():
            print(f"{k:17s} [{p['type']}] {p['value']:+.3f} ({p['lo']:+.3f} to {p['hi']:+.3f}) {p['dist']:10s} sign {p['sign']:8s} {p['label']}")
    elif a.cmd == "check":
        bad = check(P)
        print("\n".join(bad) if bad else "ok: central values are medians, draws match the ranges, the congestion file is "
              "unchanged and the browser file equals parameters.json")
        raise SystemExit(1 if bad else 0)
    elif a.cmd == "export-js":
        f = model.ROOT / "viz" / "data" / "simulate_params.js"
        f.write_text("// generated by `python -m sim export-js` from data/derived/simulate/parameters.json\nwindow.SIM_PARAMS = "
                     + json.dumps(P, indent=1) + ";\n")
        print("wrote", f.relative_to(model.ROOT))
    elif a.cmd == "run":
        t = scenarios.flat(P, night=a.night)
        if a.peak:
            t = scenarios.weekday_peaks(P, [float(x) for x in a.peak.split(",")])
            if a.night is not None:
                t[:, 0] = a.night
        if a.pm is not None:
            t[:, 3] = a.pm
        th = model.draw(P, a.draws, a.seed)
        d, _, _ = compare(P, t, th)
        print("toll table [Mon..Fri] x [night, am, mid, pm]:", t.tolist())
        for k, lab in OUTPUTS:
            print(f"  {lab:42s} {fmt(model.summarise(d[k], BETTER[k]), 2)}")
        print("\n" + "\n".join("note: " + x for x in NOTES))
    else:
        out = run_scenarios(P, a.draws, a.seed)
        if a.cmd == "scenarios":
            (DER / "scenarios.json").write_text(json.dumps(out, indent=1))
            for name, s in out["scenarios"].items():
                print(f"\n{name}: {s['label']}")
                for k, lab in OUTPUTS:
                    print(f"  {lab:42s} {fmt(s['vs_current'][k], 2)}")
            print("\nhot night:", out["hot_night"]["label"])
            for k, v in out["hot_night"]["vs_current"].items():
                print(f"  {k:42s} {fmt(v, 3)}")
            print("\n" + "\n".join("note: " + x for x in NOTES))
        else:
            for name, s in out["scenarios"].items():
                print(f"\n{name}")
                for k, lab in OUTPUTS:
                    top = ", ".join(f"{p} {100 * v:.0f}%" for p, v in s["sensitivity"][k].items())
                    print(f"  {lab:42s} {top}")


if __name__ == "__main__":
    main()
