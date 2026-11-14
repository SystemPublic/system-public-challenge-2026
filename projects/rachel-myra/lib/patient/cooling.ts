// Morning cooling-place matching (spec §4.4 item 3): a specific air-conditioned public place
// near the patient, open that day, step-free if needed, with a leave-by time so they
// "get there before 11 AM". Uses the routing agent's cooling_match.csv when present
// (real travel times); otherwise this fallback: nearest by straight line × detour factor
// at an age-appropriate walking speed, or a naive transit estimate (labeled).

import type { CoolingPlaceRules } from "../types/health-system.ts";
import type { CoolingMatch, CoolingPlaceOption, LatLon } from "../types/patient.ts";
import { fmtMin, toMin } from "./escalation.ts";

export interface CoolingPlace {
  id: string;
  name: string;
  category: string;
  indoor: boolean;
  address: string | null;
  lat: number;
  lon: number;
  official: boolean;
  finderStatus: string | null;
  stepFree: "yes" | "no" | "unknown";
  hours: Record<string, string> | null;
  openingHours: string | null;
  facilityType: string | null;
  membershipRequired: string | null;
}

export function fmtAddress(street: string, borough?: string | null, zip?: string | null): string {
  const tail = [borough, zip].filter((x) => x && String(x).trim()).join(" ");
  return tail ? `${street}, ${tail}` : street;
}

export function placesFromGeoJson(gj: any): CoolingPlace[] {
  return (gj?.features ?? [])
    .filter((f: any) => f?.geometry?.type === "Point")
    .map((f: any) => {
      const p = f.properties ?? {};
      const acc = String(p.accessible ?? "").toLowerCase();
      const wc = String(p.wheelchair ?? "").toLowerCase();
      const stepFree: CoolingPlace["stepFree"] = acc === "yes" || wc === "yes" ? "yes" : acc === "no" || wc === "no" || wc === "limited" ? "no" : "unknown";
      return {
        id: String(p.source_id ?? p.name),
        name: String(p.name ?? "Unnamed place"),
        category: String(p.category ?? ""),
        indoor: p.indoor !== false,
        address: p.address ? fmtAddress(p.address, p.borough, p.zip) : null,
        lon: f.geometry.coordinates[0],
        lat: f.geometry.coordinates[1],
        official: p.official_cooling_center === true,
        finderStatus: p.finder_status ?? null,
        stepFree,
        hours: p.hours && typeof p.hours === "object" ? p.hours : null,
        openingHours: typeof p.opening_hours === "string" ? p.opening_hours : typeof p.hours === "string" ? p.hours : null,
        facilityType: p.facility_type ?? null,
        membershipRequired: p.membership_required ?? null,
      } as CoolingPlace;
    });
}

// ---------------------------------------------------------------- hours parsing

const DAY_NAMES = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
const OSM_DAYS = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];

/** "9a", "8:30a", "12p", "12a" (as a closing time → 24:00), "10:00" → minutes after midnight. */
export function parseClock(s: string, isClose = false): number | null {
  const t = s.trim().toLowerCase();
  let m = t.match(/^(\d{1,2})(?::(\d{2}))?\s*([ap])m?$/);
  if (m) {
    let h = Number(m[1]) % 12;
    if (m[3] === "p") h += 12;
    let v = h * 60 + Number(m[2] ?? 0);
    if (isClose && v === 0) v = 1440;
    return v;
  }
  m = t.match(/^(\d{1,2}):(\d{2})$/);
  if (m) {
    let v = Number(m[1]) * 60 + Number(m[2]);
    if (isClose && v === 0) v = 1440;
    return v;
  }
  return null;
}

function parseRanges(s: string): { open: number; close: number } | null {
  const parts = s.split(",").map((x) => x.trim()).filter(Boolean);
  let open = Infinity;
  let close = -Infinity;
  for (const r of parts) {
    const [a, b] = r.split("-");
    if (!a || !b) return null;
    const o = parseClock(a);
    const c = parseClock(b, true);
    if (o === null || c === null) return null;
    open = Math.min(open, o);
    close = Math.max(close, c);
  }
  return Number.isFinite(open) ? { open, close } : null;
}

