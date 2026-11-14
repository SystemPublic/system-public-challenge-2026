"""EXPLORATORY (not registered; written after the registered results were seen). Placebo and pre-trend
checks for the left-turn calming design in did.py. The registered event series showed the treated/control
ratio falling before installation, so this script estimates:
  placebo   months -24..-13 against -12..-1 (a fake installation 12 months early), same model
  trend-adjusted log ratio = registered log ratio - (25/12) * placebo log ratio, which assumes the
            pre-installation linear trend in the log ratio would have continued (window midpoints are
            25 months apart in the registered contrast and 12 months apart in the placebo)
  year2     months -24..-1 against +13..+24 (second post year only)
Standard errors for the adjusted contrast are approximated by sqrt(se_main^2 + (25/12)^2 se_placebo^2),
ignoring their positive covariance (shared pre months), so they are conservative.
Writes data/derived/turn_restrictions/did_explore.json."""
import json, math, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "analyses/turn_restrictions"))
import did as D  # noqa: E402


def window_factory(a0, a1, b0, b1):
    def w(c, t0):
        pre = sum(v for m, v in c.items() if t0 + a0 <= m <= t0 + a1)
        post = sum(v for m, v in c.items() if t0 + b0 <= m <= t0 + b1)
        return pre, post
    return w


def main():
    sites = json.loads((D.OUT / "sites.json").read_text())["sites"]
    X, Y, M, PED, LT, _ = D.load_crashes()
    counts = D.site_monthly(sites, X, Y, M, PED, LT)
    main_res = json.loads((D.OUT / "did_results.json").read_text())["primary"]
    out = {}
    orig = D.window
    for o in D.OUTCOMES:
        D.window = window_factory(-24, -13, -12, -1)
        pl = D.fit(D.stack(sites, counts, o))
        D.window = window_factory(-24, -1, 13, 24)
        y2 = D.fit(D.stack(sites, counts, o))
        D.window = orig
        m = main_res[o]
        k = 25 / 12
        adj = m["log_ror"] - k * pl["log_ror"]
        se = math.sqrt(m["se_log"] ** 2 + (k * pl["se_log"]) ** 2)
        out[o] = {"registered": {x: m[x] for x in ("ror", "lo", "hi")},
                  "placebo_12m_early": {x: pl[x] for x in ("ror", "lo", "hi")},
                  "second_post_year": {x: y2[x] for x in ("ror", "lo", "hi")},
                  "trend_adjusted": {"ror": round(math.exp(adj), 4), "lo": round(math.exp(adj - 1.96 * se), 4),
                                     "hi": round(math.exp(adj + 1.96 * se), 4)}}
    (D.OUT / "did_explore.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
