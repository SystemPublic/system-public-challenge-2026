#!/usr/bin/env python3
"""Tier 0: anchor NYC leading causes of death to SPG concepts via Wikidata.

Path: NYC icd10Codes -> Wikidata item (P494 = ICD-10) -> SPG concept (wikidata_id).
Joins against the FULL SPG concept set (45,721), not just the 473 domain-tagged ones —
SPG contains canonical items (asthma Q35869, Alzheimer's Q11081, COPD Q199804, ...)
that fall outside the challenge domains.

Verification is code-based. SPARQL hits on wdt:P494 = token are verified by
construction; name-search candidates are verified by fetching their P494 claims.
Batched requests (one SPARQL for all causes), gentle pacing, 429 backoff; every
successful HTTP response cached under mapping/cache/wikidata/.
Run: python3 -I mapping/wikidata_anchors.py
"""
import hashlib
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "mapping" / "out"
CACHE = BASE / "mapping" / "cache" / "wikidata"
CACHE.mkdir(parents=True, exist_ok=True)
UA = "spg-nyc-concept-map/0.1 (local research use)"
SLEEP = 1.2


def http_json(url: str):
    key = hashlib.sha1(url.encode()).hexdigest()[:16]
    path = CACHE / f"{key}.json"
    if path.exists():
        return json.loads(path.read_text())
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.loads(r.read().decode())
            path.write_text(json.dumps(data))
            time.sleep(SLEEP)
            return data
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = max(int(e.headers.get("Retry-After", 0) or 0), 30 * (attempt + 1))
                print(f"  … 429, waiting {wait}s ({url[:60]})", flush=True)
                time.sleep(wait)
                continue
            if attempt == 5:
                print(f"  !! HTTP {e.code}: {url[:90]}", flush=True)
                return None
            time.sleep(5)
        except Exception as e:  # noqa: BLE001
            if attempt == 5:
                print(f"  !! failed: {url[:90]} -> {e}", flush=True)
                return None
            time.sleep(5)


def run_sparql(query: str):
    u = ("https://query.wikidata.org/sparql?query="
         + urllib.parse.quote(query) + "&format=json")
    data = http_json(u)
    out = {}
    if data and "results" in data:
        for b in data["results"]["bindings"]:
            qid = b["item"]["value"].rsplit("/", 1)[-1]
            out[qid] = (b.get("itemLabel", {}).get("value", ""),
                        b.get("val", {}).get("value", ""))
    return out


def search_entities(term: str, limit=6):
    u = ("https://www.wikidata.org/w/api.php?action=wbsearchentities&format=json"
         f"&search={urllib.parse.quote(term)}&language=en&limit={limit}")
    data = http_json(u)
    return [(r["id"], r.get("label", ""), r.get("description", ""))
            for r in (data or {}).get("search", [])]


def p494_batch(qids):
    if not qids:
        return {}
    out = {}
    for i in range(0, len(qids), 50):
        u = ("https://www.wikidata.org/w/api.php?action=wbgetentities&format=json"
             f"&ids={'|'.join(qids[i:i + 50])}&props=claims")
        data = http_json(u)
        for qid, ent in (data or {}).get("entities", {}).items():
            vals = [c["mainsnak"]["datavalue"]["value"]
                    for c in ent.get("claims", {}).get("P494", [])
                    if c.get("mainsnak", {}).get("datavalue", {}).get("value")]
            out[qid] = vals
    return out


def icd_tokens(icd10: str):
    s = re.sub(r"^[A-Za-z ]+:", "", icd10)
    return [t.strip() for t in s.split(",") if re.match(r"^[A-Z]\d", t.strip())]


