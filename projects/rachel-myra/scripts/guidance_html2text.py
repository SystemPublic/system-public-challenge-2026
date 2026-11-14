"""Convert a saved HTML file (untrusted data) to plain text using stdlib only.
Usage: python3 -I scripts/guidance_html2text.py in.html out.txt"""
import sys, html.parser, re

BLOCK = {"p","div","li","tr","h1","h2","h3","h4","h5","h6","br","td","th","table","ul","ol","section","article","caption","dt","dd"}
SKIP = {"script","style","noscript","svg","head"}

class P(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.out=[]; self.skip=0
    def handle_starttag(self, t, a):
        if t in SKIP: self.skip += 1
        if t in BLOCK: self.out.append("\n")
        if t in ("td","th"): self.out.append(" | ")
    def handle_endtag(self, t):
        if t in SKIP and self.skip: self.skip -= 1
        if t in BLOCK: self.out.append("\n")
    def handle_data(self, d):
        if not self.skip: self.out.append(d)

p = P(); p.feed(open(sys.argv[1], encoding="utf-8", errors="replace").read())
txt = "".join(p.out)
txt = re.sub(r"[ \t\xa0]+", " ", txt)
txt = "\n".join(l.strip() for l in txt.splitlines())
txt = re.sub(r"\n{3,}", "\n\n", txt)
open(sys.argv[2], "w", encoding="utf-8").write(txt.strip() + "\n")
