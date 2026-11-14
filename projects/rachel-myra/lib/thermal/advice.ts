// Advice from a product-temperature trace: port of scripts/thermal_sim/advice.py.
// Three tiers only (the honesty rule). Never returns a potency percentage.

import { PARAMS } from "./params.ts";
import { mktC } from "./metrics.ts";

export type Tier = "use_as_normal" | "check_with_pharmacist" | "request_replacement";
export const TIER_RANK: Record<Tier, number> = { use_as_normal: 0, check_with_pharmacist: 1, request_replacement: 2 };
export const ACTION: Record<Tier, string> = {
  use_as_normal: "Use as normal",
  check_with_pharmacist: "Check with your pharmacist",
  request_replacement: "Request a replacement",
};
const HARM = new Set(["loss", "device_failure", "measurement_error"]);

export type Evidence = {
  id: string;
  finding: string;
  exposure: { temp_c: number | null; hours: number | null; mode: string } | null;
  outcome: string;
  used_in_rule: boolean;
  citation?: { text?: string; pmid?: string | null; doi?: string | null; url?: string; status?: string };
};

export type DrugProfile = {
  id: string;
  name: string;
  shipped_cold?: boolean;
  dispense_temp_c: number;
  mkt_delta_h_kj_mol?: number;
  label: { min_c: number; max_c: number; spike: { max_c: number; max_hours: number } | null; hard_max_c: number | null; summary?: string };
  evidence: Evidence[];
  caveats?: string[];
  advice_text: Record<Tier, string>;
};

export type Assessment = {
  tier: Tier;
  action: string;
  message: string;
  reasons: string[];
  matched_evidence: string | null;
  exposure: { peak_c: number; min_c: number; hours_above_label_max: number; mkt_c: number };
};

const fOfC = (c: number) => (c * 9) / 5 + 32;

function cite(ev: Evidence): string {
  const c = ev.citation ?? {};
  const ident = c.pmid ? `PMID ${c.pmid}` : c.doi ? `DOI ${c.doi}` : c.url ?? "";
  return `${c.text ?? ""} (${ident}; ${c.status ?? ""})`;
}

export function assess(tempsC: number[], profile: DrugProfile, dtS: number = PARAMS.num.dt_s): Assessment {
  const body = tempsC.length > 1 ? tempsC.slice(1) : tempsC;
  const peak = Math.max(...tempsC);
  const low = Math.min(...tempsC);
  const lab = profile.label;
  const hoursAbove = (thr: number) => (body.filter((x) => x > thr).length * dtS) / 3600;
  const hoursAtOrAbove = (thr: number) => (body.filter((x) => x >= thr).length * dtS) / 3600;
  const hAbove = hoursAbove(lab.max_c);
  const reasons: string[] = [];
  let matched: string | null = null;
  const highBreach = peak > lab.max_c;
  const spikeOk = highBreach && !!lab.spike && peak <= lab.spike.max_c && hAbove <= lab.spike.max_hours;
  const lowBreach = low < lab.min_c;
  let tier: Tier;

  if (!lowBreach && (!highBreach || spikeOk)) {
    tier = "use_as_normal";
    if (spikeOk && lab.spike) {
      reasons.push(`Peaked at ${peak.toFixed(1)} C (${fOfC(peak).toFixed(0)} F), above ${lab.max_c.toFixed(0)} C for ${(hAbove * 60).toFixed(0)} min: inside the label's allowed short spike (up to ${lab.spike.max_c.toFixed(0)} C for up to ${lab.spike.max_hours.toFixed(0)} h).`);
    } else {
      reasons.push(`Stayed between ${low.toFixed(1)} and ${peak.toFixed(1)} C, inside the labeled ${lab.min_c.toFixed(0)}-${lab.max_c.toFixed(0)} C range.`);
    }
  } else {
    tier = "request_replacement";
    if (lowBreach) reasons.push(`Fell to ${low.toFixed(1)} C, below the label minimum of ${lab.min_c.toFixed(0)} C; no study in our evidence base tested this.`);
    if (highBreach) {
      reasons.push(`Peaked at ${peak.toFixed(1)} C (${fOfC(peak).toFixed(0)} F) and spent ${(hAbove * 60).toFixed(0)} min above the label maximum of ${lab.max_c.toFixed(0)} C.`);
      if (lab.hard_max_c != null && peak > lab.hard_max_c) reasons.push(`Exceeded the label's hard limit of ${lab.hard_max_c.toFixed(0)} C.`);
      let harm: Evidence | null = null;
      for (const ev of profile.evidence ?? []) {
        const ex = ev.exposure;
        if (!ev.used_in_rule || !HARM.has(ev.outcome) || !ex || ex.temp_c == null || ex.hours == null) continue;
        if (peak >= ex.temp_c && hoursAtOrAbove(ex.temp_c) >= ex.hours) { harm = ev; break; }
      }
      if (harm && harm.exposure) {
        matched = harm.id;
        reasons.push(`Reached at least ${harm.exposure.temp_c!.toFixed(0)} C for at least ${(harm.exposure.hours! * 60).toFixed(0)} min, where a study found problems: ${cite(harm)}.`);
      } else if (!lowBreach && (lab.hard_max_c == null || peak <= lab.hard_max_c)) {
        for (const ev of profile.evidence ?? []) {
          const ex = ev.exposure;
          if (!ev.used_in_rule || ev.outcome !== "no_meaningful_change" || !ex) continue;
          if (ex.mode !== "constant" || ex.temp_c == null || ex.hours == null) continue;
          if (ex.temp_c <= lab.max_c) continue;
          if (peak <= ex.temp_c && hAbove <= ex.hours) {
            tier = "check_with_pharmacist";
            matched = ev.id;
            reasons.push(`Within what a study tested: held at ${ex.temp_c.toFixed(0)} C for ${(ex.hours / 24).toFixed(0)} days without a meaningful loss - ${cite(ev)}.`);
            break;
          }
        }
        if (tier === "request_replacement") reasons.push("Beyond what any study in our evidence base tested for this product.");
      }
    }
    for (const cav of profile.caveats ?? []) reasons.push("Caveat: " + cav);
  }
  return {
    tier,
    action: ACTION[tier],
    message: profile.advice_text[tier],
    reasons,
    matched_evidence: matched,
    exposure: { peak_c: peak, min_c: low, hours_above_label_max: hAbove, mkt_c: mktC(body, profile.mkt_delta_h_kj_mol) },
  };
}
