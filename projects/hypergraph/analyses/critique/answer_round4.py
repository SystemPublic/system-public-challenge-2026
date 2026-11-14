"""Answers to the 30 blind referee reports of 13 Nov 2026 (critique/<id>.md; 27 in commit 47e4591, three
later ones on the discovery studies).

Each change goes through concord.claims.revise, which keeps the earlier outcome in `history`.
No registration is touched. Numbers marked "referee" are the referee's re-estimates. Numbers
marked "re-checked" were recomputed by the coordinator before being written here:
  further-subway-crime-per-million-repro  2,028 complaints over 1,226.8 million rides (1.653)
  further-chinatown-shift                 the two exact tract sets and the fixed-area changes
  graph-confounders-trees-surftemp        the duplicated PUMA populations and the corrected change
  transfer-chicago-weekday-pattern        the paired interval for Loop minus rest
  heat-mech-outdoors                      the shares by period and the next-day control

Run once: python analyses/critique/answer_round4.py
"""
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from concord import claims as C

DATE = "13 Nov 2026"


def load(i):
    return json.loads((C.OUT / f"{i}.json").read_text())


def answer(cid, note, reason, short, **changes):
    """Append `note` to the outcome's notes and apply `changes`. The stance is kept as it
    stands unless `changes` sets it or sets RECOMPUTE."""
    o = load(cid)
    if o.get("revision", {}).get("critique") == f"critique/{cid}.md":
        print("already answered:", cid)
        return
    ch = dict(changes)
    base = ch.pop("notes", o.get("notes") or "")
    ch["notes"] = base + f"\n\nAfter the referee ({DATE}): " + note
    if ch.pop("RECOMPUTE", False):
        ch.pop("stance", None)
    elif "stance" not in ch:
        ch["stance"] = o.get("stance")
    crit = {"report": f"critique/{cid}.md", "answer": short}
    if o.get("critique"):
        crit["earlier"] = o["critique"]
    ch["critique"] = crit
    C.revise(cid, ch, reason, f"critique/{cid}.md")
    print("revised:", cid)


def swap(text, old, new):
    assert old in text, old[:60]
    return text.replace(old, new)


# ---------------------------------------------------------------- verdict change

o = load("retimed-daytime-burglary")
answer(
    "retimed-daytime-burglary",
    "the verdict is changed from contested to unsettled. The second refutation condition (lower bound of the 95% "
    "interval above 0.95) was met by 0.003 with the one seed that was run, and the registration fixed 2,000 draws but "
    "no seed. The referee found the lower bound between 0.947 and 0.956 over 40 other seeds, above 0.95 in 62% of "
    "them, 0.9509 with 50,000 draws and 0.9499 in the registrant's own check with 20,000 draws. The registered "
    "procedure therefore does not place the bound on either side of the threshold, the condition is neither met nor "
    "unmet, and rule 2 applies (rule 9, added after this result, states this). Seven of eight further specifications "
    "run by the referee have a lower bound below 0.95 (recent period 2023-2025 0.999 (0.936 to 1.061); public housing "
    "excluded 0.985 (0.925 to 1.049); start and end within one day 0.988 (0.920 to 1.055)). Two things the outcome "
    "did not examine. Public housing rose from 5.2% to 10.9% of complaints and its ratio is 1.24 (1.00 to 1.52), "
    "which raises the citywide ratio. The recorded day is the start of the victim's absence, and complaints with a "
    "window of two days or more have a ratio of 1.11 (0.96 to 1.29) against 0.99 (0.92 to 1.06) for those within one "
    "day, which is what more Friday departures for long weekends would produce. What stands: no fall is seen, and a "
    "fall of more than about 5% to 7% is unlikely. The district contrast (-13.2%) has a permutation p of 0.08 over "
    "the 48 districts, so its bootstrap interval is too narrow. The graph finding PMID 35491751 concerns alcohol "
    "outlets and has no bearing on occupancy.",
    "Referee: the refutation bound depends on the bootstrap seed (met in 62% of seeds; 0.9509 at 50,000 draws); "
    "verdict changed from contested to unsettled under rules 2 and 9.",
    "accepted; verdict changed to unsettled",
    verdict="unsettled",
    prediction_scored="miss. The registered fall of 5% to 10% did not appear: the ratio is 1.011 (0.953 to 1.077). "
    "Neither condition is decided. The lower bound of the interval is 0.9525 with the seed that was run, 0.947 to "
    "0.956 over 40 other seeds and 0.9509 with 50,000 draws, so the registered procedure cannot place it above or "
    "below the 0.95 threshold of the second refutation condition. No sign of a fall is seen, and a fall of more than "
    "about 5% to 7% is unlikely.",
)

# ---------------------------------------------------------------- reproductions

o = load("further-subway-crime-per-million-repro")
notes = swap(o["notes"], " The table description says it counts arrests; the felony counts are below the complaint "
             "counts, which is consistent with that.", "")
notes = swap(notes, "The table's rates are therefore on a larger denominator and a smaller count than the State's "
             "number implies.",
             "The table's rates are therefore on a larger denominator and a smaller count than the State's number "
             "implies (the denominator is subway plus bus ridership; see the referee's check below).")
answer(
    "further-subway-crime-per-million-repro",
    "contested here means that the registered source was the wrong one. It does not mean that the State's figure "
    "fails. The State's 1.65 per million does reproduce: 2,028 NYPD felony complaints of the seven major types with "
    "the subway premise, 1 January to 14 December 2025, over 1,226.8 million subway rides in the MTA daily ridership "
    "table (sayj-mze2) give 1.653, and 1,695 complaints over 722.4 million rides in the same days of 2021 "
    "(vxuj-8kew) give 2.346, a fall of 29.5% (referee; re-checked by a fresh query on 13 November). This reading was "
    "found after the data were seen, so under rule 4 it decides nothing and the verdict stays. The registered table "
    "(yeek-jhmu) fails because its NYCT rate is per subway and bus rider: the riders implied by its NYCT rows equal "
    "subway plus NYCT Bus plus MTA Bus ridership in the MTA monthly table (xfre-bxip; median ratio 0.998 over 93 "
    "months), 1,578 million for January to November 2025, of which the subway is 1,171 million. The sentence that "
    "the table's counts are consistent with arrests has been removed: the counts are 90% of the complaint counts "
    "and the column description reads 'the count of Major Felonies committed'. Whether the 1,755 includes crimes on "
    "buses was not tested. R1's fall of 26.96% is just below the 27 to 33 percent band, not at its edge. With four "
    "of the six registered readings equal or close to R1, the registration tested one reading of one table.",
    "Referee: keep contested under rule 4; notes rewritten to say the State's figure reproduces (1.653) from NYPD "
    "subway complaints over subway ridership and that the registered source was the wrong one.",
    "accepted; verdict kept, notes and settle rewritten",
    notes=notes,
    prediction_scored=swap(o["prediction_scored"], "at the lower edge of the 27 to 33 percent band",
                           "just below the 27 to 33 percent band (26.96%)"),
    settle="The State's figure is reproduced to two decimal places (1.653 against 1.65, and a fall of 29.5% against "
    "30%) by NYPD subway-premise felony complaints over MTA subway ridership from 1 January to 14 December 2025. "
    "This reading was found after the data were seen. It should be registered as a new claim and tested on the full "
    "year 2025 and on 2024. The release should name its source and its rider count.",
    reproduction_found_after_data={
        "reading": "NYPD felony complaints (seven major types, premise TRANSIT - NYC SUBWAY, by occurrence date) "
                   "over MTA daily subway ridership, 1 January to 14 December",
        "y2025": {"complaints": 2028, "rides_millions": 1226.8, "rate_per_million": 1.653},
        "y2021": {"complaints": 1695, "rides_millions": 722.4, "rate_per_million": 2.346},
        "fall_percent": 29.5,
        "datasets": ["qgea-i56i", "sayj-mze2", "vxuj-8kew"],
        "status": "exploratory under rule 4; decides nothing; candidate for a new registration",
        "found_by": "critique/further-subway-crime-per-million-repro.md; re-checked 13 Nov 2026",
    },
)

