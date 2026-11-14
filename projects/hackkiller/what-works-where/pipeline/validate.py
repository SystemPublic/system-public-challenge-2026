"""Fail loudly if the evidence data breaks any rule in AI_HANDOFF.md section 4/7.

Run: python3 pipeline/validate.py   (exit code 1 on any failure)
"""
from __future__ import annotations

import json
import re
import sys

import pandas as pd

from common import DATA, INTERIM, ROOT, SITE_DATA, TEAM_PROCESSED, VERIFIED

VOCAB = {
    "intervention_class": {"nets", "smc", "vaccines", "combination"},
    "outcome_tier": {"vector / entomological", "infection", "clinical malaria", "severe / hospital",
                     "anaemia & growth", "mortality", "other"},
    "role": {"effect on outcome", "use or coverage as exposure (observational)", "uptake / behaviour"},
    "verification_status": {"pending_source_review", "checked against abstract", "checked against full text",
                            "checked against paper", "label corrected", "comparator restored",
                            "time point restored", "paper supplement", "excluded: not an intervention effect"},
}
CONTRACTS = {
    "countries.csv": "iso3,name,region,seasonality,showcase,in_who,in_map,in_pf8,notes",
    "context_country_year.csv": "iso3,year,source,indicator,value,lower,upper,unit,estimate_type,release,flags",
    "pf8_sp_country_year.csv": "iso3,year,drug,n_determined,n_resistant,n_sensitive,n_undetermined,resistant_share,scope",
}
FULLTEXT_HEADER = ("result_id,pmid,pmcid,location,quoted_text,value_found,ci_found,matches_our_value,"
                   "discrepancy_note,checked_by,checked_at")
def _secret_patterns() -> list[str]:
    """The real key (read from .env, never stored in code) plus a generic 'x-api-key: <long token>' pattern."""
    pats = [r"x-api-key\s*[:=]\s*['\"][A-Za-z0-9]{20,}"]
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("SYSTEM_API_KEY=") and len(line.split("=", 1)[1].strip()) > 10:
                pats.append(re.escape(line.split("=", 1)[1].strip()))
    return pats


KEY_RX = re.compile("|".join(_secret_patterns()))
ISO_RX = re.compile(r"^[A-Z]{3}$")

failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        failures.append(msg)


def iso_ok(series: pd.Series, name: str) -> None:
    bad = {t for v in series.fillna("") for t in str(v).split(";") if t and not ISO_RX.match(t)}
    check(not bad, f"{name}: non-ISO3 tokens {sorted(bad)[:5]}")


