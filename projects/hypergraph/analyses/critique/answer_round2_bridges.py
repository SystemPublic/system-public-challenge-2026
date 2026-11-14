"""Answer to the bridge referee (12 Nov 2026): apply rule 8 (discriminating endpoint tests)."""
import json, math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from concord import claims as C

def load(i): return json.loads((C.OUT / f"{i}.json").read_text())

# Crash bridge: z_chain 0.32, z_null 0.43 (referee, critique/bridge-crz-injury-crashes.md).
st = C.endpoint_stance(0.32, 0.43)
o = load("bridge-crz-injury-crashes")
C.revise("bridge-crz-injury-crashes", {"verdict": "unsettled", "stance": st,
    "notes": (o.get("notes") or "") + "\n\nAfter the bridge referee: the composed prediction (-0.4%) is near zero because the speed and volume terms cancel, so the endpoint (z 0.32 from the chain, 0.43 from no effect) cannot separate the chain from no effect; a contentless chain would have passed with probability above 0.99. The endpoint also depends on an unregistered geocoding change: injury crashes without coordinates fell from 8.7-10.7% (2022-24) to 2.6% (2025), a bias of 0 to about -10 points; at -10 points the estimate is about +11.5% (z about 2.1), which would refute the chain. Re-estimating against a comparison area that avoids the geocoding change (Manhattan north of 60th St) is exploratory now that the endpoint has been seen, and is listed as research needed."},
    "Rule 8: the endpoint test does not discriminate (D = 0.08); verdict unsettled.", "critique/bridge-crz-injury-crashes.md")

# Heat-EMS bridge: z_chain 0.41; z_null from the endpoint IRR against 1.
o = load("bridge-heat-shootings-ems"); e = o["city_effect"]
se = (math.log(e["hi"]) - math.log(e["lo"])) / 3.92
z_null = math.log(e["estimate"]) / se
st = C.endpoint_stance(0.41, z_null)
C.revise("bridge-heat-shootings-ems", {"stance": st,
    "notes": (o.get("notes") or "") + f"\n\nAfter the bridge referee: the test discriminates from no effect (z_null {z_null:.1f}) but is weak in specificity. About 37% of SHOT dispatches are the shooting victims counted in the first link, the test refutes only if the dispatch multiplier lies outside about [-0.08, 1.09], and the stabbing contrast (IRR 1.076) would also have passed. It supports 'heat raises violence-related EMS load' more than this particular chain. Modelling non-victim dispatches directly is listed as exploratory research needed."},
    "Rule 8 applied: discriminates from null; kept bridged with weak-specificity note.", "critique/bridge-heat-shootings-ems.md")

# Link claims.
o = load("bridge-shot-ems-link")
C.revise("bridge-shot-ems-link", {"stance": None, "notes": (o.get("notes") or "") + "\n\nAfter the bridge referee: this is a check on how records are kept (one shooting, about 1.25 EMS gunshot dispatches), not a research link; it has no graph estimate, so no stance. The same-day slope is confounded by temperature."},
    "Referee: keep; stance null.", "critique/bridge-shot-ems-link.md")
o = load("bridge-crz-crash-link")
C.revise("bridge-crz-crash-link", {"prediction_scored": "not scored: a research link with no city test of its own. The volume elasticity of 0.9 is an assumption, not an estimate.", "stance": None},
    "Referee: keep no_test; not scored; elasticity is an assumption.", "critique/bridge-crz-crash-link.md")
print(st)