o = load("further-chinatown-shift")
notes = swap(o["notes"], "AALDEF's area therefore holds more Asian and fewer Black and Hispanic residents than B1, "
             "which points to a boundary closer to the Chinatown core. An exploratory comparison of NTA unions "
             "(data/derived/further/chinatown_exploratory_unions.csv, not registered, decides nothing) found none "
             "that matches.",
             "An exploratory comparison of NTA unions (data/derived/further/chinatown_exploratory_unions.csv, not "
             "registered, decides nothing) found none that matches. The reason is given in the referee's finding "
             "below: the published table uses a different tract set in each year.")
rn = [dict(r) for r in o["research_needed"]]
rn[0] = {"question": "Will AALDEF confirm the two tract lists found by the referee (22 tracts for 2010, 25 for the "
                     "2018-22 ACS) and say why the area differs between the two years?",
         "data": "AALDEF tract lists; 2010 census and ACS 2018-22 table B03002",
         "design": "Request to AALDEF; register a new reproduction on the two exact sets, with the fixed-area change "
                   "as the prediction",
         "priority": "high"}
half95 = (o["city_effect"]["hi"] - o["city_effect"]["lo"]) / 2 / 1.645 * 1.96
se = half95 / 1.96
est = -o["city_effect"]["estimate"]
z = est / se
answer(
    "further-chinatown-shift",
    "the earlier diagnosis of the mismatch was wrong and has been removed. The referee searched tract sets near B1 "
    "and found one that matches AALDEF's 2010 table exactly on all five rows, and a different one that matches its "
    "2020 column exactly on all five rows (re-checked from the tract tables in data/derived/further). The 2010 set "
    "is B1 without tracts 22.02, 26.01, 26.02 and 28 and with tracts 41, 43 and 45 (22 tracts: total 116,722, white "
    "23,314, Black 8,457, Hispanic 30,227, Asian 52,613). The 2020 set is the 24 tracts of B1 plus tract 41 (25 "
    "tracts, ACS 2018-22: 120,173; 30,520; 11,094; 32,840; 41,024). None of the seven tracts that differ changed "
    "boundary between the censuses, so the published table compares two different areas. On AALDEF's 2010 set in "
    "both years the total fell 7.7%, Asian residents fell 25.7% against the ACS (90% margin -30.5 to -20.9) and "
    "12.9% against the 2020 census, white residents rose 15.8%, Black residents 15.1% and Hispanic residents fell "
    "7.4%. On its 2020 set the figures are -6.6%, -23.6% (-28.5 to -18.8), -11.6%, +15.0%, +8.1% and -7.8%. The "
    "published +3% total, +31% white, +31% Black, +9% Hispanic and the gain of about 12,000 white, Black and "
    "Hispanic residents come from the change of area; on the 2010 set the three groups together gained about 2,700. "
    "The Asian decline of 22% to 26% against the ACS does not depend on the change of area. The search was made "
    "after the data were seen and decides nothing under rule 4; the verdict rests on the registered readings. The "
    "row labelled 'Asian or Pacific Islander' is Asian alone (23 Pacific Islanders in the set). The gap between the "
    "ACS and the 2020 census can come from a census count that is too high, an ACS estimate that is too low, or "
    "real change within the 2018-22 window; the undercount check ran in one direction only, and the "
    "Post-Enumeration Survey estimated a net overcount of the Asian population nationally. Group quarters and "
    "student housing in tracts 41, 43 and 45 were not examined.",
    "Referee: keep contested; the notes' boundary diagnosis replaced by the finding that the published table uses "
    "two different tract sets.",
    "accepted; verdict kept, boundary diagnosis replaced",
    notes=notes,
    research_needed=rn,
    settle="AALDEF's confirmation of the two tract lists found by the referee, which reproduce its 2010 and 2020 "
    "columns exactly and are not the same area. With one area held fixed, the Asian decline is 24% to 26% against "
    "the 2018-22 ACS and 12% to 13% against the 2020 census, and the total population falls. Which of the ACS and "
    "the 2020 census is closer to the truth for Asian residents of these tracts is the second open question (the "
    "Post-Enumeration Survey by race, or administrative records such as NYCHA and school enrolment).",
    stance={"value": round(math.tanh(z / 2), 3), "lo": round(math.tanh((est - half95) / se / 2), 3),
            "hi": round(math.tanh((est + half95) / se / 2), 3), "z": round(z, 2),
            "note": "Agreement with the direction of change (a decline in Asian residents), not with the published "
                    "counts; the contested verdict concerns the counts. The interval in city_effect is a 90% ACS "
                    "margin and is converted to 95% here."},
)

answer(
    "repro-dot-2025-deaths",
    "contested here means that the open NYPD collision tables do not reproduce DOT's reconciled count. It does not "
    "mean that DOT's count is wrong; DOT's file is not published and the claim cannot test it. The referee "
    "re-queried both tables and obtained the same 229 and 268. Removing fatal crashes whose contributing factor is "
    "a medical event removes 12 deaths in 2025 and 8 in 2024 (217 and 260), so the one exclusion visible in the "
    "open data accounts for at most half of the 2025 gap, and 2025 stays outside the tolerance. Deaths that NYPD "
    "later reclassifies (suicides, homicides by vehicle, private property) are corrected in DOT's file and not in "
    "the open table. November 2025 has 7 recorded deaths against 13 to 29 in the other months and 23 in November "
    "2024; if November is incomplete in the open table the gap is larger than 24. DOT's fall from 2024 to 2025 is "
    "19.0% and the open tables give 14.6%. The referee recalled, without checking, that the open tables were also "
    "about 24 deaths above DOT in 2019 to 2021; if so the gap is the usual one and the 5% tolerance would be missed "
    "in most years. That is not verified here.",
    "Referee: keep contested; notes state that the label concerns reproduction from the open tables, not the "
    "correctness of DOT's count.",
    "accepted; verdict kept, meaning of the label stated",
    verdict_note="The open NYPD tables do not reproduce DOT's reconciled count of deaths (229 against 205). This is "
                 "not a finding that DOT's count is wrong. The injury counts reproduce within 0.5%.",
    stance=None,
)

answer(
    "repro-dcp-2025-completions",
    "the match (38,689 against 38,682) is on release 26Q2.1, later than the 25Q4 release the snapshot used. Of the "
    "2025 completions, 209 jobs with 19,800 units were updated after 15 January 2026 and DCP edited classaprop by "
    "hand on 19 jobs, so the agreement is a match after revision and not proof that DCP used exactly this rule. The "
    "referee recomputed R1 at row level and under three further variants and obtained 38,689 each time. The permit "
    "figure is not reproduced (18,539 against 17,673), and the referee found no simple rule that gives 17,673 in "
    "this release; permits dated December 2025 hold 4,138 units, so late recording is a plausible source. A "
    "row-level copy of the new-building rows was in the project cache before registration; the registration says "
    "only its headers were read, which cannot be verified. The interval in city_effect is the size of one earlier "
    "revision and not a sampling interval, so the stance computed from it had no statistical meaning and is now "
    "null, as for repro-dot-2025-deaths.",
    "Referee: keep confirmed; notes say the match is on release 26Q2.1 and that the permit figure was not "
    "reproduced; stance set to null (rule 6).",
    "accepted; verdict kept, stance null",
    verdict_note="Reproduced on release 26Q2.1, not on the 25Q4 release the snapshot used. The permit figure in the "
                 "same snapshot was not reproduced.",
    stance=None,
)

o = load("repro-mmr-cbd-speed")
st = dict(o["stance"])
st["note"] = ("The interval is the range over the five readings that reproduced both years, so it is conditioned on "
              "success and is narrower than the spread of the nine registered readings (fiscal 2026: 6.43 to 9.13 "
              "mph).")
