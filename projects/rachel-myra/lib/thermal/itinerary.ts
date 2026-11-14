// Shipping itineraries: port of scripts/thermal_sim/itinerary.py.
// Template clock times are ASSUMPTIONS (see scripts/thermal_sim/README.md).

import { PARAMS } from "./params.ts";
import type { Leg } from "./model.ts";

export type Speed = "next_day" | "ground_3day";
const OUT_FOR_DELIVERY_H = 6.5;
const PACK_H = 16.0;
const PICKUP_H = 16.5;
const HUB_ARRIVE_H = 18.0;
const NEXT_DAY_MIDDLE: [string, number, number][] = [["hub", HUB_ARRIVE_H, 24 + OUT_FOR_DELIVERY_H]];
const GROUND_MIDDLE: [string, number, number][] = [
  ["hub", 18, 22],
  ["truck", 22, 30],
  ["hub", 30, 36],
  ["truck", 36, 44],
  ["hub", 44, 54],
  ["truck", 54, 62],
  ["hub", 62, 72 + OUT_FOR_DELIVERY_H],
];
const SPEED_DAYS: Record<Speed, number> = { next_day: 1, ground_3day: 3 };

/** Python's round() (half to even) so step rounding matches the reference. */
export function roundHalfEven(x: number): number {
  const r = Math.round(x);
  return Math.abs(x % 1) === 0.5 && r % 2 !== 0 ? r - 1 : r;
}

export function localMidnightUtc(day: string): number {
  const [y, m, d] = day.split("-").map(Number);
  return Date.UTC(y, m - 1, d) / 1000 - PARAMS.site.utc_offset_h * 3600;
}

export function addDays(day: string, n: number): string {
  const [y, m, d] = day.split("-").map(Number);
  return new Date(Date.UTC(y, m - 1, d + n)).toISOString().slice(0, 10);
}

export function localHour(epoch: number): number {
  return (((epoch + PARAMS.site.utc_offset_h * 3600) % 86400) + 86400) % 86400 / 3600;
}

/** Legs from packing (16:00 local on shipDay) to afterH hours after the package is brought inside. */
export function build(shipDay: string, speed: Speed, deliveryHour: number, doorstep: string, dwellH: number,
  afterEnv = "home_ac", afterH = 3.0, dispenseEnv = "pharmacy"): Leg[] {
  const m = localMidnightUtc(shipDay);
  const H = 3600;
  const dt = PARAMS.num.dt_s;
  const days = SPEED_DAYS[speed];
  const middle = speed === "next_day" ? NEXT_DAY_MIDDLE : GROUND_MIDDLE;
  const legs: Leg[] = [
    [dispenseEnv, m + PACK_H * H, m + PICKUP_H * H],
    ["truck", m + PICKUP_H * H, m + HUB_ARRIVE_H * H],
  ];
  for (const [e, a, b] of middle) legs.push([e, m + a * H, m + b * H]);
  const ofd = m + (24 * days + OUT_FOR_DELIVERY_H) * H;
  let deliver = m + (24 * days + Math.max(deliveryHour, OUT_FOR_DELIVERY_H + 0.25)) * H;
  deliver = m + roundHalfEven((deliver - m) / dt) * dt;
  legs.push(["truck", ofd, deliver]);
  const inside = deliver + roundHalfEven((dwellH * H) / dt) * dt;
  if (inside > deliver) legs.push([doorstep, deliver, inside]);
  if (afterH > 0) legs.push([afterEnv, inside, inside + roundHalfEven((afterH * H) / dt) * dt]);
  return legs;
}
