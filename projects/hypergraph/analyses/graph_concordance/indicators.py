"""The mapping table: each city indicator, its source, the graph concepts it is mapped to, and its polarity.

polarity is +1 when a higher indicator value means more of the concept, -1 when it means less.
concepts is a list of (system_id, label); an empty list means the graph has no usable concept
(the reason is in `note`). Source ("ehdp", indicator id, measure id) is the NYC DOHMH Environment and
Health Data Portal at the commit pinned in analyses/mobility/ehdp.py, at UHF42. Source ("project", file,
column, how) is one of this project's derived tract tables, aggregated to UHF42 in city.py.
The table was fixed before any city correlation was computed (claim graph-concordance-matrix).
"""

E_, O_ = "exposure", "outcome"

INDICATORS = [
    # key, role, label, source, polarity, concepts, note
    ("pm25", E_, "PM2.5, annual mean", ("ehdp", 2023, 1425), +1, [("jtzZPZ8DQh", "PM 2.5"), ("gX6h_gZWHH", "particulates")], ""),
    ("no2", E_, "Nitrogen dioxide, annual mean", ("ehdp", 2025, 1431), +1, [("DC_F0GO0WQ", "nitrogen dioxide")], ""),
    ("black_carbon", E_, "Black carbon, annual mean", ("ehdp", 2024, 1428), +1, [("zRxOHnsEfh", "black carbon")], ""),
    ("ozone", E_, "Ozone, summer mean", ("ehdp", 2027, 1435), +1, [("JMeOsYIcbL", "ozone")], "the concept also holds medical ozone"),
    ("traffic", E_, "Traffic volume (vehicle miles)", ("ehdp", 2112, 643), +1, [("HMQHUKEqkM", "traffic"), ("oG8Da1gCE9", "traffic-related pollution")], ""),
    ("surface_temp", E_, "Surface temperature", ("ehdp", 2141, 688), +1, [("sSuplgYnDQ", "surface temperature"), ("UbF0-c8zHb", "urban heat island")], ""),
    ("green_cover", E_, "Grass and tree cover", ("ehdp", 2143, 690), +1, [("lHLIKbfnYp", "green space"), ("RF7tCwCaa5", "vegetation cover"), ("hsryqxdFzE", "Normalized Difference Vegetation Index")], ""),
    ("tree_shade", E_, "Tree shade (canopy)", ("ehdp", 2157, 708), +1, [("I2CN3brExA", "tree")], ""),
    ("park_access", E_, "Park access", ("ehdp", 2388, 1224), +1, [("6DTj2ennMm", "park")], ""),
    ("walkability", E_, "Walkability score", ("ehdp", 2133, 673), +1, [], "no concept: search for walkability returns nothing"),
    ("noise", E_, "Modelled transport noise (dB)", ("project", "neighbourhood/noise_map_tracts.csv", "noise_leq_db", "popmean"), +1, [("OI_Yok9JP4", "noise"), ("cEPG6i4Yq1", "traffic noise"), ("36gde7OoEQ", "noise pollution")], ""),
    ("ac", E_, "Households with air conditioning", ("ehdp", 2185, 781), +1, [("OnRtQgvIkg", "air conditioning")], ""),
    ("crowding", E_, "Crowded housing units", ("ehdp", 15, 25), +1, [("xTTEM0NvmJ", "household crowding"), ("XvZRe9CYoN", "overcrowding")], ""),
    ("owner_occupied", E_, "Owner-occupied homes", ("ehdp", 17, 29), -1, [("7uxeY6j12S", "renting")], "no home-ownership concept; renting with reversed polarity"),
    ("housing_problems", E_, "Rented homes with maintenance problems", ("ehdp", 2399, 1248), -1, [("NSSHqnR5tw", "housing quality")], ""),
    ("leaks", E_, "Homes with leaks", ("ehdp", 42, 80), +1, [], "no concept for damp, mould or leaks"),
    ("cockroaches", E_, "Homes with cockroaches", ("ehdp", 107, 245), +1, [("JgRYwtm5Zx", "cockroach")], ""),
    ("rodents", E_, "Failed rat inspections (share)", ("project", "neighbourhood/rodents_asthma_uhf.csv", "rat_fail_share", "uhf"), +1, [], "no concept: 'rats' and 'mouse' are laboratory animals; rodent variables are ungrounded"),
    ("poverty", E_, "Poverty", ("ehdp", 103, 221), +1, [("bIwjlkmcHV", "poverty"), ("ADplkYjn2k", "poverty area")], ""),
    ("unemployment", E_, "Unemployment", ("ehdp", 2337, 1032), +1, [("3x-TeF7nX4", "unemployment"), ("hupL32mZNu", "unemployed")], ""),
    ("high_school", E_, "Completed high school", ("ehdp", 2334, 1025), +1, [("E5nEeeLpcM", "education"), ("GVQ7y6M5KG", "high school diploma")], ""),
    ("evictions", E_, "Evictions", ("ehdp", 2365, 1128), +1, [("31gLuixqrR", "housing instability")], "no eviction concept; housing instability is the nearest"),
    ("limited_english", E_, "Limited English", ("ehdp", 2335, 1027), +1, [("Ic3j2gkecR", "limited English proficiency")], ""),
    ("foreign_born", E_, "Foreign born", ("ehdp", 14, 24), +1, [("7MSXfJXmhm", "immigrant"), ("R-hjC4EY_S", "immigration")], ""),
    ("insurance", E_, "Adults with health insurance", ("ehdp", 2132, 672), +1, [("1IF-zFK6LW", "health insurance"), ("ONf6ct5iQ3", "insurance coverage")], ""),
    ("alcohol_outlets", E_, "Alcohol outlets (on-premises) per resident", ("ehdp", 2049, 465), +1, [], "no concept for alcohol outlets or liquor licences"),
    ("transit_commute", E_, "Commute by public transport", ("ehdp", 2415, 1306), +1, [("nB_DNapip8", "public transport")], "concept exists with no relationships"),
    ("walk_commute", E_, "Commute on foot", ("ehdp", 2415, 1307), +1, [("_2dhcsFISl", "walking")], ""),
    ("bike_commute", E_, "Commute by bicycle", ("ehdp", 2415, 1304), +1, [], "no concept: bicycle, bicycling, cycling, bike and cyclist return nothing relevant"),
    ("car_commute", E_, "Commute by car", ("ehdp", 2415, 1305), +1, [("RlDnc5QgX2", "driving"), ("iSnN_TnuWd", "motor car")], ""),
    ("exercise", E_, "Any exercise in past 30 days", ("ehdp", 2060, 500), +1, [("dPeET-pgVN", "physical activity"), ("9xkOyRJxD9", "physical exercise")], ""),
    ("smoking", E_, "Current smokers", ("ehdp", 2019, 307), +1, [("NI8J66klok", "smoking"), ("wbFMjf8vLB", "tobacco smoking"), ("2Cgoxznk46", "cigarette smoking")], ""),
    ("binge_drinking", E_, "Binge drinking", ("ehdp", 2051, 470), +1, [("DU5dF5vxkA", "binge drinking"), ("N5xiUDm5Jr", "alcohol consumption")], ""),
    ("sugary_drinks", E_, "Sugary drinks daily", ("ehdp", 2097, 609), +1, [("BxJRIdZ1wJ", "sugar-sweetened beverage")], ""),
    ("shootings", E_, "Shootings per resident", ("project", "neighbourhood/vacant_shootings_tracts.csv", "shootings", "rate_per_pop"), +1, [("X7hfhwez9f", "gun violence"), ("2qLKgaxkm_", "violence"), ("Sb3zGs-d5I", "violent crime")], ""),
    ("vacant_land", E_, "Vacant land (share of lot area)", ("project", "neighbourhood/vacant_shootings_tracts.csv", "vac_area/lot_area", "ratio_of_sums"), +1, [], "no concept: vacant-lot variables are ungrounded or grounded to housing"),
    ("pop_density", E_, "Population density", ("project", "neighbourhood/tracts_acs.csv", "pop/land_km2", "ratio_of_sums"), +1, [("WLNXo1tGFr", "population density")], ""),
    ("asthma_adult", O_, "Asthma ED visits, adults", ("ehdp", 2380, 1199), +1, [("EAshH_Ko3h", "asthma")], ""),
    ("asthma_child", O_, "Asthma ED visits, age 5 to 17", ("ehdp", 2379, 1196), +1, [("PQ1nPOBjAX", "childhood asthma")], ""),
    ("obesity", O_, "Obesity", ("ehdp", 2063, 506), +1, [("cj7G775u_Q", "obesity")], ""),
    ("diabetes", O_, "Diabetes", ("ehdp", 2169, 717), +1, [("DQbECFISI6", "diabetes"), ("h59nBSHN14", "type 2 diabetes")], ""),
    ("depression", O_, "Depression", ("ehdp", 2417, 1324), +1, [("PfzPevl_MY", "mental depression"), ("HlOsAtlSea", "depressive disorder"), ("ZuREWSEpi7", "major depressive disorder")], ""),
    ("distress", O_, "Serious psychological distress", ("ehdp", 2419, 1330), +1, [("9BEEXPEHYj", "distress")], ""),
    ("psych_hosp", O_, "Psychiatric hospitalisations", ("ehdp", 2418, 1327), +1, [("-0HrxUPkp2", "mental disorder")], ""),
    ("good_health", O_, "Self-reported good health", ("ehdp", 2232, 1059), +1, [("VTzraMNryq", "health status")], ""),
    ("premature_death", O_, "Death before 65", ("ehdp", 2322, 983), +1, [("hXsXEM2vfb", "Mortality, Premature"), ("QPxlNKv3zV", "mortality rate"), ("oEWjV89s3H", "all-cause mortality")], ""),
    ("preterm", O_, "Preterm birth", ("ehdp", 1, 2), +1, [("sdWLpL7z_l", "preterm birth")], ""),
    ("low_birthweight", O_, "Low birthweight at term", ("ehdp", 4, 8), +1, [("VM_BejazFq", "low birth weight infant")], ""),
    ("infant_death", O_, "Infant deaths", ("ehdp", 5, 10), +1, [("rNvNuxXEdo", "infant mortality")], ""),
    ("pedestrian_injury", O_, "Pedestrian injuries", ("ehdp", 2094, 676), +1, [("sz00kCqokr", "pedestrian"), ("5aHRpqbEkQ", "traffic collision")], ""),
    ("heat_ed", O_, "Heat ED visits", ("ehdp", 2075, 537), +1, [("rYCo7LTyzN", "heat stroke"), ("PtQBvGm5CM", "heat illness")], ""),
    ("lead", O_, "Child blood lead 5+ mcg/dL", ("ehdp", 2184, 777), +1, [("k-4NQAUWa9", "lead poisoning"), ("Z1DkcC8Exg", "Blood lead level")], ""),
    ("walking_difficulty", O_, "Difficulty walking", ("ehdp", 2459, 1460), +1, [("lzYVURvPRv", "disability")], ""),
    ("cognitive_difficulty", O_, "Cognitive difficulty", ("ehdp", 2461, 1464), +1, [("yvzAi6nThy", "cognitive dysfunction"), ("dkRizMJDpS", "cognitive disorder"), ("g4giO_RrZB", "dementia")], ""),
    ("hearing_difficulty", O_, "Hearing difficulty", ("ehdp", 2462, 1466), +1, [("fdqTZ-jKB3", "hearing loss")], ""),
    ("vision_difficulty", O_, "Vision difficulty", ("ehdp", 2464, 1470), +1, [("YLi9bM-hbf", "visual impairment")], ""),
]

KEYS = [r[0] for r in INDICATORS]
BY_KEY = {r[0]: dict(key=r[0], role=r[1], label=r[2], source=r[3], polarity=r[4], concepts=r[5], note=r[6]) for r in INDICATORS}
