"""Timeline figure for the Red Hook lot: what each source says about Brooklyn block 555, lot 124 (348 Van Brunt St, the
inferred site of the photograph) and lot 27 (100 Sullivan St, the alternative), in order of date, ending with a crop of
Jeff Vernon's photograph of 8 Nov 2026. Events are taken from data/derived/construction2/red_hook/records.json; same-day
records of one kind are merged. NAIP entries are this agent's visual readings (inferences).
Writes figures/construction2/red_hook_timeline.png and data/derived/construction2/red_hook/timeline.csv."""
import json
import subprocess
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "data/derived/construction2/red_hook"
R = json.loads((D / "records.json").read_text())
FIG = ROOT / "figures/construction2"
ev = []


def add(d, src, text, lot="124"):
    ev.append(dict(date=pd.Timestamp(str(d)[:10]), source=src, text=text, lot=lot))


def nm(x):
    t = x.title()
    for a, b in (("Llc", "LLC"), ("L.L.C.", "LLC"), ("Lp", "LP"), ("Ddg", "DDG"), ("S3 Sb", "S3 SB"), ("Inc.", "Inc")):
        t = t.replace(a, b)
    return t


def money(x):
    x = float(x or 0)
    return f"${x/1e6:.4g}M" if x >= 1e6 else f"${x/1e3:.0f}K"


# ACRIS
for lot in ("124", "27"):
    parties = {}
    for p in R[lot]["acris_parties"]:
        parties.setdefault(p["document_id"], {}).setdefault(p["party_type"], []).append(nm(p["name"]))
    by = {}
    for m in R[lot]["acris_master"]:
        d = (m.get("document_date") or m.get("recorded_datetime"))[:10]
        if lot == "27" and d < "2019-01-01":
            continue
        t, pp = m["doc_type"], parties.get(m["document_id"], {})
        if t == "DEED":
            s = f"deed, {money(m.get('document_amt'))}, to {pp.get('2', ['?'])[0]}"
        elif t == "MTGE":
            by.setdefault(d, []).append(("M", pp.get("2", ["?"])[0], money(m.get("document_amt"))))
            continue
        elif t == "ZONE":
            s = "zoning lot description recorded"
        else:
            continue
        by.setdefault(d, []).append(s)
    for d, ss in by.items():
        txt = [x for x in ss if isinstance(x, str)]
        lenders = {}
        for x in ss:
            if isinstance(x, tuple):
                lenders.setdefault(x[1], []).append(x[2])
        txt += [("mortgages " if len(v) > 1 else "mortgage ") + " and ".join(sorted(v)) + f" from {k}" for k, v in lenders.items()]
        add(d, "ACRIS", "; ".join(txt), lot)

# DOB legacy job filings (BIS)
add("2020-10-07", "DOB filings", "legacy NB job 321598419 filed: 4 storeys, 4 units (owner DDG Conover Owner LLC)")
add("2021-09-23", "DOB filings", "NB job 321598419 plans approved; no permit was ever issued")
add("2020-05-29", "DOB filings", "legacy NB job 321591078 filed (one-family house)", "27")
add("2021-02-16", "DOB filings", "NB job 321591078 plans approved", "27")
# DOB NOW filings for lot 124
add("2021-02-12", "DOB filings", "DOB NOW plumbing, mechanical, structural, sprinkler, curb-cut filings (2021); none permitted")
add("2026-07-22", "DOB filings", "new DOB NOW NB job B01433306: 5 storeys, 8 units, under plan review")
add("2026-08-03", "DOB filings", "B01433306 construction-fence filing approved (no permit issued)")
add("2026-10-22", "DOB filings", "B01433306 filings for foundation, earthwork, excavation support, framing: under review")

# Permits
for lot in ("124", "27"):
    for p in R[lot]["dob_permits_legacy"]:
        if p.get("permit_type") == "NB":
            add(p["issuance_date"], "DOB permits", f"NB permit, {p['filing_status'].lower()}, to {p['expiration_date']}", lot)
    keep = {"Support of Excavation", "Foundation", "Structural", "Construction Fence"}
    for p in R[lot]["dobnow_permits"]:
        if p["work_type"] in keep and p["filing_reason"] == "Initial Permit":
            add(p["issued_date"], "DOB permits", f"DOB NOW {p['work_type'].lower()} permit ({p['permit_status'].lower()})", lot)
add("2026-11-08", "DOB permits", "lot 124: no permit on record in either system (as of 12 Nov 2026)")

add("2026-11-08", "COs", "no certificate of occupancy (CO) for either lot (as of 12 Nov 2026)")

