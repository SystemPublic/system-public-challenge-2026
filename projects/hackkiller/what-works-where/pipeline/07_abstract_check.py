"""Pre-check review-queue rows against paper abstracts (Europe PMC).

For each priority 1-2 row, look for the extracted estimate and both CI bounds in the abstract and
keep the sentence that contains them as a source quote. A match means "the number exists in the
abstract"; it does NOT confirm that the graph bound it to the right arm, comparator or time point.
"""
from __future__ import annotations

import json
import re
import time

import pandas as pd
import requests

from common import DATA, log_request

EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
Q = DATA / "review" / "review_queue.csv"
ABS = DATA / "review" / "abstracts.json"
# priority-3 papers pulled in for C2 (ITN -> under-5 / child mortality)
EXTRA_PMIDS = {"17889242", "34051817", "28990922", "27146674", "24052575", "29402245"}


def fetch_abstracts(pmids: list[str]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for i in range(0, len(pmids), 20):
        batch = pmids[i:i + 20]
        query = "(" + " OR ".join(f"EXT_ID:{p}" for p in batch) + ") AND SRC:MED"
        params = {"query": query, "resultType": "core", "format": "json", "pageSize": 100}
        r = requests.get(EPMC, params=params, timeout=60)
        log_request("europepmc", EPMC, {"n_ids": len(batch)}, r.status_code, None)
        r.raise_for_status()
        for res in r.json().get("resultList", {}).get("result", []):
            out[res.get("pmid")] = {"abstract": res.get("abstractText") or "", "title": res.get("title"),
                                    "pmcid": res.get("pmcid"), "is_open_access": res.get("isOpenAccess")}
        time.sleep(0.3)
    return out


def variants(x: str) -> list[str]:
    """String forms a number may take in an abstract: 0.70 / 0.7 / .70 / 0·70."""
    x = (x or "").strip()
    if not x:
        return []
    try:
        f = float(x)
    except ValueError:
        return [x]
    forms = {x, f"{f:g}", f"{f:.2f}", f"{f:.1f}" if abs(f) >= 1 else f"{f:.2f}", f"{f:.3f}"}
    forms |= {s.lstrip("0") for s in list(forms) if s.startswith("0.")}
    return sorted(forms, key=len, reverse=True)


def find(num: str, text: str) -> bool:
    return any(re.search(rf"(?<![\d.]){re.escape(v)}(?![\d])", text) for v in variants(num))


def main() -> None:
    q = pd.read_csv(Q, dtype=str, keep_default_na=False)
    raw = pd.read_csv(DATA / "interim" / "candidates.csv", dtype=str, keep_default_na=False)
    raw = raw.set_index("system_id")[["statistic_value", "ci_lower", "ci_upper"]]
    q.loc[q.pubmed_id.isin(EXTRA_PMIDS) & (q.review_priority == "3"), "review_priority"] = "2"
    target = q[q.review_priority.isin(["1", "2"])]
    pmids = sorted(set(target.pubmed_id))
    abstracts = fetch_abstracts(pmids)
    ABS.write_text(json.dumps(abstracts, indent=1, ensure_ascii=False))

    found_v, found_ci, quotes = [], [], []
    for _, r in q.iterrows():
        if r.review_priority not in ("1", "2"):
            found_v.append(""); found_ci.append(""); quotes.append("")
            continue
        text = (abstracts.get(r.pubmed_id, {}).get("abstract") or "").replace("·", ".").replace(" ", " ")
        v, lo, hi = raw.loc[r.system_id] if r.system_id in raw.index else (r.statistic_value, r.ci_lower, r.ci_upper)
        if not text:
            found_v.append("no abstract"); found_ci.append(""); quotes.append("")
            continue
        fv = find(v, text)
        fci = bool(lo and hi and find(lo, text) and find(hi, text))
        quote = ""
        if fv:
            for sent in re.split(r"(?<=[.;])\s+(?=[A-Z(])", text):
                if find(v, sent):
                    quote = sent.strip()[:400]
                    break
        found_v.append("yes" if fv else "no"); found_ci.append("yes" if fci else ("no" if lo else "n/a"))
        quotes.append(quote)
    q.insert(q.columns.get_loc("qc_flags") + 1, "abstract_value_found", found_v)
    q.insert(q.columns.get_loc("abstract_value_found") + 1, "abstract_ci_found", found_ci)
    q.insert(q.columns.get_loc("abstract_ci_found") + 1, "abstract_quote", quotes)
    q.to_csv(Q, index=False)
    t = q[q.review_priority.isin(["1", "2"])]
    print("abstracts fetched:", len(abstracts), "of", len(pmids))
    print(t.groupby(["review_priority", "abstract_value_found"]).size().to_string())
    print("value+CI both found:", int(((t.abstract_value_found == "yes") & (t.abstract_ci_found == "yes")).sum()),
          "of", len(t))


if __name__ == "__main__":
    main()
