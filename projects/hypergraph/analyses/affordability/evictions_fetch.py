"""Executed residential evictions (NYC marshals, NYC Open Data 6z8x-wfk4) by community district and year,
mapped to the 55 sub-borough areas. Writes data/derived/affordability/evictions_sba_year.csv and a source record."""
import json, sys
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(ROOT))
from concord import socrata
D = ROOT / "data/derived/affordability"
BORO = {"MANHATTAN": 1, "BRONX": 2, "BROOKLYN": 3, "QUEENS": 4, "STATEN ISLAND": 5}
MERGE = {(1, 1): 101, (1, 2): 101, (1, 3): 102, (1, 4): 103, (1, 5): 103, (1, 6): 104, (1, 7): 105, (1, 8): 106, (1, 9): 107,
         (1, 10): 108, (1, 11): 109, (1, 12): 110, (2, 1): 201, (2, 2): 201, (2, 3): 202, (2, 6): 202, (2, 4): 203, (2, 5): 204,
         (2, 7): 205, (2, 8): 206, (2, 9): 207, (2, 10): 208, (2, 11): 209, (2, 12): 210}
def sba(b, cd):
    if (b, cd) in MERGE: return MERGE[(b, cd)]
    if b in (3, 4, 5): return b * 100 + cd
    return None
rows, src = socrata.query("6z8x-wfk4", select="borough, community_board, date_extract_y(executed_date) as yr, count(*) as n",
                          where="residential_commercial_ind='Residential'", group="borough, community_board, yr", limit=50000)
d = pd.DataFrame(rows); d["n"] = d.n.astype(int)
d["b"] = d.borough.str.upper().map(BORO); d["cd"] = pd.to_numeric(d.community_board, errors="coerce")
d["sba"] = [sba(b, int(c)) if pd.notna(b) and pd.notna(c) else None for b, c in zip(d.b, d.cd)]
tot = d.n.sum(); miss = d[d.sba.isna()].n.sum()
out = d.dropna(subset=["sba"]).groupby(["sba", "yr"]).n.sum().reset_index(); out["sba"] = out.sba.astype(int)
out.to_csv(D / "evictions_sba_year.csv", index=False)
src["unmapped_share"] = float(miss / tot); src["total_rows_counted"] = int(tot)
(D / "evictions_source.json").write_text(json.dumps(src, indent=1))
print(tot, miss, out.groupby("yr").n.sum().to_dict())
