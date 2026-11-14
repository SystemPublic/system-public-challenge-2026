# Learn content — pfdhps K540E

Draft for `content/markers.ts`. **Science lead must skim before `reviewed: true`.**
Every claim below is standard textbook biochemistry of the folate pathway, but
it has not been checked against a source by a human yet.

---

## Identity

- species: `Plasmodium falciparum`
- gene: `pfdhps`
- geneFullName: `dihydropteroate synthase`
- alteration: `K540E`
- alterationPlain: `lysine replaced by glutamate at codon 540`
- drug: `sulfadoxine` (used clinically with pyrimethamine, as SP)

## One-sentence answer

> **Parasites carrying K540E in pfdhps are associated with reduced efficacy of
> sulfadoxine, one half of the SP combination used to prevent malaria in
> pregnancy and in seasonal chemoprevention.**

## Mechanism — three paragraphs

**1. What the enzyme normally does.**
Every cell needs folate to build DNA. Humans don't make it — we absorb it from
food — but *Plasmodium falciparum* has to synthesize its own. Dihydropteroate
synthase, DHPS, catalyses one step of that synthesis: it joins a small molecule
called para-aminobenzoic acid, or pABA, onto a pterin backbone. Without that
step the parasite runs out of folate, and without folate it cannot copy its DNA
or divide. Because we don't share this pathway, it is an unusually clean drug
target.

**2. What the drug does.**
Sulfadoxine is a sulfonamide, and sulfonamides are shaped like pABA. The drug
slots into the DHPS active site where pABA is meant to go and competes for it.
With the site occupied, the enzyme turns over far more slowly, folate synthesis
stalls, and the parasite starves of the building blocks it needs to replicate.
This is competitive inhibition: the effect depends on how tightly the drug binds
relative to the natural substrate.

> **Superseded.** Paragraph 3 below is the original draft. The shipped text in
> `content/markers.ts` was rewritten after measuring PDB 6JWX and 6KCL:
> residue 540 is about 9–11 Å from the nearest ligand in both, so those
> structures do not support "weakens the enzyme's grip on sulfadoxine".

**3. What the mutation changes.**
K540E swaps a lysine for a glutamate — a positively charged residue for a
negatively charged one — in the region of the enzyme that shapes that binding
pocket. The charge reversal weakens the enzyme's grip on sulfadoxine more than
its grip on pABA. The natural substrate still gets through; the drug competes
less well. In practice K540E rarely appears alone, and the literature usually
reports it alongside A437G as a double mutant, with resistance increasing as
further changes accumulate.

## Ladder diagram config

pfdhps rungs, lowest first. Highlight rung 2 as the demo marker.

| rung | alteration | label |
|---|---|---|
| 1 | A437G | usually the first change to appear |
| 2 | **K540E** | with A437G forms the "double mutant" |
| 3 | A581G | further reduction in sulfadoxine efficacy |

Caption under the diagram, verbatim:

> These changes accumulate in individual parasites. A region's position on this
> ladder can only be read from studies that genotyped the combination directly —
> never by adding up separate single-mutation results.

## Limits — three bullets

- Carrying this marker is not the same as a patient's treatment failing.
  Outcome depends on the drug, the rest of the parasite's genetic background,
  and the clinical setting.
- A marker not appearing in the evidence here does not mean it is absent in the
  world. It may mean nobody has published on it, or that the extraction missed it.
- Nothing here is clinical guidance. It describes published research, not
  treatment decisions.

## Still needed in `lib/stats.ts`

Source these before filling. Do not type any from memory.

| constant | where to get it |
|---|---|
| PLACEHOLDER_ANNUAL_DEATHS | the challenge brief states ~610,000/year, most young children in sub-Saharan Africa; attribute to WHO World Malaria Report |
| PLACEHOLDER_ANNUAL_CASES | WHO World Malaria Report |
| PLACEHOLDER_SHARE_UNDER_5 | WHO World Malaria Report |
| PLACEHOLDER_SHARE_AFRICA | WHO World Malaria Report |
| PLACEHOLDER_DRUG_INTRODUCED_YEAR | per-drug, for the Data timeline |
| PLACEHOLDER_RESISTANCE_FIRST_REPORTED | per-drug, for the Data timeline |

If a timeline year can't be sourced in the next twenty minutes, cut the
timeline rather than shipping it out of order.