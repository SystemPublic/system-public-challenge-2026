"""FAERS heat-reaction disproportionality (reporting odds ratios) via the openFDA API.

WARNING SIGNAL, NOT PROOF: FAERS is spontaneous reporting. Anyone can report,
there is no denominator of people taking each drug, reports are duplicated and
stimulated by publicity, and a report does not show the drug caused the event.

Method (all counts are distinct safety reports from drug/event.json):
  drug clause   patient.drug.openfda.generic_name:"<ingredient>"  (any role: suspect,
                concomitant or interacting; openFDA cannot tie drugcharacterization to
                a specific drug entry within a report, so primary-suspect restriction
                is not possible with search/count queries)
  heat PTs      HEAT STROKE, HYPERTHERMIA, HEAT EXHAUSTION, HEAT ILLNESS,
                BODY TEMPERATURE INCREASED, ANHIDROSIS, HYPOHIDROSIS
                -> "broad" composite. "Specific" composite (primary) = HEAT STROKE, HEAT EXHAUSTION,
                HEAT ILLNESS, ANHIDROSIS, HYPOHIDROSIS (drops fever-like and NMS/serotonin PTs).
  fluid PTs     DEHYDRATION, HYPONATRAEMIA, ACUTE KIDNEY INJURY (scored separately)
  2x2 table     a = drug & event, b = drug - a, c = event - a, d = N_total - a - b - c
  ROR           (a/b)/(c/d), 95% CI exp(ln ROR +/- 1.96*sqrt(1/a+1/b+1/c+1/d))
  signal        a >= 3 and lower 95% CI > 1
  calibrated    above_neg_control_band = signal AND lower CI > highest upper CI among the
                negative controls (amoxicillin, levothyroxine, atorvastatin) for that event

API calls per ingredient: 4+ (drug total; per-PT counts among drug & any target PT, with
per-PT fallbacks if the 999-term list is truncated; receivedate histograms for each composite
-> composite totals + seasonality).
Background: 3 calls. Responses cached in data/raw/openfda/cache/.

Usage:
  uv run python scripts/faers_heat_signals.py [--extra data/processed/system_hidden_drug_candidates.csv]
Outputs: data/processed/faers_heat_signals.csv, data/processed/faers_heat_seasonality.csv
"""
import argparse, csv, math, os, sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from openfda_common import INGREDIENTS, PROCESSED, get, net_calls  # noqa: E402

EVENT = "https://api.fda.gov/drug/event.json"
HEAT_PTS = ["HEAT STROKE", "HYPERTHERMIA", "HEAT EXHAUSTION", "HEAT ILLNESS",
            "BODY TEMPERATURE INCREASED", "ANHIDROSIS", "HYPOHIDROSIS"]
FLUID_PTS = ["DEHYDRATION", "HYPONATRAEMIA", "ACUTE KIDNEY INJURY"]
ALL_PTS = HEAT_PTS + FLUID_PTS
PT_FIELD = "patient.reaction.reactionmeddrapt.exact"
HEAT_CLAUSE = PT_FIELD + ":(" + " ".join(f'"{p}"' for p in HEAT_PTS) + ")"
ALL_CLAUSE = PT_FIELD + ":(" + " ".join(f'"{p}"' for p in ALL_PTS) + ")"
HEAT_COMPOSITE = "HEAT COMPOSITE BROAD (any of 7 heat PTs)"
# Narrow composite drops BODY TEMPERATURE INCREASED (mostly fever) and HYPERTHERMIA (mostly
# NMS / serotonin syndrome / malignant hyperthermia), which made negative controls look positive.
SPECIFIC_PTS = ["HEAT STROKE", "HEAT EXHAUSTION", "HEAT ILLNESS", "ANHIDROSIS", "HYPOHIDROSIS"]
SPECIFIC_CLAUSE = PT_FIELD + ":(" + " ".join(f'"{p}"' for p in SPECIFIC_PTS) + ")"
HEAT_SPECIFIC = "HEAT COMPOSITE SPECIFIC (heat stroke/exhaustion/illness, an-/hypohidrosis)"
COMPOSITES = [(HEAT_SPECIFIC, SPECIFIC_CLAUSE), (HEAT_COMPOSITE, HEAT_CLAUSE)]
CAVEAT = "warning signal, not proof"


