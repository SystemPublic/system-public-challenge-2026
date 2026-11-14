from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
DER = ROOT / "data" / "derived" / "health_gaps"
FIG = ROOT / "figures" / "health_gaps"
DER.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)
