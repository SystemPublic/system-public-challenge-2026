"""Study populations behind telework, commuting and transit-ridership variables.
Run: ~/.venvs/nyc-concordance/bin/python -u -m analyses.transfer.graph_telework
Writes data/derived/graph/transfer_chicago/telework_commute_studies.json
"""
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import analyses.transfer.gcount as gc  # noqa
from concord import sysgraph as g  # noqa

OUT = ROOT / "data" / "derived" / "graph" / "transfer_chicago"
GROUPS = {
    "telework": (["telework", "telecommuting", "remote work", "hybrid work", "working from home", "work from home"],
                 re.compile(r"telework|telecommut|work(ing)? (from|at) home|remote(ly)? work|working remotely|hybrid work|home.?based work|home.?working", re.I), 120),
    "ridership": (["ridership", "transit ridership", "public transit ridership", "subway ridership"], re.compile(r"ridership", re.I), 40),
    "commuting": (["commuting", "commute", "commuting time", "active commuting"], re.compile(r"commut", re.I), 110),
}
MAXSTUDIES = 260


def main():
    res = {}
    studies = {}
    for grp, (searches, rx, cap) in GROUPS.items():
        seen = {}
        for t in searches:
            for r in g.variables(t, limit=100):
                if rx.search(r.get("name") or ""):
                    seen[r["system_id"]] = r
        vs = list(seen.values())[:cap]
        print(grp, len(seen), "variables;", len(vs), "used", gc.N, flush=True)
        sids = {}
        for r in vs:
            for a in g.variable_associations(r["system_id"], max_items=100):
                if a.get("study_id"):
                    sids.setdefault(a["study_id"], a.get("pubmed_id"))
        res[grp] = {"n_variables_found": len(seen), "n_variables_used": len(vs), "study_ids": sorted(sids)}
        print(grp, len(sids), "studies", gc.N, flush=True)
    allids = sorted({s for v in res.values() for s in v["study_ids"]})
    print("distinct studies", len(allids), flush=True)
    for i, sid in enumerate(allids[:MAXSTUDIES]):
        s = g.study(sid)
        studies[sid] = {"pubmed_id": s.get("pubmed_id"), "doi": s.get("doi"), "population": s.get("population")}
        if i % 25 == 0:
            print(i, gc.N, flush=True)
    res["studies"] = studies
    res["n_studies_not_fetched"] = max(0, len(allids) - MAXSTUDIES)
    res["uncached_requests"] = gc.N["uncached"]
    (OUT / "telework_commute_studies.json").write_text(json.dumps(res, indent=1))
    print("DONE", gc.N, flush=True)


if __name__ == "__main__":
    main()
