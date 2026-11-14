"""
Build the evidence slice for the Retrofit Evidence Explorer from retrofit.duckdb.

Outputs (data/):
  candidates.csv   one row per finding matched to an intervention group (with review columns)
  coverage.csv     per group x role: findings, studies, studies linked to a health outcome
  gap_grid.csv     per group x role x outcome group: distinct studies
  search_log.md    the exact search terms, exclusions and date (scope disclosure)
Run: python scripts/build_evidence.py   (from the repo root)
"""
import datetime as dt
import re
import duckdb
import pandas as pd

DB = "retrofit.duckdb"
OUT = "data"

# ---- 8 intervention groups: (intervention terms, exposure terms) -------------
GROUPS = {
    "Moisture & mould remediation": (
        r"(mou?ld|damp\w*|moisture|water[- ]damage)\w* \w* ?remediat\w*|remediat\w* (of )?(mou?ld|damp\w*|moisture|water damage)|\bleak repair|repair\w* (of )?leaks?\b|\bdehumidif\w*|mou?ld removal|moisture control|damp[- ]proof\w*",
        r"\bdamp\w*|\bmou?ld(s|y|iness)?\b|visible mou?ld|water[- ]damage|condensation|indoor fung\w*|household fung\w*|home moisture|moisture (in|damage)",
    ),
    "Building fabric (insulation, airtightness)": (
        r"(home|house|housing|dwelling|loft|wall|roof|floor|cavity|building|thermal)\w* insulat\w*|insulat\w* (of|in) (the )?(home|house|dwelling|building|walls?|roofs?|lofts?)|insulated (home|house|dwelling)s?|\bretrofit\w*|weatheri[sz]\w*|(home|house|dwelling|building)\w* airtight\w*|air[- ]tightness of|draught[- ]?proof\w*|draft[- ]?proof\w*|double[- ]glaz\w*|energy[- ]efficien\w* (home|hous|dwelling|retrofit|upgrade|improvement)\w*|home energy (upgrade|improvement)|energy upgrade",
        r"(home|house|dwelling|building) (air )?leakage",
    ),
    "Ventilation & source capture": (
        r"extractor fan|exhaust fan|range hood|cooker hood|heat[- ]recovery ventilation|\bmvhr\b|trickle vent|(building|home|house|dwelling|school|classroom|office)\w* ventilation system|ventilation system\w* (in|of) (the )?(home|house|dwelling|building|school|classroom|office)|(house|household|dwelling|building|school|classroom|kitchen|bathroom|bedroom|office|living)\w* \w* ?ventilat\w*",
        r"poor ventilation|inadequate ventilation|natural ventilation|ventilation (in|of) (the )?(home|house|household|dwelling|building|kitchen|room|classroom)|air exchange|air change rate|window opening|open(ing)? windows?",
    ),
    "Particle filtration": (
        r"air purifier\w*|air cleaner\w*|\bair filt\w*|\bhepa\b|portable (air )?filt\w*|indoor air filtration",
        r"indoor (pm\S*|particulate\w*|particle\w*|fine particle\w*)|household (pm\S*|particulate\w*)",
    ),
    "Clean cooking": (
        r"induction (hob|stove|cook\w*|range)|electric (stove|cook\w*|hob)|clean(er)? (cooking )?fuel\w*|improved (cook)?stove\w*|cookstove intervention|\blpg\b|liquefied petroleum gas|stove (replacement|intervention|exchange)",
        r"gas (cook\w*|stove\w*|hob\w*|range)|cooking fuel\w*|solid fuel\w*|biomass fuel\w*|biomass smoke|biomass (use|exposure|burning|cooking)|(household|domestic|indoor) cooking|cooking with (wood|coal|biomass|gas|kerosene|charcoal|dung)|charcoal|animal dung|crop residue|kerosene|household air pollution|indoor (no2|nitrogen dioxide|air pollution)|cooking (smoke|fume\w*)|unvented|unflued|wood ?stove\w*|wood burning|coal (stove|heating|use)",
    ),
    "Indoor temperature (heating & cooling)": (
        r"central heating|heating system\w*|heating type|type of heating|heating (fuel|source|method|equipment|appliance)\w*|home heating|space heat\w*|heat pumps?|electric heat\w*|floor heating|\bheaters?\b|thermostat\w*|warm homes?|winter fuel|fuel payment|air[- ]condition(er|ers|ing)\b|\bshading\b|\bshutters\b|cool roof\w*|green roof\w*|\bfan use|electric fans?",
        r"cold homes?|cold housing|cold (indoor|house)|indoor temperature\w*|bedroom temperature|living[- ]room temperature|overheat\w*|indoor heat|thermal comfort|excess cold|indoor cold|fuel poverty|energy poverty|energy insecurity",
    ),
    "Radon mitigation": (
        r"radon (mitigation|remediation|reduction|sump|test\w*|control)",
        r"\bradon\b",
    ),
    "Allergen & pest control (household)": (
        r"integrated pest management|(home|household|residential)\w* pest (control|management)|mattress (cover|encas\w*)|(bedding|pillow) encas\w*|impermeable cover\w*|allergen (avoidance|reduction|control|remov\w*)|home[- ]based (asthma|environmental)|asthma home visit\w*|home environmental (intervention|assessment)|environmental asthma intervention|carpet removal",
        r"dust mite\w*|house dust|cockroach\w*|mouse allergen\w*|rodent (infestation|allergen)\w*|pet allergen\w*|indoor allergen\w*|household allergen\w*|(house|home|household|indoor|mattress|airborne|dust|bedding)\w* endotoxin\w*|endotoxin\w* (in|from) (the )?(house|home|dust|mattress|bedding)",
    ),
}

