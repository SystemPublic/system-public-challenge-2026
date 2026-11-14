"""Graph side: findings that link two claim ends, their direction, and whose population the studies describe."""
import re

import numpy as np
import pandas as pd

RATIO = {"odds_ratio", "adjusted_odds_ratio", "hazard_ratio", "adjusted_hazard_ratio", "relative_risk_ratio",
         "incident_rate_ratio", "prevalence_ratio"}
SIGNED = {"mean_difference_unstandardized", "mean_difference_standardized", "coefficient", "pearson_r",
          "spearman_correlation", "risk_difference", "elasticity", "t_test"}

# A variable named "lack of X" or "low X" measures the opposite of X.
NEGATION = re.compile(r"\b(no|non|not|lack of|lacking|without|absence of|absent|low|lower|lowest|reduced|reduction|"
                      r"less|decreased|inadequate|insufficient|poor|loss of|deficit)\b")

HEAT_STUDY_RX = (r"(heat ?wave|extreme heat|heat exposure|heat index|high (ambient )?temperature|ambient temperature|"
                 r"apparent temperature|hot (day|weather|season|summer)|extreme temperature|heat stress|"
                 r"temperature exposure|daily (mean |maximum |max )?temperature|diurnal temperature|"
                 r"outdoor temperature|urban heat)")

# --- population tags -------------------------------------------------------------------------------------------
NYC = re.compile(r"new york city|\bnyc\b|\bmanhattan\b|\bbrooklyn\b|\bbronx\b|\bqueens\b(?!land)|staten island|"
                 r"\bharlem\b", re.I)
REGIONS = [
    ("US", r"\bu\.?s\.?a?\b|united states|\bamerican\b|medicare|medicaid|nhanes|new york|chicago|philadelphia|boston|"
           r"los angeles|california|texas|florida|maryland|georgia|arizona|massachusetts|ohio|michigan|carolina|"
           r"houston|phoenix|atlanta|detroit|baltimore|seattle|washington, d|minnesota|wisconsin|colorado|oregon|"
           r"pennsylvania|new jersey|virginia|tennessee|kentucky|louisiana|missouri|indiana|illinois|veterans"),
    ("China", r"china|chinese|beijing|shanghai|guangzhou|wuhan|nanjing|shenzhen|hong kong|taiwan|taipei|jinan|"
              r"hangzhou|chengdu|anhui|guangdong|jiangsu|zhejiang|shandong|hubei|hunan|sichuan|yunnan"),
    ("Europe", r"europe|england|\buk\b|united kingdom|britain|british|london|scotland|wales|ireland|france|french|"
               r"paris|germany|german|italy|italian|spain|spanish|madrid|barcelona|netherlands|dutch|sweden|swedish|"
               r"denmark|danish|finland|finnish|norway|norwegian|switzerland|swiss|portugal|greece|belgium|austria|"
               r"poland|czech|hungary|romania|stockholm"),
    ("East Asia other", r"korea|seoul|japan|japanese|tokyo|osaka"),
    ("Australia", r"australia|queensland|sydney|melbourne|adelaide|brisbane|perth|new zealand"),
    ("Other place", r"india|brazil|mexic|iran|israel|africa|kenya|uganda|vietnam|thailand|bangladesh|pakistan|canada|"
                    r"ontario|toronto|chile|peru|colombia|saudi|turkey|egypt|nigeria|ghana|ethiopia|nepal|indonesia|"
                    r"malaysia|singapore|philippines|argentina|kuwait|qatar|emirates"),
]
REGIONS = [(k, re.compile(v, re.I)) for k, v in REGIONS]
ANIMAL = re.compile(r"\b(cows?|cattle|heifers?|pigs?|sows?|swine|piglets?|chickens?|broilers?|hens?|poultry|mice|"
                    r"mouse|rats?|sheep|ewes?|lambs?|goats?|buffalo|fish|calves|dairy|bulls?|rabbits?|horses?|quail|"
                    r"ducks?|zebrafish|drosophila|primates?|monkeys?|dogs?|cats?|camels?|steers?|boars?|gilts?)\b", re.I)
OLDER = re.compile(r"aged? (6[05]|7[05]|8[05])|older (adults|people|persons|population)|elderly|65 (and|or) (over|older)|"
                   r"65 years|over 65|medicare|nursing home", re.I)
LOW_INCOME = re.compile(r"low[- ]income|poverty|poor (households|families|neighbo)|deprived|deprivation|"
                        r"disadvantaged|medicaid|homeless|food insecur|public housing", re.I)
BLACK_HISP = re.compile(r"\bblack\b|african[- ]american|hispanic|latin[oax]", re.I)
URBAN = re.compile(r"\bcit(y|ies)\b|urban|metropolitan|municipal", re.I)


