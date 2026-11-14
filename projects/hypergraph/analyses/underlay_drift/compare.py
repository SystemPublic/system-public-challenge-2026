"""Compare the Underlay snapshot nyc/restaurant-inspections v1.0.0 (pushed
2026-06-12) with the live DOHMH table 43nn-pn8j (Manhattan rows). Descriptive
audit; no hypothesis is tested.

Inputs (from fetch_underlay.py and fetch_live.py):
  ~/opt/nyc-concordance/underlay/records_v1.0.0.ndjson
  ~/opt/nyc-concordance/underlay/live_43nn-pn8j_manhattan.csv.gz
  data/derived/underlay_drift/live_source.json
Outputs: data/derived/underlay_drift/*.csv, summary.json
"""
import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
BIG = Path.home() / "opt" / "nyc-concordance" / "underlay"
OUT = ROOT / "data" / "derived" / "underlay_drift"
PUSH_DATE = "2026-06-12"
WINDOW_START = "2024-01-01"   # earliest snapshot inspection is 2024-01-02


def load_snapshot():
    R, I, V = [], [], []
    for line in open(BIG / "records_v1.0.0.ndjson"):
        r = json.loads(line)
        d = dict(r["data"], _id=r["id"])
        {"Restaurant": R, "Inspection": I, "Violation": V}[r["type"]].append(d)
    R, I, V = pd.DataFrame(R), pd.DataFrame(I), pd.DataFrame(V)
    I["camis"] = I.restaurantId
    I["key"] = I.camis + "|" + I.inspectionDate + "|" + I.inspectionType
    I["score"] = I.score.astype("Int64")
    I["grade"] = I.grade.fillna("")
    I["gradeDate"] = I.gradeDate.fillna("")
    V = V.merge(I[["_id", "key"]], left_on="inspectionId", right_on="_id", suffixes=("", "_i"))
    return R, I, V


def load_live():
    L = pd.read_csv(BIG / "live_43nn-pn8j_manhattan.csv.gz", dtype=str)
    L["inspectionDate"] = L.inspection_date.str[:10]
    L["gradeDate"] = L.grade_date.str[:10].fillna("")
    L["grade"] = L.grade.fillna("")
    L["key"] = L.camis + "|" + L.inspectionDate + "|" + L.inspection_type.fillna("")
    insp = (L[L.inspectionDate > "1901"]
            .groupby("key", as_index=False)
            .agg(camis=("camis", "first"), inspectionDate=("inspectionDate", "first"),
                 inspectionType=("inspection_type", "first"), action=("action", "first"),
                 score=("score", "first"), grade=("grade", "first"), gradeDate=("gradeDate", "first"),
                 nta=("nta", "first"), zipcode=("zipcode", "first")))
    insp["score"] = pd.to_numeric(insp.score).astype("Int64")
    viol = L[L.violation_code.notna() & (L.inspectionDate > "1901")][["key", "violation_code"]] \
        .drop_duplicates().rename(columns={"violation_code": "violationCode"})
    return L, insp, viol