def drug_clause(terms):
    parts = [f'patient.drug.openfda.generic_name:"{t}"' for t in terms]
    return parts[0] if len(parts) == 1 else "(" + " ".join(parts) + ")"


def total(search=None):
    p = {"limit": 1}
    if search:
        p["search"] = search
    d = get(EVENT, p)
    return 0 if d.get("not_found") else d["meta"]["results"]["total"]


def pt_counts(search):
    # limit=1000 is refused without an API key (403 API_KEY_MISSING); 999 is accepted.
    d = get(EVENT, {"search": search, "count": PT_FIELD, "limit": 999})
    res = d.get("results", [])
    got = {r["term"].upper(): r["count"] for r in res}
    out = {}
    for p in ALL_PTS:
        if p in got or len(res) < 999:
            out[p] = got.get(p, 0)
        else:  # list truncated and PT not in it: ask directly
            out[p] = total(search + f' AND {PT_FIELD}:"{p}"')
    return out


def date_hist(search):
    d = get(EVENT, {"search": search, "count": "receivedate"})
    months = defaultdict(int)
    for r in d.get("results", []):
        months[int(r["time"][4:6])] += r["count"]
    return sum(months.values()), months


def ror(a, n_drug, n_event, n_total):
    b, c = n_drug - a, n_event - a
    d = n_total - a - b - c
    if min(a, b, c, d) <= 0:
        return None, None, None
    r = (a / b) / (c / d)
    se = math.sqrt(1 / a + 1 / b + 1 / c + 1 / d)
    return r, math.exp(math.log(r) - 1.96 * se), math.exp(math.log(r) + 1.96 * se)


