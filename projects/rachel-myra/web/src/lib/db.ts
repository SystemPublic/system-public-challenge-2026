// Live demo state in local SQLite, via Node's built-in driver (node:sqlite).
// No native build step (better-sqlite3 needs node-gyp on Windows).
//
// Server-only: import from route handlers / server code, never from client components.
// Static patient data stays in data/processed/synthetic (lib/patient); see db/schema.sql.

import { DatabaseSync } from "node:sqlite";
import fs from "node:fs";
import path from "node:path";
import { REPO_ROOT } from "@/lib/kb";

const DB_DIR = path.join(REPO_ROOT, "db");
const DB_FILE = process.env.DB_FILE ?? path.join(DB_DIR, "heat.sqlite");

// One connection, reused across dev hot reloads.
const g = globalThis as unknown as { __heatDb?: DatabaseSync };

export function db(): DatabaseSync {
  if (!g.__heatDb) {
    fs.mkdirSync(DB_DIR, { recursive: true });
    const conn = new DatabaseSync(DB_FILE);
    conn.exec("PRAGMA journal_mode = WAL;");
    conn.exec(fs.readFileSync(path.join(DB_DIR, "schema.sql"), "utf8"));
    g.__heatDb = conn;
  }
  return g.__heatDb;
}

/** Demo time = real time + fast-forward offset. Store this, not Date.now(). */
export function demoNow(): Date {
  const row = db().prepare("SELECT offset_minutes FROM demo_clock WHERE id = 1").get() as
    | { offset_minutes: number }
    | undefined;
  return new Date(Date.now() + (row?.offset_minutes ?? 0) * 60_000);
}

/** Fast-forward the demo clock (e.g. +45 to play a 45-minute escalation wait). */
export function fastForward(minutes: number): Date {
  db().prepare("UPDATE demo_clock SET offset_minutes = offset_minutes + ? WHERE id = 1").run(minutes);
  return demoNow();
}

/** Wipe live state for a fresh demo run (keeps the schema). */
export function resetDemo(): void {
  db().exec(`
    DELETE FROM messages; DELETE FROM checkins; DELETE FROM alerts;
    DELETE FROM questionnaire_responses;
    UPDATE demo_clock SET offset_minutes = 0 WHERE id = 1;
  `);
}