def grade_class(g):
    return g if g else "(blank)"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    src = json.loads((OUT / "live_source.json").read_text())
    R, I, V = load_snapshot()
    L, LI, LV = load_live()
    s = {"label": "descriptive", "snapshot": {
        "collection": "nyc/restaurant-inspections", "version": "v1.0.0",
        "hash": "ulv2:07a7f08a0d5c85649920f8adc6946d27c17f5e2d75e9ee07c0ad4ae0fcc6739c",
        "pushed": "2026-06-12T06:06:18Z", "records": int(len(R) + len(I) + len(V)),
        "inspection_dates": [I.inspectionDate.min(), I.inspectionDate.max()]},
        "live": src}

    # ---- how the snapshot was keyed: check ids against reconstructed keys
    s["keying"] = {
        "inspection_id_unique_per_camis_date_type": bool(I.key.is_unique),
        "violation_id_unique_per_inspection_code": bool((V.key + "|" + V.violationCode).is_unique),
        "live_rows_with_repeated_code_in_one_inspection": int(
            L[L.violation_code.notna()].groupby(["key", "violation_code"]).size().gt(1).sum()),
    }

    # ---- inspections in the window [WINDOW_START, PUSH_DATE)
    win = lambda d: (d >= WINDOW_START) & (d < PUSH_DATE)  # noqa: E731
    Iw, LIw = I[win(I.inspectionDate)], LI[win(LI.inspectionDate)]
    m = Iw.merge(LIw, on="key", how="outer", suffixes=("_s", "_l"), indicator=True)
    m["camis"] = m.camis_s.fillna(m.camis_l)
    m["date"] = m.inspectionDate_s.fillna(m.inspectionDate_l)
    m["month"] = m.date.str[:7]
    live_camis = set(L.camis)
    snap_camis = set(R._id)
    live_cd = set(LI.camis + "|" + LI.inspectionDate)
    snap_cd = set(I.camis + "|" + I.inspectionDate)

    def reason_snap_only(r):
        if r.camis not in live_camis:
            return "restaurant gone from live table"
        if f"{r.camis}|{r.date}" in live_cd:
            return "same restaurant and date, other inspection type (rekeyed)"
        return "restaurant still listed, inspection gone"

    def reason_live_only(r):
        if r.camis not in snap_camis:
            return "restaurant not in snapshot"
        if f"{r.camis}|{r.date}" in snap_cd:
            return "same restaurant and date, other inspection type (rekeyed)"
        return "restaurant in snapshot, inspection added"

    m["status"] = m._merge.map({"both": "both", "left_only": "snapshot only", "right_only": "live only"})
    m["reason"] = ""
    so, lo = m.status == "snapshot only", m.status == "live only"
    m.loc[so, "reason"] = m[so].apply(reason_snap_only, axis=1)
    m.loc[lo, "reason"] = m[lo].apply(reason_live_only, axis=1)

    # violation code sets per inspection
    sv = V.groupby("key").violationCode.apply(lambda x: tuple(sorted(x)))
    lv = LV.groupby("key").violationCode.apply(lambda x: tuple(sorted(x)))
    b = m[m.status == "both"].copy()
    b["v_s"] = b.key.map(sv).apply(lambda x: x if isinstance(x, tuple) else ())
    b["v_l"] = b.key.map(lv).apply(lambda x: x if isinstance(x, tuple) else ())

    def neq(a, c):
        return ~((a == c) | (a.isna() & c.isna())).fillna(False).astype(bool)
    b["d_score"] = neq(b.score_s, b.score_l)
    b["d_grade"] = b.grade_s != b.grade_l
    b["d_gradeDate"] = b.gradeDate_s != b.gradeDate_l
    b["d_action"] = b.action_s != b.action_l
    b["d_violations"] = b.v_s != b.v_l
    fields = ["d_score", "d_grade", "d_gradeDate", "d_action", "d_violations"]
    b["changed"] = b[fields].any(axis=1)
    m = m.merge(b[["key", "changed"] + fields], on="key", how="left")

    counts = m.status.value_counts().to_dict()
    s["inspections_before_push"] = {
        "window": [WINDOW_START, "2026-06-11"],
        "snapshot": int(len(Iw)), "live": int(len(LIw)),
        "both": int(counts.get("both", 0)),
        "snapshot_only": int(counts.get("snapshot only", 0)),
        "live_only": int(counts.get("live only", 0)),
        "snapshot_only_reasons": m[m.status == "snapshot only"].reason.value_counts().to_dict(),
        "live_only_reasons": m[m.status == "live only"].reason.value_counts().to_dict(),
        "both_changed_any_field": int(b.changed.sum()),
        "both_changed_by_field": {f[2:]: int(b[f].sum()) for f in fields},
    }
    # inspections before WINDOW_START in live (outside snapshot scope)
    s["live_inspections_before_2024"] = int((LI.inspectionDate < WINDOW_START).sum())
    s["live_inspections_2023"] = int(LI.inspectionDate.str[:4].eq("2023").sum())

    # ---- kinds of change
    ch = b[b.changed]
    sc = ch[ch.d_score]
    kinds = {
        "score": {
            "blank_to_value": int((sc.score_s.isna() & sc.score_l.notna()).sum()),
            "value_to_blank": int((sc.score_s.notna() & sc.score_l.isna()).sum()),
            "lowered": int((sc.score_l < sc.score_s).fillna(False).sum()),
            "raised": int((sc.score_l > sc.score_s).fillna(False).sum()),
            "median_change_points": float(np.nanmedian((sc.score_l - sc.score_s).astype(float))),
        },
        "grade_transitions": {f"{grade_class(a)} -> {grade_class(c)}": n for (a, c), n in
                              Counter(zip(ch[ch.d_grade].grade_s, ch[ch.d_grade].grade_l)).most_common()},
        "gradeDate": {
            "blank_to_date": int(((ch.gradeDate_s == "") & (ch.gradeDate_l != "") & ch.d_gradeDate).sum()),
            "date_to_blank": int(((ch.gradeDate_s != "") & (ch.gradeDate_l == "") & ch.d_gradeDate).sum()),
            "date_to_other_date": int(((ch.gradeDate_s != "") & (ch.gradeDate_l != "") & ch.d_gradeDate).sum()),
        },
        "action_transitions": {f"{a[:45]} -> {c[:45]}": n for (a, c), n in
                               Counter(zip(ch[ch.d_action].action_s, ch[ch.d_action].action_l)).most_common(8)},
    }
    dv = ch[ch.d_violations]
    rem = Counter(c for a, l in zip(dv.v_s, dv.v_l) for c in set(a) - set(l))
    add = Counter(c for a, l in zip(dv.v_s, dv.v_l) for c in set(l) - set(a))
    kinds["violations"] = {
        "inspections_with_codes_removed_only": int(sum(bool(set(a) - set(l)) and not (set(l) - set(a))
                                                      for a, l in zip(dv.v_s, dv.v_l))),
        "inspections_with_codes_added_only": int(sum(bool(set(l) - set(a)) and not (set(a) - set(l))
                                                    for a, l in zip(dv.v_s, dv.v_l))),
        "inspections_with_both": int(sum(bool(set(l) - set(a)) and bool(set(a) - set(l))
                                         for a, l in zip(dv.v_s, dv.v_l))),
        "codes_removed_total": int(sum(rem.values())), "codes_added_total": int(sum(add.values())),
        "most_removed": dict(rem.most_common(8)), "most_added": dict(add.most_common(8)),
    }
    # score change alongside violation removal
    both_sv = ch[ch.d_score & ch.d_violations]
    kinds["score_and_violations_changed_together"] = int(len(both_sv))
    s["kinds_of_change"] = kinds

    # ---- violations matched by inspection key + code
    Vw = V[V.key.isin(Iw.key)][["key", "violationCode"]]
    LVw = LV[LV.key.isin(LIw.key)]
    vm = Vw.merge(LVw, on=["key", "violationCode"], how="outer", indicator=True)
    vm["insp_in_both"] = vm.key.isin(b.key)
    s["violations_before_push"] = {
        "snapshot": int(len(Vw)), "live": int(len(LVw)),
        "both": int((vm._merge == "both").sum()),
        "snapshot_only": int((vm._merge == "left_only").sum()),
        "snapshot_only_where_inspection_in_both": int(((vm._merge == "left_only") & vm.insp_in_both).sum()),
        "live_only": int((vm._merge == "right_only").sum()),
        "live_only_where_inspection_in_both": int(((vm._merge == "right_only") & vm.insp_in_both).sum()),
    }

    # ---- restaurants
    live_r = L.groupby("camis").agg(dba=("dba", "first"), building=("building", "first"),
                                    street=("street", "first"), zipcode=("zipcode", "first"),
                                    cuisine=("cuisine_description", "first"), phone=("phone", "first"))
    live_r = live_r.fillna("").replace({"building": {"0": ""}})
    live_r["street"] = live_r.street.str.split().str.join(" ")
    rr = R.set_index("_id")
    rr = rr.assign(**{c: rr[c].fillna("") for c in ["name", "building", "street", "zipcode", "cuisineDescription", "phone"]})
    rr["street_norm"] = rr.street.str.split().str.join(" ")
    gone = sorted(set(rr.index) - set(live_r.index))
    kept = rr.index.intersection(live_r.index)
    rk, lk = rr.loc[kept], live_r.loc[kept]
    rdiff = {
        "name": int((rk.name != lk.dba).sum()),
        "building_or_street_whitespace_normalised": int(((rk.building != lk.building) | (rk.street_norm != lk.street)).sum()),
        "zipcode": int((rk.zipcode != lk.zipcode).sum()),
        "cuisine": int((rk.cuisineDescription != lk.cuisine).sum()),
        "phone": int((rk.phone != lk.phone).sum()),
    }
    # closures: latest live action that is a DOHMH closure, among snapshot restaurants
    last = LI.sort_values("inspectionDate").groupby("camis").tail(1).set_index("camis")
    closed_now = last.action.fillna("").str.contains("closed by DOHMH|re-closed", case=False)
    snap_last = I.sort_values("inspectionDate").groupby("camis").tail(1).set_index("camis")
    snap_closed = snap_last.action.fillna("").str.contains("closed by DOHMH|re-closed", case=False)
    # live camis with only placeholder (1900) rows = new, not yet inspected
    placeholder_only = set(L.camis) - set(LI.camis)
    new_camis_with_pre_push_insp = set(LIw.camis) - set(rr.index)
    s["restaurants"] = {
        "snapshot": int(len(rr)), "live_manhattan_camis": int(L.camis.nunique()),
        "snapshot_restaurants_gone_from_live": len(gone),
        "snapshot_restaurants_still_listed": int(len(kept)),
        "still_listed_field_changes": rdiff,
        "snapshot_restaurants_whose_latest_live_inspection_is_a_closure": int(closed_now.reindex(kept).fillna(False).sum()),
        "of_which_latest_snapshot_inspection_was_already_a_closure": int(
            (closed_now.reindex(kept).fillna(False) & snap_closed.reindex(kept).fillna(False)).sum()),
        "live_camis_placeholder_only_not_yet_inspected": len(placeholder_only),
        "live_camis_with_pre_push_inspection_absent_from_snapshot": len(new_camis_with_pre_push_insp),
    }
    gone_last = snap_last.reindex(gone)
    s["restaurants"]["gone_by_last_snapshot_inspection_year"] = gone_last.inspectionDate.str[:4].value_counts().sort_index().to_dict()

    # ---- by inspection month
    bym = m.groupby("month").agg(
        both=("status", lambda x: (x == "both").sum()),
        snapshot_only=("status", lambda x: (x == "snapshot only").sum()),
        live_only=("status", lambda x: (x == "live only").sum()),
        changed=("changed", lambda x: x.fillna(False).astype(bool).sum()),
        score_changed=("d_score", lambda x: x.fillna(False).astype(bool).sum()),
        grade_changed=("d_grade", lambda x: x.fillna(False).astype(bool).sum()),
        violations_changed=("d_violations", lambda x: x.fillna(False).astype(bool).sum()),
    ).reset_index()
    bym["snapshot_total"] = bym.both + bym.snapshot_only
    bym["share_snapshot_not_unchanged"] = (bym.snapshot_only + bym.changed) / bym.snapshot_total
    bym.to_csv(OUT / "by_month.csv", index=False)
    m.drop(columns=["_merge"]).to_csv(BIG / "inspection_match.csv.gz", index=False)
    m.status.groupby(m.reason.where(m.reason != "", m.status)).size().to_csv(OUT / "match_reasons.csv")

    # ---- example: one neighbourhood figure computed both ways
    # Share of graded cycle inspections (grade A/B/C) dated 2025-01-01..2026-05-31 that are A,
    # by ZIP code; snapshot vs the live table as of rowsUpdatedAt.
    def a_share(df, zipcol):
        g = df[df.grade.isin(["A", "B", "C"]) & (df.inspectionDate >= "2025-01-01") &
               (df.inspectionDate <= "2026-05-31")]
        t = g.groupby(zipcol).agg(n=("grade", "size"), a=("grade", lambda x: (x == "A").sum()))
        t["share_A"] = t.a / t.n
        return t
    Iz = I.merge(rr[["zipcode"]], left_on="camis", right_index=True)
    ts = a_share(Iz, "zipcode")
    tl = a_share(LI, "zipcode")
    ex = ts.add_suffix("_snapshot").join(tl.add_suffix("_live"), how="outer")
    ex["diff_pp"] = 100 * (ex.share_A_live - ex.share_A_snapshot)
    ex = ex[(ex.n_snapshot >= 100) & (ex.n_live >= 100)].sort_values("diff_pp")
    ex.to_csv(OUT / "example_zip_share_A.csv")
    s["example_share_A_by_zip"] = {
        "definition": "share of A among A/B/C grades on inspections dated 2025-01-01..2026-05-31, ZIPs with >=100 graded inspections in both",
        "zips": int(len(ex)),
        "diff_pp_median": float(ex.diff_pp.median()), "diff_pp_min": float(ex.diff_pp.min()),
        "diff_pp_max": float(ex.diff_pp.max()),
        "n_change_median": float((ex.n_live - ex.n_snapshot).median()),
        "manhattan_snapshot": float(a_share(Iz.assign(z="all"), "z").share_A.iloc[0]),
        "manhattan_live": float(a_share(LI.assign(z="all"), "z").share_A.iloc[0]),
        "manhattan_n_snapshot": int(a_share(Iz.assign(z="all"), "z").n.iloc[0]),
        "manhattan_n_live": int(a_share(LI.assign(z="all"), "z").n.iloc[0]),
    }
    (OUT / "summary.json").write_text(json.dumps(s, indent=1, default=int))
    print(json.dumps(s, indent=1, default=int))


if __name__ == "__main__":
    main()
