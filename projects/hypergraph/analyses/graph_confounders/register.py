#!/usr/bin/env python
"""Register graph-confounders-commute-obesity BEFORE any covariate is queried.
Run once: ~/.venvs/nyc-concordance/bin/python analyses/graph_confounders/register.py"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import claims  # noqa: E402

L = json.loads((ROOT / "data/derived/graph/confounders/links_active-travel__obesity.json").read_text())


def item(label, role, read, summary):
    v = L[label]

    def split(rows):
        return {"n_read": len(rows), "plus": sum(r["direction"] == "+" for r in rows),
                "minus": sum(r["direction"] == "-" for r in rows),
                "significant": sum(bool(r["significant"]) for r in rows)}
    rids = sorted({r["relationship_id"] for r in v["a_side"] + v["b_side"]})
    return {"concepts": [label, "walking / public transport / motor car", "obesity / overweight / body mass index"],
            "concept_id": v["system_id"], "role_assigned": role, "rank_among_318_shared": v["rank"],
            "n_findings": {"with_exposure_side": v["findings_with_a"], "with_outcome_side": v["findings_with_b"]},
            "sign_split_exposure_side": split(v["a_side"]), "sign_split_outcome_side": split(v["b_side"]),
            "relationship_ids": rids[:12], "n_relationship_ids": len(rids),
            "pubmed_ids_read": read, "summary": summary, "source": "System API v1.0 (API only; Dataverse copy not on this machine, so in_csv unknown)"}


GE = [
    item("educational stage", "confounder", [28359269, 31336862],
         "Education is linked to walking for transport (highest vs lowest education RR 0.91, 0.82-1.01, Netherlands, PMID 28359269, abstract matches) and to obesity (less than tertiary education OR 3.36, 2.01-5.66, Switzerland, PMID 31336862; the graph files this under 'socioeconomic status' with no direction in the name)."),
    item("ethnicity", "confounder", [33801836, 33064936],
         "Ethnicity is linked to steps walked (IRR 0.53 in the graph; PMID 33801836 abstract says White students walked more steps, the number is not in the abstract) and to obesity (Indian vs Chinese women OR 4.81, Singapore, PMID 33064936, matches)."),
    item("population density", "confounder", [27807683, 26693941, 17465178, 21242327],
         "Density raises walking (OR 2.19 older adults Brazil, PMID 26693941, matches; OR 1.08 is an indirect effect through perceived land-use mix, PMID 27807683) and is linked to lower BMI in New York City itself (beta -0.25, p<0.001, Rundle et al. 2007, PMID 17465178, matches). PMID 21242327 found no effect (beta -1.02, -2.41 to 0.36)."),
    item("built environment", "confounder", [28614045, 31064107, 36942421, 29202849],
         "Built-environment measures are linked to transport walking (B = 19.24 min/week, PMID 28614045; OR 8.66, 5.89-12.72, PMID 29202849; both match) and to overweight (OR 0.72 in one low-SES city only, PMID 31064107). PMID 36942421 is stored as 'odds ratio -0.34', which is a difference, not a ratio."),
    item("crime", "confounder", [24552845, 19203354, 32491115, 27773973],
         "Fear of crime is linked to less walking (PMID 24552845, numbers not in the abstract; PMID 19203354 OR 1.64 is for the LOWEST fear tertile, so the graph's variable name reverses the sign) and neighbourhood safety to child obesity (PR 1.30, 1.08-1.56 for unsafe neighbourhoods, PMID 27773973; stored as a 'coefficient' named 'neighborhood safety'). The outcome-side relationships for the concept 'crime' returned no findings from the API; the obesity link was read under 'neighborhood characteristics'."),
    item("park", "confounder (secondary set)", [34768046, 33035547, 22989176],
         "Park availability is linked to walking with mixed sign (OR 0.65 for more park area, PMID 22989176, matches) and to obesity (highest vs lowest availability OR 0.57, 0.48-0.68, PMID 34768046, matches). PMID 33035547 is stored as 'presence of a neighborhood park -> obesity OR 1.32'; the abstract says children WITHOUT parks were more likely obese, so the graph's direction is reversed."),
    item("socioeconomic status", "confounder (the analyst's poverty adjustment is one measure of it)", [31336862],
         "Three findings on the exposure side and 110 on the outcome side; rank 75. This is the only support in the graph's shared list for the analyst's adjustment variable; 'poverty' and 'income' are not shared neighbours of this pair."),
    item("physical activity", "mediator, not adjusted", [23308135, 24918414],
         "Top-ranked shared concept (105 and 689 findings). Walking is physical activity, and activity lowers obesity (most active quintile OR 0.47, 0.37-0.60 for BMI above 25, PMID 23308135, matches). It lies on the path and is left out of the adjustment set, as are 'physical exercise' (rank 4) and 'sedentary lifestyle' (rank 23)."),
]

REC = {
    "id": "graph-confounders-commute-obesity",
    "kind": "confirmation",
    "statement": "Across New York City's 42 UHF neighbourhoods, the association between the share of workers who walk or cycle to work and adult obesity becomes at least one third smaller when the adjustment set is the one read from the System Public Graph's shared neighbours of walking and obesity (education, race and ethnicity, built environment, neighbourhood safety, with poverty kept as the socioeconomic measure) in place of the analyst's poverty-only adjustment.",
    "relates_to": "mob-active-commute-obesity",
    "graph_evidence": GE,
    "literature": [
        {"citation": "Flint E, Cummins S, Sacker A. BMJ 2014;349:g4887", "doi": "10.1136/bmj.g4887",
         "finding": "Active commuters have BMI about 1 kg/m2 lower than car commuters. The outcome of mob-active-commute-obesity used this to argue that 10 points more active commuting should lower neighbourhood obesity by well under 1 percentage point."},
        {"citation": "Rundle A et al. Am J Health Promot 2007;21(4 Suppl):326-34 (PMID 17465178)", "doi": None,
         "finding": "In New York City, population density, land-use mix and transit density are each associated with lower BMI after individual and neighbourhood adjustment. Found through the graph's 'population density' link."},
    ],
    "prediction": {
        "direction": "-",
        "magnitude": "Slope of adult obesity (percentage points) per 10 points of walk-or-bike commute share under the graph-derived set: between -4.0 and -1.0 (original poverty-adjusted estimate -5.97, 95% CI -7.81 to -4.12). That is an attenuation of 33% to 83% toward the individual-level research value (below 1 point per 10).",
        "support_if": "The point estimate of the primary model is between -4.0 and +0.5 (at least one third smaller in size than -5.97) AND the half-width of its 95% interval (HC3) is at most 3.0 points, so that the estimate is informative.",
        "refute_if": "The point estimate is -5.0 or more negative (attenuation under one sixth), whatever the interval. Between -5.0 and -4.0, or half-width above 3.0, or an estimate above +0.5, the verdict is unsettled.",
    },
    "plan": "Unit: 42 UHF neighbourhoods. Data: EHDP at commit 547482b9df589006543e13e8cdf6546e00ed9998 through analyses/mobility/ehdp.py. Outcome, exposure and poverty exactly as in mob-active-commute-obesity (indicator 2063 measure 506, mean of 2017-2019; indicator 2415 measures 1304 + 1307, 2015-19; indicator 103 measure 221, 2015-19). New covariates, chosen from the graph's shared neighbours and matched to EHDP measures by reading only the EHDP metadata file (no values): education = indicator 2334 measure 1025, percent graduated high school, ACS 2015-19; race and ethnicity = indicator 2325 measures 988, 989, 987 (percent Black, Hispanic, Asian; White is the reference), ACS 2015-19; built environment and population density = indicator 2133 measure 673, walkability index, 2011 (the only period); crime and safety = indicator 2073 measure 1058, percent who perceive the neighbourhood as safe, mean of 2015 and 2016 (the only periods). Primary model: OLS of obesity on active share, poverty, high-school graduation, percent Black, percent Hispanic, percent Asian, walkability and perceived safety; HC3 standard errors; slope per 10 points. Secondary, reported and not deciding: (a) the same plus park access (indicator 2388 measure 1224, 2017) and unemployment (indicator 2337 measure 1032, 2015-19); (b) leave-one-covariate-out, to see which graph-named variable moves the estimate; (c) the analyst's own alternatives for comparison (poverty only; poverty and borough); (d) the model with the graph's mediator added (recent exercise, indicator 2060 measure 500, mean of 2017-2019), labelled as over-adjustment; (e) R2 of the active share on the covariates, as a collinearity check. Age structure and sex, which the graph also names, have no UHF42 measure in EHDP and are left out; this is stated as a limit. Missing values: complete cases, with n reported.",
    "alternatives": [
        "Collinearity: walkability and the walk-to-work share measure nearly the same thing across 42 areas, so the adjusted slope may shrink only because its variance is inflated. The half-width condition and the leave-one-out table address this.",
        "Over-adjustment: walkability may be a cause of walking to work only, with no other route to obesity, in which case adjusting for it removes real exposure variation. The leave-one-out result without walkability is reported.",
        "Any eight covariates would attenuate a slope across 42 units. The comparison with the analyst's borough adjustment (-6.62, no attenuation) is the available check; a random-covariate comparison is not registered.",
        "Residual composition: income above the poverty line, age and selection into walkable neighbourhoods remain unmeasured.",
    ],
    "prior": 0.5,
    "registrant": "Claude (graph confounders experiment), 12 November 2026",
    "already_seen": "Seen before registration: data/derived/mobility/active_commute_obesity_uhf42.csv and active_commute_results.json (obesity, walk and bike shares, poverty and borough for all 42 UHFs; unadjusted slope -6.27, poverty-adjusted -5.97, with borough -6.62, without Manhattan -11.56; correlation of poverty with active share -0.08). Poverty at UHF42 also appears in the asthma and rodent files. Not seen by this registrant, and not queried anywhere in the repo's scripts at UHF42: high-school graduation, race and ethnicity, walkability index, perceived safety, park access, unemployment, recent exercise. Only the EHDP metadata (indicator and measure names, geographies, period ids) was read to choose them. The registrant's general knowledge that Manhattan's walk-to-work neighbourhoods are highly educated and that obesity in New York is higher in Black and Hispanic neighbourhoods informed the prior.",
}

if __name__ == "__main__":
    print(claims.register(REC))
