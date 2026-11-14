"""Export viz/heat_drugs.html (export mode) to figures/heat_drugs/heat_drugs_map.png with headless Chrome.

CSS width 1040 px at device scale 1.6 gives a 1664 px wide PNG, saved with an embedded sRGB profile and a 144 ppi tag.
"""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageCms

ROOT = Path(__file__).resolve().parents[2]
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
SRGB = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
import sys  # noqa: E402
sys.path.insert(0, str(ROOT / "tools"))
from export_evidence_figures import trim  # noqa: E402


def main():
    out = ROOT / "figures/heat_drugs/heat_drugs_map.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    page = (ROOT / "viz/heat_drugs.html").resolve()
    with tempfile.TemporaryDirectory() as td:
        raw = Path(td) / "shot.png"
        cmd = [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-color-profile=srgb",
               "--force-device-scale-factor=1.6", "--window-size=1040,1200", "--virtual-time-budget=4000",
               "--allow-file-access-from-files", f"--user-data-dir={td}/prof", f"--screenshot={raw}", f"{page.as_uri()}?export=1"]
        subprocess.run(cmd, check=True, capture_output=True, timeout=120)
        img = trim(Image.open(raw).convert("RGB"))
    img.save(out, icc_profile=SRGB, dpi=(144, 144))
    print(out.relative_to(ROOT), img.width, img.height)


if __name__ == "__main__":
    main()
