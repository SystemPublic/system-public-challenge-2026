"""Rerun the deciding number of further-tidal-flooding-trend from the package's inputs.

The claim's script, analyses/round2_tidal/analyse.py, is a flat script with no functions to import: on import it
builds a daily panel, runs the primary model, two shifted-tide placebos and fifteen checks with block bootstraps,
and writes results.json and daily_panel.csv into data/derived/round2/tidal_trend/. This wrapper executes the
script's own source with four textual changes, each asserted to match exactly once:

1. D points at the package's inputs.
2. The block that aggregates complaints_by_day_zip.json (27.8 MB, not carried) into daily series is replaced by
   reading the complaint series the deciding models and the sample counts use (C3_t, C3_p, C1_t, C4_t) from
   daily_panel.csv, the panel the script wrote.
   The tide, precipitation, dry-day and knot columns are rebuilt from the carried tide and precipitation files.
3. run() does not write results.json.
4. The script stops after the primary model and the two registered shifted-tide placebos. The random generator
   (seed 20261113) is drawn in the same order as in the full script up to that point, so the bootstrap intervals
   are those of the full run.
"""
import argparse, contextlib, json, sys
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("--inputs", default=str(PKG / "inputs"))
ap.add_argument("--nboot", type=int, default=1000, help="block-bootstrap replicates (registered: 1,000)")
a = ap.parse_args()
INP = Path(a.inputs).resolve()
sys.path.insert(0, str(PKG / "code"))

import requests  # noqa: E402


def _offline(*a, **k):
    raise RuntimeError(f"offline rerun: a pinned input is missing and the code tried to fetch {a[:1]}")


requests.get = _offline

src = (PKG / "code" / "analyses" / "round2_tidal" / "analyse.py").read_text()


def sub(s, old, new):
    assert s.count(old) == 1, f"analyse.py has changed: {old[:60]!r} found {s.count(old)} times"
    return s.replace(old, new)


src = sub(src, 'D = ROOT / "data" / "derived" / "round2" / "tidal_trend"', 'D = INP / "data" / "derived" / "round2" / "tidal_trend"')
i = src.index('C = json.load(open(D / "complaints_by_day_zip.json"))')
j = src.index('df.loc[df.year >= 2020, "C3_t"] = b3t[df.year >= 2020]; df.loc[df.year >= 2020, "C3_p"] = b3p[df.year >= 2020]\n')
j += len('df.loc[df.year >= 2020, "C3_t"] = b3t[df.year >= 2020]; df.loc[df.year >= 2020, "C3_p"] = b3p[df.year >= 2020]\n')
src = src[:i] + ('_P = pd.read_csv(D / "daily_panel.csv", index_col=0, parse_dates=True)\n'
                 'for _c in ("C3_t", "C3_p", "C1_t", "C4_t"): df[_c] = _P[_c].reindex(days)\n') + src[j:]
src = sub(src, '    json.dump(res, open(D / "results.json", "w"), indent=1, default=float)\n', '    pass\n')
src = src[:src.index('    for k in (30, 40, 45): run(')]
g = {"__name__": "analyse_rerun", "__file__": str(PKG / "code" / "analyses" / "round2_tidal" / "analyse.py"), "INP": INP}
sys.argv = [sys.argv[0], str(a.nboot), "0"]
with contextlib.redirect_stdout(sys.stderr):
    exec(compile(src, "analyses/round2_tidal/analyse.py (rerun)", "exec"), g)
res = g["res"]
p, s7, s100 = res["primary"], res["placebo_shift7"], res["placebo_shift100"]
print(json.dumps({"estimate": p["tidal"]["rr"], "lo": p["tidal"]["lo"], "hi": p["tidal"]["hi"], "n": p["n_days"],
                  "ratio_tidal_over_placebo": p["ratio"]["rr"], "ratio_lo": p["ratio"]["lo"], "ratio_hi": p["ratio"]["hi"],
                  "placebo_zip_rr": p["placebo"]["rr"],
                  "shift7_tidal_rr": s7["tidal"]["rr"], "shift7_tidal_hi": s7["tidal"]["hi"],
                  "shift100_tidal_rr": s100["tidal"]["rr"], "shift100_tidal_hi": s100["tidal"]["hi"],
                  "complaints_tidal": p["complaints_tidal"], "n_boot": p["tidal"]["n_boot"]}))