MANUAL_SEARCH_TERMS = {
    "insitu or benign / uncertain neoplasms": ["benign neoplasm", "in situ neoplasm"],
    "mental and behavioral disorders due to use of alcohol": ["alcoholism"],
    "mental and behavioral disorders due to accidental poisoning and other psychoactive substance use":
        ["drug overdose", "substance abuse"],
    "accidents except drug poisoning": ["unintentional injury", "injury"],
    "essential hypertension and renal diseases": ["hypertensive heart disease", "hypertension"],
    "diseases of heart": ["heart disease", "cardiovascular disease"],
    "certain conditions originating in the perinatal period": ["perinatal disorder"],
    "complications of medical and surgical care": ["adverse effect", "medical error"],
    "assault": ["assault"],
    "intentional self-harm": ["suicide"],
    "cholelithiasis and disorders of gallbladder": ["gallstone"],
    "nephritis, nephrotic syndrome and nephrosis": ["kidney disease", "nephritis"],
    "influenza (flu) and pneumonia": ["influenza", "pneumonia"],
    "malignant neoplasms": ["cancer"],
    "cerebrovascular disease": ["cerebrovascular disease", "stroke"],
    "congenital malformations, deformations, and chromosomal abnormalities":
        ["congenital disorder"],
    "pregnancy, childbirth and the puerperium": ["pregnancy"],
    "septicemia": ["sepsis"],
    "tuberculosis": ["tuberculosis"],
    "viral hepatitis": ["hepatitis"],
    "human immunodeficiency virus disease": ["HIV/AIDS"],
    "parkinson's disease": ["Parkinson's disease"],
    "peptic ulcer": ["peptic ulcer disease"],
    "meningitis": ["meningitis"],
    "anemias": ["anemia"],
    "atherosclerosis": ["atherosclerosis"],
    "aortic aneurysm and dissection": ["aortic aneurysm"],
    "chronic liver disease and cirrhosis": ["cirrhosis"],
    "chronic lower respiratory diseases": ["chronic obstructive pulmonary disease"],
    "diabetes mellitus": ["diabetes mellitus"],
    "alzheimer's disease": ["Alzheimer's disease"],
}


