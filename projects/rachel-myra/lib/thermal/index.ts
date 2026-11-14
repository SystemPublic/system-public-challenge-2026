// Heat-Safe Delivery engine (dependency-free). Reference implementation and docs:
// scripts/thermal_sim/ (Python). Parameters: scripts/thermal_sim/PARAMETERS.md.
//
// Typical use in the app:
//   const w = makeWeather(hourlyForecast);           // {start_utc, temp_c[], wind_ms[], cloud[]}
//   const legs = build("2025-06-23", "next_day", 13.2, "porch_sun", 0.5);
//   const run = simulateLegs(w, legs, "poly_mailer", profile.dispense_temp_c);
//   const m = summarize(run.temp, undefined, profile.mkt_delta_h_kj_mol);  // peak, MKT, minutes above
//   const advice = assess(run.temp, profile);       // 3 tiers only; never a potency %
//   const check = preshipCheck({ profile, weather: w, shipDay, speed, packaging, deliveryWindow, doorstep });

export { PARAMS, PACKAGING, ENVIRONMENTS, ENV_LABELS } from "./params.ts";
export type { Packaging, EnvName } from "./params.ts";
export { makeWeather, simulateLegs, legsToGrid, solar, interp, emaHourly } from "./model.ts";
export type { Leg, Weather, WeatherInput, RunResult } from "./model.ts";
export { mktC, summarize, THRESHOLDS_C } from "./metrics.ts";
export type { Summary } from "./metrics.ts";
export { assess, ACTION, TIER_RANK } from "./advice.ts";
export type { Assessment, DrugProfile, Tier } from "./advice.ts";
export { build, addDays, localMidnightUtc, localHour } from "./itinerary.ts";
export type { Speed } from "./itinerary.ts";
export { preshipCheck, ACTION_TEXT } from "./preship.ts";
export type { PreshipInput, PlanName } from "./preship.ts";
