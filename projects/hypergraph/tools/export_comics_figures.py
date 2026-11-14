"""Export the strips of viz/comics.html to figures/comics/ with headless Chrome.

Usage:
    ~/.venvs/nyc-concordance/bin/python tools/export_comics_figures.py [--check DIR]

Each figure is the page's export mode (comics.html?export=<strip id>&frames=...) at a CSS width of 1280 px and
a device scale factor of 1.5, which gives PNGs 1920 px wide. The files carry an sRGB profile. The lettering
face is loaded from Google Fonts, so the export needs a network connection. With --check DIR the whole page is
written to DIR at 1440 and 800 px wide for inspection.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageCms

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "figures" / "comics"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
SRGB = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
# file name, query, CSS width
FIGS = [
    ("strip_heat.png", "export=heat&cap=17", 1280),
    ("strip_aircon.png", "export=aircon&cap=17", 1280),
    ("strip_restaurants.png", "export=restaurants&cap=14", 1280),
    ("strip_cameras.png", "export=cameras&cap=17", 1280),
    ("strip_rivals.png", "export=rivals&cap=14", 1280),
    ("strip_moon.png", "export=moon&cap=17", 1280),
    ("strip_medicine.png", "export=medicine&cap=17", 1280),
    ("grammar.png", "export=grammar", 1280),
]


def trim(img: Image.Image, pad: int = 20) -> Image.Image:
    a = np.asarray(img.convert("RGB")).astype(int)
    bg = a[-1, -1]
    rows = np.where((np.abs(a - bg).sum(axis=2) > 12).any(axis=1))[0]
    return img.crop((0, 0, img.width, min(a.shape[0], (rows.max() + pad) if len(rows) else a.shape[0])))


def shot(query: str, width: int, height: int, scale: float, dest: Path) -> Image.Image:
    page = (ROOT / "viz" / "comics.html").resolve()
    with tempfile.TemporaryDirectory() as td:
        raw = Path(td) / "shot.png"
        cmd = [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-color-profile=srgb",
               f"--force-device-scale-factor={scale}", f"--window-size={width},{height}", "--virtual-time-budget=6000",
               "--allow-file-access-from-files", f"--user-data-dir={td}/prof", f"--screenshot={raw}",
               f"{page.as_uri()}?{query}"]
        subprocess.run(cmd, check=True, capture_output=True, timeout=120)
        img = trim(Image.open(raw).convert("RGB"))
    dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(dest, icc_profile=SRGB, dpi=(144, 144))
    print(f"{dest.relative_to(ROOT) if dest.is_relative_to(ROOT) else dest} {img.width}x{img.height}")
    return img


def main() -> int:
    if "--check" in sys.argv:
        d = Path(sys.argv[sys.argv.index("--check") + 1])
        for w in (1440, 800):
            shot("", w, 4200 if w == 1440 else 9000, 1, d / f"check_{w}.png")
        return 0
    for name, query, width in FIGS:
        shot(query, width, 1400, 1.5, OUT / name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
