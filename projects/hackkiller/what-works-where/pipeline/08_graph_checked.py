"""Graph associations reviewed against the paper abstract (human review, recorded as data).

Each entry below was checked by reading the abstract sentence quoted in data/review/review_queue.csv.
The graph supplied the number; the review restores what the number compares (arm, comparator,
time point, population) and flags rows that are not intervention effects at all.
Output: data/verified/evidence_graph_checked.csv
"""
from __future__ import annotations

import pandas as pd

from common import DATA, VERIFIED, to_iso3

Q = pd.read_csv(DATA / "review" / "review_queue.csv", dtype=str, keep_default_na=False)

# key: (pmid, statistic_value as stored in the graph)
REVIEW = {
    ("32822362", "0.13"): dict(
        trial_family_id="smc-azithromycin-bf-ml", intervention_class="smc",
        intervention="SMC dose received within the past 28 days", comparator="last SMC dose more than 35 days earlier",
        country="Burkina Faso; Mali", site="Houndé; Bougouni", population="children 3-59 mo",
        outcome_tier="severe / hospital", outcome_definition="malaria hospitalisation or death from malaria",
        effect_measure="incidence rate ratio", followup_label="0-28 days after a dose", followup_months="1",
        verification_status="comparator restored",
        verification_note="graph exposure reads 'SMC'; the paper compares time since the last dose (within 28 d vs >35 d)"),
    ("32252774", "0.27"): dict(
        trial_family_id="mali-routine-smc", intervention_class="smc", intervention="routine SMC (year 1, 2015)",
        comparator="pre-SMC period (October 2013)", country="Mali", site="", population="children under 5",
        outcome_tier="clinical malaria", outcome_definition="malaria clinical incidence (Cox model)",
        effect_measure="hazard ratio", followup_label="first year of SMC", followup_months="12",
        verification_status="time point restored",
        verification_note="before-after comparison; graph does not say which year each HR belongs to"),
    ("32252774", "0.23"): dict(
        trial_family_id="mali-routine-smc", intervention_class="smc", intervention="routine SMC (year 2, 2016)",
        comparator="pre-SMC period (October 2013)", country="Mali", site="", population="children under 5",
        outcome_tier="clinical malaria", outcome_definition="malaria clinical incidence (Cox model)",
        effect_measure="hazard ratio", followup_label="second year of SMC", followup_months="24",
        verification_status="time point restored",
        verification_note="before-after comparison; graph does not say which year each HR belongs to"),
    ("35589153", "0.28"): dict(
        trial_family_id="smc-household-surveys-bf-ng", intervention_class="smc",
        intervention="SMC administration (survey during SMC campaign)", comparator="no recent SMC",
        country="Burkina Faso", site="household surveys", population="children 6-59 mo",
        outcome_tier="infection", outcome_definition="malaria infection by RDT", effect_measure="odds ratio",
        followup_label="during SMC campaign", followup_months="0", verification_status="checked against abstract",
        verification_note="country restored from abstract (graph row does not carry country)"),
    ("35589153", "0.4"): dict(
        trial_family_id="smc-household-surveys-bf-ng", intervention_class="smc",
        intervention="SMC administration (survey during SMC campaign)", comparator="no recent SMC",
        country="Nigeria", site="household surveys", population="children 6-59 mo",
        outcome_tier="infection", outcome_definition="malaria infection by RDT", effect_measure="odds ratio",
        followup_label="during SMC campaign", followup_months="0", verification_status="checked against abstract",
        verification_note="country restored from abstract"),
    ("35589153", "0.29"): dict(
        trial_family_id="smc-household-surveys-bf-ng", intervention_class="smc",
        intervention="SMC, survey 1 month after a round", comparator="no recent SMC", country="Burkina Faso",
        site="household surveys", population="children 6-59 mo", outcome_tier="infection",
        outcome_definition="malaria infection by RDT", effect_measure="odds ratio",
        followup_label="1 month after SMC", followup_months="1", verification_status="time point restored",
        verification_note="graph row lacks the 1-month time point and country"),
    ("35589153", "0.33"): dict(
        trial_family_id="smc-household-surveys-bf-ng", intervention_class="smc",
        intervention="SMC, survey 2 months after a round", comparator="no recent SMC", country="Burkina Faso",
        site="household surveys", population="children 6-59 mo", outcome_tier="infection",
        outcome_definition="malaria infection by RDT", effect_measure="odds ratio",
        followup_label="2 months after SMC", followup_months="2", verification_status="time point restored",
        verification_note="graph row lacks the 2-month time point and country"),
    ("35589153", "0.49"): dict(
        trial_family_id="smc-household-surveys-bf-ng", intervention_class="smc",
        intervention="SMC, survey 1 month after a round", comparator="no recent SMC", country="Nigeria",
        site="household surveys", population="children 6-59 mo", outcome_tier="infection",
        outcome_definition="malaria infection by RDT", effect_measure="odds ratio",
        followup_label="1 month after SMC", followup_months="1", verification_status="time point restored",
        verification_note="interval crosses 1 (p=0.07); graph row lacks time point and country"),
    ("26578353", "0.62"): dict(
        trial_family_id="ghana-ashanti-smc", intervention_class="smc", intervention="SMC (intention to treat)",
        comparator="placebo SMC", country="Ghana", site="Ashanti (extended seasonal transmission)",
        population="children", outcome_tier="clinical malaria", outcome_definition="malaria cases",
        effect_measure="adjusted hazard ratio", followup_label="one transmission season", followup_months="5",
        verification_status="checked against abstract",
        verification_note="randomised, placebo-controlled; per-protocol (5 courses) aHR 0.53 (0.29-0.95)"),
    ("21858096", "1.09"): dict(
        trial_family_id="mali-iptc-followon", intervention_class="smc",
        intervention="received IPTc (SP+AQ) the previous year", comparator="received placebo the previous year",
        country="Mali", site="", population="children under 5 at intervention", outcome_tier="clinical malaria",
        outcome_definition="clinical malaria in the following transmission season (Jul-Nov 2009)",
        effect_measure="incidence rate ratio", followup_label="year after IPTc stopped", followup_months="12",
        verification_status="time point restored",
        verification_note="tests rebound after stopping; no significant increase (p=0.08)"),
    ("28535793", "0.73"): dict(
        trial_family_id="uganda-refugee-ipt", intervention_class="smc",
        intervention="intermittent preventive treatment (refugee camp)", comparator="same period, previous year",
        country="Uganda", site="refugee camp, northern Uganda", population="children under 5",
        outcome_tier="clinical malaria", outcome_definition="malaria incidence", effect_measure="incidence rate ratio",
        followup_label="campaign period", followup_months="", verification_status="checked against abstract",
        verification_note="before-after comparison"),
    ("28535793", "0.7"): dict(
        trial_family_id="uganda-refugee-ipt", intervention_class="smc",
        intervention="intermittent preventive treatment (refugee camp)", comparator="same period, previous year",
        country="Uganda", site="refugee camp, northern Uganda", population="children 5-14 y",
        outcome_tier="clinical malaria", outcome_definition="malaria incidence", effect_measure="incidence rate ratio",
        followup_label="campaign period", followup_months="", verification_status="checked against abstract",
        verification_note="before-after comparison; age group restored"),
    ("34662864", "0.81"): dict(
        trial_family_id="chad-smc-districts", intervention_class="smc", intervention="SMC implementation (district)",
        comparator="no SMC implementation", country="Chad", site="district-level routine data",
        population="whole district", outcome_tier="clinical malaria",
        outcome_definition="monthly confirmed malaria cases (modelled)", effect_measure="rate ratio",
        followup_label="SMC months", followup_months="", verification_status="checked against abstract",
        verification_note="modelled routine-data analysis; graph stores 3 duplicate rows of this value"),
    ("36328000", "0.27"): dict(
        trial_family_id="access-smc", intervention_class="smc", intervention="SMC areas, 2018 survey",
        comparator="same areas, 2016 survey", country="Burkina Faso; Chad; Guinea; Mali; Niger; Nigeria; The Gambia",
        site="community surveys", population="children under 5", outcome_tier="infection",
        outcome_definition="P. falciparum carriage by PCR", effect_measure="prevalence ratio",
        followup_label="2 years of scale-up", followup_months="24", verification_status="comparator restored",
        verification_note="not SMC vs no SMC: a before-after change in SMC districts (genomic surveillance study)"),
    ("38081050", "0.27"): dict(
        trial_family_id="smc-meta-analysis-2024", intervention_class="smc", intervention="SMC (pooled trials)",
        comparator="no SMC / placebo", country="multi-country", site="systematic review",
        population="children under 5", outcome_tier="clinical malaria",
        outcome_definition="uncomplicated malaria incidence during the season", effect_measure="rate ratio",
        followup_label="transmission season", followup_months="", verification_status="checked against abstract",
        verification_note="systematic review: summary marker, not an independent trial"),
    ("35193608", "0.79"): dict(
        trial_family_id="rtss-smc-seasonal", intervention_class="combination", intervention="RTS,S/AS01 + SMC",
        comparator="SMC alone", country="Burkina Faso; Mali", site="seasonal Sahel sites", population="young children",
        outcome_tier="anaemia & growth", outcome_definition="prevalence of wasting (2018)",
        effect_measure="prevalence ratio", followup_label="2018 season", followup_months="24",
        verification_status="checked against abstract",
        verification_note="secondary nutrition outcome of the RTS,S + SMC trial; 2017 PR 0.88 (0.75-1.03)"),
    ("26488565", "62.7"): dict(
        trial_family_id="rtss-phase3", intervention_class="vaccines", intervention="RTS,S/AS01",
        comparator="control vaccine", country="multi-country", site="Phase 3 sites",
        population="children 5-17 mo", outcome_tier="clinical malaria",
        outcome_definition="clinical malaria with parasites matched to the vaccine circumsporozoite protein",
        effect_measure="hazard ratio (from VE = 1 - HR)", followup_label="1 year after vaccination",
        followup_months="12", verification_status="label corrected",
        verification_note="graph stored vaccine efficacy 62.7% as 'hazard_ratio = 62.7'; corrected to HR 0.373; "
                          "mismatched parasites VE 54.2% (49.9-58.1)",
        estimate="0.373", ci_lower="0.287", ci_upper="0.484"),
    ("21916638", "0.83"): dict(
        trial_family_id="fmp21-mali", intervention_class="vaccines",
        intervention="FMP2.1/AS02A blood-stage vaccine (AMA1)", comparator="rabies vaccine", country="Mali",
        site="", population="400 children", outcome_tier="clinical malaria",
        outcome_definition="clinical malaria (fever + >=2500 parasites/uL)", effect_measure="hazard ratio",
        followup_label="6 months", followup_months="6", verification_status="checked against abstract",
        verification_note="candidate blood-stage vaccine, not RTS,S/R21; strain-matched HR 0.36 (0.08-0.86)"),
    ("32536547", "0.62"): dict(
        trial_family_id="rtss-as02-reanalysis", intervention_class="vaccines", intervention="RTS,S/AS02 (primary effect)",
        comparator="control vaccine", country="Kenya", site="", population="trial participants",
        outcome_tier="clinical malaria", outcome_definition="clinical malaria episodes (primary effect)",
        effect_measure="hazard ratio", followup_label="first 3 months", followup_months="3",
        verification_status="time point restored",
        verification_note="methods re-analysis; effect strongest in first 3 months and weakens over time"),
    ("21998698", "0.64"): dict(
        trial_family_id="rtss-tcell", intervention_class="vaccines",
        intervention="higher TNFa+ CD4+ T-cell response among RTS,S vaccinees", comparator="lower response among vaccinees",
        country="", site="", population="vaccinated children", outcome_tier="clinical malaria",
        outcome_definition="clinical malaria", effect_measure="hazard ratio", followup_label="", followup_months="",
        verification_status="excluded: not an intervention effect",
        verification_note="immune correlate within vaccinees, stored as if it were a vaccine effect"),

    # ---- C2 (11:50 ET): nets rows recovered by the teammate's rule + ITN -> child mortality ----
    ("36174592", "0.8"): dict(
        trial_family_id="llineup-uganda", intervention_class="nets",
        intervention="PBO LLINs (PermaNet 3.0 / Olyset Plus)", comparator="conventional LLINs (PermaNet 2.0 / Olyset Net)",
        country="UGA", site="48 districts, eastern and western Uganda", population="residents (cross-sectional surveys)",
        outcome_tier="infection", outcome_definition="parasite prevalence, adjusted for baseline",
        effect_measure="prevalence ratio", followup_label="25 months after distribution", followup_months="25",
        verification_status="comparator restored",
        verification_note="graph row reads 'PBO LLINs -> parasite prevalence' without the non-PBO comparator; "
                          "17.1% vs 19.8%. Cluster-randomised (LLINEUP)"),
    ("36174592", "0.43"): dict(
        trial_family_id="llineup-uganda", intervention_class="nets", intervention="PBO LLINs, 6 months after distribution",
        comparator="same PBO arm at baseline", country="UGA", site="48 districts, eastern and western Uganda",
        population="residents (cross-sectional surveys)", outcome_tier="infection",
        outcome_definition="parasite prevalence (28.8% -> 12.0%)", effect_measure="prevalence ratio",
        followup_label="6 months after distribution", followup_months="6", verification_status="comparator restored",
        verification_note="within-arm before-after change, not PBO vs non-PBO; largest at 6 months, "
                          "PBO advantage persisted to 25 months"),
    ("17889242", "0.56"): dict(
        trial_family_id="kenya-itn-child-survival-2007", intervention_class="nets", intervention="ITN use",
        comparator="no ITN use", country="KEN", site="rural Kenya", population="children 1-59 mo",
        outcome_tier="mortality", outcome_definition="all-cause mortality", effect_measure="mortality rate ratio (adjusted)",
        followup_label="longitudinal follow-up during ITN scale-up", followup_months="",
        verification_status="checked against abstract",
        verification_note="observational longitudinal study; adjusted for age, period and confounders"),
    ("34051817", "0.76"): dict(
        trial_family_id="congo-itn-u5-mortality", intervention_class="nets",
        intervention="household owns at least one ITN", comparator="household owns no ITN", country="COG",
        site="national survey data", population="children under 5", outcome_tier="mortality",
        outcome_definition="all-cause under-5 mortality (Cox regression)", effect_measure="risk ratio",
        followup_label="", followup_months="", verification_status="checked against abstract",
        verification_note="observational; ownership, not use"),
    ("28990922", "0.75"): dict(
        trial_family_id="malawi-itn-ownership-2006-2010", intervention_class="nets",
        intervention="household owns an ITN", comparator="household owns no ITN", country="MWI",
        site="national household survey 2006-2010", population="children 1-59 mo", outcome_tier="mortality",
        outcome_definition="all-cause child mortality (Cox)", effect_measure="hazard ratio",
        followup_label="", followup_months="", verification_status="checked against abstract",
        verification_note="observational; abstract prints the CI as '0.62-90' (typo for 0.90)"),
    ("27146674", "0.946"): dict(
        trial_family_id="tanzania-hdss-net-ownership", intervention_class="nets",
        intervention="+10% village-level household net ownership", comparator="per 10-percentage-point lower ownership",
        country="TZA", site="Rufiji HDSS", population="children under 5", outcome_tier="mortality",
        outcome_definition="malaria deaths (space-time model)", effect_measure="incidence rate ratio",
        followup_label="", followup_months="", verification_status="comparator restored",
        verification_note="ratio is per 10% increase in village ownership, not ITN vs no ITN"),
    ("27146674", "0.899"): dict(
        trial_family_id="tanzania-hdss-net-ownership", intervention_class="nets",
        intervention="+10% village-level household net ownership", comparator="per 10-percentage-point lower ownership",
        country="TZA", site="Ifakara HDSS", population="children under 5", outcome_tier="mortality",
        outcome_definition="malaria deaths (space-time model)", effect_measure="incidence rate ratio",
        followup_label="", followup_months="", verification_status="comparator restored",
        verification_note="same model as Rufiji; site restored (Ifakara)"),
    ("15173148", "0.78"): dict(
        trial_family_id="asembo-kenya-itn-crt", intervention_class="nets", intervention="insecticide-treated bednets",
        comparator="control villages", country="KEN", site="western Kenya (intense perennial transmission)",
        population="infants 1-11 mo", outcome_tier="mortality", outcome_definition="all-cause infant mortality",
        effect_measure="hazard ratio", followup_label="phase 1 (Jan 1997 - Feb 2000)", followup_months="36",
        verification_status="time point restored",
        verification_note="community-randomised trial; low rates maintained in phase 2 surveillance"),
    ("15173148", "0.23"): dict(
        trial_family_id="asembo-kenya-itn-crt", intervention_class="nets", intervention="3-4 years of bednet use (study area)",
        comparator="neighbouring area without bednets", country="KEN", site="western Kenya",
        population="houses", outcome_tier="vector / entomological",
        outcome_definition="Anopheles mosquitoes per house", effect_measure="risk ratio",
        followup_label="after 3-4 years", followup_months="42", verification_status="label corrected",
        verification_note="graph outcome reads 'malaria transmission and child morbidity and mortality'; "
                          "the number is mosquito density per house"),
    ("22519853", "1.05"): dict(
        trial_family_id="nouna-itn-birth-cohort", intervention_class="nets", intervention="ITN protection from birth",
        comparator="ITN protection from age 6 months", country="BFA", site="Nouna, north-western Burkina Faso",
        population="birth cohort (n=3387)", outcome_tier="mortality", outcome_definition="all-cause mortality",
        effect_measure="rate ratio", followup_label="median 8.3 years", followup_months="100",
        verification_status="comparator restored",
        verification_note="individually randomised; no late mortality rebound from early protection"),
    ("16903880", "0.72"): dict(
        trial_family_id="rattanakiri-itn-crt", intervention_class="nets", intervention="deltamethrin-treated bednets",
        comparator="no net provision", country="KHM", site="Rattanakiri, north-east Cambodia", population="villages",
        outcome_tier="clinical malaria", outcome_definition="incidence of clinical P. falciparum (passive surveillance)",
        effect_measure="adjusted rate ratio", followup_label="10 months", followup_months="10",
        verification_status="label corrected",
        verification_note="graph outcome reads 'malaria morbidity and mortality'; paper: clinical P. falciparum incidence"),
    ("16903880", "0.63"): dict(
        trial_family_id="rattanakiri-itn-crt", intervention_class="nets", intervention="deltamethrin-treated bednets",
        comparator="no net provision", country="KHM", site="Rattanakiri, north-east Cambodia",
        population="children under 5", outcome_tier="infection", outcome_definition="P. falciparum prevalence",
        effect_measure="adjusted odds ratio", followup_label="10 months", followup_months="10",
        verification_status="checked against abstract",
        verification_note="greater reduction in under-5s than older ages (interaction p=0.042): age modifies the effect"),
    ("24052575", "0.07"): dict(
        trial_family_id="kassala-perinatal", intervention_class="nets", intervention="use of a mosquito net",
        comparator="no mosquito net", country="SDN", site="Kassala, eastern Sudan", population="births 2010-2011",
        outcome_tier="mortality", outcome_definition="perinatal death", effect_measure="odds ratio",
        followup_label="", followup_months="", verification_status="checked against abstract",
        verification_note="observational risk-factor analysis; implausibly strong association, likely confounded"),
}


