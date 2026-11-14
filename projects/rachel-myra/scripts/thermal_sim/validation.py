"""Monte-Carlo validation against published mail-order logger studies.

Targets (docs/supply-chain.md, research-notes/storage_devices_supply.md):

* JAPhA 2023 (Chowdhury et al.): summer, share of transit time out of range
  - 3-day ground 43.1 %, next-day 13.6 %.  The notes do not state whether "out
  of range" means outside 20-25 C or outside the 15-30 C excursion band, so
  both are reported.  (Study: 36 packages, NJ/CA/TN, 3 carriers.)
* ASHP Midyear 2020 (Univ. of Utah, conference): all 48 packages left
  68-77 F (20-25 C) at some point; 27-54 % of time out of range in summer.
  (6 US locations, not NYC.)

Our simulation drives the model with real hourly LaGuardia weather for
June-August 2024 and 2025 (NCEI ISD).  Random draws (all ASSUMPTIONS, listed
in VALIDATION.md): ship day, delivery time, doorstep type, porch dwell time,
mailer type.  Two free parameters (truck_beta, hub_f) are calibrated by grid
search to the two JAPhA numbers; the ASHP figures are then a partial
out-of-sample check.

Run:  cd scripts && uv run --python 3.12 --with numpy,pandas python -m thermal_sim.validation
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

from . import itinerary, params
from .batch import run_batch
from .weather_io import summer_weather

HERE = Path(__file__).resolve().parent
OUT_JSON = HERE / "validation_results.json"
OUT_MD = HERE / "VALIDATION.md"

TARGETS = {"ground_3day": 43.1, "next_day": 13.6}
ASHP_RANGE = (27.0, 54.0)
DOORSTEP_P = {"porch_shade": 0.45, "porch_sun": 0.25, "lobby": 0.20, "mailbox_sun": 0.10}
DELIVERY_WINDOW = {"next_day": (9.0, 17.0), "ground_3day": (10.0, 19.0)}
DWELL_MEDIAN_H, DWELL_SIGMA, DWELL_MAX_H = 1.0, 0.8, 8.0
N_PER_YEAR = 150
GRID_BETA = [0.0, 5.0, 10.0, 15.0, 20.0]
GRID_HUB = [0.0, 0.25, 0.5, 0.75, 1.0]


def draw_samples(year: int, speed: str, n: int, seed: int):
    rng = np.random.default_rng(seed)
    days = np.arange(np.datetime64(f"{year}-06-03"), np.datetime64(f"{year}-08-26"))
    ship = rng.choice(days, n)
    lo, hi = DELIVERY_WINDOW[speed]
    deliver_h = rng.uniform(lo, hi, n)
    door = rng.choice(list(DOORSTEP_P), n, p=list(DOORSTEP_P.values()))
    dwell = np.clip(rng.lognormal(np.log(DWELL_MEDIAN_H), DWELL_SIGMA, n), 0.1, DWELL_MAX_H)
    pkg = rng.choice(["poly_mailer", "padded_mailer"], n)
    return [dict(ship=str(s), deliver_h=float(d), door=str(o), dwell=float(w), pkg=str(p))
            for s, d, o, w, p in zip(ship, deliver_h, door, dwell, pkg)]


def simulate_arm(weathers: dict, speed: str, seed: int = 7) -> dict:
    fr_2025, fr_1530, any_exc = [], [], []
    for year, w in weathers.items():
        samples = draw_samples(year, speed, N_PER_YEAR, seed + year)
        legs = [itinerary.build(s["ship"], speed, s["deliver_h"], s["door"], s["dwell"], after_h=0.0)
                for s in samples]
        temps, env, times, valid = run_batch(w, legs, [s["pkg"] for s in samples], [22.0] * len(samples))
        body = temps[:, 1:]
        for i, s in enumerate(samples):
            pickup = legs[i][0][2]  # end of the pharmacy leg
            m = valid[i] & (times[i] >= pickup - 1e-6)
            x = body[i][m]
            fr_2025.append(100.0 * np.mean((x < 20.0) | (x > 25.0)))
            fr_1530.append(100.0 * np.mean((x < 15.0) | (x > 30.0)))
            any_exc.append(bool(np.any((x < 20.0) | (x > 25.0))))
    a, b = np.array(fr_2025), np.array(fr_1530)
    return {
        "n": int(len(a)),
        "mean_out_20_25": round(float(a.mean()), 1),
        "p10_p50_p90_out_20_25": [round(float(q), 1) for q in np.percentile(a, [10, 50, 90])],
        "share_in_ashp_27_54": round(float(np.mean((a >= ASHP_RANGE[0]) & (a <= ASHP_RANGE[1]))) * 100, 1),
        "mean_out_15_30": round(float(b.mean()), 1),
        "p10_p50_p90_out_15_30": [round(float(q), 1) for q in np.percentile(b, [10, 50, 90])],
        "share_any_excursion_20_25": round(100.0 * float(np.mean(any_exc)), 1),
    }


def loss(res: dict, key: str) -> float:
    return sum((res[s][key] - TARGETS[s]) ** 2 for s in TARGETS) ** 0.5


def main() -> dict:
    t0 = time.time()
    weathers = {2024: summer_weather("laguardia", 2024), 2025: summer_weather("laguardia", 2025)}
    prior = {k: params.PARAMS["env"][k].prior for k in ("truck_beta", "hub_f")}
    current = {k: params.PARAMS["env"][k].value for k in ("truck_beta", "hub_f")}

    def evaluate(beta, hub):
        params.set_free(truck_beta=beta, hub_f=hub)
        return {s: simulate_arm(weathers, s) for s in TARGETS}

    grid = []
    for beta in GRID_BETA:
        for hub in GRID_HUB:
            r = evaluate(beta, hub)
            grid.append({"truck_beta": beta, "hub_f": hub,
                         "ground_3day": r["ground_3day"]["mean_out_20_25"],
                         "next_day": r["next_day"]["mean_out_20_25"],
                         "ground_3day_15_30": r["ground_3day"]["mean_out_15_30"],
                         "next_day_15_30": r["next_day"]["mean_out_15_30"],
                         "rmse_20_25": round(loss(r, "mean_out_20_25") / 2 ** 0.5, 2),
                         "rmse_15_30": round(loss(r, "mean_out_15_30") / 2 ** 0.5, 2)})
            print(grid[-1], f"{time.time() - t0:.0f}s", flush=True)
    best = min(grid, key=lambda g: g["rmse_20_25"])
    best_1530 = min(grid, key=lambda g: g["rmse_15_30"])
    before = evaluate(prior["truck_beta"], prior["hub_f"])
    after_1530 = evaluate(best_1530["truck_beta"], best_1530["hub_f"])
    after = evaluate(best["truck_beta"], best["hub_f"])  # adopted: 20-25 C reading (see VALIDATION.md)
    # sensitivity (not used for calibration): morning next-day commitment, prompt retrieval
    sens = {}
    saved_win, saved_dwell = dict(DELIVERY_WINDOW), DWELL_MEDIAN_H
    DELIVERY_WINDOW["next_day"] = (8.5, 12.0)
    sens["next_day_morning_8.5_12"] = simulate_arm(weathers, "next_day")
    DELIVERY_WINDOW.update(saved_win)
    globals()["DWELL_MEDIAN_H"] = 0.25
    sens["prompt_retrieval_dwell_median_15min"] = {s: simulate_arm(weathers, s) for s in TARGETS}
    globals()["DWELL_MEDIAN_H"] = saved_dwell
    params.set_free(**current)
    res = {
        "targets": TARGETS, "ashp_summer_range": ASHP_RANGE,
        "assumptions": {"doorstep_p": DOORSTEP_P, "delivery_window_local_h": DELIVERY_WINDOW,
                        "dwell_lognormal_median_h": DWELL_MEDIAN_H, "dwell_sigma": DWELL_SIGMA,
                        "dwell_max_h": DWELL_MAX_H, "mailers": "poly 50% / padded 50%",
                        "n_per_arm": 2 * N_PER_YEAR, "weather": "LaGuardia ISD hourly, JJA 2024 + JJA 2025"},
        "prior": prior, "before": before,
        "best_if_target_is_20_25": {"truck_beta": best["truck_beta"], "hub_f": best["hub_f"],
                                    "rmse": best["rmse_20_25"]},
        "adopted": {"truck_beta": best["truck_beta"], "hub_f": best["hub_f"]}, "after": after,
        "sensitivity_at_calibrated": sens,
        "best_if_target_is_15_30": {"truck_beta": best_1530["truck_beta"], "hub_f": best_1530["hub_f"],
                                    "rmse": best_1530["rmse_15_30"], "results": after_1530},
        "grid": grid, "runtime_s": round(time.time() - t0, 1),
    }
    OUT_JSON.write_text(json.dumps(res, indent=1))
    print(json.dumps({k: res[k] for k in ("prior", "before", "adopted", "after", "best_if_target_is_15_30")}, indent=1))
    return res


if __name__ == "__main__":
    main()
