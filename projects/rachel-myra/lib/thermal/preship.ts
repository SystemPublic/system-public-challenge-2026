// Pre-ship risk check: port of scripts/thermal_sim/preship.py.
// Forecast + drug profile + shipping plan -> risk tier + ONE recommended action + reasons.
// Escalation: ship as-is -> upgrade to next-day -> insulated box + temperature packs ->
// reroute to pickup -> hold until the heat passes. Each plan is judged by its worst
// whole-hour delivery time inside the expected window.

import { build, addDays } from "./itinerary.ts";
import type { Speed } from "./itinerary.ts";
import { simulateLegs } from "./model.ts";
import type { Weather } from "./model.ts";
import { assess, TIER_RANK } from "./advice.ts";
import type { Assessment, DrugProfile, Tier } from "./advice.ts";
import { summarize } from "./metrics.ts";
import type { Summary } from "./metrics.ts";

export type PlanName = "ship_as_is" | "upgrade_next_day" | "insulated_cold_pack" | "reroute_pickup" | "hold_until_heat_passes";
const RISK: Record<Tier, string> = { use_as_normal: "low", check_with_pharmacist: "moderate", request_replacement: "high" };
export const ACTION_TEXT: Record<PlanName, string> = {
  ship_as_is: "Ship as planned",
  upgrade_next_day: "Upgrade to next-day shipping",
  insulated_cold_pack: "Ship next-day in an insulated box with temperature packs",
  reroute_pickup: "Reroute to pharmacy / indoor locker pickup",
  hold_until_heat_passes: "Hold the shipment until the heat passes",
};

type Plan = {
  speed: Speed; packaging: string; doorstep: string; ship_day: string; worst_tier: Tier; hold_days?: number;
  worst_case: { delivery_hour_local: number; assessment: Assessment; metrics: Summary };
};

export function deliveryHours(window: [number, number]): number[] {
  const out: number[] = [];
  for (let h = Math.ceil(window[0]); h <= Math.floor(window[1]); h++) out.push(h);
  return out.length ? out : [window[0]];
}

function evaluate(w: Weather, profile: DrugProfile, shipDay: string, speed: Speed, pkg: string, doorstep: string,
  window: [number, number], dwellH: number, afterEnv: string): Plan {
  const disp = "pharmacy"; // the packed box waits at room temperature; cold-chain drugs start at dispense_temp_c
  let worst: { key: [number, number]; wc: Plan["worst_case"] } | null = null;
  for (const h of deliveryHours(window)) {
    const legs = build(shipDay, speed, h, doorstep, dwellH, afterEnv, 1.0, disp);
    const r = simulateLegs(w, legs, pkg, profile.dispense_temp_c);
    const a = assess(r.temp, profile);
    const key: [number, number] = [TIER_RANK[a.tier], a.exposure.peak_c];
    if (!worst || key[0] > worst.key[0] || (key[0] === worst.key[0] && key[1] > worst.key[1])) {
      worst = { key, wc: { delivery_hour_local: h, assessment: a, metrics: summarize(r.temp, undefined, profile.mkt_delta_h_kj_mol) } };
    }
  }
  return { speed, packaging: pkg, doorstep, ship_day: shipDay, worst_tier: worst!.wc.assessment.tier, worst_case: worst!.wc };
}

export type PreshipInput = {
  profile: DrugProfile;
  weather: Weather; // hourly forecast covering the shipment
  shipDay: string; // YYYY-MM-DD (local)
  speed: Speed;
  packaging: string;
  deliveryWindow: [number, number]; // local hours
  doorstep: string; // porch_shade | porch_sun | mailbox_sun | lobby
  expectedDwellH?: number;
  afterEnv?: string;
  daysOfSupply?: number | null;
  pickupWaitH?: number;
  maxHoldDays?: number;
};