EXCLUDE = (
    r"antifung|aspergill|mou?ld-active|ventilator|non-?invasive|diffusing capacity|\bdlco\b|\btlco\b|"
    r"ventilation[- ]perfusion|minute ventilation|alveolar ventilation|ventilatory|endotracheal|intensive care|"
    r"\bicu\b|fio2|hypoxic|hyperoxic|oxygenation|insulin|nasoalveolar|health-enhancing|asbestos|insulator|"
    r"perioperative|intraoperative|surgical|anesthe|anaesthe|labou?r induction|induction of (labou?r|anesthesia|remission)|"
    r"therapeutic hypotherm|cooling (therapy|cap|vest|blanket)|cryo|warming system|\bmurine\b|\bin vitro\b|"
    r"cell culture|culture medium|mou?ld (of|in) (the )?(teeth|dental)|hepatic|wound|orthodont|denture|prosthe|"
    r"cognitive remediation|remediation (for|of) (professionalism|skills)|soil moisture|soil remediation|face mask|"
    r"mechanical ventilation|hypercapni|kyphoscoli|round window|cochlear|hemofiltration|ultrafiltration|hemodia|"
    r"filtration rate|glomerular|cascade|hematolog|transplant|operating (room|theat)|scrot|microneedle|"
    r"\bleads?\b|endotoxin[- ](treated|infusion|challenge)|lipopolysacch|\blps\b|swine|room air condition|"
    r"feline|canine|legionella|zika|dengue|virus|hospital room|laminar|controlled environ|glaucoma|water filtration|daycare"
)

