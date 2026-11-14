"""Register transfer-chicago-hot-end. Run once, before any Divvy value is queried."""
import json
from pathlib import Path

from concord import claims

ROOT = Path(__file__).resolve().parents[3]
ny = json.loads((ROOT / "data/derived/round2/hot_end/ny_by_range.json").read_text())
pw = json.loads((ROOT / "data/derived/round2/hot_end/power.json").read_text())
old = json.loads((ROOT / "claims/registered/heat-mech-outdoors.json").read_text())
r3 = lambda v: {k: round(v[k], 3) for k in ("estimate", "lo", "hi")}

rec = {
    "id": "transfer-chicago-hot-end",
    "kind": "confirmation",
    "transfer": {"from_city": "New York City", "to_city": "Chicago", "from_claim": "heat-mech-outdoors",
                 "from_exploratory": "data/derived/graph/heat_mechanisms/exploratory_hot_end.json"},
    "statement": ("In Chicago, as in New York, a daily proxy for people outdoors (Divvy bicycle trips) stops rising with "
                  "maximum temperature between 27 and 33 C while shootings keep rising, and adding the proxy to the "
                  "shootings model removes part of the rise in shootings from 15 to 21 C and little of the rise from 27 to 33 C."),
    "graph_evidence": [e for e in old["graph_evidence"] if e.get("pubmed_ids") and e["pubmed_ids"][0] in (36444549, 27128938)],
    "graph_evidence_note": ("Copied from heat-mech-outdoors. The graph holds no finding on temperature and gun violence. Its signed "
                            "findings on heat and being outdoors are negative (Kim 2022, odds of regular walking 0.95 per 1 C rural and 0.98 urban; "
                            "Mora-Rodriguez 2016, r = -0.28), which is the source of the prediction that outdoor activity flattens on hot days. "
                            "Kim 2022 was read again in PubMed on 12 Nov 2026 for this registration and matches. No graph request was made for this registration."),
    "literature": [
        {"citation": "Reeping PM, Hemenway D. The association between weather and the number of daily shootings in Chicago (2012-2016). Inj Epidemiol 2020;7:31.",
         "doi": "10.1186/s40621-020-00260-3", "finding": "+34.0% shootings per 10 C on weekdays, +41.6% on weekends and holidays; linear in temperature."}],
    "new_york_values": {
        "note": ("Exploratory in New York (run after the outcome of heat-mech-outdoors). The published New York figures used a natural cubic spline with "
                 "4 df and knots at quantiles (q4). Recomputed here with the piecewise-linear basis that this registration uses (lin). All from "
                 "data/derived/graph/heat_mechanisms/mediators_daily.csv by analyses/round2/hot_end/ny_bike_by_range.py."),
        "q4_published": {"shootings_33_vs_27": [1.126, 1.069, 1.185], "noise_33_vs_27": [0.97, 0.94, 1.00], "bike_33_vs_27": [0.98, 0.95, 1.00],
                         "share_removed_by_noise_21_vs_15": 0.46, "share_removed_by_noise_33_vs_27": -0.09},
        "lin": {p: {"proxy_33_vs_27": r3(ny[p]["proxy_curve"]["rr_33_vs_27"]), "proxy_21_vs_15": r3(ny[p]["proxy_curve"]["rr_21_vs_15"]),
                    "shootings_33_vs_27": r3(ny[p]["shootings_without"]["rr_33_vs_27"]),
                    "shootings_21_vs_15": r3(ny[p]["shootings_without"]["rr_21_vs_15"]),
                    "share_21_vs_15": r3(ny[p]["shares"]["share_21_vs_15"]), "share_33_vs_27": r3(ny[p]["shares"]["share_33_vs_27"])}
                for p in ("noise_street", "bike")}},
    "prediction": {
        "direction": "+",
        "magnitude": ("(a) Divvy trips change by a factor between 0.90 and 1.03 from 27 to 33 C (New York proxies: 0.92 and 0.93 with the linear basis, 0.97 and 0.98 "
                      "with the published basis). Shootings rise by a factor between 1.05 and 1.18 over the same range (New York 1.12, 1.05 to 1.20). "
                      "(b) Adding log(1 + Divvy trips) removes 20 to 55% of the log rise in shootings from 15 to 21 C (New York street noise: 41%, 29 to 57) and "
                      "less than a quarter of a New York-sized rise from 27 to 33 C (New York: none). The New York bicycle counts removed 2% (-1 to 6) "
                      "of the 15 to 21 C rise, so part (b) is predicted from the noise proxy and is the part most likely to fail with a bicycle proxy."),
        "support_if": ("Both parts hold with the piecewise-linear basis. (a) The 95% upper limit of the Divvy ratio 33 C against 27 C is below 1.06, and the 95% lower limit "
                       "of the shootings ratio 33 C against 27 C, fitted on the full Chicago window 2010-01-01 to 2026-08-31, is above 1.00. "
                       "(b) On the Divvy window, the share of the shootings log rise from 15 to 21 C removed by the proxy is at least 0.20 with a bootstrap lower limit above 0.10, "
                       "and the amount removed from the log rise from 27 to 33 C (log rise without the proxy minus log rise with it) is below 0.028 "
                       "(a quarter of ln 1.12, the New York hot-day rise) with a bootstrap upper limit below 0.057 (half of it)."),
        "refute_if": ("Part (a) fails in the opposite direction: the 95% lower limit of the Divvy ratio 33 C against 27 C is above 1.06 (outdoor activity keeps rising), "
                      "or the 95% upper limit of the full-window shootings ratio 33 C against 27 C is below 1.06 (shootings flatten)."),
        "otherwise": ("Unsettled. In particular, if (a) is supported and (b) is not, the verdict is unsettled and the report says that the shape transfers and the "
                      "decomposition does not with this proxy. Each part is reported with its own numbers whatever the verdict."),
    },
    "plan": (
        "Data. Shootings: daily distinct cases with a gunshot injury, Chicago Violence Reduction victims dataset gumc-mgzr, 2010-01-01 to 2026-08-31, and Midway "
        "(USW00014819) GHCN-Daily TMAX and precipitation, both as already built by analyses/transfer/chicago_heat.py "
        "(data/derived/graph/transfer_chicago/chicago_heat_daily.csv). Proxy: Divvy Trips, Chicago portal dataset fg6s-gzvg, trips per day by start_time and user_type, "
        "queried through concord/socrata.py with DOMAIN set to data.cityofchicago.org. The portal copy covers 27 June 2013 to 31 December 2019 (from the catalog metadata). "
        "The Divvy window is 2013-07-01 to 2019-12-31. A day in the window with no row in the result counts as 0 trips. The primary proxy is all trips; "
        "trips by user type Customer (casual) and Subscriber are secondary and do not decide the verdict.\n"
        "Model. Negative binomial GLM with log link and HC0 standard errors, calendar terms C(dow) + C(month) + C(year) + hol + wet as in heat-shootings, and temperature "
        "as a piecewise-linear spline of TMAX with knots at 15, 21 and 27 C (analyses/round2/hot_end/model.py, SPLINE = 'lin'). Dispersion alpha is estimated by maximum "
        "likelihood from the linear-temperature model on the same days. The ratio for 33 against 27 C is exp(6 x slope above 27 C). The share removed over a range is "
        "1 - (log rise with log(1 + trips) in the model) / (log rise without it), on the Divvy window, with a 95% interval from 500 resamples of calendar weeks (seed 1).\n"
        "Why this basis. A simulation on the Chicago weather and calendar (analyses/round2/hot_end/power.py and the check recorded in docs/round2.md) showed that the "
        "4-df quantile-knot basis of the New York exploratory analysis overstates the 27 to 33 C ratio by 0.04 to 0.07 when the true curve bends sharply at 27 C "
        "(true 1.00 estimated as 1.07; true 0.98 estimated as 1.05), because it has no knot near 27 C. The piecewise-linear basis was unbiased in the same simulation "
        "(1.00 estimated as 1.00, 0.98 as 0.98). The New York values were recomputed with it before this registration and keep their sign and size.\n"
        "Pre-specified sensitivity, reported and not deciding: the q4 basis; a natural cubic basis with knots at 9, 15, 21, 27 C; year-by-month terms in place of month and year; "
        "May to September only; the shootings ratio on the Divvy window; Customer and Subscriber trips separately; the proxy from the previous day.\n"
        "Figure: the two cities' curves side by side (shootings and the outdoor proxy against TMAX, relative to 15 C)."),
    "can_it_fail": {
        "source": ("data/derived/round2/hot_end/power.json: 120 simulated series per scenario on the Chicago weather and calendar with the registered basis; "
                   "shootings simulated at 6.7 a day, the proxy with day-to-day noise of sd 0.25 on the log scale. Standard errors of the shares in the simulation "
                   "are the spread across simulated series, standing in for the bootstrap."),
        "scenarios": {k: v for k, v in pw.items() if isinstance(v, dict)},
        "minimum_detectable": ("With 80% power at the two-sided 5% level, the smallest detectable shootings rise from 27 to 33 C is 7.5% on the full window (New York: 12%) and "
                               "13% on the Divvy window, which is why part (a) takes shootings from the full window. When shootings are simulated flat above 27 C and the proxy "
                               "rising 12%, part (a) is met in no series. Part (b)'s support rule is met in a large majority of series when 45% of the 15 to 21 C rise passes "
                               "through the proxy and in none when nothing passes through it (p_b_support in the scenarios)."),
        "days": {k: v for k, v in pw.items() if not isinstance(v, dict)},
    },
    "already_seen": (
        "Chicago shootings and Midway temperature were fetched and analysed by transfer-chicago-heat-shootings. That study saw the linear rate ratio (1.131 per 5 C, 1.120 to 1.143) "
        "and eight linear variants, and also the unadjusted mean daily count by 3 C bin of TMAX (data/derived/graph/transfer_chicago/heat_by_tmax_bin.csv, drawn in panel A of "
        "figures/graph/transfer_chicago.png): 8.30 at 24-27 C, 8.88 at 27-30 C, 9.53 at 30-33 C, 8.91 at 33-36 C (202 days) and 9.58 at 36-39 C (24 days). I read that table before "
        "registering. It suggests an unadjusted rise of roughly 7 to 10% from 27 to 33 C and a dip above 33 C, so the shootings half of part (a) is partly known and is not a blind test. "
        "No spline or range-specific model of Chicago shootings had been fitted, and I fitted none before registering. No Divvy value has been queried by this project: the Socrata cache "
        "holds no fg6s-gzvg file, and no script or document in the repository mentions Divvy. For this registration I read only catalog metadata for fg6s-gzvg and for the 311 dataset "
        "v6vf-nfxy (column names, the date range, the user types and the most frequent request types). The power simulation read the weather and calendar columns of "
        "chicago_heat_daily.csv and not the shootings column. New York's proxies, curves and decomposition are all seen and are the source of the predicted sizes."),
    "not_used": ("Chicago's 311 system has no street-noise or other outdoor-gathering request type among its most frequent types (noise complaints go to the police non-emergency line), "
                 "so no 311 proxy is registered. The Park District publishes beach water and weather sensor readings and no attendance counts. CTA ridership is not an outdoor proxy. "
                 "Divvy trips after 2019 exist only as zip archives on the operator's site and are not downloaded."),
    "alternatives": [
        "Divvy trips fall on hot days because riders switch mode, not because fewer people are outdoors; a bicycle proxy measures travel, not evening street presence.",
        "The system grew from 300 to about 600 stations in the window; growth within a year that coincides with season would distort the curve. Year terms and the year-by-month variant address it.",
        "Shared causes of trips and shootings that move with temperature (festivals, holidays, school terms) would raise the share removed without any causal step.",
        "A proxy measured with error removes less than the pathway carries, so a small share does not show that street activity is unimportant.",
        "Lake breeze: Midway can be several degrees warmer than the lakefront where many casual trips start, which blurs the temperature at which the proxy bends."],
    "prior": 0.15,
    "prior_note": "Part (a) about 0.55; part (b) about 0.25 given that New York's bicycle counts removed 2 to 4% of the slope.",
    "registrant": "Claude (round 2 agent, hot-end transfer)",
}
print(claims.register(rec))
