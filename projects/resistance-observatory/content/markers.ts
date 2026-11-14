/**
 * Marker content for the Learn tab. Swapping the demo marker is ONE edit:
 * change DEMO_MARKER_ID below.
 *
 * The demo marker, pfdhps-K540E, is transcribed from docs/MARKER-CONTENT.md.
 * It is the only marker with written content, so it is the only one here. To
 * add another, write its content in a doc first, then add an entry; do not
 * fill fields from memory.
 */
import type { Reviewable } from "./review";

/* ------------------------------------------------------------ diagrams --- */

export type LadderRung = {
  /** Named combination, as the literature uses it (docs/SCIENCE.md). */
  name: string;
  /** Alterations present at this rung, each with its gene. */
  alterations: { gene: string; codon: string; isNew: boolean }[];
  /** Effect on the drug. Science lead writes this. null = pending. */
  effect: string | null;
  /** The rung the page is about. Rendered with a text tag, not colour alone. */
  highlight?: boolean;
  /** Amino-acid change with a charge swap, drawn as two schematic residue
   *  glyphs under the rung. Only set where the charge actually changes. */
  residueChange?: {
    from: { letter: string; charge: "+" | "\u2212" };
    to: { letter: string; charge: "+" | "\u2212" };
    caption: string;
  };
};

export type LadderDiagram = {
  kind: "ladder";
  title: string;
  /** Lowest rung first (earlier rungs sit lower). */
  rungs: LadderRung[];
  /** Named combination spanning rungs (0-based, inclusive), drawn as a bracket. */
  bracket?: { from: number; to: number; lines: string[] };
  caption: string;
};

export type BeforeAfterDiagram = {
  kind: "before-after";
  title: string;
  /** Label for the protein element highlighted in both panels. */
  element: string;
  before: { heading: string; note: string };
  after: { heading: string; note: string };
  caption: string;
};

export type Diagram = LadderDiagram | BeforeAfterDiagram;

/* -------------------------------------------------------------- marker --- */

export type Marker = {
  id: string;
  organism: "Plasmodium falciparum";
  gene: string;
  /** Full name of the gene product, shown in the identity strip. */
  geneFullName?: string;
  alteration: string;
  /** The alteration in plain words. */
  alterationPlain?: string;
  /** The drug, named every time the marker is named. */
  drug: string;
  /** Clinical context for the drug, shown beside it. */
  drugNote?: string;
  /** Sourced classification chip. null = omit the chip entirely (LEARN.md). */
  classification: { label: string; source: string } | null;
  identity: Reviewable<true>;
  /** The one bolded sentence. */
  oneSentence: Reviewable<string>;
  /** Three headed paragraphs. */
  mechanism: Reviewable<[MechanismPara, MechanismPara, MechanismPara]>;
  /** The point to carry into the other tabs, shown above the mechanism. */
  keyPoint?: { heading: string; body: string };
  diagram: Reviewable<Diagram>;
  /**
   * OUR definition of where this marker lives in each source. This is the only
   * thing that connects the structure viewer to the graph findings: RCSB does
   * not reference the System graph and the graph does not reference PDB.
   */
  sources?: {
    /** Residue number of the marker in the PDB entries the viewer loads. */
    pdbResidue: number;
    /** System Public Graph variable ids whose name mentions this codon
     *  (data/graph-stats.json, marker.variables). */
    graphVariableIds: string[];
  };
  /** "What this doesn't tell you" bullets. Omitted = the page's default three. */
  limits?: [string, string, string];
};

export type MechanismPara = { heading: string; body: string };

/** The marker Learn shows when the URL carries none. ONE EDIT to swap.
 *  Confirmed as the demo marker. */
export const DEMO_MARKER_ID = "pfdhps-K540E";

/* pfdhps ladder for the demo marker — docs/MARKER-CONTENT.md, verbatim. */
const PFDHPS_LADDER: LadderDiagram = {
  kind: "ladder",
  title: "pfdhps changes and sulfadoxine",
  rungs: [
    {
      name: "A437G",
      alterations: [{ gene: "pfdhps", codon: "A437G", isNew: true }],
      effect: "usually the first change to appear",
    },
    {
      name: "K540E",
      alterations: [{ gene: "pfdhps", codon: "K540E", isNew: true }],
      effect: "with A437G forms the \u201cdouble mutant\u201d",
      highlight: true,
      residueChange: {
        from: { letter: "K", charge: "+" },
        to: { letter: "E", charge: "\u2212" },
        caption: "lysine (+) \u2192 glutamate (\u2212) at position 540",
      },
    },
    {
      name: "A581G",
      alterations: [{ gene: "pfdhps", codon: "A581G", isNew: true }],
      effect: "further reduction in sulfadoxine efficacy",
    },
  ],
  // docs/MARKER-CONTENT.md: K540E "rarely appears alone" and is usually
  // reported "alongside A437G as a double mutant".
  bracket: { from: 0, to: 1, lines: ["Double mutant", "A437G + K540E", "how K540E is", "usually reported"] },
  caption:
    "These changes accumulate in individual parasites. A region\u2019s position on this ladder can only be read from studies that genotyped the combination directly \u2014 never by adding up separate single-mutation results. Among these three, only K540E swaps the residue\u2019s charge.",
};