OUTCOMES = {
    "Asthma & wheeze": r"asthma|wheez",
    "Other respiratory": r"respirat|lung function|\blung\b|bronch|cough|copd|pneumon|rhinit|airway|breath|fev1|\bari\b|lower respiratory",
    "Allergy & skin": r"allerg|atop|eczema|dermatitis|sensiti[sz]ation|ige\b",
    "Mental health & sleep": r"depress|anxiety|mental|stress|sleep|well-?being|psycholog",
    "Cardiovascular": r"blood pressure|hypertens|cardio|heart|stroke|myocard",
    "Cancer": r"cancer|neoplasm|carcinoma|tumou?r|malignan",
    "Mortality & hospital use": r"mortality|death|hospital|admission|emergency|\bgp\b|primary care visit|healthcare use",
    "Indoor exposure measured": r"concentration|level\w* of|indoor (no2|pm|air)|humidity|temperature|mou?ld|radon|dust|allergen|damp",
}
# concept-route matching: graph concepts -> (group, role). Catches phrasings keywords miss.
CONCEPT_MAP = {
    "indoor air pollution": ("Clean cooking", "exposure"),
    "cooking": ("Clean cooking", "exposure"),
    "heating equipment": ("Indoor temperature (heating & cooling)", "intervention"),
    "air conditioning": ("Indoor temperature (heating & cooling)", "intervention"),
    "fungus": ("Moisture & mould remediation", "exposure"),
    "moisture": ("Moisture & mould remediation", "exposure"),
    "air filter": ("Particle filtration", "intervention"),
    "radon": ("Radon mitigation", "exposure"),
    "cockroach": ("Allergen & pest control (household)", "exposure"),
    "dust": ("Allergen & pest control (household)", "exposure"),
    "allergen": ("Allergen & pest control (household)", "exposure"),
}
UK = r"\b(UK|U\.K\.|United Kingdom|England|English|Scotland|Scottish|Wales|Welsh|Northern Ireland|Britain|British|London)\b"


def first(text, table):
    for k, rx in table.items():
        if rx.search(text):
            return k
    return "Other"


