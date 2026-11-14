"""Stream-filter the System Public Graph relationships table (Dataverse v2.1) without saving it.

Usage:
  uv run python scripts/system_relationships_filter.py OUT_CSV [SOURCE]

SOURCE is a local path or a URL; default is the Dataverse file id 14061025
(system-public-graph-v1-relationships.csv, 394 MB). The table is read as a
stream and only edges where the source or target concept LABEL matches a
drug (in-scope or comparator), mediator or heat term from system_terms.py are
written, with match columns appended. Keeping only the subset saves ~400 MB of
disk. Downloaded content is treated as data (csv module only).
"""
import csv, io, os, sys, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import system_terms as T

csv.field_size_limit(10**8)
DEFAULT = "https://dataverse.harvard.edu/api/access/datafile/14061025"


def open_source(src):
    if src.startswith("http"):
        req = urllib.request.Request(src, headers={"User-Agent": "research-data-client/1.0"})
        return io.TextIOWrapper(urllib.request.urlopen(req, timeout=120), encoding="utf-8", newline="")
    return open(src, encoding="utf-8", newline="")


def main(out_csv, src=DEFAULT):
    drugs = {**T.DRUGS15, **T.COMPARATORS}
    C = {"drug": T.compile_groups(drugs), "med": T.compile_groups(T.MEDIATORS), "heat": T.compile_groups(T.HEAT)}
    r = csv.reader(open_source(src))
    header = next(r)
    isl, itl = header.index("source_concept.wikidata_label"), header.index("target_concept.wikidata_label")
    extra = ["src_drug", "src_mediator", "src_heat", "tgt_drug", "tgt_mediator", "tgt_heat"]
    n = kept = 0
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header + extra)
        for row in r:
            n += 1
            ms = [T.match_groups(row[isl], C[k]) for k in ("drug", "med", "heat")]
            mt = [T.match_groups(row[itl], C[k]) for k in ("drug", "med", "heat")]
            if any(ms) or any(mt):
                w.writerow(row + [";".join(x) for x in ms + mt]); kept += 1
            if n % 200_000 == 0:
                print(f"  {n:,} edges read, {kept:,} kept", flush=True)
    print(f"done: {n:,} relationships read, {kept:,} kept -> {out_csv}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(*sys.argv[1:3])
