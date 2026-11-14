#!/usr/bin/env python3
"""Expand family-level EHDP adjudications into adjudications_ehdp.jsonl.

The LLM pass matched at the *family* level (an EHDP measure family shares one
construct; Number/Percent/rate variants don't change the concept match).
This script holds that table and expands it to one verdict row per measure.
Run: python3 -I mapping/expand_adjudications_ehdp.py
"""
import json
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "mapping" / "out"
nyc = pd.read_csv(OUT / "nyc_concepts.csv")

# family (prefix of measure label before last ",") -> verdicts
F = {
    "Commercial insecticide use": [("W3DRcIxD47", "broader-narrower", "high",
        "SPG concept 'insecticide' covers the substance measured (usage volume by commercial exterminators)")],
    "Commercial use of insecticides": [("W3DRcIxD47", "broader-narrower", "high",
        "'insecticide' covers the substance; measure is its commercial-use quantity")],
    "Commercial use of insecticides (Pyrethroid/Pyrethrin)": [("W3DRcIxD47", "broader-narrower", "high",
        "pyrethroid/pyrethrin products are insecticides; construct is the chemical class")],
    "Commercial use of insecticides (Organophosphate)": [("W3DRcIxD47", "broader-narrower", "high",
        "organophosphates are insecticides; measure is use quantity")],
    "NYC agency use of insecticides": [("W3DRcIxD47", "broader-narrower", "high",
        "'insecticide' covers the substance applied by agency contractors")],
    "Commercial use of fungicides": [("TBsyBcNA1b", "broader-narrower", "high",
        "'fungicide' covers the substance measured")],
    "NYC agency use of fungicides": [("TBsyBcNA1b", "broader-narrower", "high",
        "'fungicide' covers the substance applied by agencies")],
    "Commercial use of herbicides": [("RsRHLzVNE9", "broader-narrower", "high",
        "'herbicide' covers the substance measured")],
    "NYC agency use of herbicides": [("RsRHLzVNE9", "broader-narrower", "high",
        "'herbicide' covers the substance applied by agencies")],
    "Commercial use of rodenticides": [("ilXDKtVKMy", "broader-narrower", "high",
        "'rodenticide' covers the substance measured")],
    "NYC agency use of rodenticides": [("ilXDKtVKMy", "broader-narrower", "high",
        "'rodenticide' covers the substance applied by agencies")],
    "Commercial use of \"Best Practice\" products": [("z5gUrT2Y3H", "related-component", "medium",
        "'Best Practice' products are low-toxicity pesticides; 'pesticide' is the construct")],
    "NYC agency use of \"Best Practice\" products": [("z5gUrT2Y3H", "related-component", "medium",
        "low-toxicity pesticide products; construct is 'pesticide'")],
    "NYC agency use of glyphosate": [("7P8u0wR1ts", "broader-narrower", "high",
        "glyphosate herbicide; measure is its application quantity")],
    "NYC agency use of mosquito control": [("qG8bpAf84m", "broader-narrower", "high",
        "'mosquito control' is the activity measured (larvicide/adulticide applications)"),
        ("f1Peu4U_jE", "related-component", "medium",
         "NYC mosquito control targets West Nile fever vectors; related public-health construct")],
    "Personal pesticide use": [("z5gUrT2Y3H", "broader-narrower", "high",
        "household pesticide use; 'pesticide' is the construct")],
    "Disinfection by-products (TTHM)": [("Jmy1CVYSF8", "broader-narrower", "medium",
        "trihalomethane concentrations in drinking water; 'drinking water' is the exposure medium (no TTHM-specific SPG concept)")],
    "Disinfection by-products (HAA5)": [("Jmy1CVYSF8", "broader-narrower", "medium",
        "haloacetic acids in drinking water; 'drinking water' is the exposure medium")],
    "Race/ethnicity": [("VUbS0APNXf", "broader-narrower", "high",
        "Census race/ethnicity population composition vs 'racial group' construct"),
        ("EhpdS79G1u", "related-component", "medium", "'ethnicity' construct overlaps the measure's race/ethnicity categories")],
    "Asthma hospitalizations (adults)": [
        ("EAshH_Ko3h", "broader-narrower", "high", "'asthma' is the disease; measure is severe asthma outcomes (hospitalizations)"),
        ("Gl-I4wBZ5r", "broader-narrower", "medium", "'hospitalization' is the care event type in the measure")],
    "Asthma hospitalizations (age 4 and under)": [
        ("EAshH_Ko3h", "broader-narrower", "high", "'asthma' is the disease construct"),
        ("PQ1nPOBjAX", "broader-narrower", "high", "'childhood asthma' matches the age-4-and-under population"),
        ("Gl-I4wBZ5r", "broader-narrower", "medium", "'hospitalization' is the care event")],
    "Asthma hospitalizations (age 5 to 17)": [
        ("EAshH_Ko3h", "broader-narrower", "high", "'asthma' construct"),
        ("PQ1nPOBjAX", "broader-narrower", "high", "pediatric population matches 'childhood asthma'"),
        ("Gl-I4wBZ5r", "broader-narrower", "medium", "'hospitalization' care event")],
    "Asthma ED visits (age 5 to 17)": [
        ("EAshH_Ko3h", "broader-narrower", "high", "'asthma' construct"),
        ("PQ1nPOBjAX", "broader-narrower", "high", "pediatric population matches 'childhood asthma'"),
        ("nS9fqJ01TW", "related-component", "medium", "'emergency department' is the care setting of the visits")],
    "Asthma ED visits (age 4 and under)": [
        ("EAshH_Ko3h", "broader-narrower", "high", "'asthma' construct"),
        ("PQ1nPOBjAX", "broader-narrower", "high", "'childhood asthma' matches the age group"),
        ("nS9fqJ01TW", "related-component", "medium", "'emergency department' care setting")],
    "Asthma ED visits (adults, NTA)": [
        ("EAshH_Ko3h", "broader-narrower", "high", "'asthma' construct"),
        ("nS9fqJ01TW", "related-component", "medium", "'emergency department' care setting")],
    "Asthma ED visits (adults)": [
        ("EAshH_Ko3h", "broader-narrower", "high", "'asthma' construct"),
        ("nS9fqJ01TW", "related-component", "medium", "'emergency department' care setting")],
    "Asthma (adults)": [("EAshH_Ko3h", "broader-narrower", "high",
        "adult asthma prevalence; 'asthma' is the disease construct")],
    "Adults with asthma": [("EAshH_Ko3h", "broader-narrower", "high",
        "ever-diagnosed adult asthma; 'asthma' construct")],
    "Asthma (youth)": [
        ("EAshH_Ko3h", "broader-narrower", "high", "'asthma' construct"),
        ("PQ1nPOBjAX", "broader-narrower", "high", "high-school population matches 'childhood asthma'")],
    "Children ever diagnosed with asthma": [
        ("EAshH_Ko3h", "broader-narrower", "high", "'asthma' construct"),
        ("PQ1nPOBjAX", "broader-narrower", "high", "ages 1-13 match 'childhood asthma'")],
    "Children still with asthma": [
        ("EAshH_Ko3h", "broader-narrower", "high", "'asthma' construct"),
        ("PQ1nPOBjAX", "broader-narrower", "high", "'childhood asthma' population match")],
    "Children with a recent asthma attack": [
        ("EAshH_Ko3h", "broader-narrower", "high", "recent asthma attacks; 'asthma' construct"),
        ("PQ1nPOBjAX", "broader-narrower", "high", "'childhood asthma' population match")],
    "Heat hospitalizations": [
        ("PtQBvGm5CM", "broader-narrower", "high", "hospitalizations for heat stress; 'heat illness' is the construct"),
        ("FDJ4Gulj_Q", "related-component", "medium", "'hyperthermia' is the physiologic mechanism behind heat stress admissions"),
        ("rYCo7LTyzN", "related-component", "medium", "'heat stroke' is the severe subtype included in heat-stress hospitalizations"),
        ("Gl-I4wBZ5r", "broader-narrower", "medium", "'hospitalization' is the care event")],
    "Heat ED visits": [
        ("PtQBvGm5CM", "broader-narrower", "high", "ED visits due to heat-related illness; 'heat illness' construct"),
        ("rYCo7LTyzN", "broader-narrower", "medium", "'heat stroke' is a named cause of these visits"),
        ("2M0TDlEdLk", "broader-narrower", "medium", "'heat exhaustion' is a named cause of these visits"),
        ("nS9fqJ01TW", "related-component", "medium", "'emergency department' care setting")],
    "Heat stress: 5-year emergency department visits": [
        ("PtQBvGm5CM", "broader-narrower", "high", "5-year average of heat-illness ED visits; 'heat illness' construct"),
        ("rYCo7LTyzN", "broader-narrower", "medium", "'heat stroke' subtype"),
        ("2M0TDlEdLk", "broader-narrower", "medium", "'heat exhaustion' subtype"),
        ("nS9fqJ01TW", "related-component", "medium", "'emergency department' care setting")],
    "Heat deaths": [
        ("FDJ4Gulj_Q", "broader-narrower", "high", "deaths directly attributed to heat; 'hyperthermia' is the proximate cause construct"),
        ("PtQBvGm5CM", "broader-narrower", "medium", "'heat illness' covers fatal heat-stress cases"),
        ("rYCo7LTyzN", "related-component", "medium", "'heat stroke' is the classic fatal heat subtype")],
    "Cold deaths": [
        ("VbhaEHYy0f", "related-component", "medium", "deaths due to cold weather; 'cold weather' is the exposure construct"),
        ("h0Aryv0NjW", "related-component", "medium", "'hypothermia' is the proximate cold-death mechanism")],
    "Heat events": [
        ("wpUeTjUbAc", "broader-narrower", "high", "counts of 90/95/100-degree days operationalize 'extreme heat' exposure"),
        ("k9BAffdSqv", "broader-narrower", "high", "multi-day hot events match 'heat wave'")],
    "Households with AC": [("OnRtQgvIkg", "equivalent", "high",
        "functioning air-conditioner prevalence; 'air conditioning' construct")],
    "Adults with air conditioners": [("OnRtQgvIkg", "equivalent", "high",
        "individual AC ownership; 'air conditioning' construct")],
    "Older adults with AC": [("OnRtQgvIkg", "equivalent", "high",
        "AC ownership among 65+; 'air conditioning' construct")],
    "Heat Vulnerability Index": [
        ("PtQBvGm5CM", "related-component", "medium", "HVI predicts community heat-illness impact; 'heat illness' is the outcome construct"),
        ("UbF0-c8zHb", "related-component", "medium", "'urban heat island' is the environmental driver HVI aggregates")],
    "Surface temperature": [("sSuplgYnDQ", "equivalent", "high",
        "satellite daytime summer surface temperature; 'surface temperature' construct")],
    "Grass and tree cover": [
        ("RF7tCwCaa5", "equivalent", "high", "percent land covered by trees/grass/plants is exactly 'vegetation cover'"),
        ("I2CN3brExA", "related-component", "medium", "'tree' is the dominant component of the cover measure"),
        ("lHLIKbfnYp", "related-component", "medium", "'green space' is the urban-planning framing of vegetated land")],
    "Tree shade": [
        ("I2CN3brExA", "broader-narrower", "high", "canopy shade from 'tree' cover"),
        ("RF7tCwCaa5", "broader-narrower", "medium", "tree canopy is a component of 'vegetation cover'"),
        ("lHLIKbfnYp", "related-component", "medium", "'green space' framing")],
    "Park access": [
        ("6DTj2ennMm", "broader-narrower", "high", "walk-to-a-park access; 'park' construct"),
        ("lHLIKbfnYp", "broader-narrower", "medium", "'green space' access framing")],
    "Carbon monoxide hospitalizations": [
        ("CCVZABeZcW", "broader-narrower", "high", "CO-exposure hospitalizations; 'carbon monoxide' construct"),
        ("ET5-8-2eBO", "broader-narrower", "high", "severe CO exposure is 'carbon monoxide poisoning'"),
        ("Gl-I4wBZ5r", "broader-narrower", "medium", "'hospitalization' care event")],
    "Carbon monoxide emergency department visits": [
        ("CCVZABeZcW", "broader-narrower", "high", "'carbon monoxide' exposure construct"),
        ("ET5-8-2eBO", "broader-narrower", "high", "'carbon monoxide poisoning' outcome"),
        ("nS9fqJ01TW", "related-component", "medium", "'emergency department' care setting")],
    "Carbon monoxide deaths": [
        ("ET5-8-2eBO", "broader-narrower", "high", "CO deaths are 'carbon monoxide poisoning' deaths"),
        ("CCVZABeZcW", "broader-narrower", "high", "'carbon monoxide' exposure construct")],
    "Carbon monoxide incidents": [("CCVZABeZcW", "broader-narrower", "high",
        "FDNY CO detections; 'carbon monoxide' construct")],
    "Carbon monoxide": [("CCVZABeZcW", "broader-narrower", "high",
        "CO incidents without alarms; 'carbon monoxide' construct")],
    "Nitrogen dioxide": [("DC_F0GO0WQ", "equivalent", "high",
        "ambient NO2 concentration; 'nitrogen dioxide' construct")],
    "Ozone": [("JMeOsYIcbL", "equivalent", "high", "ambient ozone concentration; 'ozone' construct")],
    "PM2.5 (Fine particles)": [
        ("gX6h_gZWHH", "equivalent", "high", "fine-particle concentrations; 'particulates' construct"),
        ("jtzZPZ8DQh", "equivalent", "high", "'PM 2.5' names the exact pollutant measured"),
        ("P6IzhScRdx", "broader-narrower", "medium", "'air pollution' is the parent construct")],
    "Citywide PM2.5": [
        ("gX6h_gZWHH", "equivalent", "high", "'particulates' construct"),
        ("jtzZPZ8DQh", "equivalent", "high", "'PM 2.5' exact pollutant")],
    "PM2.5 (Fine particles) action days": [
        ("jtzZPZ8DQh", "related-component", "high", "AQI days driven by PM2.5; 'PM 2.5' construct"),
        ("P6IzhScRdx", "broader-narrower", "medium", "'air pollution' parent construct")],
    "Black carbon": [("zRxOHnsEfh", "equivalent", "high",
        "ambient black carbon; 'black carbon' construct")],
    "Sulfur dioxide": [("Cv_Ldh0HRR", "equivalent", "high", "'sulfur dioxide' construct")],
    "Ozone action days": [("JMeOsYIcbL", "broader-narrower", "high",
        "AQI days driven by ozone; 'ozone' construct")],
    "Air quality action days": [("P6IzhScRdx", "broader-narrower", "medium",
        "unhealthy-air days; 'air pollution' construct (AQI is multi-pollutant)")],
    "Ozone asthma hospitalizations": [
        ("JMeOsYIcbL", "broader-narrower", "high", "asthma hospitalizations attributable to 'ozone'"),
        ("EAshH_Ko3h", "broader-narrower", "high", "'asthma' outcome construct"),
        ("Gl-I4wBZ5r", "related-component", "medium", "'hospitalization' care event")],
    "Ozone asthma ED visits": [
        ("JMeOsYIcbL", "broader-narrower", "high", "'ozone' exposure construct"),
        ("EAshH_Ko3h", "broader-narrower", "high", "'asthma' outcome construct"),
        ("nS9fqJ01TW", "related-component", "medium", "'emergency department' care setting")],
    "PM2.5 asthma ED visits": [
        ("jtzZPZ8DQh", "broader-narrower", "high", "asthma ED visits attributable to 'PM 2.5'"),
        ("EAshH_Ko3h", "broader-narrower", "high", "'asthma' outcome construct"),
        ("nS9fqJ01TW", "related-component", "medium", "'emergency department' care setting")],
    "PM2.5 health burden (heart)": [
        ("jtzZPZ8DQh", "broader-narrower", "high", "cardiovascular hospitalizations attributable to 'PM 2.5'"),
        ("0GgadM9ouC", "broader-narrower", "high", "'cardiovascular disease' outcome construct"),
        ("Gl-I4wBZ5r", "related-component", "medium", "'hospitalization' care event")],
    "PM2.5 health burden (lungs)": [
        ("jtzZPZ8DQh", "broader-narrower", "high", "respiratory hospitalizations attributable to 'PM 2.5'"),
        ("JmZ-RoSC5o", "broader-narrower", "high", "'respiratory disease' outcome construct"),
        ("Gl-I4wBZ5r", "related-component", "medium", "'hospitalization' care event")],
    "Deaths from PM2.5": [
        ("jtzZPZ8DQh", "broader-narrower", "high", "all-cause deaths attributable to 'PM 2.5'"),
        ("oEWjV89s3H", "broader-narrower", "high", "attributed deaths are all-cause; 'all-cause mortality' construct"),
        ("P6IzhScRdx", "broader-narrower", "medium", "'air pollution' parent construct")],
    "Deaths from ozone": [
        ("JMeOsYIcbL", "broader-narrower", "high", "'ozone' exposure construct"),
        ("0GgadM9ouC", "related-component", "medium", "cardiac deaths are part of the ozone burden; 'cardiovascular disease'"),
        ("JmZ-RoSC5o", "related-component", "medium", "respiratory deaths part of the burden; 'respiratory disease'")],
    "Cockroaches": [("JgRYwtm5Zx", "broader-narrower", "high",
        "household cockroach infestation; 'cockroach' construct")],
    "Children living with cockroaches": [("JgRYwtm5Zx", "broader-narrower", "high",
        "children in cockroach-infested homes; 'cockroach' construct")],
    "Mice or rats (in the building)": [
        ("3a7WLWUQj1", "related-component", "low", "only a taxonomic rodent concept exists ('Murinae'); no pest-infestation construct in SPG"),
        ("CMwBPjRHn_", "related-component", "low", "'rodent control' is the response activity, not the infestation construct")],
    "Mice or rats (outside)": [
        ("3a7WLWUQj1", "related-component", "low", "taxonomic 'Murinae' proxy; no infestation construct"),
        ("CMwBPjRHn_", "related-component", "low", "'rodent control' activity")],
    "Mice or rats (inside)": [
        ("3a7WLWUQj1", "related-component", "low", "taxonomic 'Murinae' proxy"),
        ("CMwBPjRHn_", "related-component", "low", "'rodent control' activity")],
    "Homes with mice or rats in the unit or building": [
        ("3a7WLWUQj1", "related-component", "low", "taxonomic 'Murinae' proxy"),
        ("CMwBPjRHn_", "related-component", "low", "'rodent control' activity")],
    "Children in homes with mice (age 1-13)": [
        ("3a7WLWUQj1", "related-component", "low", "taxonomic 'Murinae' proxy"),
        ("CMwBPjRHn_", "related-component", "low", "'rodent control' activity")],
    "Elevated blood lead levels (age 16+)": [
        ("Z1DkcC8Exg", "equivalent", "high", "elevated 'Blood lead level' measurements are the measure itself"),
        ("k-4NQAUWa9", "broader-narrower", "medium", "elevated BLL indicates 'lead poisoning' risk")],
    "Peeling paint": [
        ("k-4NQAUWa9", "related-component", "medium", "pre-1960 peeling paint is a lead-poisoning risk factor"),
        ("NSSHqnR5tw", "related-component", "medium", "'housing quality' deficiency indicator")],
    "Very old homes": [
        ("NSSHqnR5tw", "related-component", "medium", "pre-1950 housing stock as 'housing quality' proxy"),
        ("k-4NQAUWa9", "related-component", "low", "old housing is a lead-poisoning risk factor per the measure description")],
    "Owner-occupied homes": [("IFcQ3j86qe", "related-component", "low",
        "housing tenure; only the generic 'housing' construct exists")],
    "Leaks": [("NSSHqnR5tw", "related-component", "medium",
        "moisture leaks are 'housing quality' deficiencies (asthma triggers)")],
    "Cracks": [("NSSHqnR5tw", "related-component", "medium",
        "cracks/holes are 'housing quality' deficiencies")],
    "Children in homes with cracks or holes (age 1-13)": [("NSSHqnR5tw", "related-component", "medium",
        "'housing quality' deficiency around children")],
    "Homes with 3+ housing problems": [("NSSHqnR5tw", "related-component", "medium",
        "multiple deficiencies aggregate into 'housing quality'")],
    "Housing problems": [("NSSHqnR5tw", "related-component", "medium",
        "health-related housing problems; 'housing quality' construct")],
    "Renter-occupied homes with no housing problems": [("NSSHqnR5tw", "related-component", "medium",
        "inverse indicator of 'housing quality' deficiencies")],
    "Neighborhood building quality": [("NSSHqnR5tw", "broader-narrower", "medium",
        "neighborhood-scale 'housing quality' rating")],
    "Health insurance (adults)": [("0xDFgJAfrX", "related-component", "low",
        "only 'private health insurance' exists; measure covers any insurance")],
    "Difficulty walking": [("pLOxqX8Jnn", "equivalent", "high",
        "'mobility disability' is difficulty walking/climbing stairs")],
    "Older adults living alone (65+)": [("qt5dLX7UCR", "related-component", "medium",
        "living alone among 65+ proxies 'social isolation'")],
    "Rent burden": [("31gLuixqrR", "related-component", "medium",
        "rent >30% of income is a 'housing instability' driver")],
    "Evictions": [("31gLuixqrR", "broader-narrower", "high",
        "court-ordered evictions are a direct 'housing instability' event")],
    "Limited English": [("Ic3j2gkecR", "equivalent", "high",
        "'limited English proficiency' is the exact construct")],
    "Smoke-free homes": [
        ("qsn9G63cwk", "broader-narrower", "medium", "absence of home smoking policy relates to 'tobacco smoke pollution' exposure"),
        ("JPVciSoX7p", "related-component", "medium", "'smoking ban' is the policy construct")],
    "Secondhand smoke": [
        ("qsn9G63cwk", "broader-narrower", "high", "home secondhand smoke is 'tobacco smoke pollution'"),
        ("Bgy96PVCs9", "broader-narrower", "medium", "'tobacco smoke' is the agent")],
    "Secondhand smoke (from outside)": [
        ("qsn9G63cwk", "broader-narrower", "high", "outdoor-origin home exposure is 'tobacco smoke pollution'"),
        ("Bgy96PVCs9", "broader-narrower", "medium", "'tobacco smoke' agent")],
    "Secondhand smoke at work": [
        ("qsn9G63cwk", "broader-narrower", "high", "'tobacco smoke pollution' at workplaces"),
        ("Bgy96PVCs9", "broader-narrower", "medium", "'tobacco smoke' agent")],
    "Secondhand smoke exposure at home (children)": [
        ("qsn9G63cwk", "broader-narrower", "high", "children's exposure is 'tobacco smoke pollution'"),
        ("Bgy96PVCs9", "broader-narrower", "medium", "'tobacco smoke' agent")],
    "Cigarette smoking (adults)": [
        ("2Cgoxznk46", "equivalent", "high", "'cigarette smoking' is the exact behavior"),
        ("wbFMjf8vLB", "broader-narrower", "high", "'tobacco smoking' parent construct")],
    "Cigarette smoking (youth)": [
        ("2Cgoxznk46", "equivalent", "high", "'cigarette smoking' behavior in youth"),
        ("wbFMjf8vLB", "broader-narrower", "high", "'tobacco smoking' parent construct")],
    "E-cigarette vapor exposure at home (children)": [
        ("59SJNq_Hne", "broader-narrower", "high", "'e-cigarette vapor' is the agent"),
        ("5Gts9oTP6V", "related-component", "medium", "'vaping' is the behavior")],
    "Obesity": [
        ("cj7G775u_Q", "equivalent", "high", "'obesity' (BMI 30+) is the exact construct"),
        ("YtQ5lW8obL", "broader-narrower", "medium", "BMI-based classification; 'body mass index' is the metric")],
    "Obesity (youth)": [
        ("cj7G775u_Q", "broader-narrower", "high", "'obesity' construct in youth"),
        ("YtQ5lW8obL", "broader-narrower", "medium", "BMI-based; 'body mass index' metric")],
    "Overweight": [
        ("slXbabUYMb", "equivalent", "high", "'overweight' (BMI 25+) is the exact construct"),
        ("YtQ5lW8obL", "broader-narrower", "medium", "BMI-based; 'body mass index' metric")],
    "Overweight or obesity (youth)": [
        ("cj7G775u_Q", "broader-narrower", "medium", "'obesity' included in the combined measure"),
        ("slXbabUYMb", "broader-narrower", "medium", "'overweight' included"),
        ("YtQ5lW8obL", "broader-narrower", "medium", "BMI-based; 'body mass index' metric")],
    "Diabetes (adults)": [("DQbECFISI6", "equivalent", "high",
        "adult diabetes prevalence; 'diabetes' construct (verified outside the 473)")],
    "Poverty": [("bIwjlkmcHV", "equivalent", "high", "households below federal poverty level; 'poverty' construct")],
    "Child poverty": [("CDJewvbYAW", "equivalent", "high", "'child poverty' is the exact construct")],
    "Coastal flood risk": [
        ("LQWjUNDY2O", "broader-narrower", "high", "residents in hurricane evacuation zones; 'flood' exposure construct"),
        ("rSNUatmq8T", "related-component", "medium", "coastal flood risk relates to 'sea level rise'")],
    "Walkability": [("dPeET-pgVN", "related-component", "medium",
        "walkability scores promote 'physical activity'")],
    "Death (neonatal)": [("GXPo2ZlO9e", "equivalent", "high",
        "deaths <28 days are 'neonatal mortality'")],
    "Death (postneonatal)": [("rNvNuxXEdo", "broader-narrower", "medium",
        "deaths 28 days-1 year are the postneonatal slice of 'infant mortality'")],
    "Death (infants)": [
        ("rNvNuxXEdo", "equivalent", "high", "deaths <1 year are 'infant mortality'"),
        ("Tzg0TxXii_", "equivalent", "high", "'infant death' is the event construct")],
    "Death (perinatal)": [
        ("dnIEpQCTQ1", "equivalent", "high", "fetal+early deaths 28wk-6d are 'perinatal death'"),
        ("lPNBkdfh_o", "equivalent", "high", "'perinatal mortality' is the rate construct")],
    "Death before 65": [("hXsXEM2vfb", "broader-narrower", "high",
        "deaths before 65 are premature mortality ('Mortality, Premature')")],
    "Arsenic": [
        ("Jmy1CVYSF8", "related-component", "medium", "arsenic measured in 'drinking water'"),
        ("_z7MHvIz4t", "related-component", "low", "'arsenic poisoning' is the health outcome; measure is concentration")],
    "Pneumoconiosis hospitalizations": [
        ("xU4qBZM3Je", "equivalent", "high", "'pneumoconiosis' is the exact disease"),
        ("Gl-I4wBZ5r", "related-component", "medium", "'hospitalization' care event")],
    "Asbestosis hospitalizations": [
        ("Rbalp6imET", "equivalent", "high", "'asbestosis' is the exact disease"),
        ("Gl-I4wBZ5r", "related-component", "medium", "'hospitalization' care event")],
    "Tetralogy of Fallot": [
        ("Eg5BCw9XOJ", "equivalent", "high", "'tetralogy of Fallot' birth-defect prevalence"),
        ("G-cA8ng8z2", "broader-narrower", "medium", "'congenital heart disease' parent construct")],
    "Hypoplastic left heart syndrome": [
        ("YTKMzT1S-y", "equivalent", "high", "'hypoplastic left heart syndrome' is the exact defect"),
        ("G-cA8ng8z2", "broader-narrower", "medium", "'congenital heart disease' parent")],
    "TGA": [("G-cA8ng8z2", "broader-narrower", "medium",
        "transposition of the great arteries is a 'congenital heart disease'; no TGA-specific concept surfaced")],
    "Children in homes with supplemental heat (age 13 and under)": [("Ah-wdkRcqy", "broader-narrower", "medium",
        "space-heater use in homes with children; 'heating equipment' construct")],
    "Lyme disease": [("amXWjMd84N", "equivalent", "high",
        "'Lyme disease' is the exact disease (verified in the full SPG concept set)")],
}

