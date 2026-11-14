# The Missing Label: winning plan

> **Status (14 Nov):** `spec.md` is now the source of truth. This plan was the first strategy draft, and Myra's notes (`docs/myra-strategy-notes.md`) have been merged into the spec. Where this plan disagrees with the spec, the spec wins.
>
> **Superseded parts of this plan:**
> - the FAERS / FDA adverse-event check (dropped; see spec §12.1)
> - the 24-hour timeline (actual hacking time is Sat 10 AM–3 PM; see spec §10.3)
> - the storage sensor as a core feature (moved to "add later," spec §11)
>
> **Still-open conflicts** between Rachel's and Myra's plans are listed in spec §12.2.

This plan builds on Myra's concept (The Missing Label). It sharpens the parts that could fail, adds the rigor most teams skip, and adds three angles the judges are unlikely to see anywhere else.

> **Updated after the graph check (13 Nov 2026), see `docs/graph-check-results.md`.**
> - The graph holds only about 15 direct drug × heat findings.
> - It holds about 300 drug → dehydration / low sodium / kidney injury findings, and heat → those same outcomes plus mortality.
>
> So the graph's role shifts from "evidence meter per drug" to a **two-hop heat-risk pathway** (§4A). The gap itself becomes a headline (§4D).

---

## 1. Keep, change, add

**Keep (these are strong):**
- **The label as the centerpiece.** It's familiar, readable, and memorable.
- **The evidence-vs-guidance quadrant.** It answers the brief's exact question.
- **The NYC playbook.** It moves the project from a visual to a tool.
- **The pill-bottle handout.**

**Change (the research says the original framing would get caught out):**

| Myra's draft | Problem | Fix |
|---|---|---|
| One "evidence strength meter" per drug | Our research found that the drugs on every guidance list mostly **flag who is vulnerable** rather than cause extra harm. Within-person studies in Medicare and Japan found no added heat-wave effect. A clinician judge will know this. | **Two meters on every label:** **FLAG** (how strongly this prescription identifies someone to contact) and **CHANGE** (how strongly the evidence supports changing the drug itself). Nobody else will make this distinction, and it's true. |
| Headline: "Strong evidence, guidance silent" | That zone is small. The bigger pattern is **guidance overstating** common drug classes while ignoring rare but severe harms (fentanyl patches, topiramate in adults, oxybutynin, insulin pumps, SGLT2 inhibitors). | Keep the quadrant, add **marker size = severity**, and tell a two-sided story: "guidance cries wolf on X, and is silent on Y." |
| Storage sensor that turns red at the 86°F label limit | A randomized trial found insulin pens kept at 99°F for 3 weeks worked fine. A sensor based on the label would contradict the evidence on stage. | Make it the **evidence-calibrated thermometer** (§4C). It tracks cumulative heat exposure, not just a threshold, and its limits come from evidence, not the label. |
| "Hidden heat drugs" from graph mechanism links alone | An unvalidated prediction is a liability. A judge will ask "how do you know?" | **Predict, then confirm independently** using FDA adverse-event reports, and **backtest** the method (§4A). |
| Evidence strength meter "from graph findings" | The graph has about 15 direct drug × heat findings, so the meter would be empty for almost every drug. | Each label gets **three marked evidence layers**: ① graph pathway (two-hop), ② published papers not in the graph (from our master list, citations verified), ③ FDA adverse-event signal. The brief asks for exactly this ("show which links rest on graph findings and which don't"). |
| Neighborhood "prevalence of conditions" | NYC doesn't publish prescriptions by neighborhood. | Use **CDC PLACES** (tract-level diabetes, high blood pressure, poor mental health) plus **CMS Part D** (which prescribers write heat-risk prescriptions). |

**Add (the angles no one else will have):** 1) FDA adverse-event confirmation, 2) a plug-in for clinicians' electronic health records (EHRs), 3) an audit of the graph's own data quality, handed to the System team, and 4) one national drug database that makes it work for any drug in any US city. See §4.

---

## 2. Go/no-go check: done, the decision is GO (reframed)

Results (`docs/graph-check-results.md`):

| Link type | Findings in graph | Verdict |
|---|---|---|
| Drug × heat directly (heat stroke, hyperthermia, body temperature, sweating, heat wave) | **~15** (mostly off-topic) | Near zero, so it can't carry the evidence meter |
| Drug → dehydration / hyponatremia / AKI | **~300** (ACEi/ARB 74, diuretics 55, NSAIDs 44, antipsychotics 22, loop diuretics 21, SGLT2 19, metformin 14, thiazides 12, SSRIs 10, lithium 6) | Strong enough for the first hop |
| Heat → mortality / AKI / cardiovascular disease / blood pressure / heart failure | Present (about 70 studies on mortality across heat concepts) | Strong enough for the second hop |

