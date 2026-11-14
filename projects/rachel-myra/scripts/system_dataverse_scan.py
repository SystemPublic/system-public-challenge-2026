"""One streaming pass over the System Public Graph Dataverse associations CSV (v2.1).

Usage:
  uv run python scripts/system_dataverse_scan.py ASSOCIATIONS_CSV OUT_DIR MASTER_CSV [MASTER_CSV ...]

Writes to OUT_DIR:
  assoc_relevant.csv   every association where either variable name matches a
                       mediator term or a heat term (system_terms.MEDIATORS / HEAT),
                       or either name matches an in-scope/comparator drug term,
                       with the matched groups for each side as extra columns
  assoc_master_pmids.csv  every association whose pubmed_id is cited in the master lists
  master_pmids.csv     the PMIDs (and DOIs) extracted from the master lists

Matching is on free-text variable names (concept grounding is incomplete).
The file is untrusted data: it is only parsed with the csv module.
"""
import csv, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import system_terms as T

csv.field_size_limit(10**8)


def master_ids(paths):
    """Extract PMIDs and DOIs from the master-list CSVs (any column)."""
    pmids, dois = {}, {}
    for p in paths:
        with open(p, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                rid = row.get("row_id") or row.get("ID") or ""
                drug = row.get("drug_or_class") or row.get("Drug or class") or ""
                if row.get("pmid"):
                    for m in re.findall(r"\d{5,9}", row["pmid"]):
                        pmids.setdefault(m, set()).add((rid, drug, os.path.basename(p)))
                text = " ".join(v for v in row.values() if isinstance(v, str))
                for m in re.findall(r"PMIDs?\s*:?\s*((?:\d{5,9}(?:\s*(?:,|and|;)\s*)?)+)", text):
                    for n in re.findall(r"\d{5,9}", m):
                        pmids.setdefault(n, set()).add((rid, drug, os.path.basename(p)))
                for m in re.findall(r"10\.\d{4,9}/[^\s;,\)\]]+", text):
                    dois.setdefault(m.rstrip(".").lower(), set()).add((rid, drug, os.path.basename(p)))
    return pmids, dois


def main(assoc_path, out_dir, masters):
    os.makedirs(out_dir, exist_ok=True)
    pmids, dois = master_ids(masters)
    with open(os.path.join(out_dir, "master_pmids.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id_type", "id", "master_rows"])
        for k, v in sorted(pmids.items()):
            w.writerow(["pmid", k, " | ".join(sorted(f"{a}:{b} ({c})" for a, b, c in v))])
        for k, v in sorted(dois.items()):
            w.writerow(["doi", k, " | ".join(sorted(f"{a}:{b} ({c})" for a, b, c in v))])
    print(f"master list: {len(pmids)} PMIDs, {len(dois)} DOIs")

    drugs = {**T.DRUGS15, **T.COMPARATORS}
    C = {"drug": T.compile_groups(drugs), "med": T.compile_groups(T.MEDIATORS), "heat": T.compile_groups(T.HEAT)}
    pre = T.any_re({**drugs, **T.MEDIATORS, **T.HEAT})

    f_in = open(assoc_path, encoding="utf-8", newline="")
    r = csv.reader(f_in)
    header = next(r)
    i1, i2, ip = header.index("variable_1_name"), header.index("variable_2_name"), header.index("pubmed_id")
    extra = ["v1_drug", "v1_mediator", "v1_heat", "v2_drug", "v2_mediator", "v2_heat"]
    fo = open(os.path.join(out_dir, "assoc_relevant.csv"), "w", newline="", encoding="utf-8")
    fm = open(os.path.join(out_dir, "assoc_master_pmids.csv"), "w", newline="", encoding="utf-8")
    wo, wm = csv.writer(fo), csv.writer(fm)
    wo.writerow(header + extra)
    wm.writerow(header)
    n = kept = km = 0
    for row in r:
        n += 1
        if row[ip] in pmids:
            wm.writerow(row); km += 1
        a, b = row[i1], row[i2]
        if not (pre.search(a) or pre.search(b)):
            continue
        ma = [T.match_groups(a, C[k]) for k in ("drug", "med", "heat")]
        mb = [T.match_groups(b, C[k]) for k in ("drug", "med", "heat")]
        if any(ma) or any(mb):
            wo.writerow(row + [";".join(x) for x in ma + mb]); kept += 1
        if n % 500_000 == 0:
            print(f"  {n:,} rows scanned, {kept:,} kept", flush=True)
    fo.close(); fm.close()
    print(f"done: {n:,} associations scanned; {kept:,} relevant; {km:,} from master-list PMIDs")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
