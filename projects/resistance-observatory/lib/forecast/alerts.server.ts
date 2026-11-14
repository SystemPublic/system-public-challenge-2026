/**
 * Server-only loader for the Alert tab's output. Import from a server component only.
 * Real file: data/alerts.json (array or { alerts: [...] }). Fallback: the badged placeholder.
 */
import fs from "node:fs";
import path from "node:path";
import type { AlertFeed, AlertRecord } from "./types";

const MARKER_ID = "pfdhps-K540E";

function isAlert(x: unknown): x is AlertRecord {
  if (!x || typeof x !== "object") return false;
  const a = x as Record<string, unknown>;
  return (
    typeof a.id === "string" &&
    a.id.length > 0 &&
    a.marker_id === MARKER_ID &&
    typeof a.country_iso3 === "string" &&
    /^[A-Z]{3}$/.test(a.country_iso3) &&
    typeof a.year === "number" &&
    Number.isInteger(a.year) &&
    typeof a.rule === "string" &&
    typeof a.headline === "string"
  );
}

function readJson(file: string): unknown {
  return JSON.parse(fs.readFileSync(file, "utf8"));
}

export function loadAlertFeed(): AlertFeed {
  const real = path.join(process.cwd(), "data", "alerts.json");
  if (fs.existsSync(real)) {
    try {
      const parsed = readJson(real);
      const list = Array.isArray(parsed)
        ? parsed
        : parsed && typeof parsed === "object" && Array.isArray((parsed as { alerts?: unknown }).alerts)
          ? (parsed as { alerts: unknown[] }).alerts
          : null;
      if (list === null) {
        console.warn("[forecast] data/alerts.json is not an array or { alerts: [...] }; showing no alerts.");
        return { alerts: [], placeholder: false };
      }
      return { alerts: list.filter(isAlert), placeholder: false };
    } catch (err) {
      console.warn("[forecast] could not parse data/alerts.json; showing no alerts.", err);
      return { alerts: [], placeholder: false };
    }
  }
  try {
    const ph = readJson(path.join(process.cwd(), "data", "forecast", "alerts.placeholder.json"));
    const list = Array.isArray(ph) ? ph.filter(isAlert) : [];
    return { alerts: list, placeholder: true };
  } catch (err) {
    console.warn("[forecast] could not read the placeholder alerts file.", err);
    return { alerts: [], placeholder: true };
  }
}
