"""Precompute demo scenarios -> data/processed/thermal_scenarios.json.

Contents
--------
* ``weather``      : the hourly input series (replay heat wave + 48 h spin-up),
                     so the TypeScript port can recompute everything.
* ``params``       : parameter snapshot used (incl. calibrated free params).
* ``hero``         : "Your epinephrine was delivered at 1:12 PM" - bring it in
                     after 30 min vs 4 h (sun and shade).
* ``grid``         : drug x packaging x doorstep x dwell, next-day shipment
                     delivered 1:00 PM on the hottest replay day.
* ``home``         : each drug kept at home (AC / no AC / top floor no AC)
                     through the whole replay heat wave.
* ``preship``      : pre-ship checks for each drug on the replay.

Run:  cd scripts && uv run --python 3.12 --with numpy,pandas python -m thermal_sim.scenarios
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from . import itinerary, params
from .advice import assess, load_profiles
from .batch import run_batch
from .metrics import summarize
from .model import Weather
from .preship import preship_check
from .weather_io import REPLAY, replay_weather

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "data" / "processed" / "thermal_scenarios.json"
DOWNSAMPLE = 10  # keep every 10th 1-min sample

SHIPPED_DRUGS = ["insulin_pen", "epinephrine_autoinjector", "albuterol_inhaler", "glucose_test_strips",
                 "glp1_pen", "oral_tablet_crt"]
PACKAGINGS = ["poly_mailer", "padded_mailer", "insulated_box", "insulated_box_cold_pack",
              "insulated_box_frozen_pack", "insulated_box_frozen_pack_buffered", "insulated_box_crt_pcm"]
DOORSTEPS = ["porch_shade", "porch_sun", "mailbox_sun"]
DWELLS_H = [0.5, 2.0, 6.0]


def c_to_f(c: float) -> float:
    return c * 9 / 5 + 32


def _pack(legs, pkg, T0, temps, valid_n, profile, extra=None):
    trace = temps[: valid_n + 1]
    s = summarize(trace, delta_h_kj_mol=profile.get("mkt_delta_h_kj_mol"))
    a = assess(trace, profile)
    item = {
        "inputs": {"legs": [[e, a_, b_] for e, a_, b_ in legs], "packaging": pkg, "T0_c": T0},
        "segments": [{"env": e, "start_local": itinerary.local_iso(a_), "end_local": itinerary.local_iso(b_)}
                     for e, a_, b_ in legs],
        "trace": {"start_utc": legs[0][1], "step_min": DOWNSAMPLE * params.v("num", "dt_s") / 60.0,
                  "temp_c": [round(float(x), 2) for x in trace[::DOWNSAMPLE]]},
        "metrics": s,
        "advice": a,
    }
    door = [(e, a_, b_) for e, a_, b_ in legs if e in ("porch_shade", "porch_sun", "mailbox_sun", "lobby")]
    if door:
        dt = params.v("num", "dt_s")
        i0 = int(round((door[0][1] - legs[0][1]) / dt))
        i1 = int(round((door[0][2] - legs[0][1]) / dt))
        item["temp_at_delivery_c"] = round(float(trace[i0]), 2)
        item["doorstep_metrics"] = summarize(trace[i0: i1 + 1], delta_h_kj_mol=profile.get("mkt_delta_h_kj_mol"))
    if extra:
        item.update(extra)
    return item


def run_set(w, specs, profiles):
    """specs: list of dict(drug, legs, pkg, T0, meta)."""
    temps, _, _, valid = run_batch(w, [s["legs"] for s in specs], [s["pkg"] for s in specs], [s["T0"] for s in specs])
    out = []
    for i, s in enumerate(specs):
        out.append(_pack(s["legs"], s["pkg"], s["T0"], temps[i], int(valid[i].sum()), profiles[s["drug"]],
                         dict(s["meta"], drug=s["drug"])))
    return out


def main() -> dict:
    profiles = load_profiles()
    # round-trip through the JSON format so Python and TypeScript use identical inputs
    w = Weather.from_json(replay_weather("laguardia").to_json())
    hrs = w.hours
    # hottest replay day (local) by daily max
    local = [datetime.fromtimestamp(t + params.v("site", "utc_offset_h") * 3600, tz=timezone.utc) for t in hrs]
    days = sorted({d.date().isoformat() for d in local})
    dmax = {d: max(w.temp_c[i] for i, x in enumerate(local) if x.date().isoformat() == d) for d in days}
    replay_days = days[2:]  # first 48 h are spin-up
    peak_day = max(replay_days, key=lambda d: dmax[d])
    ship_day = itinerary.add_days(peak_day, -1)

    def T0_of(drug):
        return profiles[drug]["dispense_temp_c"]

    def disp(drug):
        return "pharmacy"  # packed box waits at room temperature; cold-chain drugs start at dispense_temp_c

    # ---------------- hero
    hero_specs = []
    deliver_h = 13.0 + 12.0 / 60.0
    for door in ["porch_sun", "porch_shade"]:
        for dwell in [0.5, 4.0]:
            legs = itinerary.build(ship_day, "next_day", deliver_h, door, dwell, after_env="home_ac", after_h=2.0)
            hero_specs.append(dict(drug="epinephrine_autoinjector", legs=legs, pkg="poly_mailer",
                                   T0=T0_of("epinephrine_autoinjector"),
                                   meta={"id": f"hero_{door}_{int(dwell * 60)}min", "doorstep": door, "dwell_h": dwell}))
    hero = run_set(w, hero_specs, profiles)
    # sensitivity: the truck/hub parameters that best fit the 15-30 C reading of the
    # logger studies (sun-heated truck cargo, unconditioned hubs); see VALIDATION.md
    val = json.loads((Path(__file__).resolve().parent / "validation_results.json").read_text())
    alt = val["best_if_target_is_15_30"]
    override = {"truck_beta": alt["truck_beta"], "hub_f": alt["hub_f"]}
    saved = {k: params.v("env", k) for k in override}
    params.set_free(**override)
    hero_alt = run_set(w, hero_specs, profiles)
    params.set_free(**saved)
    for h in hero_alt:
        h["id"] += "_hot_truck"
        h["inputs"]["params_override"] = {"env": override}
    t_del = itinerary.local_midnight_utc(peak_day) + deliver_h * 3600
    amb = float(w.at(w.temp_c, np.array([t_del]))[0])
    hero_block = {
        "story": "Your epinephrine was delivered at 1:12 PM. Bring it inside within 30 minutes.",
        "delivered_local": itinerary.local_iso(t_del),
        "outdoor_temp_c_at_delivery": round(amb, 1),
        "outdoor_temp_f_at_delivery": round(c_to_f(amb), 0),
        "note": "Outdoor temperature is the LaGuardia hourly observation interpolated to 1:12 PM on the hottest replay day; the pitch line says 94 F, the replay value is shown here.",
        "scenarios": hero,
        "sensitivity_hot_truck": {
            "what": "Same four cases with the truck/hub parameters that best fit the 15-30 C reading of the logger studies (truck cargo heated by the sun, unconditioned hubs). Upper case for pre-delivery heat; see VALIDATION.md.",
            "scenarios": hero_alt,
        },
    }

    # ---------------- grid
    grid_specs = []
    for drug in SHIPPED_DRUGS:
        for pkg in PACKAGINGS:
            for door in DOORSTEPS:
                for dwell in DWELLS_H:
                    legs = itinerary.build(ship_day, "next_day", 13.0, door, dwell, after_env="home_ac", after_h=1.0,
                                           dispense_env=disp(drug))
                    grid_specs.append(dict(drug=drug, legs=legs, pkg=pkg, T0=T0_of(drug),
                                           meta={"id": f"{drug}|{pkg}|{door}|{dwell:g}h", "packaging": pkg,
                                                 "doorstep": door, "dwell_h": dwell}))
    grid = run_set(w, grid_specs, profiles)

    # ---------------- home (whole replay)
    start = itinerary.local_midnight_utc(replay_days[0])
    end = hrs[-1]
    home_specs = []
    for drug in SHIPPED_DRUGS + ["insulin_pump_reservoir"]:
        for env in ["home_ac", "home_noac", "home_noac_top"]:
            legs = [(env, start, start + np.floor((end - start) / 3600.0) * 3600.0)]
            home_specs.append(dict(drug=drug, legs=legs, pkg="poly_mailer", T0=T0_of(drug) if not profiles[drug].get("shipped_cold") else 22.0,
                                   meta={"id": f"{drug}|{env}", "environment": env,
                                         "note": "Product kept in its pharmacy bag at home for the whole replay (refrigerated products: kept OUT of the fridge, i.e. in-use pen)."}))
    home = run_set(w, home_specs, profiles)

    # ---------------- pre-ship checks
    pre = []
    for drug in SHIPPED_DRUGS:
        for sd, label in [(itinerary.add_days(peak_day, -3), "ground ship into the hottest day"),
                          (replay_days[0], "first replay day")]:
            r = preship_check(profiles[drug], w, sd, "ground_3day", "poly_mailer", (10.0, 19.0), "porch_sun",
                              expected_dwell_h=2.0, days_of_supply=7)
            pre.append({"id": f"{drug}|{sd}|ground_3day", "drug": drug, "ship_day": sd, "label": label,
                        "inputs": {"speed": "ground_3day", "packaging": "poly_mailer", "delivery_window": [10.0, 19.0],
                                   "doorstep": "porch_sun", "expected_dwell_h": 2.0, "days_of_supply": 7},
                        "result": r})

    out = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "honesty_rule": "Advice tiers only (within label / within what studies tested / beyond what studies tested). No potency percentages.",
        "weather": dict(w.to_json(), source=f"{REPLAY.relative_to(REPO)} (LaGuardia temp + wind) with cloud cover from NCEI ISD LaGuardia (data/raw/thermal_sim/); first 48 h are model spin-up",
                        station="LaGuardia (KLGA)"),
        "replay": {"days": replay_days, "peak_day": peak_day, "peak_day_max_c": round(dmax[peak_day], 1)},
        "params": params.flat_values(),
        "packaging": {k: {"label": p.label, "R_wall": p.R_wall, "coolant_kg": p.coolant_kg} for k, p in params.PACKAGING.items()},
        "hero": hero_block,
        "grid": grid,
        "home": home,
        "preship": pre,
    }
    OUT.write_text(json.dumps(out, separators=(",", ":")))
    print(f"wrote {OUT} ({OUT.stat().st_size / 1e3:.0f} kB): {len(grid)} grid, {len(home)} home, {len(pre)} preship")
    for h in hero:
        print(h["id"], h["metrics"]["peak_c"], h["metrics"]["mkt_c"], h["advice"]["tier"])
    return out


if __name__ == "__main__":
    main()
