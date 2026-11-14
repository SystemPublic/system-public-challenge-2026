"""Task 4: direct drug x heat count via the System API (copy of scripts/graph_check.py `api` mode).

Same logic as graph_check.py run_api() (13 Nov run): find each heat-outcome concept by label, pull ALL of its
concept-to-concept relationships, keep those whose other end's label matches a graph_check drug group,
and sum num_findings / num_studies. Differences from the original:
  - uses the cached, rate-limited client (scripts/system_api_client.py); aliases dropped before caching
  - writes NEW files only:
      data/processed/system_api_graph_coverage.csv           (instead of data/graph_coverage.csv)
      data/processed/system_api_graph_heat_relationships.csv  (instead of data/graph_heat_relationships.csv)
  - records which concept each label resolved to.
The original script and its outputs are not touched.
Run:  uv run --with requests python scripts/system_api_graph_check.py
"""
import csv, os, sys

sys.path.insert(0, os.path.dirname(__file__))
from graph_check import DRUGS, DRUG_RE, HEAT_CORE  # noqa: E402
from system_api_client import Client  # noqa: E402
from system_api_common import PROC  # noqa: E402

HEAT_CONCEPTS = {  # identical to graph_check.run_api
    "heat illness/stroke": ["heat stroke", "heat illness", "heat exhaustion", "heat-related illness", "hot"],
    "hyperthermia/body temp": ["hyperthermia", "body temperature", "thermoregulation", "fever"],
    "ambient heat/heat wave": ["heat wave", "ambient temperature", "extreme heat", "temperature"],
    "sweating": ["sweating", "anhidrosis", "hypohidrosis", "hyperhidrosis"],
    "dehydration/volume": ["dehydration", "hypovolemia"],
    "hyponatremia": ["hyponatremia"],
    "acute kidney injury": ["acute kidney injury"],
}


def main():
    c = Client()
    out_rows, seen, resolved = [], set(), []
    for outcome, labels in HEAT_CONCEPTS.items():
        for label in labels:
            hits = (c.get("/concepts", search=f"wikidata_label:{label}", limit=5) or {}).get("data", [])
            exact = [h for h in hits if (h.get("wikidata_label") or "").lower() == label]
            hits = exact or hits[:1]
            for h in hits:
                resolved.append((outcome, label, h["system_id"], h.get("wikidata_label"), bool(exact)))
                rels = c.paged(f"/concepts/{h['system_id']}/relationships", page=1000, cap=20000, drop_keys=("wikidata_aliases",))
                for rel in rels:
                    other = rel["target_concept"] if rel["source_concept"]["system_id"] == h["system_id"] else rel["source_concept"]
                    text_label = other.get("wikidata_label") or ""
                    for drug, dre in DRUG_RE.items():
                        if dre.search(text_label):
                            key = (rel["relationship_id"], drug, outcome)
                            if key in seen:
                                continue
                            seen.add(key)
                            out_rows.append([drug, outcome, h.get("wikidata_label"), text_label,
                                             f"{rel['source_concept'].get('wikidata_label')} -> {rel['target_concept'].get('wikidata_label')}",
                                             rel.get("num_findings") or 0, rel.get("num_studies") or 0,
                                             rel.get("last_published_date"), rel["relationship_id"]])
                print(f"{outcome:24s} {h.get('wikidata_label')!r}: {len(rels)} relationships ({c.stats()})")
    with open(os.path.join(PROC, "system_api_graph_heat_relationships.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["drug_group", "outcome_group", "heat_concept", "drug_concept", "relationship", "num_findings",
                    "num_studies", "last_published_date", "relationship_id"])
        w.writerows(sorted(out_rows, key=lambda r: (r[0], r[1], -r[6])))
    with open(os.path.join(PROC, "system_api_graph_coverage.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["drug", "outcome", "heat_core_outcome", "relationships", "findings", "studies_summed"])
        for drug in DRUGS:
            for out in HEAT_CONCEPTS:
                rs = [r for r in out_rows if r[0] == drug and r[1] == out]
                w.writerow([drug, out, out in HEAT_CORE, len(rs), sum(r[5] for r in rs), sum(r[6] for r in rs)])
    with open(os.path.join(PROC, "system_api_graph_check_concepts.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["outcome_group", "search_label", "concept_id", "concept_label", "exact_label_match"])
        w.writerows(resolved)
    tot = sum(r[5] for r in out_rows if r[1] in HEAT_CORE)
    print(f"\nDrug x core-heat concept-edge findings: {tot} in {sum(1 for r in out_rows if r[1] in HEAT_CORE)} relationships")
    for drug in DRUGS:
        core = [r for r in out_rows if r[0] == drug and r[1] in HEAT_CORE]
        other = [r for r in out_rows if r[0] == drug and r[1] not in HEAT_CORE]
        print(f"  {drug:24s} core-heat findings {sum(r[5] for r in core):5d} (rels {len(core):3d}) | dehydration/Na/AKI findings {sum(r[5] for r in other):5d}")
    print(c.stats())


if __name__ == "__main__":
    main()
