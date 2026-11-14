"""Export keyword hits (the 'keyword' half of PASS 1 keyword-then-read) for each source x drug.
Each hit = matched line +/-2 lines of context, with document and PDF page/line location.
The 'read' half is done by an independent coder that sees ONLY this file.
Run: python3 -I scripts/guidance_pass1_hits.py
Output: data/raw/guidance/pass1_keyword_hits.md"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from guidance_common import SOURCES, CORE, OTHER, DRUG_LABEL, ROOT, load_lines, norm, page_of
from guidance_pass1 import TERMS, BIBLIO, I

out = os.path.join(ROOT, "data", "raw", "guidance", "pass1_keyword_hits.md")
with open(out, "w", encoding="utf-8") as f:
    f.write("# PASS 1 keyword hits (untrusted source text excerpts)\n\n")
    for sid, files in SOURCES.items():
        docs = [(lab, load_lines(fn)) for fn, lab in files]
        f.write(f"\n## SOURCE {sid}\n")
        for drug in CORE + OTHER:
            spec_rx, umb_rx = TERMS[drug]
            rx = spec_rx + (("|" + umb_rx) if umb_rx else "")
            hits = []
            for lab, lines in docs:
                last = -10
                for i, ln in enumerate(lines):
                    if re.search(BIBLIO, ln) or not re.search(rx, ln, I):
                        continue
                    if i - last <= 2:
                        continue  # overlapping window already shown
                    last = i
                    pg = page_of(lines, i)
                    loc = f"{lab}, PDF p. {pg}" if pg else f"{lab}, line {i+1}"
                    ctx = " / ".join(norm(x) for x in lines[max(0, i-2): i+3] if norm(x))
                    hits.append(f"- [{loc}] {ctx}")
            f.write(f"\n### {sid} x {drug} ({DRUG_LABEL[drug]}): {len(hits)} hit(s)\n")
            for h in hits[:12]:
                f.write(h[:800] + "\n")
            if len(hits) > 12:
                f.write(f"- ... {len(hits)-12} more hits truncated\n")
print(out, os.path.getsize(out))