**Why not switch to The Next Aspirin:** near-zero direct coverage is a finding, not a failure. The brief asks where the evidence runs out. The two-hop pathway uses the graph more meaningfully than a lookup would, and no other team will build it.

**One check left (Myra, H0–1):** a full-text scan of the 442 MB associations CSV confirms the direct count isn't an undercount caused by filing under general concepts. Run `py -3 scripts/graph_check.py csv <file>`. Put the final number on the methods slide.

---

## 3. Data pipeline: the rigor most teams skip

Judges can't verify everything in 3 minutes. They notice **visible rigor**, so make every step below show up in the product as a "Methods & receipts" page.

**A. Normalize drug names (RxNorm).** Use the free NLM RxNav API to map every drug name, brand, generic, or class mention in the graph to its RxNorm ingredient and drug class. Without this step, "Lasix", "furosemide" and "loop diuretic" get counted as three different things. Report "N raw strings → M normalized drugs."

**B. Clean the graph findings.**
- Group heat-outcome synonyms (heat stroke, hyperthermia, heat-related illness, and so on) into a small set of canonical outcomes.
- **Deduplicate** so one paper with five findings doesn't count as five studies. Count **independent papers**, not findings.
- Tag study design where you can tell it, and tag effect direction (harm / null / protective).
- Use female-specific variable names to estimate how much of the evidence includes women. Report that coverage.

**C. Hand-check a sample.** Randomly pick about 40 graph findings and check each against its abstract: does the variable, direction and population match? Report **extraction accuracy = X%** and list the errors (this feeds §4D).

**D. Code the guidance documents twice.** Myra and you each code the 8 guidance documents × about 25 drugs separately, as yes/no for "mentions the drug" and for "gives a specific action." Calculate **Cohen's kappa** (a standard score for how often two coders agree), then settle disagreements together. It takes about 90 minutes, and almost no hackathon team does it. Put "κ = 0.8x" on the methods slide.

**E. Verify citations.** 46 of the 86 rows in the master list aren't fully verified. Run a script against PubMed's lookup API and Crossref to confirm each PMID/DOI exists and its title matches. Anything that can't be confirmed gets dropped from public labels or marked "unverified."

**F. Pin data versions.** Record a version or access date for every dataset (graph snapshot date, PLACES release, Part D year, guidance publication dates) in one `data/SOURCES.md`.

**G. A transparent evidence-scoring rubric.** Publish the formula behind both meters, for example: design weight × number of independent studies × consistency × how well the study population matches the people at risk. Show the formula on the methods page. A meter you can explain beats a vibe.

---

## 4. The standout angles

### A. The two-hop heat-risk pathway, then hidden heat drugs confirmed with FDA data (the "graph as a graph" moment)

**The core move:** the graph almost never links a drug straight to heat, but it does link drugs to the harms heat causes, and it links heat to those same harms. Chain them:

```
HEAT ──(graph)──► kidney injury / low sodium / dehydration / mortality ◄──(graph)── DRUG
```

For each drug, compute a **pathway score**:
- **Inputs:** for each mediator, the drug's findings and studies, and heat's findings and studies.
- **Combining:** take the weaker hop for each mediator, then sum across mediators.
- **Counts that matter:** count only same-direction effects (both hops raise the risk), and count **distinct papers**.

Show it as a **Sankey or network diagram**: drugs on the left, mediators in the middle, heat outcomes on the right. Line width is the number of studies. Lines are dashed where the link comes from published papers outside the graph.

**Validation (this is what makes it credible):**
- **Does it rediscover what's known?** Does a high pathway score pick out the drugs the 2003 French and Medicare heat-wave studies flagged, such as loop diuretics, ACEi/ARBs and antipsychotics? Report the share it gets right.
- **Where it disagrees, say so.** Anticholinergics score low on the pathway because their mechanism is sweating, and the graph has no anticholinergic × sweating findings. That's a real blind spot of mediator-based inference, and naming it earns trust.

Then extend to hidden drugs:

1. **Predict.** Find drugs with strong graph links to the mediators that appear on **no** guidance list. Candidates from the check: SGLT2 inhibitors (19 graph findings, on none of the 8 guidance lists), metformin, NSAIDs. Add mechanism classes the mediators miss: the published **Anticholinergic Burden (ACB) scale** for drugs that reduce sweating, and carbonic-anhydrase inhibitors.
2. **Confirm independently.** Query **openFDA's adverse-event database (FAERS)**, which is free and needs no key for small queries, for reaction terms: heat stroke, hyperthermia, heat exhaustion, dehydration, hyponatremia, anhidrosis/hypohidrosis.
   - For each drug, compute a **reporting odds ratio with a 95% confidence interval**. This shows whether the drug appears in heat-related reports more often than expected.
   - Optional: check whether those reports cluster in summer.
3. **Backtest the method.** Hide the known heat drugs (the CDC list) from the predictor and check whether it rediscovers them. Report **precision and recall** (the share of its flags that were correct, and the share of known drugs it found).

**Headline:** "The graph has almost nothing on drugs and heat directly. But connecting what it *does* know rediscovered X of Y known heat drugs, then flagged N drugs that appear on no warning list. FDA adverse-event reports back up M of them."

**Caveat:** adverse-event reports are biased; they support a signal but don't prove cause. Say so on the slide; judges reward that honesty.

### B. The label that works on the systems clinicians already use (scalability)

Build the heat-risk knowledge base once (JSON: drug → buckets, FLAG/CHANGE scores, plain-language line, citations, guidance coverage). Then show it reaching patients through several outputs:

1. **Printable label** (PDF generator): the pill-bottle prop.
2. **Heat Label API:** send an RxNorm code, get back the heat label JSON. Because of §3A, this covers any US drug, not just our 25.
3. **EHR prescribing alert** (using the CDS Hooks standard):
   - When a clinician prescribes a flagged drug and the National Weather Service forecast for that zip shows high heat, a card pops up in the EHR with the label and one suggested action.
   - Demo it in the free public CDS Hooks sandbox.
   - Chethan Sarabu, the challenge owner, is a clinician in digital health, so this is the piece he'll remember.
4. **Pharmacist counter card and SMS text** for patients.

**Scalability line for the pitch:** "NYC is the demo. The data sources (PLACES, Part D, National Weather Service, RxNorm) cover every county in the US." Have a toggle that switches the playbook to **Phoenix** live.

### C. The evidence-calibrated thermometer (hardware, only if parts are in hand tonight)

- **Low effort, highest memorability (do this even without electronics):** **thermochromic ink** on the printed label, so the heat warning **appears** as the judge's hand warms the bottle. Look for ink that activates at about 31°C (88°F).
- **Optional build:** an ESP32 + SHT31 sensor that computes **cumulative heat exposure** using *mean kinetic temperature*, a standard pharmaceutical measure of total heat exposure over time. Each drug gets its own limit taken from evidence:
  - It stays **green** for an insulin pen at 99°F, in line with the trial.
  - It turns **red** for epinephrine, glucose strips and pump reservoirs.
  - On stage: "Our thermometer disagrees with the label, and here's the trial that says why."

Skip the sensor entirely if the core product isn't working by Saturday midday.

### D. Give System's team an audit of their own graph

From §3C and the gap analysis, deliver a one-page **"Graph audit: medication × heat"**:
- **the headline number: "about 15 direct drug × heat findings, versus 60+ published studies we found"**
- for each landmark study (French 2003, Layton 2020 Medicare, Kalisch Ellett 2016, Wong 2024 Japan, the topiramate series, the fentanyl heat studies): is it indexed? If so, were its findings extracted, and under which concepts?
- extraction accuracy from the hand-checked sample
- the women and age coverage estimate
- entity-matching problems from RxNorm normalization

Most of the judges work on the graph itself. Handing them a list of fixes shows you used the graph deeply, and they'll remember it.

### E. Replay a real NYC heat wave

There's no heat in a November forecast, so **replay** a past NYC heat wave using NOAA records. Then sanity-check the playbook: do the neighborhoods it ranks highest match where NYC's Environment & Health Data Portal shows heat-related ED visits or deaths concentrating? Even a rough match ("our top-quintile neighborhoods account for X% of heat deaths") is strong validation.

---

## 5. The playbook in detail

**Input:** a forecast heat wave (replay or live NWS feed).

**72-hour output:**
1. **Where:** NYC neighborhoods ranked by Heat Vulnerability Index × PLACES prevalence of diabetes, high blood pressure, poor mental health and COPD. Overlay **cooling centers** and **pharmacies** from NYC Open Data.
2. **Who to alert:** Part D shows which **specialties and areas** write the most heat-risk prescriptions (e.g., "312 NYC prescribers write 80% of Medicare heat-risk claims"). Show aggregates on stage, **never individual clinicians' names**. Note that Part D covers ages 65+ only and is located by prescriber, not patient.
3. **What to send:** the label lines, split into **"call these patients"** (FLAG) and **"consider changing"** (CHANGE).
4. **Power-outage add-on:** a reminder for patients on power-dependent devices. Cite the 2003 blackout finding: half of respiratory EMS calls involved failed home equipment.