def main():
    con = duckdb.connect(DB, read_only=True)
    allterms = "|".join(f"(?:{i})|(?:{e})" for i, e in GROUPS.values())
    rows = con.sql(f"""
        SELECT a.*, s.doi, s.population_string, s.study_type
        FROM associations a LEFT JOIN studies s USING (study_id)
        WHERE regexp_matches(lower(coalesce(a.variable_1_name,'') || ' || ' || coalesce(a.variable_2_name,'')), '{allterms.replace("'", "''")}')
    """).df()
    print("raw keyword hits:", len(rows))

    exc = re.compile(EXCLUDE, re.I)
    g_int = {k: re.compile(v[0], re.I) for k, v in GROUPS.items()}
    g_exp = {k: re.compile(v[1], re.I) for k, v in GROUPS.items()}
    outc = {k: re.compile(v, re.I) for k, v in OUTCOMES.items()}
    ukre = re.compile(UK)

    recs = []
    for r in rows.itertuples(index=False):
        v1, v2 = str(r.variable_1_name or ""), str(r.variable_2_name or "")
        both = v1 + " || " + v2
        if exc.search(both):
            continue
        for g in GROUPS:
            side = None
            role = None
            for i, v in ((1, v1), (2, v2)):
                if g_int[g].search(v):
                    side, role = i, "intervention"
                    break
            if side is None:
                for i, v in ((1, v1), (2, v2)):
                    if g_exp[g].search(v):
                        side, role = i, "exposure"
                        break
            if side is None:
                continue
            other = v2 if side == 1 else v1
            recs.append({
                "group": g, "role": role,
                "matched_variable": v1 if side == 1 else v2, "other_variable": other,
                "outcome_group": first(other, outc),
                "association_id": r.system_id, "study_id": r.study_id, "pubmed_id": r.pubmed_id, "doi": r.doi,
                "statistic_type": r.statistic_type, "statistic_value": r.statistic_value,
                "ci_lower": r.ci_lower, "ci_upper": r.ci_upper, "p_value": r.p_value, "p_value_equality": r.p_value_equality,
                "population": r.population_string, "study_type": r.study_type,
                "is_trial": bool(re.search("trial|experiment", str(r.study_type or ""), re.I)),
                "is_uk": bool(ukre.search(str(r.population_string or ""))),
                "variable_1_name": v1, "variable_2_name": v2,
                # review columns for the research lead
                "review_status": "candidate", "component": "", "plain_language": "", "notes": "",
            })
    for rec in recs:
        rec["match_method"] = "keyword"
    have = {(r["group"], r["association_id"]) for r in recs}
    clabels = "','".join(CONCEPT_MAP)
    cids = con.sql(f"select system_id, lower(wikidata_label) lab from concepts where lower(wikidata_label) in ('{clabels}')").df()
    cmap = dict(zip(cids.system_id, cids.lab))
    ids = "','".join(cmap)
    crow = con.sql(f"""
        SELECT a.*, s.doi, s.population_string, s.study_type
        FROM associations a LEFT JOIN studies s USING (study_id)
        WHERE a.variable_1_concept_id IN ('{ids}') OR a.variable_2_concept_id IN ('{ids}')
    """).df()
    added = 0
    for r in crow.itertuples(index=False):
        v1, v2 = str(r.variable_1_name or ""), str(r.variable_2_name or "")
        if exc.search(v1 + " || " + v2):
            continue
        side = 1 if r.variable_1_concept_id in cmap else 2
        g, role = CONCEPT_MAP[cmap[r.variable_1_concept_id if side == 1 else r.variable_2_concept_id]]
        if (g, r.system_id) in have:
            continue
        have.add((g, r.system_id))
        other = v2 if side == 1 else v1
        recs.append({
            "group": g, "role": role, "matched_variable": v1 if side == 1 else v2, "other_variable": other,
            "outcome_group": first(other, outc), "association_id": r.system_id, "study_id": r.study_id,
            "pubmed_id": r.pubmed_id, "doi": r.doi, "statistic_type": r.statistic_type, "statistic_value": r.statistic_value,
            "ci_lower": r.ci_lower, "ci_upper": r.ci_upper, "p_value": r.p_value, "p_value_equality": r.p_value_equality,
            "population": r.population_string, "study_type": r.study_type,
            "is_trial": bool(re.search("trial|experiment", str(r.study_type or ""), re.I)),
            "is_uk": bool(ukre.search(str(r.population_string or ""))),
            "variable_1_name": v1, "variable_2_name": v2,
            "review_status": "candidate", "component": "", "plain_language": "", "notes": "", "match_method": "concept",
        })
        added += 1
    print("added via concept route:", added)
    ev = pd.DataFrame(recs).drop_duplicates(["group", "association_id"])
    ev.to_csv(f"{OUT}/candidates.csv", index=False)

    health = ev[~ev.outcome_group.isin(["Other", "Indoor exposure measured"])]
    cov = (ev.groupby(["group", "role"]).agg(findings=("association_id", "count"), studies=("study_id", "nunique"),
                                             trial_studies=("study_id", lambda s: s[ev.loc[s.index, "is_trial"]].nunique()),
                                             uk_studies=("study_id", lambda s: s[ev.loc[s.index, "is_uk"]].nunique()))
           .join(health.groupby(["group", "role"]).study_id.nunique().rename("health_linked_studies"))
           .fillna(0).astype(int).reset_index())
    cov.to_csv(f"{OUT}/coverage.csv", index=False)

    grid = ev.groupby(["group", "role", "outcome_group"]).study_id.nunique().rename("studies").reset_index()
    grid.to_csv(f"{OUT}/gap_grid.csv", index=False)

    with open(f"{OUT}/search_log.md", "w") as f:
        f.write(f"# Search log\n\nRun: {dt.datetime.now().isoformat(timespec='minutes')}\n\n")
        f.write("Source: System Public Graph, Harvard Dataverse v2.1 (doi:10.7910/DVN/7V6JDO), curated associations CSV.\n")
        f.write("Matching: case-insensitive regex on both variable names; clinical false matches excluded. "
                "Keyword search is not exhaustive; counts describe coverage, not evidence strength.\n\n")
        for g, (i, e) in GROUPS.items():
            f.write(f"## {g}\n- intervention terms: `{i}`\n- exposure terms: `{e}`\n\n")
        f.write(f"## Exclusions\n`{EXCLUDE}`\n")

    print(cov.to_string(index=False))


if __name__ == "__main__":
    main()
