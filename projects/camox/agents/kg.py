"""The project knowledge graph, built in code from a project's stored answers (no model invents a fact).
Entities: graph concepts, World Bank indicators, places, population groups and papers. Edges are statements
("linked to", "measures", "studied in", "reported in") with qualifiers: effect, value, CI, verdict, population, DOI, run.
Model calls only name things: places and populations in a population string, and the project's topics from its goals.
Topics link to graph concepts and indicators found by the tools; thin entities (<=2 studies) get external evidence.
Every node and edge carries data.source (and nodes a data.url)."""
import hashlib
import json
import re
from concurrent.futures import ThreadPoolExecutor

from openai import OpenAI

from agents.harness import MODEL
from tools import graph, literature, worldbank

EXTRACT = {"type": "object", "additionalProperties": False, "required": ["places", "populations"], "properties": {
    "places": {"type": "array", "items": {"type": "object", "additionalProperties": False, "required": ["name", "kind"],
               "properties": {"name": {"type": "string"}, "kind": {"type": "string", "enum": ["country", "region", "city"]}}}},
    "populations": {"type": "array", "items": {"type": "string"}}}}
TOPICS = {"type": "object", "additionalProperties": False, "required": ["topics"], "properties": {"topics": {
    "type": "array", "items": {"type": "object", "additionalProperties": False, "required": ["name", "subtopics"], "properties": {
        "name": {"type": "string"}, "subtopics": {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": ["name", "search_terms"],
            "properties": {"name": {"type": "string"}, "search_terms": {"type": "array", "items": {"type": "string"}}}}}}}}}}
TOPICS_PROMPT = ("List the 2-4 main topics of this research project, from its goals and questions. For each topic give 2-4 "
                 "specific sub-entities a researcher would measure (e.g. topic 'AI': 'early adopters of AI', 'employment in "
                 "AI-exposed industries', 'AI skills'), each with 2-4 search terms: one- or two-word Wikidata-style concept labels "
                 "it is made of ('artificial intelligence', 'automation', 'employment', 'women'). Name things only; state no facts.")
GRAPH, WB, OA = "System Public Graph", "World Bank Data360", "OpenAlex"
PROMPT = ("From this study-population description, list the places studied (countries, regions or cities, in English, "
          "canonical names such as 'Ghana' or 'Sub-Saharan Africa') and the population groups studied as short generic "
          "noun phrases ('school children', 'pregnant women', 'adults'). Leave out groups the text says were not studied. "
          "Use only what the text says; return empty lists if it names none.")


def _ask(instructions, text, schema):
    r = OpenAI().responses.create(model=MODEL, instructions=instructions, input=text[:6000], text={"format": {
        "type": "json_schema", "name": "out", "strict": True, "schema": schema}})
    return json.loads(r.output_text)


def fetch(cache: dict, new: dict, calls: dict):
    """Run the {key: zero-argument function} calls not yet cached, 8 at a time; failures are left uncached."""
    todo = [k for k in calls if k not in cache]

    def one(k):
        try:
            return calls[k]()
        except Exception:
            return None
    with ThreadPoolExecutor(8) as pool:
        for k, v in zip(todo, pool.map(one, todo)):
            if v is not None:
                cache[k] = new[k] = v


def _key(s):
    return re.sub(r"\s+", " ", s.strip().lower())


def _doi(d):
    return re.sub(r"^https?://(dx\.)?doi\.org/", "", (d or "").strip()).lower() or None


