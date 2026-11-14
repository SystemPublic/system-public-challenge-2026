"""Scan the fixed System Public Graph association snapshot and export malaria-prevention candidates.

A row is a candidate if EITHER rule matches (match_rule = ours | teammate | both):
  ours      an intervention term in the row AND malaria context in the paper (any variable of the same
            PMID mentions malaria/Plasmodium/Anopheles/mosquito/parasite/ITN/LLIN)
  teammate  the exact PATTERNS + MALARIA regexes of scripts/clean_data.py (repo root) on the row text
Also records, over the whole snapshot, duplicate and conflicting association ids (teammate's QC).
Outputs data/interim/candidates.csv and candidates_summary.json.
"""
from __future__ import annotations

import hashlib
import re
from collections import Counter

import pandas as pd

from common import INTERIM, RAW_CSV, write_json

MALARIA_CTX = re.compile(r"malaria|plasmodium|falciparum|anophel|mosquito|parasit|\bitns?\b|\bllins?\b", re.I)

OUR_CLASSES = {
    "nets": re.compile(
        r"\bitns?\b|\bllins?\b|bed ?nets?|bednets?|mosquito nets?|insecticid\w*[- ]treated (bed ?)?nets?"
        r"|long[- ]lasting insecticid\w*|interceptor\s*g2|\big2\b|olyset|permanet|royal ?guard|pronet"
        r"|piperonyl|\bpbo\b|chlorfenapyr|pyriproxyfen|dual[- ]a(?:ctive)?[- ]?i(?:ngredient)?", re.I),
    "smc": re.compile(
        r"seasonal malaria chemopreven|\bsmc\b|\bspaq\b|\bsp ?\+ ?aq\b|sulfadoxine[- ]pyrimethamine"
        r"(?: plus| and| \+) amodiaquine|intermittent preventive treatment in children|\biptc\b", re.I),
    "vaccines": re.compile(r"rts,? ?s|\br21\b|malaria vaccin|mosquirix|matrix-m|vaccin\w* against malaria", re.I),
}
# verbatim from scripts/clean_data.py (teammate, v1.1.0)
TEAM_PATTERNS = {
    "nets": r"insecticide[ -]treated (?:bed[ -]?)?nets?|long[ -]lasting insecticid\w* nets?|\b(?:bed[ -]?nets?|llins?|interceptor g2|royal guard|permanet|olyset)\b|(?:chlorfenapyr|pyriproxyfen|piperonyl butoxide)",
    "smc": r"seasonal malaria chemoprevention|\bsmc\b|sulfadoxine[ -]pyrimethamine.{0,35}amodiaquine|\bsp[ +/\-]+aq\b",
    "vaccines": r"\brts\s*[,/\-]?\s*s\b|\br21(?:/matrix[ -]?m)?\b|malaria vaccin\w*|vaccin\w*.{0,30}malaria",
}
TEAM_RX = {k: re.compile(v, re.I) for k, v in TEAM_PATTERNS.items()}
TEAM_CTX = re.compile(r"malaria|plasmodium|anopheles|mosquito|\b(?:itns?|llins?)\b", re.I)

CHUNK = 250_000


def main() -> None:
    ctx_pmids: set[str] = set()
    id_sig: dict[str, bytes] = {}
    dup = Counter()
    conflict: set[str] = set()
    n_rows = 0
    for chunk in pd.read_csv(RAW_CSV, dtype=str, chunksize=CHUNK, keep_default_na=False):
        n_rows += len(chunk)
        text = chunk["variable_1_name"] + " || " + chunk["variable_2_name"]
        ctx_pmids.update(chunk.loc[text.str.contains(MALARIA_CTX), "pubmed_id"].tolist())
        for rec in chunk.itertuples(index=False):
            sig = hashlib.blake2b("\x1f".join(rec).encode(), digest_size=12).digest()
            prev = id_sig.get(rec.system_id)
            if prev is None:
                id_sig[rec.system_id] = sig
            else:
                dup[rec.system_id] += 1
                if prev != sig:
                    conflict.add(rec.system_id)

    keep = []
    for chunk in pd.read_csv(RAW_CSV, dtype=str, chunksize=CHUNK, keep_default_na=False):
        text = chunk["variable_1_name"] + " || " + chunk["variable_2_name"]
        joined = chunk["variable_1_name"] + " " + chunk["variable_2_name"]
        in_ctx = chunk["pubmed_id"].isin(ctx_pmids) | text.str.contains(MALARIA_CTX)
        ours = {k: text.str.contains(rx) & in_ctx for k, rx in OUR_CLASSES.items()}
        team_ctx = joined.str.contains(TEAM_CTX)
        team = {k: joined.str.contains(rx) & team_ctx for k, rx in TEAM_RX.items()}
        any_ours = ours["nets"] | ours["smc"] | ours["vaccines"]
        any_team = team["nets"] | team["smc"] | team["vaccines"]
        sel = any_ours | any_team
        if sel.any():
            sub = chunk.loc[sel].copy()
            sub["class"] = [";".join(k for k in OUR_CLASSES if ours[k].loc[i] or team[k].loc[i]) for i in sub.index]
            sub["match_rule"] = ["both" if any_ours.loc[i] and any_team.loc[i] else
                                 ("ours" if any_ours.loc[i] else "teammate") for i in sub.index]
            keep.append(sub)

    cand = pd.concat(keep, ignore_index=True)
    cand["exact_duplicate_rows"] = cand["system_id"].map(lambda s: dup.get(s, 0))
    cand["conflicting_association_id"] = cand["system_id"].isin(conflict)
    cand = cand.drop_duplicates("system_id")
    for col in ("statistic_value", "ci_lower", "ci_upper", "ci_level", "p_value"):
        cand[col + "_num"] = pd.to_numeric(cand[col], errors="coerce")
    INTERIM.mkdir(parents=True, exist_ok=True)
    cand.to_csv(INTERIM / "candidates.csv", index=False)

    summary = {
        "snapshot_file": str(RAW_CSV.name), "snapshot_rows": n_rows,
        "snapshot_duplicate_ids": len(dup), "snapshot_conflicting_ids": len(conflict),
        "malaria_context_pmids": len(ctx_pmids),
        "candidates": len(cand), "candidate_pmids": int(cand["pubmed_id"].nunique()),
        "by_match_rule": cand["match_rule"].value_counts().to_dict(),
        "by_class": {n: int(cand["class"].str.contains(n).sum()) for n in OUR_CLASSES},
        "pmids_by_class": {n: int(cand.loc[cand["class"].str.contains(n), "pubmed_id"].nunique()) for n in OUR_CLASSES},
        "with_both_ci": int((cand["ci_lower_num"].notna() & cand["ci_upper_num"].notna()).sum()),
        "statistic_types": cand["system_statistic_type"].value_counts().head(15).to_dict(),
    }
    write_json(INTERIM / "candidates_summary.json", summary)
    print(summary)


if __name__ == "__main__":
    main()
