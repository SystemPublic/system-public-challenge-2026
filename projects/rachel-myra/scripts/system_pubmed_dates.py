"""Fetch publication date, title and journal for PMIDs via NCBI E-utilities esummary.

The Dataverse studies table has no publication date, so we look dates up in PubMed.

Usage:
  uv run python scripts/system_pubmed_dates.py OUT_CSV PMID_LIST_FILE

PMID_LIST_FILE: one PMID per line. Results are cached: PMIDs already in OUT_CSV
are skipped, so the script can be re-run. Batches of 200, ~3 requests/second max
(no API key), with retry and backoff.
"""
import csv, json, os, sys, time, urllib.parse, urllib.request

URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"


def fetch(batch):
    data = urllib.parse.urlencode({"db": "pubmed", "id": ",".join(batch), "retmode": "json",
                                   "tool": "research-data-client"}).encode()
    for attempt in range(5):
        try:
            req = urllib.request.Request(URL, data=data, headers={"User-Agent": "research-data-client/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))["result"]
        except Exception as e:  # noqa: BLE001 - network retry
            wait = 2 ** attempt * 2
            print(f"  retry {attempt + 1} after error {e!r}; sleeping {wait}s", flush=True)
            time.sleep(wait)
    return {}


def main(out_csv, list_file):
    want = [l.strip() for l in open(list_file) if l.strip().isdigit()]
    have = set()
    if os.path.exists(out_csv):
        with open(out_csv, encoding="utf-8") as f:
            have = {r["pmid"] for r in csv.DictReader(f)}
    todo = sorted(set(want) - have)
    print(f"{len(want)} PMIDs requested, {len(have)} cached, {len(todo)} to fetch")
    new = not os.path.exists(out_csv)
    with open(out_csv, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["pmid", "pubdate", "sortpubdate", "pub_year", "title", "journal"])
        for i in range(0, len(todo), 200):
            batch = todo[i:i + 200]
            res = fetch(batch)
            for p in batch:
                d = res.get(p) or {}
                sp = d.get("sortpubdate", "")
                w.writerow([p, d.get("pubdate", ""), sp, sp[:4], d.get("title", ""), d.get("fulljournalname", "")])
            f.flush()
            time.sleep(0.4)
            print(f"  {min(i + 200, len(todo))}/{len(todo)}", flush=True)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
