# Climate data (raw) — The Missing Label

Access date for everything here: **2026-11-14** (fetched ~06:00–06:15 UTC). All sources are NOAA/NWS/CDC public
data. Downloaded files are untrusted inputs; nothing in this folder was hand-edited.
User-Agent used for every request: `missing-label-hackathon (research prototype)`.
Total size of this folder: about 35 MB.

Scripts (all in `scripts/`, run with `~/.local/bin/uv run --with <pkgs> python scripts/<file>.py`):

| Script | Packages | Produces |
|---|---|---|
| `climate_ghcnd.py` | pandas | `nyc_daily_climate.csv`, `nyc_heatwaves.csv`, `nyc_heatwave_daily_odds.csv` |
| `climate_hourly_replay.py --start --end [--out]` | pandas | `replay_heatwave_hourly.csv` |
| `climate_nws.py` | (stdlib) | `nws_zip_gridpoints.json` |
| `climate_heatrisk.py --start --end` | rasterio, pyproj | `heatrisk_zip_current.json`, `heatrisk_zip_replay.csv` |
| `climate_cpc.py` | pyshp, shapely | `cpc_outlook_nyc.json` |

All outputs are in `data/processed/`.

---

## 1. GHCN-Daily history → `data/processed/nyc_daily_climate.csv`

- Source: `https://www.ncei.noaa.gov/data/global-historical-climatology-network-daily/access/<station>.csv`
  - `ghcnd/USW00094728.csv` — NY City Central Park (40.779, -73.969), record from 1869
  - `ghcnd/USW00014732.csv` — LaGuardia Airport (40.779, -73.880)
- Output: 1991-01-01 → **2026-11-10** (latest available), 13,098 days × 2 stations = 26,196 rows.
- Columns: `tmax_f, tmin_f, tavg_f, dewpoint_avg_f, wetbulb_avg_f, rh_avg_pct, rh_min_pct, rh_max_pct,
  wind_avg_mph, prcp_in, heat_index_max_approx_f`.
- Converted from GHCN units (tenths °C, tenths mm, tenths m/s). Values with a non-blank GHCN quality flag were dropped.
- **Caveats**
  - Humidity in GHCN-Daily (ADPT dew point, RHAV/RHMN/RHMX, AWBT) exists only **2006-01-01 → 2024-12-31** at both
    stations. It's blank before 2006 and from 2025 on, so the approximate heat index is blank there too.
  - `heat_index_max_approx_f` = NWS heat index at TMAX using the **daily-mean** dew point. It's a rough proxy and
    usually overstates the afternoon value, because dew point often drops in the afternoon. For real heat index,
    use the hourly replay file.
  - TAVG is only sparsely reported (1998–2005).
  - 2026 values are recent and may still be revised by NCEI QC.

## 2. 1991–2020 daily normals

- Source: `https://www.ncei.noaa.gov/data/normals-daily/1991-2020/access/<station>.csv`
  → `normals/normals_daily_1991-2020_USW00094728.csv` (Central Park) and `..._USW00014732.csv` (LaGuardia).
- Daily TMAX/TMIN normals and their standard deviations are merged into `nyc_heatwave_daily_odds.csv`
  (`cp_normal_tmax_f`, `cp_normal_tmin_f`, `cp_normal_tmax_sd_f`, and the same with `lga_`). Example: Central Park normal high is 85.3 °F on 07-17.

## 3. Heat-wave definitions, list and odds

### Official NWS New York (OKX, Upton NY) criteria
These cover the NYC and Bronx zones. Fetched from `https://www.weather.gov/okx/wwa_definitions` and
`https://www.weather.gov/okx/extremeheat`; page copies are saved in `nws/okx_*.html`.
- **Heat Advisory:** "Issued when the heat index is forecast to reach 95F or greater for at least 2 consecutive days
  or 100 to 104 F for any length of time." The extremeheat page words the first condition as "95 to 99F for at least 2 consecutive days".
