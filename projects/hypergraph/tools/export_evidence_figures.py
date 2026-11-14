#!/usr/bin/env python
"""Export slide PNGs of viz/evidence.html with headless Chrome into figures/viz/.

    ~/.venvs/nyc-concordance/bin/python tools/export_evidence_figures.py

Each figure is rendered from the page's export mode (evidence.html?export=...) at a CSS width of 1040 px and
a device scale of 1.6, so the PNG is 1664 px wide. Blank rows below the content are trimmed, and the file is
saved with an embedded sRGB profile and a 144 ppi resolution tag.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageCms

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "figures" / "viz"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
SIX = ["rlc-expansion-rearend", "rlc-expansion-injuries", "turn-calming-ped", "turn-calming-leftturn",
       "ems-taxi-2026-onset", "restaurants-score-complaints"]
FIGS = [
    ("evidence_cards_placebos.png", f"export=cards&ids={','.join(SIX)}", 900),
    ("evidence_review_changes.png", "export=review", 900),
    ("evidence_lineage_heat-shootings.png", "export=lineage&claim=heat-shootings", 900),
    ("evidence_lineage_levers-vacant-lot-trial-match.png", "export=lineage&claim=levers-vacant-lot-trial-match", 900),
]
SRGB = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()


def trim(img: Image.Image, pad: int = 24) -> Image.Image:
    a = np.asarray(img.convert("RGB")).astype(int)
    bg = a[-1, -1]
    rows = np.where((np.abs(a - bg).sum(axis=2) > 12).any(axis=1))[0]
    bottom = min(a.shape[0], (rows.max() + pad) if len(rows) else a.shape[0])
    return img.crop((0, 0, img.width, bottom))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    page = (ROOT / "viz" / "evidence.html").resolve()
    for name, query, h in FIGS:
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / "shot.png"
            cmd = [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-color-profile=srgb",
                   "--force-device-scale-factor=1.6", f"--window-size=1040,{h}", "--virtual-time-budget=4000",
                   "--allow-file-access-from-files", f"--user-data-dir={td}/prof", f"--screenshot={raw}",
                   f"{page.as_uri()}?{query}"]
            subprocess.run(cmd, check=True, capture_output=True, timeout=120)
            img = trim(Image.open(raw).convert("RGB"))
        dest = OUT / name
        img.save(dest, icc_profile=SRGB, dpi=(144, 144))
        print(f"{dest.relative_to(ROOT)} {img.width}x{img.height}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
