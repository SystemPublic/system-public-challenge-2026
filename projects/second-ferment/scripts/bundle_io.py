"""Write the HeatRx bundle in its three forms: evidence.json, evidence.js (window.HEATRX_BUNDLE) and the
self-contained check page (bundle/check.html from scripts/check_template.html)."""
import json
import os


def write(b, bundle_path):
    with open(bundle_path, "w") as fh:
        json.dump(b, fh, separators=(",", ":"))
    data = "window.HEATRX_BUNDLE=" + json.dumps(b, separators=(",", ":")).replace("</", "<\\/") + ";"
    with open(bundle_path[:-5] + ".js", "w") as fh:
        fh.write(data + "\n")
    tpl = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "check_template.html")).read()
    with open(os.path.join(os.path.dirname(bundle_path), "check.html"), "w") as fh:
        fh.write(tpl.replace("/*BUNDLE*/", data, 1))
