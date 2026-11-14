"""EXPLORATORY (not registered, decides nothing): which NTA unions near the AALDEF boundary give counts close to AALDEF's table?"""
import json, itertools
import pandas as pd
from concord import socrata as s
from analyses.further import chinatown_analysis as A   # re-runs analysis import; fine
rows, src = s.query("8ius-dhrr", limit=3000)
nta = {("36061" + r["_2010_census_tract"].zfill(6)): r["neighborhood_tabulation_area_nta_code"] for r in rows if r["borough"] == "Manhattan"}
cands = ["MN27", "MN28", "MN24", "MN25", "MN22"]
out = []
for k in range(1, 4):
    for combo in itertools.combinations(cands, k):
        s10 = [g for g, n in nta.items() if n in combo]; s20 = A.s20_m1(s10)
        n10 = A.t10.loc[s10, "nh_ap"].sum(); n20a = A.acs.loc[s20, "nh_ap"].sum(); n20c = A.t20.loc[s20, "nh_ap"].sum()
        out.append(dict(ntas="+".join(combo), tot10=int(A.t10.loc[s10, "total"].sum()), nhap10=int(n10), nhap20_acs=int(n20a), pct_acs=round((n20a / n10 - 1) * 100, 1),
                        nhap20_census=int(n20c), pct_census=round((n20c / n10 - 1) * 100, 1), white10=int(A.t10.loc[s10, "nh_white"].sum()), black10=int(A.t10.loc[s10, "nh_black"].sum()), hisp10=int(A.t10.loc[s10, "hisp"].sum())))
df = pd.DataFrame(out); df["dist"] = ((df.tot10 - 116722).abs() / 116722 + (df.nhap10 - 52613).abs() / 52613)
pd.set_option("display.width", 250)
print(df.sort_values("dist").head(8).to_string())
df.to_csv(A.D / "chinatown_exploratory_unions.csv", index=False)
