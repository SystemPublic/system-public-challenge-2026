"""Registration of transfer-chicago-concordance-matrix. Run once, after the scripts are committed and before any
Chicago indicator value is loaded.

    python analyses/round5_chicago_matrix/register.py <commit that holds the scripts>
"""
import hashlib
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
from concord import claims  # noqa: E402
from chicago_indicators import CHICAGO, NOT_FOUND  # noqa: E402

commit = sys.argv[1]
files = {}
for f in ("chicago_indicators.py", "fetch.py", "matrix.py"):
    b = (HERE / f).read_bytes()
    files[f"analyses/round5_chicago_matrix/{f}"] = {
        "sha256": hashlib.sha256(b).hexdigest(),
        "git_blob": subprocess.run(["git", "hash-object", str(HERE / f)], capture_output=True, text=True, check=True).stdout.strip()}

rec = {
    "id": "transfer-chicago-concordance-matrix",
    "kind": "confirmation",
    "transfer": {"from_city": "New York City", "to_city": "Chicago", "from_claim": "graph-concordance-matrix",
                 "nyc_estimate": {"air_traffic_noise_pairs_agreeing": "10 of 27", "exposure_with_outcome_pairs_agreeing": "29 of 56",
                                  "all_pairs_agreeing": "72 of 109", "always_positive": "70 of 109"}},
    "statement": ("Across Chicago's 77 community areas, pairs of an air pollution or traffic indicator with a health outcome agree with the "
                  "sign of the System Public Graph's findings more often than the same kind of pair did across New York's 42 UHF "
                  "neighbourhoods (10 of 27), as the residential-sorting explanation of the New York result predicts for a city whose "
                  "polluted areas are poor."),
    "graph_evidence": [{
        "concepts": "the New York concept mapping, reused unchanged (data/derived/graph/concordance/indicator_concepts.csv)",
        "n_findings": 8792, "n_studies": None,
        "direction": "all 15 qualifying pairs of PM2.5, ozone or traffic with a Chicago health outcome have a positive literature sign",
        "summary": ("Literature signs are read from data/derived/graph/concordance/literature_signs.csv, computed for graph-concordance-matrix "
                    "on 12 Nov 2026 (API v1.0). Of the 37 Chicago indicators, all map to a New York key; 80 of their pairs qualify in the "
                    "literature (at least 3 signed studies, at least 80% one sign), 77 with a positive sign. Fifteen include PM2.5 (6), "
                    "ozone (5) or traffic (4), each paired with a health outcome. No new graph request is made."),
        "pubmed_ids": []}],
    "literature": [],
    "prediction": {
        "direction": "+",
        "magnitude": ("(a) Share of qualifying pairs that include PM2.5, ozone or traffic whose deciding correlation has the literature's sign: "
                      "60% in Chicago (range 40% to 80%), against 10 of 27 (37%) in New York and 6 of 15 (40%) in New York on the same fifteen "
                      "pairs. (b) Spearman correlation of PM2.5 with poverty across community areas: +0.35 (range +0.10 to +0.60), against "
                      "+0.11 across New York's UHF neighbourhoods (Pearson -0.06; computed from city_indicators_uhf42.csv, n = 42). "
                      "(c) Descriptive: overall agreement of the deciding correlation 68% (range 58% to 78%), and a margin over the "
                      "always-positive rule between -3 and +5 percentage points."),
        "support_if": ("At least 12 qualifying pairs include PM2.5, ozone or traffic and have a computable deciding correlation; all of them are "
                       "pairs of an exposure with a health outcome. Among them the share that agrees with the literature's sign is at least 60%, "
                       "the lower limit of its 95% bootstrap interval (community areas resampled, 2,000 draws, seed 20261113) is above "
                       "New York's 10 of 27 (0.370), and the share exceeds New York's share on the same pairs."),
        "refute_if": ("With at least 12 such pairs, the share is at most 0.370 and the upper limit of the same bootstrap interval is below 60%."),
        "no_test_if": ("Fewer than 12 qualifying pairs that include PM2.5, ozone or traffic have a computable deciding correlation in Chicago "
                       "(for example because an air indicator has no period with 70 of 77 areas). The verdict is then no_test and the "
                       "other quantities are reported as descriptive."),
        "otherwise": "unsettled",
        "prediction_b": ("Scored hit when the Spearman correlation of PM2.5 with poverty is positive and its 95% bootstrap interval excludes "
                         "zero; miss when the estimate is zero or negative; partial otherwise. It does not decide the verdict. If it is a "
                         "miss, the outcome says that Chicago, as measured here, is not a city whose high-PM2.5 areas are poor, and that "
                         "prediction (a) is then not a test of the sorting explanation for PM2.5."),
        "prediction_c": "Reported with intervals, without a verdict.",
    },
    "plan": (
        "Unit: Chicago community area (n = 77). Indicators: the 37 in analyses/round5_chicago_matrix/chicago_indicators.py, each a Chicago "
        "Health Atlas topic matched to a New York indicator key, so that the New York concepts, polarities and literature signs apply "
        "unchanged. Two topics that report absence (uninsured, physically inactive) are reversed as 100 minus the value. Each topic is read "
        "at the community-area layer for the total population, at the latest period (by end year; the longer window on a tie) with a value "
        "for at least 70 of the 77 areas; a topic with no such period is dropped (fetch.py). Qualifying rule, as in New York: signed findings "
        "from at least 3 studies and at least 80% of signed findings on one side. City sign, as in New York: Spearman correlation across "
        "areas, raw, and with poverty partialled out (correlation of the residuals of each indicator's ranks on poverty's ranks); the "
        "partialled correlation decides, and the raw correlation decides for pairs that include poverty. matrix.py copies "
        "spearman_matrix, partial_matrix and decide from analyses/graph_concordance/matrix.py and was checked before registration to "
        "reproduce New York's 72 of 109, 10 of 27 and 29 of 56 from the New York files. Reported for Chicago: agreement overall and by kind "
        "of pair (the four kinds of graph_concordance/explore.py and the referee's three role kinds), each with a 95% bootstrap interval "
        "over areas; the agreement of an always-positive rule and the margin over it with an interval; the area-shuffle null (each "
        "indicator shuffled across areas, poverty fixed) and the sign-shuffle null (literature signs shuffled among qualifying pairs), "
        "2,000 draws each; the Spearman correlation of PM2.5 with poverty with a bootstrap interval. New York is recomputed with the same "
        "code on all its qualifying pairs and on the pairs that qualify and are computable in both cities, and the difference in the "
        "air-and-traffic share on the same pairs is reported with an interval from independent bootstrap draws. Seed 20261113 "
        "(numpy default_rng([seed, 0]) for Chicago, [seed, 1] and [seed, 2] for New York), 2,000 draws. The verdict is computed by "
        "verdict() in matrix.py from the conditions above. Under PRECEDENCE rule 9 the run is repeated with 20,000 draws and with five "
        "other seeds (--draws, --seed, --tag, --no-null); if the bootstrap condition is met under some and not others, the verdict is "
        "unsettled. Scripts fixed at commit " + commit + " on local main and identified by content: " + str(files) + ". "
        "The support condition is on pairs of an exposure with an outcome, where the literature's sign says something about a cause, "
        "and not on the overall rate, which the always-positive rule nearly reproduces (referee report critique/graph-concordance-matrix.md). "
        "Within the fifteen air and traffic pairs every literature sign is positive, so agreement there equals the always-positive rate and "
        "the comparison is between cities, not against that rule. "
        "Differences from New York that the design does not remove: PM2.5 and ozone are EPA EJSCREEN regional model surfaces, smoother than "
        "New York's street-level survey, and ozone may vary very little across the city; traffic is proximity to traffic, not vehicle miles; "
        "asthma is survey prevalence, not emergency visits; premature death is years of potential life lost; low birthweight is not restricted "
        "to term births; depression is a CDC PLACES model estimate built partly from demographic predictors. Notes per indicator are in "
        "chicago_indicators.py. New York indicators with no Chicago match: " + "; ".join(f"{k} ({v})" for k, v in NOT_FOUND.items()) + ". "
        "Disclosure: before registration the registrant read only metadata from the Chicago Health Atlas API (the topic list with names, units "
        "and descriptions; the coverage endpoint, which lists periods and population groups for 59 topics; the layer list) and, to learn the "
        "response format of the data endpoint, one response for the topic POP (total population, not an indicator in this study), of which "
        "about a dozen community-area population counts were displayed. No value of any of the 37 indicators was loaded, and no file under "
        "data/cache/chicago_atlas existed. The project's earlier Chicago claims (transfer-chicago-heat-shootings, -hot-end, -weekday-pattern) "
        "used citywide daily series, not community-area indicators. The New York side is fully seen. The registrant knows from general "
        "reading that Chicago's South and West sides are poorer, have worse health and hold the industrial corridors, that traffic is "
        "densest near the expressways and the Loop, and that EJSCREEN PM2.5 varies by about 1 microgram per cubic metre within a city."),
    "alternatives": [
        "Measurement: a smooth regional PM2.5 or ozone surface ranks community areas by position in the region (a north-south gradient), so its correlation with outcomes may reflect geography and not exposure.",
        "Ozone: in New York ozone pairs agreed (5 of 6) because ozone is lowest in the dense core; the same chemistry may or may not hold on the EJSCREEN surface.",
        "Partialling poverty removes much of what sorting adds in a city where pollution follows poverty, so agreement after partialling may still fail even if the sorting explanation is right; the raw correlation is reported beside it.",
        "Racial segregation: in Chicago health outcomes follow race more closely than the poverty rate, and a poverty partial leaves that in.",
        "Common valence and dependence: fifteen pairs share three exposures and a handful of outcomes, so the effective number of independent pairs is small; the bootstrap over areas carries this.",
        "Different measures of the outcomes in the two cities (prevalence against emergency visits, years of life lost against death before 65).",
    ],
    "prior": 0.35,
    "registrant": "Claude (round 5: Chicago concordance matrix)",
}
print(claims.register(rec))
