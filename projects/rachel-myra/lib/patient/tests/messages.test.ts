import { test } from "node:test";
import assert from "node:assert/strict";
import type { MedicationOrder } from "../../types/patient.ts";
import { provisionalIndex } from "../drug-profiles.ts";
import { medRiskStack } from "../med-risk.ts";
import type { MessageContext } from "../messages.ts";
import { CLOSING, checkMessageSafety, contactCheckText, coolingPlaceText, fluidRule, heatCard, safetyAlert } from "../messages.ts";
import { q } from "./helpers.ts";

const idx = provisionalIndex();
const meds = (...names: string[]): MedicationOrder[] => names.map((g, i) => ({ id: `m${i}`, generic: g, status: "active" }));
const ctx = (names: string[], over: Partial<MessageContext> = {}): MessageContext => {
  const m = meds(...names);
  return { patientName: "Test", age: 60, language: "en", supportedLanguages: ["en", "es"], fallbackLanguage: "en", q: q(), med: medRiskStack(m, idx), meds: m, idx, heatriskToday: 3, cooling: null, ...over };
};

test("safety alert names the headline drugs (lithium first) and ends with the closing line", () => {
  const m = safetyAlert(ctx(["hydrochlorothiazide", "lithium"]));
  assert.match(m.text, /^Heat danger today\. Your lithium and water pill \(hydrochlorothiazide\) make heat riskier\./);
  assert.ok(m.text.endsWith(CLOSING.en));
  assert.deepEqual(checkMessageSafety(m), []);
});

test("fluid-restricted patients never get blanket 'drink more water'", () => {
  const c = ctx(["furosemide"], { q: q({ fluidRestricted: true }) });
  for (const m of [safetyAlert(c), heatCard(c)]) {
    assert.doesNotMatch(m.text, /Drink water regularly/);
    assert.match(m.text, /fluid limit your care team set/);
  }
  assert.equal(fluidRule(ctx(["hydrochlorothiazide", "sertraline"])).id, "low_sodium_risk");
  assert.equal(fluidRule(ctx(["furosemide"])).id, "ask_fluid_plan");
  assert.equal(fluidRule(ctx(["amlodipine"], { conditionKeys: ["heart_failure"] })).id, "ask_fluid_plan");
  assert.equal(fluidRule(ctx(["amlodipine"])).id, "default_hydrate");
});

test("child → parent/caregiver wording; adult with caregiver respondent → 'person you care for'", () => {
  const kid = heatCard(ctx(["topiramate"], { age: 9, q: q({ respondent: "parent_or_caregiver" }) }));
  assert.equal(kid.audience, "caregiver");
  assert.match(kid.text, /your child's topiramate/);
  const adult = safetyAlert(ctx(["oxybutynin"], { age: 81, q: q({ respondent: "parent_or_caregiver" }) }));
  assert.match(adult.text, /person you care for/);
  assert.doesNotMatch(adult.text, /child/);
});

test("Spanish when preferred and supported; other languages fall back to English + interpreter flag", () => {
  const es = safetyAlert(ctx(["lithium", "hydrochlorothiazide"], { q: q({ preferredLanguage: "es" }) }));
  assert.equal(es.language, "es");
  assert.match(es.text, /^Peligro por calor hoy/);
  assert.ok(es.text.endsWith(CLOSING.es));
  const bn = safetyAlert(ctx(["lithium"], { q: q({ preferredLanguage: "bn" }) }));
  assert.equal(bn.language, "en");
  assert.equal(bn.needsTranslation, true);
});

test("cooling text includes place, leave-by and 'before 11 AM'", () => {
  const m = coolingPlaceText(
    ctx(["lithium"], {
      cooling: { id: "x", name: "Belmont Library", category: "library", address: "610 E 186 St, Bronx 10458", lat: 0, lon: 0, officialCoolingCenter: true, stepFree: "yes", hoursToday: "10a-6p", opensMin: 600, closesMin: 1080, distanceKm: 0.5, travelMin: 8, travelMode: "routed", leaveBy: "10:35", arriveBy: "11:00", caveats: [] },
    }),
  )!;
  assert.match(m.text, /Belmont Library/);
  assert.match(m.text, /Leave by 10:35 to get there before 11 AM/);
  assert.match(m.text, /8 min walk/);
});

test("contact message carries the checklist and ends at a human / 911 instruction, no water sips if fluid-restricted", () => {
  const m = contactCheckText("Ana", "en", ["en", "es"], true);
  assert.match(m.text, /Look for: confusion, hot dry skin/);
  assert.match(m.text, /call 911/);
  assert.doesNotMatch(m.text, /sips of water/);
  assert.match(contactCheckText("Ana", "en", ["en", "es"], false).text, /sips of water/);
});

test("guardrail checker catches stop-taking, dose numbers and a missing closing line", () => {
  const mk = (text: string) => ({ text, language: "en", audience: "patient" as const });
  assert.ok(checkMessageSafety(mk(`Stop taking lithium. ${CLOSING.en}`)).length);
  assert.ok(checkMessageSafety(mk(`Take 300 mg. ${CLOSING.en}`)).length);
  assert.ok(checkMessageSafety(mk(`Lower your dose. ${CLOSING.en}`)).length);
  assert.ok(checkMessageSafety({ text: `Deje de tomar el litio. ${CLOSING.es}`, language: "es", audience: "patient" }).length);
  assert.deepEqual(checkMessageSafety(mk("Stay cool.")), ["missing closing line"]);
  assert.deepEqual(checkMessageSafety(mk(`Stay cool. ${CLOSING.en}`)), []);
});
