/**
 * Data tab content. Same discipline as Learn:
 * - Biology comes only from docs/SCIENCE.md, word for word where possible, and
 *   is released for display (`reviewed: true`).
 * - Project method / data-source facts come from CLAUDE.md and render.
 * - Every number comes from lib/stats.ts, which reads the pinned graph pull.
 * - There is no history narrative: docs/SCIENCE.md holds no sourced text for
 *   one, so the page does not have that section.
 */
import type { Reviewable } from "./review";

const released = <T,>(value: T): Reviewable<T> => ({ value, reviewed: true });

/* ------------------------------------------------------------- biology --- */

/** docs/SCIENCE.md "The one-paragraph version", split for typesetting. */
export const ONE_PARAGRAPH = released([
  "Malaria is caused by Plasmodium parasites, most dangerously P. falciparum.",
  "Specific mutations in parasite genes reduce how well particular drugs work. Those mutations are tracked as resistance markers.",
  "New findings about them are published continuously, across a large and scattered literature.",
]);

/** docs/SCIENCE.md "Candidate markers" table. */
export const CANDIDATE_MARKERS = released([
  { gene: "pfdhps", alterations: "A437G, K540E, A581G", drug: "sulfadoxine (with pyrimethamine, as SP)" },
  { gene: "pfdhfr", alterations: "S108N, N51I, C59R, I164L", drug: "pyrimethamine (as SP)" },
  { gene: "pfcrt", alterations: "K76T", drug: "chloroquine" },
  { gene: "pfmdr1", alterations: "N86Y, Y184F, D1246Y", drug: "partner drugs; direction varies" },
  { gene: "kelch13 / K13", alterations: "C580Y, R561H, P441L, A675V", drug: "artemisinin partial resistance" },
]);

/** docs/SCIENCE.md antifolate paragraph. */
export const ANTIFOLATE = released({
  body:
    "Antifolate (dhfr/dhps) resistance accumulates in a roughly known order, and the literature uses named combinations: the triple mutant (dhfr N51I + C59R + S108N), the quintuple (the dhfr triple plus dhps A437G + K540E), and the sextuple (the quintuple plus dhps A581G).",
  constraint:
    "A combination is a property of an individual parasite. It is never inferred from separate single-mutation findings in different papers.",
});

/* -------------------------------------------------------------- glossary --- */
/* From docs/SCIENCE.md "Vocabulary for the pitch". */

export type GlossaryEntry = { term: string; definition: string; reviewed: boolean };

export const GLOSSARY: GlossaryEntry[] = [
  {
    term: "Association",
    definition:
      "The evidence graph's atomic unit: two variables linked by a statistic. This, not prevalence, is what the alerts are built on.",
    reviewed: true,
  },
  {
    term: "Divergence",
    definition:
      "A new finding pointing the opposite way from prior findings on the same variable pair and statistic type. We flag it; we do not judge which finding is right.",
    reviewed: true,
  },
  {
    term: "Marker",
    definition: "A mutation tracked as a resistance signal. Always named together with its drug.",
    reviewed: true,
  },
  {
    term: "Partial resistance",
    definition:
      "The correct term for artemisinin. Slowed clearance, not outright treatment failure.",
    reviewed: true,
  },
  {
    term: "Replay",
    definition:
      "Playing real publication history forward, in the order findings were actually published, to test the matcher. The feed is a frozen snapshot, not live surveillance.",
    reviewed: true,
  },
  {
    term: "Snapshot",
    definition:
      "A frozen copy of the evidence graph taken on one date. Nothing published after that date is in it.",
    reviewed: true,
  },
];