- **Extreme Heat Warning:** "Issued when heat index values are forecast to reach or exceed 105°F for at least 2
  consecutive hours." The **Watch** is issued 24–48 h ahead and the **Warning** within 24 h. "Extreme Heat" replaced the
  older "Excessive Heat" product name in 2025. News articles from before then use "Excessive Heat Warning" with the same
  105 °F threshold.
- These criteria are for **forecast heat index**, so they can't be applied exactly to daily TMAX/TMIN history.

### Climatological definition used for the history files
A heat wave is **≥3 consecutive days with TMAX ≥ 90 °F** at a station. This is the common NYC / NWS-climate usage.
- `data/processed/nyc_heatwaves.csv`: 1991 → 2026-11-10. **83 at Central Park, 100 at LaGuardia.**
  Columns: start/end dates, length, peak TMAX and its date, mean TMAX, warmest TMIN and its date, mean TMIN,
  nights with TMIN ≥ 75 °F and ≥ 80 °F, approximate peak heat index (2006–2024 only), and max daily-mean dew point.
  - Longest at Central Park: 1999-07-23 → 08-02 (11 days).
  - Hottest at Central Park: 2011-07-21 → 07-24 (104 °F, low of 84 °F).
- `data/processed/nyc_heatwave_daily_odds.csv`: one row per calendar day (MM-DD, 366 rows), computed over the complete
  years **1991–2025** (35 years). Columns for each station (`cp_`, `lga_`):
  - `p_in_heatwave`: fraction of years in which that date was inside a heat wave. This is the probability-bar fallback.
  - `p_in_heatwave_smoothed15d`: 15-day centered mean of the above. It's less noisy; use it for display.
  - `p_heatwave_within_14d`: fraction of years with any heat-wave day in [date, date+13].
  - `p_tmax_ge_90` and `p_tmin_ge_75`.
  - `mean_tmax_f` and `mean_tmin_f` (1991–2025).
  - 1991–2020 normals.
  - Central Park examples: 07-20 → p_in_heatwave 0.23, smoothed 0.20, within 14 days 0.54. 11-13 → 0.0.
  - 02-29 is based on 9 leap years only.

## 4. Replay heat wave: **June 22–25, 2025** → `data/processed/replay_heatwave_hourly.csv`

**Why this event:**
- **Recent and well documented.** NWS OKX issued an **Extreme Heat Watch, then an Extreme Heat Warning** for the
  Bronx zone NYZ073, valid 2025-06-22 16Z → 2025-06-25 00Z. A Heat Advisory followed on 06-25. This was verified
  from the IEM VTEC archive, `nws/iem_vtec_NYZ073_2025.json`, at
  `https://mesonet.agron.iastate.edu/json/vtec_events_byugc.php?ugc=NYZ073&sdate=2025-01-01&edate=2026-11-14`.
- **Severe.** Central Park reached 99 °F on 06-24 (GHCN daily; the highest hourly reading was 98.1 °F) and LaGuardia
  reached 100.9 °F. The hourly heat index peaked at **105.7 °F** at Central Park on 06-23, which meets the
  Extreme Heat Warning criterion.
- **Nights that didn't cool, the spec's key compounding factor.** Central Park daily lows were 80.1, 81.0 and 81.0 °F
  on 06-23 to 06-25. That's **3 straight nights ≥ 80 °F**, tied for the most of any Central Park heat wave in 1991–2026.
  The only other one is July 2013, which lasted 7 days. Every other heat wave has ≤ 2 such nights.
- **HeatRisk for the Bronx demo ZIPs, from the archived Day-1 forecasts:** Orange 06-19, Red 06-22 and 06-23,
  **Magenta (4, extreme) 06-24**, Red 06-25, then Yellow. See `data/processed/heatrisk_zip_replay.csv`. The replay
  climbs through every HeatRisk color, which suits the simulator.
- **Multi-day:** 3 days at Central Park (06-23 → 06-25) and 4 at LaGuardia (06-22 → 06-25) by the ≥90 °F rule.

