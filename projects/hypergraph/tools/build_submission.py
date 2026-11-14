"""Build the System Public Challenge 2026 submission folder from this repository.

    ~/.venvs/nyc-concordance/bin/python tools/build_submission.py [--check-only]

The folder is submission/projects/hypergraph/. It is a selection from the
repository, not a copy of all of it: the claims, the referee reports, the
clients, tools and analysis scripts, the pages and their data, the documents,
the figures they reference, the replication packages and the deck source.
The README, LICENSE and download_data.py come from tools/submission/, and
requirements.txt is written by `uv pip freeze` from the project's venv.

Files are taken from a commit (HEAD unless --rev is given) with git archive,
so only committed files are copied: nothing that .gitignore excludes, and no
uncommitted work. Commit changes before rebuilding. The build is made
in a temporary folder and then synchronised into the target: changed files are
replaced, and files that are no longer selected are moved to
_trash/<date>/submission-<time>/, never deleted.

After the build the script checks the folder and reports on each check:
  1. size: no file over 25 MB; the total is printed;
  2. secrets: no System key, no Underlay key (`ul_...`), neither of the local
     tokens as a literal string, no .env file (the tokens are never printed);
  3. absolute paths: no /Users/ or /Volumes/ in HTML, JS or JSON (other text
     files are listed as warnings);
  4. abstracts: no PubMed abstract text (no abstracts/ folder or abstracts file,
     no JSON field holding abstract text);
  5. links: every relative src/href in the HTML and every relative link in the
     Markdown resolves inside the folder, and every figures/... path named in
     the pages' data exists;
  6. challenge .gitignore: no file that the challenge repository would ignore.
The exit status is 1 if any check fails.
"""
from __future__ import annotations

import argparse
import filecmp
import fnmatch
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "submission" / "projects" / "hypergraph"
VENV = Path.home() / ".venvs" / "nyc-concordance"
MAX_BYTES = 25 * 1024 * 1024

# Folders copied whole (subject to .gitignore and EXCLUDE).
TREES = ["claims/registered", "claims/outcomes", "critique", "concord", "tools", "analyses", "sim",
         "viz", "replication", "deck", "docs"]
# Single files always copied, besides the figures found by scanning.
FILES = ["figures/viz/dashboard.png"]
# Paths never copied.
EXCLUDE = ["**/__pycache__/**", "**/*.pyc", "**/.DS_Store", "**/.env", "**/.env.*",
           "**/abstracts/**", "**/abstracts*.json", "**/abstracts*.txt", "**/abstracts_graph.txt",
           "**/verification_samples.json", "tools/submission/**",
           "replication/*/work/**", "replication/*/refetched/**", "replication/*/.venv/**"]
# Deck slides refer to images uploaded to the deck's asset store. These are the
# same images as files in figures/viz/ (matched by the slides' alt text).
DECK_BLOBS = {
    "a3eca3595dc81227a8cb6951f88b067a": "figures/viz/evidence_lineage_heat-shootings_timeline.png",
    "ffa86ea4f83becf09cec869593221487": "figures/viz/evidence_review_changes.png",
    "4cfa77fe0620107c8581201d20ad038a": "figures/viz/evidence_cards_placebos.png",
    "ebe9401b4622b41606c1233d01bf7fb0": "figures/hypergraph/slide_edge_field.png",
    "576181bdf4afbf11f78c4623d9b01c60": "figures/hypergraph/slide_edge_panel.png",
    "17d9b5aa575d5359b04d90a22076ed09": "figures/hypergraph/slide_edges_about_edges.png",
    "5115c7adc20b0f486260a73573902434": "figures/heat_drugs/slide_heat_drugs.png",
}
# Files scanned for figure references.
SCAN_FOR_FIGURES = ("docs/", "viz/", "deck/", "claims/", "critique/", "replication/")
FIG_RE = re.compile(r"(?<![\w.-])(?:\.\./)*(figures/[\w./-]+?\.(?:png|jpe?g|svg|gif|webp|pdf))", re.I)
TEXT_EXT = {".md", ".html", ".htm", ".js", ".json", ".jsonl", ".css", ".py", ".txt", ".csv", ".sh", ".toml",
            ".yaml", ".yml", ".geojson", ".svg", ".meta", ".sql", ""}