def main() -> None:
    summ = json.loads((INTERIM / "candidates_summary.json").read_text())
    check(summ["snapshot_rows"] == 1_999_877, f"snapshot rows {summ['snapshot_rows']} != 1,999,877")

    g = pd.DataFrame(json.loads((SITE_DATA / "graph.json").read_text()))
    check(g.system_id.is_unique, "graph.json: duplicate system_id")
    team_path = TEAM_PROCESSED / "system_candidates.json"
    if team_path.exists():
        team = {r["system_id"] for r in json.loads(team_path.read_text())}
        missing = team - set(g.system_id)
        check(not missing, f"{len(missing)} teammate candidate ids missing from graph.json")
    for col in ("intervention_class", "outcome_tier", "role"):
        bad = set(g[col]) - VOCAB[col]
        check(not bad, f"graph.json {col}: unknown values {bad}")
    iso_ok(g["iso3"], "graph.json iso3")
    pr = g[g.plottable_ratio]
    ok = (pr.statistic_value > 0) & (pr.ci_lower > 0) & (pr.ci_lower <= pr.statistic_value) \
        & (pr.statistic_value <= pr.ci_upper) & (pr.statistic_value <= 20)
    check(bool(ok.all()), f"{int((~ok).sum())} plottable rows break ratio rules")

    q = pd.read_csv(DATA / "review" / "review_queue.csv", dtype=str, keep_default_na=False)
    check(len(q) == len(g) and set(q.system_id) == set(g.system_id), "review queue != graph candidates")

    for fname in ("evidence_verified.csv", "evidence_graph_checked.csv"):
        v = pd.read_csv(VERIFIED / fname, dtype=str, keep_default_na=False)
        check(v.result_id.is_unique, f"{fname}: duplicate result_id")
        bad = set(v.verification_status) - VOCAB["verification_status"] - {"checked against paper"}
        check(not bad, f"{fname}: unknown verification_status {bad}")
        check(bool((v.source_url.str.len() > 0).all()), f"{fname}: missing source_url")
        bad_ic = set(v.intervention_class) - VOCAB["intervention_class"]
        check(not bad_ic, f"{fname}: unknown intervention_class {bad_ic}")
        est = pd.to_numeric(v.estimate, errors="coerce")
        lo = pd.to_numeric(v.ci_lower, errors="coerce")
        hi = pd.to_numeric(v.ci_upper, errors="coerce")
        shown = ~v.verification_status.str.startswith("excluded")
        if fname == "evidence_graph_checked.csv":
            shown &= v.stat_family_hint.ne("difference") if "stat_family_hint" in v else shown
        ratio_like = shown & ~v.effect_measure.str.contains("difference", case=False)
        good = (est[ratio_like] > 0) & (lo[ratio_like] > 0) & (lo[ratio_like] <= est[ratio_like]) \
            & (est[ratio_like] <= hi[ratio_like])
        check(bool(good.all()), f"{fname}: {int((~good).sum())} shown rows with bad estimate/CI")
        if "graph_association_id" in v:
            ids = {i for i in v.graph_association_id if i}
            if fname == "evidence_graph_checked.csv":
                check(ids <= set(g.system_id), f"{fname}: association ids not in candidates "
                                                f"{sorted(ids - set(g.system_id))[:3]}")
                check(bool((v.source_quote.str.len() > 0).all()), f"{fname}: missing source_quote")
        if "iso3" in v:
            iso_ok(v["iso3"], f"{fname} iso3")

    for p in SITE_DATA.glob("*.json"):
        check(p.stat().st_size < 25 * 1024 * 1024, f"{p.name} >= 25 MB")
    for p in [*ROOT.rglob("*.json"), *ROOT.rglob("*.csv"), *ROOT.rglob("*.py"), *ROOT.rglob("*.md")]:
        if ".env" in p.name or "restored" in p.parts:
            continue
        try:
            if KEY_RX.search(p.read_text(errors="ignore")):
                failures.append(f"possible API key in {p.relative_to(ROOT)}")
        except OSError:
            pass

    ctx = DATA / "context"
    for name, header in CONTRACTS.items():
        f = ctx / name
        if f.exists():
            got = f.read_text().splitlines()[0].strip()
            check(got == header, f"{name}: header mismatch")
            df = pd.read_csv(f, dtype=str, keep_default_na=False)
            iso_ok(df["iso3"], name)
    ft = VERIFIED / "fulltext_checks.csv"
    if ft.exists():
        check(ft.read_text().splitlines()[0].strip() == FULLTEXT_HEADER, "fulltext_checks.csv: header mismatch")

    if failures:
        print("VALIDATION FAILED:")
        for f in failures:
            print("  -", f)
        sys.exit(1)
    gc = pd.read_csv(VERIFIED / "evidence_graph_checked.csv", dtype=str)
    print(f"OK: {len(g)} candidates ({g.pubmed_id.nunique()} papers), {len(q)} queued, "
          f"{len(pd.read_csv(VERIFIED / 'evidence_verified.csv'))} paper-verified + {len(gc)} abstract-checked rows, "
          f"context files present: {sorted(p.name for p in ctx.glob('*.csv'))}")


if __name__ == "__main__":
    main()
