"""Compare two versions of an Underlay collection of claims and return strips, joined to System's public graph.

Written on 14 November 2026, during the event, for the live demo (tools/demo_server.py, viz/compare.html).

  build(owner, slug, frm, to) -> {"meta": ..., "strips": [...]}

Three sources, each at a fixed version, are read through the Underlay's public API:
  1. the difference between two versions of the claims collection (GET .../versions/<to>/diff?from=<from>);
  2. for an edge that already had a test, the earlier outcome (GET .../versions/<from>/records/Outcome/<id>);
  3. System's public graph, system/public-graph: the Relationship record that the claim cites, which supplies
     the two concept labels and the counts of findings and studies.
Node names come from the graph's Relationship record when the claim cites one, from the claim's own concept
names otherwise, and from viz/data/strip_nodes.json only for the few claims that need a hand-set layout.
Responses for a named version never change, so they are cached in memory.
"""
from __future__ import annotations

import json
import math
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[1]
API = "https://www.underlay.org/api"
GRAPH = ("system", "public-graph")
NODES = json.loads((ROOT / "viz" / "data" / "strip_nodes.json").read_text())
_cache: dict[str, object] = {}
_session = requests.Session()
# Anonymous callers get 60 units a minute and a difference costs 5, so requests are signed when a key is present.
# The key is read from the user's config folder, is sent only to underlay.org and is never printed or returned.
_TOKEN = Path.home() / ".config" / "underlay" / "token"
if _TOKEN.exists():
    _session.headers["Authorization"] = "Bearer " + _TOKEN.read_text().strip()


def get(url: str, params: dict | None = None):
    key = url + "?" + json.dumps(params or {}, sort_keys=True)
    if key not in _cache:
        r = _session.get(url, params=params, timeout=60)
        if r.status_code == 429:
            raise RuntimeError("the Underlay's rate limit was reached; wait a minute")
        if r.status_code != 200:
            return None  # not cached, so a later call can succeed
        _cache[key] = r.json()
    return _cache[key]


def versions(owner: str, slug: str) -> list[dict]:
    v = _session.get(f"{API}/collections/{owner}/{slug}/versions", timeout=60).json()
    v = v if isinstance(v, list) else v.get("versions", [])
    return [{"semver": x.get("semver"), "createdAt": x.get("createdAt"), "recordCount": x.get("recordCount"), "message": x.get("message")} for x in v]


def record(owner: str, slug: str, semver: str, rtype: str, rid: str) -> dict | None:
    return get(f"{API}/collections/{owner}/{slug}/versions/{semver}/records/{rtype}/{quote(rid, safe='')}")


def graph_relationship(rel_id: str) -> dict | None:
    """The Relationship record for a concept pair, in either order, from system/public-graph."""
    a, _, b = rel_id.partition("|")
    recs = [r for r in (record(*GRAPH, "latest", "Relationship", f"{a}|{b}"), record(*GRAPH, "latest", "Relationship", f"{b}|{a}")) if r]
    if not recs:
        return None
    d = recs[0]["data"]
    return {"id": recs[0]["id"], "semver": recs[0].get("semver"), "source": d.get("sourceLabel"), "target": d.get("targetLabel"),
            "findings": sum(r["data"].get("numFindings") or 0 for r in recs), "studies": sum(r["data"].get("numStudies") or 0 for r in recs)}


def fmt(x: float, null) -> str:
    if null == 1:
        return f"{x:.2f}"
    a = abs(x)
    return f"{x:.0f}" if a >= 100 else f"{x:.1f}" if a >= 10 else f"{x:.2f}" if a >= 0.1 else f"{x:.3f}"


def eff(e: dict | None) -> dict | None:
    if not e or e.get("estimate") is None:
        return None
    lo, hi, est, null = e.get("lo"), e.get("hi"), e["estimate"], e.get("null")
    se = None
    try:
        if lo is not None and hi is not None:
            se = (math.log(hi) - math.log(lo)) / 3.92 if null == 1 and lo > 0 else None
    except (ValueError, TypeError):
        se = None
    nulled = lo is not None and hi is not None and null is not None and lo <= null <= hi
    label = ("×" + fmt(est, 1)) if null == 1 else fmt(est, null)
    iv = f"{fmt(est, null)} ({fmt(lo, null)} to {fmt(hi, null)})" if lo is not None and hi is not None else fmt(est, null)
    return {"est": est, "lo": lo, "hi": hi, "null": null, "se": se, "nulled": nulled, "label": label, "interval": iv, "scale": e.get("scale") or ""}


