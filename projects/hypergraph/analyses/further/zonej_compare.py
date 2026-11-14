import json, numpy as np, pandas as pd
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageCms
ROOT = Path(__file__).resolve().parents[2]
R = json.loads((ROOT/"data/derived/further/zonej_results.json").read_text())
G = pd.read_csv(ROOT/"data/derived/further/zonej_goldbook.csv")
D = pd.read_csv(ROOT/"data/derived/further/zonej_daily.csv", parse_dates=["date"])
rng = np.random.default_rng(7)
rJ = pd.Series({int(k): v for k, v in R["N.Y.C."]["annual_norm_twh"].items()})*1000   # GWh
rK = pd.Series({int(k): v for k, v in R["LONGIL"]["annual_norm_twh"].items()})*1000
dJ = pd.Series({int(k): v for k, v in R["N.Y.C."]["design_day_peak_mw"].items()})
E = G[G.measure == "energy_gwh"]
out = []
for e in range(2021, 2026):
    g = E[E.edition == e].set_index("year").J; b = e - 1
    for t in range(b+1, 2026):
        out.append(dict(edition=e, base=b, target=t, h=t-b, F_growth=100*(g[t]/g[b]-1), R_growth=100*(rJ[t]/rJ[b]-1)))
c = pd.DataFrame(out); c["err_pp"] = c.F_growth - c.R_growth
# exploratory: against Gold Book's own later actuals (2026 edition historical, through 2025)
g26 = E[E.edition == 2026].set_index("year").J
c["A_growth"] = [100*(g26[t]/g26[b]-1) for t, b in zip(c.target, c.base)]
c["err_vs_goldbook_actual_pp"] = c.F_growth - c.A_growth
c.to_csv(ROOT/"data/derived/further/zonej_goldbook_vs_realised.csv", index=False)
h3 = c[c.h == 3]
vals = h3.err_pp.values
bs = [rng.choice(vals, len(vals)).mean() for _ in range(5000)]
res = {"horizon3_n_editions": int(len(vals)), "horizon3_editions": h3.edition.tolist(), "horizon3_errors_pp": vals.round(2).tolist(),
       "horizon3_mean_pp": float(vals.mean()), "horizon3_boot_lo": float(np.percentile(bs, 2.5)), "horizon3_boot_hi": float(np.percentile(bs, 97.5)),
       "all_pairs_mean_err_pp": float(c.err_pp.mean()), "by_h": c.groupby("h").err_pp.agg(["mean","count"]).round(2).to_dict("index"),
       "exploratory_vs_goldbook_actual_h3_mean_pp": float(h3.err_vs_goldbook_actual_pp.mean()), "exploratory_vs_goldbook_actual_h3": h3.err_vs_goldbook_actual_pp.round(2).tolist()}
# validation: PAL raw annual energy vs Gold Book historical (2026 edition)
raw = D[D.zone == "N.Y.C."].groupby(D.date.dt.year).energy_mwh.agg(["sum","count"])
val = pd.DataFrame({"pal_gwh": raw["sum"]/1000, "days": raw["count"], "goldbook2026_gwh": g26}).dropna()
val["pal_gwh_scaled_to_365"] = val.pal_gwh*365.25/val.days
val["ratio"] = val.pal_gwh_scaled_to_365/val.goldbook2026_gwh
res["pal_vs_goldbook_ratio"] = val.ratio.round(3).to_dict()
(ROOT/"data/derived/further/zonej_goldbook_summary.json").write_text(json.dumps(res, indent=1, default=float))
print(json.dumps(res, indent=1, default=float)); print(c.round(2).to_string())

# Figure
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
fig, ax = plt.subplots(1, 2, figsize=(10, 4.2), dpi=200)
yrs = list(range(2015, 2026))
a = ax[0]
for s, lab, col in ((rJ, "Zone J (N.Y.C.)", "#1b4f72"), (rK, "Zone K (Long Island, placebo)", "#b9770e")):
    idx = 100*s/s[2015]; a.plot(yrs, idx.values, "-", color=col, lw=1.8, label=lab)
    for y in (2020, 2021): a.plot(y, idx[y], "o", mfc="white", mec=col)
a.axvspan(2020.2, 2021.5, color="0.9", zorder=0)
a.set_ylabel("Weather-normalised annual energy, 2015 = 100"); a.set_xticks(yrs[::2]); a.legend(frameon=False, loc="lower left")
tj, tk = R["N.Y.C."]["energy"], R["LONGIL"]["energy"]
a.set_title(f"Trend (daily model, 2015-2025, pandemic days excluded)\nZone J {tj['est']:.2f}% a year (95% CI {tj['lo']:.2f} to {tj['hi']:.2f}); Zone K {tk['est']:.2f}% ({tk['lo']:.2f} to {tk['hi']:.2f})", fontsize=8.5, loc="left")
b = ax[1]
b.plot(yrs, rJ.values/1000, "-", color="#1b4f72", lw=2, label="Realised, weather-normalised (PAL load)")
cols = plt.cm.viridis(np.linspace(0.05, 0.85, 5))
for e, col in zip(range(2021, 2026), cols):
    g = E[E.edition == e].set_index("year").J; bb = e-1
    ys = [t for t in range(bb, 2026)]
    b.plot(ys, [rJ[bb]/1000*g[t]/g[bb] for t in ys], "--", color=col, lw=1.2, label=f"{e} Gold Book growth path")
b.set_ylabel("TWh a year (forecasts scaled to realised base year)"); b.set_xticks(yrs[::2]); b.legend(frameon=False, fontsize=7, loc="lower left")
b.set_title("Gold Book Zone J forecast growth against realised", fontsize=8.5, loc="left")
fig.text(0.01, 0.005, "Sources: NYISO PAL integrated real-time load (mis.nyiso.com), NOAA GHCN-Daily Central Park, NYISO Gold Book 2021-2025. Open circles: 2020-2021, partly excluded.", fontsize=6.5)
fig.tight_layout(rect=(0, 0.03, 1, 1))
f = ROOT/"figures/further/zonej_demand_growth.png"
fig.savefig(f)
im = Image.open(f).convert("RGB"); prof = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
im.save(f, icc_profile=prof, dpi=(200, 200))
