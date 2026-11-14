"""Shared definitions for transit-gtrain-substitution, as registered."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DER = ROOT / "data" / "derived" / "transit"
FIG = ROOT / "figures" / "transit"
DER.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

# G-only station complexes (wujg-7c2s station_complex_id) -> (name, taxi zone, phases with no G service)
G_ONLY = {
    "282": ("21 St", 145, (1, 2)),
    "283": ("Greenpoint Av", 112, (1, 2)),
    "284": ("Nassau Av", 112, (2,)),
    "286": ("Broadway", 80, (2,)),
    "287": ("Flushing Av", 17, (2,)),
    "288": ("Myrtle-Willoughby Avs", 17, (2,)),
    "289": ("Bedford-Nostrand Avs", 17, ()),
    "290": ("Classon Av", 49, (3,)),
    "291": ("Clinton-Washington Avs", 49, (3,)),
    "292": ("Fulton St", 97, (3,)),
}
PHASES = {1: ("2024-06-29", "2024-07-04"), 2: ("2024-07-05", "2024-08-11"), 3: ("2024-08-12", "2024-09-02")}
TREATED = {112: (1, 2), 145: (1, 2), 17: (2,), 80: (2,), 256: (2,), 49: (3,), 97: (3,)}
G_DEPENDENT = (112, 17, 49)
G_SHARED = (25, 40, 106, 133, 181, 257)   # in neither group
AIRPORTS = (132, 138)
WINDOW = ("2024-06-01", "2024-09-30")
DROP_DAYS = ("2024-06-28", "2024-09-03")