def plural(n: int, one: str, many: str | None = None) -> str:
    return f"{n} {one if n == 1 else (many or one + 's')}"


def width(e: dict) -> int:
    if e["se"] is None:
        return 2
    return 3 if e["se"] < 0.012 else 2 if e["se"] < 0.04 else 1


def wrap(s: str, n: int = 13) -> str:
    out, line = [], ""
    for w in str(s).split():
        if line and len(line) + 1 + len(w) > n:
            out.append(line); line = w
        else:
            line = (line + " " + w).strip()
    out.append(line)
    return "\n".join(out[:3])


def names_for(cid: str, claim: dict | None) -> tuple[str, str, dict | None, str]:
    """Node names, the graph relationship if the claim cites one, and where the names came from."""
    ge = ((claim or {}).get("data", {}).get("registration") or {}).get("graph_evidence") or []
    rel = None
    for g in ge:
        rid = g.get("relationship_id") if isinstance(g, dict) else None
        for x in (rid if isinstance(rid, list) else [rid]):
            if isinstance(x, str) and "|" in x and " " not in x and rel is None:
                rel = graph_relationship(x)
    m = NODES.get(cid) if isinstance(NODES.get(cid), dict) else None
    if m and m.get("a"):
        return m["a"], m["b"], rel, "typed by hand"
    if rel:
        return wrap(rel["source"]), wrap(rel["target"]), rel, "the graph's Relationship record"
    for g in ge:
        c = g.get("concepts") if isinstance(g, dict) else None
        if isinstance(c, list) and len(c) >= 2:
            return wrap(str(c[0]).split("(")[0]), wrap(str(c[-1]).split("(")[0]), None, "the claim's own concept names"
    return "", "", None, ""


