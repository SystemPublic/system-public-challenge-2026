"""Research evidence on commute time and health in the System graph (Dataverse CSV v2.1, offline).

The graph has no concept for commuting or commute time (only 'telecommuting'), so the
search runs over variable names: associations where one variable mentions commuting and
either variable mentions time, duration, length, minutes, hours or distance. Rows are
then classed by hand into outcome groups. Writes data/derived/commuting/graph_evidence.json.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import duckdb

from analyses.commuting.common import DER

DB = Path.home() / "opt" / "nyc-concordance" / "dataverse" / "graph.duckdb"

GROUPS = {
    "sleep": r"sleep",
    "mental health": r"depress|anxiety|mental|psycholog|fatigue|vitality|burnout|stress",
    "physical inactivity": r"inactiv|sedentary",
    "self-rated health": r"self-reported health",
    "bmi or obesity": r"bmi|body mass|obes|waist",
}


def main():
    c = duckdb.connect(str(DB), read_only=True)
    q = """select system_id, pubmed_id, study_id, statistic_type, statistic_value v, ci_lower lo, ci_upper hi,
                  p_value p, variable_1_name v1, variable_2_name v2
           from associations
           where (lower(variable_1_name) like '%commut%' or lower(variable_2_name) like '%commut%')"""
    d = c.sql(q).df()
    timey = d.apply(lambda r: bool(re.search(r"time|duration|length|minute|hour|long|distance",
                                              f"{r.v1} {r.v2}", re.I)), axis=1)
    # keep exposures that are commute duration or distance, not active-commuting mode
    expo = d.apply(lambda r: bool(re.search(r"commut\w* (time|distance|duration)|time (spent )?(in|on) commut|"
                                             r"duration of (daily commute|public transport commut)|commute time|"
                                             r"long commut|daily commute", f"{r.v1}", re.I)), axis=1)
    sel = d[timey & expo].copy()
    rows = []
    for _, r in sel.iterrows():
        grp = next((g for g, pat in GROUPS.items() if re.search(pat, r.v2, re.I)), None)
        if grp is None:
            continue
        rows.append({"association_id": r.system_id, "pubmed_id": int(r.pubmed_id) if r.pubmed_id == r.pubmed_id else None,
                     "statistic": r.statistic_type, "value": r.v, "lo": None if r.lo != r.lo else r.lo,
                     "hi": None if r.hi != r.hi else r.hi, "exposure": r.v1, "outcome": r.v2, "group": grp})
    summary = {}
    for g in GROUPS:
        gr = [x for x in rows if x["group"] == g]
        ratios = [x["value"] for x in gr if re.search(r"odds|OR|ratio|risk", x["statistic"] or "", re.I)]
        summary[g] = {"n_findings": len(gr), "n_studies": len({x["pubmed_id"] for x in gr}),
                      "ratios_above_1": sum(v > 1 for v in ratios), "ratios": len(ratios),
                      "pubmed_ids": sorted({x["pubmed_id"] for x in gr if x["pubmed_id"]})}
    out = {"source": {"kind": "dataverse", "doi": "doi:10.7910/DVN/7V6JDO", "version": "2.1",
                      "note": "System Public Graph CSV export loaded into DuckDB by analyses/graph_audit/build_dataverse.py"},
           "n_commute_associations": int(len(d)), "n_commute_time_exposure": int(len(sel)),
           "summary": summary, "rows": rows}
    (DER / "graph_evidence.json").write_text(json.dumps(out, indent=1))
    for g, s in summary.items():
        print(f"{g:22s} {s['n_findings']:3d} findings {s['n_studies']:2d} studies; ratios>1 {s['ratios_above_1']}/{s['ratios']}; {s['pubmed_ids']}")


if __name__ == "__main__":
    main()