function osmDaySet(spec: string): Set<number> | null {
  const out = new Set<number>();
  for (const part of spec.split(",").map((x) => x.trim())) {
    const [a, b] = part.split("-");
    const ia = OSM_DAYS.indexOf(a);
    if (ia < 0) return null;
    if (!b) out.add(ia);
    else {
      const ib = OSM_DAYS.indexOf(b);
      if (ib < 0) return null;
      for (let i = ia; ; i = (i + 1) % 7) {
        out.add(i);
        if (i === ib) break;
      }
    }
  }
  return out;
}

export type DayHours = { open: number; close: number; text: string } | "closed" | null;

/** Hours on a weekday (0 = Sunday). null = unknown. */
export function hoursOn(place: Pick<CoolingPlace, "hours" | "openingHours">, weekday: number): DayHours {
  if (place.hours) {
    const v = place.hours[DAY_NAMES[weekday]];
    if (v === undefined || /closed/i.test(v)) return "closed";
    const r = parseRanges(v);
    return r ? { ...r, text: v } : null;
  }
  const oh = place.openingHours?.trim();
  if (!oh) return null;
  if (oh === "24/7") return { open: 0, close: 1440, text: "24/7" };
  let result: DayHours = null;
  let anyRule = false;
  for (const rule of oh.split(";").map((x) => x.trim()).filter(Boolean)) {
    const m = rule.match(/^((?:(?:Mo|Tu|We|Th|Fr|Sa|Su)(?:-(?:Mo|Tu|We|Th|Fr|Sa|Su))?\s*,?\s*)+)\s+(.*)$/);
    let days: Set<number> | null;
    let body: string;
    if (m) {
      days = osmDaySet(m[1].replace(/\s+/g, "").replace(/,$/, ""));
      body = m[2].trim();
    } else if (/^PH\b/.test(rule)) continue;
    else {
      days = new Set([0, 1, 2, 3, 4, 5, 6]);
      body = rule;
    }
    if (!days) return null;
    anyRule = true;
    if (!days.has(weekday)) continue;
    if (/^(off|closed)$/i.test(body)) result = "closed";
    else {
      const r = parseRanges(body);
      if (!r) return null;
      result = { ...r, text: `${OSM_DAYS[weekday]} ${body}` };
    }
  }
  return anyRule && result === null ? "closed" : result;
}

// ---------------------------------------------------------------- matching

export function haversineKm(a: LatLon, b: LatLon): number {
  const R = 6371;
  const dLat = ((b.lat - a.lat) * Math.PI) / 180;
  const dLon = ((b.lon - a.lon) * Math.PI) / 180;
  const s = Math.sin(dLat / 2) ** 2 + Math.cos((a.lat * Math.PI) / 180) * Math.cos((b.lat * Math.PI) / 180) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(s));
}

export function weekdayOf(isoDate: string): number {
  return new Date(`${isoDate.slice(0, 10)}T12:00:00Z`).getUTCDay();
}

export interface CoolingNeeds {
  home: LatLon | null;
  age: number;
  stepFreeNeeded: boolean;
  canReach: "yes" | "with_help" | "no" | null;
}