answer(
    "repro-mmr-cbd-speed",
    "the referee rebuilt R1 from the 36 trip files and obtained 6.949 and 6.617 mph, identical to the outcome. "
    "Fiscal 2026 reproduces to 0.12 mph, which rounds to 6.6 and not to the published 6.5. The method is not "
    "identified: five of the nine registered readings pass, and the 0.2 mph tolerance is half of the 0.4 mph change "
    "the indicator reports. Ten of eleven further trip filters stay within tolerance (fiscal 2026 from 6.44 to "
    "6.70); standard-rate trips or positive fares give 6.44 and 6.87, which round to 6.4 and 6.9. A jackknife over "
    "days gives a standard error of 0.05 mph, so R1 is 2.3 standard errors from the stated fiscal 2026 value and is "
    "accepted because of the registered tolerance. The share of vendor 1, whose trips are 0.1 to 0.3 mph slower, "
    "fell from 25% to 19% of trips, and a change in the trip records is not ruled out as part of the fiscal 2026 "
    "fall; weather in February 2026 was not examined. The registration has no statement of which data the "
    "registrant had seen; the MTA speed series fetched earlier that day runs 1.7 mph higher and could not have been "
    "used to tune R1.",
    "Referee: keep confirmed; notes say fiscal 2026 reproduces to 0.12 mph (6.6 against 6.5 after rounding) and "
    "that the method is not uniquely identified.",
    "accepted; verdict kept",
    verdict_note="Level and direction reproduce within the registered 0.2 mph. Fiscal 2026 is 6.62 against the "
                 "published 6.5, and several trip filters pass, so DOT's method is not identified.",
    stance=st,
)

# ---------------------------------------------------------------- graph-confounder claims

o = load("graph-confounders-trees-surftemp")
ce = dict(o["city_effect"])
ce_new = {**ce, "estimate": -0.25, "lo": -0.99, "hi": 0.58,
          "label": ce["label"] + "; population density corrected for the four PUMAs that each cover two districts",
          "as_registered_with_density_error": {"estimate": ce["estimate"], "lo": ce["lo"], "hi": ce["hi"]}}
answer(
    "graph-confounders-trees-surftemp",
    "population density was wrong for eight districts. EHDP reports population by PUMA, and four PUMAs each cover "
    "two districts (101 and 102, 104 and 105, 201 and 202, 203 and 206). Each of the eight districts was given the "
    "population of its pair over its own area, so its density was overstated by about a factor of two. With each "
    "pair's population divided by the pair's combined area the change in the slope is -0.25 (-0.99 to +0.58) and "
    "the slope under the graph set is +0.25 (-0.56 to +1.07) (referee; re-checked from cd.csv: -0.25, -1.01 to "
    "+0.61 with another seed). The city effect now carries the corrected change and keeps the registered figure "
    "beside it. The verdict is the same, because condition (b) fails either way, but the corrected change is "
    "outside the predicted band of -0.3 to -1.2, so condition (a) is not met either and the prediction is a miss. "
    "The fall in the slope is a change of the exposure's denominator and not removed confounding: street trees per "
    "km2 of land equal street trees per km2 of street times the road share, and with trees per km2 of street as the "
    "exposure and no graph covariates the slope is -0.82 F per SD (-1.51 to -0.13, n = 54); adding population "
    "density and footprint share to that model moves it by +0.07 (-0.24 to +0.38). That measure was chosen after "
    "the data and decides nothing. The waterfront-lot bias in road share does not drive the result (change -0.44 "
    "with the waterfront lot share added). The graph_effect entry is the registrant's derivation from a correlation "
    "of 0.82 in one municipality (Prizren); across New York's districts the correlation of population density with "
    "surface temperature is 0.00 after the correction. Against the centre of the predicted range z is about +1 and "
    "against no change about -1, so the test does not separate the prediction from no change. The two lines of the "
    "script changed after registration cannot be shown from git, because the script was first committed with the "
    "outcome.",
    "Referee: keep unsettled; population density was overstated for eight paired-PUMA districts; corrected change "
    "-0.25 (-0.99 to +0.58) recorded and the prediction rescored as a miss.",
    "accepted; verdict kept, corrected change recorded, prediction rescored",
    city_effect=ce_new,
    prediction_scored="miss (rescored after the referee found an error in population density). With the density "
    "corrected the change is -0.25 (-0.99 to +0.58) F per SD, outside the predicted band of -0.3 to -1.2, and the "
    "slope under the graph set is +0.25 (-0.56 to +1.07), outside -0.7 to +0.2. Support condition (a) is not met, "
    "(b) is not met because the interval includes zero, and (c) is met. The refutation condition (a positive "
    "change) is not met. As first scored, with the density error, the change was -0.40 (-1.11 to +0.34) and "
    "condition (a) appeared met. Road share alone accounts for the fall (-0.73 (-1.38 to -0.26)).",
    RECOMPUTE=True,
)

answer(
    "graph-confounders-commute-obesity",
    "the stance is set to null. It was computed from the sign of the adjusted slope (+0.876), but the claim is "
    "about attenuation of that slope and its prediction was a miss, so the value presented a missed prediction as "
    "strong agreement. A paired bootstrap over neighbourhoods gives an attenuation of 28% with a 95% interval from "
    "-14% to +64%; 0.42 of resamples fall in the support range and 0.30 in the refutation range, so the data "
    "cannot tell an attenuation of one third from none. The registered thresholds were applied to a point estimate "
    "(rule 10 now asks that the interval be reported beside such a threshold). Leaving out UHF 305 puts the "
    "estimate in the support range and leaving out UHF 307 puts it in the refutation range. Without Manhattan the "
    "slope is -7.60 (-12.98 to -2.22); with borough terms it is -4.16 (-8.43 to +0.11), so the HC3 interval is "
    "likely too narrow for contiguous neighbourhoods. The random-covariate comparison that the registration named "
    "and did not run was run by the referee: six noise covariates give slopes from -6.59 to -5.36 and none of 2,000 "
    "draws reaches -4.40, so the attenuation is not what any eight covariates produce. Most of it rests on the "
    "2011 walkability index, which has a correlation of 0.85 with the exposure. The graph_effect entry compares a "
    "prevalence slope across 42 areas with an individual-level BMI difference (Flint et al. 2014); the two differ "
    "in unit, outcome and scale and should not be read as a comparison of size.",
    "Referee: keep unsettled; stance set to null (it was the sign of the slope, not the registered attenuation); "
    "bootstrap interval of the attenuation added.",
    "accepted; verdict kept, stance null",
    stance=None,
    stance_note="Null after the referee: the claim concerns the attenuation of the slope, and a stance computed "
                "from the sign of the adjusted slope showed a missed prediction as agreement.",
)

o = load("graph-confounders-surftemp-ed")
notes = swap(o["notes"], "which as a point estimate lies in the range of 0.003 to 0.008 derived from the graph's "
             "odds ratios, with an interval of -0.012 to +0.025 that includes zero.",
             "with an interval of -0.012 to +0.025, which includes zero and three times the value derived from the "
             "graph's odds ratios (0.003 to 0.008), so it neither agrees nor disagrees with the graph.")
answer(
    "graph-confounders-surftemp-ed",
    "the stance is set to null under rule 6. The claim predicts a change near zero, and the value of -0.242 was "
    "computed as though it predicted a negative change. Condition (a) is missed by 0.09 points, which is less than "
    "the effect of removing one district: leaving out one district at a time gives changes from +0.28 to +0.93, and "
    "12 of the 54 deletions bring the change inside the band. The statement that the living-alone coefficient "
    "agrees with the graph has been withdrawn. The living-alone measure is reported by PUMA, so eight districts "
    "carry the same value in pairs; a bootstrap that resamples the pairs together gives -1.49 to +3.30. The "
    "built-form secondary models used the population density that is overstated for those districts (see "
    "graph-confounders-trees-surftemp). With the density corrected the built-form model gives -3.1 (-11.8 to +6.5), "
    "a change of +7.3 (+0.4 to +15.9); with the waterfront lot share added the interval of that change includes "
    "zero (+7.0, -0.4 to +16.1). Road share has a correlation of +0.51 with surface temperature, so adding it "
    "removes part of the exposure. With borough terms the change is -0.83 (-5.46 to +3.35), which leaves the "
    "registered limit of condition (b). The covariate has a correlation of -0.15 with surface temperature and "
    "could move the slope little in either direction; the result is 0.52 standard errors from no change and 0.95 "
    "from the centre of the prediction.",
    "Referee: keep unsettled; stance set to null (rule 6); the claim of agreement with the graph for the "
    "living-alone coefficient withdrawn; density error in the secondary models recorded.",
    "accepted; verdict kept, stance null",
    notes=notes,
    stance=None,
    stance_note="Null after the referee (rule 6): the claim predicts a change near zero, for which the stance "
                "formula has no null that expresses the research direction.",
)

