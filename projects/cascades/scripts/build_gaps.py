"""Gaps register: where evidence is absent or thin, by group x role x outcome, by UK coverage and by setting,
plus data gaps (no open dataset) carried from the dataset review. Every gap says what kind of gap it is."""
import itertools
import pandas as pd

ev = pd.read_csv("data/evidence.csv")
k = ev[ev.relevance == "keep"]
groups = sorted(k.group.unique().tolist() + [g for g in ["Building fabric (insulation, airtightness)"] if g not in k.group.unique()])
roles = ["exposure", "intervention"]
outcomes = ["Infection", "Asthma & wheeze", "Other respiratory", "Allergy & skin", "Mental health & sleep", "Cardiovascular", "Cancer", "Mortality & hospital use"]
SEARCH = "keyword + concept search of curated System Public Graph v2.1, hand-labelled 14 Nov 2026"

def label(n):
    return "no match under this search" if n == 0 else "thin (1-4 studies)" if n < 5 else "moderate (5-19 studies)" if n < 20 else "well studied (20+ studies)"

rows = []
for g, r, o in itertools.product(groups, roles, outcomes):
    if g == "Crowding (exposure)" and r == "intervention":
        rows.append(dict(gap_type="evidence: group x role x outcome", group=g, role=r, outcome=o, setting="all", studies=None, uk_studies=None,
                         status="not applicable", uk_status="", search_scope=SEARCH, note="crowding is an exposure linked to Ventilation and Moisture & mould; fixes are housing supply/allocation, not building interventions"))
        continue
    s = k[(k.group == g) & (k.role == r) & (k.outcome_group == o)]
    n, uk = s.study_id.nunique(), s[s.is_uk].study_id.nunique()
    rows.append(dict(gap_type="evidence: group x role x outcome", group=g, role=r, outcome=o, setting="all",
                     studies=n, uk_studies=uk, status=label(n), uk_status="no UK study" if uk == 0 else f"{uk} UK",
                     search_scope=SEARCH, note=""))
for g, r in itertools.product(groups, roles):
    if g == "Crowding (exposure)" and r == "intervention": continue
    s = k[(k.group == g) & (k.role == r)]
    for st in ["home", "school", "workplace"]:
        n = s[s.setting == st].study_id.nunique()
        rows.append(dict(gap_type="evidence: setting", group=g, role=r, outcome="any", setting=st, studies=n,
                         uk_studies=s[(s.setting == st) & s.is_uk].study_id.nunique(), status=label(n),
                         uk_status="", search_scope=SEARCH, note="setting parsed from population text and variable names"))
DATA_GAPS = [
 ("Moisture & mould remediation", "No open dataset linking damp/mould remediation to health outcomes; EHS gives prevalence only"),
 ("Building fabric (insulation, airtightness)", "Few observed before/after retrofit energy + health datasets; EPC is modelled; heat-pump monitoring (EoH) access unverified"),
 ("Ventilation & source capture", "Small measured samples only (7 English homes, 70 California homes, 1 Finnish office); no intervention-linked health data"),
 ("Particle filtration", "No UK school filtration dataset; SICAS (US) published null result only; China purifier data observational"),
 ("Clean cooking", "No UK gas-to-induction switch trial with health outcomes; most graph evidence is solid fuel in LMICs"),
 ("Radon mitigation", "No open building-level pre/post mitigation data; radon atlas licence not stated"),
 ("Allergen & pest control (household)", "No open intervention dataset with health outcomes; SICAS IPM arm published only"),
 ("Indoor temperature (heating & cooling)", "Sparse measured overheating/comfort data; no cooling intervention health data for UK homes"),
 ("(cross-cutting) schools & offices", "Pupil absence is aggregate context; office productivity/absence data essentially absent"),
 ("Crowding (exposure)", "Only 5 UK studies on household crowding in the graph; Census gives prevalence (2021, pandemic census day) but no area-level overcrowding-by-tenure table (RM099 download failed)"),
 ("Clean cooking", "No UK figure found for share of homes cooking on gas, so EU/US attributable fractions (12-12.7% child asthma) cannot be scaled to UK"),
 ("Ventilation & source capture", "California 70-homes range hood + NO2 dataset needs browser download (Dryad 401); seven English homes have no room labels and uncalibrated NO2"),
 ("Building fabric (insulation, airtightness)", "Retrofit quality is a hidden variable: NAO found 98% external / 29% internal wall insulation under ECO4/GBIS with major issues (damp & mould risk) - no health follow-up of affected homes"),
 ("(cross-cutting) indoor air", "NICE NG149 research recommendations: health impact of individual indoor pollutants; effective interventions for people without pre-existing conditions; minimum air-exchange rate; building materials"),
 ("(cross-cutting) co-benefits", "Installation cost, observed bill savings, who pays, displacement and peak demand are unverified gaps"),
]
for g, note in DATA_GAPS:
    rows.append(dict(gap_type="data: no open linked dataset", group=g, role="intervention", outcome="health / co-benefit", setting="",
                     studies=None, uk_studies=None, status="data gap", uk_status="", search_scope="dataset review (Christina, 14 Nov 2026)", note=note))
