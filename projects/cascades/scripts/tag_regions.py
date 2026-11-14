"""Tag each graph finding with study country, world region, UK flag and setting (home / school / workplace / other).
Country is parsed from the study's population description (System `population_string`); it is often missing or vague,
so `country` = 'unknown' is common and is reported, not guessed."""
import re
import pandas as pd
import pycountry

ALIASES = {  # extra names, demonyms, cities and states that commonly appear in population strings
    "United Kingdom": "uk|u\\.k\\.|britain|british|england|english|scotland|scottish|wales|welsh|northern ireland|london|manchester|birmingham|glasgow|edinburgh|leeds|liverpool|bristol|avon|alspac",
    "United States": "usa|u\\.s\\.a?\\.?|united states|america(?!n indian)|american|new york|california|texas|boston|chicago|baltimore|detroit|seattle|los angeles|philadelphia|massachusetts|ohio|michigan|minnesota|north carolina|navajo|nhanes|puerto rico|cincinnati|denver|arizona|washington state|iowa|wisconsin|oregon|georgia, us|new jersey|connecticut|pennsylvania|maryland|virginia|colorado|utah|alaska|hawaii|inner-city|inner city",
    "China": "china|chinese|beijing|shanghai|guangzhou|wuhan|xuanwei|hong kong|yunnan|sichuan|shenyang|tianjin|hubei|anhui|shandong|jiangsu|zhejiang|guangdong|henan|hunan|shaanxi|gansu|harbin|chongqing|nanjing|charls|kadoorie",
    "Taiwan": "taiwan|taipei",
    "India": "india|indian(?! ocean)|delhi|mumbai|chennai|kolkata|tamil nadu|kerala|bangalore|pune|andhra|lucknow",
    "Korea, Republic of": "korea|korean|seoul",
    "Japan": "japan|japanese|tokyo|osaka",
    "Netherlands": "netherlands|dutch|piama|rotterdam|amsterdam",
    "Germany": "germany|german|munich|lisa|gini",
    "Sweden": "sweden|swedish|stockholm|bamse",
    "Finland": "finland|finnish|kuopio",
    "Denmark": "denmark|danish|copenhagen",
    "Norway": "norway|norwegian|oslo",
    "France": "france|french|paris",
    "Spain": "spain|spanish|madrid|barcelona",
    "Italy": "italy|italian|rome|milan",
    "Poland": "poland|polish|krakow|cracow",
    "Australia": "australia|australian|sydney|melbourne|tasmania",
    "New Zealand": "new zealand|nz\\b",
    "Canada": "canada|canadian|ontario|quebec|toronto|montreal",
    "Mexico": "mexico|mexican",
    "Brazil": "brazil|brazilian",
    "Bolivia, Plurinational State of": "bolivia",
    "Guatemala": "guatemala|respire",
    "Peru": "peru|peruvian|lima|puno",
    "Nigeria": "nigeria|nigerian",
    "Ghana": "ghana|ghanaian",
    "Kenya": "kenya|kenyan",
    "Ethiopia": "ethiopia|ethiopian",
    "Malawi": "malawi",
    "Uganda": "uganda",
    "Tanzania, United Republic of": "tanzania",
    "South Africa": "south africa",
    "Nepal": "nepal|nepalese",
    "Bangladesh": "bangladesh",
    "Pakistan": "pakistan|pakistani",
    "Turkey": "turkey|turkish|türkiye",
    "Iran, Islamic Republic of": "iran|iranian|tehran",
    "Viet Nam": "vietnam|viet nam",
    "Thailand": "thailand|thai",
    "Indonesia": "indonesia",
    "Saudi Arabia": "saudi",
}
REGION = {
    "United Kingdom": "UK", "Ireland": "Europe (non-UK)",
    "United States": "North America", "Canada": "North America", "Mexico": "Latin America",
    "Australia": "Oceania", "New Zealand": "Oceania",
    "China": "East Asia", "Taiwan": "East Asia", "Japan": "East Asia", "Korea, Republic of": "East Asia", "Mongolia": "East Asia",
    "India": "South Asia", "Nepal": "South Asia", "Bangladesh": "South Asia", "Pakistan": "South Asia", "Sri Lanka": "South Asia",
}
EUROPE = {c.name for c in pycountry.countries if c.alpha_2 in
          "AT BE BG HR CY CZ DK EE FI FR DE GR HU IS IT LV LT LU MT NL NO PL PT RO SK SI ES SE CH RS UA BA AL MK ME BY MD".split()}