# ---------------------------------------------------------------- transfer claims

o = load("transfer-chicago-weekday-pattern")
comp = json.loads(json.dumps(o["components"]))
old_lmr = comp["loop_minus_rest_delta"]
comp["loop_minus_rest_delta"] = {
    "estimate": old_lmr["estimate"], "ci": [6.2, 8.0],
    "method": "paired bootstrap: the same weeks resampled for the Loop and for the rest of the system",
    "superseded_ci_independent_resamples": old_lmr["ci"]}
comp["loop_station_gap"] = ("State/Lake (station 40260), one of the 15 Loop stations, has no entries on 234 days of "
                            "the recent period. Excluding it from both periods changes the Delta by 0.2 points.")
answer(
    "transfer-chicago-weekday-pattern",
    "the interval for the Loop minus rest-of-system difference was wrong. The script drew separate bootstrap "
    "samples of weeks for the two areas, although both are observed in the same weeks. Resampling the same weeks "
    "for both gives 7.1 (6.2 to 8.0) in place of 7.1 (-1.1 to 15.7) (referee; re-checked from "
    "chicago_daily_entries.csv). The registered secondary prediction that the Loop changed more than the rest of "
    "the system is therefore clearly met. State/Lake, one of the 15 Loop stations, has no entries on 234 days of "
    "the recent period; the outcome said 15 stations for both periods. Excluding it from both changes the Delta by "
    "0.2 points. The verdict follows rule 1, since the registered primary (15.9) is above 13.1, but the threshold "
    "is not robustly exceeded: the referee's variants run from 12.4 (baseline 2018) to 16.1, and the excess over "
    "13.1 comes from the week of 28 January 2019. With weeks holding a day under 70% of the week's median dropped "
    "in both cities, the Loop is 12.9 (11.6 to 14.2) and the New York CBD 7.1 (6.1 to 8.2), a ratio of 1.8, so on "
    "a like-for-like basis the size still does not transfer. Against New York's registered office core (9.3 with "
    "the same rule) the ratio is 1.4, which the registration would call partial transfer; the Loop box is an "
    "office core and the New York CBD includes residential districts. The lower recovery of Loop entries (57% of "
    "2019 against 75%) is the simplest untested account of a larger Delta. The Friday deficit in the Loop (20.1%) "
    "exceeds the Monday deficit (16.4%), the reverse of New York.",
    "Referee: keep contested; Loop minus rest interval corrected to 7.1 (6.2 to 8.0) by a paired bootstrap; "
    "State/Lake gap recorded.",
    "accepted; verdict kept, interval corrected",
    components=comp,
    prediction_scored=o["prediction_scored"] + " Corrected after the referee: the Loop minus rest-of-system "
    "difference is 7.1 points (6.2 to 8.0) with a paired bootstrap, so the registered secondary prediction that the "
    "Loop changed more than the rest of the system is met.",
)

answer(
    "transfer-chicago-heat-shootings",
    "the referee rebuilt the daily series, obtained the same estimate (1.131, 1.120 to 1.143) and found it inside "
    "the transfer band under six further specifications; errors that allow for serial correlation widen the "
    "interval by about a tenth (1.119 to 1.144). What transfers is the average slope and not the shape of the "
    "dose-response. Fitted separately below and above 20 C, Chicago's slope is 1.148 (1.133 to 1.164) below and "
    "1.104 (1.084 to 1.124) above, and New York's from 2010 is 1.137 (1.112 to 1.164) below and 1.174 (1.139 to "
    "1.210) above. Chicago flattens on hot days and New York steepens, and the average slopes agree in part "
    "because Chicago has more cold days. The claim transfer-chicago-hot-end addresses the shape. New York refitted "
    "from 2010 gives 1.151 (1.132 to 1.170), so the difference in periods does not matter.",
    "Referee: keep confirmed; notes say the average slope transfers and the shape does not.",
    "accepted; verdict kept",
)

o = load("transfer-chicago-hot-end")
st = dict(o["stance"])
st["note"] = ("Computed from the shootings ratio alone, the half of part (a) that was not blind. It says nothing "
              "about part (b), which failed and makes the verdict unsettled.")
answer(
    "transfer-chicago-hot-end",
    "the stance (0.859) describes only the shootings half of part (a) and now carries a note saying so. The "
    "outcome's intervals use HC0 errors and daily counts are correlated from day to day; with errors that allow for "
    "this the shootings ratio is 1.058 (1.008 to 1.110) and the Divvy ratio 0.949 (0.876 to 1.027). Part (a) still "
    "passes and part (b) fails in every variant the referee ran. Part (a) depends on the composition of riders: "
    "subscribers make three quarters of trips and their trips fall on hot days (0.958), while casual trips do not "
    "fall (0.992, 0.924 to 1.066) and would not have met the 1.06 condition. The flattening may therefore be "
    "commuters avoiding heat and not fewer people on the street. Part (b) was predicted from New York street-noise "
    "complaints and tested with bicycle trips, and New York's own bicycle counts removed 0.021, so the failure of "
    "(b) agrees with New York's bicycle result and says little about its noise result. The shootings condition is "
    "met only on the full window (1.053, 0.987 to 1.123 on the Divvy window), and with autocorrelation-robust "
    "errors D for the shootings half is 3.4, below the 4 of rule 8.",
    "Referee: keep unsettled; stance annotated as covering the shootings half of part (a) only; HAC intervals and "
    "the rider-composition alternative recorded.",
    "accepted; verdict kept, stance annotated",
    stance=st,
)

# ---------------------------------------------------------------- heat mechanisms

answer(
    "heat-mech-outdoors",
    "the share removed by street-noise complaints is not stable over time. It is 0.24 (0.14 to 0.37) in 2010 to "
    "2019, just under the 0.25 threshold, and 0.84 (0.51 to 1.36) in 2022 to 2026 (referee; re-run). The pooled "
    "0.44 averages two regimes of 311 use, and the registered sensitivity without 2020 and 2021 (0.335) does not "
    "show this. On the 2010 to 2019 data alone the claim would have been unsettled. A negative control was run: "
    "next-day complaints, which today's street activity cannot cause, remove 0.10 (0.05 to 0.16) of the slope, and "
    "complaints seven days later or earlier remove 0.007 and 0.004. A small part of the same-day share therefore "
    "comes from variation that complaints and shootings share over a few days. After 2020 complaints are four to "
    "ten times their 2010 to 2014 level; either the proxy became a better measure of street gatherings, or "
    "complaints now respond to the same gatherings, disorder and police presence that go with shootings, which is "
    "a common cause and not a step from heat. The data cannot separate the two. Of three proxies that rise with "
    "heat, only this one removes the slope. The graph_effect entry records Kim 2022's rural odds ratio (0.95); "
    "the urban value, 0.98 (0.97 to 1.00), is the relevant one for New York, and the study concerns habitual "
    "walking over a week in Korea, so no comparison of size can be made.",
    "Referee: keep confirmed; notes state the instability by period (0.24 in 2010-2019, 0.84 in 2022-2026) and the "
    "next-day negative control (0.10).",
    "accepted; verdict kept, period split and negative control recorded",
    verdict_note="Confirmed on the pooled 2010 to 2026 series. The share is 0.24 in 2010 to 2019 and 0.84 in 2022 "
                 "to 2026, and a next-day negative control removes 0.10.",
)

