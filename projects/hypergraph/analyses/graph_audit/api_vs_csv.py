"""How many System API associations are absent from the Dataverse CSV?

The v1.0 API documentation says that about 20% of the associations the API
returns are mis-extracted, that these were removed from the Dataverse CSV
(doi:10.7910/DVN/7V6JDO, v2.1), and that API associations absent from the CSV
should be dropped. This script measures the absent share for a sample of
urban and public-health concepts and for the variables whose names contain
"vacant".

For each concept it pages through GET /v1/associations filtered on
variable_1_concept_id and on variable_2_concept_id (1000 rows per call), and
for each vacant-property variable through GET /v1/variables/{id}/associations.
Every API association id is looked up in the DuckDB copy of the CSV built by
build_dataverse.py. Responses are cached by concord.sysgraph.

Outputs (repo-relative):
  data/derived/graph_audit/api_vs_csv_by_concept.csv
  data/derived/graph_audit/api_vs_csv_by_stat.csv
  data/derived/graph_audit/api_vs_csv_rows.parquet   one row per API association
"""
from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import sysgraph  # noqa: E402

DB = Path.home() / "opt" / "nyc-concordance" / "dataverse" / "graph.duckdb"
OUT = ROOT / "data" / "derived" / "graph_audit"

CONCEPTS = {
    "k9BAffdSqv": "heat wave",
    "X7hfhwez9f": "gun violence",
    "lHLIKbfnYp": "green space",
    "UbF0-c8zHb": "urban heat island",
    "P6IzhScRdx": "air pollution",
    "EAshH_Ko3h": "asthma",
    "36gde7OoEQ": "noise pollution",
    "nS9fqJ01TW": "emergency department",
    "rYCo7LTyzN": "heat stroke",
    "DC_F0GO0WQ": "nitrogen dioxide",
    "5aHRpqbEkQ": "traffic collision",
    "V7ImOTxbql": "crime",
    "IFcQ3j86qe": "housing",
    "kC0GoD2RzW": "urban area",
    "bIwjlkmcHV": "poverty",
    "14UOQBVakG": "firearm",
}
MAX_PER_SIDE = 25000


def api_assocs_for_concept(cid: str) -> list[dict]:
    rows = []
    for side in (1, 2):
        rows += sysgraph.page_all("/v1/associations", {"filter": f"variable_{side}_concept_id:{cid}"},
                                  limit=1000, max_items=MAX_PER_SIDE)
    seen, out = set(), []
    for r in rows:
        if r["system_id"] not in seen:
            seen.add(r["system_id"])
            out.append(r)
    return out


def main() -> None:
    con = duckdb.connect(str(DB), read_only=True)
    frames = []
    for cid, label in CONCEPTS.items():
        rows = api_assocs_for_concept(cid)
        df = pd.DataFrame(rows)
        df["sample"] = label
        df["sample_kind"] = "concept"
        frames.append(df)
        print(f"{label:22s} {len(df):6d} API associations", flush=True)
    for v in sysgraph.variables("vacant", limit=50):
        rows = sysgraph.variable_associations(v["system_id"])
        if not rows:
            continue
        df = pd.DataFrame(rows)
        df["sample"] = "vacant: " + v["name"]
        df["sample_kind"] = "variable"
        frames.append(df)
    api = pd.concat(frames, ignore_index=True)
    con.register("api_ids", api[["system_id"]].drop_duplicates())
    found = con.execute("SELECT a.system_id FROM api_ids a JOIN associations c USING (system_id)").df()
    api["in_csv"] = api["system_id"].isin(set(found["system_id"]))
    # do the absent rows belong to a relationship that survives in the CSV?
    api["rel_id"] = api["variable_1_concept_id"].astype(str) + "|" + api["variable_2_concept_id"].astype(str)
    con.register("api_rels", api[["rel_id"]].drop_duplicates())
    rels = con.execute("SELECT r.rel_id FROM api_rels r JOIN relationships x ON x.relationship_id = r.rel_id").df()
    api["rel_in_csv"] = api["rel_id"].isin(set(rels["rel_id"]))
    api["both_grounded"] = api["variable_1_concept_id"].notna() & api["variable_2_concept_id"].notna()

    keep = ["system_id", "sample", "sample_kind", "statistic_type", "system_statistic_type", "statistic_value",
            "ci_lower", "ci_upper", "p_value", "variable_1_name", "variable_2_name", "variable_1_concept_id",
            "variable_2_concept_id", "pubmed_id", "study_id", "in_csv", "rel_in_csv", "both_grounded"]
    OUT.mkdir(parents=True, exist_ok=True)
    api[keep].to_parquet(OUT / "api_vs_csv_rows.parquet", index=False)

    api["vacant"] = api["sample"].str.startswith("vacant:")
    api["group"] = api["sample"].where(~api["vacant"], "vacant-property variables")
    by = api.drop_duplicates(["group", "system_id"]).groupby("group").agg(
        api_n=("system_id", "size"), in_csv=("in_csv", "sum"), rel_in_csv=("rel_in_csv", "sum"),
        both_grounded=("both_grounded", "sum"))
    by["absent_share"] = 1 - by["in_csv"] / by["api_n"]
    u = api.drop_duplicates("system_id")
    by.loc["ALL (distinct)"] = [len(u), u["in_csv"].sum(), u["rel_in_csv"].sum(), u["both_grounded"].sum(),
                                1 - u["in_csv"].mean()]
    by = by.sort_values("api_n", ascending=False)
    by.to_csv(OUT / "api_vs_csv_by_concept.csv")
    print(by.to_string())

    st = u.groupby("system_statistic_type").agg(api_n=("system_id", "size"), in_csv=("in_csv", "sum"))
    st["absent_share"] = 1 - st["in_csv"] / st["api_n"]
    st = st.sort_values("api_n", ascending=False)
    st.to_csv(OUT / "api_vs_csv_by_stat.csv")
    print(st.to_string())
    ab = u[~u["in_csv"]]
    print("absent rows whose concept pair is a CSV relationship:", int(ab["rel_in_csv"].sum()), "of", len(ab))
    print("absent rows with both variables grounded:", int(ab["both_grounded"].sum()), "of", len(ab))


if __name__ == "__main__":
    main()
