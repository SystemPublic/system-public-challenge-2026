import { test } from "node:test";
import assert from "node:assert/strict";
import type { TrustedContact } from "../../types/patient.ts";
import type { TravelLookup } from "../escalation.ts";
import { checkinSchedule, escalationPlan, timeBudget } from "../escalation.ts";
import { config, q } from "./helpers.ts";

const contact = (id: string, rel = "neighbor"): TrustedContact => ({ id, patientId: "P", priority: 1, givenName: "A", familyName: "B", relationship: rel, home: null });
const cfg = config();
const plan = (over: Partial<Parameters<typeof escalationPlan>[0]> = {}) =>
  escalationPlan({ age: 70, q: q(), contacts: [], readiness: "high", heatriskToday: 2, travel: new Map(), rules: cfg.escalation, finalStep: cfg.contacts.final_step, buddyProgram: cfg.contacts.buddy_program, ...over });

test("time budget by readiness, tightened on red/magenta days and hot no-AC homes", () => {
  const r = cfg.escalation;
  assert.equal(timeBudget("medium", 1, q(), r).tMax, r.t_max_min.medium);
  assert.equal(timeBudget("high", 2, q(), r).tMax, r.t_max_min.high);
  assert.equal(timeBudget("medium", 3, q(), r).tMax, r.t_max_min.very_high);
  assert.equal(timeBudget("medium", 1, q({ workingAc: "no", homeGetsHot: "often" }), r).tMax, r.t_max_min.very_high);
});

test("contact eligibility: T_travel ≤ T_max − p90(patient) − p90(contact); fastest first", () => {
  const travel: TravelLookup = new Map([
    ["c1", { minutes: 25, mode: "walk", source: "routed" }],
    ["c2", { minutes: 4, mode: "walk", source: "routed" }],
    ["c3", { minutes: 200, mode: "drive", source: "routed" }],
  ]);
  const p = plan({ contacts: [contact("c1"), contact("c2"), contact("c3")], travel });
  const allowed = cfg.escalation.t_max_min.high - cfg.escalation.response_p90_min.patient_app_or_sms.value - cfg.escalation.response_p90_min.contact.value;
  assert.equal(p.allowedTravelMin, allowed);
  assert.equal(p.tWaitMin + p.tContactMin + p.allowedTravelMin, p.tMaxMin);
  assert.equal(p.firstContactId, "c2");
  assert.deepEqual(p.contacts.map((c) => c.eligible), [25 <= allowed, true, false]);
  assert.equal(p.resendAtMin, Math.round(p.tWaitMin / 2));
  assert.equal(p.steps[0].atMin, 0);
  assert.equal(p.steps[1].atMin, p.resendAtMin);
  assert.equal(p.steps[2].to, "c2");
  assert.equal(p.steps.at(-1)!.atMin, p.tMaxMin);
  assert.match(p.steps.at(-1)!.action, /human/i);
});

test("no qualifying contact → clinic call list at T_wait, buddy offer, priority list", () => {
  const p = plan({ contacts: [contact("c1")], travel: new Map([["c1", { minutes: 90, mode: "transit", source: "naive_placeholder" }]]) });
  assert.equal(p.noQualifyingContact, true);
  assert.equal(p.firstContactId, null);
  assert.match(p.fallback!, /buddy/);
  assert.equal(p.steps[2].to, "clinic");
  assert.ok(p.assumptions.some((a) => /NAIVE/.test(a)));
});

test("voice-call patients get a longer wait", () => {
  assert.ok(plan({ q: q({ alertChannel: "voice_call" }) }).tWaitMin > plan().tWaitMin);
});

test("opted-out or low readiness → not enrolled", () => {
  assert.equal(plan({ q: q({ alertOptIn: false }) }).enrolled, false);
  assert.equal(plan({ readiness: "low" }).enrolled, false);
});

test("check-ins densify for very high readiness on red days; worst case = longest gap + T_max", () => {
  const base = checkinSchedule(q(), "very_high", 2, cfg.escalation);
  assert.deepEqual(base.times, ["10:00", "16:00"]);
  assert.equal(base.longestGapMin, 360);
  const dense = checkinSchedule(q(), "very_high", 3, cfg.escalation);
  assert.deepEqual(dense.times, ["10:00", "14:00", "16:00", "18:00"]);
  assert.ok(dense.longestGapMin < base.longestGapMin);
  const p = plan({ readiness: "very_high", heatriskToday: 3 });
  assert.equal(p.worstCaseUnnoticedMin, p.longestGapMin + p.tMaxMin);
});