answer(
    "heat-mech-intox",
    "the referee found no error, and the share stays between 0.09 and 0.19 in every variant (0.154 in 2010 to "
    "2019, 0.107 in 2022 to 2026, 0.017 for next-day dispatches). With street-noise complaints already in the "
    "model, drug dispatches still remove 0.166 (0.086 to 0.277) of the remaining slope, so the named alternative "
    "that dispatches measure people in public view does not account for the result as far as noise complaints "
    "measure street presence. The claim of no step is not supported (A is 5.9 standard errors from zero) and a "
    "step of a quarter of the slope is excluded (4.6 standard errors below 0.25); the registered rule has no "
    "verdict for a small non-zero share other than unsettled. Not addressed: same-day events such as parades, "
    "street parties and paydays, which produce both intoxication calls and shootings without heat acting through "
    "intoxication. The first-link hit is a match with a range the registrant built by assuming a reference "
    "temperature about 20 C cooler, which the abstract of Nori-Sarma et al. does not give.",
    "Referee: keep unsettled; variants and the unaddressed same-day-event alternative recorded.",
    "accepted; verdict kept",
)

# ---------------------------------------------------------------- further claims

o = load("further-zonej-demand-growth")
ce = dict(o["city_effect"])
ce["interval_year_clustered"] = {"lo": -1.027, "hi": -0.475,
                                 "note": "standard errors clustered by year (referee); about three times as wide as "
                                         "the registered HAC interval with 14 lags, which is kept in lo and hi "
                                         "because it is the registered one"}
ce["interval_year_block_bootstrap"] = {"lo": -1.176, "hi": -0.517}
ce["step_model"] = {"step_percent": -5.7, "step_lo": -7.1, "step_hi": -4.2, "trend_with_step": 0.031,
                    "trend_lo": -0.222, "trend_hi": 0.285,
                    "note": "trend plus a step after 30 June 2021, HAC 60 lags (referee); exploratory"}
answer(
    "further-zonej-demand-growth",
    "the registered interval is about three times too narrow. The trend is identified by nine to eleven years and "
    "residuals are correlated over much longer than 14 days. With standard errors clustered by year the trend is "
    "-0.752 (-1.027 to -0.475) percent a year; a bootstrap of whole calendar years gives -1.176 to -0.517. The "
    "upper limit is below +0.5 under every method, so the verdict does not depend on the interval. The result is a "
    "step and not a steady decline: a single step of -5.7% (-7.1 to -4.2) across the excluded pandemic window "
    "accounts for the whole negative trend, and with the step in the model the trend is +0.03 (-0.22 to +0.29) "
    "percent a year. The refutation condition is still met in the step model. After June 2021 the slope is +0.36 "
    "(about -0.02 to +0.75), so whether Zone J demand is growing now is open. The verdict means that the registered "
    "claim about Zone J over 2015 to 2025 was refuted. It does not contradict NYISO's statement, which concerns the "
    "whole state and forecasts. Measured load is net of behind-the-meter solar. The PAL series has no data for 1 to "
    "24 April 2017 and 1 to 7 April 2021, which the outcome did not report. With three applicable Gold Book "
    "editions the registration called for that part to be reported as not done; the mean and interval given should "
    "be read that way. The `last_modified_range` in the source record is the alphabetical minimum and maximum of "
    "date strings and not a range of dates. The design-day peak series is a straight line by construction.",
    "Referee: keep contested; year-clustered interval (-1.027 to -0.475) and the step finding (-5.7%; trend +0.03 "
    "with the step) recorded.",
    "accepted; verdict kept, wider interval and step finding recorded",
    city_effect=ce,
    verdict_note="The registered claim of growth above 0.5 percent a year in Zone J over 2015 to 2025 is refuted. "
                 "The decline is a step of about -5.7% across 2020 to 2021 and not a steady trend, and the result "
                 "does not test NYISO's statewide forecast.",
)

o = load("further-containers-rats-cd9")
ce = dict(o["city_effect"])
ce["interval_between_districts"] = {
    "lo": 0.69, "hi": 1.49,
    "note": "from the spread of the same rate ratio across the eleven Manhattan districts without containers (SD "
            "0.196 on the log scale, against 0.093 from the month-pair bootstrap) (referee); the registered "
            "interval is kept in lo and hi"}
ce["quasi_poisson_check"] = {"district_and_month_effects": [1.018, 0.832, 1.245],
                             "district_and_one_period_effect": [1.018, 0.704, 1.470],
                             "note": "the check the registration said would be reported; fitted by the referee"}
answer(
    "further-containers-rats-cd9",
    "the registered interval (0.86 to 1.23) is too narrow. The same rate ratio computed for each of the other "
    "eleven Manhattan districts, none of which had containers, runs from 0.77 to 1.56, a spread about twice what "
    "the month-pair bootstrap reports; with that spread the interval for CD9 is roughly 0.69 to 1.49. The "
    "quasi-Poisson check that the registration said would be reported was not fitted; the referee's fit gives "
    "1.018 (0.832 to 1.245) with district and month effects. The answer depends on the pre-trend and on repeat "
    "calls: CD9's share of the comparison districts' sightings rose in each of the three years before the bins "
    "(0.133, 0.144, 0.153, 0.156), a model with a linear trend gives 0.92 (0.80 to 1.07) and one without gives "
    "1.08 (0.99 to 1.17). Counting distinct addresses gives 1.11 (0.95 to 1.29); on that unregistered measure the "
    "refutation condition would be met, and it decides nothing. The bins were installed in April and May 2025, "
    "inside the pre-period, and July 2024 holds 17% of CD9's pre-period sightings (without the July pair the ratio "
    "is 1.06). District boundaries stand in for the treated blocks, so a district ratio near 1 is compatible with a "
    "fall on the streets that have bins. Support needed a ratio below about 0.83, so most of the predicted range "
    "could not have been confirmed.",
    "Referee: keep unsettled; wider interval from the spread across untreated districts (0.69 to 1.49) and the "
    "omitted quasi-Poisson check recorded.",
    "accepted; verdict kept, wider interval recorded",
    city_effect=ce,
)

answer(
    "further-datacentre-share-manhattan-v2",
    "the stance is set to null. Its interval resampled only the buildings outside the numerator, so the z of 36 "
    "measured nothing about reporting error or tenant metering, and the comparison with the national 4.4% is not "
    "like for like. The result describes the share visible in landlord-reported Local Law 84 electricity, not "
    "metered data-centre load: the unreported load would need to be 1.9 times the allocated load for the share to "
    "reach 4.4%, which is not a large factor for tenant-metered colocation. Condition (b) passes by 0.011 points "
    "on a point estimate whose bootstrap interval (0.96 to 1.06) includes the limit, and a PUE of 1.3 gives 0.98 "
    "and fails it (rule 10 asks that this be said). D1 counts campuses twice: 468 parent rows (2.16 TWh) and 685 "
    "child rows (1.68 TWh) are both summed. Without child rows the figures are 1.12 and 2.51 percent, and without "
    "parent rows 1.16 and 2.59; all four conditions remain met. The high figure is not an upper figure: fifteen "
    "other Manhattan rows whose largest use type is 'Data Center', mostly telephone central offices, hold 99 GWh, "
    "and with them the share is 2.84 percent. Each of conditions (b) and (c) rests on one building: the Western "
    "Union Building supplies 86 of the 173 GWh in the low figure and 111 Eighth Avenue 107 of the 289 GWh of "
    "excess; without the largest contributor the figures are 0.51 and 1.64. The join of 60 Hudson Street to 56 "
    "Hudson Street is correct, since both are addresses of the same building. The registrant had seen the first "
    "run's totals, which bounded the high figure between 1.66 and 3.9 before registration.",
    "Referee: keep confirmed; stance set to null (its interval measures nothing about the uncertainty that "
    "matters); double counting, omitted buildings and the 0.011-point margin recorded.",
    "accepted; verdict kept, stance null",
    stance=None,
    stance_note="Null after the referee: the bootstrap interval excluded reporting error and tenant metering, and "
                "the national figure is not a like-for-like comparison.",
    verdict_note="The registered conditions are met for landlord-reported electricity. Condition (b) passes by "
                 "0.01 points, and the result is an allocation, not a measurement of data-centre load.",
)

