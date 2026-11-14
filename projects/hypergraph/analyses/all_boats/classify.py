"""Step 3: assign each association to an outcome domain and a benefit or harm sign.

The graph stores the sign between two variables as named, not which one is the exposure.
This script therefore (1) keeps an association only when the other variable's name falls
in one of eight outcome domains, (2) sets the polarity of the outcome (is more of it good
or bad) and of the exposure (is the variable the feature or its absence) from keywords,
and (3) calls a finding beneficial when sign x outcome polarity x exposure polarity > 0.
These are the unverified "raw" cells. verify_sample.py picks findings to read.
"""
import re, sys
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/derived/all_boats"
sys.path.insert(0, str(Path(__file__).parent))
from interventions import INTERVENTIONS

DOMAINS = [  # first match wins
    ("housing_cost", r"\brents?\b|rental (price|cost)|property value|hous(e|ing) price|home (value|price)|gentrif|displacement of resid|residential displacement|evict|housing (cost|afford)|sale price|land value"),
    ("mortality", r"mortalit|\bdeaths?\b|life expectancy|surviv|fatal"),
    ("crime_safety", r"crime|violen|shooting|homicide|assault|\bguns?\b|firearm|burglar|robber|theft|arrest|injur|crash|collision|perceived safety|fear of|victimi|disorder(ly)? conduct|vandal|police|stop-and-frisk|drowning"),
    ("education", r"school (attend|absen|perform|achiev|readiness|complet)|academic|test score|reading (score|abilit|skill|profic)|math|graduat|literacy|absentee|educational (attain|achiev|outcome)|grade point|cognitive development|kindergarten readiness"),
    ("income_employment", r"\bincome|employ|earnings|\bwages?\b|poverty|job (access|loss)|economic (mobility|activity|status)|labor|labour|productivity|business|retail sales|food insecur"),
    ("social_ties", r"social (cohes|capital|support|ties|isolat|interact|network|contact|participat|connect|trust|engage)|lonel|sense of (community|belonging)|neighbo(u)?r(ing|liness)|civic|collective efficacy|community (engage|attach|participat)|belonging|trust"),
    ("mental_health", r"depress|anxi|distress|\bstress|mental|well-?being|suicid|psych|dementia|cognit|adhd|attention deficit|autis|happiness|life satisfaction|mood|sleep|quality of life|bipolar|schizo|self-harm|burnout|substance|opioid|alcohol|drug"),
    ("physical_health", r"asthma|obes|overweight|\bbmi\b|body mass|diabet|hypertens|blood pressure|cardiovasc|heart|coronary|stroke|cancer|birth ?weight|preterm|gestation|physical(ly)? activ|walking|exercise|self-rated|self-reported health|general health|respirat|lung|wheez|allerg|infect|covid|heat (stress|illness|stroke|exhaust|related)|hospital|emergency (department|room|visit)|blood lead|lead level|lead poison|fruit|vegetable|diet|nutrition|myocard|\bami\b|disease|illness|morbid|health (status|outcome)|sunburn|myopia|cholesterol|metabolic|frailty|symptom|steps|sedentary|cycling|active (travel|commut|transport)|smok|tobacco|vaccin|dengue|malaria|tubercul|legion|pneumon"),
]
GOOD = r"physical(ly)? activ|walking|\bwalk\b|exercise|well-?being|quality of life|life satisfaction|happiness|surviv|life expectancy|birth ?weight|sleep (duration|quality)|cognitive (function|perform|develop|abilit)|cognition|test score|achiev|attend|graduat|literacy|readiness|reading|math|academic|employ|\bincome|earnings|wage|economic|productiv|business|retail|social (cohes|capital|support|ties|interact|network|contact|participat|connect|trust|engage)|sense of|neighbo(u)?r(ing|liness)|civic|collective efficacy|community (engage|attach|participat)|belonging|trust|perceived safety|safety|fruit|vegetable|lung function|\bfev|health (status)|self-rated health|general health|mental health|resilien|steps|cycling|active (travel|commut|transport)|vaccin|cessation|quit|smoke-free|job access|restor"
FLIP = r"\bpoor|\blow\b|insufficien|lack|fair to poor|\bnot\b|\bno\b|inadequa|unemploy|loss|absen|decline|impair|difficult|problem|disorder|deficit|short sleep|inactiv|\bless\b|reduced|worse|delay|illness|symptom|distress|burden|insecur|isolat|lonel|poverty|absentee"
EXP_NEG = r"\black\b|distance (to|from)|\bno\b|without|absence|\bfar\b|fewer|\blow\b|\bpoor\b|inadequa|substandard|\bvacant|abandon|blight|desert|\bloss\b|removal|unmaintained|limited|not having|non-?use|unavailab|proximity to (bus|transit|rail)? ?stop.*distance|closure|closing|problems?\b|deficien|disrepair|damp|mold|mould|cold hom"
EXP_POS_OVERRIDE = r"remediat|greening|maintained|abatement|repair|improv|restor|intervention|renovat|program|cleanup"


def domain(name: str):
    n = (name or "").lower()
    for d, pat in DOMAINS:
        if re.search(pat, n):
            return d
    return None


def out_pol(name: str, dom: str) -> int:
    n = (name or "").lower()
    if dom == "housing_cost":
        return -1  # higher rents and prices are counted as a harm to residents who rent
    good = bool(re.search(GOOD, n))
    flip = bool(re.search(FLIP, n))
    if good and not flip:
        return 1
    return -1


def exp_pol(name: str) -> int:
    n = (name or "").lower()
    if re.search(EXP_NEG, n) and not re.search(EXP_POS_OVERRIDE, n):
        return -1
    return 1


def main():
    a = pd.read_csv(OUT / "associations.csv")
    a = a[a.intervention.isin(INTERVENTIONS)].copy()
    # an "outcome" that is itself a variable of the same feature is not an outcome
    a["domain"] = a.outcome_var.map(domain)
    n_all = len(a)
    a = a[a.domain.notna()].copy()
    a["out_pol"] = [out_pol(n, d) for n, d in zip(a.outcome_var, a.domain)]
    a["exp_pol"] = a.exposure_var.map(exp_pol)
    s = a.direction.map({"+": 1, "-": -1})
    a["effect"] = (s * a.out_pol * a.exp_pol).map({1: "benefit", -1: "harm"}).fillna("unsigned")
    a.to_csv(OUT / "associations_classified.csv", index=False)
    a["study"] = a.pubmed_id.fillna(a.study_id).astype(str)
    g = a.groupby(["intervention", "domain"]).agg(
        n_studies=("study", "nunique"), n_findings=("study", "size"),
        benefit=("effect", lambda x: int((x == "benefit").sum())), harm=("effect", lambda x: int((x == "harm").sum())),
        unsigned=("effect", lambda x: int((x == "unsigned").sum()))).reset_index()
    g.to_csv(OUT / "matrix_raw.csv", index=False)
    print(n_all, "associations;", len(a), "in an outcome domain")
    print(g.pivot(index="intervention", columns="domain", values="n_studies").fillna(0).astype(int).to_string())


if __name__ == "__main__":
    main()