export function matchCoolingPlace(needs: CoolingNeeds, places: CoolingPlace[], date: string, rules: CoolingPlaceRules, nAlternatives = 2): CoolingMatch {
  if (!needs.home) return { source: "fallback_nearest", best: null, alternatives: [], note: "No home location on file" };
  const wd = weekdayOf(date);
  const target = toMin(rules.arrive_before) - rules.arrival_buffer_min;
  const slow = needs.age >= 65 || needs.stepFreeNeeded;
  const speed = slow ? rules.walk_speed_mps.older_or_mobility.value : rules.walk_speed_mps.adult.value;
  const detour = rules.detour_factor.value;

  type Scored = CoolingPlaceOption & { _rank: number[] };
  const scored: Scored[] = [];
  for (const p of places) {
    if (!p.indoor || !rules.include_categories.includes(p.category)) continue;
    if (p.finderStatus === "CLOSED") continue;
    if (p.facilityType && rules.older_adult_only_facility_types.includes(p.facilityType) && needs.age < rules.older_adult_min_age) continue;
    if (needs.stepFreeNeeded && p.stepFree === "no") continue;
    const km = haversineKm(needs.home, p);
    if (km > rules.max_radius_km) continue;
    const h = hoursOn(p, wd);
    if (h === "closed") continue;
    const walkMin = (km * detour * 1000) / speed / 60;
    let travelMin = walkMin;
    let mode: CoolingPlaceOption["travelMode"] = "walk";
    if (walkMin > rules.max_walk_min) {
      travelMin = rules.naive_transit.wait_min + ((km * detour) / rules.naive_transit.speed_kmh) * 60;
      mode = "transit_naive";
    }
    const caveats: string[] = [];
    let openRank: number;
    if (h === null) {
      openRank = 2;
      caveats.push("Hours not listed: call ahead");
    } else if (h.open > target) continue; // doesn't open in time for a before-11 arrival
    else openRank = h.close >= toMin("17:00") ? 0 : 1;
    if (h && h.close < toMin("17:00")) caveats.push(`Closes at ${fmtMin(h.close)}, before the hottest hours end`);
    if (needs.stepFreeNeeded && p.stepFree === "unknown") caveats.push("Step-free entrance not confirmed: call ahead");
    if (p.membershipRequired) caveats.push(p.membershipRequired);
    if (needs.canReach === "no") caveats.push("Patient can't get there alone: arrange a ride or escort");
    else if (needs.canReach === "with_help") caveats.push("Patient needs help getting there");
    if (mode === "transit_naive") caveats.push("Travel time is a naive transit estimate (not routed)");
    const earliest = h ? Math.max(h.open, 0) : null;
    const leave = target - travelMin;
    scored.push({
      id: p.id,
      name: p.name,
      category: p.category,
      address: p.address,
      lat: p.lat,
      lon: p.lon,
      officialCoolingCenter: p.official,
      stepFree: p.stepFree,
      hoursToday: h ? h.text : null,
      opensMin: earliest,
      closesMin: h ? h.close : null,
      distanceKm: +km.toFixed(2),
      travelMin: Math.round(travelMin),
      travelMode: mode,
      leaveBy: fmtMin(Math.floor(leave / 5) * 5),
      arriveBy: rules.arrive_before,
      caveats,
      _rank: [openRank, needs.stepFreeNeeded ? (p.stepFree === "yes" ? 0 : 1) : 0, Math.round(travelMin / 5), p.official ? 0 : 1, travelMin],
    });
  }
  scored.sort((a, b) => {
    for (let i = 0; i < a._rank.length; i++) if (a._rank[i] !== b._rank[i]) return a._rank[i] - b._rank[i];
    return a.id.localeCompare(b.id);
  });
  const clean = (s: Scored): CoolingPlaceOption => {
    const { _rank, ...rest } = s;
    return rest;
  };
  const best = scored[0] ? clean(scored[0]) : null;
  return {
    source: "fallback_nearest",
    best,
    alternatives: scored.slice(1, 1 + nAlternatives).map(clean),
    note: best
      ? `Fallback match: straight-line distance × ${detour} detour at ${speed} m/s walking (${slow ? rules.walk_speed_mps.older_or_mobility.source : rules.walk_speed_mps.adult.source}); routed times replace this when cooling_match.csv exists`
      : `No open indoor cool place within ${rules.max_radius_km} km${needs.stepFreeNeeded ? " with a step-free entrance" : ""}: clinic to arrange`,
  };
}

/**
 * Adapter for the routing agent's cooling_match.csv (real walking times on the OSM network,
 * patient-specific pace, step-free filter; computed for a reference heat day). Hours are
 * re-checked for the scored day from the cooling-place file; places closed that day (or
 * opening too late for a before-11 arrival) are dropped. Returns null when nothing is left,
 * so the caller falls back to matchCoolingPlace().
 */