def tag_population(text):
    t = text if isinstance(text, str) else ""
    nyc = bool(NYC.search(t))
    region = "NYC" if nyc else next((k for k, rx in REGIONS if rx.search(t)), "No place stated")
    human = not ANIMAL.search(t)
    tags = {"region": region, "human": human, "nyc": nyc, "us": nyc or region == "US",
            "older": bool(OLDER.search(t)), "low_income": bool(LOW_INCOME.search(t)),
            "black_hispanic": bool(BLACK_HISP.search(t)), "urban": bool(URBAN.search(t) or nyc)}
    # How much this study looks like New York City residents (0-1). Stated on a slide; crude on purpose.
    if not human:
        fit = 0.0
    elif nyc:
        fit = 1.0
    elif region == "US":
        fit = 0.5 if tags["urban"] else 0.35
    elif region in ("Europe", "East Asia other", "Australia"):
        fit = 0.25 if tags["urban"] else 0.15
    elif region == "No place stated":
        fit = 0.1
    else:
        fit = 0.15 if tags["urban"] else 0.1
    tags["fit"] = fit
    return tags


# --- findings ----------------------------------------------------------------------------------------------------
def _match_sql(prefix, end):
    parts = []
    if end.get("concepts"):
        ids = ",".join(f"'{c}'" for c in end["concepts"])
        parts.append(f"{prefix}_concept_id in ({ids})")
    if end.get("regex"):
        parts.append(f"regexp_matches(lower({prefix}_name), '{end['regex']}')")
    cond = "(" + " or ".join(parts) + ")"
    if end.get("exclude"):
        cond += f" and not regexp_matches(lower({prefix}_name), '{end['exclude']}')"
    return cond


def findings(con, a, b):
    """All associations with one variable matching end a and the other matching end b (either order)."""
    q = f"""
      with hits as (
        select *, variable_1_name as name_a, variable_2_name as name_b from associations
          where {_match_sql('variable_1', a)} and {_match_sql('variable_2', b)}
        union all
        select *, variable_2_name as name_a, variable_1_name as name_b from associations
          where {_match_sql('variable_2', a)} and {_match_sql('variable_1', b)}
      )
      select distinct on (h.system_id) h.*, s.population_string, s.doi
      from hits h left join studies s using (study_id)"""
    df = con.execute(q).df()
    if df.empty:
        return df
    df["sign"] = df.apply(lambda r: _sign(r, a, b), axis=1)
    df["tested"] = df.apply(_tested, axis=1)
    tags = df["population_string"].map(tag_population)
    for k in ("region", "human", "nyc", "us", "older", "low_income", "black_hispanic", "urban", "fit"):
        df[k] = tags.map(lambda t: t[k])
    return df[df["human"]]


COMPARATOR = re.compile(r"\[(vs\.?|versus)[^\]]*\]|\((vs\.?|versus|compared (with|to))[^)]*\)|\b(vs\.?|versus)\b.*$")


def _polarity(name, end):
    n = COMPARATOR.sub("", name.lower())  # "heat wave days [vs non-heat wave days]" is not a negation
    p = -1 if (end.get("negation", True) and NEGATION.search(n)) else 1
    if end.get("inverse") and re.search(end["inverse"], n):
        p = -p
    return p


def _tested(r):
    return (pd.notna(r["ci_lower"]) and pd.notna(r["ci_upper"])) or pd.notna(r["p_value"])


def _significant(r, null):
    lo, hi = r["ci_lower"], r["ci_upper"]
    if pd.notna(lo) and pd.notna(hi):
        return (lo > null and hi > null) or (lo < null and hi < null)
    p = r["p_value"]
    if pd.notna(p):
        eq = r["p_value_equality"]
        return p < 0.05 or (eq in ("<", "<=", "<<") and p <= 0.05)
    return False


def _sign(r, a, b):
    """+1 / -1 if the finding shows a significant association with a readable direction, 0 if null, NaN if unreadable."""
    t, v = r["system_statistic_type"], r["statistic_value"]
    if pd.isna(v):
        return np.nan
    if t in RATIO:
        null = 1.0
    elif t in SIGNED:
        null = 0.0
    else:
        return np.nan
    if _tested(r) and not _significant(r, null):
        return 0  # tested and not significant: a null finding
    # untested estimates (no CI, no p) count by the sign of the point estimate
    s = 1 if v > null else -1 if v < null else 0
    return s * _polarity(r["name_a"], a) * _polarity(r["name_b"], b)