rows = []
missing_fams = []
for fam, verdicts in F.items():
    sub = nyc[nyc.collection == "environment-health"]
    hits = sub[sub.label.str.startswith(fam + ",") | (sub.label == fam)]
    if len(hits) == 0:
        missing_fams.append(fam)
    for _, r in hits.iterrows():
        for sid, mt, conf, why in verdicts:
            rows.append({"nyc_id": r.nyc_id, "spg_system_id": sid,
                         "match_type": mt, "confidence": conf, "rationale": why})

with (OUT / "adjudications_ehdp.jsonl").open("w") as fh:
    for r in rows:
        fh.write(json.dumps(r) + "\n")

matched = {r["nyc_id"] for r in rows}
ehdp = nyc[nyc.collection == "environment-health"]
print(f"{len(rows)} verdict rows; {len(matched)}/{len(ehdp)} EHDP measures matched")
if missing_fams:
    print("FAMILIES WITH NO MEASURES (check prefixes):")
    for f in missing_fams:
        print("  -", f)
unmatched = sorted(set(ehdp.nyc_id) - matched)
(OUT / "ehdp_unmatched_preview.json").write_text(json.dumps(unmatched, indent=1))
print(f"{len(unmatched)} unmatched EHDP measures -> ehdp_unmatched_preview.json")