def main() -> None:
    rows = []
    for (pmid, val), ann in REVIEW.items():
        hit = Q[(Q.pubmed_id == pmid) & (Q.statistic_value.astype(float).round(4) == round(float(val), 4))]
        if hit.empty:
            print("not found in queue:", pmid, val)
            continue
        r = hit.iloc[0]
        rows.append({
            "result_id": f"G-{pmid}-{val}", "trial_family_id": ann["trial_family_id"], "pmid": pmid,
            "short_ref": f"{(r.title or '')[:60]}… ({r.year})", "intervention_class": ann["intervention_class"],
            "intervention": ann["intervention"], "comparator": ann["comparator"], "country": ann["country"], "iso3": to_iso3(ann["country"]),
            "site": ann["site"], "population": ann["population"], "outcome_tier": ann["outcome_tier"],
            "outcome_definition": ann["outcome_definition"], "effect_measure": ann["effect_measure"],
            "estimate": ann.get("estimate", r.statistic_value), "ci_lower": ann.get("ci_lower", r.ci_lower),
            "ci_upper": ann.get("ci_upper", r.ci_upper), "ci_level": r.ci_level,
            "followup_label": ann["followup_label"], "followup_months": ann["followup_months"],
            "publication_year": r.year, "origin": "graph (abstract-checked)",
            "graph_association_id": r.system_id, "graph_original_label": f"{r.intervention_text} -> {r.outcome_text}",
            "graph_statistic": f"{r.system_statistic_type} {r.statistic_value} ({r.ci_lower}-{r.ci_upper})",
            "verification_status": ann["verification_status"], "verification_note": ann["verification_note"],
            "source_location": "Abstract", "source_quote": r.abstract_quote,
            "source_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/", "doi": r.doi,
        })
    out = pd.DataFrame(rows)
    out.to_csv(VERIFIED / "evidence_graph_checked.csv", index=False)
    print(out.groupby(["intervention_class", "verification_status"]).size().to_string())


if __name__ == "__main__":
    main()
