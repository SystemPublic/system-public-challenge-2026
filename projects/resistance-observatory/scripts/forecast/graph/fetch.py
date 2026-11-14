"""Stage 1: variable-name searches. Stage 2: associations for kept variables.
Stage 3: studies. Writes stage outputs to work/*.json. Run:
  set -a; source <repo>/.env.local; set +a; python3 fetch.py <stage>
Responses are cached in raw/, so re-running costs no requests."""
import json, os, re, sys, urllib.parse
import apilib
from apilib import resp, paged, pmap

HERE = apilib.HERE
WORK = os.path.join(apilib.RAW, "work")
os.makedirs(WORK, exist_ok=True)

SP_TERMS = ["sulfadoxine", "sulphadoxine", "sulfadoxine-pyrimethamine", "sulphadoxine-pyrimethamine",
            "sulfadoxine pyrimethamine", "Fansidar", "pyrimethamine", "IPTp", "IPTp-SP",
            "intermittent preventive treatment", "intermittent preventive therapy",
            "seasonal malaria chemoprevention", "SPAQ", "SP-AQ", "SP+AQ", "IPTi",
            "perennial malaria chemoprevention", "SMC"]
DHPS_TERMS = ["dhps", "pfdhps", "dihydropteroate", "K540E", "540E", "540", "A437G", "437G",
              "quintuple", "sextuple", "dhfr-dhps", "IRNGE", "SGEAA", "ISGEAA", "581G"]

SP_RX = re.compile(r"sulfadoxine|sulphadoxine|sulfadoxin|fansidar|\bSP\b|\bSPAQ\b|SP[-+/ ]AQ|\bIPTp-SP\b|\bSP-IPTp\b", re.I)
DHPS_RX = re.compile(r"dhps|dihydropteroate", re.I)
K540_RX = re.compile(r"540\s*E|540\s*K\s*/\s*E|Glu-?540|K540|SGEAA|IRNGE|quintuple|sextuple", re.I)


def stage1():
    out = {}
    for t in SP_TERMS + DHPS_TERMS:
        q = urllib.parse.quote(t, safe="")
        rows, total, err = paged(f"/variables?search=name:{q}", page=200, maxrows=1000)
        out[t] = {"hits": len(rows), "error": err, "rows": rows}
        print(f"{t!r}: {len(rows)} {'ERR '+str(err) if err else ''}")
    json.dump(out, open(os.path.join(WORK, "search.json"), "w"), indent=1)


if __name__ == "__main__":
    if sys.argv[1] == "1": stage1()
    print(apilib.COUNT)


EXCL_RX = re.compile(r"carinii|pneumocystis|co-trimoxazole|dihydropyridine|DHPs\)|\(DHPs|Dental|16-DHPS|triathlon|searches for DHPs|^DHPs$|Seasonal Pattern|seasonality|mood disorder|step size|^SPAQ$", re.I)
SP_CONCEPTS = ["bzQO0hAZXK", "6Q_i0GlCWE"]  # sulfadoxine Q411557, pyrimethamine Q421072
CAP = int(os.environ.get("NET_CAP", "285"))


def load_vars():
    s = json.load(open(os.path.join(WORK, "search.json")))
    v = {}
    for t, d in s.items():
        for r in d["rows"]:
            v.setdefault(r["system_id"], dict(r, terms=[]))["terms"].append(t)
    return v


def is_sp_name(n):
    return bool(SP_RX.search(n or "")) and not EXCL_RX.search(n or "")


def is_dhps_name(n):
    n = n or ""
    if EXCL_RX.search(n):
        return False
    return bool(DHPS_RX.search(n) or K540_RX.search(n))


def stage2():
    v = load_vars()
    assoc = {}
    # A. concept filters (already cheap)
    for c in SP_CONCEPTS:
        for side in ["variable_1_concept_id", "variable_2_concept_id"]:
            rows, _, _ = paged(f"/associations?filter={side}:{c}", page=1000, maxrows=5000)
            for r in rows:
                assoc.setdefault(r["system_id"], dict(r, _via=[]))["_via"].append(f"concept:{side}:{c}")
    # B. per-variable: dhps first, then SP vars not grounded to SP concepts
    dh = sorted([x for x in v.values() if is_dhps_name(x["name"])], key=lambda x: x["system_id"])
    sp = sorted([x for x in v.values() if is_sp_name(x["name"]) and x.get("concept_id") not in SP_CONCEPTS
                 and not is_dhps_name(x["name"])], key=lambda x: x["system_id"])
    done, skipped = [], []
    def fetch_var(x):
        if apilib.COUNT["net"] >= CAP:
            return x, None
        rows, _, err = paged(f"/variables/{x['system_id']}/associations", page=500, maxrows=2000)
        return x, rows
    for group in (dh, sp):
        for x, rows in pmap(fetch_var, group):
            if rows is None:
                skipped.append(x); continue
            done.append(x["system_id"])
            for r in rows:
                assoc.setdefault(r["system_id"], dict(r, _via=[]))["_via"].append(f"variable:{x['system_id']}")
    json.dump({"assoc": assoc, "vars_fetched": done, "vars_skipped": skipped,
               "n_dhps_vars": len(dh), "n_sp_vars_nonconcept": len(sp)},
              open(os.path.join(WORK, "assoc.json"), "w"), indent=1)
    print("assoc", len(assoc), "vars fetched", len(done), "skipped", len(skipped), "dh", len(dh), "sp", len(sp))


if __name__ == "__main__" and sys.argv[1] == "2":
    stage2(); print(apilib.COUNT)


def stage3():
    """Study records for dhps findings via API (budget), the rest from Dataverse studies.tsv if present."""
    a = json.load(open(os.path.join(WORK, "assoc.json")))["assoc"]
    keep = {k: r for k, r in a.items() if any(is_sp_name(r.get(f)) or is_dhps_name(r.get(f)) for f in ("variable_1_name", "variable_2_name"))}
    dh_st = sorted({r["study_id"] for r in keep.values() if any(is_dhps_name(r.get(f)) for f in ("variable_1_name", "variable_2_name"))})
    out = {}
    for sid, r in zip(dh_st, pmap(lambda s: resp(f"/studies/{s}") if apilib.COUNT["net"] < CAP else None, dh_st)):
        if r: out[sid] = dict(r, _source="api")
    json.dump(out, open(os.path.join(WORK, "studies_api.json"), "w"), indent=1)
    print("studies via api", len(out))


if __name__ == "__main__" and sys.argv[1] == "3":
    stage3(); print(apilib.COUNT)
