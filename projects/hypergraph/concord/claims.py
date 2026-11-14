"""The claim register: preregistered hypotheses, then outcomes.

The method follows the lab's inquiry practice (warrants, prediction before
data, independent criticism). Each hypothesis is registered BEFORE the city
data are queried for it. Registration fixes the statement, the graph evidence,
the prediction, and what would count as support or refutation. The register
file is hashed and committed, so the order "prediction, then data" can be
shown from git history. An outcome is written later and scored against the
registered prediction. A registered claim is never edited; a changed plan is
a new registration that names the one it replaces (`supersedes`).

Kinds (the challenge's three, plus the common middle):
  confirmation  graph and city data are expected to agree
  conflict      graph and city data are expected (or found) to disagree
  bridge        a link neither source holds alone, composed from several
  reproduction  a published number (usually from a government report built on
                open data) recomputed from the same data; `target` names it.
                confirmed = reproduced within the registered tolerance under the
                primary reading of the method; contested = not reproduced under
                any registered reading; unsettled = the primary reading misses
                but another reading reproduces it. The share of other readings
                that reproduce it is reported as method sensitivity.
Verdicts (set by the outcome, not the registration):
  confirmed     same direction, city interval excludes zero
  contested     opposite direction, city interval excludes zero
  unsettled     city interval includes zero, or the design cannot separate
                the hypothesis from a named alternative (the usual case)
  bridged       every link of the chain is at least `confirmed` or `unsettled`
                with the right sign, and the composed path is reported
  no_test       the data could not address the question

Stance: a number in [-1, 1] summarising agreement of the city evidence with
the research direction, with an interval. It is computed from the city effect
and its interval on a standardised scale (see `stance()`), so a claim with a
wide interval spreads across the middle of the dashboard's strip instead of
being forced into a box.

CLI:
  python -m concord.claims list
  python -m concord.claims export      -> viz/data/claims.json
  python -m concord.claims check       (validates files, reports hash mismatches)
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REG = ROOT / "claims" / "registered"
OUT = ROOT / "claims" / "outcomes"

KINDS = {"confirmation", "conflict", "bridge", "reproduction"}
VERDICTS = {"confirmed", "contested", "unsettled", "bridged", "no_test"}

REGISTER_FIELDS = {
    "id": "short slug, e.g. heat-shootings",
    "kind": "confirmation | conflict | bridge | reproduction",
    "target": "for reproductions: {report, agency, date, url, location, number, definition, data_used, data_access}",
    "statement": "one sentence, the hypothesis as tested",
    "graph_evidence": "list of {relationship_id|association_id, concepts, n_findings, n_studies, direction, summary, pubmed_ids}",
    "literature": "list of {citation, doi, finding} beyond the graph",
    "prediction": "{direction: +|-|0, magnitude: text with a range, support_if: text, refute_if: text}",
    "plan": "the analysis, data sets, unit, model, before any city query",
    "alternatives": "named rival explanations the design should separate",
    "prior": "0-1, registrant's probability that the outcome will be 'confirmed'",
    "registrant": "agent or person",
    "chain": "for bridges: ordered list of link claim ids",
}

OUTCOME_FIELDS = {
    "id": "same as registration",
    "verdict": "confirmed | contested | unsettled | bridged | no_test",
    "city_effect": "{label, estimate, lo, hi, scale: e.g. 'IRR per 5C', null: 0 or 1, n}",
    "graph_effect": "{label, estimate, lo, hi, scale, null} summarising the research side if comparable",
    "sources": "list of source records (socrata/noaa/sysgraph/other) with versions",
    "prediction_scored": "hit | miss | partial, with a sentence",
    "settle": "what information would settle the remaining disagreement",
    "research_needed": "list of {question, data, design, priority}",
    "figures": "list of repo-relative paths",
    "notes": "plain prose",
    "critique": "optional: independent critic's report path and the answer",
}


def _hash(d: dict) -> str:
    d = {k: v for k, v in d.items() if k not in ("sha256", "registered_at")}
    return hashlib.sha256(json.dumps(d, sort_keys=True).encode()).hexdigest()


def register(rec: dict, *, overwrite: bool = False) -> Path:
    missing = [k for k in ("id", "kind", "statement", "prediction", "plan") if k not in rec]
    if missing:
        raise ValueError(f"registration missing {missing}")
    if rec["kind"] not in KINDS:
        raise ValueError(f"kind must be one of {KINDS}")
    REG.mkdir(parents=True, exist_ok=True)
    f = REG / f"{rec['id']}.json"
    if f.exists() and not overwrite:
        raise FileExistsError(f"{f} exists; registrations are not edited. Register a new id with 'supersedes'.")
    if (OUT / f"{rec['id']}.json").exists():
        raise RuntimeError("an outcome already exists for this id; registration must precede the outcome")
    rec = dict(rec)
    rec["registered_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    rec["sha256"] = _hash(rec)
    f.write_text(json.dumps(rec, indent=1, ensure_ascii=False))
    return f


def outcome(rec: dict) -> Path:
    if rec.get("verdict") not in VERDICTS:
        raise ValueError(f"verdict must be one of {VERDICTS}")
    reg = REG / f"{rec['id']}.json"
    if not reg.exists():
        raise FileNotFoundError(f"no registration for {rec['id']}; register first")
    r = json.loads(reg.read_text())
    if r.get("sha256") != _hash(r):
        raise RuntimeError(f"registration {reg} was edited after hashing")
    OUT.mkdir(parents=True, exist_ok=True)
    rec = dict(rec)
    rec["registration_sha256"] = r["sha256"]
    rec["decided_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    rec["stance"] = stance(rec.get("city_effect"), r.get("prediction", {}).get("direction", "+"))
    f = OUT / f"{rec['id']}.json"
    f.write_text(json.dumps(rec, indent=1, ensure_ascii=False))
    return f


PRECEDENCE = """Verdict precedence (fixed 12 Nov 2026 after the first critique round):
1. The registration's own support_if and refute_if decide the verdict when they are met:
   support_if met -> confirmed; refute_if met -> contested (for a conflict-kind claim the
   roles are as registered). This holds even when the city interval includes zero.
