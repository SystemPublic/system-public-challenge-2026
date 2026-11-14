"""Note on transfer-chicago-hot-end after the night-of check of round 5 (verdict unchanged)."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import claims

o = json.loads((ROOT / "claims/outcomes/transfer-chicago-hot-end.json").read_text())
note = ("Round 5 check (analyses/critique/round5_night_of_check.py): this claim counts gunshot injuries by calendar "
        "date, so injuries between 00:00 and 05:59 are counted on a date whose maximum came later. With each injury "
        "assigned to the day whose night it falls in (06:00 to 05:59), the Chicago ratio for 33 against 27 C is "
        "1.035 (0.991 to 1.082) against 1.059 (1.014 to 1.105) by calendar date. Part (a) would then not be met. "
        "The verdict was already unsettled and stays unsettled.")
notes = o.get("notes")
new = (notes + " " + note) if isinstance(notes, str) else (list(notes or []) + [note])
claims.revise("transfer-chicago-hot-end", {"notes": new,
              "verdict_note": "Unsettled. On night-of counts part (a) is also not met (1.035, 0.991 to 1.082)."},
              "Referee of heat-night-minimum: calendar-day counts include small-hours shootings that precede the day's maximum.",
              critique="critique/heat-night-minimum.md")
