"""Answer to critique round 1b (neighbourhood claims, 12 Nov 2026). Verdicts kept; notes added."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from concord import claims as C

def add_note(cid, text, reason):
    o = json.loads((C.OUT / f"{cid}.json").read_text())
    C.revise(cid, {"notes": (o.get("notes") or "") + "\n\nAfter critique round 1b: " + text, "stance": o.get("stance")},
             reason, f"critique/{cid}.md")

add_note("nbhd-vacant-shootings",
    "The association is between neighbourhoods. With NTA fixed effects the IRR is 0.98 (0.94 to 1.01); with NTA-clustered errors the interval is 1.10 to 1.25. It is therefore consistent with neighbourhood-level confounding. The NYC and Philadelphia figures use different outcomes, exposures, units and scales, so they are similar in size but not equal. The exposure is PLUTO 2026 and the shootings are 2019-2024.",
    "Referee: keep confirmed; report within-NTA null and the non-comparability with Philadelphia.")
add_note("nbhd-noise311-exposure",
    "Settling this needs street noise (outdoor sensors) separated from neighbour noise (indoor measurement or survey). Housing form and repeat callers are not addressed.",
    "Referee: keep unsettled; sharpen the settle condition.")
add_note("nbhd-rodents-asthma",
    "This result is fragile. The housing-problems control (EHDP measure 1248, fallback 86) itself includes rodents and cockroaches, which is why it correlates with the exposure at 0.90, so the adjusted coefficient is not rodents net of housing. Adding the non-Hispanic white share gives 0.35 (-0.09 to 0.78); dropping Sunset Park gives -0.06 to 0.90. A re-analysis needs a housing control without pests and adjustment for race and ethnicity. It should not support a bridge until then.",
    "Referee: keep confirmed as registered but flag as fragile; control contains the exposure.")
print("ok")
