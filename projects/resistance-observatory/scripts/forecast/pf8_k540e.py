"""Build data/forecast/genome-k540e.json (GenomeDataset) from two MalariaGEN Pf8 files.

Counts QC-pass samples by country x collection year at pfdhps codon 540
(Pf8 column "dhps_540[K]").

Usage (from the repo root):
  python3 -I scripts/forecast/pf8_k540e.py \
      <Pf8_drug_resistance_marker_genotypes.tsv> <Pf8_samples.txt> \
      <download time, ISO UTC, e.g. 2026-11-14T16:04:38Z> data/forecast/genome-k540e.json

Source files (not committed):
  https://pf8-release.cog.sanger.ac.uk/Pf8_drug_resistance_marker_genotypes.tsv
  https://pf8-release.cog.sanger.ac.uk/metadata/Pf8_samples.txt
  https://pf8-release.cog.sanger.ac.uk/Pf8_README.txt

Counting rules:
  k_only       every comma-separated haplotype is K (K, K,K)
  e_only       every haplotype is E (E)
  mixed_with_e at least one E haplotype among others (K,E / E,K / E,N / N,E)
  other        usable call, no E, not all K (N, Y, K,N, N,K, K,Y, Y,K): NOT K540E
  missing      "-" or any value containing "*" (or "!"); the Pf8 README says "*" calls
               "are perhaps best considered missing". Not part of `tested`.
"""
import csv
import json
import sys
from collections import Counter, defaultdict

geno_path, meta_path, dl_time, out_json = sys.argv[1:5]

ISO3 = {
    "Bangladesh": "BGD", "Benin": "BEN", "Burkina Faso": "BFA", "Cambodia": "KHM",
    "Cameroon": "CMR", "Colombia": "COL", "Côte d'Ivoire": "CIV",
    "Democratic Republic of the Congo": "COD", "Ethiopia": "ETH", "Gabon": "GAB",
    "Gambia": "GMB", "Ghana": "GHA", "Guinea": "GIN", "Honduras": "HND", "India": "IND",
    "Indonesia": "IDN", "Kenya": "KEN", "Laos": "LAO", "Madagascar": "MDG", "Malawi": "MWI",
    "Mali": "MLI", "Mauritania": "MRT", "Mozambique": "MOZ", "Myanmar": "MMR",
    "Nigeria": "NGA", "Papua New Guinea": "PNG", "Peru": "PER", "Senegal": "SEN",
    "Sudan": "SDN", "Tanzania": "TZA", "Thailand": "THA", "Uganda": "UGA",
    "Venezuela": "VEN", "Vietnam": "VNM",
}
COL = "dhps_540[K]"

LICENCE = ("These data are available open access under the terms of the Creative Commons "
           "Attribution 4.0 International license (CC-BY 4.0). Publications using these data "
           "should acknowledge and cite the source of the data.")
CITATION = ("This publication uses data from MalariaGEN as described in 'Pf8: An open dataset of "
            "Plasmodium falciparum genome variation in 33,325 worldwide samples', MalariaGEN et al., "
            "Wellcome Open Research, 2025; 10: 325 DOI: 10.12688/wellcomeopenres.24031.1")
NOTES = [
    "Samples come from partner studies, not national surveys, so counts are not national prevalence.",
    "A year without samples is not sampled, not zero.",
    "A mixed call that includes E counts as carrying K540E and is shown separately.",
    "Other alleles at codon 540 (for example N or Y) count as tested but not as K540E.",
    "The 9 calls marked with * in the Pf8 file are treated as missing, following the Pf8 README.",
    "Country is where the sample was collected; the year is the collection year.",
]


def bucket(v):
    v = v.strip()
    if v in ("", "-") or "*" in v or "!" in v:
        return "missing"
    alleles = v.split(",")
    if all(a == "K" for a in alleles):
        return "k_only"
    if all(a == "E" for a in alleles):
        return "e_only"
    if "E" in alleles:
        return "mixed_with_e"
    return "other"


meta = {}
with open(meta_path, newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f, delimiter="\t"):
        meta[row["Sample"]] = row

agg = defaultdict(Counter)
n_geno = skipped = 0
with open(geno_path, newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f, delimiter="\t"):
        n_geno += 1
        m = meta.get(row["Sample"])
        if m is None or m["QC pass"] != "True" or not m["Country"].strip() or not m["Year"].strip():
            skipped += 1
            continue
        agg[(m["Country"].strip(), int(float(m["Year"])))][bucket(row[COL])] += 1

by_country = defaultdict(list)
for (country, year), c in sorted(agg.items()):
    tested = c["k_only"] + c["e_only"] + c["mixed_with_e"] + c["other"]
    by_country[country].append({
        "year": year, "tested": tested, "kOnly": c["k_only"], "eOnly": c["e_only"],
        "mixedWithE": c["mixed_with_e"], "withE": c["e_only"] + c["mixed_with_e"],
        "other": c["other"], "missing": c["missing"],
    })

unknown = [c for c in by_country if c not in ISO3]
if unknown:
    sys.exit(f"no ISO3 for: {unknown}")

countries = [{"iso3": ISO3[c], "name": c, "years": ys} for c, ys in sorted(by_country.items(), key=lambda kv: ISO3[kv[0]])]
years = [y["year"] for c in countries for y in c["years"]]
out = {
    "source": {
        "id": "malariagen-pf8", "label": "MalariaGEN Pf8", "licence": LICENCE, "citation": CITATION,
        "url": "https://www.malariagen.net/resource/36/", "retrievedAt": dl_time, "notes": NOTES,
    },
    "minYear": min(years), "maxYear": max(years), "countries": countries,
}
with open(out_json, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print(f"genotype rows {n_geno}, skipped {skipped}, countries {len(countries)}, years {min(years)}-{max(years)}, "
      f"tested+missing {sum(y['tested'] + y['missing'] for c in countries for y in c['years'])}")
