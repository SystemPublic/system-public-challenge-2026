"""World Bank data: indicator search and values. Indicators API v2 first (retries; it is often slow),
then the Data360 API, which serves the same WDI series plus jobs, gender, informality and more."""
import time

from tools._http import get_json

V2 = "https://api.worldbank.org/v2"
D360 = "https://data360api.worldbank.org/data360"
MAX_ROWS = 200
_v2_down_until = 0.0


def search_worldbank_indicators(text: str, k: int = 10) -> list:
    """Find World Bank indicators by meaning (e.g. "informal employment", "health spending per capita").
    Returns ids to pass to get_worldbank_data, with names and the database each comes from."""
    try:
        hits = get_json(f"{D360}/searchv2", post={"search": text, "top": min(k, 25), "select":
                        "series_description/idno, series_description/name, series_description/database_id"})["value"]
        return [{"id": h["series_description"]["idno"], "name": h["series_description"]["name"],
                 "database": h["series_description"]["database_id"]} for h in hits]
    except RuntimeError:
        rows = get_json(f"{V2}/indicator", {"format": "json", "source": 2, "per_page": 2000}, timeout=30, tries=3)[1]
        return [{"id": r["id"], "name": r["name"], "database": "WB_WDI"}
                for r in rows if text.lower() in r["name"].lower()][:k]


def get_worldbank_data(indicator_id: str, countries: list[str] | None = None, year_from: int | None = None,
                       year_to: int | None = None) -> dict:
    """Values of one World Bank indicator by country and year, newest first (max 200 rows, with the total).
    indicator_id: a WDI code like "SL.UEM.TOTL.ZS" or an id from search_worldbank_indicators. countries: ISO3
    codes like ["KEN", "NGA"]; omit for all countries (then give a year range)."""
    global _v2_down_until
    if "." in indicator_id and time.time() >= _v2_down_until:
        params = {"format": "json", "per_page": 1000}
        if year_from or year_to:
            params["date"] = f"{year_from or 1960}:{year_to or time.localtime().tm_year}"
        try:
            meta, rows = get_json(f"{V2}/country/{';'.join(countries or ['all'])}/indicator/{indicator_id}",
                                  params, timeout=6, tries=1)
            rows = [{"country": r["countryiso3code"] or r["country"]["id"], "year": int(r["date"]), "value": r["value"]}
                    for r in rows if r["value"] is not None]
            return _result(indicator_id, "worldbank_v2", rows)
        except (RuntimeError, ValueError, TypeError):
            _v2_down_until = time.time() + 300  # skip v2 for 5 minutes, Data360 answers meanwhile
    if "." in indicator_id:
        indicator_id = "WB_WDI_" + indicator_id.replace(".", "_")
    params = {"DATABASE_ID": "_".join(indicator_id.split("_")[:2]), "INDICATOR": indicator_id}
    if countries:
        params["REF_AREA"] = ",".join(countries)
    if year_from:
        params["timePeriodFrom"] = str(year_from)
    if year_to:
        params["timePeriodTo"] = str(year_to)
    data = get_json(f"{D360}/data", params, timeout=30, tries=2)
    rows = []
    for r in data["value"]:
        if r["OBS_VALUE"] is None:
            continue
        row = {"country": r["REF_AREA"], "year": int(r["TIME_PERIOD"][:4]), "value": float(r["OBS_VALUE"])}
        dims = [r.get(d) for d in ("SEX", "AGE", "URBANISATION", "COMP_BREAKDOWN_1", "COMP_BREAKDOWN_2", "COMP_BREAKDOWN_3")]
        if any(d not in (None, "_T", "_Z") for d in dims):
            row["breakdown"] = ",".join(d for d in dims if d not in (None, "_T", "_Z"))
        rows.append(row)
    return _result(indicator_id, "data360", rows, data.get("count"))


def _result(indicator_id, source, rows, total=None):
    rows.sort(key=lambda r: (-r["year"], r["country"]))
    return {"indicator": indicator_id, "source": source, "total": total or len(rows), "shown": min(len(rows), MAX_ROWS),
            "rows": rows[:MAX_ROWS]}
