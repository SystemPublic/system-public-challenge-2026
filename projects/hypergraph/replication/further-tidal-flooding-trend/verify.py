#!/usr/bin/env python
"""Verify this replication package. Usage: python verify.py [--refetch] [--python PATH]

1. Checks the sha256 of every file copied into inputs/ against manifest.json.
2. Reruns the deciding number with code/rerun.py on inputs/ (no network) and compares it with the recorded
   outcome within the tolerance stated in manifest.json.
3. With --refetch, re-runs each pinned Socrata query and NOAA download (no key needed), writes the responses to
   refetched/ in the same layout, compares them with the pinned hashes, and, where the recipe allows, reruns the
   deciding number on the live data.

Result: MATCH (inputs intact, number within tolerance), DRIFT (an input differs from its pin: a copy was altered,
or with --refetch a live source has changed), MISMATCH (inputs intact, number outside tolerance: the code or the
environment differs). Only files inside this folder are read.
"""
import argparse, hashlib, json, shutil, subprocess, sys, time, urllib.parse, urllib.request
from pathlib import Path

PKG = Path(__file__).resolve().parent
M = json.loads((PKG / "manifest.json").read_text())


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while b := f.read(1 << 20):
            h.update(b)
    return h.hexdigest()


def rows_sha(rows):
    return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def rerun(py, inputs):
    r = subprocess.run([py, str(PKG / "code" / "rerun.py"), "--inputs", str(inputs)], cwd=PKG, capture_output=True, text=True)
    if r.returncode:
        return None, r.stderr[-3000:]
    try:
        return json.loads(r.stdout.strip().splitlines()[-1]), None
    except Exception as e:  # noqa: BLE001
        return None, f"could not parse rerun output: {e}: {r.stdout[-500:]}"


def compare(got):
    d = M["deciding"]
    rows, ok = [], True
    for k, tol in d["tolerance"].items():
        rec, new = d["recorded"].get(k), got.get(k)
        good = rec is not None and new is not None and abs(float(new) - float(rec)) <= tol
        ok &= good
        rows.append({"key": k, "recorded": rec, "rerun": new, "tolerance": tol, "within": good})
    return ok, rows


def get(url, params=None, timeout=300):
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "replication-package-verify"})
    ctx = None
    try:  # some Python builds have no CA bundle for urllib; certifi (installed with requests) supplies one
        import certifi, ssl
        ctx = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        pass
    for i in range(5):
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                return r.read(), dict(r.headers)
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(3 * (i + 1))
    raise RuntimeError(f"fetch failed {url}: {last}")


def refetch():
    out = PKG / "refetched"
    report = []
    for f in M["inputs"]["files"]:  # start from the copies, so derived tables are present
        if f["copied"]:
            dst = out / f["path"]
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(PKG / "inputs" / f["path"], dst)
    for e in M["data"]:
        if e.get("type") == "socrata":
            ds, dom = e["dataset"], e["domain"]
            try:
                meta = json.loads(get(f"{dom}/api/views/{ds}.json")[0])
                ts = meta.get("rowsUpdatedAt")
                live_ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts)) if ts else None
            except Exception as ex:  # noqa: BLE001
                live_ts = f"error: {ex}"
            r = {"source": f"socrata {ds}", "pinned_rows_updated_at": e.get("rows_updated_at"), "live_rows_updated_at": live_ts}
            changed_ts = live_ts != e.get("rows_updated_at")
            for cf in e.get("cache_files", []):
                if not cf["copied"]:
                    r.setdefault("not_refetched", []).append(cf["path"])
                    continue
                pinned = json.loads((PKG / "inputs" / cf["path"]).read_text())
                params = pinned["source"]["query"]
                # the cached page may carry $offset; the source record in the file is the page's own query
                body, _ = get(f"{dom}/resource/{ds}.json", params)
                rows = json.loads(body)
                new = rows_sha(rows)
                r.setdefault("pages", []).append({"path": cf["path"], "pinned_rows_sha256": cf["rows_sha256"],
                                                  "live_rows_sha256": new, "same": new == cf["rows_sha256"],
                                                  "pinned_n": len(pinned["rows"]), "live_n": len(rows)})
                (out / cf["path"]).write_text(json.dumps({"source": {**pinned["source"], "fetched": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                                                                     "n_rows": len(rows)}, "rows": rows}))
            r["drift"] = changed_ts or any(not p["same"] for p in r.get("pages", []))
            report.append(r)
        elif e.get("type") == "noaa" and e.get("file", {}).get("copied"):
            body, hdr = get(e["url"])
            p = out / e["file"]["path"]
            p.write_bytes(body)
            p.with_suffix(".meta").write_text(hdr.get("Last-Modified", "") + "\n" + time.strftime("%Y-%m-%dT%H:%M:%S%z"))
            new = hashlib.sha256(body).hexdigest()
            pin = e["file"].get("full_sha256", e["file"]["sha256"])
            report.append({"source": f"noaa {e['station']}", "pinned_last_modified": e.get("last_modified"),
                           "live_last_modified": hdr.get("Last-Modified"), "pinned_sha256": pin,
                           "live_sha256": new, "drift": new != pin})
    return out, report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refetch", action="store_true")
    ap.add_argument("--python", default=sys.executable)
    a = ap.parse_args()
    res = {"claim": M["claim"]["id"], "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    bad = []
    for f in M["inputs"]["files"]:
        if f["copied"]:
            p = PKG / "inputs" / f["path"]
            if not p.exists() or sha(p) != f["sha256"]:
                bad.append(f["path"])
    missing = [f["path"] for f in M["inputs"]["files"] if f.get("required_for_rerun_but_missing")]
    res["inputs"] = {"copied": sum(f["copied"] for f in M["inputs"]["files"]), "hash_failures": bad,
                     "required_but_pointer_only": missing}
    if not (PKG / "code" / "rerun.py").exists():
        res["status"] = "DRIFT" if bad else "NO_RERUN"
        res["note"] = "No rerun recipe is packaged for this claim; only the input hashes were checked."
        print(json.dumps(res, indent=1))
        return
    got, err = rerun(a.python, PKG / "inputs")
    res["rerun"] = got if got else {"error": err}
    ok, rows = compare(got) if got else (False, [])
    res["comparison"] = rows
    if a.refetch:
        try:
            rdir, rep = refetch()
        except Exception as ex:  # noqa: BLE001
            rdir, rep = None, [{"source": "refetch", "error": str(ex)[:500], "drift": None}]
        res["refetch"] = rep
        drift = any(r.get("drift") for r in rep)
        if rdir is None:
            res["rerun_on_live_inputs"] = "not run: the refetch failed"
        elif M["deciding"].get("refetch_rerun"):
            got2, err2 = rerun(a.python, rdir)
            res["rerun_on_live_inputs"] = got2 if got2 else {"error": err2}
            if got2:
                ok2, res["comparison_live"] = compare(got2)
                res["live_number_within_tolerance"] = ok2
        else:
            res["rerun_on_live_inputs"] = ("not run: the deciding number is computed from derived tables whose upstream "
                                           "stages are not packaged; the live check covers the pinned sources only")
    else:
        drift = False
    if bad:
        res["status"] = "DRIFT"
    elif got is None or not ok:
        res["status"] = "MISMATCH"
    elif drift:
        res["status"] = "DRIFT"
    else:
        res["status"] = "MATCH"
    print(json.dumps(res, indent=1, default=str))
    (PKG / "verify_result.json").write_text(json.dumps(res, indent=1, default=str))
    sys.exit(0 if res["status"] == "MATCH" else 1)


if __name__ == "__main__":
    main()
