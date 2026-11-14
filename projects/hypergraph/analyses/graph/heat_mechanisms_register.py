"""Register heat-mech-outdoors and heat-mech-intox before any mediator series is queried.

Graph evidence is read from data/derived/graph/heat_mechanisms/ (built by
heat_mechanisms_graph.py, heat_mechanisms_findings.py and heat_mechanisms_variables.py).
Run once: python analyses/graph/heat_mechanisms_register.py <id>
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import claims  # noqa: E402

D = ROOT / "data" / "derived" / "graph" / "heat_mechanisms"
sh = {s["label"]: s for s in json.loads((D / "shared_neighbours.json").read_text())["shared"]}
cf = json.loads((D / "candidate_findings.json").read_text())


def item(label, side, summary, pmids, direction):
    s, c = sh[label], cf[label]
    via = s["temp_via"] if side == "temp" else {k: v for k, v in s["viol_via"].items() if k != "injury"}
    sp = c["temp_split" if side == "temp" else "viol_split"]
    return {"relationship_id": sorted({r for v in via.values() for r in v["relationship_ids"]}),
            "concepts": [("temperature side: " if side == "temp" else "violence side: ") + ", ".join(via), label],
            "n_findings": sum(v["n_findings"] for v in via.values()), "n_associations_returned": sp["n"],
            "n_studies": sp["studies"], "sign_split": {"plus": sp["plus"], "minus": sp["minus"], "unsigned": sp["unsigned"]},
            "direction": direction, "summary": summary, "pubmed_ids": pmids}


SEEN = ("Already seen by the project before this registration: the daily shootings and Central Park temperature series and "
        "their relation (heat-shootings: IRR 1.146 per 5 C, 1.130 to 1.163; spline RR against the median TMAX 1.37 at 27 C, "
        "1.46 at 30 C, 1.54 at 33 C); daily FDNY EMS dispatches of type SHOT, T-SHOT and STAB (bridge-shot-ems-link, "
        "bridge-heat-shootings-ems); the 2023 totals of EMS dispatches by initial call type (DRUG 88,621; EDP 98,371); 311 "
        "noise complaints of 2022-2024 summed by latitude and longitude, not by day (nbhd-noise311-exposure); daily 311 "
        "street-flooding complaints (further-tidal-flooding-311); and, for this registration, the number of rows and sensors "
        "per year and travel mode in ct66-47at (no count values). No daily series of 311 Noise - Street/Sidewalk, 311 Drinking, "
        "EMS DRUG or EDP dispatches, or bicycle counts has been queried or seen.")

COMMON_PLAN = (
    "Daily series for New York City. Shootings (5ucz-vwe8, distinct incident_key per occur_date), Central Park TMAX and PRCP "
    "(GHCN-Daily USW00094728) and the calendar terms are built exactly as in analyses/heat/shootings.py. Base model B0: "
    "negative binomial GLM of daily shooting incidents on TMAX/5, day of week, calendar month, year, holiday and rain >= 1 mm "
    "(alpha by ML, HC0 errors), refitted on the days for which the mediator exists. First link L1: the same model with the "
    "mediator's daily count as the outcome, giving the mediator's IRR per 5 C; and the same with a natural cubic spline of "
    "TMAX (4 df) to read the mediator's RR at 21, 27 and 33 C against 15 C. Mediator model B1: B0 plus log(1 + mediator count) "
    "on the same day. Attenuation A = 1 - b1/b0, where b0 and b1 are the coefficients of TMAX/5 in B0 and B1. Interval for A: "
    "500 bootstrap resamples of calendar weeks (all seven days of a week kept together), alpha held at its full-sample value, "
    "2.5th and 97.5th percentiles. This is mediation by proxy and not identification: the proxy measures the mediator with "
    "error, which pulls A toward zero; an unmeasured cause of both the mediator and shootings that is correlated with "
    "temperature pushes A upward; and conditioning on a mediator can open a path through such a cause. Pre-specified "
    "sensitivity, the same for every mediator: (s1) year-by-month fixed effects in place of month and year; (s2) 2020 and "
    "2021 excluded; (s3) warm season May to September only; (s4) mediator on the previous day in place of the same day. If "
    "A under s1 falls on the other side of a decision threshold from the primary A, the verdict is unsettled. " + SEEN)

OUTDOORS = {
    "id": "heat-mech-outdoors",
    "kind": "bridge",
    "statement": ("People outdoors is a step between heat and shootings in New York City: daily 311 Noise - Street/Sidewalk "
                  "complaints, a proxy for street activity, rise with the day's maximum temperature, and adding them to the "
                  "daily model removes at least a quarter of the temperature slope of shootings."),
    "graph_evidence": [
        item("walking", "temp", "Graph sign for the first link is negative. Kim et al. 2022 (Korea Community Health Survey 2018): "
             "odds of walking practice 0.95 (0.94 to 0.97) per 1 C of the preceding week's "
             "daily maximum in rural areas and 0.98 (0.97 to 1.00) in urban areas; the graph holds the rural value only. The "
             "second association returned (walking after fan precooling, rectal temperature) is a laboratory finding on body "
             "temperature and is noise here.", [36444549], "-"),
        item("physical activity", "temp", "The relationship aggregates report 13 findings; the API returns one. "
             "Mora-Rodriguez et al. 2016 (573 adults, Spain, Greece, Germany): self-reported physical activity falls with "
             "ambient temperature, r = -0.277.", [27128938], "-"),
        item("physical exercise", "temp", "Ten laboratory findings on exercise time, intensity and heart rate in hot versus "
             "temperate chambers, signs mixed (6 plus, 3 minus); grounded to the concept 'hot'. They concern capacity under "
             "heat stress, not whether people are outdoors. Not read in abstract; not relied on.", [], "0"),
        item("walking", "viol", "Six of seven findings are negative and run from crime to walking (fear of crime, crime "
             "safety, violent crime reduce walking). The graph holds no finding that more people walking or outdoors raises "
             "violence; the second arrow of this pathway is absent from the graph.", [], "-"),
        item("physical activity", "viol", "Eight of nine negative: neighbourhood crime lowers physical activity, and active "
             "adolescents report less fighting. Again the reverse direction or an individual trait, not a daily exposure "
             "effect.", [], "-"),
        {"association_id": "variable search 'hot days'", "concepts": ["hot days (variable name)", "violent crime"],
         "n_findings": 1, "n_studies": 1, "direction": "+",
         "summary": ("Found only through variable names. Potgieter et al. 2022, Khayelitsha, South Africa, 2006-2016: days "
                     "at or above 25 C raise the cumulative relative risk of violent crime by up to 32% (the graph stores "
                     "RR 1.32 without an interval; the abstract gives none). A direct heat-violence finding that the concept "
                     "search for temperature and violence did not return."), "pubmed_ids": [35061073]},
    ],
    "literature": [
        {"citation": "Heat-shootings claim in this repository (claims/outcomes/heat-shootings.json)", "doi": None,
         "finding": "NYC daily shooting incidents: IRR 1.146 (1.130 to 1.163) per 5 C TMAX; the spline keeps rising to 35 C."},
        {"citation": "Reeping PM, Hemenway D. Inj Epidemiol 2020;7:31.", "doi": "10.1186/s40621-020-00260-3",
         "finding": "Chicago shootings rise with temperature more on weekends and holidays, read by the authors as routine activity."},
    ],
    "prediction": {
        "direction": "+",
        "magnitude": ("First link: IRR of daily Noise - Street/Sidewalk complaints per 5 C TMAX between 1.15 and 1.45. The graph "
                      "predicts the opposite sign for outdoor activity in heat (walking OR 0.95 to 0.98 per 1 C, activity "
                      "r = -0.28); I expect the graph's sign to appear only at the hot end, as a flattening: the spline RR of "
                      "the mediator rises less from 27 to 33 C than from 15 to 21 C, and for the bicycle counts the RR at 33 C "
                      "is at or below the RR at 27 C, while the shootings curve (already seen) rises 12% from 27 to 33 C. "
                      "Attenuation A between 0.10 and 0.35 for the noise proxy."),
        "support_if": ("confirmed: the mediator's IRR per 5 C has a lower limit above 1, its coefficient in B1 is positive "
                       "with a lower limit above 0, and A >= 0.25 with the lower bootstrap limit above 0.10."),
        "refute_if": ("contested: A < 0.10 with the upper bootstrap limit below 0.25, or the mediator does not rise with "
                      "temperature (upper limit of its IRR at or below 1). Anything else is unsettled."),
    },
    "plan": ("Primary mediator: daily count of 311 service requests with complaint_type 'Noise - Street/Sidewalk' by "
             "created_date, from 76ig-c548 (2010-2019) and erm2-nwe9 (2020 to present), 2010-01-01 to 2026-08-31. Secondary "
             "mediator, reported but not deciding: daily bicycle counts from ct66-47at (travelmode bike), summed over the "
             "sensors that report on at least 90% of the analysed days of a calendar year, year by year, 2014 to 2026; if the "
             "aggregation query does not complete, this is reported as not done. The shape comparison (spline RR at 27 and "
             "33 C) is reported for both and is descriptive. " + COMMON_PLAN),
    "alternatives": [
        "Noise complaints rise in heat because windows are open and complainants are at home, not because more people are on the street; the proxy then overstates the first link.",
        "Complaints and shootings share causes other than temperature within a month (block parties, holidays, the summer of 2020); sensitivity s1 and s2 address part of this.",
        "Physiology (irritability, sleep loss) acts on the same days; a positive A does not exclude it, and a small A may reflect a poor proxy.",
        "Bicycle counts on bridges and commuter routes measure travel, not people lingering outdoors at night when most shootings occur.",
    ],
    "prior": 0.3,
    "registrant": "Claude (graph-mechanisms agent), for Jeff Vernon",
    "chain": ["heat-shootings"],
}

INTOX = {
    "id": "heat-mech-intox",
    "kind": "bridge",
    "statement": ("Alcohol and drug intoxication is not a measurable step between heat and shootings in New York City: daily "
                  "FDNY EMS dispatches for drug and alcohol abuse rise with the day's maximum temperature by only a few "
                  "percent per 5 C, and adding them to the daily model removes less than a tenth of the temperature slope of "
                  "shootings."),
    "graph_evidence": [
        item("alcohol consumption", "temp", "The only temperature-alcohol finding is between countries and negative: "
             "Ventura-Cots et al. 2019, 193 countries, Spearman rho -0.5 between mean annual temperature and litres of "
             "alcohol per person. It is a climate comparison and says nothing about hot days; for a daily mechanism it is "
             "noise or a confounder of place. The graph has no finding that people drink more on hot days.", [30324707], "-"),
        item("drinking behavior", "temp", "Same study: share of drinkers falls with mean temperature, rho -0.49.", [30324707], "-"),
        item("alcohol consumption", "viol", "The second arrow is well supported: 72 of 76 returned associations are "
             "positive. Read: Nicosia et al. 2023, repeal of Sunday sales bans, homicide IRR 1.125 (1.02 to 1.24) and firearm "
             "homicide IRR 1.17 (1.03 to 1.33); Hohl et al. 2017, Philadelphia adolescents, firearm homicide aOR 4.1 (1.2 to "
             "14.0) for a history of alcohol use and 3.2 (1.1 to 9.1) for high outlet density; Rubanzana et al. 2015, Rwanda, "
             "homicide victimisation aOR 3.1, 10.1 and 11.5 by drinking level; Scribner et al. 1999, New Orleans tracts, "
             "elasticity 0.21 to 0.24 of homicide on off-sale outlet density. All four match their abstracts.",
             [37980844, 28055064, 26293322, 10371257], "+"),
        item("cocaine", "temp", "Marzuk et al. 1998, New York City medical examiner 1993-1995: on days at or above 31.1 C "
             "fatal cocaine overdoses were 33% more frequent (2.34 vs 1.76 per day), but the share of 4,638 homicide victims "
             "with cocaine in their blood was 18.9% on hot days and 19.5% on other days (P = .69). The graph stores the "
             "homicide comparison as a mean difference of -0.6 with p 0.69, which matches. Chang et al. 2023, California ED "
             "visits: cocaine overdose OR 1.159 (1.053 to 1.276) and cocaine use OR 1.044 (1.021 to 1.068) for the 50th to "
             "95th percentile of daily mean temperature; Auger et al. 2017, Quebec: cocaine overdose death OR 2.07 (1.15 to "
             "3.73) at 30 C vs 20 C weekly maximum.", [9628710, 37897873, 28645059], "+"),
        item("mental disorder", "temp", "Nori-Sarma et al. 2022, US ED visits 2010-2019: extreme heat days IRR 1.08 (1.07 to "
             "1.09) for any mental health condition and 1.08 (1.07 to 1.10) for substance use disorders (the latter found "
             "through the variable name 'ambient temperature'). Runkle et al. 2024: psychiatric ED visits in pregnancy IRR "
             "1.07 (1.01 to 1.14) per 5 C. Sun et al. 2021: 7.9% (5.2 to 10.7) excess ED visits for mental disorders on "
             "extreme heat days; the graph stores this as a relative risk of 7.9 (5.2 to 10.7), a mis-extraction.",
             [35195664, 38829735, 34819309], "+"),
    ],
    "literature": [
        {"citation": "Heat-shootings claim in this repository (claims/outcomes/heat-shootings.json)", "doi": None,
         "finding": "NYC daily shooting incidents: IRR 1.146 (1.130 to 1.163) per 5 C TMAX."}],
    "prediction": {
        "direction": "0",
        "magnitude": ("First link: IRR of daily DRUG dispatches per 5 C TMAX between 1.01 and 1.06, from the graph's "
                      "substance-use ED findings (IRR 1.08 for extreme heat days against a reference about 20 C cooler; OR "
                      "1.04 for cocaine use over about 10 C). Attenuation A between -0.02 and 0.08. The same is expected for "
                      "psychiatric dispatches (EDP)."),
        "support_if": ("confirmed (no measurable mediation): A < 0.10 with the upper bootstrap limit below 0.25, whatever "
                       "the first link. The first-link prediction is scored separately as hit if the IRR lies in 1.01 to 1.06."),
        "refute_if": ("contested: A >= 0.25 with the lower bootstrap limit above 0.10 and a positive mediator coefficient "
                      "in B1. Anything else is unsettled."),
    },
    "plan": ("Primary mediator: daily count of FDNY EMS dispatches (76xm-jjuj) with initial_call_type 'DRUG' (drug and "
             "alcohol abuse) or 'DRUGFC', by date of incident_datetime, 2006-01-01 to 2026-08-31. Secondary mediators, "
             "reported but not deciding: (a) psychiatric dispatches, initial_call_type EDP, EDPC or EDPM, the graph's 'mental "
             "disorder' candidate; (b) 311 complaints of complaint_type 'Drinking' (public drinking), 2010-01-01 to "
             "2026-08-31, from 76ig-c548 and erm2-nwe9. The call type DRUG does not separate alcohol from other drugs. "
             + COMMON_PLAN),
    "alternatives": [
        "EMS dispatches measure intoxication severe enough for an ambulance, not drinking among people who shoot or are shot; a small A may reflect a poor proxy and does not show that alcohol plays no part.",
        "Dispatch volume depends on people being in public to be seen and reported, so DRUG calls may partly measure street activity.",
        "Coding of call types changed over twenty years; year terms absorb level shifts but not within-year changes.",
    ],
    "prior": 0.75,
    "registrant": "Claude (graph-mechanisms agent), for Jeff Vernon",
    "chain": ["heat-shootings"],
}

if __name__ == "__main__":
    rec = {"heat-mech-outdoors": OUTDOORS, "heat-mech-intox": INTOX}[sys.argv[1]]
    print(claims.register(rec).relative_to(ROOT))