# Patterns from the challenge repository's .gitignore.
CHALLENGE_IGNORE = [".env", ".env.*", "*.key", "secrets.*", "*.parquet", "*.zip", "*.gz", "__pycache__",
                    "*.pyc", ".venv", "venv", ".ipynb_checkpoints", "node_modules", ".DS_Store", "Thumbs.db"]


def match_any(rel: str, pats) -> bool:
    # fnmatch's * also matches "/", so "**/x/**" covers nested paths; the second
    # test lets it match at the top level too.
    return any(fnmatch.fnmatch(rel, p) or (p.startswith("**/") and fnmatch.fnmatch(rel, p[3:])) for p in pats)


def git_files(rev: str, paths: list[str]) -> list[str]:
    """Files under paths in commit rev (only committed files, so nothing that
    .gitignore excludes and no one's uncommitted work)."""
    out = subprocess.run(["git", "ls-tree", "-r", "-z", "--name-only", rev, "--", *paths],
                         cwd=ROOT, capture_output=True, check=True).stdout.decode()
    return sorted({p for p in out.split("\0") if p})


def export_tree(rev: str, dest: Path) -> None:
    """Write the files of commit rev under TREES and figures/ into dest."""
    tar = subprocess.run(["git", "archive", "--format=tar", rev, "--", *TREES, "figures", "LICENSE"],
                         cwd=ROOT, capture_output=True, check=True).stdout
    subprocess.run(["tar", "-x", "-C", str(dest)], input=tar, check=True)


def select(rev: str, src: Path) -> list[str]:
    files = [f for f in git_files(rev, TREES) if not match_any(f, EXCLUDE)]
    figs = set(FILES) | set(DECK_BLOBS.values())
    for f in files:
        if f.startswith(SCAN_FOR_FIGURES) and Path(f).suffix in TEXT_EXT:
            for m in FIG_RE.finditer((src / f).read_text(errors="replace")):
                figs.add(m.group(1).rstrip("."))
    known = set(git_files(rev, ["figures"]))
    files += sorted(f for f in figs if f in known)
    return sorted(set(files))


def freeze() -> str:
    try:
        r = subprocess.run(["uv", "pip", "freeze"], env={**os.environ, "VIRTUAL_ENV": str(VENV)},
                           capture_output=True, text=True, check=True)
        return r.stdout
    except (OSError, subprocess.CalledProcessError) as e:
        print(f"  uv pip freeze failed ({e}); keeping the previous requirements.txt")
        old = TARGET / "requirements.txt"
        return old.read_text() if old.exists() else ""


def stage(rev: str, src: Path, dest: Path) -> list[str]:
    export_tree(rev, src)
    files = select(rev, src)
    for rel in files:
        out = dest / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src / rel, out)
        if rel.startswith("deck/") and rel.endswith(".html"):
            t = out.read_text()
            for blob, fig in DECK_BLOBS.items():
                t = t.replace(f"/_blob/{blob}", os.path.relpath(ROOT / fig, (ROOT / rel).parent))
            out.write_text(t)
    for name in ("README.md", "download_data.py"):
        shutil.copy2(src / "tools" / "submission" / name, dest / name)
    (dest / "LICENSE").write_text((src / "tools" / "submission" / "LICENSE_NOTE.md").read_text() + "## MIT licence\n\n"
                                  + (src / "LICENSE").read_text())
    (dest / "requirements.txt").write_text(freeze())
    return files


def sync(src: Path, dst: Path) -> dict:
    """Make dst equal to src without deleting: stale files go to _trash/."""
    stats = {"added": 0, "updated": 0, "unchanged": 0, "moved_to_trash": 0}
    trash = ROOT / "_trash" / time.strftime("%Y-%m-%d") / f"submission-{time.strftime('%H%M%S')}"
    want = {p.relative_to(src).as_posix() for p in src.rglob("*") if p.is_file()}
    if dst.exists():
        for p in sorted(dst.rglob("*")):
            rel = p.relative_to(dst).as_posix()
            if p.is_file() and rel not in want:
                (trash / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(p), trash / rel)
                stats["moved_to_trash"] += 1
        for p in sorted((q for q in dst.rglob("*") if q.is_dir()), key=lambda q: -len(q.parts)):
            if not any(p.iterdir()):
                p.rmdir()  # empty folders only
    for rel in sorted(want):
        s, d = src / rel, dst / rel
        if d.exists() and filecmp.cmp(s, d, shallow=False):
            stats["unchanged"] += 1
            continue
        stats["updated" if d.exists() else "added"] += 1
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(s, d)
    if stats["moved_to_trash"]:
        stats["trash"] = trash.relative_to(ROOT).as_posix()
    return stats