**Window:** 2025-06-19 → 2025-06-28 local time, which is the heat wave plus 3 days on each side. 480 rows
(24 hourly METARs × 10 days × 2 stations).
- Source: NCEI Access Data Service, Global Hourly (ISD):
  `https://www.ncei.noaa.gov/access/services/data/v1?dataset=global-hourly&stations=<id>&startDate=...&endDate=...&format=csv`
  - Stations: 72505394728 (KNYC Central Park) and 72503014732 (KLGA LaGuardia).
  - Raw files: `hourly/isd_*_20250619_20250628.csv`.
- Columns: `time_utc`, `time_local` (America/New_York), `temp_f`, `dewpoint_f`, `rh_pct` (Magnus formula from T and Td),
  `wind_dir_deg`, `wind_speed_mph`, `sea_level_pressure_hpa`, `heat_index_f`.
  - `heat_index_f` uses the NWS Rothfusz regression with the Steadman simple formula below 80 °F and the NWS low/high-RH
    adjustments (https://www.wpc.ncep.noaa.gov/html/heatindex_equation.shtml).
- **Caveats**
  - Only routine FM-15 hourly reports (:51 past the hour) are kept, so peaks between reports are missed.
  - KNYC wind is known to be sheltered by trees and reads low.
- **Alternative considered:** 2026-06-30 → 07-04. GHCN shows Central Park 100 °F and LaGuardia 104 °F, and IEM shows
  an Extreme Heat Warning for 07-01 → 07-05. It was **not chosen** because NCEI Global Hourly returned **no 2026 data**
  for these stations through the access service on 2026-11-14 (the ISD access URL now redirects to the AWS bucket).
  It also had only 1 night ≥ 80 °F, and 2026 daily values are still preliminary.
- Another agent (thermal simulation) can reuse this file, or rerun the script with other `--start/--end` dates for 2025 or earlier.

## 5. NWS API → `data/processed/nws_zip_gridpoints.json`

- ZIP centroids: US Census 2024 Gazetteer ZCTA internal points, saved as `nws/zcta_gazetteer_2024_demo_zips.tsv`.
- `GET https://api.weather.gov/points/{lat},{lon}` for each ZIP. All four are office **OKX**, forecast zone
  **NYZ073** (Bronx) and county zone **NYC005**.
  - Grids: 10453 → (35,49); 10457 → (36,49); 10458 → (36,49); 10460 → (37,48).
- Saved per ZIP:
  - forecast, hourly forecast and gridData URLs
  - a sample 7-day forecast and the first 48 hourly periods, with temperature, dew point, RH and PoP
  - full responses in `nws/points_*.json`, `nws/forecast_*.json` and `nws/forecast_hourly_*.json`
- Active alerts for NYZ073 and NYC005, plus `alerts/active?area=NY`: **0 alerts** on 2026-11-14, as expected in November.
- For heat index: the gridData endpoint (`forecast_grid_data_url`) has `heatIndex`, `apparentTemperature`, `maxTemperature`
  and `minTemperature` time series. It wasn't saved, because heat index values are null or uninformative in November.

## 6. HeatRisk (NWS/CDC, experimental)

What works, all tested 2026-11-14:
1. **ArcGIS ImageServer identify at a point.** This is the best route for "HeatRisk by ZIP, next 7 days".
   `https://mapservices.weather.noaa.gov/experimental/rest/services/NWS_HeatRisk/ImageServer/identify?geometry={"x":lon,"y":lat,"spatialReference":{"wkid":4326}}&geometryType=esriGeometryPoint&returnCatalogItems=true&returnGeometry=false&f=json`
   - `properties.Values[i]` is the category 0–4 for `catalogItems.features[i]`.
   - Each feature's `name` is `HeatRisk_<day>_Mercator` and its `idp_validtime` is in epoch ms.
   - Output: `data/processed/heatrisk_zip_current.json`. All 4 ZIPs are **0 (green) for all 7 days**. Raw: `heatrisk/identify_*.json`, `imageserver_info.json`.
   - WMS and WCS endpoints also exist under `.../experimental/services/NWS_HeatRisk/ImageServer/{WMSServer,WCSServer}`.
2. **Latest GeoTIFF and KML per day** from `https://www.wpc.ncep.noaa.gov/heatrisk/data/`:
   - `HeatRisk_<1-7>_Mercator.tif`, about 110 KB each
   - `HeatRisk_Day<1-7>_Fcst.kml`
   - `HeatRisk_Entire_Fcst.kml`
   - Issue times are in `data/FileTimes.js`.
   - These were not downloaded, because route 1 covers the same data.
3. **Daily archive of Day-1 forecasts** (PNG, KML and GeoTIFF), from 2024 onward:
   `https://www.wpc.ncep.noaa.gov/heatrisk/data/archive/HeatRisk_CONUS_YYYYMMDD.tif`
   - The GeoTIFF is single-band uint8, EPSG:3857, about 2.5 km pixels. Values 0–4 are categories and 5 is nodata.
   - Downloaded for 2025-06-19 → 06-28 (`heatrisk/archive/`) and sampled at the ZIP centroids → `data/processed/heatrisk_zip_replay.csv`.
4. **CDC HeatRisk Dashboard backend** (undocumented; found in the dashboard's JS bundle):
   `https://ephtracking.cdc.gov/DataExplorer/HeatForecastData/<county FIPS>` returns
   `[{"date": <epoch ms>, "day0".."day6": <0-4>, "countyFips": 36005}]`.
   - It's **county level only**, so all of the Bronx shares one value. The dashboard looks up ZIP → county first.
   - Saved as `heatrisk/cdc_heatforecastdata_36005.json`: all zeros.
   - It's undocumented and could change without notice.

What doesn't work or wasn't found:
- The CDC Tracking public API (`ephtracking.cdc.gov/apigateway/api/v1/...`) rejects `HeatForecastData`
  ("Invalid Call from API"), and anonymous use is rate-limited (HTTP 429).
- There's no official ZIP-level HeatRisk JSON. ZIP values come from sampling the 2.5 km grid at the ZIP centroid.
  The 4 demo ZIPs are only a few pixels apart and always had the same value.
- Historical HeatRisk at stations for earlier years requires a request form on the WPC data page.

## 7. CPC outlooks → `data/processed/cpc_outlook_nyc.json`

- Query point: ZIP 10457 centroid (40.8457, -73.8979).
- Sources:
  - ArcGIS MapServer point queries at `https://mapservices.weather.noaa.gov/vector/rest/services/outlooks/`:
    `cpc_6_10_day_outlk/0`, `cpc_8_14_day_outlk/0`, `cpc_mthly_temp_outlk/0`, and `cpc_sea_temp_outlk/0..12` (leads 1–13).
  - Week 3–4 isn't on the map service. It comes from the shapefile
    `https://ftp.cpc.ncep.noaa.gov/GIS/us_tempprcpfcst/wk34temp_latest.zip` (point-in-polygon).
  - Raw responses are in `cpc/`.
- Values at NYC on 2026-11-14:

| Outlook | Issued | Valid | Favored | Prob |
|---|---|---|---|---|
| 6–10 day | 2026-11-13 | Nov 19–23 | Above | 70% |
| 8–14 day | 2026-11-13 | Nov 21–27 | Above | 60% |
| Week 3–4 | 2026-11-13 | Nov 28–Dec 11 | Above | 40% |
| Monthly | 2026-10-31 | Nov 2026 | Above | 50% |
| Seasonal L1–L12 | 2026-10-15 | NDJ 2026–27 … OND 2027 | Above | 40–50% (JJA 2027: 50%) |
| Seasonal L13 | 2026-10-15 | NDJ 2027–28 | EC | 33% |

- **Caveats**
  - `prob` is the CPC contour value, which is the lower edge of the band the point falls in (e.g. "50" = 50–60%).
  - `p_above_normal_est_pct` is **derived by us**, using the convention that the opposite tercile takes the remainder
    and near-normal stays at 33.3%. CPC doesn't publish it.
  - Outlooks are relative to 1991–2020 normals. "Above normal" in November is not heat-wave risk. It matters for
    the probability bar only in late spring and summer.
  - For summer use, the bar should combine `cp_p_in_heatwave_smoothed15d` with the CPC above-normal tilt.
    No custom ML is used, per spec §6.6.
