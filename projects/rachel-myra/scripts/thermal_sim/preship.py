"""Pre-ship risk check: forecast + drug profile + shipping plan -> risk tier and
ONE recommended action, with reasons.

Each candidate plan is simulated for every whole-hour delivery time in the
expected delivery window, and judged by its *worst* case (the honesty rule
applies: tiers come from ``advice.assess``; nothing is extrapolated).

Escalation order (least disruptive first; the first plan whose worst case is
"use as normal" is recommended):

1. ship_as_is
2. upgrade_next_day             (if not already next-day)
3. insulated_cold_pack          (next-day + insulated box; frozen gel packs
                                 with a buffer around the product for
                                 cold-chain drugs, 22 C phase-change packs for
                                 room-temperature drugs)
4. reroute_pickup               (next-day to a conditioned pharmacy counter /
                                 indoor locker; the trip home is not modeled)
5. hold_until_heat_passes       (ship as planned on the first later day in the
                                 forecast that is "use as normal"; only if the
                                 patient's supply lasts)

If no plan reaches "use as normal", the plan with the best worst-case tier
(then the lowest peak) is recommended and the result says so.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np

from . import itinerary
from .advice import TIER_RANK, assess
from .metrics import summarize
from .batch import run_batch
from .model import Weather

RISK = {"use_as_normal": "low", "check_with_pharmacist": "moderate", "request_replacement": "high"}
ACTION_TEXT = {
    "ship_as_is": "Ship as planned",
    "upgrade_next_day": "Upgrade to next-day shipping",
    "insulated_cold_pack": "Ship next-day in an insulated box with temperature packs",
    "reroute_pickup": "Reroute to pharmacy / indoor locker pickup",
    "hold_until_heat_passes": "Hold the shipment until the heat passes",
}


def delivery_hours(window: Tuple[float, float]) -> List[float]:
    """Whole hours inside the window (or the window start if none)."""
    hours = [float(h) for h in range(int(np.ceil(window[0])), int(np.floor(window[1])) + 1)]
    return hours or [float(window[0])]


def _evaluate(weather: Weather, profile: dict, ship_day: str, speed: str, pkg: str, doorstep: str,
              window: Tuple[float, float], dwell_h: float, after_env: str) -> dict:
    T0 = profile["dispense_temp_c"]
    disp = "pharmacy"  # the packed box waits at room temperature; cold-chain drugs start at dispense_temp_c
    worst = None
    hours = delivery_hours(window)
    legs_list = [itinerary.build(ship_day, speed, float(h), doorstep, dwell_h, after_env=after_env, after_h=1.0,
                                 dispense_env=disp) for h in hours]
    temps, _, _, valid = run_batch(weather, legs_list, [pkg] * len(hours), [T0] * len(hours))
    for i, h in enumerate(hours):
        n = int(valid[i].sum())
        trace = temps[i, : n + 1]
        a = assess(trace, profile)
        key = (TIER_RANK[a["tier"]], a["exposure"]["peak_c"])
        if worst is None or key > worst[0]:
            s = summarize(trace, delta_h_kj_mol=profile.get("mkt_delta_h_kj_mol"))
            worst = (key, {"delivery_hour_local": float(h), "assessment": a, "metrics": s})
    w = worst[1]
    return {"speed": speed, "packaging": pkg, "doorstep": doorstep, "ship_day": ship_day,
            "worst_tier": w["assessment"]["tier"], "worst_case": w}


def preship_check(profile: dict, weather: Weather, ship_day: str, speed: str, packaging: str,
                  delivery_window: Tuple[float, float], doorstep: str, expected_dwell_h: float = 2.0,
                  after_env: str = "home_ac", days_of_supply: Optional[float] = None,
                  pickup_wait_h: float = 4.0, max_hold_days: int = 5) -> dict:
    cold_pkg = "insulated_box_frozen_pack_buffered" if profile.get("shipped_cold") else "insulated_box_crt_pcm"
    plans: List[Tuple[str, dict]] = []
    base = _evaluate(weather, profile, ship_day, speed, packaging, doorstep, delivery_window, expected_dwell_h, after_env)
    plans.append(("ship_as_is", base))
    if speed != "next_day":
        plans.append(("upgrade_next_day", _evaluate(weather, profile, ship_day, "next_day", packaging, doorstep,
                                                    delivery_window, expected_dwell_h, after_env)))
    plans.append(("insulated_cold_pack", _evaluate(weather, profile, ship_day, "next_day", cold_pkg, doorstep,
                                                   delivery_window, expected_dwell_h, after_env)))
    plans.append(("reroute_pickup", _evaluate(weather, profile, ship_day, "next_day", packaging, "lobby",
                                              delivery_window, pickup_wait_h, after_env)))
    # hold: later ship days that the forecast fully covers
    fc_end = weather.hours[-1]
    hold = None
    for d in range(1, max_hold_days + 1):
        if days_of_supply is not None and d >= days_of_supply:
            break
        day = itinerary.add_days(ship_day, d)
        legs = itinerary.build(day, speed, delivery_window[1], doorstep, expected_dwell_h, after_env=after_env, after_h=1.0)
        if legs[-1][2] > fc_end:
            break
        ev = _evaluate(weather, profile, day, speed, packaging, doorstep, delivery_window, expected_dwell_h, after_env)
        if ev["worst_tier"] == "use_as_normal":
            hold = ev
            hold["hold_days"] = d
            break
    if hold is not None:
        plans.append(("hold_until_heat_passes", hold))

    chosen = next(((n, p) for n, p in plans if p["worst_tier"] == "use_as_normal"), None)
    none_ok = chosen is None
    if none_ok:
        chosen = min(plans, key=lambda np_: (TIER_RANK[np_[1]["worst_tier"]],
                                             np_[1]["worst_case"]["metrics"]["peak_c"]))
    name, plan = chosen
    wc = base["worst_case"]
    reasons = [
        f"As planned ({speed.replace('_', ' ')}, {packaging.replace('_', ' ')}, {doorstep.replace('_', ' ')}, "
        f"{expected_dwell_h:g} h before it is brought inside), the worst delivery hour "
        f"({wc['delivery_hour_local']:.0f}:00) gives a peak product temperature of "
        f"{wc['metrics']['peak_c']:.1f} C and {wc['metrics']['minutes_above']['30']:.0f} min above 30 C: "
        f"{wc['assessment']['action'].lower()}.",
    ] + wc["assessment"]["reasons"]
    if name != "ship_as_is":
        pc = plan["worst_case"]
        extra = f" (ship on {plan['ship_day']}, {plan['hold_days']} day(s) later)" if name == "hold_until_heat_passes" else ""
        reasons.append(f"{ACTION_TEXT[name]}{extra}: worst-case peak {pc['metrics']['peak_c']:.1f} C -> "
                       f"{pc['assessment']['action'].lower()}.")
    if none_ok:
        reasons.append("No option in the forecast window keeps this product within its label; "
                       "this is the least-bad option. Consider a local fill instead of mail.")
    if name == "reroute_pickup":
        reasons.append("Assumes the package waits in a conditioned pharmacy or indoor locker; the trip home is not modeled.")
    return {
        "risk_tier": RISK[base["worst_tier"]],
        "recommended_action": name,
        "recommended_action_text": ACTION_TEXT[name],
        "reasons": reasons,
        "no_option_within_label": none_ok,
        "options": [{"action": n, "tier": p["worst_tier"], "peak_c": p["worst_case"]["metrics"]["peak_c"],
                     "minutes_above_30": p["worst_case"]["metrics"]["minutes_above"]["30"],
                     "ship_day": p["ship_day"], "speed": p["speed"], "packaging": p["packaging"],
                     "doorstep": p["doorstep"]} for n, p in plans],
    }
