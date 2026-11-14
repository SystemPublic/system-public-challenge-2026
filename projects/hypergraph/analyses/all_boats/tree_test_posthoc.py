"""Post hoc checks on the exploratory crime slope of all-boats-trees-rent. Chosen after the
data were seen; they decide nothing (precedence rule 4)."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd, statsmodels.formula.api as smf
sys.path.insert(0, str(Path(__file__).parent))
from tree_test import base, OUT
d = base().merge(pd.read_csv(OUT / "violent_crime_tracts.csv", dtype={"geoid": str}), on="geoid", how="left").fillna({"viol_early": 0, "viol_late": 0})
d["lbase"] = np.log1p(d.viol_early)
d = d[d.poverty.notna()]
res = {}
for name, f in {"plus_poverty": "viol_late ~ dt100 + lbase + trees05_km + lrent12 + nhw_share12 + ldens12 + poverty + C(boro)",
                "nta_fixed_effects": "viol_late ~ dt100 + lbase + trees05_km + lrent12 + nhw_share12 + ldens12 + poverty + C(nta2020)"}.items():
    m = smf.glm(f, d, family=__import__("statsmodels.api").api.families.Poisson()).fit(cov_type="cluster", cov_kwds={"groups": d.nta2020})
    lo, hi = m.conf_int().loc["dt100"]
    res[name] = {"estimate": float(m.params["dt100"]), "lo": float(lo), "hi": float(hi), "n": int(m.nobs)}
m = smf.ols("d_logrent ~ dt100 + trees05_km + lrent12 + nhw_share12 + ldens12 + C(nta2020)", d).fit(cov_type="cluster", cov_kwds={"groups": d.nta2020})
lo, hi = m.conf_int().loc["dt100"]
res["rent_nta_fixed_effects"] = {"estimate": float(m.params["dt100"]), "lo": float(lo), "hi": float(hi), "n": int(m.nobs)}
res["citywide_change_violent"] = float(d.viol_late.sum() / d.viol_early.sum() - 1)
res["gain_by_third"] = d.groupby("third").apply(lambda g: {"mean_gain_trees": float(g.dt100.mean() * 100), "share_gaining": float((g.dt100 > 0).mean()),
                                                           "violent_change": float(g.viol_late.sum() / g.viol_early.sum() - 1),
                                                           "rent_change_log": float(g.d_logrent.mean())}).to_dict()
(OUT / "tree_test_posthoc.json").write_text(json.dumps(res, indent=1))
print(json.dumps(res, indent=1))

# Rival found after the data: since 2008 the zoning resolution requires street trees with new
# buildings, so tree gain may mark new construction, which adds residents (more crime counted)
# and new units at higher rents. Adjust for population change, ACS 2008-12 to 2018-22.
d["dlogpop"] = np.log(d["pop"] / d.pop12)
m = smf.glm("viol_late ~ dt100 + dlogpop + lbase + trees05_km + lrent12 + nhw_share12 + ldens12 + poverty + C(boro)", d,
            family=__import__("statsmodels.api").api.families.Poisson()).fit(cov_type="cluster", cov_kwds={"groups": d.nta2020})
lo, hi = m.conf_int().loc["dt100"]
res["crime_plus_population_change"] = {"estimate": float(m.params["dt100"]), "lo": float(lo), "hi": float(hi), "n": int(m.nobs)}
m = smf.ols("d_logrent ~ dt100 + dlogpop + trees05_km + lrent12 + nhw_share12 + ldens12 + C(boro)", d).fit(cov_type="cluster", cov_kwds={"groups": d.nta2020})
lo, hi = m.conf_int().loc["dt100"]
res["rent_plus_population_change"] = {"estimate": float(m.params["dt100"]), "lo": float(lo), "hi": float(hi), "n": int(m.nobs)}
res["corr_gain_population_change"] = float(d[["dt100", "dlogpop"]].corr(method="spearman").iloc[0, 1])
(OUT / "tree_test_posthoc.json").write_text(json.dumps(res, indent=1))
print({k: res[k] for k in ("crime_plus_population_change", "rent_plus_population_change", "corr_gain_population_change")})