CERTAINTY = [
 ("Moisture & mould remediation","Cochrane (Sauni 2015): repair reduces adult asthma symptoms/infections but certainty moderate to very low; school evidence inconsistent","COCHRANE_MOULD"),
 ("Allergen & pest control (household)","Cochrane (Gotzsche 2008): single dust-mite control measures show no benefit; review flagged as out of date; multi-trigger programmes not reviewed","COCHRANE_HDM"),
 ("Clean cooking","HAPIN RCT (LMIC): LPG cut exposure but did not change birth weight, pneumonia or stunting - exposure reduction did not equal health gain","HAPIN"),
 ("Particle filtration","Only small RCTs (e.g. HAPI, n=71, US): PM2.5 fell ~60% but primary asthma-control outcome not significant","HAPI_HEPA"),
 ("Ventilation & source capture","School ventilation-absence evidence is observational (California 1.6%/L/s; Scotland small effect); no trials","MENDELL_VENT; GAIHRE_SCOT"),
 ("Radon mitigation","No study measures health outcomes after mitigation; benefit is modelled from exposure-response (cost/QALY GBP 36.8k retrofit vs 11.4k new build)","GRAY_RADON"),
 ("Building fabric (insulation, airtightness)","Health benefit concentrated in people with inadequate warmth/chronic respiratory disease; untargeted retrofit >GBP 100k/QALY (NICE model)","COCHRANE_WARMTH; NICE_NG6"),
]
for g, note, src in CERTAINTY:
    rows.append(dict(gap_type="evidence: low certainty or null result", group=g, role="intervention", outcome="health", setting="",
                     studies=None, uk_studies=None, status="low certainty / null", uk_status="", search_scope="reviews and trials outside the graph (see sources.csv)", note=note + " [" + src + "]"))
gaps = pd.DataFrame(rows)
PRI = {"Ventilation & source capture":"core", "Particle filtration":"core", "Clean cooking":"core", "Moisture & mould remediation":"core",
       "Radon mitigation":"core", "Allergen & pest control (household)":"core", "Crowding (exposure)":"core (exposure)",
       "Building fabric (insulation, airtightness)":"air-quality trade-off", "Indoor temperature (heating & cooling)":"secondary (parked)"}
gaps["air_quality_priority"] = gaps.group.map(PRI).fillna("cross-cutting")
gaps.to_csv("data/gaps.csv", index=False)
ev_g = gaps[gaps.gap_type == "evidence: group x role x outcome"]
print(ev_g.status.value_counts().to_string()); print()
print("intervention x outcome cells with no match:", ((ev_g.role == "intervention") & (ev_g.studies == 0)).sum(), "of", (ev_g.role == "intervention").sum())
print("cells with zero UK studies:", (ev_g.uk_studies == 0).sum(), "of", len(ev_g))
print(ev_g[ev_g.role == "intervention"].pivot_table(index="group", columns="outcome", values="studies", aggfunc="sum").to_string())
