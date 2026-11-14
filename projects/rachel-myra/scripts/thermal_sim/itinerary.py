"""Shipping itineraries: ordered legs (environment, start, end) in UTC epoch.

All template times are local clock times (fixed offset ``site.utc_offset_h``)
and are ASSUMPTIONS describing a typical pharmacy -> carrier -> home chain:

next_day      packed 16:00 -> carrier pickup 16:30 -> truck to hub (1.5 h) ->
              hub/air network overnight -> out for delivery 06:30 next day ->
              delivered -> doorstep dwell -> indoors
ground_3day   same first evening, then alternating line-haul trailer and hub
              legs for two days (one daytime trailer leg each day), out for
              delivery 06:30 on day 3
Doorstep 'lobby' = conditioned lobby / package room / pickup locker.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import List, Tuple

from .params import v

Leg = Tuple[str, float, float]

OUT_FOR_DELIVERY_H = 6.5
PACK_H = 16.0
PICKUP_H = 16.5
HUB_ARRIVE_H = 18.0

# (env, start offset h, end offset h) relative to local midnight of ship day
NEXT_DAY_MIDDLE: List[Tuple[str, float, float]] = [
    ("hub", HUB_ARRIVE_H, 24 + OUT_FOR_DELIVERY_H),
]
GROUND_MIDDLE: List[Tuple[str, float, float]] = [
    ("hub", 18.0, 22.0),
    ("truck", 22.0, 30.0),      # overnight line-haul
    ("hub", 30.0, 36.0),
    ("truck", 36.0, 44.0),      # daytime line-haul (day 1, 12:00-20:00)
    ("hub", 44.0, 54.0),
    ("truck", 54.0, 62.0),      # day 2, 06:00-14:00
    ("hub", 62.0, 72 + OUT_FOR_DELIVERY_H),
]
SPEED_DAYS = {"next_day": 1, "ground_3day": 3}


def local_midnight_utc(day: str) -> float:
    d = date.fromisoformat(day)
    return datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp() - v("site", "utc_offset_h") * 3600.0


def local_hour(epoch: float) -> float:
    return ((epoch + v("site", "utc_offset_h") * 3600.0) % 86400.0) / 3600.0


def local_iso(epoch: float) -> str:
    off = v("site", "utc_offset_h")
    tz = timezone(timedelta(hours=off))
    return datetime.fromtimestamp(epoch, tz=tz).isoformat(timespec="minutes")


def add_days(day: str, n: int) -> str:
    return (date.fromisoformat(day) + timedelta(days=n)).isoformat()


def build(ship_day: str, speed: str, delivery_hour: float, doorstep: str, dwell_h: float,
          after_env: str = "home_ac", after_h: float = 3.0, dispense_env: str = "pharmacy") -> List[Leg]:
    """Legs from packing to `after_h` hours after the package is brought inside.

    delivery_hour is local clock time on the delivery day; it is clamped to be
    at least 15 minutes after the truck leaves at 06:30.
    """
    m = local_midnight_utc(ship_day)
    H = 3600.0
    days = SPEED_DAYS[speed]
    middle = NEXT_DAY_MIDDLE if speed == "next_day" else GROUND_MIDDLE
    legs: List[Leg] = [
        (dispense_env, m + PACK_H * H, m + PICKUP_H * H),
        ("truck", m + PICKUP_H * H, m + HUB_ARRIVE_H * H),
    ]
    legs += [(e, m + a * H, m + b * H) for e, a, b in middle]
    ofd = m + (24 * days + OUT_FOR_DELIVERY_H) * H
    deliver = m + (24 * days + max(delivery_hour, OUT_FOR_DELIVERY_H + 0.25)) * H
    # round to whole steps so legs line up with the integration grid
    dt = v("num", "dt_s")
    deliver = m + round((deliver - m) / dt) * dt
    legs.append(("truck", ofd, deliver))
    inside = deliver + round(dwell_h * H / dt) * dt
    if inside > deliver:
        legs.append((doorstep, deliver, inside))
    if after_h > 0:
        legs.append((after_env, inside, inside + round(after_h * H / dt) * dt))
    return legs

