"""Chicago indicators for the concordance matrix, each tied to a New York indicator key.

Every row reuses the New York key from analyses/graph_concordance/indicators.py, so the concept mapping, the
polarity and the literature signs in data/derived/graph/concordance/literature_signs.csv apply unchanged and no
new graph request is needed. Source: Chicago Health Atlas API (chicagohealthatlas.org/api/v1), community-area
layer, total population. transform "100-x" turns a rate of absence into the New York indicator's rate of presence.
The table was fixed from topic metadata (names, units, descriptions, periods) before any Chicago value was loaded
(claim transfer-chicago-concordance-matrix).
"""

CHICAGO = [
    # NY key, Atlas topic, transform, how the Chicago measure differs from the New York one
    ("pm25", "PMC", "x", "EPA EJSCREEN annual mean, a regional model surface; New York's is the NYCCAS street-level survey"),
    ("ozone", "OOO", "x", "EPA EJSCREEN, mean of the 10 highest daily 8-hour values; New York's is the NYCCAS summer mean"),
    ("traffic", "TRF", "x", "EPA EJSCREEN traffic proximity (vehicles within 500 m over distance); New York's is vehicle miles in the area"),
    ("tree_shade", "UTC", "x", "tree canopy share of land"),
    ("pop_density", "POD", "x", ""),
    ("crowding", "HTJ", "x", ""),
    ("owner_occupied", "HUO", "x", ""),
    ("evictions", "EVR", "x", "Eviction Lab rate; latest period is several years old"),
    ("poverty", "POV", "x", ""),
    ("unemployment", "UMP", "x", ""),
    ("high_school", "EDB", "x", ""),
    ("limited_english", "LEP", "x", "share of households; New York's is share of residents"),
    ("foreign_born", "FOR", "x", ""),
    ("insurance", "UNS", "100-x", "uninsured residents of all ages, reversed; New York's is insured adults"),
    ("car_commute", "CAR", "x", "drive alone to work"),
    ("exercise", "HCSPAP", "100-x", "physical inactivity, reversed"),
    ("smoking", "HCSSMKP", "x", ""),
    ("binge_drinking", "HCSBDP", "x", ""),
    ("sugary_drinks", "HCSSP", "x", ""),
    ("shootings", "VRFIR", "x", "firearm homicide deaths per resident; New York's is shooting incidents per resident"),
    ("asthma_adult", "HCSATHP", "x", "survey prevalence of current asthma; New York's is emergency visits"),
    ("obesity", "HCSOBP", "x", ""),
    ("diabetes", "HCSDIAP", "x", ""),
    ("depression", "DPR", "x", "CDC PLACES model-based estimate"),
    ("distress", "HCSSPDP", "x", ""),
    ("good_health", "HCSOHSP", "x", ""),
    ("premature_death", "YPLL", "x", "years of potential life lost per 100,000; New York's is the death rate before 65"),
    ("preterm", "VRPTP", "x", ""),
    ("low_birthweight", "VRBWP", "x", "all births under 2,500 g; New York's is low birthweight at term"),
    ("infant_death", "VRIMR", "x", ""),
    ("pedestrian_injury", "CHAVTZN", "x", "traffic deaths of all road users per resident; New York's is pedestrian injuries"),
    ("heat_ed", "CHAJBFH", "x", "heat-related deaths; New York's is heat emergency visits"),
    ("lead", "LDPP", "x", ""),
    ("walking_difficulty", "HCSIDQZ", "x", ""),
    ("cognitive_difficulty", "HCSXWSF", "x", ""),
    ("hearing_difficulty", "HCSYWEG", "x", ""),
    ("vision_difficulty", "HCSRACB", "x", ""),
]

# New York indicators with a concept for which no matching Chicago community-area measure was found in the metadata.
NOT_FOUND = {
    "no2": "no NO2 topic", "black_carbon": "diesel particulate matter (DPM) exists but is a different quantity and concept",
    "noise": "no noise topic", "surface_temp": "no surface temperature topic", "green_cover": "green space proximity (EKG) is discontinued and measures distance, not cover",
    "park_access": "no park access topic", "ac": "no air conditioning topic", "housing_problems": "no maintenance topic", "cockroaches": "no pest topic",
    "transit_commute": "active transportation (ACT) mixes walking, cycling and public transport", "walk_commute": "same",
    "asthma_child": "youth asthma ED visits (CHAOHOB) are not published by community area", "psych_hosp": "behavioural health hospitalisations (HDBHR) are not published by community area",
}

KEYS = [r[0] for r in CHICAGO]
N_AREAS = 77
MIN_AREAS = 70   # a period is used when at least this many of the 77 areas have a value (New York: 40 of 42)
