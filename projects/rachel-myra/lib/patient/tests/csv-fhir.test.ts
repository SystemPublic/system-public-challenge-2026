import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { parseCsv } from "../csv.ts";
import { ageOn, conditionKey, patientsFromFhirBundle } from "../fhir.ts";
import { ROOT } from "./helpers.ts";

test("parseCsv handles quotes, embedded commas and newlines", () => {
  const rows = parseCsv('a,b,c\n1,"x, y","he said ""hi"""\n2,"multi\nline",\n');
  assert.equal(rows.length, 2);
  assert.equal(rows[0].b, "x, y");
  assert.equal(rows[0].c, 'he said "hi"');
  assert.equal(rows[1].b, "multi\nline");
  assert.equal(rows[1].c, "");
});

test("conditionKey maps ICD-10 prefixes", () => {
  assert.equal(conditionKey("Heart failure, unspecified", "I50.9"), "heart_failure");
  assert.equal(conditionKey("chronic kidney disease", "N18.3"), "ckd");
  assert.equal(conditionKey("overactive bladder"), "overactive_bladder");
});

test("ageOn counts birthdays correctly", () => {
  assert.equal(ageOn("1948-08-27", "2026-11-14"), 78);
  assert.equal(ageOn("1948-08-27", "2026-08-26"), 77);
});

test("FHIR bundle → 300 synthetic PatientRecords with meds, contacts and answers", () => {
  const bundle = JSON.parse(readFileSync(join(ROOT, "data/processed/synthetic/patients_fhir.json"), "utf8"));
  const ps = patientsFromFhirBundle(bundle);
  assert.equal(ps.length, 300);
  assert.ok(ps.every((p) => p.synthetic));
  const s01 = ps.find((p) => p.id === "S01")!;
  assert.equal(s01.zip, "10457");
  assert.equal(s01.language, "es");
  assert.deepEqual(s01.medications.map((m) => m.generic).sort(), ["furosemide", "lisinopril", "metoprolol", "oxybutynin"]);
  assert.ok(s01.conditions.some((c) => c.key === "heart_failure"));
  assert.equal(s01.contacts.length, 1);
  assert.equal(s01.questionnaire?.workingAc, "no");
  assert.equal(s01.questionnaire?.livesAlone, true);
  assert.equal(s01.questionnaire?.floor, 6);
  assert.deepEqual(s01.questionnaire?.checkinTimes, ["10:00", "14:00", "16:00", "18:00"]);
  const meds = ps.reduce((n, p) => n + p.medications.length, 0);
  assert.equal(meds, 952);
});