answer(
    "further-subway-crime-per-ride-by-hour",
    "the State's fall is measured from 2021 and the registered test measures the late-night rate from 2019, so the "
    "statement about 'the State's all-day fall' needs that qualification. On the State's baseline (calendar 2025 "
    "against 2021, same numerator and denominator) the all-day rate fell by 30% (ratio 0.70, 0.66 to 0.75), the "
    "0-5 rate by about 19% (0.81, 0.71 to 0.92) and the rate for hours 5 to 24 by about 35% (0.65, 0.61 to 0.70). "
    "The late-night fall since 2021 is smaller than the daytime fall, while against 2019 the late-night rate is "
    "level. This comparison was made after the data were seen and decides nothing; it is the natural second "
    "registration. The pooled late-night ratio near 1 hides opposite movements by offence: within the 0-5 band, "
    "felony assaults per entry are 1.95 (1.44 to 2.64) times their 2019 level, robbery 0.73 (0.55 to 0.95) and "
    "grand larceny 0.88 (0.77 to 1.02). 'At its 2019 level' is therefore not a statement about personal safety. "
    "Changes in how assaults are charged and recorded after 2020, and the overnight police patrols that began in "
    "2025, are rivals for the rise in assaults and were not examined. The 2019 monthly counts in the band are "
    "overdispersed (dispersion 2.6); a bootstrap over months gives 0.97 (0.85 to 1.10). The predicted rise of 1.2 "
    "to 2.2 is rejected (z = -3.8 from its lower edge), and a rate at its 2019 level is unsettled only because the "
    "refutation rule was written as an upper bound below 1.",
    "Referee: keep unsettled; notes add the comparison on the State's 2021 baseline (late night -19%, daytime "
    "-35%) and the doubling of late-night felony assaults per entry.",
    "accepted; verdict kept",
)

answer(
    "further-tidal-flooding-trend",
    "the referee reproduced the result with an independent bootstrap (2.00, 1.64 to 2.34) and it survives stricter "
    "dry-day rules, wind, season and influence checks. Three qualifications are added. The figure of 2.00 per 10 "
    "cm depends on the knot (1.73, 2.00, 2.38 and 2.88 at 0.30 to 0.45 m; 1.11 per 10 cm log-linear over all dry "
    "days) and should not be quoted as a general dose-response; the direction and the coastal specificity do not "
    "depend on it. The effect is concentrated in the Rockaway ZIP codes (2.01 to 2.52); Howard Beach, which "
    "supplies 625 of the 2,042 complaints, shows 1.25 (0.98 to 1.59) and Red Hook 1.10 (0.70 to 1.73). Several of "
    "the busiest dry days follow Hurricane Irene, and without the ten busiest days the estimate is 1.82 (1.60 to "
    "2.17). The other-ZIP series also rises, so some common factor moves complaints citywide on high-water days. "
    "The referee added the strongest evidence against the weather rival: complaints in the coastal set follow the "
    "part of the water level that is predictable from lunar and seasonal periods (1.083 per 10 cm, SE 0.020) as "
    "well as the remainder (1.136, SE 0.022). In data/derived/round2/tidal_trend/graph_flood_findings.json the "
    "records under 'flooding -> post-traumatic stress disorder' with PMIDs 29344631, 32758312 and 24368465 are "
    "trials of a psychotherapy technique called flooding and are not flood evidence; docs/round2.md already says "
    "that the concept 'flooding' is mis-grounded, and no outcome cites those records.",
    "Referee: keep confirmed; notes add the dependence of the size on the knot, the concentration in the Rockaway "
    "ZIP codes and the mis-grounded graph records.",
    "accepted; verdict kept",
    verdict_note="Direction and coastal specificity are confirmed. The size (2.00 per 10 cm) depends on the knot "
                 "and the effect is concentrated in the Rockaway ZIP codes.",
)

# ---------------------------------------------------------------- re-timed week

o = load("retimed-ems-presence")
answer(
    "retimed-ems-presence",
    "the result depends on Midtown. Without community district 105 the contrast is -0.016 (-0.036 to +0.004), and "
    "against the six other Manhattan districts it is -0.021 (-0.043 to +0.002); both intervals include zero. "
    "District 105 alone gives -0.071 and 104 gives -0.039, while 103 and 106 give 0.000 and +0.011 although 106 "
    "has nearly the largest thinning of entries. A dose-response within the business district is therefore not "
    "shown, and something particular to Midtown on Mondays and Fridays (events, hotels, shelter intake sites, a "
    "change in unit coverage) is not separated from office attendance. In favour of the claim, a night placebo "
    "(20:00 to 05:59) gives +0.009 (-0.014 to +0.032), every pairing of a baseline year with a recent year gives a "
    "negative contrast, and five other seeds give the same upper bound. The interval of the elasticity treats its "
    "denominator (-0.0639) as known and is somewhat too narrow; the verdict rests on the contrast. Incidents "
    "without a district code rose from about 1.0% to 2.4% of daytime incidents from January 2026, spread evenly "
    "over weekdays. Part of the contrast is a midweek rise (Wednesday index 0.998 to 1.013), which the statement "
    "'fell on Mondays and Fridays' does not say. The estimator and exposure files were committed with the outcome, "
    "so their state at registration rests on file times.",
    "Referee: keep confirmed; notes say the contrast loses significance without Midtown district 105 and against "
    "the rest of Manhattan.",
    "accepted; verdict kept, dependence on district 105 recorded",
    settle=o["settle"] + " The call type, which the dataset already holds, would separate office-hours illness "
    "and injury from calls tied to events, hotels and shelters in Midtown, where the fall is concentrated.",
    verdict_note="Confirmed under the registered pooled contrast. The fall is concentrated in Midtown (district "
                 "105); without it the interval includes zero.",
)

answer(
    "retimed-taxi-fhv-pickups",
    "the two registered measures disagree and the outcome did not say by how much. A slope of 0.5 implies a "
    "contrast of -0.038 between thirds, and the observed contrast (-0.011) is 2.1 standard errors from that "
    "prediction and 0.9 from no effect, so on the contrast the data favour no effect. The rank correlation between "
    "the two changes across the 147 zones is 0.11 (p = 0.17); the least-squares slope depends on a few zones with "
    "large thinning. With a business-district indicator the slope is 0.26 (SE 0.15). A weekend placebo fails: the "
    "change in the weekend-to-midweek ratio of pickups has a slope of -0.79 (SE 0.19) on the same exposure, so "
    "Mondays and Fridays are not the only days that moved and the registered ratio does not isolate office days. "
    "The bootstrap resamples seven and six weeks and its interval is too narrow; the 2018 against 2019 placebo "
    "gave a slope of -0.30. Leaving out one week at a time changes neither condition. An alternative that fits the "
    "pattern was not tested: trips moved to the home end on days worked at home. The February 2019 congestion "
    "surcharge falls in the baseline months. The registration's summary of PMID 32253258 omits that the odds "
    "ratio is per 100 additional trips.",
    "Referee: keep unsettled; notes add that the contrast is 2.1 standard errors from its own prediction and that "
    "the rank correlation across zones is 0.11.",
    "accepted; verdict kept",
)

# ---------------------------------------------------------------- graph splits

o = load("split-temp-asthma-ems")
answer(
    "split-temp-asthma-ems",
    "the bound in the outcome applies to variation within a calendar month at lags of up to four days, and not "
    "generally. The sign of the cool-season slope depends on how time is controlled: with year effects and four "
    "annual harmonics it is 0.985 (0.972 to 0.9985), which would have met the support condition, and with "
    "year-month effects and lags 0 to 21 it is 1.027 (1.006 to 1.049). Neither was registered and neither changes "
    "the verdict. The named alternative that asthma calls are absorbed by difficulty-breathing codes on cold days "
    "was tested by the referee and does not hide a cold effect: those codes rise with temperature in the cool "
    "half-year (1.0125, 1.0055 to 1.0196). Asthma dispatches fell from about 24,000 a year in 2014 to about 9,000 "
    "in 2024, which may reflect a change in call typing; the slope is the same before and after 2013. On the graph "
    "side, PMID 35817164 supplies several rows that are strata of one analysis (2.16 is the relative risk on days "
    "with high PM2.5 and 1.64 on days with low PM2.5), so '16 of 17 findings' overstates the number of independent "
    "results and '7 studies' is the better count.",
    "Referee: keep unsettled; settle states that the bound applies to within-month variation at short lags.",
    "accepted; verdict kept, scope of the bound stated",
    settle=swap(o["settle"], "The EMS series bounds the effect of a cold day within four days at under 1% per 5 C "
                "in either direction;",
                "The EMS series bounds the within-month effect of a cold day within four days at under 1% per 5 C "
                "in either direction, and the sign changes under other time controls (see notes);"),
)