# ---------------------------------------------------------------- checks

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []

    def handle_starttag(self, tag, attrs):
        for k, v in attrs:
            if k in ("src", "href") and v:
                self.refs.append(v)


SKIP_REF = re.compile(r"^(?:[a-z][a-z0-9+.-]*:|#|//)|\$\{", re.I)
MD_LINK = re.compile(r"!?\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
MD_HTML = re.compile(r"""<(?:img|a|script|link)\b[^>]*?\b(?:src|href)\s*=\s*["']([^"']+)["']""", re.I)


def resolve(base: Path, file: Path, ref: str) -> str | None:
    """None if the reference resolves inside base, else the reason."""
    ref = ref.split("#")[0].split("?")[0]
    if not ref:
        return None
    if ref.startswith("/"):
        return "absolute path"
    p = Path(os.path.normpath(file.parent / ref))
    try:
        p.relative_to(base)
    except ValueError:
        return "outside the folder"
    if not p.exists():
        return "missing"
    cur = base
    for part in p.relative_to(base).parts:
        cur = cur / part
        if cur.is_symlink():
            return "passes through a symbolic link"
    return None


def check(base: Path) -> bool:
    files = sorted(p for p in base.rglob("*") if p.is_file())
    rel = lambda p: p.relative_to(base).as_posix()  # noqa: E731
    texts = {p: p.read_text(errors="replace") for p in files if p.suffix.lower() in TEXT_EXT}
    ok_all = True

    def report(name, ok, lines=(), warn=()):
        nonlocal ok_all
        ok_all &= ok
        print(f"[{'PASS' if ok else 'FAIL'}] {name}")
        for line in list(lines)[:40]:
            print(f"       {line}")
        for line in list(warn)[:20]:
            print(f"       warning: {line}")

    # 1. size
    sizes = {p: p.stat().st_size for p in files}
    big = [f"{rel(p)} {s / 1e6:.1f} MB" for p, s in sizes.items() if s > MAX_BYTES]
    largest = sorted(sizes.items(), key=lambda kv: -kv[1])[:3]
    report(f"size: {len(files)} files, {sum(sizes.values()) / 1e6:.1f} MB in all; largest "
           + ", ".join(f"{rel(p)} ({s / 1e6:.1f} MB)" for p, s in largest), not big, big)

    # 2. secrets (token values are compared, never printed)
    tokens = []
    for t in (Path.home() / ".config" / "system" / "token", Path.home() / ".config" / "underlay" / "token"):
        if t.exists() and t.read_text().strip():
            tokens.append((t.parent.name, t.read_text().strip().encode()))
    pats = [("Underlay key", re.compile(rb"\bul_[A-Za-z0-9_]{20,}")),
            ("System key assignment", re.compile(rb"(?i)(?:SYSTEM_API_KEY|x-api-key)[\"']?\s*[:=]\s*[\"']?(?!your-key)[A-Za-z0-9]{24,}")),
            ("40-character mixed-case token", re.compile(rb"\b(?=[A-Za-z0-9]{0,39}[A-Z])(?=[A-Za-z0-9]{0,39}[a-z])(?=[A-Za-z0-9]{0,39}[0-9])[A-Za-z0-9]{40}\b"))]
    hits = []
    for p in files:
        b = p.read_bytes()
        for name, tok in tokens:
            if tok in b:
                hits.append(f"{rel(p)}: contains the local {name} token")
        for name, rx in pats:
            if rx.search(b):
                hits.append(f"{rel(p)}: {name} pattern")
        if p.name == ".env" or p.name.startswith(".env."):
            hits.append(f"{rel(p)}: .env file")
    report(f"secrets: {len(tokens)} local tokens and {len(pats)} patterns searched in every file; no .env files",
           not hits, hits)

    # 3. absolute paths
    abs_rx = re.compile(r"/Users/|/Volumes/|file:///")
    bad, warn = [], []
    for p, t in texts.items():
        if abs_rx.search(t):
            n = len(abs_rx.findall(t))
            (bad if p.suffix.lower() in (".html", ".htm", ".js", ".json", ".jsonl") else warn).append(f"{rel(p)} ({n})")
    report("absolute paths: none in HTML, JS or JSON", not bad, bad, warn)

    # 4. abstracts
    # Scripts that fetch abstracts (analyses/*/abstracts.py) are code and are allowed; data files are not.
    bad = [rel(p) for p in files if p.suffix != ".py"
           and ("abstracts" in p.name.lower() or "abstracts" in rel(p).split("/")[:-1])]
    key_rx = re.compile(r'"(?:abstract|abstract_text|AbstractText|abstracts)"\s*:\s*"((?:[^"\\]|\\.){300,})"')
    bad += [f"{rel(p)}: JSON field holding abstract text" for p, t in texts.items()
            if p.suffix in (".json", ".js", ".jsonl") and key_rx.search(t)]
    report("abstracts: no PubMed abstract text (no abstracts files or folders, no abstract fields)", not bad, bad)

    # 5. links
    bad, n = [], 0
    for p, t in texts.items():
        if p.suffix.lower() in (".html", ".htm"):
            lp = Links()
            lp.feed(t)
            refs = lp.refs
        elif p.suffix.lower() == ".md":
            body = re.sub(r"```.*?```", "", t, flags=re.S)
            body = re.sub(r"`[^`\n]*`", "", body)
            refs = MD_LINK.findall(body) + MD_HTML.findall(body)
        else:
            continue
        for r in refs:
            if SKIP_REF.search(r):
                continue
            n += 1
            why = resolve(base, p, r)
            if why:
                bad.append(f"{rel(p)} -> {r}: {why}")
    figrefs, figbad = 0, []
    for p, t in texts.items():
        if rel(p).startswith(("viz/", "docs/", "deck/")) and p.suffix in (".js", ".json", ".html", ".md"):
            for m in FIG_RE.finditer(t):
                figrefs += 1
                if not (base / m.group(1)).exists():
                    figbad.append(f"{rel(p)} names {m.group(1)}, not in the folder")
    report(f"links: {n} relative links in HTML and Markdown resolve; {figrefs} figure paths in pages, docs and data exist",
           not bad and not figbad, bad + sorted(set(figbad)))

    # 6. the challenge repository's .gitignore
    bad = [rel(p) for p in files if any(fnmatch.fnmatch(part, pat) for part in rel(p).split("/")
                                       for pat in CHALLENGE_IGNORE)]
    report("challenge .gitignore: no file the challenge repository would ignore", not bad, bad)
    return ok_all


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check-only", action="store_true", help="check the existing folder without rebuilding")
    ap.add_argument("--dir", type=Path, help="check this folder instead of the target (with --check-only)")
    ap.add_argument("--rev", default="HEAD", help="the commit to build from (default HEAD); commit changes first")
    a = ap.parse_args(argv)
    base = (a.dir or TARGET).resolve()
    if not a.check_only:
        rev = subprocess.run(["git", "rev-parse", "--short=12", a.rev], cwd=ROOT, capture_output=True,
                             text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--", *TREES, "figures"], cwd=ROOT,
                               capture_output=True, text=True).stdout.strip()
        if dirty:
            print(f"note: uncommitted changes under the selected folders are not included (building from {rev})")
        with tempfile.TemporaryDirectory(prefix="hypergraph-src-") as src, \
                tempfile.TemporaryDirectory(prefix="hypergraph-") as tmp:
            files = stage(rev, Path(src), Path(tmp))
            stats = sync(Path(tmp), TARGET)
        print(f"built {TARGET.relative_to(ROOT)} from commit {rev}: {len(files)} repository files plus 4 written "
              "(README.md, LICENSE, requirements.txt, download_data.py); "
              + ", ".join(f"{k} {v}" for k, v in stats.items()))
    return 0 if check(base) else 1


if __name__ == "__main__":
    raise SystemExit(main())
