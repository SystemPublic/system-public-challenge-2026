/**
 * The Forecast map contract. `data/alerts.json` holds the Alert tab's default
 * alerts for every country (each region's default rule, genome counts only),
 * generated from k540e-data-pack/ by `node lib/alert/generate-map-alerts.mts`.
 *
 * Link an alert back to its inspector with `/alert?alert=<id>`.
 */
import alerts from "@/data/alerts.json";
import type { Trigger } from "./derive";

export type MapAlert = {
  id: string;
  /** Shared URL marker id, e.g. "pfdhps-K540E". */
  marker_id: string;
  country_iso3: string;
  /** Collection year of the genome cell that fired. */
  year: number;
  /** "band_change" | "first_detection" | "change" */
  rule: string;
  headline: string;
};

export function getDefaultMapAlerts(): MapAlert[] {
  return alerts as MapAlert[];
}

/** Which watch trigger produces a given rule, so `?alert=<id>` can rebuild the watch. */
export const RULE_TRIGGER: Record<string, Trigger> = {
  band_change: "who_band",
  first_detection: "first_detection",
  change: "change",
};

/** The Alert tab's own event id for a map alert. */
export const eventIdFor = (a: MapAlert) => `g:${a.country_iso3}:${a.year}:${a.rule}`;
