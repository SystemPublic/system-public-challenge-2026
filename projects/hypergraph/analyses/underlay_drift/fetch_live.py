"""Pull every live Manhattan row of DOHMH Restaurant Inspection Results (43nn-pn8j)
through concord.socrata, and record the dataset's rowsUpdatedAt.

Writes ~/opt/nyc-concordance/underlay/live_43nn-pn8j_manhattan.csv.gz (the rows)
and data/derived/underlay_drift/live_source.json (the source record).
"""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import socrata  # noqa: E402

OUT_BIG = Path.home() / "opt" / "nyc-concordance" / "underlay"
OUT = ROOT / "data" / "derived" / "underlay_drift"
COLS = ("camis,dba,boro,building,street,zipcode,phone,cuisine_description,inspection_date,action,"
        "violation_code,violation_description,critical_flag,score,grade,grade_date,record_date,"
        "inspection_type,latitude,longitude,community_board,nta")


def main(refresh=False):
    OUT_BIG.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    if refresh:
        socrata.metadata("43nn-pn8j", refresh=True)
    rows, src = socrata.query_all("43nn-pn8j", select=COLS, where="boro='Manhattan'")
    df = pd.DataFrame(rows)
    df.to_csv(OUT_BIG / "live_43nn-pn8j_manhattan.csv.gz", index=False)
    src["local_copy"] = "~/opt/nyc-concordance/underlay/live_43nn-pn8j_manhattan.csv.gz"
    (OUT / "live_source.json").write_text(json.dumps(src, indent=1))
    print(json.dumps(src, indent=1))


if __name__ == "__main__":
    main()
