#!/usr/bin/env python
"""Register graph-confounders-trees-surftemp and graph-confounders-surftemp-ed BEFORE any covariate is queried.
Run once: ~/.venvs/nyc-concordance/bin/python analyses/round2_heat_confounders/register.py"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import claims  # noqa: E402

SRC = "System API v1.0, read from data/cache/sysgraph and data/derived/graph/confounders/links_*.json; Dataverse copy not on this machine, so in_csv unknown"
SEEN_COMMON = ("Seen before registration by this registrant: data/derived/heat/bridge_cd.csv and bridge_nta.csv (every value of street-tree density, "
               "surface temperature, vegetative cover, heat ED rate, heat hospitalization rate, poverty, percent Black and AC, by community district "
               "and by NTA), bridge_results.json, and the outcomes of heat-trees-surftemp, heat-surftemp-ed, heat-trees-ed-chain and "
               "heat-trees-canopy-within-nta. The registrant recomputed the two original estimates from bridge_cd.csv before registering. "
               "PLUTO (64uk-42ks, version 26v2) queries already in data/cache/socrata are citywide sums by land use and by year built, lot area by "
               "2020 tract, land use and owner type (for nbhd-vacant-shootings), and single lots; none is grouped by community district or 2010 tract "
               "and none holds building area by area. The EHDP file for indicator 2325 (race and total population) is on disk because the commuting "
               "re-analysis read its UHF42 rows; its CD and NTA rows have not been read. The file for indicator 2112 (traffic density) is on disk "
               "for the concordance matrix at UHF42; its CD rows have not been read by this registrant. Indicator 2146 (older adults living alone) "
               "has not been downloaded. Only EHDP metadata (measure names, geographies, periods) and the PLUTO column list were read to choose the "
               "covariates. The registrant's general knowledge of New York (Manhattan is the densest borough, has many one-person households, and "
               "the original outcome notes say that hot-surface districts are central) informed the priors.")

A = {
    "id": "graph-confounders-trees-surftemp",
    "kind": "confirmation",
    "relates_to": "heat-trees-surftemp",
    "statement": "Across New York City community districts, the positive adjusted association between street-tree density and daytime surface temperature (+0.50 F per SD, the opposite of the research direction) becomes smaller by at least 0.3 F per SD when population density, built-up area and road area, the common causes named by findings in the System Public Graph, are added to the analyst's adjustment set of poverty and percent Black.",
    "graph_evidence": [
        {"association_id": "CQuKL8Vr5G", "relationship_id": "WLNXo1tGFr|sSuplgYnDQ", "concepts": ["population density", "surface temperature"],
         "n_findings": 1, "n_studies": 1, "direction": "+",
         "summary": "Population density and land surface temperature, Pearson r = 0.8206, Prizren, Kosovo, Landsat 8 (doi 10.22630/srees.2324). No PubMed id; the Crossref abstract gives r = 0.8206, so the stored value matches. The study compares pixels of one municipality from countryside to town centre.",
         "pubmed_ids": [], "source": SRC},
        {"association_id": "w_1tAHxbUU", "relationship_id": "WLNXo1tGFr|UbF0-c8zHb", "concepts": ["population density", "urban heat island"],
         "n_findings": 1, "n_studies": 1, "direction": "+",
         "summary": "Population density and urban heat island across districts of Ho Chi Minh City, R2 = 0.64 (doi 10.46326/jmes.2021.62(5).06). No PubMed id; the Crossref abstract gives R2 = 0.64. The graph stores no direction; the abstract describes an increase.",
         "pubmed_ids": [], "source": SRC},
        {"association_id": "9xCRp0g69S, sVI20gcmIM, hKUE8RwXOV", "concepts": ["urban built-up area", "road area", "urban heat island"],
         "n_findings": 3, "n_studies": 1, "direction": "+",
         "summary": "One study of Xiamen 2001-2007 (conference paper, doi 10.1109/rsete.2011.5965025): coefficients on urban heat island of +2.333 for urban built-up area, +1.291 for road area and -5.602 for urban greenland. No PubMed id and no abstract on Crossref, so the numbers and their units could not be checked. The three variables are grounded to the concepts 'urban population' or to no concept; they were found by reading variable names under 'urban heat island'.",
         "pubmed_ids": [], "source": SRC},
        {"concepts": ["poverty", "percent Black", "surface temperature", "green cover"], "n_findings": 0, "n_studies": 0, "direction": "0",
         "summary": "The analyst's two covariates are not shared neighbours of green cover and temperature in the graph (docs/graph_experiments.md, confounders section).",
         "pubmed_ids": [], "source": SRC},
    ],
    "literature": [
        {"citation": "Ziter CD et al. PNAS 2019;116:7575-7580", "doi": "10.1073/pnas.1817561116",
         "finding": "Canopy cools and impervious cover warms daytime air; the two interact. Impervious cover is the common cause the original registration named and did not adjust for."}],
    "prediction": {
        "direction": "-",
        "magnitude": "The change in the slope of surface temperature on z(log live street trees per km2) when log population density, built-up share and road share are added is between -0.3 and -1.2 F per SD, so the slope under the graph set lies between -0.7 and +0.2 F per SD (original +0.50, 95% CI -0.03 to +1.04, n = 55). Derivation: on a standardised scale the one-confounder formula is b_adj = (r_xy - r_xz*r_zy)/(1 - r_xz^2). r_xy = 0.28 is seen (tree density and surface temperature across the 55 districts, SD of temperature 2.03 F). The graph gives r_zy = 0.8 for population density and surface temperature (r = 0.82; R2 = 0.64). r_xz, the correlation of street-tree density with population density, has not been queried; for r_xz between 0.3 and 0.6 the formula gives b_adj between +0.04 and -0.31 SD, that is +0.1 to -0.6 F, a change of -0.4 to -1.1 F. The band is widened at both ends because the graph's two correlations come from study areas that run from farmland to city centre, a wider range of density than New York's districts, so the correlation here is expected to be lower than 0.8, and because built-up and road area are added as well.",
        "support_if": "All three hold in the primary model: (a) the change in the point estimate (graph set minus original, same districts) is -0.30 F per SD or more negative; (b) the 95% percentile interval of the change from a paired bootstrap over districts (5000 resamples, both models refitted on each) excludes zero; (c) the largest variance inflation factor among the regressors of the graph-set model is 10 or less.",
        "refute_if": "The change is positive and the bootstrap interval of the change excludes zero (the graph's covariates move the slope further from the research direction), with the largest VIF 10 or less.",
        "otherwise": "Unsettled. no_test if the largest VIF exceeds 10, or if fewer than 50 districts have all variables. Whether the slope under the graph set is negative with an interval excluding zero (which would reverse the reading of heat-trees-surftemp) is reported and does not decide this verdict.",
    },
    "plan": "Unit: community districts with the original covariates (55 expected). Outcome, exposure, poverty and percent Black are read unchanged from data/derived/heat/bridge_cd.csv. New covariates. Population density: EHDP indicator 2325 measure 992 (total population, ACS 2015-19, CD) divided by the district's land area from EHDP CD.geojson as computed in analyses/heat/bridge.py, in logs. Built-up area: building footprint share of land, the sum over tax lots of bldgarea/numfloors (lots with numfloors > 0 and bldgarea > 0) from PLUTO 64uk-42ks grouped by cd, divided by land area, in percent. Road area: the share of land outside tax lots, 100*(1 - sum of lotarea over lots that are not submerged (lottype not 9) / land area); streets and sidewalks are the land that is in no tax lot. Values are used as computed; districts with a share below 0 or above 60 are listed. Primary model: OLS of surface temperature on z(log tree density), poverty, percent Black, log population density, built-up share and road share, HC3 standard errors; the original model is refitted on the same rows; the change and its paired bootstrap interval (seed 20261113) are computed by analyses/round2_heat_confounders/reanalysis.py, written before this registration and not yet run. VIF is computed for every regressor of the graph-set model with an intercept. Secondary, reported and not deciding: each covariate alone; log built floor area per km2 in place of footprint share; EHDP traffic density (indicator 2112 measure 643, 2019, CD, log) in place of road share; vegetative cover (EHDP 2143) as the exposure; and the same primary model at NTA2010 (n about 190; original +0.44, 95% CI +0.15 to +0.73), with PLUTO grouped by borocode and ct2010 and assigned to NTAs through the 2010 tract-to-NTA equivalency table (8ius-dhrr) and population from indicator 2325 at NTA2010. Descriptive: the share of the tract-level variance of footprint share and floor-area ratio that lies between NTAs, to say what the neighbourhood fixed effects of heat-trees-canopy-within-nta remove. Timing: trees are from 2015, the Landsat scene from 17 July 2018, population from 2015-19 and PLUTO from version 26v2 (2026); buildings completed after 2018 are counted, which is a limit.",
    "power": "The original slope has HC3 SE 0.272 (n = 55). The SE of the change is about sqrt(SE_graph^2 - SE_original^2). If the graph covariates explain half of the variance of tree density (VIF 2) and none of the residual variance of temperature, SE_graph is 0.39 and the SE of the change 0.27, so the smallest change detectable with 80% power at the 5% level is about 0.76 F per SD; with VIF 1.5 it is 0.54. The lower part of the predicted band (changes of -0.3 to -0.5) would therefore probably end as unsettled at district level. At NTA2010 the original SE is 0.148 and the same calculation gives a detectable change of 0.41 (VIF 2), which is why the NTA model is registered as a secondary. The test can fail in three ways: the change can be small, it can be positive (adding borough terms to the original raised the slope to +0.61), or the covariates can be too collinear.",
    "alternatives": [
        "Mechanical coupling: street trees per km2 of land is street trees per km2 of street multiplied by the road share, so adjusting for road share changes the exposure into trees per unit of street. A fall in the slope then reflects a better exposure measure more than removed confounding. The road-only secondary model shows how much of the change this accounts for.",
        "Over-adjustment: built-up share and vegetative cover are nearly complements, and built-up surface is part of what a tree-poor district is. The footprint share may absorb the effect of having few trees.",
        "Any three district covariates move a slope across 55 units. The poverty and percent Black adjustment moved it by 0.01.",
        "PLUTO is eight years later than the Landsat scene.",
    ],
    "prior": 0.4,
    "registrant": "Claude (round 2, graph-derived adjustment sets for heat), 12 November 2026",
    "already_seen": SEEN_COMMON + " Seen for this claim: unadjusted slope +0.50 (-0.04 to +1.03), adjusted +0.50 (-0.03 to +1.04), with borough terms +0.61, vegetative cover -0.62 (-1.17 to -0.07), NTA adjusted +0.44 (+0.15 to +0.73); Spearman correlations of tree density with vegetative cover -0.23 and with poverty +0.10.",
    "precedence": "Verdict by concord.claims.PRECEDENCE rules 1 to 4.",
}

B = {
    "id": "graph-confounders-surftemp-ed",
    "kind": "confirmation",
    "relates_to": "heat-surftemp-ed",
    "statement": "Across New York City community districts, adding the share of older adults who live alone, the common cause that the System Public Graph's findings name for temperature and heat illness, to the analyst's adjustment set (poverty, percent Black, air conditioning) changes the negative association between surface temperature and the heat-stress emergency department rate (-10.3% per 1 F) by less than 2.5 percentage points, and the association stays negative.",
    "graph_evidence": [
        {"association_id": "rzWTS1XpNk", "relationship_id": "aU6CVgYD7i|dINFs04idR", "concepts": ["home environment (living alone)", "heat illness"],
         "n_findings": 1, "n_studies": 1, "direction": "+",
         "summary": "Living alone and heat-related death, OR 8.1 (1.4 to 48.1), case-control study of the 1999 Chicago heat wave, 63 cases and 77 controls matched on neighbourhood and age (Naughton et al. 2002). Checked against the PubMed abstract on 12 Nov 2026: matches. The same abstract gives a working air conditioner OR 0.2 (0.1 to 0.7) as the strongest protective factor, which supports the analyst's AC covariate although the graph does not list air conditioning as a shared neighbour of this pair.",
         "pubmed_ids": [11988377], "source": SRC},
        {"association_id": "0PyCQfb-eu", "relationship_id": "aU6CVgYD7i|rYCo7LTyzN", "concepts": ["home environment (living alone)", "heat wave death"],
         "n_findings": 1, "n_studies": 1, "direction": "+",
         "summary": "Living alone and death during the 2009 Adelaide heat wave, adjusted OR 42.31 (2.3 to 792.8), 82 deaths and 164 controls matched on age and sex, median age 77.5 (Zhang et al. 2017). Checked against the PubMed abstract: matches. The abstract also gives air conditioning in bedrooms, adjusted OR 0.004.",
         "pubmed_ids": [27221967], "source": SRC},
        {"concepts": ["age group", "heat illness"], "n_findings": 1, "n_studies": 1, "direction": "+",
         "summary": "Age group is a shared neighbour (one readable finding, value 2.41, PMID 33176353, not relied on here). The city outcome is an age-adjusted rate, so age is handled in the outcome and no age covariate is added.",
         "pubmed_ids": [33176353], "source": SRC},
    ],
    "literature": [
        {"citation": "Madrigano J et al. Environ Health Perspect 2015;123:672-678", "doi": "10.1289/ehp.1408178",
         "finding": "New York City heat-wave deaths were more likely in areas with higher surface temperature and less green space (case-only)."}],
    "prediction": {
        "direction": "-",
        "magnitude": "The slope stays negative: between -12.8% and -9.8% per 1 F under the graph set (original -10.3%, 95% CI -17.5 to -2.6, n = 54), a change between -2.5 and +0.5 percentage points, central guess -0.5. Derivation from the graph's sizes: if a share p of older adults lives alone and living alone multiplies their heat-illness risk by the odds ratio (8.1 or 42.3, treated as risk ratios for a rare outcome), the rate among older adults is proportional to 1 + p(OR - 1); raising p from 25% to 35% raises it by 26% (OR 8.1) or 36% (OR 42.3), about 0.023 to 0.031 in log rate per point. Older adults are assumed to carry 15% to 25% of an age-adjusted heat ED rate, so the all-age log rate rises by about 0.003 to 0.008 per point of living alone. The change in the temperature coefficient is minus that number times the partial slope of living alone on surface temperature. That partial slope has not been queried; with a between-district SD of living alone of 6 to 8 points, an SD of temperature of 2.0 F and a partial correlation of at most 0.4 in size it is at most 1.6 points per F, giving a change of at most 1.3% per F in size, and 5% only if the odds ratio applied to residents of every age. The sign is taken as negative because one-person households among older adults are expected to be more common in the central districts, which are the hot-surface districts.",
        "support_if": "All hold in the primary model: (a) the change in the point estimate (graph set minus original, same districts, percent per 1 F) is between -2.5 and +0.5; (b) the 95% paired-bootstrap interval of the change lies inside -5.2 to +5.2, half of the original estimate, so that the test excludes that living alone accounts for half of the slope; (c) the upper 95% limit (HC3) of the slope under the graph set is below 0; (d) the largest VIF is 10 or less.",
        "refute_if": "The change is +3.4 or more (the slope loses a third or more of its size) or -5.2 or less, and the bootstrap interval of the change excludes zero, with the largest VIF 10 or less.",
        "otherwise": "Unsettled. no_test if the largest VIF exceeds 10 or fewer than 50 districts have all variables.",
    },
    "plan": "Unit: community districts with a heat ED rate and the original covariates (54 expected). Outcome (log age-adjusted heat-stress ED rate, EHDP 2443 measure 1405, 2018-22), exposure (surface temperature, EHDP 2141) and the three original covariates are read unchanged from data/derived/heat/bridge_cd.csv. New covariate: EHDP indicator 2146 measure 693, percent of people aged 65 and over who live alone, ACS 2015-19, CD. Primary model: OLS of log rate on surface temperature, poverty, percent Black, AC and living alone, HC3 standard errors, reported as percent change per 1 F; the original model refitted on the same rows; change and paired bootstrap interval (5000 resamples, seed 20261113) by analyses/round2_heat_confounders/reanalysis.py, written before this registration and not yet run. Secondary, not deciding: the primary model plus the three built-form covariates of graph-confounders-trees-surftemp (log population density, footprint share, road share); those three without living alone; and at NTA2010 the heat hospitalization rate from hvi-nta.csv on surface temperature with the original NTA covariates plus living alone at NTA2010 (original -3.9%, -7.2 to -0.4). The coefficient of living alone is reported with its interval and compared with the 0.003 to 0.008 per point derived from the graph.",
    "power": "The original coefficient has HC3 SE 0.0424 log units per F (n = 54). If living alone has a partial R2 of 0.1 with surface temperature the SE of the change is about 0.014, and the smallest detectable change is about 3.9 percentage points; with partial R2 0.05 it is 2.7. A change of one third of the slope (3.4 points) is therefore near the limit of detection, and condition (b) can fail if living alone is strongly related to surface temperature. The prediction is of a small change, so the test fails if living alone turns out to be a strong ecological correlate of both variables, which is possible: in New York older adults living alone are common in affluent central districts with low heat ED rates.",
    "alternatives": [
        "Ecological sign reversal: the individual-level finding is that living alone raises risk, but across districts the share living alone may mark affluent central districts with low ED use, so its coefficient may be negative and the change positive.",
        "The graph's findings are for death among mostly older people during two heat waves; the outcome here is ED visits at all ages over five summers, many of them among outdoor workers.",
        "The same two abstracts name air conditioning as the strongest protective factor, which the analyst already included; the graph-derived addition may carry little beyond it.",
    ],
    "prior": 0.5,
    "registrant": "Claude (round 2, graph-derived adjustment sets for heat), 12 November 2026",
    "already_seen": SEEN_COMMON + " Seen for this claim: unadjusted -6.6% (-13.6 to +1.0), adjusted -10.3% (-17.5 to -2.6), percent Black +10.9% per 10 points in the adjusted model, NTA hospitalizations adjusted -3.9% (-7.2 to -0.4); Spearman correlations of surface temperature with AC -0.18 and with poverty +0.22.",
    "precedence": "Verdict by concord.claims.PRECEDENCE rules 1 to 4.",
}

if __name__ == "__main__":
    for rec in (A, B):
        print(claims.register(rec))
