"""The heat claims. Each claim names its graph ends (concepts and/or variable-name patterns) and its city test.

Ends are deliberately explicit so anyone can read exactly what counted as evidence.
"""

BODY_TEMP = (r"skin|body|core|rectal|oral|tympanic|esophageal|muscle|testicular|scrotal|brain|basal|fever|"
             r"febrile|incubation|storage|cooking|water temperature|sea surface|soil")

HEAT = {"label": "heat exposure",
        "concepts": ["wpUeTjUbAc", "mUxSLRMwIy", "sSuplgYnDQ", "UbF0-c8zHb"],  # extreme heat, air/surface temp, UHI
        "regex": r"heat ?wave|extreme heat|heat exposure|heat index|high (ambient |outdoor |air )?temperature|"
                 r"ambient temperature|apparent temperature|hot (day|weather|season|summer)|extreme temperature|"
                 r"temperature exposure|daily (mean |maximum |max )?temperature|outdoor temperature|urban heat|"
                 r"air temperature|surface temperature|heat island",
        "exclude": BODY_TEMP}
TEMP = {"label": "local temperature",
        "concepts": ["sSuplgYnDQ", "mUxSLRMwIy", "UbF0-c8zHb"],
        "regex": r"surface temperature|air temperature|ambient temperature|heat island|urban heat|"
                 r"outdoor temperature|street temperature|thermal comfort|cooling effect",
        "exclude": BODY_TEMP}
HEAT_ILLNESS = {"label": "heat illness",
                "concepts": ["PtQBvGm5CM", "rYCo7LTyzN"],  # heat illness, heat stroke
                "regex": r"heat[- ]related|heat (illness|stroke|exhaustion|syncope|cramps)|heatstroke|"
                         r"hyperthermia|heat[- ]associated"}
HOSPITAL = {"label": "hospital and ER visits",
            "concepts": ["Gl-I4wBZ5r", "nS9fqJ01TW"],  # hospitalization, emergency department
            "regex": r"hospitali[sz]ation|hospital admission|emergency (department|room)|\bed visits?|"
                     r"emergency (visits?|admissions?)|ambulance"}
HEAT_HARM = {"label": "heat illness, hospital and ER visits",
             "concepts": HEAT_ILLNESS["concepts"] + HOSPITAL["concepts"],
             "regex": HEAT_ILLNESS["regex"] + "|" + HOSPITAL["regex"]}
AC = {"label": "air conditioning", "concepts": ["OnRtQgvIkg"], "regex": r"air[- ]condition"}
GREEN = {"label": "trees and greenery",
         "concepts": ["I2CN3brExA", "lHLIKbfnYp", "jsCEk-G4lX", "hsryqxdFzE"],  # tree, green space, vegetation, NDVI
         "regex": r"tree canopy|tree cover|canopy cover|street trees?|urban trees?|trees|green ?space|greenness|"
                  r"vegetation|ndvi|urban forest|green infrastructure",
         "exclude": r"tree nut|decision tree|phylogenetic|regression tree|family tree|tree[- ]ring|ring width|"
                    r"radial growth|tree growth|growth of trees|chronolog|crop|yield|forest fire|wildfire"}
TREES = {"label": "street trees",
         "concepts": ["I2CN3brExA"],
         "regex": r"tree canopy|tree cover|canopy cover|street trees?|urban trees?|tree density|trees",
         "exclude": GREEN["exclude"]}
POVERTY = {"label": "poverty",
           "concepts": ["bIwjlkmcHV", "yPfH_YBxUJ", "6yoKTYSOJa", "_zLVUxvG7F"],  # poverty, income x2, SES
           "regex": r"poverty|low[- ]income|deprivation|socioeconomic|household income|income",
           "exclude": r"sleep|food deprivation|water deprivation|maternal deprivation|sensory",
           "inverse": r"income|socioeconomic (status|position)|wealth|affluen"}  # higher income = less poverty
OLDER_ALONE = {"label": "older adults living alone",
               "concepts": ["qt5dLX7UCR"],  # social isolation
               "regex": r"living alone|lives alone|live alone|social isolation|socially isolated|older age|elderly|"
                        r"aged? (65|75)|older adults"}
COLD_HOME = {"label": "cold homes (no heat)", "negation": False,  # "lack of heating" already means a cold home
             "regex": r"cold (homes?|houses?|housing|indoor)|living in cold|energy poverty|fuel poverty|"
                      r"lack of heating|inadequate heating|without heating|unheated|measures of cold homes"}
COLD_HARM = {"label": "cold, respiratory and general health harm",
             # "poor mental health" IS the harm, not its absence (hand-check, v1.1.0); v1.0.0 read it inverted
             "negation": False,
             "concepts": ["h0Aryv0NjW"],  # hypothermia
             "regex": r"hypothermia|cold[- ]related|frostbite|respirator|asthma|wheez|cough|infection|mortality|"
                      r"death|hospitali|blood pressure|ecg|electrocardiogram|poor (mental )?health|health outcomes"}