def load_extra(path):
    """Read extra drug classes from another agent's CSV. Columns tried: class/drug_class/drug, term/terms/ingredient/generic_name."""
    out = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            low = {k.lower().strip(): (v or "").strip() for k, v in row.items() if k}
            cls = low.get("class") or low.get("drug_class") or low.get("drug") or low.get("name")
            terms = low.get("terms") or low.get("ingredients") or low.get("ingredient") or low.get("generic_name") or cls
            if not cls:
                continue
            for t in [t.strip() for t in terms.replace(";", "|").replace(",", "|").split("|") if t.strip()]:
                out.append((f"hidden candidate: {cls}", t.lower(), "hidden_candidate"))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--extra", help="CSV of extra (hidden-candidate) drugs to score")
    ap.add_argument("--max-calls", type=int, default=600)
    args = ap.parse_args()

    ingredients = list(INGREDIENTS)
    if args.extra and os.path.exists(args.extra):
        known = {t for _, t, _ in ingredients}
        ingredients += [x for x in load_extra(args.extra) if x[1] not in known]

    n_total = total()
    bg_pt = pt_counts(ALL_CLAUSE)
    bg_comp = {name: date_hist(cl) for name, cl in COMPOSITES}
    bg_event = dict(bg_pt, **{name: v[0] for name, v in bg_comp.items()})

    # units: each ingredient, plus each class pooled (OR of its ingredients)
    units = [(c, t, role, "ingredient", [t]) for c, t, role in ingredients]
    by_class = defaultdict(list)
    roles = {}
    for c, t, role in ingredients:
        by_class[c].append(t)
        roles[c] = role
    units += [(c, "ALL: " + "+".join(ts), roles[c], "class", ts) for c, ts in by_class.items()
              if len(ts) > 1 and roles[c] != "negative_control"]

    sig_rows, seas_rows = [], []
    for cls, label, role, level, terms in units:
        dc = drug_clause(terms)
        try:
            n_drug = total(dc)
            pts = pt_counts(dc + " AND " + ALL_CLAUSE)
            comp = {name: date_hist(dc + " AND " + cl) for name, cl in COMPOSITES}
        except RuntimeError as e:
            print("stopping:", e, file=sys.stderr)
            break
        events = dict(pts, **{name: v[0] for name, v in comp.items()})
        for ev in [HEAT_SPECIFIC, HEAT_COMPOSITE] + ALL_PTS:
            a = events[ev]
            r, lo, hi = ror(a, n_drug, bg_event[ev], n_total) if n_drug else (None, None, None)
            sig_rows.append({
                "drug_class": cls, "ingredient": label, "level": level, "role": role,
                "event": ev, "event_group": "heat composite" if ev.startswith("HEAT COMPOSITE") else ("heat PT" if ev in HEAT_PTS else "fluid/kidney PT"),
                "n_cases": a, "n_reports_drug": n_drug, "n_reports_event": bg_event[ev], "n_reports_total": n_total,
                "ror": f"{r:.3f}" if r else "", "ror_ci_low": f"{lo:.3f}" if lo else "", "ror_ci_high": f"{hi:.3f}" if hi else "",
                "signal": "yes" if (r and a >= 3 and lo > 1) else "no",
                "caveat": CAVEAT,
            })
        for name, (n_c, months) in comp.items():
            bg_n, bg_m = bg_comp[name]
            for m in range(1, 13):
                seas_rows.append({
                    "drug_class": cls, "ingredient": label, "level": level, "role": role, "composite": name, "month": m,
                    "n_heat_reports": months.get(m, 0), "n_heat_reports_drug_total": n_c,
                    "share_of_drug_heat_reports": f"{months.get(m, 0) / n_c:.4f}" if n_c else "",
                    "n_heat_reports_all_drugs": bg_m.get(m, 0),
                    "share_of_all_heat_reports": f"{bg_m.get(m, 0) / bg_n:.4f}",
                    "caveat": CAVEAT + "; month = FDA receivedate, not event date",
                })
        print(f"{label[:40]:40s} N={n_drug:>8} heat={events[HEAT_SPECIFIC]:>5}/{events[HEAT_COMPOSITE]:>5}  calls={net_calls[0]}", file=sys.stderr)

    for name, (bg_n, bg_m) in bg_comp.items():
        for m in range(1, 13):
            seas_rows.append({
                "drug_class": "ALL DRUGS", "ingredient": "ALL", "level": "background", "role": "background",
                "composite": name, "month": m,
                "n_heat_reports": bg_m.get(m, 0), "n_heat_reports_drug_total": bg_n,
                "share_of_drug_heat_reports": f"{bg_m.get(m, 0) / bg_n:.4f}",
                "n_heat_reports_all_drugs": bg_m.get(m, 0), "share_of_all_heat_reports": f"{bg_m.get(m, 0) / bg_n:.4f}",
                "caveat": CAVEAT + "; month = FDA receivedate, not event date",
            })

    # Calibration: per event, the highest upper CI among negative controls. A signal whose lower CI
    # clears that band is less likely to be generic reporting noise (age, polypharmacy).
    band = {}
    for r in sig_rows:
        if r["role"] == "negative_control" and r["ror_ci_high"]:
            band[r["event"]] = max(band.get(r["event"], 0), float(r["ror_ci_high"]))
    for r in sig_rows:
        r["neg_control_band_max"] = f"{band[r['event']]:.3f}" if r["event"] in band else ""
        r["above_neg_control_band"] = "yes" if (r["signal"] == "yes" and r["event"] in band
                                                 and float(r["ror_ci_low"]) > band[r["event"]]) else "no"
        r["caveat"] = r.pop("caveat")

    os.makedirs(PROCESSED, exist_ok=True)
    for name, rows in [("faers_heat_signals.csv", sig_rows), ("faers_heat_seasonality.csv", seas_rows)]:
        with open(os.path.join(PROCESSED, name), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    print(f"N_total={n_total} composites={ {k: v[0] for k, v in bg_comp.items()} } bg_pts={bg_pt} network_calls={net_calls[0]}", file=sys.stderr)


if __name__ == "__main__":
    main()