answer(
    "split-temp-covid-growth",
    "the end of the file is incomplete and the registered filter did not protect against it. The last five days "
    "report 4, 2, 1, 1 and 0 admissions against about 20 a day before, and the week ending 12 October 2025 passes "
    "the filter of 20 with the most negative growth in the sample (-0.75). Dropping the last three weeks gives "
    "+0.0078 (-0.0009 to +0.0165); the verdict does not change. The sign is not stable: weighting weeks by the "
    "precision of the log ratio gives -0.0025 (-0.0129 to +0.0079), and single-week exposure windows alternate in "
    "sign, as serial dependence in weekly growth would produce. With five or six large waves, a chance alignment "
    "of two or three wave onsets with warm or cold spells can move a coefficient of this size, and year effects "
    "with harmonics do not remove it. Care-seeking and admission practice respond to weather within the same week "
    "and were not named as an alternative. The lower limit (-0.0036) lies just inside the registered range, so the "
    "weakest registered effect is not excluded; the earlier wording 'excludes effects more negative than -0.004' "
    "should be read with that. On the graph side, PMID 33162141 reports a negative coefficient for Bangladesh and "
    "a positive one for Afghanistan and describes mixed effects, so 'mixed' is the accurate code for that study.",
    "Referee: keep unsettled; the incomplete final weeks of the file recorded.",
    "accepted; verdict kept",
)

# ---------------------------------------------------------------- transit, trees, bridge

o = load("transit-gtrain-substitution")
ce = o["city_effect"]
sd = ce["permutation_sd"]
z = ce["estimate"] / sd
answer(
    "transit-gtrain-substitution",
    "the stance now uses the permutation standard deviation (0.032, z = 1.32) in place of the zone-clustered "
    "interval (z = 2.02), which the outcome itself called too narrow. The estimate is not a 4% rise in pickups "
    "overall: weighted by June pickups it is +0.020 (SE 0.020), in line with the registered Poisson (+0.016), so "
    "the result leans on the smaller treated zones. In the other direction, a triple difference with 2023 has a "
    "permutation p of 0.047 (1,000 draws); that was not a registered condition and decides nothing, but it "
    "suggests the registered permutation was the less powerful of two reasonable designs. The registration "
    "contradicts itself on zone 256, which is listed as treated for Metropolitan Av although that station shares a "
    "complex with the L; without it the estimate is +0.051 and p is 0.15. Several stations lie within metres of a "
    "zone border, so some substitute trips were recorded in control zones. The reference period is itself "
    "affected: with June as the only reference the estimate is +0.057 (permutation p 0.052), and treated zones "
    "were 2.8% above their June level in September after service returned. Support needed a coefficient of at "
    "least 0.064, so the lower half of the predicted range could not have been confirmed.",
    "Referee: keep unsettled; stance recomputed from the permutation standard deviation; weighted estimate and "
    "zone 256 recorded.",
    "accepted; verdict kept, stance recomputed",
    stance={"value": round(math.tanh(z / 2), 3), "lo": round(math.tanh((z - 1.96) / 2), 3),
            "hi": round(math.tanh((z + 1.96) / 2), 3), "z": round(z, 2),
            "note": "From the permutation standard deviation (0.0324), not the zone-clustered interval, which is "
                    "too narrow with seven treated zones."},
)

answer(
    "transit-weekday-pattern",
    "the referee rebuilt every deciding number from the cache and all three conditions hold under four further "
    "variants. Two qualifications are added. The size is nearer 7.4 points (6.4 to 8.5) than 8.7 once the weeks of "
    "the two disrupted Mondays are dropped by rule, and the Chicago transfer claim took its band from 8.7. "
    "Condition (b) passes narrowly: 68% of bootstrap resamples give a midweek range of 3 points or less. What is "
    "confirmed is the pattern and not its attribution to hybrid work. The rest of the system also changed by 4.2 "
    "points (2.2 to 6.6) and outer-borough AM-peak entries by 9.4, so about half of the CBD change is not specific "
    "to the office district; the largest change is in the AM peak (15.2 against 12.5 in the PM), which the "
    "office-worker account does not predict for entries inside the CBD; and the MTA's reduction of Monday and "
    "Friday service from 2023 is not tested. The two literature entries the registrant marked as unverified "
    "(Motte-Baumvol et al. and the SWAA day-of-week shares) should not be quoted as findings.",
    "Referee: keep confirmed; notes say the confirmed claim is the pattern, not its cause, and give the size "
    "without the two disrupted weeks (7.4).",
    "accepted; verdict kept",
    verdict_note="The weekday pattern is confirmed. Its attribution to hybrid work is not tested: about half of "
                 "the change also appears outside the business district.",
)

answer(
    "heat-trees-canopy-within-nta",
    "what is confirmed is the association and not the causal edge. The vegetation share 200 to 300 m away stays as "
    "large as the local share in every model, as the settle field already says. The referee reproduced the "
    "estimate and it survives clustering by NTA (-0.261 to -0.141), other NDVI thresholds and leaving out one NTA. "
    "A model with all rings together gives -0.165 (-0.214 to -0.115) for 0 to 25 m, nothing from 25 to 200 m and "
    "-0.212 (-0.332 to -0.093) for 200 to 300 m; the ring widths were chosen after the data. An alternative not "
    "addressed is shade on the sensor housing as distinct from cooler air: all of the local association lies "
    "within 25 m, which fits shading of the instrument at least as well as cooling. The slope differs by year "
    "(-0.14 in 2018, -0.24 in 2019) with largely different sensors. The published temperature file is a balanced "
    "panel (every sensor-day has 7 of 7 afternoon hours), so it was gap-filled or cleaned before publication and "
    "the registered 5-of-7 filter removed nothing. On like-for-like radius the city slope is larger than Ziter's. "
    "The graph row for PMID 35060045 stores r = -1.0, which is not a published number; it was used for direction "
    "only.",
    "Referee: keep confirmed; label says the confirmed claim is the association; ring model, instrument shading "
    "and the difference between years recorded.",
    "accepted; verdict kept",
    verdict_note="The association is confirmed. Vegetation 200 to 300 m away predicts temperature as strongly as "
                 "vegetation within 50 m, so the local causal reading is not supported.",
)

answer(
    "bridge-crz-injury-crashes-v2",
    "the referee reproduced the deciding numbers and every variant leaves the verdict unsettled. The two areas are "
    "not the same kind of road network: the north area includes limited-access highways that hold 12% to 14% of "
    "its injury crashes, against almost none in the zone; without them the estimate is +6.1% (-0.8 to +13.5) and "
    "the placebo +16.4%. The way crash locations are recorded changed, and differently in the two areas: records "
    "with an on-street name only (about 750 a year in the north area in 2022 and 2023) are gone by 2025, and the "
    "2024 placebo difference sits in that class. The registration treated geocoding as a matter of coverage only. "
    "The estimate depends on the pre-period: -4.9% against 2024 alone, +9.5% against 2022-2023 alone. Recovering "
    "records without coordinates by matching street names gives +4.1% (-3.2 to +12.0), so missing coordinates do "
    "not explain the 2024 divergence. The verdict 'bridged' could not have been reached: the rule required it at "
    "three bias points that are 0.13 apart on the log scale, and the window in which it holds at one point is 0.04 "
    "wide. The registration attributes PMID 23411678 to Teschke et al. 2012; it is Harris et al., Injury "
    "Prevention 2013, and its odds ratio applies to intersections only. There is no prereg branch for this claim, "
    "so the evidence that it was public before the query is weaker than for claims that have one.",
    "Referee: keep unsettled; highway asymmetry, the change of record format, the unreachable 'bridged' outcome and "
    "the wrong attribution of PMID 23411678 recorded.",
    "accepted; verdict kept",
)