export function coolingFromRoutedRows(
  rows: Record<string, string>[],
  places: Map<string, CoolingPlace>,
  rules: CoolingPlaceRules,
  date?: string,
): CoolingMatch | null {
  if (!rows.length) return null;
  const get = (r: Record<string, string>, ks: string[]) => {
    for (const k of ks) if (r[k] !== undefined && r[k] !== "") return r[k];
    return undefined;
  };
  const target = toMin(rules.arrive_before) - rules.arrival_buffer_min;
  const wd = date ? weekdayOf(date) : null;
  const sorted = [...rows].sort((a, b) => Number(get(a, ["rank", "choice_rank"]) ?? 1) - Number(get(b, ["rank", "choice_rank"]) ?? 1));
  const opts: CoolingPlaceOption[] = [];
  let refDay = "";
  for (const r of sorted) {
    const pid = get(r, ["place_source_id", "place_id", "source_id", "cooling_place_id"]) ?? "";
    const pl = places.get(pid);
    refDay = get(r, ["ref_day"]) ?? refDay;
    const travel = Number(get(r, ["walk_min", "travel_min", "travel_time_min", "duration_min", "routed_travel_min"]) ?? NaN);
    if (!Number.isFinite(travel)) continue;
    let hoursToday = get(r, ["hours_ref_day_raw", "hours_today"]) ?? null;
    let opens: number | null = get(r, ["opens_ref_day"]) ? toMin(get(r, ["opens_ref_day"])!) : null;
    let closes: number | null = get(r, ["closes_ref_day"]) ? toMin(get(r, ["closes_ref_day"])!) : null;
    const caveats = (get(r, ["notes", "caveats", "note"]) ?? "").split(";").map((x) => x.trim()).filter(Boolean);
    if (pl && wd !== null) {
      const h = hoursOn(pl, wd);
      if (h === "closed") continue;
      if (h) {
        if (h.open > target) continue;
        hoursToday = h.text;
        opens = h.open;
        closes = h.close;
      } else {
        hoursToday = null;
        opens = closes = null;
        caveats.push("Hours not listed for this day: call ahead");
      }
    }
    if (closes !== null && closes < toMin("17:00")) caveats.push(`Closes at ${fmtMin(closes)}, before the hottest hours end`);
    const sf = (get(r, ["step_free_status", "step_free", "accessible", "wheelchair"]) ?? pl?.stepFree ?? "unknown").toLowerCase();
    opts.push({
      id: pid,
      name: get(r, ["place_name", "name"]) ?? pl?.name ?? pid,
      category: get(r, ["place_type", "category"]) ?? pl?.category ?? "",
      address: get(r, ["address"]) ? fmtAddress(get(r, ["address"])!, get(r, ["borough"]), get(r, ["zip"])) : pl?.address ?? null,
      lat: Number(get(r, ["place_lat", "lat"]) ?? pl?.lat ?? NaN),
      lon: Number(get(r, ["place_lon", "lon"]) ?? pl?.lon ?? NaN),
      officialCoolingCenter: (get(r, ["official_cooling_center"]) ?? String(pl?.official ?? false)) === "true",
      stepFree: sf.startsWith("y") ? "yes" : sf.startsWith("n") ? "no" : "unknown",
      hoursToday,
      opensMin: opens,
      closesMin: closes,
      distanceKm: Number(get(r, ["walk_dist_km", "distance_km", "network_km"]) ?? NaN),
      travelMin: Math.round(travel),
      travelMode: "routed",
      leaveBy: fmtMin(Math.floor((target - travel) / 5) * 5),
      arriveBy: rules.arrive_before,
      caveats: [...caveats, `Routed walk (${get(r, ["walk_pace"]) ?? "routed pace"}${get(r, ["routing_engine"]) ? `, ${get(r, ["routing_engine"])}` : ""})`],
    });
  }
  if (!opts.length) return null;
  return {
    source: "routing_agent",
    best: opts[0],
    alternatives: opts.slice(1, 3),
    note: `Routed walking times from cooling_match.csv (routing agent; reference day ${refDay || "n/a"}); hours re-checked for ${date ?? "the reference day"}; leave-by = ${rules.arrive_before} − ${rules.arrival_buffer_min} min buffer − walk`,
  };
}