def strip_for(owner, slug, frm, to, cid, g, n_from) -> dict | None:
    base_from = frm if frm else None
    claim, out, rev = g.get("Claim"), g.get("Outcome"), g.get("Revision")
    if out is None:
        out = record(owner, slug, to, "Outcome", cid)
    if claim is None:
        claim = record(owner, slug, to, "Claim", cid)
    e = eff(out["data"].get("city_effect")) if out else None
    if not e:
        return None
    a_name, b_name, rel, name_src = names_for(cid, claim)
    if not a_name:
        return None
    m = NODES.get(cid) if isinstance(NODES.get(cid), dict) else {}
    verdict = out["data"].get("verdict", "")
    withdrawn = bool(rev and rev["data"].get("verdict_changed") and rev["data"].get("verdict_before") == "confirmed")
    state = "gone" if withdrawn else "new"
    reg = ((claim or {}).get("data", {}).get("registered_at") or "")[:10]
    frames, sources = [], []
    A, B = {"id": "A", "label": a_name, "x": 76, "y": 150}, {"id": "B", "label": b_name, "x": 322, "y": 150}
    # frame: System's public graph
    if rel:
        sources.append({"text": f"Relationship {rel['id']} in system/public-graph {rel['semver'] or ''}: {plural(rel['findings'], 'finding')} from {plural(rel['studies'], 'study', 'studies')}.",
                        "href": f"https://www.underlay.org/api/collections/system/public-graph/versions/latest/records/Relationship/{quote(rel['id'], safe='')}", "link": "record"})
        frames.append({"head": "System's graph", "nodes": [{"id": "A", "label": wrap(rel["source"]), "x": 76, "y": 150}, {"id": "B", "label": wrap(rel["target"]), "x": 322, "y": 150}],
                       "edges": [{"a": "A", "b": "B", "ev": "cor", "dir": "none", "w": 3 if rel["findings"] >= 10 else 2 if rel["findings"] >= 3 else 1,
                                  "label": f"{plural(rel['findings'], 'finding')}\n{plural(rel['studies'], 'study', 'studies')}", "refs": [len(sources)], "lo": -24}],
                       "cap": f"System's public graph links {rel['source']} and {rel['target']}: {plural(rel['findings'], 'finding')} from {plural(rel['studies'], 'study', 'studies')}. It does not record which one is the cause, so the line has no arrow head."})
    # frame: the earlier version of the claims collection
    ctx = record(owner, slug, base_from, "Outcome", m["context"]) if (m.get("context") and base_from) else None
    ce = eff(ctx["data"].get("city_effect")) if ctx else None
    was = record(owner, slug, base_from, "Outcome", cid) if (base_from and out.get("change") == "updated") else None
    we = eff(was["data"].get("city_effect")) if was else None
    if ce:
        sources.append({"text": f"Outcome {m['context']} in {owner}/{slug} {frm}.", "href": f"https://www.underlay.org/api/collections/{owner}/{slug}/versions/{frm}/records/Outcome/{m['context']}", "link": "record"})
        frames.append({"head": f"Version {frm[1:]}", "nodes": [dict(A, y=120), dict(B, y=120)],
                       "edges": [{"id": "ab", "a": "A", "b": "B", "ev": "obs", "w": width(ce), "city": True, "label": ce["label"], "refs": [len(sources)], "lo": -14}],
                       "cap": f"Version {frm[1:]} of our collection has a city test on this edge: {ce['interval']}, {ctx['data']['verdict']}."})
    elif we:
        frames.append({"head": f"Version {frm[1:]}", "nodes": [A, B],
                       "edges": [{"a": "A", "b": "B", "ev": "obs", "w": width(we), "city": True, "label": we["label"], "lo": -14}],
                       "cap": f"Version {frm[1:]} held this claim as {was['data'].get('verdict')}: {we['interval']}."})
    elif not rel:
        frames.append({"head": f"Version {frm[1:]}" if frm else "Before", "nodes": [A, B], "edges": [],
                       "texts": [{"text": "no record\non this edge", "x": 199, "y": 150, "size": 13}],
                       "cap": (f"Version {frm[1:]} of our collection holds {n_from} records and has no test on this edge." if frm else "Before the first version there is no record on this edge.")})
    # frame: what the later version adds
    sources.append({"text": f"Outcome {cid} in {owner}/{slug} {to}. Registration sha256 {out['data'].get('registration_sha256', '')[:12]}. Node names: {name_src}.",
                    "href": f"https://www.underlay.org/api/collections/{owner}/{slug}/versions/{to}/records/Outcome/{quote(cid, safe='')}", "link": "record"})
    ref = len(sources)
    scale = "" if e["null"] == 1 else (" " + e["scale"][:48] if e["scale"] else "")
    verb = "adds" if out.get("change", "added") == "added" else "changes"
    cap2 = f"Version {to[1:]} {verb} our test, registered on {reg} and scored <b>{verdict}</b>: {e['interval']}{scale}."
    if m.get("compare") and base_from:
        cr = record(owner, slug, base_from, "Outcome", m["compare"])
        cme = eff(cr["data"].get("city_effect")) if cr else None
        if cme:
            cap2 += f" In {m.get('compare_place', 'the other city')} the same test gave {cme['interval']}."
    if ce and m.get("modifies"):
        f2 = {"head": f"Version {to[1:]} {verb}", "nodes": [dict(A, y=96), dict(B, y=96), {"id": "M", "label": m["node"], "x": 199, "y": 236, "state": state}],
              "edges": [{"id": "ab", "a": "A", "b": "B", "ev": "obs", "w": width(ce), "city": True, "label": ce["label"], "lo": -14}],
              "mods": [{"from": "M", "onto": "ab", "ev": "obs", "w": width(e), "state": state, "city": True, "label": e["label"], "refs": [ref], "lx": 40, "ly": 0, **({"mark": "x"} if withdrawn else {})}],
              "cap": cap2}
    else:
        edge = {"a": "A", "b": "B", "ev": "obs", "w": width(e), "state": state, "city": True, "label": e["label"], "refs": [ref], "lo": -14, "labelT": 0.36}
        if withdrawn:
            edge["mark"] = "x"
        elif verdict == "unsettled":
            edge.update(mark="?", markT=0.7)
        elif e["nulled"]:
            edge.update(mark="0", markT=0.7)
        f2 = {"head": f"Version {to[1:]} {verb}", "nodes": [A, B], "edges": [edge], "cap": cap2}
    frames.append(f2)
    # frame: a revision carried by the same difference
    if rev:
        sources.append({"text": f"Revision {rev['id']} in {to}: {rev['data'].get('critique') or 'no report path'}.",
                        "href": f"https://www.underlay.org/api/collections/{owner}/{slug}/versions/{to}/records/Revision/{quote(rev['id'], safe='')}", "link": "record"})
        f3 = json.loads(json.dumps(f2))
        f3["head"] = "A referee's revision"
        for part in f3.get("edges", []) + f3.get("mods", []):
            if part.get("state") == "new":
                part["state"] = "kept"
        for n in f3["nodes"]:
            if n.get("state") == "new":
                n.pop("state")
        vb, va = rev["data"].get("verdict_before"), rev["data"].get("verdict_after")
        if vb != va:
            f3.setdefault("texts", []).append({"text": f"verdict: {vb} → {va}", "x": 199, "y": 277 if (ce and m.get("modifies")) else 222, "state": "gone" if withdrawn else "new", "size": 13})
        reason = (rev["data"].get("reason") or "").strip()
        f3["cap"] = "The same version holds a revision. <b>" + (reason[:230] + ("…" if len(reason) > 230 else "")) + "</b>"
        frames.append(f3)
    title = f"{a_name} and {b_name}".replace("\n", " ") + (f" ({m['place']})" if m.get("place") and m["place"] not in b_name else "")
    return {"id": f"cmp-{cid}", "claim": cid, "verdict": verdict, "withdrawn": withdrawn, "has_graph": bool(rel), "has_revision": bool(rev), "title": title,
            "lede": f"Claim {cid}. " + ((claim or {}).get("data", {}).get("statement") or "")[:260], "sources": sources, "frames": frames}


