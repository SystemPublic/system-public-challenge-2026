"""City side: NYC measures from Underlay collections, one row per area, with the record ids behind every value."""
import pandas as pd

BORO = {"MANHATTAN": "1", "BRONX": "2", "BROOKLYN": "3", "QUEENS": "4", "STATEN ISLAND": "5"}

# column -> (EHDP measure id, label)
CD_MEASURES = {
    "heat_ed_rate": (1405, "heat-stress ED visits per 100,000 (5-year, age-adjusted)"),
    "heat_hosp_rate": (1283, "heat-stress hospitalizations per 100,000 (10-year, age-adjusted)"),
    "surface_temp_f": (688, "daytime summer surface temperature (°F)"),
    "veg_cover_pct": (690, "grass and tree cover (%)"),
    "poverty_pct": (221, "residents below poverty (%)"),
    "poverty_n": (233, "residents below poverty (number)"),
    "older_alone_pct": (693, "adults 65+ living alone (%)"),
    "cold_ed_rate": (1411, "cold-related ED visits per 100,000 (5-year, age-adjusted)"),
    "asthma_ed_rate": (1199, "adult asthma ED visits per 10,000 (age-adjusted)"),
}
UHF_MEASURES = {
    "heat_hosp_rate": (540, "heat-stress hospitalizations per 100,000 (age-adjusted)"),
    "heat_ed_rate": (537, "heat-stress ED visits per 100,000 (age-adjusted)"),
    "ac_households_pct": (781, "households with air conditioning (%)"),
    "tree_canopy_pct": (708, "tree canopy cover (%)"),
    "veg_cover_pct": (690, "grass and tree cover (%)"),
    "surface_temp_f": (688, "daytime summer surface temperature (°F)"),
    "poverty_pct": (221, "residents below poverty (%)"),
}


class Frame:
    """A table of areas plus provenance for each column."""

    def __init__(self, unit, df, sources, labels):
        self.unit, self.df, self.sources, self.labels = unit, df, sources, labels


def measure(con, mid, geotype):
    """Latest single period per area for one EHDP measure. Returns value, Observation id, period label."""
    return con.execute(f"""
        select o.data->>'geographyId' as id, cast(o.data->>'value' as double) as value, o.id as record_id,
               t.data->>'label' as period
        from eh o join eh t on t.id = o.data->>'timePeriodId'
        where o.type='Observation' and o.data->>'measureId'='measure:{mid}' and o.data->>'geoType'='{geotype}'
          and o.data->>'value' is not null
        qualify row_number() over (partition by o.data->>'geographyId'
                                   order by cast(t.data->>'endYear' as int) desc,
                                            cast(t.data->>'startYear' as int) desc) = 1""").df().set_index("id")


def _eh_source(m, mid, label):
    periods = sorted(set(m["period"]))
    return {"alias": "eh", "record_type": "Observation", "record_ids": sorted(m["record_id"].tolist()),
            "measure": f"measure:{mid}", "label": label, "period": ", ".join(periods)}


def _geo_names(con, geotype):
    return con.execute(f"""select id, data->>'name' as name, data->>'borough' as borough,
        cast(data->>'areaSqKm' as double) as area_km2 from geo
        where type='Geography' and data->>'geoType'='{geotype}'""").df().set_index("id")