LATAM = {c.name for c in pycountry.countries if c.alpha_2 in "AR BO BR CL CO CR CU DO EC SV GT HN JM NI PA PY PE PR UY VE HT".split()}
AFRICA = {c.name for c in pycountry.countries if c.alpha_2 in
          "DZ AO BJ BW BF BI CM CV CF TD KM CG CD CI DJ EG GQ ER SZ ET GA GM GH GN GW KE LS LR LY MG MW ML MR MU MA MZ NA NE NG RW ST SN SC SL SO ZA SS SD TZ TG TN UG ZM ZW".split()}
SEASIA = {c.name for c in pycountry.countries if c.alpha_2 in "BN KH ID LA MY MM PH SG TH TL VN".split()}
MENA = {c.name for c in pycountry.countries if c.alpha_2 in "BH IR IQ IL JO KW LB OM QA SA SY TR AE YE PS AF".split()}

def region_of(country):
    if country in REGION: return REGION[country]
    if country in EUROPE: return "Europe (non-UK)"
    if country in LATAM: return "Latin America"
    if country in AFRICA: return "Africa"
    if country in SEASIA: return "Southeast Asia"
    if country in MENA: return "Middle East & Central Asia"
    return "Other"

patterns = []
for c in pycountry.countries:
    names = {c.name} | ({getattr(c, "common_name")} if hasattr(c, "common_name") else set())
    alias = ALIASES.get(c.name, "")
    rx = "|".join(re.escape(n.lower()) for n in names) + (("|" + alias) if alias else "")
    patterns.append((c.name, re.compile(r"\b(" + rx + r")\b", re.I)))
patterns.append(("Taiwan", re.compile(r"\b(" + ALIASES["Taiwan"] + r")\b", re.I)))
patterns.sort(key=lambda p: 0 if p[0] in ALIASES else 1)   # aliased (common) countries first
MULTI = re.compile(r"\b(sub-saharan|low- and middle-income|lmic|multi-?country|countries|europe(an)?|asia|africa|latin america|global|worldwide|\d+ countries)\b", re.I)
SETTINGS = [("school", r"school|classroom|pupil|student|kindergarten|day ?care|nursery"),
            ("workplace", r"office|worker|workplace|employee|occupational|staff|miner|factory|industr"),
            ("home", r"home|house|household|dwelling|resident|bedroom|kitchen|domestic|mattress|living room|cook")]

def tag(pop, text):
    pop = str(pop or "")
    found = []
    for name, rx in patterns:
        if rx.search(pop):
            found.append(name)
    found = list(dict.fromkeys(found))
    if len(found) == 1: country = found[0]
    elif len(found) > 1: country = "multiple: " + "; ".join(found[:4])
    elif MULTI.search(pop): country = "multi-country/region (unspecified)"
    else: country = "unknown"
    if country.startswith("multiple") or country.startswith("multi-country"):
        region = "Multi-country"
    elif country == "unknown":
        region = "Unknown"
    else:
        region = region_of(country)
    s = (pop + " " + text).lower()
    setting = next((k for k, rx in SETTINGS if re.search(rx, s)), "other/unspecified")
    return country, region, setting

ev = pd.read_csv("data/evidence.csv")
out = ev.apply(lambda r: tag(r.population, f"{r.variable_1_name} {r.variable_2_name}"), axis=1, result_type="expand")
ev[["study_country", "study_region", "setting"]] = out
ev["is_uk"] = ev.study_region.eq("UK")
ev.to_csv("data/evidence.csv", index=False)
k = ev[ev.relevance == "keep"].drop_duplicates(["group", "study_id"])
tab = k.pivot_table(index="group", columns="study_region", values="study_id", aggfunc="count", fill_value=0)
tab["total"] = tab.sum(axis=1)
tab.to_csv("data/coverage_by_region.csv")
st = k.pivot_table(index="group", columns="setting", values="study_id", aggfunc="count", fill_value=0)
st.to_csv("data/coverage_by_setting.csv")
print(tab.to_string()); print(); print(st.to_string())
print("\nunknown-country share of studies:", (k.study_region == "Unknown").mean().round(2))
