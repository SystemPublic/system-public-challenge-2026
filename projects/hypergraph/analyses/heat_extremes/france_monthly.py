"""Can monthly police counts for Paris tell a downturn from a rise in a heat-wave month?

Reads the Interior Ministry's monthly series by departement (Etat 4001, index 7, 'Autres coups et
blessures volontaires', January 1996 to August 2022; data.gouv.fr) for Paris (75) and metropolitan France.
The heat-wave months (August 2003, June and July 2019, June to August 2022) and 2020 are left out,
and the month-to-month noise of the remaining summer months is measured: the residual standard
deviation of log counts after year and month terms. The size a heat wave could have in a monthly
count is computed from the US curve in curves.csv. The heat-wave months are not read.

Run with a Python that has openpyxl: python3 -m analyses.heat_extremes.france_monthly
Writes data/derived/heat_extremes/france_monthly_noise.json
"""
import json
from pathlib import Path

import numpy as np
import openpyxl

ROOT = Path(__file__).resolve().parents[2]
RAW = Path.home() / "opt" / "nyc-concordance" / "heat_extremes" / "france" / "tableaux-4001-ts.xlsx"
TARGET = {(2003, 8), (2019, 6), (2019, 7), (2022, 6), (2022, 7), (2022, 8)}


def series(wb, sheet):
    rows = list(wb[sheet].iter_rows(values_only=True))
    head = rows[0]
    r7 = next(r for r in rows[1:] if r[0] == 7)
    return {(int(h[1:5]), int(h[6:8])): v for h, v in zip(head[2:], r7[2:]) if h and v is not None}


def noise(s):
    keys = [k for k in s if k not in TARGET and k[0] != 2020 and 2000 <= k[0] <= 2022]
    years, months = sorted({k[0] for k in keys}), list(range(1, 13))
    X = np.zeros((len(keys), len(years) + 11))
    for i, (y, m) in enumerate(keys):
        X[i, years.index(y)] = 1
        if m > 1:
            X[i, len(years) + m - 2] = 1
    yv = np.log([s[k] for k in keys])
    b = np.linalg.lstsq(X, yv, rcond=None)[0]
    res = yv - X @ b
    summer = np.array([k[1] in (6, 7, 8) for k in keys])
    dof = len(keys) - X.shape[1]
    return {"months_used": len(keys), "resid_sd_all": float(np.sqrt((res ** 2).sum() / dof)), "resid_sd_summer": float(res[summer].std(ddof=1) * np.sqrt(len(keys) / dof)),
            "mean_monthly_count_summer": float(np.mean([s[k] for k in keys if k[1] in (6, 7, 8)]))}


def main():
    wb = openpyxl.load_workbook(RAW, read_only=True)
    out = {"source": "https://www.data.gouv.fr/datasets/chiffres-departementaux-mensuels-relatifs-aux-crimes-et-delits-enregistres-par-les-services-de-police-et-de-gendarmerie-depuis-janvier-1996 (tableaux-4001-ts.xlsx, 31 Oct 2022)",
           "index": "7 Autres coups et blessures volontaires criminels ou correctionnels", "left_out": sorted(TARGET)}
    for name, sheet in (("paris_75", "75"), ("france_metro", "France_Métro")):
        out[name] = noise(series(wb, sheet))
    # effect sizes: 13 heat-wave days of 31 (August 2003). Rise: the US pooled curve from 23-26 C to 35-38 C. Downturn: those days fall back to the 23-26 C rate or 5% below it.
    rise = 1.15 / 1.03
    out["expected_monthly_log_effect"] = {"rise": float(np.log(1 + 13 / 31 * (rise - 1))), "downturn": float(np.log(1 + 13 / 31 * (0.95 - 1)))}
    gap = out["expected_monthly_log_effect"]["rise"] - out["expected_monthly_log_effect"]["downturn"]
    for name in ("paris_75", "france_metro"):
        sd = out[name]["resid_sd_summer"]
        out[name]["D_one_month"] = float((gap / sd) ** 2)
        # the five other target months had waves of about six days, so their gap is 6/13 of August 2003's
        out[name]["D_six_months"] = float((gap / sd) ** 2 * (1 + 5 * (6 / 13) ** 2))
    (ROOT / "data" / "derived" / "heat_extremes" / "france_monthly_noise.json").write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
