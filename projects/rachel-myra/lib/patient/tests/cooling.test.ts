import { test } from "node:test";
import assert from "node:assert/strict";
import type { CoolingPlace } from "../cooling.ts";
import { coolingFromRoutedRows, hoursOn, matchCoolingPlace, parseClock, weekdayOf } from "../cooling.ts";
import { config } from "./helpers.ts";

const rules = config().data_sources.cooling_places;
const home = { lat: 40.84, lon: -73.89 };
const place = (over: Partial<CoolingPlace>): CoolingPlace => ({
  id: "p",
  name: "Place",
  category: "library",
  indoor: true,
  address: "1 Main St",
  lat: 40.842,
  lon: -73.89,
  official: false,
  finderStatus: null,
  stepFree: "yes",
  hours: null,
  openingHours: "Mo-Su 09:00-18:00",
  facilityType: null,
  membershipRequired: null,
  ...over,
});

test("parseClock handles both hour formats", () => {
  assert.equal(parseClock("9a"), 540);
  assert.equal(parseClock("8:30a"), 510);
  assert.equal(parseClock("12p"), 720);
  assert.equal(parseClock("12a", true), 1440);
  assert.equal(parseClock("10:00"), 600);
  assert.equal(parseClock("noonish"), null);
});

test("hoursOn: Cool Options day map, OSM opening_hours, closed days", () => {
  const cc = { hours: { Monday: "9a-5p", Tuesday: "CLOSED" }, openingHours: null };
  assert.deepEqual(hoursOn(cc, 1), { open: 540, close: 1020, text: "9a-5p" });
  assert.equal(hoursOn(cc, 2), "closed");
  assert.equal(hoursOn(cc, 3), "closed"); // day missing from the map
  const osm = { hours: null, openingHours: "Mo,We,Fr 10:00-18:00; Tu 13:00-20:00; Sa 10:00-17:00; Su off" };
  assert.deepEqual(hoursOn(osm, 3), { open: 600, close: 1080, text: "We 10:00-18:00" });
  assert.equal((hoursOn(osm, 2) as { open: number }).open, 780);
  assert.equal(hoursOn(osm, 0), "closed");
  assert.equal(hoursOn(osm, 4), "closed"); // Thursday not listed
  assert.equal(hoursOn({ hours: null, openingHours: null }, 1), null);
  assert.equal(hoursOn({ hours: null, openingHours: "Mo-Fr 10:00-13:00,14:00-18:00" }, 1)!.toString(), "[object Object]");
});

test("weekdayOf", () => {
  assert.equal(weekdayOf("2025-06-24"), 2); // Tuesday
  assert.equal(weekdayOf("2026-11-14"), 6); // Saturday
});

test("matcher: nearest open place, step-free if needed, leave-by before 11", () => {
  const near = place({ id: "near", lat: 40.8405, stepFree: "no" });
  const ok = place({ id: "ok", lat: 40.845, stepFree: "yes" });
  const late = place({ id: "late", lat: 40.8401, openingHours: "Mo-Su 12:00-20:00" });
  const closed = place({ id: "closed", lat: 40.8402, finderStatus: "CLOSED" });
  const outdoor = place({ id: "pool", lat: 40.8403, category: "pool", indoor: false });
  const all = [near, ok, late, closed, outdoor];

  const m1 = matchCoolingPlace({ home, age: 40, stepFreeNeeded: false, canReach: "yes" }, all, "2025-06-24", rules);
  assert.equal(m1.best!.id, "near");
  const m2 = matchCoolingPlace({ home, age: 80, stepFreeNeeded: true, canReach: "with_help" }, all, "2025-06-24", rules);
  assert.equal(m2.best!.id, "ok");
  assert.ok(m2.best!.caveats.some((c) => /help/.test(c)));
  const target = 11 * 60 - rules.arrival_buffer_min;
  const [h, mm] = m2.best!.leaveBy!.split(":").map(Number);
  assert.ok(h * 60 + mm + m2.best!.travelMin <= target);
  assert.ok(!m1.alternatives.concat(m1.best!).some((o) => ["late", "closed", "pool"].includes(o.id)));
});

test("matcher respects older-adult-only centers", () => {
  const oac = place({ id: "oac", facilityType: "Older Adult Center", category: "cooling center" });
  assert.equal(matchCoolingPlace({ home, age: 30, stepFreeNeeded: false, canReach: "yes" }, [oac], "2025-06-24", rules).best, null);
  assert.equal(matchCoolingPlace({ home, age: 70, stepFreeNeeded: false, canReach: "yes" }, [oac], "2025-06-24", rules).best!.id, "oac");
});

test("routed rows: hours re-checked for the scored day; closed places dropped", () => {
  const places = new Map([
    ["A", place({ id: "A", hours: { Monday: "9a-5p" }, openingHours: null })],
    ["B", place({ id: "B", hours: { Monday: "9a-5p", Tuesday: "9a-5p" }, openingHours: null })],
  ]);
  const rows = [
    { patient_id: "P", rank: "1", place_source_id: "A", place_name: "A", walk_min: "6", step_free_status: "yes" },
    { patient_id: "P", rank: "2", place_source_id: "B", place_name: "B", walk_min: "12", step_free_status: "yes" },
  ];
  const mon = coolingFromRoutedRows(rows, places, rules, "2025-06-23")!;
  assert.equal(mon.best!.id, "A");
  const tue = coolingFromRoutedRows(rows, places, rules, "2025-06-24")!;
  assert.equal(tue.best!.id, "B");
  assert.equal(tue.best!.travelMode, "routed");
  assert.equal(coolingFromRoutedRows(rows.slice(0, 1), places, rules, "2025-06-24"), null); // → caller falls back
});
