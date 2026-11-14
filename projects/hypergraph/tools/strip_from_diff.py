"""Draw strips from the difference between two versions of an Underlay collection.

Usage:
  ~/.venvs/nyc-concordance/bin/python tools/strip_from_diff.py [--owner system-community]
      [--slug nyc-concordance-claims] [--from v1.0.0] [--to v1.1.0]

Reads GET /api/collections/<owner>/<slug>/versions/<to>/diff?from=<from> (public, no key), groups the changed
Claim, Outcome and Revision records by claim, and writes viz/data/comics_generated.js, which viz/comics.html
loads after comics.js. Each subject becomes one strip:

  frame 1  the edge as the earlier version holds it (an Outcome named as 'context', read from that version)
  frame 2  what the later version adds (yellow) or withdraws (red: a verdict that left 'confirmed')
  frame 3  a Revision record added in the later version, with the interval before and after
A 'compare' entry in strip_nodes.json adds the same test in another place, read from the earlier version, to frame 2.

Numbers, verdicts, dates and revision reasons come from the records. The two node names of an edge do not: the
collection has no exposure field, so viz/data/strip_nodes.json supplies them. Captions are filled from templates
and are not edited by hand.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[1]
API = "https://www.underlay.org/api"
NODES = json.loads((ROOT / "viz" / "data" / "strip_nodes.json").read_text())


def num(x: float) -> str:
    return f"{x:.2f}"


def eff(e: dict | None) -> dict | None:
    if not e or e.get("estimate") is None:
        return None
    lo, hi, est, null = e.get("lo"), e.get("hi"), e["estimate"], e.get("null", 1)
    se = (math.log(hi) - math.log(lo)) / 3.92 if lo and hi and null == 1 else None
    return {"est": est, "lo": lo, "hi": hi, "null": null, "se": se,
            "nulled": lo is not None and hi is not None and lo <= null <= hi}


def width(e: dict) -> int:
    if e["se"] is None:
        return 2
    return 3 if e["se"] < 0.012 else 2 if e["se"] < 0.04 else 1


def interval(e: dict) -> str:
    return f"{num(e['est'])} ({num(e['lo'])} to {num(e['hi'])})"


def get_record(base: str, semver: str, rtype: str, rid: str) -> dict | None:
    r = requests.get(f"{base}/versions/{semver}/records/{rtype}/{quote(rid, safe='')}", timeout=60)
    return r.json() if r.status_code == 200 else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--owner", default="system-community")
    ap.add_argument("--slug", default="nyc-concordance-claims")
    ap.add_argument("--from", dest="frm", default="v1.0.0")
    ap.add_argument("--to", default="v1.1.0")
    ap.add_argument("--keep", action="store_true", help="keep strips already generated from other version pairs")
    a = ap.parse_args()
    base = f"{API}/collections/{a.owner}/{a.slug}"
    d, cursor, recs = None, None, {"added": [], "updated": [], "removed": []}
    while True:
        d = requests.get(f"{base}/versions/{a.to}/diff", params={"from": a.frm, "limit": 500, **({"cursor": cursor} if cursor else {})}, timeout=120).json()
        for k in recs:
            recs[k] += d[k]
        if not d["pagination"]["hasMore"]:
            break
        cursor = d["pagination"]["nextCursor"]
    vfrom = requests.get(f"{base}/versions/{a.frm}", timeout=60).json()
    vto = requests.get(f"{base}/versions/{a.to}", timeout=60).json()
    by = {}
    for change in ("added", "updated"):
        for r in recs[change]:
            cid = r["data"].get("claim", r["id"]) if r["type"] != "Claim" else r["id"]
            by.setdefault(cid, {})[r["type"]] = {"change": change, **r}
    url = f"https://www.underlay.org/{a.owner}/{a.slug}/versions/compare?from={a.frm}&to={a.to}"
    subjects: dict[str, list[str]] = {}
    for cid in by:
        m = NODES.get(cid)
        if m and "twin_of" not in m:
            subjects.setdefault(m["subject"], []).append(cid)
    strips = []
    for subject, cids in sorted(subjects.items()):
        for cid in cids:
            m, g = NODES[cid], by[cid]
            out, claim, rev = g.get("Outcome"), g.get("Claim"), g.get("Revision")
            e = eff(out["data"].get("city_effect")) if out else None
            if not e:
                continue
            twins = [t for t, tm in NODES.items() if isinstance(tm, dict) and tm.get("twin_of") == cid and t in by]
            ctx = get_record(base, a.frm, "Outcome", m["context"]) if m.get("context") else None
            ce = eff(ctx["data"].get("city_effect")) if ctx else None
            place = m.get("place", "New York")
            A = {"id": "A", "label": m["a"], "x": 70, "y": 150}
            B = {"id": "B", "label": m["b"], "x": 326, "y": 150}
            verdict = out["data"]["verdict"]
            withdrawn = rev and rev["data"].get("verdict_changed") and rev["data"].get("verdict_before") == "confirmed"
            state = "gone" if withdrawn else "new"
            reg = (claim["data"].get("registered_at") or "")[:10] if claim else ""
            frames = []
            # frame 1: the earlier version
            if ce:
                A1, B1 = dict(A, y=120), dict(B, y=120)
                frames.append({"head": f"Version {a.frm[1:]}", "nodes": [A1, B1],
                               "edges": [{"id": "ab", "a": "A", "b": "B", "ev": "obs", "w": width(ce), "city": True, "label": "×" + num(ce["est"]), "refs": [1], "lo": -14}],
                               "cap": f"Version {a.frm[1:]} of the collection holds {vfrom.get('recordCount')} records. On this edge it has claim {m['context']}: {interval(ce)}, {ctx['data']['verdict']}."})
            else:
                frames.append({"head": f"Version {a.frm[1:]}", "nodes": [A, B], "edges": [],
                               "texts": [{"text": "no record\non this edge", "x": 198, "y": 150, "size": 13}],
                               "cap": f"Version {a.frm[1:]} of the collection holds {vfrom.get('recordCount')} records. It has no claim on this edge."})
            # frame 2: what the later version adds
            lab = "×" + num(e["est"])
            twin_txt = ""
            for t in twins:
                te = eff(by[t]["Outcome"]["data"].get("city_effect")) if "Outcome" in by[t] else None
                if te:
                    twin_txt = f" Claim {t} repeats it on another window: {interval(te)}."
            cap2 = f"Version {a.to[1:]} adds claim {cid}, registered on {reg} and scored {verdict}: {interval(e)}.{twin_txt}"
            if m.get("compare"):
                cmp_rec = get_record(base, a.frm, "Outcome", m["compare"])
                cmp_e = eff(cmp_rec["data"].get("city_effect")) if cmp_rec else None
                if cmp_e:
                    cap2 += f" In {m.get('compare_place', 'the other city')}, claim {m['compare']} gave {interval(cmp_e)}."
            if ce and m.get("modifies"):
                A2, B2 = dict(A, y=96), dict(B, y=96)
                M = {"id": "M", "label": m["node"], "x": 198, "y": 236, "state": state}
                f2 = {"head": f"Version {a.to[1:]} adds", "nodes": [A2, B2, M],
                      "edges": [{"id": "ab", "a": "A", "b": "B", "ev": "obs", "w": width(ce), "city": True, "label": "×" + num(ce["est"]), "lo": -14}],
                      "mods": [{"from": "M", "onto": "ab", "ev": "obs", "w": width(e), "state": state, "city": True, "label": lab, "refs": [2], "lx": 40, "ly": 0,
                                **({"mark": "x"} if withdrawn else {})}], "cap": cap2}
            else:
                edge = {"a": "A", "b": "B", "ev": "obs", "w": width(e), "state": state, "city": True, "label": lab, "refs": [2], "lo": -14, "labelT": 0.36}
                if withdrawn:
                    edge["mark"] = "x"
                elif e["nulled"]:
                    edge.update(mark="0", markT=0.7)
                f2 = {"head": f"Version {a.to[1:]} adds", "nodes": [A, B], "edges": [edge], "cap": cap2}
            frames.append(f2)
            # frame 3: a revision in the same difference
            if rev:
                be = eff(rev["data"].get("before", {}).get("city_effect"))
                f3 = json.loads(json.dumps(f2))
                f3["head"] = "A revision"
                for part in f3.get("edges", []) + f3.get("mods", []):
                    if part.get("state"):
                        part["state"] = "kept" if not withdrawn else "gone"
                for n in f3["nodes"]:
                    n.pop("state", None)
                if be and (abs(be["lo"] - e["lo"]) > 0.0005 or abs(be["hi"] - e["hi"]) > 0.0005):
                    y = 277 if (ce and m.get("modifies")) else 214
                    n3 = (lambda x: f"{x:.3f}") if (num(be["lo"]), num(be["hi"])) == (num(e["lo"]), num(e["hi"])) else num
                    f3["texts"] = [{"text": f"interval {n3(be['lo'])} to {n3(be['hi'])}, now {n3(e['lo'])} to {n3(e['hi'])}", "x": 198, "y": y, "state": "new", "size": 12.5, "refs": [3]}]
                f3["cap"] = f"The same version holds a revision record. <b>{rev['data']['reason']}</b>"
                frames.append(f3)
            sources = []
            if ce:
                sources.append({"text": f"Outcome {m['context']} in {a.owner}/{a.slug} {a.frm}.", "href": f"https://www.underlay.org/api/collections/{a.owner}/{a.slug}/versions/{a.frm}/records/Outcome/{m['context']}", "link": "record"})
            else:
                sources.append({"text": f"{a.owner}/{a.slug} {a.frm}, {vfrom.get('recordCount')} records.", "href": f"https://www.underlay.org/{a.owner}/{a.slug}/versions", "link": "versions"})
            sources.append({"text": f"Outcome {cid} in {a.to}, added in this difference. Registration sha256 {out['data'].get('registration_sha256', '')[:12]}.", "href": f"https://www.underlay.org/api/collections/{a.owner}/{a.slug}/versions/{a.to}/records/Outcome/{cid}", "link": "record"})
            if rev:
                sources.append({"text": f"Revision {rev['id']} in {a.to}: {rev['data'].get('critique', '')}.", "href": f"https://www.underlay.org/api/collections/{a.owner}/{a.slug}/versions/{a.to}/records/Revision/{quote(rev['id'], safe='')}", "link": "record"})
            strips.append({"id": f"diff-{cid}", "generated": True, "pair": f"{a.frm}..{a.to}", "title": f"Generated from the Underlay: {m['a'].replace(chr(10), ' ')} and {m['b'].replace(chr(10), ' ')}, {a.frm} to {a.to}" + (f" ({place})" if m.get("place") else ""),
                           "lede": f"Drawn by tools/strip_from_diff.py from the difference between two versions of {a.owner}/{a.slug}: {len(recs['added'])} records added, {len(recs['updated'])} updated, {len(recs['removed'])} removed. Numbers, verdicts and the revision reason are read from the records; only the two variable names are supplied by hand. The same difference on the Underlay: {url}",
                           "sources": sources, "frames": frames})
    out = ROOT / "viz" / "data" / "comics_generated.js"
    meta = {"owner": a.owner, "slug": a.slug, "from": a.frm, "to": a.to, "from_hash": vfrom.get("hash"), "to_hash": vto.get("hash"),
            "added": len(recs["added"]), "updated": len(recs["updated"]), "removed": len(recs["removed"]), "compare": url}
    metas = [meta]
    if a.keep and out.exists():
        old = json.loads(out.read_text().split("const COMICS_GENERATED = ", 1)[1].rsplit(";\nif (typeof", 1)[0])
        pair = f"{a.frm}..{a.to}"
        strips = strips + [s for s in old["strips"] if s.get("pair") != pair]  # newest difference first
        metas = [m for m in old.get("metas", [old.get("meta")]) if m and (m["from"], m["to"]) != (a.frm, a.to)] + metas
    out.write_text("// Written by tools/strip_from_diff.py. Do not edit by hand.\n"
                   f"const COMICS_GENERATED = {json.dumps({'metas': metas, 'strips': strips}, indent=1, ensure_ascii=False)};\n"
                   "if (typeof COMICS !== 'undefined') COMICS.strips.splice(1, 0, ...COMICS_GENERATED.strips);\n")
    print(json.dumps(meta, indent=1))
    for s in strips:
        print(s["id"], len(s["frames"]), "frames")
        for f in s["frames"]:
            print("   ", f["head"], "|", f["cap"].replace("<b>", "").replace("</b>", ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
