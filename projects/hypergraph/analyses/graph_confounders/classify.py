#!/usr/bin/env python
"""The registrant's reading of each shared concept's role, from variable names and abstracts.
Writes data/derived/graph/confounders/classification.json with counts for the top 20 of each pair.
Roles: confounder (common cause), mediator (on the path), consequence (other outcome of either end,
or a collider), same (the same construct measured another way), noise (homonym, laboratory or animal
study, unrelated), unreadable (confounder-like label but the API returned no findings to read)."""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/derived/graph/confounders"
R = {
 "green__temperature": {
  "physical activity": "consequence", "urban area": "unreadable", "thermodynamic temperature": "same", "ethnicity": "unreadable",
  "psychological stress": "consequence", "COVID-19": "noise", "blood pressure": "consequence", "SARS-CoV-2": "noise",
  "stroke": "consequence", "age group": "noise", "neighborhood characteristics": "noise", "bone fracture": "noise",
  "population density": "confounder", "prevalence": "noise", "arterial hypertension": "consequence", "satellite imagery": "noise",
  "social isolation": "unreadable", "sleep": "consequence", "tobacco use": "noise", "sleep quality": "unreadable",
  "tuberculosis": "noise", "soil moisture": "mediator"},
 "temperature__heat-illness": {
  "mortality rate": "consequence", "temperature": "same", "gender": "unreadable", "body temperature": "mediator",
  "preterm birth": "consequence", "heart rate": "mediator", "diabetes": "unreadable", "cardiac output": "mediator",
  "hypertension": "consequence", "cardiovascular disease": "consequence", "urban area": "unreadable", "survival rate": "noise",
  "thermodynamic temperature": "same", "breathing": "noise", "drowning": "consequence", "psychological stress": "noise",
  "arterial blood pressure": "mediator", "COVID-19": "noise", "age group": "confounder", "morbidity": "consequence"},
 "green__heat-illness": {
  "psychological stress": "unreadable", "body mass index": "confounder", "urban area": "unreadable", "COVID-19": "noise",
  "thermodynamic temperature": "mediator", "rural area": "confounder", "overweight": "confounder", "myocardial infarction": "noise",
  "age group": "confounder", "blood pressure": "noise", "mental health": "noise", "alcohol consumption": "noise"},
 "active-travel__obesity": {
  "physical activity": "mediator", "mortality rate": "consequence", "stroke": "noise", "physical exercise": "mediator",
  "age group": "confounder", "dementia": "noise", "gender": "confounder", "mental depression": "consequence",
  "heart rate": "noise", "quality of life": "consequence", "cognitive dysfunction": "noise", "muscle strength": "noise",
  "educational stage": "confounder", "lower back pain": "noise", "frailty syndrome": "noise", "knee replacement": "noise",
  "anxiety": "consequence", "diabetes": "consequence", "bone density": "noise", "heart failure": "noise"},
 "housing-vacancy__gun-violence": {
  "mental depression": "consequence", "depressive disorder": "consequence", "mental health": "consequence", "gender": "confounder",
  "psychological stress": "consequence", "ethnicity": "confounder", "psychotic disorder": "noise", "physical activity": "consequence",
  "smoking": "noise", "anxiety": "consequence", "age group": "confounder", "food security": "consequence",
  "asthma": "noise", "quality of life": "consequence", "substance abuse": "confounder", "death": "consequence",
  "mortality rate": "consequence", "post-traumatic stress disorder": "consequence", "preterm birth": "consequence", "income": "confounder"},
}
# confounder-like concepts found below rank 20, with rank
LOWER = {
 "temperature__heat-illness": {"home environment (living alone)": 38},
 "active-travel__obesity": {"ethnicity": 22, "park": 43, "built environment": 45, "crime": 51, "urban area": 65,
                            "socioeconomic status": 75, "population density": 96, "neighborhood characteristics": 103},
 "housing-vacancy__gun-violence": {"homeless person": 32, "educational stage": 37, "social vulnerability": 60,
                                   "lead poisoning (housing age)": 66, "employment": 82, "poverty": 138, "socioeconomic status": 160},
}
out = {}
for pair, roles in R.items():
    sh = json.loads((OUT / f"shared_{pair}.json").read_text())["shared"]
    # ties at the weaker-link count are ordered arbitrarily, so every concept tied with rank 20 is classified
    cut = sh[min(19, len(sh) - 1)]["weaker_link"]
    top = [s["label"] for s in sh if s["weaker_link"] >= cut and s["label"] in roles]
    out[pair] = {"n_shared": len(sh), "top20_roles": roles, "n_classified": len(roles), "counts": dict(Counter(roles.values())),
                 "confounder_like_below_rank_20": LOWER.get(pair, {})}
    print(pair, len(sh), out[pair]["counts"])
(OUT / "classification.json").write_text(json.dumps(out, indent=1))
