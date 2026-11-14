"""Run everything: graph evidence, city tests, verdicts, research-needed scores, export.

    python -m pipeline.build

Writes web/data/ground_truth.json, web/data/districts.geojson and out/ (summary, per-claim findings for review).
Verdicts are computed twice: v1.0.0 uses every finding; v1.1.0 drops findings marked "wrong" in
review/to_check.csv (findings we checked against the paper and found wrongly extracted).
"""
import csv
import datetime as dt
import json

import numpy as np
import pandas as pd
from shapely.geometry import mapping, shape

from . import city, config as C, graph, stats
from .claims import CLAIMS
from .data import connect, version_info


TRIAGE_HINTS = {  # applied only when a claim is not confirmed
    "trees-cool": ["weak proxy"],
    "hot-districts-heat-ed": ["weak proxy"],
    "greenery-cools-cd": ["scale"],
    "hot-summers-hospitalizations": ["low variation"],
    "older-alone-heat-ed": ["population mismatch"],
    "poverty-heat-ed": ["weak proxy"],
}
VERDICT_WEIGHT = {"contested": 1.5, "inconclusive": 1.2, "bridged": 1.0, "confirmed": 0.3}

RULES = [
    "Research direction: majority sign of findings with a readable direction (ratio CI wholly above or below 1; "
    "signed coefficient or correlation with CI excluding 0 or p < 0.05). 'mixed' if fewer than 70% agree. "
    "Variables named 'lack of', 'low', 'no' etc. count in the opposite direction. Animal studies excluded.",
    "City test: Spearman rank correlation across areas; partial Spearman controlling for poverty; bootstrap 95% CI; "
    f"Benjamini–Hochberg false discovery rate {int(C.FDR * 100)}% across all city tests.",
    "Confirmed: city sign matches research, significant after correction, and the sign survives poverty control.",
    "Contested: city sign opposes research and is significant, or opposes it both before and after poverty control.",
    "Bridged: research links each step of a chain, no single dataset holds both ends, and the city end-to-end test "
    "has the predicted sign and is significant. Each middle link is reported.",
    "Inconclusive: everything else. Every non-confirmed claim says what data would settle it.",
]


def sgn(v):
    return 0 if v is None or pd.isna(v) else int(np.sign(v))


CHECKLIST = C.PROJECT / "review" / "to_check.csv"


def load_exclusions():
    """Findings judged wrong by hand: checklist rows marked 'wrong', with their reasons."""
    if not CHECKLIST.exists():
        return {}
    with open(CHECKLIST) as f:
        return {r["system_id"]: r.get("reason", "") for r in csv.DictReader(f)
                if (r.get("decision") or "").strip().lower() == "wrong"}


# Code fixes that came out of the hand-check (the findings themselves were right; our reading was not).
READER_FIXES = ['Our code read "poor mental health" as the absence of harm, so 2 cold-home findings counted '
                'backwards. Fixed: the cold-harm end no longer flips on words like "poor" or "lower".']


def load_review():
    """Hand-check decisions from review/to_check.csv: system_id -> ok | wrong | unclear, plus notes for the readme."""
    if not CHECKLIST.exists():
        return {}, []
    with open(CHECKLIST) as f:
        rows = [r for r in csv.DictReader(f) if (r.get("decision") or "").strip()]
    decided = {r["system_id"]: r["decision"].strip().lower() for r in rows}
    notes = [f'Excluded {r["system_id"]} ({r["claim"]}): "{r["variable_a"]}" and "{r["variable_b"]}", '
             f'{r["graph_says"]}. {r.get("reason", "").strip()}' for r in rows if r["decision"].strip().lower() == "wrong"]
    return decided, notes + READER_FIXES


def review_counts(ids, decided):
    got = [decided[i] for i in ids if i in decided]
    return {"checked": len(got), "ok": got.count("ok"), "wrong": got.count("wrong"), "unclear": got.count("unclear")}


