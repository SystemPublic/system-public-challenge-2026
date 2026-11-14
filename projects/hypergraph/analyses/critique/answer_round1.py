"""Answer to critique round 1 (12 Nov 2026): apply the accepted changes through
concord.claims.revise, which keeps each earlier outcome in `history`.
The referee's reports are in critique/<id>.md; the answers are in critique/ANSWERS.md."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from concord import claims as C

O = C.OUT
def load(i): return json.loads((O / f"{i}.json").read_text())

# 1. Four-year completion: the registered pooled statistic decides (rule 1-2, 4).
C.revise("construction-four-year-completion", {
    "verdict": "unsettled",
    "city_effect": {"label": "share of NB jobs with a first CO within 4 years of first NB permit, pooled cohorts 2010-2017 (registered statistic)",
                    "estimate": 0.734, "lo": 0.727, "hi": 0.741, "scale": "proportion; null set to the registered support threshold 0.75",
                    "null": 0.75, "n": 15224},
    "exploratory": {"label": "cohorts 2013-2017 only (chosen after seeing that the legacy CO table starts July 2012)",
                    "estimate": 0.807, "lo": 0.799, "hi": 0.814, "n": 10712},
    "prediction_scored": "partial. The registered pooled 2010-2017 share is 0.734 (0.727-0.741), between the support threshold (0.75) and the refutation threshold (0.65), so the registered rule gives unsettled. The 2013-2017 figure of 0.807 is exploratory. The Housing Database shares are not an independent check, because their completion dates come from DOB certificates of occupancy.",
}, "Referee: the verdict was moved by a post hoc cohort restriction; HDB is not independent of DOB COs.", "critique/construction-four-year-completion.md")

# 2. Permit funnel: the registered per-year rule fails in 2010-2012.
C.revise("construction-permit-funnel", {
    "verdict": "unsettled",
    "prediction_scored": "partial. Registered support required at least 3 rows per distinct job in every issuance year 2010-2019. Per-year values are 2.55 (2010), 2.64 (2011), 2.90 (2012) and 3.00-3.28 for 2013-2019, so the rule fails in three years; the refutation rule is not met either. Lifetime rows per job by cohort (7.0-10.3) and 54% renewals are exploratory measures chosen after the per-year figure was seen. That permit rows overstate buildings is not in doubt; the registered test did not decide it.",
    "stance": None,
}, "Referee: the registered per-year rule fails for 2010-2012; the outcome substituted a lifetime measure.", "critique/construction-permit-funnel.md")

# 3. CRZ NO2 (NYCCAS): registered refutation is met -> contested (rule 1).
C.revise("mob-crz-air-nyccas", {"verdict": "contested"},
    "Referee: the registered refutation (DiD at or above 0, inside the placebo distribution) is met; rule 1 gives contested.",
    "critique/mob-crz-air-nyccas.md")

# 4. CRZ air (AQS): the primary NO2 test could not run -> no_test (rule 3).
C.revise("mob-crz-air", {"verdict": "no_test", "stance": None},
    "Referee: no Manhattan NO2 monitor in AQS 2022-2025, so the registered primary test was not run; the PM2.5 secondary mixes monitor methods and a changing comparison set.",
    "critique/mob-crz-air.md")

# 5. Bridge chain: weakest-link stance (rule 5).
reg = json.loads((C.REG / "heat-trees-ed-chain.json").read_text())
C.revise("heat-trees-ed-chain", {"stance": C.bridge_stance(reg["chain"])},
    "Referee: the composed product agrees in sign only because both links have the wrong sign; stance now from the weakest link.",
    "critique/heat-trees-ed-chain.md")

# 6. Aerial triangulation: proportion with null 0 has no meaningful stance (rule 6).
C.revise("construction-aerial-triangulation", {"stance": None},
    "Referee: stance computed against null 0 for a proportion is meaningless.", "critique/construction-aerial-triangulation.md")

# 7. Sheds: a ratio of two counts is a description, not a test against research; keep verdict, stance null.
C.revise("construction-sheds-outnumber-nb", {"stance": None},
    "Referee: keep the verdict for the permit counts only; the ratio has no research-side null.", "critique/construction-sheds-outnumber-nb.md")

# 8. Active commuting: keep confirmed for the area-level association; research comparison marked not comparable.
o = load("mob-active-commute-obesity")
ge = dict(o.get("graph_effect") or {}); ge["comparable"] = False
ge["note"] = "Not comparable: an area-level slope across 42 UHFs is not the individual-level effect in the research."
C.revise("mob-active-commute-obesity", {"graph_effect": ge},
    "Referee: the area-level slope is far too large to compare with individual-level research effects.", "critique/mob-active-commute-obesity.md")

# 9. Surface temperature -> ED: keep contested, narrow the label.
o = load("heat-surftemp-ed"); ce = dict(o["city_effect"])
ce["label"] = "Area-level (community district) association, contradicting the registrant's bridge link: " + ce["label"]
C.revise("heat-surftemp-ed", {"city_effect": ce},
    "Referee: keep contested, but label it as an area-level association that contradicts the bridge link, not the individual-level research.",
    "critique/heat-surftemp-ed.md")
print("revised")