ASTHMA = {"label": "asthma", "concepts": ["EAshH_Ko3h"], "regex": r"asthma"}

# city: frame (cd | uhf | year), x, y, and x_polarity = -1 when the city x measures the opposite of the first end.
CLAIMS = [
    {"id": "hot-summers-hospitalizations", "title": "Hotter summers send more New Yorkers to hospital for heat",
     "kind": "direct", "ends": [HEAT, HEAT_HARM],
     "city": {"frame": "year", "x": "days_90f", "y": "heat_hosp_n", "control": None},
     "settle_if_not": "Daily emergency-department syndromic counts by date instead of yearly totals: thousands "
                      "of days instead of about 20 years."},
    {"id": "ac-protects", "title": "Air conditioning protects against heat illness",
     "kind": "direct", "ends": [AC, HEAT_ILLNESS],
     "city": {"frame": "uhf", "x": "ac_households_pct", "y": "heat_hosp_rate", "control": "poverty_pct"},
     "settle_if_not": "Air-conditioner use during heat waves (not ownership), by neighborhood, plus heat deaths at home."},
    {"id": "canopy-cools", "title": "Tree canopy cools neighborhoods",
     "kind": "direct", "ends": [GREEN, TEMP],
     "city": {"frame": "uhf", "x": "tree_canopy_pct", "y": "surface_temp_f", "control": "poverty_pct"},
     "settle_if_not": "Street-level air temperature sensors next to canopy measurements."},
    {"id": "trees-cool", "title": "Counting street trees tells you which districts are cooler",
     "kind": "direct", "ends": [GREEN, TEMP],
     "city": {"frame": "cd", "x": "tree_density_per_km2", "y": "surface_temp_f", "control": "poverty_pct"},
     "settle_if_not": "Canopy area instead of tree counts: a young street tree shades almost nothing. "
                      "Compare with the canopy claim."},
    {"id": "greenery-cools-cd", "title": "Greener districts are cooler",
     "kind": "direct", "ends": [GREEN, TEMP],
     "city": {"frame": "cd", "x": "veg_cover_pct", "y": "surface_temp_f", "control": "poverty_pct"},
     "settle_if_not": "Block-level greenery and temperature: 59 districts average away the contrast."},
    {"id": "hot-districts-heat-ed", "title": "Hotter districts send more people to the ER for heat",
     "kind": "direct", "ends": [HEAT, HEAT_HARM],
     "city": {"frame": "cd", "x": "surface_temp_f", "y": "heat_ed_rate", "control": "poverty_pct"},
     "settle_if_not": "Indoor temperatures in homes, by district. Satellite surface temperature measures roofs and "
                      "pavement, not the apartments where people get sick."},
    {"id": "poverty-heat-ed", "title": "Poorer districts suffer more heat illness",
     "kind": "direct", "ends": [POVERTY, HEAT_ILLNESS],
     "city": {"frame": "cd", "x": "poverty_pct", "y": "heat_ed_rate", "control": None},
     "settle_if_not": "Heat deaths by district: poorer residents may die at home without reaching an ER."},
    {"id": "older-alone-heat-ed", "title": "Districts with more older adults living alone have more heat illness",
     "kind": "direct", "ends": [OLDER_ALONE, HEAT_ILLNESS],
     "city": {"frame": "cd", "x": "older_alone_pct", "y": "heat_ed_rate", "control": "poverty_pct"},
     "settle_if_not": "Heat ER visits for ages 65+ by district, instead of all-age rates."},
    {"id": "hot-districts-asthma", "title": "Hotter districts have more asthma emergencies",
     "kind": "direct", "ends": [HEAT, ASTHMA],
     "city": {"frame": "cd", "x": "surface_temp_f", "y": "asthma_ed_rate", "control": "poverty_pct"},
     "settle_if_not": "Daily asthma ER visits against daily temperature, which separates heat from poverty."},
    {"id": "bridge-trees-heat-ed", "title": "Street trees mean fewer heat ER visits, through cooler streets",
     "kind": "bridge", "ends": [GREEN, TEMP, HEAT_HARM],
     # the graph's greenery-temperature evidence is thin and split, so NYC's canopy data can supply that link
     "link_fallback": {0: {"frame": "uhf", "x": "tree_canopy_pct", "y": "surface_temp_f"}},
     "city": {"frame": "cd", "x": "tree_density_per_km2", "y": "heat_ed_rate", "control": "poverty_pct",
              "middle": "surface_temp_f"},
     "settle_if_not": "A district study of trees, indoor heat and ER visits that adjusts for income and housing age."},
    {"id": "bridge-no-heat-cold-ed", "title": "Apartments without winter heat send people to the ER for cold",
     "kind": "bridge", "ends": [COLD_HOME, COLD_HARM],
     "city": {"frame": "cd", "x": "no_heat_complaints_per_1k", "y": "cold_ed_rate", "control": "poverty_pct"},
     "note": "The Underlay collection nyc/heat-complaints is about missing heat in winter, not summer heat.",
     "settle_if_not": "Indoor winter temperatures in buildings with repeated no-heat complaints."},
]
