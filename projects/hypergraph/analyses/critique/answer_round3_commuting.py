"""Answer to the commuting referee (12 Nov 2026)."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from concord import claims as C
def load(i): return json.loads((C.OUT / f"{i}.json").read_text())

o = load("commute-time-depression")
C.revise("commute-time-depression", {
    "prediction_scored": "uninformative. The design's standard error (about 0.44 points per 5 minutes) gave about 10% power against the predicted upper slope of +0.3, so the registration could not have produced support. The point estimate is not stable: weighting by CHS precision gives +0.19, dropping Manhattan gives +0.67.",
    "settle": "Individual-level data linking commute time to depression (a survey with both items), or a panel around a change in commute time; neighbourhood-level aggregates in NYC lack the power for the effect size the research reports. (A PUMS linkage cannot supply depression and was dropped.)",
    "stance": o.get("stance")},
    "Referee: keep unsettled; the test was uninformative; settle condition revised.", "critique/commute-time-depression.md")

o = load("commute-fhv-subway-distance")
st = o.get("stance") or {}
flipped = {"value": -st["value"], "lo": -st["hi"] if st.get("hi") is not None else None,
           "hi": -st["lo"] if st.get("lo") is not None else None, "z": -st.get("z", 0),
           "note": "Sign taken against the research direction (Barajas and Brown 2021), not the registrant's prediction."} if st.get("value") is not None else None
C.revise("commute-fhv-subway-distance", {"stance": flipped,
    "notes": (o.get("notes") or "") + "\n\nAfter the referee: 'contested' follows the registered rule, but it contradicts the registrant's prediction, not the published research. The one peer-reviewed source (Barajas and Brown 2021) also finds more ride-hail use near transit, and the city data agree with it. The stance is therefore drawn against the research direction. The reversal after adding car-free households is not decisive: car ownership is plausibly a mediator, the reversed estimate is +0.09 with an interval including zero when Staten Island is dropped, and it was registered as report-only."},
    "Referee: keep contested under the rule; stance shown against the research direction, which the city data agree with.", "critique/commute-fhv-subway-distance.md")
print("ok")