def summarize(df):
    """Research direction for one link."""
    if df is None or df.empty:
        return {"direction": None, "n_findings": 0, "n_studies": 0, "n_directional": 0, "n_null": 0,
                "agree_share": None, "evidence_fit": None}
    d = df[df["sign"].isin([1, -1])]
    pos, neg = int((d["sign"] == 1).sum()), int((d["sign"] == -1).sum())
    n = pos + neg
    if n == 0:
        direction, agree = None, None
    else:
        agree = max(pos, neg) / n
        direction = ("+" if pos > neg else "-") if agree >= 0.7 else "mixed"
    studies = df.drop_duplicates("study_id")
    return {"direction": direction, "n_findings": int(len(df)), "n_studies": int(studies["study_id"].nunique()),
            "n_directional": n, "n_positive": pos, "n_negative": neg, "n_null": int((df["sign"] == 0).sum()),
            "n_untested": int((~df["tested"]).sum()) if "tested" in df else 0,
            "agree_share": None if agree is None else round(agree, 2),
            "evidence_fit": round(float(studies["fit"].mean()), 3)}


def population_profile(df):
    s = df.drop_duplicates("study_id")
    return {"regions": {k: int(v) for k, v in s["region"].value_counts().items()},
            "nyc": int(s["nyc"].sum()), "us": int(s["us"].sum()), "older": int(s["older"].sum()),
            "low_income": int(s["low_income"].sum()), "black_hispanic": int(s["black_hispanic"].sum()),
            "urban": int(s["urban"].sum())}


# --- whose evidence: heat studies and NYC-tracked outcomes -----------------------------------------------------------
def heat_studies(con):
    rows = con.execute(f"""
        select distinct s.study_id, coalesce(s.population_string, '') as population_string, s.doi
        from associations a join studies s using (study_id)
        where regexp_matches(lower(variable_1_name), '{HEAT_STUDY_RX}')
           or regexp_matches(lower(variable_2_name), '{HEAT_STUDY_RX}')
        order by 1""").df()
    tags = rows["population_string"].map(tag_population)
    for k in ("region", "human", "nyc", "us", "older", "low_income", "black_hispanic", "urban"):
        rows[k] = tags.map(lambda t: t[k])
    rows["mentions_new_york"] = rows["population_string"].str.contains("new york", case=False)
    return rows


# NYC-tracked health problems (EHDP topics) -> graph concept labels
OUTCOMES = [
    ("Asthma", ["asthma"]),
    ("Obesity", ["obesity"]),
    ("Type 2 diabetes", ["type 2 diabetes"]),
    ("Hypertension", ["hypertension"]),
    ("Preterm birth", ["preterm birth"]),
    ("Infant mortality", ["infant mortality"]),
    ("Depression", ["major depressive disorder", "depression"]),
    ("Dementia", ["dementia"]),
    ("Heart disease", ["coronary artery disease", "cardiovascular disease"]),
    ("Stroke", ["stroke"]),
    ("COPD", ["chronic obstructive pulmonary disease"]),
    ("Lead poisoning", ["lead poisoning"]),
    ("Air pollution", ["air pollution", "particulates"]),
    ("Smoking", ["smoking", "tobacco smoking"]),
    ("Food insecurity", ["food insecurity"]),
    ("Gun violence", ["gun violence", "firearm"]),
    ("Heat illness", ["heat illness", "heat stroke", "extreme heat"]),
]


def outcome_sweep(con):
    out = []
    for name, labels in OUTCOMES:
        ids = [r[0] for r in con.execute(
            "select system_id from concepts where lower(wikidata_label) in (select unnest(?))",
            [[l.lower() for l in labels]]).fetchall()]
        if not ids:
            continue
        idl = ",".join(f"'{i}'" for i in ids)
        rows = con.execute(f"""select distinct s.study_id, coalesce(s.population_string,'') as p
            from associations a join studies s using (study_id)
            where variable_1_concept_id in ({idl}) or variable_2_concept_id in ({idl})""").df()
        tags = rows["p"].map(tag_population)
        human = tags.map(lambda t: t["human"])
        t = tags[human]
        n = int(len(t))
        if n == 0:
            continue
        cnt = lambda k: int(t.map(lambda x: x[k]).sum())
        out.append({"outcome": name, "concepts": labels, "concept_ids": ids, "studies": n,
                    "nyc": cnt("nyc"), "us": cnt("us"), "low_income": cnt("low_income"),
                    "black_hispanic": cnt("black_hispanic"), "older": cnt("older"),
                    "no_place": int(t.map(lambda x: x["region"] == "No place stated").sum())})
    return sorted(out, key=lambda r: -r["studies"])


if __name__ == "__main__":
    from .data import connect
    con = connect()
    h = heat_studies(con)
    print("heat studies", len(h), "human", int(h["human"].sum()), "nyc", int(h["nyc"].sum()),
          "mentions NY", int(h["mentions_new_york"].sum()))
    print(h["region"].value_counts().to_dict())
    print(h[h["nyc"]][["study_id", "doi", "population_string"]].to_string(max_colwidth=110))
    for r in outcome_sweep(con):
        print(r["outcome"], r["studies"], "NYC", r["nyc"], "US", r["us"], "low-inc", r["low_income"], "B/H", r["black_hispanic"])
