"""Rule 9 check for stalled-flood-zone-starts: the upper bound (-0.0023) is close to the threshold 0, so the bootstrap is
re-run with 20,000 draws (seed 20261113) and with 2,000 draws under 20 other seeds."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from flood_predictor import mh

D = Path(__file__).resolve().parents[2] / "data/derived/stalled"
m = pd.read_csv(D / "flood_jobs.csv")
groups = [g for _, g in m.groupby(["borough", "flood"])]


def run(seed, draws):
    rng = np.random.default_rng(seed)
    arrs = [(g.y.to_numpy(), g.borough.iloc[0], g.flood.iloc[0]) for g in groups]
    bs = []
    for _ in range(draws):
        parts = [pd.DataFrame({"y": rng.choice(y, len(y)), "borough": b, "flood": f}) for y, b, f in arrs]
        bs.append(mh(pd.concat(parts)))
    return float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))


big = run(20261113, 20000)
seeds = {s: run(s, 2000) for s in range(1, 21)}
res = dict(draws20000=big, other_seeds=seeds, upper_below_zero=sum(v[1] < 0 for v in seeds.values()))
print(json.dumps(res, indent=1))
(D / "flood_rule9_check.json").write_text(json.dumps(res, indent=1))