def research_side(con, claim, excluded, frames):
    ends = claim["ends"]
    links = []
    for a, b in zip(ends, ends[1:]):
        df = graph.findings(con, a, b)
        kept = df[~df["system_id"].isin(excluded)] if not df.empty else df
        links.append({"from": a["label"], "to": b["label"], "all": df, "kept": kept, "source": "graph",
                      "summary_v1": graph.summarize(df), "summary": graph.summarize(kept)})
    # A bridge link the graph can't sign may be supplied by a significant city link (that is what makes it a bridge)
    for i, fb in claim.get("link_fallback", {}).items():
        if links[i]["summary"]["direction"] in ("+", "-"):
            continue
        f = frames[fb["frame"]]
        d = f.df[[fb["x"], fb["y"]]].dropna()
        rho, p = stats.spearman(d[fb["x"]], d[fb["y"]])
        if p < 0.05:
            links[i]["city_fill"] = {"direction": "+" if rho > 0 else "-", "rho": round(rho, 3), "p": round(p, 5),
                                     "n": int(len(d)), "unit": f.unit, "x_label": f.labels[fb["x"]],
                                     "y_label": f.labels[fb["y"]],
                                     "sources": sources_for(f, [fb["x"], fb["y"]])}
            links[i]["source"] = "city"

    def chain_dir(key):
        dirs = [l.get("city_fill", {}).get("direction") or l[key]["direction"] for l in links]
        if any(d not in ("+", "-") for d in dirs):
            return None if any(d is None for d in dirs) else "mixed"
        return "+" if np.prod([1 if d == "+" else -1 for d in dirs]) > 0 else "-"

    allf = pd.concat([l["all"] for l in links]) if links else pd.DataFrame()
    kept = pd.concat([l["kept"] for l in links]) if links else pd.DataFrame()
    return links, chain_dir("summary"), chain_dir("summary_v1"), allf, kept


def city_side(frame, spec):
    x, y, ctrl = spec["x"], spec["y"], spec.get("control")
    cols = [x, y] + ([ctrl] if ctrl else [])
    d = frame.df[cols + [c for c in ("name",) if c in frame.df]].dropna(subset=cols)
    rho, p = stats.spearman(d[x], d[y])
    out = {"x": x, "y": y, "x_label": frame.labels[x], "y_label": frame.labels[y], "unit": frame.unit,
           "n": int(len(d)), "rho": round(rho, 3), "p": round(p, 5), "ci": stats.bootstrap_ci(d[x], d[y]),
           "partial_rho_poverty": None, "partial_p_poverty": None,
           "scatter": [{"id": i, "name": r.get("name"), "x": round(float(r[x]), 3), "y": round(float(r[y]), 3)}
                       for i, r in d.iterrows()],
           "_cols": [x, y] + ([spec["middle"]] if spec.get("middle") else [])}
    if ctrl:
        pr, pp = stats.partial_spearman(d[x].values, d[y].values, d[ctrl].values)
        out["partial_rho_poverty"], out["partial_p_poverty"] = round(pr, 3), round(pp, 5)
    if spec.get("middle"):
        m = spec["middle"]
        out["middle_links"] = []
        for a, b in ((x, m), (m, y)):
            dd = frame.df[[a, b]].dropna()
            r_, p_ = stats.spearman(dd[a], dd[b])
            out["middle_links"].append({"x_label": frame.labels[a], "y_label": frame.labels[b], "n": int(len(dd)),
                                        "rho": round(r_, 3), "p": round(p_, 5)})
    return out


def verdict(kind, expected, cty, q, direction):
    sig = q < C.FDR
    if direction == "mixed":  # the research disagrees with itself; a clear city result takes a side
        return "contested" if sig else "inconclusive"
    if expected not in (1, -1):
        return "inconclusive"
    s, ps = sgn(cty["rho"]), sgn(cty["partial_rho_poverty"])
    has_ctrl = cty["partial_rho_poverty"] is not None
    match = s == expected
    # poverty control must leave a real association in the predicted direction, not just the same sign
    survives = (not has_ctrl) or (ps == expected and abs(cty["partial_rho_poverty"]) >= 0.1)
    if match and sig and survives:
        return "bridged" if kind == "bridge" else "confirmed"
    if not match and (sig or (has_ctrl and ps == -expected)):
        return "contested"
    return "inconclusive"


def sources_for(frame, cols):
    out = []
    for c in cols:
        s = dict(frame.sources[c])
        vi = version_info(s.pop("alias"))
        out.append({**vi, **s})
    return out