export function preshipCheck(inp: PreshipInput) {
  const { profile, weather: w, shipDay, speed, packaging, deliveryWindow: win, doorstep } = inp;
  const dwell = inp.expectedDwellH ?? 2.0;
  const afterEnv = inp.afterEnv ?? "home_ac";
  const coldPkg = profile.shipped_cold ? "insulated_box_frozen_pack_buffered" : "insulated_box_crt_pcm";
  const plans: [PlanName, Plan][] = [];
  const base = evaluate(w, profile, shipDay, speed, packaging, doorstep, win, dwell, afterEnv);
  plans.push(["ship_as_is", base]);
  if (speed !== "next_day") plans.push(["upgrade_next_day", evaluate(w, profile, shipDay, "next_day", packaging, doorstep, win, dwell, afterEnv)]);
  plans.push(["insulated_cold_pack", evaluate(w, profile, shipDay, "next_day", coldPkg, doorstep, win, dwell, afterEnv)]);
  plans.push(["reroute_pickup", evaluate(w, profile, shipDay, "next_day", packaging, "lobby", win, inp.pickupWaitH ?? 4.0, afterEnv)]);
  const fcEnd = w.hours[w.hours.length - 1];
  for (let d = 1; d <= (inp.maxHoldDays ?? 5); d++) {
    if (inp.daysOfSupply != null && d >= inp.daysOfSupply) break;
    const day = addDays(shipDay, d);
    const legs = build(day, speed, win[1], doorstep, dwell, afterEnv, 1.0);
    if (legs[legs.length - 1][2] > fcEnd) break;
    const ev = evaluate(w, profile, day, speed, packaging, doorstep, win, dwell, afterEnv);
    if (ev.worst_tier === "use_as_normal") {
      ev.hold_days = d;
      plans.push(["hold_until_heat_passes", ev]);
      break;
    }
  }
  let chosen = plans.find(([, p]) => p.worst_tier === "use_as_normal");
  const noneOk = !chosen;
  if (!chosen) {
    chosen = [...plans].sort((a, b) => TIER_RANK[a[1].worst_tier] - TIER_RANK[b[1].worst_tier] || a[1].worst_case.metrics.peak_c - b[1].worst_case.metrics.peak_c)[0];
  }
  const [name, plan] = chosen;
  const wc = base.worst_case;
  const reasons = [
    `As planned (${speed.replace(/_/g, " ")}, ${packaging.replace(/_/g, " ")}, ${doorstep.replace(/_/g, " ")}, ${dwell} h before it is brought inside), the worst delivery hour (${wc.delivery_hour_local.toFixed(0)}:00) gives a peak product temperature of ${wc.metrics.peak_c.toFixed(1)} C and ${wc.metrics.minutes_above["30"].toFixed(0)} min above 30 C: ${wc.assessment.action.toLowerCase()}.`,
    ...wc.assessment.reasons,
  ];
  if (name !== "ship_as_is") {
    const pc = plan.worst_case;
    const extra = name === "hold_until_heat_passes" ? ` (ship on ${plan.ship_day}, ${plan.hold_days} day(s) later)` : "";
    reasons.push(`${ACTION_TEXT[name]}${extra}: worst-case peak ${pc.metrics.peak_c.toFixed(1)} C -> ${pc.assessment.action.toLowerCase()}.`);
  }
  if (noneOk) reasons.push("No option in the forecast window keeps this product within its label; this is the least-bad option. Consider a local fill instead of mail.");
  if (name === "reroute_pickup") reasons.push("Assumes the package waits in a conditioned pharmacy or indoor locker; the trip home is not modeled.");
  return {
    risk_tier: RISK[base.worst_tier],
    recommended_action: name,
    recommended_action_text: ACTION_TEXT[name],
    reasons,
    no_option_within_label: noneOk,
    options: plans.map(([n, p]) => ({ action: n, tier: p.worst_tier, peak_c: p.worst_case.metrics.peak_c, minutes_above_30: p.worst_case.metrics.minutes_above["30"], ship_day: p.ship_day, speed: p.speed, packaging: p.packaging, doorstep: p.doorstep })),
  };
}