for lot in ("124", "27"):
    s = {c["unique_key"]: c for c in R[lot]["complaints_311_bbl"]}
    by = {}
    for c in s.values():
        by.setdefault(c["created_date"][:10], set()).add(f"{c['complaint_type']} ({c.get('descriptor')})")
    for d, ss in by.items():
        if lot == "27" and not any("Dust" in x for x in ss):
            continue
        add(d, "311 / DOB complaints", "311: " + "; ".join(sorted(ss)), lot)

pl = R["124"]["pluto"][0]
add("2026-08-24", "PLUTO", f"PLUTO {pl.get('version')} (table updated 24 Aug 2026): vacant land (V1), 4,250 sq ft, owner {nm(pl.get('ownername'))}")
for c in R["124"]["dob_complaints"]:
    if c["date_entered"][-4:] >= "2010":
        add(pd.Timestamp(c["date_entered"]), "311 / DOB complaints",
            f"DOB complaint {c['complaint_number']}, category {c['complaint_category']}, closed {c['disposition_date']} (code {c['disposition_code']})")

for d, t in [("2011-07-05", "frontage under trees; unclear (1.0 m per pixel)"),
             ("2015-05-22", "paved yard with parked vehicles over lots 124 and 27"),
             ("2019-08-30", "bare ground; the large site to the north cleared"),
             ("2021-11-05", "bare; new building at 155 King St stands to the north"),
             ("2022-07-19", "bare ground and weeds on both lots; no structure (latest NAIP flight available)")]:
    add(d, "NAIP aerial", t)

add("2026-11-08", "Photograph", "rebar mats and foam forms, reeds grown over them (J. Vernon); lot inferred, not located by GPS")

df = pd.DataFrame(ev)
df["last"] = df.source == "Photograph"
df = df.sort_values(["last", "date", "source"]).drop(columns="last").reset_index(drop=True)
df.to_csv(D / "timeline.csv", index=False)

colors = {"ACRIS": "#1f5f99", "PLUTO": "#7a7a7a", "DOB filings": "#b35806", "DOB permits": "#d7301f",
          "COs": "#6a3d9a", "311 / DOB complaints": "#33a02c", "NAIP aerial": "#0f8b8d", "Photograph": "#111111"}
n = len(df)
fig = plt.figure(figsize=(15, 0.27 * n + 2.4), dpi=150)
ax = fig.add_axes([0.02, 0.06, 0.70, 0.88])
ax.set_xlim(0, 1); ax.set_ylim(n, -1.2); ax.axis("off")
ax.text(0, -1.0, "Brooklyn block 555: what each source says, in order of date", fontsize=12, va="center")
ax.plot([0.11, 0.11], [-0.3, n - 0.5], color="#ccc", lw=1, zorder=0)
for i, e in df.iterrows():
    c = colors[e.source]
    ax.text(0.0, i, f"{e.date:%d %b %Y}", fontsize=7.5, va="center", color="#333")
    ax.plot(0.11, i, "o" if e.lot == "124" else "D", ms=5.5, color=c, mfc=c if e.lot == "124" else "white", mew=1.3)
    ax.text(0.125, i, e.source, fontsize=7.5, va="center", color=c, weight="bold")
    ax.text(0.33, i, ("" if e.lot == "124" else "lot 27: ") + e.text, fontsize=7.5, va="center", color="#111")
ax.text(0, n + 0.1, "Filled circle: lot 124, 348 Van Brunt St (the inferred site). Open diamond: lot 27, 100 Sullivan St (the alternative); lot 27's\n"
        "records before 2019 and its parking complaints are omitted. NAIP entries are our visual readings, not measurements. Sources: ACRIS\n"
        "(8h5j-fqxa, bnx9-e6tj, 636b-3b5g), PLUTO (64uk-42ks), DOB filings (ic3t-wcy2, w9ak-ipjd), permits (ipu4-2q9a, rbx6-tga4), COs (bs8b-p36w,\n"
        "pkdm-hqz6), 311 (erm2-nwe9), all fetched 12 Nov 2026; USDA FSA NAIP 2011-2022.", fontsize=6.3, va="top", color="#444")
ph = Image.open(FIG / "red_hook_slide01.jpg").convert("RGB").crop((190, 560, 1040, 1060))
h = 0.30
pax = fig.add_axes([0.735, 0.06, 0.25, h])
pax.imshow(ph); pax.set_xticks([]); pax.set_yticks([])
pax.set_title("Last entry: 8 Nov 2026, photograph by Jeff Vernon (crop)", fontsize=7.5, loc="left")
out = FIG / "red_hook_timeline.png"
fig.savefig(out)
subprocess.run(["sips", "--embedProfile", "/System/Library/ColorSync/Profiles/sRGB Profile.icc", str(out)], capture_output=True)
print(df.to_string())