def districts(con):
    cols, sources, labels = {}, {}, {}
    for col, (mid, label) in CD_MEASURES.items():
        m = measure(con, mid, "CD")
        cols[col] = m["value"]
        sources[col], labels[col] = _eh_source(m, mid, label), label
    df = pd.DataFrame(cols)
    df = df[df["poverty_pct"].notna()]  # the 59 residential districts
    names = _geo_names(con, "CD")
    df = names.join(df, how="inner")

    trees = con.execute("""select 'CD:' || (data->>'communityBoard') as id, count(*) as n from trees
        where type='Tree' and data->>'status'='Alive' group by 1""").df().set_index("id")["n"]
    df["trees_alive"] = trees
    df["tree_density_per_km2"] = df["trees_alive"] / df["area_km2"]
    sources["tree_density_per_km2"] = {
        "alias": "trees", "record_type": "Tree", "record_ids": [],
        "query": "count of Tree records with status='Alive' grouped by communityBoard (CD), "
                 "divided by Geography.areaSqKm from nyc/geographies", "label": "living street trees per km²",
        "period": "2015 census"}
    labels["tree_density_per_km2"] = "living street trees per km²"

    # 311 "no heat / no hot water": complete winter seasons only; per 1,000 residents (population = poor / poverty share)
    comp = con.execute("""select data->>'communityBoard' as cb, data->>'heatSeason' as season, count(*) as n
        from complaints where type='Complaint' and data->>'heatSeason' in ('2024-25','2025-26') group by 1,2""").df()
    comp = comp[comp["cb"].str.match(r"^\d\d [A-Z ]+$", na=False)]
    comp["id"] = comp["cb"].map(lambda s: "CD:" + BORO.get(s[3:], "?") + s[:2])
    per_season = comp.groupby("id")["n"].sum() / 2
    df["population_est"] = df["poverty_n"] / (df["poverty_pct"] / 100)
    df["no_heat_complaints_per_1k"] = per_season / df["population_est"] * 1000
    sources["no_heat_complaints_per_1k"] = {
        "alias": "complaints", "record_type": "Complaint", "record_ids": [],
        "query": "Complaint records in heatSeason 2024-25 and 2025-26, grouped by communityBoard → CD, averaged per "
                 "season, per 1,000 residents (residents = poverty number / poverty share, measures 233 and 221)",
        "label": "311 no-heat complaints per 1,000 residents per winter", "period": "winters 2024-25, 2025-26"}
    labels["no_heat_complaints_per_1k"] = "311 no-heat complaints per 1,000 residents per winter"
    sources["population_est"] = sources["poverty_n"]
    return Frame("community district", df, sources, labels)


def uhf42(con):
    cols, sources, labels = {}, {}, {}
    for col, (mid, label) in UHF_MEASURES.items():
        m = measure(con, mid, "UHF42")
        cols[col] = m["value"]
        sources[col], labels[col] = _eh_source(m, mid, label), label
    df = _geo_names(con, "UHF42").join(pd.DataFrame(cols), how="inner")
    return Frame("UHF42 neighborhood", df, sources, labels)


def yearly(con):
    """Citywide per year: heat hospitalizations and ED visits (sum of boroughs) vs hot days at Central Park."""
    def series(mid):
        return con.execute(f"""
            select cast(t.data->>'startYear' as int) as year, sum(cast(o.data->>'value' as double)) as v,
                   list(o.id order by o.id) as ids, count(*) as n
            from eh o join eh t on t.id = o.data->>'timePeriodId'
            where o.type='Observation' and o.data->>'measureId'='measure:{mid}' and o.data->>'geoType'='Borough'
              and t.data->>'isMultiYear'='false'
            group by 1 having count(*) = 5 order by 1""").df().set_index("year")
    hosp, ed = series(538), series(535)
    hot = con.execute("""select cast(data->>'year' as int) as year,
            sum(case when cast(data->>'tmaxF' as double) >= 90 then 1 else 0 end) as days_90f,
            count(*) as days, list(id order by id) as ids
        from weather where type='Day' and data->>'stationId'='USW00094728' group by 1""").df().set_index("year")
    hot = hot[hot["days"] >= 360]
    df = pd.DataFrame({"heat_hosp_n": hosp["v"], "heat_ed_n": ed["v"], "days_90f": hot["days_90f"]})
    df = df[df["days_90f"].notna()]
    df.index = [f"Y:{y}" for y in df.index.astype(int)]
    df["name"] = [i[2:] for i in df.index]
    sources = {
        "heat_hosp_n": {"alias": "eh", "record_type": "Observation", "measure": "measure:538",
                        "record_ids": sorted(i for ids in hosp["ids"] for i in ids),
                        "label": "heat-stress hospitalizations, citywide (sum of 5 boroughs)", "period": "yearly"},
        "heat_ed_n": {"alias": "eh", "record_type": "Observation", "measure": "measure:535",
                      "record_ids": sorted(i for ids in ed["ids"] for i in ids),
                      "label": "heat-stress ED visits, citywide (sum of 5 boroughs)", "period": "yearly"},
        "days_90f": {"alias": "weather", "record_type": "Day", "record_ids": [],
                     "query": "Day records for station USW00094728 (Central Park), count of days with tmaxF >= 90 "
                              "per year (years with >= 360 days)", "label": "days at or above 90°F (Central Park)",
                     "period": "yearly"},
    }
    labels = {k: v["label"] for k, v in sources.items()}
    return Frame("year", df, sources, labels)


if __name__ == "__main__":
    from .data import connect
    con = connect()
    for f in (districts(con), uhf42(con), yearly(con)):
        print(f.unit, f.df.shape)
        print(f.df.drop(columns=[c for c in ("name", "borough") if c in f.df]).describe().T[["count", "mean", "min", "max"]].round(2))