2. When neither is met, the verdict is unsettled.
3. When the registered test could not be run as planned, the verdict is no_test, whatever
   secondary results exist; secondary results are reported in notes.
4. A measure chosen after the data were seen never decides a verdict. It is reported as
   exploratory, and may be registered as a new claim.
5. A bridge's stance is the stance of its weakest link (the link with the lowest value),
   since a composed estimate can agree in sign when every link disagrees.
6. Stance is null when the city effect has no null value that expresses the research
   direction (for example a raw proportion with null 0).
7. A bridge with an endpoint test (a composed prediction checked against data not used
   to build it) gets the verdict `bridged` when its registered endpoint condition is met.
   Its stance is the agreement of the endpoint with the composed prediction, from the
   standardised difference z: value = 2*exp(-z^2/2) - 1 (z = 0 gives +1, |z| = 1.18 gives
   0, |z| = 2.5 gives -0.91). Rule 5 applies only to bridges without an endpoint test.
   (Added 12 Nov 2026 in commit 3d8ac0d at 16:12:16, after the outcomes of the first two
   endpoint-tested bridges, bridge-crz-injury-crashes and bridge-heat-shootings-ems, had been
   decided and committed in f024acb at 16:11:46. For those two claims the verdict label
   `bridged` and the endpoint-agreement stance were therefore chosen after the data were seen.
   Under rule 4 they decide nothing for those claims; the outcome of bridge-crz-injury-crashes
   records this in `stance_rule_note`. Later registrations, such as
   bridge-crz-injury-crashes-v2, name rules 7 and 8 before their data are queried.)
8. An endpoint test must discriminate. Let z_chain and z_null be the standardised
   distances of the endpoint from the composed prediction and from no effect. The test
   discriminates when D = z_null^2 - z_chain^2 >= 4 (a likelihood ratio of about 7 in
   favour of the chain). When it does not, the verdict is `unsettled`, however well the
   endpoint matches. The rule 7 stance is multiplied by 1 - exp(-max(D,0)/2), so a test
   that cannot tell the chain from no effect sits near the middle of the strip.
   (Added 12 Nov 2026 after the bridge referee showed that a near-zero composed
   prediction would have passed with probability above 0.99.)
