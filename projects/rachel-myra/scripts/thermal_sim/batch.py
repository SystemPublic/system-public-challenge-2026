"""Run many itineraries at once (vectorised over samples)."""
from __future__ import annotations

from typing import List, Sequence

import numpy as np

from .model import ENV_CODE, Weather, legs_to_grid, run
from .params import v


def run_batch(weather: Weather, legs_list: List[list], pkg_ids: Sequence[str], T0: Sequence[float]):
    """Returns (temps (N, K+1), env (N, K), times (N, K), valid (N, K) mask)."""
    grids = [legs_to_grid(l) for l in legs_list]
    K = max(len(g[0]) for g in grids)
    N = len(grids)
    dt = v("num", "dt_s")
    times = np.empty((N, K))
    env = np.empty((N, K), int)
    valid = np.zeros((N, K), bool)
    for i, (t, e) in enumerate(grids):
        n = len(t)
        times[i, :n] = t
        env[i, :n] = e
        valid[i, :n] = True
        if n < K:  # pad: keep integrating in the last environment, masked out
            times[i, n:] = t[-1] + dt * np.arange(1, K - n + 1)
            env[i, n:] = e[-1]
    out = run(weather, times, env, list(pkg_ids), np.asarray(T0, float))
    return out["temp"], env, times, valid