def research_json(links, direction, allf, kept):
    studies = kept.drop_duplicates("study_id") if not kept.empty else kept
    fit = round(float(studies["fit"].mean()), 3) if not studies.empty else None
    g = version_info("graph")
    return {
        "direction": direction,
        "n_studies": int(kept["study_id"].nunique()) if not kept.empty else 0,
        "n_findings": int(len(kept)),
        "n_excluded_after_review": int(len(allf) - len(kept)),
        "agree_share": links[0]["summary"]["agree_share"] if len(links) == 1 else None,
        "evidence_fit": fit,
        "population": graph.population_profile(kept) if not kept.empty else {},
        "links": [{"from": l["from"], "to": l["to"], "source": l["source"], **l["summary"],
                   **({"city_fill": l["city_fill"]} if "city_fill" in l else {})} for l in links],
        "dois": sorted({d for d in kept.get("doi", pd.Series(dtype=str)).dropna()})[:200],
        "association_ids": sorted(kept["system_id"].tolist()) if not kept.empty else [],
        "graph": g,
    }


def district_need(cd, claims_out):
    df = cd.df.copy()
    pct = lambda s: s.rank(pct=True)
    burden = pct(df["heat_ed_rate"]).fillna(pct(df["heat_hosp_rate"])).fillna(0.5)
    vuln = (pct(df["poverty_pct"]) + pct(df["older_alone_pct"])) / 2
    open_claims = [c for c in claims_out if c["city"]["unit"] == "community district"
                   and c["verdict"] != "confirmed" and c["id"] != "bridge-no-heat-cold-ed"]
    gap = np.mean([(1 - (c["research"]["evidence_fit"] or 0)) * VERDICT_WEIGHT[c["verdict"]] for c in open_claims])
    raw = burden * (0.5 + 0.5 * vuln) * gap
    df["need_score"] = ((raw - raw.min()) / (raw.max() - raw.min())).round(3)
    df["need_rank"] = df["need_score"].rank(ascending=False, method="first").astype(int)

    groups = {"poverty_pct": "residents living in poverty", "older_alone_pct": "older adults living alone",
              "surface_temp_f": "residents of the city's hottest blocks"}
    out = []
    for i, r in df.iterrows():
        # the open claim whose exposure this district is most extreme on
        best, best_score = None, -1
        for c in open_claims:
            x = c["city"]["x"]
            score = (pct(df[x]).get(i, 0) if x in df else 0) * VERDICT_WEIGHT[c["verdict"]]
            if score > best_score:
                best, best_score = c, score
        who = [label for col, label in groups.items() if pct(df[col]).get(i, 0) >= 0.67] or ["its residents"]
        settle = (best or {}).get("settle") or ""
        out.append({
            "id": i, "name": r["name"], "borough": r["borough"],
            **{k: (None if pd.isna(r[k]) else round(float(r[k]), 2)) for k in (
                "heat_ed_rate", "heat_hosp_rate", "surface_temp_f", "veg_cover_pct", "tree_density_per_km2",
                "poverty_pct", "older_alone_pct", "cold_ed_rate", "asthma_ed_rate", "no_heat_complaints_per_1k")},
            "need_score": float(r["need_score"]), "need_rank": int(r["need_rank"]),
            "top_need_claim": best["id"] if best else None,
            "missing_study": (f"Heat illness among {' and '.join(who)} in {r['name']}. "
                              f"Almost none of the {len(open_claims) and ''}studies behind these claims describe them. "
                              f"{settle}").replace("  ", " "),
        })
    return out


def districts_geojson(con, ids):
    rows = con.execute("""select id, data->>'name' as name, data->>'borough' as borough,
        cast(data->'geometry' as varchar) as g from geo where type='Geography' and data->>'geoType'='CD'""").fetchall()
    feats = []
    for i, name, boro, g in rows:
        if i not in ids:
            continue
        geom = shape(json.loads(g)).simplify(0.0003, preserve_topology=True)
        feats.append({"type": "Feature", "id": i, "properties": {"id": i, "name": name, "borough": boro},
                      "geometry": json.loads(json.dumps(mapping(geom)))})
    return {"type": "FeatureCollection", "features": feats}


