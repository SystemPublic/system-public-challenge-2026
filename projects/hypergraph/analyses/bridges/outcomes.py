"""Outcomes for the bridge claims, scored against the registrations (rules: concord.claims.PRECEDENCE)."""
from __future__ import annotations

import json

from analyses.bridges.common import DER, ROOT
from concord import claims

FIG1 = "figures/bridges/bridge_crz_injury_crashes.png"
FIG2 = "figures/bridges/bridge_heat_shootings_ems.png"


def set_bridge_stance(cid, chain):
    """Rule 5: a bridge takes the stance of its weakest link."""
    f = ROOT / "claims" / "outcomes" / f"{cid}.json"
    o = json.loads(f.read_text())
    o["endpoint_stance"] = o.get("stance")
    o["stance"] = claims.bridge_stance(chain)
    f.write_text(json.dumps(o, indent=1, ensure_ascii=False))


def main():
    cr = json.loads((DER / "crz_crashes_results.json").read_text())
    R, comp = cr["results"], cr["composed"]
    p, pl, cm = R["primary_injury_crashes"], R["placebo_2024"], R["compatibility"]
    em = json.loads((DER / "ems_results.json").read_text())
    E, comp2 = em["results"], em["composed"]
    e, c2, l2, S = E["endpoint_SHOT_irr_per5C"], E["compatibility"], E["link_dispatches_per_incident"], E["sensitivity"]

    claims.outcome({
        "id": "bridge-crz-crash-link",
        "verdict": "no_test",
        "city_effect": None,
        "graph_effect": {"label": "Power-model exponent for injury crashes on urban roads (Elvik 2009); volume elasticity assumed 0.9",
                         "estimate": 1.2, "lo": None, "hi": None, "scale": "exponent on relative speed", "null": 0},
        "sources": [{"kind": "literature", "citation": "Elvik R (2009), TOI Report 1034/2009"},
                    {"kind": "literature", "citation": "Nilsson G (2004), Lund Bulletin 221"},
                    {"kind": "sysgraph", "file": "data/derived/bridges/abstracts_graph.txt", "note": "speed findings in the graph; no volume or power-model findings"}],
        "prediction_scored": "partial: the link has no city test of its own. It was tested only jointly, through the endpoint of bridge-crz-injury-crashes, which was compatible with it.",
        "settle": "A test of the speed exponent at low urban speeds would need crashes and speeds on the same street segments over time, for example NYC DOT segment speeds from the Traffic Speeds feed (i4gi-tjb9) joined to geocoded crashes on streets outside the zone.",
        "research_needed": [{"question": "Does the power model hold at network speeds below 15 mph?", "data": "Segment-level speeds and crashes in a dense city", "design": "Panel of street segments with speed changes from signal timing or speed limits", "priority": "medium"},
                            {"question": "Add the speed-crash literature (Nilsson, Elvik, Cameron and Elvik 2010) and the London congestion charge accident study to the System graph", "data": "Papers", "design": "Extraction", "priority": "high"}],
        "figures": [FIG1],
        "notes": "A research link, registered so that the bridge's chain names every link. The System graph holds a few speed-severity findings (child pedestrians, moped riders, cyclists) but no power-model or volume-crash findings, so the exponents come from Elvik (2009) and the volume elasticity is an assumed range.",
    })

    claims.outcome({
        "id": "bridge-crz-injury-crashes",
        "verdict": "confirmed",
        "city_effect": {"label": "Endpoint: NYPD injury crashes in the CBD geofence vs rest of city, 2025 vs 2022-24 (OLS log monthly count, HAC 3)",
                        "estimate": p["pct"], "lo": p["lo"], "hi": p["hi"], "scale": "percent change", "null": 0, "n": p["n"]},
        "graph_effect": {"label": "Composed prediction from mob-crz-traffic and bridge-crz-crash-link (Monte Carlo, 200,000 draws)",
                         "estimate": comp["median"], "lo": comp["lo"], "hi": comp["hi"], "scale": "percent change", "null": 0},
        "endpoint_test": {"D_log": cm["D"], "se": cm["se"], "z": cm["z"], "compatible": cm["compatible"],
                          "placebo_2024_pct": [pl["pct"], pl["lo"], pl["hi"]]},
        "sources": cr["sources"],
        "prediction_scored": (f"partial. The registered endpoint test is met: the observed change, {p['pct']:+.1f}% ({p['lo']:+.1f} to {p['hi']:+.1f}), "
                              f"is compatible with the composed {comp['median']:+.1f}% ({comp['lo']:+.1f} to {comp['hi']:+.1f}); z = {cm['z']:.2f}, "
                              f"and the 2024 placebo includes zero ({pl['pct']:+.1f}%, {pl['lo']:+.1f} to {pl['hi']:+.1f}). The registrant's directional bet "
                              "(a decline of 2 to 15 percent) was not borne out: the point estimate is positive and the interval spans zero."),
        "settle": "The endpoint interval (about 12 points wide) and the composed interval (about 17 points wide) both include zero, so the test can rule out large changes (a decline of the London size, 30 to 40 percent, or a rise above about 8 percent) but cannot tell whether the speed and volume terms cancel or are both small. Segment-level speeds and volumes inside the zone, and crashes by segment, would separate the two terms.",
        "research_needed": [
            {"question": "Do the speed and volume effects on crashes cancel, or are both near zero at 8 to 9 mph?", "data": "MTA or DOT segment speeds and counts inside the zone; geocoded crashes", "design": "Segment panel, 2023-2026", "priority": "high"},
            {"question": "Why did London's charge reduce accidents by about 40 percent while New York's shows no change?", "data": "Both cities' crash series with common definitions", "design": "Comparison of designs (London 2003 vs 20 cities; NYC zone vs rest)", "priority": "medium"},
            {"question": "How much does improved geocoding in 2025 bias the zone-vs-rest comparison?", "data": "Crash records without coordinates, geocoded from street names", "design": "Re-geocode 2022-2025 missing-coordinate records", "priority": "medium"},
        ],
        "figures": [FIG1],
        "notes": (
            f"Secondary results (reported, not deciding): Poisson GLM {R['poisson_injury_crashes']['pct']:+.1f}% ({R['poisson_injury_crashes']['lo']:+.1f} to {R['poisson_injury_crashes']['hi']:+.1f}); "
            f"persons injured {R['persons_injured']['pct']:+.1f}% ({R['persons_injured']['lo']:+.1f} to {R['persons_injured']['hi']:+.1f}); "
            f"pedestrians and cyclists injured {R['ped_cyc_injured']['pct']:+.1f}% ({R['ped_cyc_injured']['lo']:+.1f} to {R['ped_cyc_injured']['hi']:+.1f}); "
            f"all crashes {R['crashes']['pct']:+.1f}% ({R['crashes']['lo']:+.1f} to {R['crashes']['hi']:+.1f}); "
            f"persons killed (Poisson) {R['persons_killed_poisson']['pct']:+.0f}% ({R['persons_killed_poisson']['lo']:+.0f} to {R['persons_killed_poisson']['hi']:+.0f}), against a composed +7% (-4 to +23), with 11 to 18 deaths a year in the zone; "
            f"zone including the excluded highways {R['with_highways']['pct']:+.1f}% ({R['with_highways']['lo']:+.1f} to {R['with_highways']['hi']:+.1f}); "
            f"with January-August 2026 added {R['through_aug_2026']['pct']:+.1f}% ({R['through_aug_2026']['lo']:+.1f} to {R['through_aug_2026']['hi']:+.1f}). "
            "Exploratory, not registered: the share of injury crashes without coordinates fell citywide from about 9 to 11 percent in 2022-2024 to 2.6 percent in 2025, while among crashes coded MANHATTAN it rose from about 2 to 4.4 percent. "
            "If the missing records are distributed like the geocoded ones within each borough, this biases the zone-vs-rest estimate downward by roughly 2 to 3 points, which would move it to about +4 percent, still compatible with the composed prediction. "
            "Stance: rule 5 gives the weakest link's stance (mob-crz-traffic; the research link has none). The endpoint's own stance against the registered negative direction is kept as endpoint_stance. "
            "A compatible endpoint supports the chain as a whole; it does not show that each link is right, since a larger speed exponent and a larger volume elasticity would compose to the same result."),
    })
    set_bridge_stance("bridge-crz-injury-crashes", ["mob-crz-traffic", "bridge-crz-crash-link"])

    claims.outcome({
        "id": "bridge-shot-ems-link",
        "verdict": "confirmed",
        "city_effect": {"label": "Daily EMS SHOT dispatches per NYPD shooting incident, same day (OLS with day of week, month, year, holiday; HAC 7)",
                        "estimate": l2["estimate"], "lo": l2["lo"], "hi": l2["hi"], "scale": "dispatches per incident", "null": 0, "n": l2["n"]},
        "graph_effect": None,
        "sources": em["sources"],
        "prediction_scored": f"hit: {l2['estimate']:.2f} ({l2['lo']:.2f} to {l2['hi']:.2f}) lies in the registered 0.6 to 1.6.",
        "settle": "Linked records (EMS incident to NYPD incident) would show how many SHOT dispatches have a recorded shooting behind them; the published data cannot be linked.",
        "research_needed": [{"question": "What share of EMS gunshot dispatches correspond to an NYPD-recorded shooting victim?", "data": "Linked FDNY and NYPD records", "design": "Record linkage", "priority": "medium"}],
        "figures": [FIG2],
        "notes": "This link test uses the endpoint dataset's daily levels but not its relation to temperature. Annual SHOT dispatches are 2.5 to 4 times the NYPD incident count, so most SHOT dispatches have no NYPD-recorded shooting behind them.",
    })

    claims.outcome({
        "id": "bridge-heat-shootings-ems",
        "verdict": "confirmed",
        "city_effect": {"label": "Endpoint: daily FDNY EMS SHOT dispatches, Central Park TMAX lag 0, NB GLM as heat-shootings, 2006 to Aug 2026",
                        "estimate": e["estimate"], "lo": e["lo"], "hi": e["hi"], "scale": "IRR per 5 C", "null": 1, "n": E["n_days"]},
        "graph_effect": {"label": "Composed prediction from heat-shootings and bridge-shot-ems-link (Monte Carlo)",
                         "estimate": comp2["median"], "lo": comp2["lo"], "hi": comp2["hi"], "scale": "IRR per 5 C", "null": 1},
        "endpoint_test": {"D_log": c2["D"], "se": c2["se"], "z": c2["z"], "compatible": c2["compatible"]},
        "sources": em["sources"],
        "prediction_scored": (f"hit: the observed IRR {e['estimate']:.3f} ({e['lo']:.3f} to {e['hi']:.3f}) is inside the composed {comp2['median']:.3f} "
                              f"({comp2['lo']:.3f} to {comp2['hi']:.3f}); z = {c2['z']:.2f}."),
        "settle": "The composed interval is wide because the temperature gradient of SHOT dispatches without a recorded victim was unknown (k between 0 and 1). The endpoint is far more precise than the prediction, so the test mainly rules out the two extremes: that only victim dispatches follow heat (IRR about 1.055) and that all dispatches follow heat as shootings do (1.146). Linked EMS and NYPD records would allow the victim and non-victim gradients to be estimated separately.",
        "research_needed": [{"question": "Do shots-fired reports without a victim follow temperature as shootings do?", "data": "ShotSpotter activations and 911 shots-fired calls (NYPD calls for service)", "design": "Same daily model", "priority": "medium"},
                            {"question": "Does the gradient carry through to ED visits for assault?", "data": "Daily assault and firearm ED visits (syndromic), which the Health Department holds but does not publish; EHDP publishes only annual counts for 2018-2023", "design": "Same daily model", "priority": "high"}],
        "figures": [FIG2],
        "notes": (f"Sensitivity (registered, not deciding): May-September {S['warm_season']['estimate']:.3f} ({S['warm_season']['lo']:.3f} to {S['warm_season']['hi']:.3f}); "
                  f"2006-2019 {S['2006_2019']['estimate']:.3f} ({S['2006_2019']['lo']:.3f} to {S['2006_2019']['hi']:.3f}); "
                  f"SHOT plus T-SHOT {S['SHOT_plus_T-SHOT']['estimate']:.3f}; STAB dispatches, outside the chain, {S['STAB_contrast']['estimate']:.3f} ({S['STAB_contrast']['lo']:.3f} to {S['STAB_contrast']['hi']:.3f}). "
                  "Exploratory: with a victim share of 0.37 (1.25 dispatches per incident times 974 incidents over 3,164 dispatches in 2023), the observed IRR implies k of about 0.64, so dispatches without a recorded victim rise with heat at about two thirds of the shootings rate. "
                  "The second bridge first proposed, from heat to assault ED visits in EHDP-data, could not be built: EHDP publishes violence-related and firearm ED visits only as annual counts and rates by area (indicators 2400, 2437; SPARCS 2018-2023), with no daily or monthly series. EMS dispatches were used as the endpoint instead. "
                  "Stance: rule 5, weakest link (heat-shootings or bridge-shot-ems-link)."),
    })
    set_bridge_stance("bridge-heat-shootings-ems", ["heat-shootings", "bridge-shot-ems-link"])


if __name__ == "__main__":
    main()