# ---------------------------------------------------------------- three later reports (discovery studies)

o = load("graph-concordance-matrix")
ce = o["city_effect"]
se = (ce["hi"] - ce["lo"]) / 3.92
bench = 0.642
zb = (ce["estimate"] - bench) / se
answer(
    "graph-concordance-matrix",
    "the referee recommended unsettled. The verdict is kept as confirmed, because the registered support condition "
    "is written on the agreement rate itself (at least 60% and above the 97.5th percentile of the area-shuffle "
    "null, 58.7%), the rate is 66.1%, and rule 1 binds. What is confirmed is narrower than the registered "
    "statement reads. The test shows that these indicators, coded so that higher means more of an adverse "
    "condition, are positively correlated across neighbourhoods after partialling poverty. It does not show that "
    "the graph's signs carry information about the city. Of the 109 literature signs 105 are positive, and a rule "
    "that ignores the literature and always answers 'positive' scores 70 of 109 (64.2%) against the literature's 72 "
    "(66.1%). The four pairs with a negative literature sign split three to one (Fisher exact p = 0.13), and the "
    "registered sign-shuffle null gives p = 0.14. The exposure-with-outcome pairs, where the literature's sign says "
    "something about a cause, agree at 29 of 56 (51.8%), which is chance; the 41 pairs of two health outcomes agree "
    "at 82.9%, the same as always-positive. The lower bootstrap bound (59.6%) is below the 60% threshold and 5% of "
    "resamples fall below it, so the condition is met on a point estimate about 1.3 standard errors above its "
    "threshold (rule 10). An always-positive rule passes the 60% threshold in 78% of resamples, so a literature "
    "with no information beyond valence would usually have been confirmed. Seven indicators each appear in 12 to "
    "19 pairs; leaving one indicator out moves the rate between 63.5% and 70.0%. A pair qualifies only with three "
    "studies and 80% consistency, and published associations between two adverse conditions are almost all "
    "positive, so the qualifying set holds almost no negative signs by construction. The stance is now measured "
    "against the always-positive rate and not against 50%.",
    "Referee recommended unsettled. Kept confirmed under rule 1 (the registered condition is on the point "
    "estimate and is met); statement of what is confirmed narrowed and stance measured against the "
    "always-positive benchmark.",
    "partly accepted; verdict kept under rule 1, meaning narrowed, stance reduced",
    verdict_note="Confirmed only in this sense: adverse indicators are positively correlated across neighbourhoods "
                 "after partialling poverty. The literature's signs add two pairs in 109 to a rule that always "
                 "answers 'positive' (66.1% against 64.2%; sign-shuffle p = 0.14), and exposure-with-outcome pairs "
                 "agree at 29 of 56.",
    prediction_scored=o["prediction_scored"] + " After the referee: the hit is on the registered rate. Against the "
    "always-positive rule (64.2%) the excess is 1.8 points, and the lower bootstrap bound (59.6%) is below the 60% "
    "threshold.",
    stance={"value": round(math.tanh(zb / 2), 3), "lo": round(math.tanh((ce["lo"] - bench) / se / 2), 3),
            "hi": round(math.tanh((ce["hi"] - bench) / se / 2), 3), "z": round(zb, 2),
            "note": "Measured against the always-positive rate of 64.2%, not against 50%: the stance is the "
                    "agreement the literature's signs add beyond common valence."},
)

for cid, zc, zn in (("graph-triad-cold-asthma-absence", 3.81, 4.19), ("graph-triad-hot-asthma-absence", 0.32, 0.44)):
    o = load(cid)
    st = C.endpoint_stance(zc, zn)
    st["note"] = ("Rules 7 and 8: agreement of the endpoint with the composed prediction, scaled by how well the "
                  "test separates the chain from no effect. The earlier value was the stance of a direct effect "
                  "against its null.")
    if cid.startswith("graph-triad-cold"):
        answer(
            cid,
            "the verdict is changed from confirmed to unsettled. The claim is a bridge with an endpoint test and "
            "was registered more than six hours after rule 8, so its support condition could not be a test of "
            "direction only. The endpoint lies 3.81 standard errors from the composed prediction (1.0073) and 4.19 "
            "from no effect, D = 3.0, below the 4 that rule 8 requires, and the registration itself reported an "
            "expected D of 0.23. The endpoint rejects the chain's size while agreeing with its sign: the composed "
            "0.7% and the city's 10% differ by a factor of about 13, and the asthma path accounts for about 8% of "
            "the log ratio. The direct association between cold days and absence is robust. The referee rebuilt "
            "the series and obtained 1.101 (1.053 to 1.152); clustered by school year the interval is 1.039 to "
            "1.167; with fixed effects for each week of each school year the ratio is 1.096 (1.040 to 1.155); from "
            "2009-10 onward it is 1.071 (1.016 to 1.129) and 1.070 (1.015 to 1.127) with laboratory-confirmed "
            "influenza in the model, so influenza, the rival the registrant named, does not account for it. "
            "Dropping days near a recess raises the estimate (1.128), a placebo exposure two days ahead gives "
            "1.009 (0.968 to 1.051), and absence rises in steps with cold (1.06 at 0 to 5 C, 1.11 at -5 to 0 C, "
            "1.34 at or below -5 C). The size depends on a few extreme days (1.070 without the five "
            "highest-absence exposed days); a defensible range is 1.06 to 1.10. The alternative that remains is a "
            "direct effect of cold on attendance that has nothing to do with health (travel, parents keeping "
            "children home, ice). This association should be registered as a direct claim that does not name "
            "asthma. The snow indicator used the previous kept school day and not the previous calendar day "
            "(corrected: 1.100).",
            "Referee: a bridge registered after rule 8 whose endpoint test does not discriminate (D = 3.0); "
            "verdict changed from confirmed to unsettled; stance recomputed by the endpoint formula.",
            "accepted; verdict changed to unsettled",
            verdict="unsettled",
            stance=st,
            prediction_scored="partial. The direct association is present and robust: 1.101 (1.053 to 1.152), 1.07 "
            "with an influenza control. The triad is not supported as an account of it: the endpoint is 3.81 "
            "standard errors above the composed 1.0073 and D = 3.0, below the 4 of rule 8, so the test does not "
            "separate the chain from no effect, and the asthma path accounts for about 8% of the log ratio.",
            settle=o["settle"] + " The referee added the influenza control (1.070, 1.015 to 1.127, from 2009-10). "
            "The cold-day association should be registered as a direct claim that does not name asthma and tested "
            "on school years not used here.",
            verdict_note="Unsettled as a bridge (rule 8, D = 3.0). The direct cold-day association with absence is "
                         "robust (1.10, 1.05 to 1.15; 1.07 with an influenza control) and is not explained by the "
                         "asthma chain.",
        )
    else:
        answer(
            cid,
            "the referee reproduced the estimate (1.009, 0.970 to 1.050) and no variant moves it away from 1. A "
            "placebo exposure, TMAX at or above 30 C two days later with today's exposure in the model, gives "
            "1.021 (0.985 to 1.058), as large as the estimate itself, so the small positive point estimate "
            "reflects the end-of-year decline in attendance and not the day's heat; it comes from May and June "
            "(September alone 0.995). Rule 8 gives the same verdict as rule 2: D = 0.1. The stance is now the "
            "endpoint stance of rules 7 and 8 (0.04), as for the cold arm. A citywide rate cannot show an effect "
            "confined to schools without air conditioning, and air-conditioning status by school and year is not "
            "in the open files. The published relative risk (PMID 27343213) concerns all ages in Hong Kong, where "
            "adults were the most sensitive and children under 5 the least.",
            "Referee: keep unsettled; placebo two days ahead (1.021) recorded; stance set by the endpoint formula.",
            "accepted; verdict kept, placebo recorded",
            stance=st,
        )

print("done")