---

## 6. Rubric map

| Criterion | What earns the points |
|---|---|
| Meaningful use of the graph | Two-hop heat-risk pathway (drug → mediator ← heat), validated against known heat drugs; hidden-drug prediction; a measured gap (about 15 direct findings) and a graph audit returned to System |
| Insight and usefulness | The FLAG-vs-CHANGE distinction; the two-sided guidance gap; hidden drugs confirmed by FDA data; a playbook a health department could run |
| Technical execution | RxNorm normalization, reporting odds ratios, backtest precision/recall, kappa, CDS Hooks card, API, live NWS feed, optional sensor |
| Communication | The label, thermochromic bottle, quadrant, NYC map, one plain-language line per drug, the Methods & receipts page |
| Rigor (unscored, but judges notice) | Hand-check accuracy, double-coding, citation verification, pinned versions, stated caveats |

---

## 7. Scope tiers (protect the demo)

- **Must have (by Saturday midday):** CSV confirmation scan; two-hop pathway scores and Sankey diagram for about 15 drugs; three-layer evidence per label; double-coded guidance; labels for about 8 drugs; quadrant; Methods page with the gap number; printed bottles.
- **Should have:** FAERS confirmation and pathway validation; graph audit one-pager; playbook with HVI × PLACES map; NYC heat-wave replay; Heat Label API.
- **Could have:** CDS Hooks card; Phoenix toggle; sensor.
- **Won't do:** naming individual prescribers, patient-level advice, recreational drugs.

Cut from the bottom of the list. Never cut the Methods page.

---

## 8. Timeline (H0 = start of build)

| When | You | Myra |
|---|---|---|
| H0–1 | Pull all drug → mediator and heat → mediator findings from the API (associations, not just counts) | Download the CSV and run the confirmation scan; order thermochromic labels and pill bottles |
| H1–4 | RxNorm normalization; clean and deduplicate both hops; tag effect direction | Code guidance documents (first pass) |
| H4–6 | Code guidance documents (second pass) → kappa | Label design system (three evidence layers); quadrant prototype |
| H6–9 | Pathway scores + validation; FAERS reporting odds ratios | Hand-check ~40 findings; check landmark studies for the graph audit |
| H9–12 | Knowledge-base JSON + scoring rubric | Build the site: Sankey diagram, labels, quadrant, Methods page |
| Sleep | | |
| H16–20 | Playbook data (HVI, PLACES, Part D, cooling centers, NWS) | Playbook UI + map |
| H20–22 | API / CDS Hooks card (if on schedule) | Print labels; assemble bottles |
| H22–24 | **Freeze code.** Check every number on every slide against its source | Rehearse the pitch twice, timed |

---

## 9. Pitch (3 minutes)

1. **(0:00)** Hand a judge a bottle. "This warns you about alcohol. Hold it for a second." The heat warning appears. "This is the label that doesn't exist."
2. **(0:25)** Lithium label: two meters, one plain-language line, one-click evidence receipts.
3. **(0:55)** Quadrant: "Guidance cries wolf here, and is silent here, where fentanyl patches have killed people."
4. **(1:25)** The twist: "System's graph has 15 findings on drugs and heat, and we found 60 studies that should be there." Then show the Sankey diagram: "But the graph knows what heat does to kidneys and sodium, and what drugs do to them. Connected, it rediscovered X of Y known heat drugs, and flagged N on no warning list. FDA reports back up M."
5. **(1:55)** "A heat wave hits Thursday." Run the replay → map → who to call → message.
6. **(2:30)** "Works on any drug, in any US county, and inside the EHR." Flip to Phoenix, or show the CDS card.
7. **(2:50)** "We also audited the graph. Here's your fix list." Hand over the one-pager.

---

## 10. What could go wrong, and what to do about it

- **Medical-advice risk.** Every label reads "Prototype. Considerations for clinicians, not instructions to patients." No brand names or pharmacy logos on the props.
- **Overclaiming.** Adverse-event reports and case reports go on screen labeled as such. Show confounding explicitly.
- **Live demo failure.** Pre-record a 60-second video of the playbook as a backup.
- **Scope creep.** At H12, review the scope tiers and cut whatever is behind.
