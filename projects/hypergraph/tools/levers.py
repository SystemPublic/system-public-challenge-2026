"""Rank the levers a city or a charity could pull, on five separate components.

    python tools/levers.py                 # table sorted by design strength
    python tools/levers.py --sort burden   # or effect, breadth, reach, cost, design
    python tools/levers.py --json          # write data/derived/levers/levers.json and viz/data/levers.js

The components are kept apart on purpose. They are not on a common scale and no weights are defensible, so the tool
does not add them up.

(a) effect: the headline verified finding for the lever from the System graph (docs/all_boats.md), with its interval,
    study design and population. Each was read against its PubMed abstract (data/derived/levers/abstracts/). The
    sortable number `effect_pct` is the percentage change in the outcome (or in its odds, for odds ratios, which
    overstates the change in risk when the outcome is common); negative is a benefit.
(b) breadth: domains with a verified benefit and with a verified harm (data/derived/all_boats/breadth.csv).
(c) burden: the size per year of the New York outcome the lever acts on, and the share held by the tenth of areas
    with the most (analyses/levers/city_metrics.py -> data/derived/levers/city_metrics.json).
(d) reach: how many places or households in New York are eligible.
(e) cost per unit from a published source, or None where none was found.

`like_nyc` marks whether the population studied resembles New York's: "yes", "partly" or "no", with the reason.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DER = ROOT / "data" / "derived" / "levers"

DESIGN_RANK = {"experiment": 4, "quasi-experiment": 3, "cohort": 2, "case-control": 1.5, "cross-section": 1, "none": 0}

# name, all_boats key, effect, burden metric, reach, cost, place-targetable
LEVERS = [
    dict(id="vacant_lot_greening", label="Vacant-lot greening or cleanup", key="vacant_lot_greening",
         effect=dict(outcome="shootings near the lot", estimate=-6.8, lo=-10.6, hi=-2.7, scale="% change", design="experiment",
                     pmid="30496003", study="Moyer et al. 2019, cluster randomised trial, 541 lots, Philadelphia",
                     note="Cleanup only (mowing, trash): -9.2% (-13.2 to -4.8). Branas et al. 2018 (PMID 29483246): gun violence -29.1% below the poverty line."),
         like_nyc="partly", like_note="A US city with concentrated gun violence, but the trial lots were abandoned and blighted; most New York vacant lots are held for development (see the registered test).",
         burden="shootings", reach=dict(value=24663, unit="tax lots in land use 11 (vacant land), PLUTO 26v2", source="64uk-42ks"),
         cost=dict(value=5.0, unit="$ per m2 to green, plus $0.50 per m2 a year to maintain", source="Branas et al. 2018, PNAS, citing earlier cost studies"),
         place=True),
    dict(id="abandoned_house_remediation", label="Abandoned-house remediation (doors, windows, cleanup)", key=None,
         effect=dict(outcome="gun assaults near the house", estimate=-13.12, lo=-21.32, hi=-3.01, scale="% change", design="experiment",
                     pmid="36469329", study="South et al. 2023, cluster randomised trial, 258 houses, Philadelphia",
                     note="Shootings -6.96% (-15.32 to 3.03), not significant; weapons violations -8.43%. Cleanup alone had no effect. Added: not one of the 25 in all_boats; the graph files it under vacant land."),
         like_nyc="partly", like_note="Predominantly Black, low-income Philadelphia neighbourhoods with many abandoned row houses; New York has far fewer abandoned houses.",
         burden="shootings", reach=dict(metric="vacate_orders_active"), cost=None, place=True),
    dict(id="housing_repair", label="Housing repair and insulation", key="housing_repair",
         effect=dict(outcome="reported wheeze", estimate=-43.0, lo=-53.0, hi=-30.0, scale="% change in odds (OR 0.57, 0.47-0.70)", design="experiment",
                     pmid="17324975", study="Howden-Chapman et al. 2007, cluster randomised trial, 1,350 households, New Zealand",
                     note="Also children's days off school OR 0.49 (0.31-0.80), adults' days off work OR 0.62 (0.46-0.83). Glasgow controlled study (PMID 23597345): mental health +2.41 (0.03-4.80) on SF-12."),
         like_nyc="partly", like_note="Uninsulated detached houses in a mild climate; New York's problem housing is multifamily, often overheated, with mould and pests.",
         burden="asthma_ed", reach=dict(metric="hpd_open_c_buildings"),
         cost=dict(value=1800, unit="NZ$ per dwelling (2009)", source="Chapman et al. 2009, cost-benefit of the insulation trial (J Epidemiol Community Health 63:271)"),
         place=True),
    dict(id="traffic_calming", label="Speed humps and traffic calming", key="traffic_calming",
         effect=dict(outcome="pedestrian-vehicle collisions on the street", estimate=-22.0, lo=-34.0, hi=-9.0, scale="% change (IRR 0.78, 0.66-0.91)", design="quasi-experiment",
                     pmid="26264227", study="Rothman et al. 2015, before-after with comparison streets, Toronto",
                     note="Children IRR 0.57 (0.41-0.79). Ghana trunk roads (PMID 36163153): injury severity OR 0.23 (0.11-0.47)."),
         like_nyc="yes", like_note="A large North American city; New York's own speed-hump programme is similar.",
         burden="ped_injuries", reach=dict(value=1409, unit="speed-reducer requests found feasible and queued or accepted, not yet installed", source="9n6h-pt9g (statuses: BC prioritized installation queue 1,034; Accept planning proposal of Feasible 339; Planning proposal - Feasible 36)"),
         cost=dict(value=12000, unit="$ per speed hump (2014)", source="NYC DOT to City Council, reported by Streetsblog NYC, 15 May 2014"),
         place=True),
    dict(id="air_conditioning", label="Air conditioner provision", key="air_conditioning",
         effect=dict(outcome="heat-wave death", estimate=-80.0, lo=-90.0, hi=-30.0, scale="% change in odds (OR 0.2, 0.1-0.7)", design="case-control",
                     pmid="11988377", study="Naughton et al. 2002, case-control, Chicago 1999 heat wave",
                     note="Rogot et al. 1992 cohort (PMID 1415127): central air conditioning 42% lower hot-weather mortality, room units no benefit. Harms: asthma in some cross-sectional studies."),
         like_nyc="yes", like_note="US city heat waves; New York's heat deaths are concentrated in homes without air conditioning (city reports).",
         burden="heat_ed", reach=dict(value=None, unit="9.3% of households without air conditioning (mean of NTAs, EHDP); the count of households was not computed", source="data/derived/heat/bridge_nta.csv"), cost=None, place=True),
    dict(id="lead_abatement", label="Interior lead hazard control", key="lead_abatement",
         effect=dict(outcome="children with blood lead >= 15 ug/dL", estimate=-60.0, lo=-79.0, hi=-20.0, scale="% change in odds (OR 0.40, 0.21-0.80)", design="experiment",
                     pmid="11781171", study="Haynes et al. 2002, meta-analysis of four randomised trials",
                     note="No change in mean blood lead or in the share >= 10 ug/dL (OR 0.85, 0.56-1.3)."),
         like_nyc="partly", like_note="US urban trials of the 1990s, at blood lead levels far above New York's today.",
         burden=None, reach=dict(metric="hpd_open_lead_buildings"), cost=None, place=True),
    dict(id="smoke_free", label="Smoke-free laws (now: smoke-free private housing)", key="smoke_free",
         effect=dict(outcome="heart attack deaths", estimate=-7.4, lo=-11.4, hi=-3.3, scale="% change", design="quasi-experiment",
                     pmid="20864706", study="Dove et al. 2010, Massachusetts state workplace law, interrupted time series",
                     note="New York City has had a workplace and restaurant law since 2003 and smoke-free public housing since 2018, so the remaining lever is private multifamily housing, which this finding does not test."),
         like_nyc="partly", like_note="A US state; the lever it tests is already in force in New York.",
         burden=None, reach=None, cost=None, place=False),
    dict(id="transit_access", label="Free or reduced-fare transit for older people", key="transit_access",
         effect=dict(outcome="depressive symptoms (CES-D points)", estimate=None, lo=None, hi=None, scale="-0.95 points (-1.71 to -0.19)", design="quasi-experiment",
                     pmid="29352012", study="Reinhard et al. 2018, eligibility for free bus passes, England",
                     note="Loneliness also lower. Harms: pedestrian collisions at bus stops (Lima, cross-section)."),
         like_nyc="partly", like_note="English older adults; New York already gives half fares to people over 65.",
         burden=None, reach=None, cost=None, place=False),
    dict(id="street_lighting", label="Street lighting", key="street_lighting",
         effect=dict(outcome="adolescent homicide", estimate=-76.0, lo=-91.0, hi=-30.0, scale="% change in odds (OR 0.24, 0.09-0.70)", design="case-control",
                     pmid="26954939", study="Culyba et al. 2016, case-control, Philadelphia",
                     note="An experiment in England and Wales (PMID 26219885) found that switching off or dimming lights did not raise crime or collisions. A New York public-housing lighting experiment (Chalfin et al. 2022) is not in the graph."),
         like_nyc="partly", like_note="Philadelphia; the same paper's odds ratios for many street features are large and imprecise.",
         burden="shootings", reach=dict(metric="streetlight_complaints_2025"), cost=None, place=True),
    dict(id="street_trees", label="Street trees and canopy", key="street_trees",
         effect=dict(outcome="incident diabetes", estimate=-31.3, lo=-45.3, hi=-14.5, scale="% change in odds (OR 0.687, 0.547-0.855), canopy >= 30% vs 0-9%", design="cohort",
                     pmid="31722373", study="Astell-Burt and Feng 2020, cohort of 46,786 adults, Sydney, Newcastle and Wollongong",
                     note="Harm in a New York birth cohort (PMID 23322788): asthma RR 1.17 (1.02-1.33) per SD of canopy. The repo's rent test (all-boats-trees-rent) is unsettled."),
         like_nyc="partly", like_note="Australian adults aged 45 and over, mostly suburban.",
         burden="heat_ed", reach=dict(value=31615, unit="dead trees and stumps in the 2015 street tree census (planting sites)", source="uvpi-gqnh (13,961 dead, 17,654 stumps)"),
         cost=None, place=True),
    dict(id="green_space", label="Parks and green space", key="green_space",
         effect=dict(outcome="incident psychological distress", estimate=-54.0, lo=-71.0, hi=-31.0, scale="% change in odds (OR 0.46, 0.29-0.69), green space >= 30% vs < 5%", design="cohort",
                     pmid="31348510", study="Astell-Burt and Feng 2019, cohort of 46,786 adults, Australia", note=""),
         like_nyc="partly", like_note="Australian adults, mostly suburban.", burden=None, reach=None, cost=None, place=True),
    dict(id="bike_lanes", label="Bicycle lanes", key="bike_lanes",
         effect=dict(outcome="bicycle injuries after a lane was added", estimate=None, lo=None, hi=None, scale="about 90% lower injury risk on painted lanes (abstract gives no interval)", design="cross-section",
                     pmid="29564357", study="Wall et al. 2016, 839 injured cyclists, Bellevue Hospital, New York",
                     note="Protected lanes with light separation had higher risk in another study (PMID 32388015)."),
         like_nyc="yes", like_note="New York data.", burden="cyclist_injuries", reach=None, cost=None, place=True),
    dict(id="community_gardens", label="Community gardens", key="community_gardens",
         effect=dict(outcome="mortality (home gardening, people with mobility limits)", estimate=-18.0, lo=-29.0, hi=-6.0, scale="% change in hazard (HR 0.82, 0.71-0.94)", design="cohort",
                     pmid="27486315", study="Leng and Wang 2016, 11-year cohort, Taiwan",
                     note="Gardening as an activity, not a community garden. No benefit for those without mobility limits."),
         like_nyc="no", like_note="Taiwanese older adults gardening at home.", burden=None,
         reach=dict(value=553, unit="active GreenThumb gardens", source="p78i-pat6"), cost=None, place=True),
    dict(id="clean_heat", label="Clean heating fuel", key="clean_heat",
         effect=dict(outcome="natural mortality per ug/m3 of residual-oil PM2.5", estimate=None, lo=None, hi=None, scale="HR 1.13 per ug/m3 of residual-oil PM2.5 (the benefit is the reverse)", design="cohort",
                     pmid="35737879", study="Chen et al. 2022, 14 pooled European cohorts (ELAPSE)",
                     note="New York phased out No. 6 oil by 2015 and No. 4 oil by 2030 under the Clean Heat programme."),
         like_nyc="partly", like_note="European adults; New York's residual-oil emissions have already fallen.", burden=None, reach=None, cost=None, place=True),
    dict(id="supermarkets", label="Supermarkets and fresh food", key="supermarkets",
         effect=dict(outcome="adverse cardiovascular events (food desert)", estimate=None, lo=None, hi=None, scale="HR 1.03 for living in a food desert", design="cohort",
                     pmid="37094491", study="Lloyd et al. 2023, US veterans with cardiovascular disease", note="Harm: obesity near supermarkets (Brazil, cross-section)."),
         like_nyc="partly", like_note="US veterans, mostly outside dense cities.", burden=None, reach=None, cost=None, place=True),
    dict(id="third_places", label="Cafes, senior centres and third places", key="third_places",
         effect=dict(outcome="depressive symptoms", estimate=None, lo=None, hi=None, scale="b = -0.03 per unit (rural Korea only)", design="cross-section",
                     pmid="36833010", study="Kim et al. 2023, survey of 10,097 older adults, South Korea", note=""),
         like_nyc="no", like_note="Rural South Korea; no effect in urban areas.", burden=None, reach=None, cost=None, place=True),
    dict(id="recreation_centres", label="Recreation centres and playgrounds", key="recreation_centres",
         effect=dict(outcome="physical activity", estimate=None, lo=None, hi=None, scale="no effect size in the abstract", design="cohort",
                     pmid="31363889", study="Heredia et al. 2020, low-income Latino adults, Texas", note="Harm: assault without a gun near recreation centres, Philadelphia, OR 1.2 (PMID 26414941)."),
         like_nyc="partly", like_note="", burden=None, reach=None, cost=None, place=True),
    dict(id="libraries", label="Libraries", key="libraries",
         effect=dict(outcome="reading aloud daily to infants", estimate=None, lo=None, hi=None, scale="aOR 2.0 (1.0-3.8) for a library card", design="cross-section",
                     pmid="27056451", study="Chen et al. 2016, families with infants, Boston", note=""),
         like_nyc="partly", like_note="Low-income families at a US urban clinic.", burden=None, reach=None, cost=None, place=True),
    dict(id="broadband", label="Broadband access", key="broadband",
         effect=dict(outcome="severe mental stress in students", estimate=-75.0, lo=-92.0, hi=-24.0, scale="% change in odds (OR 0.25, 0.08-0.76)", design="cross-section",
                     pmid="35462833", study="Jiang et al. 2022, university students, China", note="Regional internet access, not a household connection."),
         like_nyc="no", like_note="Chinese provinces.", burden=None, reach=None, cost=None, place=False),
    dict(id="walkability", label="Walkability and sidewalks", key="walkability",
         effect=dict(outcome="transport walking", estimate=None, lo=None, hi=None, scale="sidewalks OR 3.75 (1.06-13.27)", design="cross-section",
                     pmid="28219427", study="Malambo et al. 2017, adults, South Africa", note="Harms: more antidepressant use, less measured activity in other studies."),
         like_nyc="no", like_note="South African adults.", burden=None, reach=None, cost=None, place=True),
    dict(id="cooling_centres", label="Cooling centres and heat alerts", key="cooling_centres",
         effect=dict(outcome="mortality of older adults on heat-alert days", estimate=0.5, lo=-0.3, hi=1.3, scale="% change (RR 1.005, 0.997-1.013)", design="quasi-experiment",
                     pmid="34461376", study="Weinberger et al. 2021, alert days matched to non-alert days, 2,817 US counties", note="Concerns alerts, not cooling centres. Heat-stroke admissions rose on alert days (RR 1.094)."),
         like_nyc="yes", like_note="US Medicare population including New York.", burden="heat_ed", reach=None, cost=None, place=False),
    dict(id="school_based_health", label="School-based health centres", key="school_based_health",
         effect=dict(outcome="graduation", estimate=None, lo=None, hi=None, scale="two nurse-workload measures with opposite signs", design="cohort",
                     pmid="33748993", study="McKinley Yoder et al. 2021, school nurse workload, Washington State", note="Not a study of school-based health centres."),
         like_nyc="partly", like_note="", burden=None, reach=None, cost=None, place=True),
    dict(id="housing_vouchers", label="Housing mobility vouchers", key="housing_vouchers",
         effect=dict(outcome="child mortality", estimate=13.0, lo=-27.0, hi=70.0, scale="% change in odds (OR 1.13, 0.73-1.70)", design="experiment",
                     pmid="23202264", study="Jacob, Ludwig and Miller 2013, housing voucher lottery, Chicago", note="No overall effect. The negative breadth score in all_boats is an artefact of selection into assistance."),
         like_nyc="partly", like_note="Chicago public-housing families.", burden=None, reach=None, cost=None, place=False),
    dict(id="public_pools", label="Public pools", key="public_pools",
         effect=dict(outcome="no usable finding", estimate=None, lo=None, hi=None, scale="", design="none", pmid=None, study="",
                     note="The graph's pool findings concern private pools and chlorination."),
         like_nyc="no", like_note="", burden=None, reach=None, cost=None, place=True),
    dict(id="youth_employment", label="Summer youth employment", key="youth_employment",
         effect=dict(outcome="no variable matched in the graph", estimate=None, lo=None, hi=None, scale="", design="none", pmid=None, study="",
                     note="Lottery studies of New York's and Chicago's programmes exist outside the graph and were not read here."),
         like_nyc="yes", like_note="", burden="shootings", reach=None, cost=None, place=False),
    dict(id="congestion_low_emission", label="Low-emission and congestion zones", key="congestion_low_emission",
         effect=dict(outcome="no variable matched in the graph", estimate=None, lo=None, hi=None, scale="", design="none", pmid=None, study="",
                     note="See docs/congestion_tradeoffs.md for the city's own results."),
         like_nyc="yes", like_note="", burden="traffic_deaths", reach=None, cost=None, place=False),
]


def load():
    cm = json.loads((DER / "city_metrics.json").read_text())["metrics"]
    br = {r["intervention"]: r for r in csv.DictReader(open(ROOT / "data/derived/all_boats/breadth.csv"))}
    lot = DER / "lot_test_results.json"
    lot = json.loads(lot.read_text()) if lot.exists() else None
    out = []
    for L in LEVERS:
        r = {k: L[k] for k in ("id", "label", "like_nyc", "like_note", "place")}
        e = dict(L["effect"])
        e["design_rank"] = DESIGN_RANK[e["design"]]
        r["effect"] = e
        b = br.get(L["key"]) if L["key"] else None
        r["breadth"] = ({"benefit": int(b["benefit_domains"]), "harm": int(b["harm_domains"]),
                         "experimental": int(b["experimental_benefit_domains"]), "net": int(b["breadth"])}
                        if b else {"benefit": 1, "harm": 0, "experimental": 1, "net": 1, "note": "not in all_boats; counted from its own trial"})
        if L["burden"]:
            m = cm[L["burden"]]
            r["burden"] = {"value": m["value"], "unit": m["unit"], "top_decile_share": m["top_decile_share"],
                           "areas": m["areas"], "source": m["source"]}
        else:
            r["burden"] = None
        rc = L["reach"]
        if rc and "metric" in rc:
            m = cm[rc["metric"]]
            r["reach"] = {"value": m["value"], "unit": m["unit"], "source": m["source"]}
        else:
            r["reach"] = rc
        if L["id"] == "vacant_lot_greening" and lot:
            r["reach_trial_like"] = lot.get("reach_summary")
        r["cost"] = L["cost"]
        out.append(r)
    return out


def key(comp):
    def f(r):
        if comp == "design":
            return -r["effect"]["design_rank"]
        if comp == "effect":
            v = r["effect"]["estimate"]
            return v if v is not None and v < 0 else 1e9
        if comp == "breadth":
            return -r["breadth"]["net"]
        if comp == "burden":
            return -(r["burden"]["value"] if r["burden"] and isinstance(r["burden"]["value"], (int, float)) else -1)
        if comp == "reach":
            return -(r["reach"]["value"] if r["reach"] and isinstance(r["reach"].get("value"), (int, float)) else -1)
        if comp == "cost":
            return 0 if r["cost"] else 1
        return 0
    return f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sort", default="design", choices=["design", "effect", "breadth", "burden", "reach", "cost"])
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    rows = load()
    if a.json:
        DER.mkdir(parents=True, exist_ok=True)
        (DER / "levers.json").write_text(json.dumps(rows, indent=1))
        (ROOT / "viz/data/levers.js").write_text("window.LEVERS = " + json.dumps(rows) + ";\n")
        lt = DER / "lot_test_results.json"
        oc = ROOT / "claims/outcomes/levers-vacant-lot-trial-match.json"
        if lt.exists() and oc.exists():
            o = json.loads(oc.read_text())
            naip = {r["bbl"]: r for r in csv.DictReader(open(DER / "lots_naip.csv"))}
            chips = []
            for p in sorted((ROOT / "figures/levers/chips").glob("*.png"))[:40]:
                n = naip.get(p.stem, {})
                v = n.get("veg_share")
                chips.append({"path": f"figures/levers/chips/{p.name}", "bbl": p.stem, "type": n.get("type", ""),
                              "veg": round(float(v), 2) if v not in (None, "") else None})
            reading = ("The share lies in the registered range, near its top. NDVI cannot show trash or neglect, so some of these "
                       "lots may be maintained side yards; a visual check of 40 images suggests about a fifth show a building or a ball field. "
                       "The prevented-shootings figure carries the trial's interval only and assumes that the Philadelphia effect transfers.")
            (ROOT / "viz/data/levers_lots.js").write_text("window.LEVER_LOTS = " + json.dumps(
                {"results": json.loads(lt.read_text()), "verdict": o["verdict"], "reading": reading, "chips": chips}) + ";\n")
    for r in sorted(rows, key=key(a.sort)):
        e = r["effect"]
        est = "" if e["estimate"] is None else f"{e['estimate']:+.1f}% ({e['lo']}, {e['hi']})"
        bu = "" if not r["burden"] else f"{r['burden']['value']} {r['burden']['unit'][:40]}"
        re_ = "" if not r["reach"] else f"{r['reach'].get('value')}"
        print(f"{r['label'][:42]:42} | {e['design']:16} | {est:28} | breadth {r['breadth']['net']:+d} | {bu[:55]:55} | reach {re_[:12]:12} | cost {'yes' if r['cost'] else 'missing'} | like NYC {r['like_nyc']}")


if __name__ == "__main__":
    main()