def build(runs: list[dict], cache: dict, goals: str = "") -> tuple[list, list, dict]:
    """(nodes, edges, new cache entries) from the project's goals and done runs [{id, query, answer}].
    `cache` holds model extractions and tool results from earlier builds, by key."""
    nodes, edges, new, cache = {}, {}, {}, dict(cache)

    def node(id, kind, label, **data):
        n = nodes.setdefault(id, {"id": id, "kind": kind, "label": label, "data": {"facts": 0, "dois": set(), "runs": set(), **data}})
        if data:
            n["data"].update(data)
        return n

    def fact(source, target, kind, q, src=GRAPH):
        """One statement: the edge (merged per source, target, kind) keeps every qualifier set; both ends embed its DOI."""
        if source == target:
            return
        e = edges.setdefault((source, target, kind), {"source": source, "target": target, "kind": kind,
                                                      "data": {"facts": [], "dois": set(), "source": src}})
        e["data"]["facts"].append({k: v for k, v in q.items() if v not in (None, "", [])})
        for d in [q.get("doi"), *q.get("dois", [])]:
            if _doi(d):
                e["data"]["dois"].add(_doi(d))
                for end in (source, target):
                    nodes[end]["data"]["dois"].add(_doi(d))
        for end in (source, target):
            nodes[end]["data"]["facts"] += 1
            if q.get("run_id"):
                nodes[end]["data"]["runs"].add(q["run_id"])

    # Concepts: labels and graph-wide study counts for every concept id any section rests on
    ids = list(dict.fromkeys(c for r in runs for s in r["answer"]["sections"] for c in s.get("concept_ids", [])))
    pairs = [(f["variable_1"], f["variable_2"]) for r in runs for s in r["answer"]["sections"] if s["type"] == "evidence"
             for c in s["cards"] for f in c["findings"]]
    names = list({n for p in pairs for n in p})
    var_concept = {}
    for row in graph._rows("""SELECT n, c, count(*) k FROM (SELECT variable_1_name n, variable_1_concept_id c FROM associations
                              UNION ALL SELECT variable_2_name, variable_2_concept_id FROM associations)
                              WHERE list_contains($names, n) GROUP BY 1, 2 ORDER BY k""", {"names": names}):
        var_concept[row["n"]] = row["c"]
    ids += [c for c in var_concept.values() if c not in ids]
    sub = graph.subgraph(ids)
    wiki = {r["system_id"]: r["wikidata_id"] for r in graph._rows(
        "SELECT system_id, wikidata_id FROM concepts WHERE list_contains($ids, system_id)", {"ids": ids})}
    for n in sub["nodes"]:
        node(n["id"], "concept", n["label"], n_studies=n["n_studies"], wikidata_id=wiki.get(n["id"]))
    by_label = {_key(n["label"]): n["id"] for n in sub["nodes"]}

    def concept(label):
        """A concept id for a free-text label (policy chains): the graph concept with that label, else a text node."""
        k = _key(label)
        return by_label.get(k) or node(f"text:{k}", "concept", label.strip(), n_studies=None)["id"]

    # Places and populations from the findings' population strings (and the cards' population notes)
    texts = {t for r in runs for s in r["answer"]["sections"] for t in
             ([x for c in s["cards"] for x in [c["populations"]] + [f["population"] for f in c["findings"]]]
              if s["type"] == "evidence" else [l["note"] for l in s["links"]] if s["type"] == "indicator_map" else [])
             if t}
    fetch(cache, new, {t: lambda t=t: _ask(PROMPT, t, EXTRACT) for t in texts})

    def studied_in(concept_ids, population, q):
        got = cache.get(population) or {}
        for p in got.get("places", []):
            pid = f"place:{_key(p['name'])}"
            node(pid, "place", p["name"].strip(), place_kind=p["kind"])
            for c in concept_ids:
                fact(c, pid, "studied in", q)
        for g in got.get("populations", []):
            gid = f"population:{_key(g)}"
            node(gid, "population", g.strip())
            for c in concept_ids:
                fact(c, gid, "studied in", q)

    for r in runs:
        rid, a = r["id"], r["answer"]
        for s in a["sections"]:
            if s["type"] == "evidence":
                for card in s["cards"]:
                    found = [var_concept.get(v) for f in card["findings"] for v in (f["variable_1"], f["variable_2"])]
                    studied_in(list(dict.fromkeys(c for c in found if c)), card["populations"], {
                        "run_id": rid, "claim": card["claim"], "verdict": card["verdict"], "basis": "card population note",
                        "dois": [_doi(f["doi"]) for f in card["findings"] if _doi(f["doi"])]})
                    for f in card["findings"]:
                        c1, c2 = var_concept.get(f["variable_1"]), var_concept.get(f["variable_2"])
                        q = {"run_id": rid, "claim": card["claim"], "verdict": card["verdict"],
                             "variables": [f["variable_1"], f["variable_2"]], "effect": f["stat_type"], "value": f["value"],
                             "ci": [f["ci_lower"], f["ci_upper"]] if f["ci_lower"] is not None else None,
                             "n_studies": (card.get("meter") or {}).get("studies"), "population": f["population"],
                             "doi": _doi(f["doi"])}
                        if c1 and c2:
                            fact(c1, c2, "linked to", q)
                        if f.get("population"):
                            studied_in([c for c in (c1, c2) if c], f["population"], q)
                        if _doi(f["doi"]):
                            pid = f"doi:{_doi(f['doi'])}"
                            node(pid, "paper", _doi(f["doi"]), doi=_doi(f["doi"]))
                            for c in (c1, c2):
                                if c:
                                    fact(c, pid, "reported in", q)
            elif s["type"] == "policy":
                for link in s["links"]:
                    chain = [concept(x) for x in [link["cause"], *link["via"], link["effect"]]]
                    for x, y in zip(chain, chain[1:]):
                        fact(x, y, "linked to", {"run_id": rid, "policy": s["policy"], "support": link["support"],
                                                 "n_studies": link["n_studies"], "note": link["note"],
                                                 "dois": [_doi(d) for d in link["dois"] if _doi(d)]})
            elif s["type"] == "indicator_map":
                def indicator(i):
                    return node(f"ind:{i['indicator_id']}", "indicator", i["name"], indicator_id=i["indicator_id"],
                                database=i["database"])["id"]
                seed = indicator(s["seed"])
                for m in s["matches"]:
                    if m["concept_id"] in nodes:
                        fact(seed, m["concept_id"], "measures", {"run_id": rid, "match": m["match"], "note": m["why"]}, WB)
                for link in s["links"]:
                    if link["concept_id"] not in nodes:
                        node(link["concept_id"], "concept", link["concept_label"], n_studies=None)
                    for m in s["matches"]:
                        if m["concept_id"] in nodes:
                            fact(m["concept_id"], link["concept_id"], "linked to", {
                                "run_id": rid, "n_studies": link["studies"], "note": link["note"],
                                "dois": [_doi(d) for d in link["dois"] if _doi(d)]})
                    studied_in([link["concept_id"]], link["note"], {"run_id": rid, "basis": "indicator link note",
                                                                    "n_studies": link["studies"], "note": link["note"],
                                                                    "dois": [_doi(d) for d in link["dois"] if _doi(d)]})
                    for i in link["indicators"]:
                        fact(indicator(i), link["concept_id"], "measures", {"run_id": rid, "note": f"Indicator for {link['concept_label']}"}, WB)

    # Topics from the goals and questions; each sub-entity links to the graph concepts and indicators the tools find
    context = "Goals: " + goals + "\nQuestions:\n" + "\n".join(r["query"] for r in runs)
    tkey = "topics:" + hashlib.sha1((TOPICS_PROMPT + context).encode()).hexdigest()
    fetch(cache, new, {tkey: lambda: _ask(TOPICS_PROMPT, context, TOPICS)})
    subs = [(t, s) for t in (cache.get(tkey) or {}).get("topics", []) for s in t["subtopics"]]
    fetch(cache, new, {f"wb:{s['name']}": lambda s=s: worldbank.search_worldbank_indicators(s["name"], k=3) for _, s in subs})
    for t, s in subs:
        tid, sid = f"topic:{_key(t['name'])}", f"topic:{_key(t['name'])}/{_key(s['name'])}"
        node(tid, "topic", t["name"], source="Project goals and questions", top=True)
        node(sid, "topic", s["name"], source="Project goals and questions", search_terms=s["search_terms"])
        fact(tid, sid, "includes", {}, "Project goals and questions")
        hits = {}
        for term in s["search_terms"][:4]:   # the concept whose label is the term (or its singular or plural)
            t = _key(term)
            for c in graph.search_concepts(term, k=5):
                if _key(c["label"]) in (t, t + "s", t.removesuffix("s"), t.removesuffix("en") + "an"):
                    hits.setdefault(c["concept_id"], {**c, "term": term})
                    break
        for c in sorted(hits.values(), key=lambda c: -c["n_studies"])[:4]:
            node(c["concept_id"], "concept", c["label"], n_studies=c["n_studies"], wikidata_id=c["wikidata_id"])
            fact(sid, c["concept_id"], "about", {"search_term": c["term"], "n_studies": c["n_studies"]})
        nodes[sid]["data"]["n_studies"] = max([c["n_studies"] for c in hits.values()] + [0])
        for i in cache.get(f"wb:{s['name']}") or []:
            node(f"ind:{i['id']}", "indicator", i["name"], indicator_id=i["id"], database=i["database"])
            fact(sid, f"ind:{i['id']}", "measured by", {"search": s["name"]}, WB)

    # Thin coverage (<=2 studies): top OpenAlex works, and World Bank indicators where none is linked yet
    thin = [n for n in nodes.values() if n["kind"] in ("concept", "topic") and not n["data"].get("top")
            and (n["data"].get("n_studies") or 0) <= 2][:15]
    has_ind = {e["source"] for e in edges.values() if e["kind"] in ("measured by",)} | {e["target"] for e in edges.values() if e["kind"] == "measures"}
    fetch(cache, new, {f"oa:{n['label']}": lambda n=n: literature.search_openalex(n["label"], k=3) for n in thin})
    fetch(cache, new, {f"wb:{n['label']}": lambda n=n: worldbank.search_worldbank_indicators(n["label"], k=2)
                       for n in thin if n["id"] not in has_ind})
    for n in thin:
        n["data"]["thin"] = True
        for w in cache.get(f"oa:{n['label']}") or []:
            d = _doi(w["doi"])
            pid = f"doi:{d}" if d else f"oa:{w['url']}"
            node(pid, "paper", w["title"], title=w["title"], year=w["year"], venue=w["venue"], doi=d, source=OA,
                 url=w["doi"] or w["url"], external=True, cited_by_count=w["cited_by_count"])
            fact(n["id"], pid, "external evidence", {"search": n["label"]}, OA)
        if n["id"] not in has_ind:
            for i in cache.get(f"wb:{n['label']}") or []:
                node(f"ind:{i['id']}", "indicator", i["name"], indicator_id=i["id"], database=i["database"], external=True)
                fact(n["id"], f"ind:{i['id']}", "external evidence", {"search": n["label"]}, WB)

    # Papers: titles from OpenAlex; every DOI an edge cites gets a paper node
    for e in edges.values():
        for d in e["data"]["dois"]:
            node(f"doi:{d}", "paper", d, doi=d)
    dois = [n["data"]["doi"] for n in nodes.values() if n["kind"] == "paper" and not n["data"].get("external")]
    for i in range(0, len(dois), 50):
        try:
            for w in literature.lookup_dois(dois[i:i + 50]):
                n = nodes.get(f"doi:{w['doi'].lower()}")
                if n:
                    n["label"] = w["title"] or n["label"]
                    n["data"].update(title=w["title"], year=w["year"], venue=w["venue"])
        except Exception:
            pass
    for n in nodes.values():
        d = n["data"]
        d["dois"], d["runs"] = sorted(d["dois"]), sorted(d["runs"])
        d["n_papers"] = len(d["dois"])
        if n["kind"] == "indicator":
            d.setdefault("source", WB)
            d.setdefault("url", f"https://data360.worldbank.org/en/indicator/{d['indicator_id']}")
        elif n["kind"] == "paper" and d.get("doi"):
            d.setdefault("url", f"https://doi.org/{d['doi']}")
        elif d.get("wikidata_id"):
            d.setdefault("url", f"https://www.wikidata.org/wiki/{d['wikidata_id']}")
        d.setdefault("source", GRAPH)
    for e in edges.values():
        e["data"]["dois"] = sorted(e["data"]["dois"])
        e["data"]["n_papers"] = len(e["data"]["dois"])
        e["data"]["n_studies"] = max([f.get("n_studies") or 0 for f in e["data"]["facts"]] + [e["data"]["n_papers"]])
    return list(nodes.values()), list(edges.values()), new