def main():
    con = connect()
    excluded = load_exclusions()
    decided, review_notes = load_review()
    frames = {"cd": city.districts(con), "uhf": city.uhf42(con), "year": city.yearly(con)}
    C.OUT.mkdir(parents=True, exist_ok=True)
    (C.PROJECT / "review").mkdir(exist_ok=True)

    rows = []
    for cl in CLAIMS:
        links, direction, direction_v1, allf, kept = research_side(con, cl, excluded, frames)
        frame = frames[cl["city"]["frame"]]
        cty = city_side(frame, cl["city"])
        pol = cl["city"].get("x_polarity", 1)
        rows.append({"claim": cl, "links": links, "direction": direction, "direction_v1": direction_v1,
                     "allf": allf, "kept": kept, "frame": frame, "city": cty,
                     "expected": sgn({"+": 1, "-": -1}.get(direction, 0)) * pol,
                     "expected_v1": sgn({"+": 1, "-": -1}.get(direction_v1, 0)) * pol})
        cols = ["system_id", "study_id", "doi", "name_a", "name_b", "system_statistic_type", "statistic_value",
                "ci_lower", "ci_upper", "p_value", "sign", "region", "population_string"]
        if not allf.empty:
            allf[cols].to_csv(C.OUT / f"findings_{cl['id']}.csv", index=False)

    # every finding behind every claim; pipeline/review.py turns it into the hand-check list review/to_check.csv
    sheet = [r["allf"].assign(claim=r["claim"]["id"]) for r in rows if not r["allf"].empty]
    if sheet:
        rv = pd.concat(sheet)
        rv["paper"] = "https://doi.org/" + rv["doi"].fillna("")
        rv["pubmed"] = rv["pubmed_id"].map(lambda x: f"https://pubmed.ncbi.nlm.nih.gov/{int(x)}/" if pd.notna(x) else "")
        rv[["claim", "system_id", "paper", "pubmed", "name_a", "name_b", "system_statistic_type", "statistic_value",
            "ci_lower", "ci_upper", "p_value", "sign", "region", "population_string"]].to_csv(
            C.OUT / "review_sheet.csv", index=False)

    qs = stats.benjamini_hochberg([r["city"]["p"] for r in rows])
    claims_out = []
    for r, q in zip(rows, qs):
        cl, cty = r["claim"], r["city"]
        v = verdict(cl["kind"], r["expected"], cty, q, r["direction"])
        v1 = verdict(cl["kind"], r["expected_v1"], cty, q, r["direction_v1"])
        resolution = None
        if r["direction"] == "mixed" and q < C.FDR:
            resolution = (f"The studies disagree. New York's data take a side: where {cty['x_label']} is higher, "
                          f"{cty['y_label']} is {'higher' if cty['rho'] > 0 else 'lower'} "
                          f"(ρ {cty['rho']:+.2f}, n {cty['n']}).")
        triage = []
        if v != "confirmed":
            triage += TRIAGE_HINTS.get(cl["id"], [])
            if r["direction"] in (None, "mixed"):
                triage.append("research mixed" if r["direction"] == "mixed" else "no readable research")
            if cty["n"] < 30:
                triage.append("small n")
            pr = cty["partial_rho_poverty"]
            if pr is not None and (sgn(pr) != sgn(cty["rho"]) or abs(pr) < max(0.1, abs(cty["rho"]) / 2)):
                triage.append("poverty confounding")
            fit = r["kept"].drop_duplicates("study_id")["fit"].mean() if not r["kept"].empty else 0
            if fit < 0.2 and "population mismatch" not in triage:
                triage.append("population mismatch")
            if cl["kind"] == "bridge" and cty.get("middle_links"):
                if any(m["p"] >= 0.05 for m in cty["middle_links"]):
                    triage.append("mechanism unconfirmed")
        bridge_note = None
        if cl["kind"] == "bridge" and cty.get("middle_links"):
            ml = cty["middle_links"]
            held = [m["p"] < 0.05 for m in ml]
            bridge_note = ("Both middle links hold in city data." if all(held) else
                           "The end-to-end link is tested directly; " +
                           ", ".join(f"{m['x_label']} → {m['y_label']} {'holds' if h else 'does not hold'} "
                                     f"(ρ {m['rho']:+.2f})" for m, h in zip(ml, held)) + ".")
        research = research_json(r["links"], r["direction"], r["allf"], r["kept"])
        city_out = {k: v_ for k, v_ in cty.items() if not k.startswith("_")}
        city_out["q"] = round(float(q), 5)
        city_out["sources"] = sources_for(r["frame"], cty["_cols"] + (
            [cl["city"]["control"]] if cl["city"].get("control") else []))
        claims_out.append({
            "id": cl["id"], "title": cl["title"], "kind": cl["kind"],
            "chain": [{"label": e["label"], "concept_ids": e.get("concepts", []), "pattern": e.get("regex")}
                      for e in cl["ends"]],
            "research": research, "city": city_out,
            "verdict": v, "verdict_v1": v1, "triage": list(dict.fromkeys(triage)),
            "settle": None if v == "confirmed" else cl["settle_if_not"],
            "bridge_note": bridge_note, "note": cl.get("note"), "resolution": resolution,
            "review": review_counts(set(r["allf"]["system_id"]) if not r["allf"].empty else set(), decided),
        })

    heat = graph.heat_studies(con)
    human = heat[heat["human"]]
    headline = {
        "studies_total": int(len(heat)), "studies_human": int(len(human)), "studies_nyc": int(heat["nyc"].sum()),
        "studies_mention_new_york": int(heat["mentions_new_york"].sum()),
        "studies_us": int(heat["us"].sum()), "studies_china": int((heat["region"] == "China").sum()),
        "studies_europe": int((heat["region"] == "Europe").sum()),
        "studies_no_place": int((heat["region"] == "No place stated").sum()),
        "studies_non_human": int((~heat["human"]).sum()),
        "studies_name_older_adults": int(human["older"].sum()),
        "studies_name_low_income": int(human["low_income"].sum()),
        "studies_name_black_or_hispanic": int(human["black_hispanic"].sum()),
        "nyc_studies": heat[heat["nyc"]][["study_id", "doi", "population_string"]].to_dict("records"),
        "pattern": graph.HEAT_STUDY_RX,
    }
    dots = [{"study_id": s.study_id, "region": s.region if s.human else "Animal studies", "human": bool(s.human),
             "doi": s.doi} for s in heat.itertuples()]

    districts = district_need(frames["cd"], claims_out)
    geo = districts_geojson(con, {d["id"] for d in districts})
    inputs = [version_info(a) for a in C.COLLECTIONS] + [version_info("graph")]
    out = {
        "meta": {
            "mock": False, "title": "Ground Truth", "outcome": "heat illness",
            "geography": "NYC community districts (59), UHF42 neighborhoods (42), citywide years",
            "generated_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
            "graph_citation": C.GRAPH_CITATION, "inputs": inputs, "rules": RULES,
            "excluded_findings": len(excluded),
            "review": {**review_counts(set(decided), decided), "notes": review_notes},
            "claims_collection": {"owner": C.CLAIMS_OWNER, "slug": C.CLAIMS_SLUG,
                                  "url": f"{C.UNDERLAY_WEB}/{C.CLAIMS_OWNER}/{C.CLAIMS_SLUG}",
                                  "compare_url": f"{C.UNDERLAY_WEB}/{C.CLAIMS_OWNER}/{C.CLAIMS_SLUG}/versions/compare"
                                                 f"?from=v1.0.0&to=v1.1.0",
                                  "versions": [{"semver": "v1.0.0", "label": "automated verdicts"},
                                               {"semver": "v1.1.0", "label": "after hand-checking findings"}]},
        },
        "headline": headline,
        "outcomes": graph.outcome_sweep(con),
        "evidence_dots": dots,
        "claims": claims_out,
        "districts": districts,
    }
    C.WEB_DATA.mkdir(parents=True, exist_ok=True)
    (C.WEB_DATA / "ground_truth.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":"),
                                                             default=lambda o: o.item() if hasattr(o, "item") else str(o)))
    (C.WEB_DATA / "districts.geojson").write_text(json.dumps(geo, separators=(",", ":")))

    summary = pd.DataFrame([{
        "claim": c["id"], "research": c["research"]["direction"], "studies": c["research"]["n_studies"],
        "findings": c["research"]["n_findings"], "fit": c["research"]["evidence_fit"], "unit": c["city"]["unit"][:4],
        "n": c["city"]["n"], "rho": c["city"]["rho"], "p": c["city"]["p"], "q": c["city"]["q"],
        "partial": c["city"]["partial_rho_poverty"], "verdict": c["verdict"], "v1": c["verdict_v1"]}
        for c in claims_out])
    summary.to_csv(C.OUT / "summary.csv", index=False)
    with pd.option_context("display.width", 200, "display.max_columns", 20):
        print(summary.to_string(index=False))
    print(f"\nheadline: {headline['studies_total']} heat studies, {headline['studies_nyc']} NYC, "
          f"{headline['studies_name_low_income']} name low-income, {headline['studies_name_black_or_hispanic']} "
          f"name Black/Hispanic, {headline['studies_non_human']} non-human")
    top = sorted(districts, key=lambda d: d["need_rank"])[:5]
    print("research needed most:", ", ".join(f"{d['name']} ({d['need_score']})" for d in top))
    size = (C.WEB_DATA / "ground_truth.json").stat().st_size / 1e6
    print(f"wrote {C.WEB_DATA / 'ground_truth.json'} ({size:.1f} MB) and districts.geojson")


if __name__ == "__main__":
    main()