9. The procedure is fixed with the registration. The analysis script, the number of
   resampling draws and the random seed are committed with the registration or before it,
   and the registration names the commit. A verdict cannot turn on a part of the procedure
   that was left open. When a condition on a resampled bound is met under some seeds, or
   some numbers of draws, and not under others, it is neither met nor unmet and rule 2
   applies. The check is a re-run with at least ten times the registered draws and with
   other seeds.
   (Added 13 Nov 2026, after the data, in answer to the referee of retimed-daytime-burglary,
   whose refutation bound was 0.9525 against a threshold of 0.95 with the one seed run, above
   0.95 in 62% of 40 other seeds and 0.9509 with 50,000 draws. Applied to decided claims it
   changes that verdict only, from contested to unsettled, as the referee recommended. The
   referees of 13 November found that most analysis scripts were first committed with their
   outcomes; for those claims the order of model and data rests on the plan text and on file
   times, which critique/ANSWERS.md records, and no verdict is changed on that ground. The
   requirement to commit the script binds registrations made after this rule.)
10. A condition written on a point estimate alone (a threshold or a band with no condition
   on the interval) still decides the verdict under rule 1. The outcome then reports the
   estimate's interval beside the threshold, and when the interval crosses the threshold
   `prediction_scored` and the notes say that the condition was met or missed within
   sampling error. Registrations made after this rule state their conditions on interval
   bounds.
   (Added 13 Nov 2026, after the data. The referees of 13 November found conditions met or
   missed by less than the sampling error in further-datacentre-share-manhattan-v2 (inside
   a band by 0.011 points), graph-confounders-surftemp-ed (outside by 0.09),
   graph-confounders-commute-obesity, transfer-chicago-weekday-pattern (threshold 13.1,
   variants 12.4 to 16.1) and graph-concordance-matrix (66.1% against 60%, lower bound
   59.6%), and recommended keeping each verdict except the last. The rule changes no
   verdict; it requires the margin to be stated, which the revisions of 13 November do.)
11. A registered placebo (the same design applied where or when no effect can exist) is part
   of the test. When the placebo itself meets support_if, or the estimate does not
   discriminate from the placebo under the rule 8 measure with the placebo as the null, the
   design cannot tell an effect from its own bias, and the verdict is unsettled.
   (Added 13 Nov 2026, after the data, in answer to the referee of rlc-expansion-rearend,
   whose estimate was 1.327 (1.061 to 1.650) while the placebo year gave 1.250 (lower bound
   1.052, meeting support_if), D = -2.3 against the placebo. It changes that verdict only,
   from confirmed to unsettled.)
12. A before-and-after or difference-in-differences registration names a placebo (the same
   estimator with the intervention date moved into the pre-period, or applied to untreated
   units) as part of the test, so that rule 11 can apply.
   (Added 13 Nov 2026, after the turn-calming referee found that an unregistered placebo
   would have made two confirmations unsettled. It binds later registrations only and
   changes no verdict; under rule 4 an unregistered placebo decides nothing.)