def main():
    nyc = pd.read_csv(OUT / "nyc_concepts.csv")
    spg = pd.read_csv(OUT / "spg_concepts.csv")
    full = pd.read_csv(BASE / "dataverse_files" /
                       "system-public-graph-v1-concepts-1.csv", dtype=str).fillna("")
    dom_ids = set(spg.system_id)
    full_by_qid = {}
    for sid, qid, lab in zip(full.system_id, full.wikidata_id, full.wikidata_label):
        if qid:
            full_by_qid.setdefault(qid, (sid, lab))
    spg_label = dict(zip(spg.system_id, spg.label))

    deaths = nyc[nyc.collection == "leading-causes-of-death"]
    causes = []  # (nyc_id, label, tokens, terms)
    for _, r in deaths.iterrows():
        toks = icd_tokens(r["icd10"])
        key = r["label"].casefold()
        terms = [r["label"]] + MANUAL_SEARCH_TERMS.get(key, [])
        causes.append((r["nyc_id"], r["label"], toks, terms))

    # ---- one SPARQL per match mode for ALL causes -------------------------
    all_tokens = sorted({t for _, _, toks, _ in causes for t in toks})
    starts = sorted({re.match(r"^[A-Z]\d+", t).group(0) for t in all_tokens})
    print(f"{len(causes)} causes, {len(all_tokens)} tokens, {len(starts)} range-starts")

    exact: dict[str, tuple] = {}   # qid -> (label, matched values csv)
    for qid, (lab, val) in run_sparql(
            "SELECT ?item ?itemLabel ?val WHERE { VALUES ?val { "
            + " ".join(f'"{t}"' for t in all_tokens)
            + " } ?item wdt:P494 ?val. SERVICE wikibase:label "
              "{ bd:serviceParam wikibase:language 'en'. } } LIMIT 500").items():
        lab0, v0 = exact.get(qid, ("", ""))
        exact[qid] = (lab or lab0, (v0 + ";" if v0 else "") + val)

    prefixed: dict[str, tuple] = {}
    for qid, (lab, val) in run_sparql(
            "SELECT ?item ?itemLabel ?val WHERE { VALUES ?start { "
            + " ".join(f'"{s}"' for s in starts)
            + " } ?item wdt:P494 ?val. FILTER(STRSTARTS(?val, ?start)) "
              "SERVICE wikibase:label { bd:serviceParam wikibase:language 'en'. } "
              "} LIMIT 500").items():
        lab0, v0 = prefixed.get(qid, ("", ""))
        prefixed[qid] = (lab or lab0, (v0 + ";" if v0 else "") + val)

    print(f"SPARQL: {len(exact)} exact + {len(prefixed)} prefix items")
    sparql_hits = {qid: (lab, val) for qid, (lab, val) in
                   {**prefixed, **exact}.items()}

    anchors, wd_only, unmatched = [], [], []
    search_cache = {}

    for nyc_id, label, toks, terms in causes:
        cands: dict[str, dict] = {}
        for qid, (lab, val) in sparql_hits.items():
            hit = sorted({v for v in val.split(";") for t in toks
                          if v == t or t in v})
            if hit:
                cands[qid] = {"qid": qid, "wd_label": lab, "wd_desc": "",
                              "found": "sparql_p494=" + ";".join(hit),
                              "matched_token": ";".join(hit), "p494_sample": val}

        # name search only if SPARQL produced no SPG hit
        have_spg = any(q in full_by_qid for q in cands)
        if not have_spg:
            for t in terms:
                if t not in search_cache:
                    search_cache[t] = search_entities(t)
                for qid, lab, desc in search_cache[t]:
                    if qid not in cands:
                        cands[qid] = {"qid": qid, "wd_label": lab, "wd_desc": desc,
                                      "found": f"search:{t}", "matched_token": "",
                                      "p494_sample": ""}
            claims = p494_batch([q for q, c in cands.items() if c["found"].startswith("search:")])
            for qid, c in cands.items():
                if qid in claims:
                    vals = claims[qid]
                    hit = sorted({v for v in vals for t in toks if v == t or t in v})
                    c["p494_sample"] = "; ".join(sorted(set(vals))[:8])
                    c["matched_token"] = ";".join(hit)
                    if hit:
                        c["found"] = "claims_p494=" + ";".join(hit)
        verified = [c for c in cands.values() if c["matched_token"]]

        rows = []
        for c in verified:
            sid = full_by_qid.get(c["qid"], ("", ""))[0]
            rows.append({**c, "nyc_id": nyc_id,
                         "spg_system_id": sid,
                         "spg_label": full_by_qid.get(c["qid"], ("", ""))[1],
                         "spg_in_challenge_domains": sid in dom_ids,
                         "method": c["found"].split("=")[0]})
        spg_rows = [r for r in rows if r["spg_system_id"]]
        if spg_rows:
            anchors.extend(spg_rows)
            print(f"= {label}: {len(spg_rows)} SPG-anchored "
                  f"({[r['spg_label'] for r in spg_rows][:4]})")
        elif rows:
            wd_only.extend(rows)
            print(f"~ {label}: {len(rows)} verified on Wikidata, none in SPG")
        else:
            unmatched.append({"nyc_id": nyc_id, "cause": label, "icd10": toks,
                              "terms": terms})
            print(f"? {label}: no verified candidate")

    pd.DataFrame(anchors).to_csv(OUT / "tier0_anchors.csv", index=False)
    pd.DataFrame(wd_only).to_csv(OUT / "tier0_wikidata_only.csv", index=False)
    (OUT / "tier0_unmatched.json").write_text(json.dumps(unmatched, indent=2))
    print(f"\n{len(anchors)} rows anchored to SPG; {len(wd_only)} Wikidata-only; "
          f"{len(unmatched)} causes with nothing verified")


if __name__ == "__main__":
    main()
