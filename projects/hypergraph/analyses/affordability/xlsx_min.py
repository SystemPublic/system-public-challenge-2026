"""Minimal .xlsx reader (standard library only): sheet names and rows of cell values."""
import re, zipfile
import xml.etree.ElementTree as ET
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}

def _col(ref):
    n = 0
    for ch in re.match(r"[A-Z]+", ref).group(0):
        n = n * 26 + ord(ch) - 64
    return n - 1

def sheets(path):
    z = zipfile.ZipFile(path)
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    rid = {r.get("Id"): r.get("Target") for r in rels}
    out = []
    for s in wb.find("m:sheets", NS):
        t = rid[s.get("{%s}id" % NS["r"])]
        out.append((s.get("name"), "xl/" + t.lstrip("/").replace("xl/", "")))
    return out

def rows(path, sheet):
    z = zipfile.ZipFile(path)
    ss = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")):
            ss.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])))
    target = dict(sheets(path))[sheet]
    with z.open(target) as f:
        for _, el in ET.iterparse(f):
            if el.tag != "{%s}row" % NS["m"]:
                continue
            vals = []
            for c in el:
                i = _col(c.get("r"))
                while len(vals) < i:
                    vals.append(None)
                v = c.find("m:v", NS); t = c.get("t")
                if t == "inlineStr":
                    x = "".join(tt.text or "" for tt in c.iter("{%s}t" % NS["m"]))
                elif v is None:
                    x = None
                elif t == "s":
                    x = ss[int(v.text)]
                elif t in ("str", "b", "e"):
                    x = v.text
                else:
                    try: x = float(v.text)
                    except ValueError: x = v.text
                vals.append(x)
            yield vals
            el.clear()