def build(owner: str, slug: str, frm: str | None, to: str) -> dict:
    t0 = time.time()
    base = f"{API}/collections/{owner}/{slug}"
    recs, cursor = {"added": [], "updated": [], "removed": []}, None
    while True:
        p = {"limit": 5000, **({"from": frm} if frm else {}), **({"cursor": cursor} if cursor else {})}
        d = get(f"{base}/versions/{to}/diff", p)
        for k in recs:
            recs[k] += d[k]
        if not d["pagination"]["hasMore"]:
            break
        cursor = d["pagination"]["nextCursor"]
    vfrom = get(f"{base}/versions/{frm}") if frm else None
    by: dict[str, dict] = {}
    for change in ("added", "updated"):
        for r in recs[change]:
            cid = r["id"] if r["type"] == "Claim" else r["data"].get("claim", r["id"])
            cur = by.setdefault(cid, {})
            if r["type"] == "Revision" and "Revision" in cur and (cur["Revision"]["data"].get("seq") or 0) > (r["data"].get("seq") or 0):
                continue
            cur[r["type"]] = {"change": change, **r}
    twins = {c for c, m in NODES.items() if isinstance(m, dict) and m.get("twin_of") in by}
    cids = [c for c in by if c not in twins]
    n_from = (vfrom or {}).get("recordCount")
    with ThreadPoolExecutor(max_workers=16) as ex:
        strips = [s for s in ex.map(lambda c: _safe(owner, slug, frm, to, c, by[c], n_from), cids) if s]
    strips.sort(key=lambda s: (not s["withdrawn"], not s["has_graph"], not s["has_revision"], s["claim"]))
    meta = {"owner": owner, "slug": slug, "from": frm, "to": to, "added": len(recs["added"]), "updated": len(recs["updated"]), "removed": len(recs["removed"]),
            "claims_touched": len(by), "strips": len(strips), "with_graph_record": sum(s["has_graph"] for s in strips), "withdrawn": sum(s["withdrawn"] for s in strips),
            "graph": "system/public-graph v1.0.0", "seconds": round(time.time() - t0, 2),
            "compare": f"https://www.underlay.org/{owner}/{slug}/versions/compare?from={frm}&to={to}" if frm else f"https://www.underlay.org/{owner}/{slug}/versions"}
    return {"meta": meta, "strips": strips}


def _safe(owner, slug, frm, to, cid, g, n_from):
    try:
        return strip_for(owner, slug, frm, to, cid, g, n_from)
    except RuntimeError:
        raise
    except Exception:  # one malformed record must not stop the comparison
        return None


if __name__ == "__main__":
    import sys
    frm, to = (sys.argv[1] if len(sys.argv) > 1 else "v1.1.0"), (sys.argv[2] if len(sys.argv) > 2 else "v1.2.0")
    r = build("system-community", "nyc-concordance-claims", None if frm in ("none", "-") else frm, to)
    print(json.dumps(r["meta"], indent=1))
    for s in r["strips"][:8]:
        print(s["claim"], "|", s["title"], "|", len(s["frames"]), "frames", "| graph" if s["has_graph"] else "")
