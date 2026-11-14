"""Registrations for the restaurant analyses. Run with the claim id as argument:
  python analyses/restaurants/register.py restaurants-score-complaints
Each registration is committed at once and pushed to prereg/<id>."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import claims  # noqa: E402

DER = ROOT / "data" / "derived" / "restaurants"

GRAPH_COMPLAINTS = [
    {"association_id": "RzNvMLQc9u (variable) protection from contamination violation -> outbreak level", "pubmed_ids": ["31928421"],
     "direction": "+", "n_findings": 1, "n_studies": 1,
     "summary": "Minnesota chain outbreak (Firestone 2020): a protection-from-contamination violation at the last routine inspection, OR 4.92 (1.57-15.39) for outbreak level; 54 restaurants."},
    {"association_id": "FCDuRbXqiy (variable) evidence of vermin -> food-borne outbreaks", "pubmed_ids": ["11344897"],
     "direction": "+", "n_findings": 2, "n_studies": 1,
     "summary": "Miami-Dade 1995 case-control (Cruz 2001): overall inspection outcome and number of critical violations did not differ between outbreak and control restaurants; only vermin, OR 3.3 (1.1-13.1)."},
    {"association_id": "z1sSUpT_EZ (variable) complaint rates -- outbreak rates", "pubmed_ids": ["21375880"],
     "direction": "+", "n_findings": 1, "n_studies": 1,
     "summary": "US local health departments (Li 2011): complaint and outbreak rates correlate, r = 0.38; complaints detect a median 69% of outbreaks."},
    {"association_id": "CCatfE2F4k (variable) chain restaurants -- violations per inspection", "pubmed_ids": ["28060568"],
     "direction": "-", "n_findings": 1, "n_studies": 1,
     "summary": "Philadelphia 2013-2014 (Leinwand 2017): chains 6.5 against 9.6 violations per inspection; used here as a covariate."},
]

LIT_COMPLAINTS = [
    {"citation": "Irwin K et al. Am J Public Health 1989;79:586-590 (PMID 2705592)", "doi": "10.2105/ajph.79.5.586",
     "finding": "Seattle-King County, 28 outbreak restaurants and 56 matched controls: poor routine scores 5 times, temperature-control violations 10 times more likely in outbreak restaurants."},
    {"citation": "Jones TF et al. Emerg Infect Dis 2004;10:688-692 (PMID 15200861)", "doi": "10.3201/eid1004.030343",
     "finding": "Tennessee 1993-2000, 167,574 inspections: mean scores of outbreak restaurants did not differ from others; inspector means ranged 69-92."},
    {"citation": "Petran RL, White BW, Hedberg CW. J Food Prot 2012;75:2016-2027 (PMID 23127711)", "doi": "10.4315/0362-028X.JFP-12-147",
     "finding": "No overall association between routine inspection scores and outbreak inspection scores at outbreak restaurants; some specific violations more likely."},
    {"citation": "Harrison C et al. MMWR 2014;63:441-445 (PMID 24848215)", "doi": None,
     "finding": "NYC Yelp pilot: of 468 illness reviews only 3% had been reported to DOHMH by phone or online, so 311 complaints are a small, selected share of illness."},
    {"citation": "Wong MR et al. Am J Public Health 2015;105:e81-e87 (PMID 25602861)", "doi": "10.2105/AJPH.2014.302404",
     "finding": "NYC letter grading: probability of an A-range score on unannounced inspection +35% (31-40%) three years after launch."},
    {"citation": "Firestone MJ, Hedberg CW. Emerg Infect Dis 2018;24:2164-2168 (PMID 30457518)", "doi": "10.3201/eid2412.180544",
     "finding": "Salmonella rates in NYC fell 5.3% a year relative to the rest of New York State after letter grading (2011-2015 against 2006-2010)."},
    {"citation": "Jin GZ, Leslie P. Q J Econ 2003;118:409-451", "doi": "10.1162/003355303321675428",
     "finding": "Los Angeles grade cards raised hygiene scores and were followed by a fall in foodborne-illness hospitalisations (about 20%). Not in PubMed; abstract not read here, cited from the paper's published summary."},
]


def restaurants_score_complaints():
    power = json.loads((DER / "power_complaints.json").read_text())
    pw = power["notA_vs_A_phi2.5"]
    return {
        "id": "restaurants-score-complaints",
        "kind": "confirmation",
        "statement": "Restaurants that score 14 or more points (not A-range) at a routine initial inspection draw more 311 Food Poisoning complaints in the following 365 days than restaurants that score 0-13, after borough, cuisine, chain status and quarter, and the excess is larger than for Noise - Commercial complaints at the same lots.",
        "graph_evidence": GRAPH_COMPLAINTS,
        "literature": LIT_COMPLAINTS,
        "prediction": {
            "direction": "+",
            "magnitude": "IRR (not-A against A-range) 1.10 to 1.60, midpoint 1.33. The literature is split: Irwin 1989 found poor scores predict outbreaks (about 5 times), Cruz 2001, Jones 2004 and Petran 2012 found no overall association. 311 complaints are a noisy, self-selected signal of illness (Harrison 2014), which dilutes any effect.",
            "support_if": "The primary IRR has a 95% lower bound above 1.00 AND the ratio of the food-poisoning IRR to the Noise - Commercial IRR has a 95% lower bound above 1.00 (independence assumed for the ratio's variance, which is conservative when the two estimates covary positively).",
            "refute_if": "The primary IRR has a 95% upper bound below 1.10 (the low end of the band is excluded).",
            "rule11": "The placebo is the Noise - Commercial model. If its IRR has a 95% lower bound above 1.00 (it meets the first half of support_if), or D_placebo = z_placebo^2 - z_pred^2 < 4, where z_placebo = (b_fp - b_noise)/sqrt(se_fp^2 + se_noise^2) and z_pred = (b_fp - log 1.33)/se_fp, the verdict is unsettled unless refute_if is met.",
            "power": f"Computed before the join from marginal counts (data/derived/restaurants/power_complaints.json): about {pw['expected_events_exposed']} complaints at not-A and {pw['expected_events_reference']} at A-range restaurants expected; se(log IRR) {power['notA_vs_A_phi1.5']['se_log_irr']} to {pw['se_log_irr']} for dispersion 1.5 to 2.5; if the midpoint is true, z = {pw['z_if_mid_true']} to {power['notA_vs_A_phi1.5']['z_if_mid_true']} and D against no effect = {pw['D_if_mid_true']} to {power['notA_vs_A_phi1.5']['D_if_mid_true']} (>= 4, so the test discriminates the midpoint from no effect); at IRR 1.10 it does not (z about 1).",
        },
        "plan": "Script analyses/restaurants/complaints_test.py at commit 0c147b3 (no resampling, no seed). Cohort: first Cycle Inspection / Initial Inspection with a score per CAMIS, 2023-01-01 to 2025-06-30, citywide live 43nn-pn8j, restricted to CAMIS whose 10-digit BBL holds exactly one CAMIS in the live data from 2022 on. Exposure: score >= 14 against 0-13. Outcome: count of erm2-nwe9 complaints, type Food Poisoning, location type Restaurant/Bar/Deli/Bakery, at the BBL, created on days 1-365 after the inspection. Model: Poisson GLM, HC1 robust SE, covariates borough, cuisine group (top 20), chain (dba with >= 10 CAMIS), inspection quarter. Placebo: same model with Noise - Commercial complaints at the BBL. Secondary, deciding nothing: C-range (>= 28) against A; per 10 points; NTA fixed effects; Manhattan only; complaints in the 365 days before the inspection.",
        "alternatives": [
            "Volume: busy restaurants have more diners, so more complaints, and more chances for violations; the noise placebo and cuisine and chain controls address part of this.",
            "Reporting propensity: neighbourhoods and clienteles that complain more to 311 also draw stricter inspections or are in areas inspected differently.",
            "Persistent quality: a restaurant's hygiene is stable, so the association reflects the restaurant, not the inspection; the pre-window secondary shows this and does not make the result causal.",
            "Survivorship: the live data keep only restaurants open now; restaurants that closed after a bad score and many complaints are missing, biasing the IRR towards 1.",
            "Linkage: single-CAMIS BBLs are smaller buildings and differ from food halls and towers.",
        ],
        "prior": 0.3,
        "registrant": "claude (restaurants agent, 13 November 2026)",
        "script_commit": "0c147b3",
    }


def restaurants_nta_harshness():
    return {
        "id": "restaurants-nta-harshness",
        "kind": "confirmation",
        "statement": "Critical violations detected per routine initial inspection are not even across Manhattan's 2020 NTAs: after cuisine, chain status, quarter, day of week, daily inspection workload, new-restaurant status and the NTA's restaurant count, the between-NTA variation exceeds a permutation null, with a between-NTA standard deviation of 5 to 20 percent.",
        "graph_evidence": [GRAPH_COMPLAINTS[3]],
        "literature": [
            {"citation": "Jones TF et al. Emerg Infect Dis 2004;10:688-692 (PMID 15200861)", "doi": "10.3201/eid1004.030343",
             "finding": "Tennessee: mean scores of individual inspectors ranged from 69 to 92 on a 100-point scale, so who inspects changes the result."},
            {"citation": "Leinwand SE et al. Public Health Rep 2017;132:180-187 (PMID 28060568)", "doi": "10.1177/0033354916687741",
             "finding": "Philadelphia: violations per inspection differ by chain status (6.5 against 9.6) and by block-group racial composition (0.6 fewer risk-factor and 1.0 more retail-practice violations), and fall with inspection frequency in non-chains."},
            {"citation": "Wong MR et al. Am J Public Health 2015;105:e81-e87 (PMID 25602861)", "doi": "10.2105/AJPH.2014.302404",
             "finding": "NYC models of inspection outcomes adjust for season and chain status; grading changed scores citywide."},
        ],
        "prediction": {
            "direction": "+",
            "magnitude": "Between-NTA SD of the adjusted log rate ratio (tau) 0.05 to 0.20; permutation p <= 0.01.",
            "support_if": "Permutation p <= 0.01 (10,000 draws, seed 20261113) AND tau >= 0.05.",
            "refute_if": "Permutation p > 0.10 (the NTAs are as even as random assignment of restaurants to NTAs).",
            "other": "p <= 0.01 with tau < 0.05 means statistically detectable but practically even and is unsettled under rule 2. Per rule 9 the p condition is re-checked with 100,000 draws and other seeds; if it is met under some and not others, it is neither met nor unmet.",
        },
        "plan": "Script analyses/restaurants/evenness_test.py at commit 48147d6. Fixed source: Underlay nyc/restaurant-inspections v1.0.0 (hash ulv2:07a7f08a0d5c85649920f8adc6946d27c17f5e2d75e9ee07c0ad4ae0fcc6739c), Manhattan inspections 2024-01-02 to 2026-06-09, chosen because the live table drops closed restaurants and revises recent violations downward (docs/underlay_drift.md). NTA by point in polygon (9nt8-h7nd); NTAs with < 20 restaurants dropped. Unit: Cycle Inspection / Initial Inspection; outcome: critical violation records. Null Poisson GLM as in the script docstring; statistic S = sum over NTAs of (sum(y - mu))^2 / sum(mu); null by permuting NTA labels across restaurants. tau from an NTA fixed-effects model, SE clustered by restaurant, method of moments. A companion frequency test (cycle initial inspections per restaurant-year) is computed by the same script; its result was seen by accident during a synthetic-outcome check of the script before this registration, so it is reported as exploratory and is not registered.",
        "alternatives": [
            "Inspector assignment: inspectors work in geographic teams, so an NTA's rate reflects its inspectors' stringency rather than its restaurants.",
            "Unmeasured restaurant mix: size, menu complexity, age of premises and owner experience vary by NTA and are not in the data; cuisine is a weak proxy.",
            "Building stock: older buildings have more pests (the most common critical violations are vermin), which is real hygiene, not harshness.",
            "Clientele and complaints: complaint-driven attention may differ by NTA.",
            "Adjudication: the snapshot holds violations before some hearings; dismissal rates may differ by NTA.",
        ],
        "prior": 0.55,
        "registrant": "claude (restaurants agent, 13 November 2026)",
        "script_commit": "48147d6",
    }


REG = {"restaurants-score-complaints": restaurants_score_complaints, "restaurants-nta-harshness": restaurants_nta_harshness}

if __name__ == "__main__":
    cid = sys.argv[1]
    print(claims.register(REG[cid]()))