13. For a claim registered with direction 0 (a prediction of no effect, with equivalence bounds),
   rule 11 is read in reverse. A placebo that also lies inside the bounds is the expected result
   and does not unsettle the verdict. The verdict is unsettled when the placebo falls outside
   the bounds, because the design then shows an effect where none can exist.
   (Added 14 Nov 2026, after the data, in answer to the referee of moon-full-emergencies, who
   noted that rule 11 read literally gives unsettled because the placebo also meets support_if,
   and recommended confirmed. It changes no verdict.)"""


def endpoint_stance(z: float, z_null: float | None = None) -> dict:
    v = 2 * math.exp(-z * z / 2) - 1
    out = {"lo": None, "hi": None, "z": round(z, 2), "rule": 7}
    if z_null is not None:
        D = z_null * z_null - z * z
        out["D"] = round(D, 2)
        out["discriminates"] = D >= 4
        v = v * (1 - math.exp(-max(D, 0) / 2))
        out["rule"] = "7+8"
    out["value"] = round(v, 3)
    return out


def revise(cid: str, changes: dict, reason: str, critique: str | None = None) -> Path:
    """Change an outcome after criticism, keeping the earlier version in `history`.
    The registration is untouched. `changes` replaces top-level outcome fields."""
    f = OUT / f"{cid}.json"
    old = json.loads(f.read_text())
    hist = old.pop("history", [])
    hist.append({k: old.get(k) for k in ("verdict", "city_effect", "stance", "decided_at", "prediction_scored")})
    new = {**old, **changes}
    new["history"] = hist
    new["revision"] = {"reason": reason, "critique": critique, "revised_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                       "rule": "concord.claims.PRECEDENCE"}
    reg = json.loads((REG / f"{cid}.json").read_text())
    if "stance" not in changes:
        new["stance"] = stance(new.get("city_effect"), reg.get("prediction", {}).get("direction", "+"))
    f.write_text(json.dumps(new, indent=1, ensure_ascii=False))
    return f


def bridge_stance(chain_ids: list[str]) -> dict | None:
    """Weakest-link stance for a bridge (rule 5)."""
    vals = []
    for c in chain_ids:
        o = OUT / f"{c}.json"
        if o.exists():
            s = json.loads(o.read_text()).get("stance")
            if s and s.get("value") is not None:
                vals.append((s["value"], c, s))
    if not vals:
        return None
    v, c, s = min(vals)
    return {**s, "from_link": c}


def stance(eff: dict | None, predicted: str = "+") -> dict | None:
    """Map a city effect and interval onto [-1, 1] agreement with the predicted sign.

    For ratio scales (null == 1) the log is taken. The estimate is divided by
    the half-width of its interval (a z-like value) and squashed with tanh(z/2),
    so a precise effect in the predicted direction approaches +1, a precise
    opposite effect approaches -1, and an effect whose interval spans zero
    sits near the middle with an interval that crosses it.
    """
    if not eff or eff.get("estimate") is None:
        return None
    null = eff.get("null", 0)
    tr = (lambda x: math.log(x)) if null == 1 else (lambda x: x)
    try:
        e = tr(eff["estimate"]) - tr(null) if null == 1 else eff["estimate"] - null
        lo = tr(eff["lo"]) - (tr(null) if null == 1 else null) if eff.get("lo") is not None else None
        hi = tr(eff["hi"]) - (tr(null) if null == 1 else null) if eff.get("hi") is not None else None
    except (ValueError, TypeError):
        return None
    sign = {"+": 1, "-": -1, "0": 0}.get(str(predicted), 1)
    if sign == 0:  # predicted null: agreement is closeness to zero
        if lo is None or hi is None:
            return None
        width = max(hi - lo, 1e-9)
        s = 1 - min(1, abs(e) / width)
        return {"value": round(s, 3), "lo": round(s - 0.2, 3), "hi": round(min(1, s + 0.2), 3)}
    if lo is None or hi is None:
        return {"value": round(math.tanh(sign * e * 2), 3), "lo": None, "hi": None}
    se = max((hi - lo) / 3.92, 1e-12)
    z, zlo, zhi = sign * e / se, sign * lo / se, sign * hi / se
    vals = sorted([math.tanh(zlo / 2), math.tanh(zhi / 2)])
    return {"value": round(math.tanh(z / 2), 3), "lo": round(vals[0], 3), "hi": round(vals[1], 3), "z": round(z, 2)}


def load_all() -> list[dict]:
    out = []
    for f in sorted(REG.glob("*.json")):
        r = json.loads(f.read_text())
        r["hash_ok"] = r.get("sha256") == _hash(r)  # before adding derived keys
        o = OUT / f.name
        r["outcome"] = json.loads(o.read_text()) if o.exists() else None
        out.append(r)
    return out


def export(path: Path | None = None) -> Path:
    path = path or ROOT / "viz" / "data" / "claims.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"generated": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "claims": load_all()}
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False))
    return path


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "list"
    if cmd == "list":
        for c in load_all():
            o = c["outcome"] or {}
            print(f"{c['id']:32s} {c['kind']:13s} {o.get('verdict', '(open)'):10s} prior={c.get('prior')} hash={'ok' if c['hash_ok'] else 'EDITED'}")
    elif cmd == "export":
        print(export())
    elif cmd == "check":
        bad = [c["id"] for c in load_all() if not c["hash_ok"]]
        print("all registrations intact" if not bad else f"edited after registration: {bad}")
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv)
