"""Extract text from untrusted PDFs with pypdf, writing per-page markers.
Usage: uv run --with pypdf python -I scripts/guidance_pdf2text.py in.pdf out.txt"""
import sys
from pypdf import PdfReader
r = PdfReader(sys.argv[1])
with open(sys.argv[2], "w", encoding="utf-8") as f:
    for i, pg in enumerate(r.pages, 1):
        f.write(f"\n=== [page {i}] ===\n")
        f.write((pg.extract_text() or "") + "\n")
print(sys.argv[1], len(r.pages), "pages")