/** Signed off for display. */
const ok = <T,>(value: T): Reviewable<T> => ({ value, reviewed: true });

export const MARKERS: Record<string, Marker> = {
  "pfdhps-K540E": {
    id: "pfdhps-K540E",
    organism: "Plasmodium falciparum",
    gene: "pfdhps",
    geneFullName: "dihydropteroate synthase",
    alteration: "K540E",
    alterationPlain: "lysine replaced by glutamate at codon 540",
    drug: "sulfadoxine",
    drugNote: "used clinically with pyrimethamine, as SP",
    classification: null,
    identity: ok(true),
    oneSentence: ok(
      "Parasites carrying K540E in pfdhps are associated with reduced efficacy of sulfadoxine, one half of the SP combination used to prevent malaria in pregnancy and in seasonal chemoprevention.",
    ),
    mechanism: ok([
      {
        heading: "What the enzyme normally does",
        body: "Every cell needs folate to build DNA. Humans don\u2019t make it \u2014 we absorb it from food \u2014 but Plasmodium falciparum has to synthesize its own. Dihydropteroate synthase, DHPS, catalyses one step of that synthesis: it joins a small molecule called para-aminobenzoic acid, or pABA, onto a pterin backbone. Without that step the parasite runs out of folate, and without folate it cannot copy its DNA or divide. Because we don\u2019t share this pathway, it is an unusually clean drug target.",
      },
      {
        heading: "What the drug does",
        body: "Sulfadoxine is a sulfonamide, and sulfonamides are shaped like pABA. The drug slots into the DHPS active site where pABA is meant to go and competes for it. With the site occupied, the enzyme turns over far more slowly, folate synthesis stalls, and the parasite starves of the building blocks it needs to replicate. This is competitive inhibition: the effect depends on how tightly the drug binds relative to the natural substrate.",
      },
      {
        heading: "What the mutation changes",
        // Rewritten after measuring the deposited structures (PDB 6JWX, 6KCL):
        // residue 540 is about 9-11 \u00c5 from the nearest ligand in both, so the
        // earlier wording about weakening the enzyme's grip on the drug is not
        // supported by them. docs/MARKER-CONTENT.md still carries the old text.
        body: "K540E swaps a lysine for a glutamate at position 540 \u2014 a positively charged residue for a negatively charged one. In both deposited crystal structures that position sits roughly 9\u201311 \u00c5 from the bound ligand, so it is not in contact with it: these structures do not show a direct contact between residue 540 and what is bound. In practice K540E rarely appears alone. The literature reports it as part of a haplotype, usually alongside A437G as the double mutant, so it is used as a marker for that combination rather than being established as the direct cause of reduced binding.",
      },
    ]),
    keyPoint: {
      heading: "K540E rarely appears alone",
      body: "The literature usually reports it alongside A437G as a double mutant, with resistance increasing as further changes accumulate. So a finding about K540E is usually a finding about a combination that contains it. When another tab talks about a haplotype containing K540E, it is talking about this marker.",
    },
    diagram: ok(PFDHPS_LADDER),
    sources: {
      pdbResidue: 540,
      graphVariableIds: [
        "4PX5Wm7Ytz",
        "5bJrK_wJcx",
        "6nc-md3xWP",
        "bkHgD5M-T3",
        "r04Uj8fH3c",
        "TaKS18jKT6",
        "zFQpDYEjPr",
        "w1ktrLk4Wc",
      ],
    },
    limits: [
      "Carrying this marker is not the same as a patient\u2019s treatment failing. Outcome depends on the drug, the rest of the parasite\u2019s genetic background, and the clinical setting.",
      "A marker not appearing in the evidence here does not mean it is absent in the world. It may mean nobody has published on it, or that the extraction missed it.",
      "Nothing here is clinical guidance. It describes published research, not treatment decisions.",
    ],
  },
};

/** Unknown ids fall back to the demo marker; Learn shows a visible notice when
 *  that happens. The key "pfdhps-K540E" is shared with other tabs — keep it exact. */
export function getMarker(id: string | null | undefined): Marker {
  return (id && MARKERS[id]) || MARKERS[DEMO_MARKER_ID];
}
