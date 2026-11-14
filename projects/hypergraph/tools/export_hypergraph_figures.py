"""Export three figures of viz/hypergraph.html to figures/hypergraph/ with headless Chrome.

Usage:
    ~/.venvs/nyc-concordance/bin/python tools/export_hypergraph_figures.py [--check DIR]

Each figure is the page's export mode (hypergraph.html?export=...) at a CSS width of 1280 px and a device
scale factor of 1.3, which gives PNGs 1664 px wide. The files carry an sRGB profile. With --check DIR the
whole page is also written to DIR at 1440 and 800 px wide, light and dark, for inspection.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageCms

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "figures" / "hypergraph"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
SRGB = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
FIGS = [
    ("hypergraph_edge_field.png", "export=field", 2600),
    ("hypergraph_edge_panel_heat_homicide.png", "export=edge&edge=4FaXcuNJRt%7CYZku29igbl", 1400),
    ("hypergraph_edges_about_edges.png", "export=relations", 2600),
]


def trim(img: Image.Image, pad: int = 24) -> Image.Image:
    a = np.asarray(img.convert("RGB")).astype(int)
    bg = a[-1, -1]
    rows = np.where((np.abs(a - bg).sum(axis=2) > 12).any(axis=1))[0]
    return img.crop((0, 0, img.width, min(a.shape[0], (rows.max() + pad) if len(rows) else a.shape[0])))


def shot(query: str, width: int, height: int, scale: float, dest: Path) -> Image.Image:
    page = (ROOT / "viz" / "hypergraph.html").resolve()
    with tempfile.TemporaryDirectory() as td:
        raw = Path(td) / "shot.png"
        cmd = [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-color-profile=srgb",
               f"--force-device-scale-factor={scale}", f"--window-size={width},{height}", "--virtual-time-budget=4000",
               "--allow-file-access-from-files", f"--user-data-dir={td}/prof", f"--screenshot={raw}",
               f"{page.as_uri()}?{query}"]
        subprocess.run(cmd, check=True, capture_output=True, timeout=120)
        img = trim(Image.open(raw).convert("RGB"))
    dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(dest, icc_profile=SRGB, dpi=(144, 144))
    print(f"{dest} {img.width}x{img.height}")
    return img


def main() -> int:
    if "--check" in sys.argv:
        d = Path(sys.argv[sys.argv.index("--check") + 1])
        for w in (1440, 800):
            for th in ("light", "dark"):
                shot(f"theme={th}", w, 5200 if w == 1440 else 7600, 1, d / f"check_{w}_{th}.png")
        return 0
    for name, query, h in FIGS:
        shot(query, 1280, h, 1.3, OUT / name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
