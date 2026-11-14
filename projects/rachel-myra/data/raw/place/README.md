# Place data (NYC heat, health, prescriptions, cooling places)

Collected 2026-11-14 (overnight, unattended). All downloads are untrusted third-party data. Scripts in
`scripts/place_*.py` are re-runnable (stdlib Python 3.9 unless noted; they reuse cached raw files when present).
Processed outputs are in `data/processed/`. Nothing here is invented: every value is from the named source.

## 0. SBH catchment ZIPs: CONFIRMED

- Source: SBH Health System *2025-2027 Community Health Needs Assessment / Community Service Plan*,
  p.21 ("F. Community Health Assessment, 1a. Service Area"):
  https://www.sbhny.org/fr/community-engagement/wp-content/uploads/2025/12/SBH-2025-2027-CSP.pdf
  (raw: `sbh/SBH-2025-2027-CSP.pdf` + extracted text `sbh/SBH-2025-2027-CSP.txt`; executive summary also saved).
- Quote: "SBH Health System's primary service areas are in the following Bronx zip codes (highest to lowest number of
  patients): 10457, 10458, 10460, 10456, 10453, 10468, 10462, 10467, 10459, 10472, and 10452. In 2024, 38% of SBH
  patients came from 10457 and 10458 zip codes." The CHNA's defined community is Bronx County as a whole.
- The spec's 4 demo ZIPs (10453, 10457, 10458, 10460) are all in the list; the list adds 7 more.
- Processed: `data/processed/sbh_catchment_zips.csv` (11 rows, rank by patient volume).

## 1. Heat Vulnerability Index (HVI)

| Output | Rows | Source |
|---|---|---|
| `hvi_nta2020.csv` / `.geojson` | 197 NTAs (all matched to 2020 NTA polygons) | NYC DOHMH Environment & Health Data Portal (EHDP) indicator 2411, measure 1288, "2023" release; GitHub `nychealth/EHDP-data` branch `production`, `indicators/data/2411.json` |
| `hvi_zcta.csv` | 184 ZCTAs | NYC Open Data `4mhf-duep` "Heat Vulnerability Index Rankings" (DOHMH, updated 2024-09-19) |
| `hvi_modzcta.geojson` | 178 MODZCTA polygons (177 with HVI; 99999 has none) | HVI from `4mhf-duep` joined on MODZCTA code; polygons NYC Open Data `pri4-ifjk` |

- HVI is a 1-5 quintile score (5 = highest risk). Inputs: surface temp (ECOSTRESS 27 Aug 2020), vegetative cover
  (LiDAR 2017), AC access (HVS 2017), median household income (ACS 2016-20), % non-Hispanic Black (Census 2020).
- Also in raw: CDTA-level HVI (`ehdp/2191.json`). EHDP NTA GeoIDs (e.g. 50101) were matched to NTA2020 codes
  (e.g. BX0101) by exact NTA name via EHDP `geography/GeoLookup.csv`; 197/197 matched.
- SBH demo ZIPs 10453, 10457, 10458, 10460 are all HVI 5.

## 2. Household air conditioning

- Source: EHDP indicator 2185 "Household air conditioning" (NYC Housing and Vacancy Survey). `ehdp/2185.json`.
- **Finest geography: PUMA 2020 (55 areas) for 2023**; PUMA2010 / sub-borough for 2014 and 2017; UHF42 for 2014/2017;
  borough and citywide. No NTA or ZIP AC estimate exists in the portal.
- `ac_households_nyc.csv`: all geographies, years, measures (% with AC, # with AC, % without AC) with 95% CI and the
  portal's high-CV caution note (958 rows).
- `ac_households_puma2020.geojson`: 2023 % with/without AC per PUMA 2020 polygon (NYC Open Data `pikk-p9nv`).
- Methodology changed in the 2021 HVS; the portal warns earlier years are not strictly comparable.
- Related raw indicators also saved (not processed): adults with AC (2104, UHF42), older adults with AC (2155, 2013),
  surface temperature (2141, NTA2010), tree canopy (2157), heat ED visits (2075, 2443), heat deaths (2074),
  heat hospitalizations (2410).

## 3. CDC PLACES

- 2025 release (BRFSS 2023 model-based small-area estimates): ZCTA `qnzd-25i4`, tract `cwsq-ngmh` on data.cdc.gov.
- **CKD (KIDNEY) is not in the 2024 or 2025 releases**; taken from the 2023 release (BRFSS 2021): ZCTA `9umn-c3jf`,
  tract `em5e-5hvn`. The 2023 tract file uses **2010 tract IDs**, so 137 kidney-only rows in the tract output
  are 2010 tracts with no 2025 measures.
- Measures: DIABETES, BPHIGH, BPMED, CHD, STROKE, COPD, DEPRESSION, MHLTH (frequent mental distress = "mental health
  not good" >=14 days), OBESITY, CASTHMA, DISABILITY, MOBILITY, COGNITION, SELFCARE, INDEPLIVE, HEARING, VISION,
  GHLTH, LONELINESS, EMOTIONSPT, SHUTUTILITY, LACKTRPT, HOUSINSECU, ACCESS2, KIDNEY. Crude prevalence %, with 95% CI.
- NYC ZCTAs = every ZCTA listed in MODZCTA; tracts = the 5 NYC counties. Pulled with SoQL `$where` filters.
- Outputs: `places_nyc_zcta.csv` (186 ZCTAs, wide), `places_nyc_tract.csv` (2,368 rows, wide; 2,231 2020 tracts with
  2025 data). Raw long files in `places/`.

## 4. CDC/ATSDR Social Vulnerability Index

- SVI **2022** (latest published; 2023/2024 URLs 404), New York state tract CSV:
  https://svi.cdc.gov/Documents/Data/2022/csv/states/NewYork.csv -> `svi/NewYork_2022_tract.csv` (5,394 NY tracts).
- **Percentiles (RPL_*) are ranked within New York State**, not nationally (the US file would give national ranks).
- Outputs: `svi2022_nyc_tract.csv` / `.geojson` (2,324 NYC tracts, all joined to 2020 tract polygons, NYC Open Data
  `63ge-mke6`), with overall + 4 theme percentiles, flags, and key EP_* percentages; -999 -> blank.

## 5. CMS Medicare Part D prescribing (data year 2024)

Script: `scripts/place_partd.py`. data.cms.gov data-api v1, filtered server-side (`filter[...]`, `IN` operator,
`column=`); no full-file download. Data year **2024** (latest; released 2026).

| Dataset | API id | Use |
|---|---|---|
| Part D Prescribers - by Provider and Drug, 2024 | `9552739e-3d05-4c1b-8eff-ecabf391e2e5` | NY prescribers x our generic names (439,987 NY rows fetched) |
| Part D Prescribers - by Provider, 2024 | `14d8e8a9-7e9b-4370-a044-bf97c46b4b44` | NPI -> practice ZIP5 + specialty (the provider-drug file has city only, no ZIP) |
| Part D Prescribers - by Geography and Drug, 2024 | `c8ea3f8e-3a09-4fea-86f2-8902fb4b0920` | national generic/brand list (3,632 rows) for class mapping; national + NY state rows |

Method: generic/brand pairs from the national file are classified into the 15 classes (`partd/drug_class_map_2024.csv`,
382 pairs; regexes in the script). Antipsychotics use CMS's own `Antpsyct_Drug_Flag`. Exclusions: insulin supplies/
pump cartridges/reusable pens; buprenorphine injections (Sublocade, Brixadi) and sublingual forms (only generic
"Buprenorphine" with brand Butrans/generic = transdermal patch is kept with fentanyl); epinephrine vials (Adrenalin)
and nasal spray (Neffy). Anticholinergics = oxybutynin, tolterodine, trospium, solifenacin, darifenacin,
fesoterodine, benztropine, trihexyphenidyl (diphenhydramine is OTC, not in Part D). SSRIs = sertraline, fluoxetine,
citalopram, escitalopram, paroxetine, fluvoxamine. Combination products count in every class they contain
(e.g. lisinopril/HCTZ in ACEi/ARB and thiazides; Cobenfy xanomeline/trospium in antipsychotics and anticholinergics).
NYC = prescriber practice ZIP in any ZCTA of the NYC MODZCTA file (51,903 NY prescribers; 177,605 NYC prescriber x
drug rows kept).

Outputs (no NPIs, no names):
- `data/processed/partd_nyc_zip_drugclass.csv` (2,401 rows; 187 ZIPs x class): n_prescribers, tot_clms,
  tot_30day_fills, tot_day_suply, tot_benes_sum, n_rows_benes_suppressed, ge65_tot_clms, small_cell, generics.
- `data/processed/partd_nyc_specialty_drugclass.csv` (702 rows; CMS prescriber type x class), same columns.
- `data/processed/partd_geo_drug_national_ny.csv` (740 rows: 382 national + 358 New York state, by generic/brand).

Caveats:
- CMS omits any prescriber-drug row with <11 claims and blanks Tot_Benes when <11 (`n_rows_benes_suppressed`), so
  totals are undercounts, worst for rarely used drugs (epinephrine, fentanyl patches, lithium in primary care).
- `tot_benes_sum` sums prescriber-level beneficiary counts: a patient seen by two prescribers counts twice.
- ZIP is the **prescriber's practice address**, not where patients live; hospital/clinic ZIPs (e.g. SBH's 10457)
  concentrate claims. Medicare Part D only (mostly 65+ and disabled; not Medicaid/commercial).
- `small_cell` = fewer than 3 prescribers in the cell (473 of 2,401 ZIP rows); don't show those cells alone in the app.
- Raw NPI-level files (`partd/nyc_prescribers_2024_npi_zip.csv`, `partd/nyc_provider_drug_2024_npi_level.csv`,
  21 MB) hold NPI + counts only (names were never requested) and must stay out of the app.
- SBH 11 ZIPs, 2024 claims by class: ACEi/ARB 240,093; beta blockers 165,813; metformin 121,112; thiazides 91,791;
  SSRIs 82,849; antipsychotics 80,389; SGLT2 61,178; insulin 57,192; loop diuretics 52,838; anticholinergics 17,936;
  topiramate/zonisamide 3,329; lithium 2,112; ADHD stimulants 1,173; fentanyl/bup patches 559; epinephrine 269.
- Second demo city not pulled (not specified); rerun with a different ZIP list/state.

## 6. Cooling places -> `data/processed/cooling_places_nyc.geojson`

1,868 Point features, one per place, each with `source`, `category`, `indoor`, `official_cooling_center`, and
hours/accessibility where the source has them. Script: `scripts/place_cooling.py`. Dedup: a lower-priority record
within 50 m of a kept place (same indoor/outdoor) is dropped and listed in `also_in`.

| source | kept | what | hours | accessibility |
|---|---|---|---|---|
| `nycem_cool_options` | 1,341 | NYC Emergency Management "Cool Options" finder (finder.nyc.gov/coolingcenters). ArcGIS layer `services6.arcgis.com/yG5s3afENB5iO9fj/arcgis/rest/services/Cool_Options/FeatureServer/0`, joined on `NYCEM_ID` to `services5.arcgis.com/tMsas0Edz7Aih7fO/arcgis/rest/services/Cooling_Centers_PROD_view/FeatureServer/0` for operator/facility type. 476 indoor cooling centers + 13 "other indoor cool options" (Finder_status OPEN); 761 spray showers + 91 pools (outdoor, CLOSED for the season) | per-day strings (`hours`) | `accessible` Yes/No, pet-friendly, age restriction |
| `nyc_parks_rec_center` | 47 (of 54) | NYC Parks rec centers feed nycgovparks.org/bigapps/DPR_RecreationCenter_001.json; coords = NYC Parks Structures (`n8q6-i44s`, recreation_center=true) footprint centroid, else NYC GeoSearch geocode (`coord_method`) | building hours | none |
| `facdb_public_library` | 52 | NYC Facilities Database `ji82-xba5`, PUBLIC LIBRARY (226 rows: NYPL 91, BPL 68, QPL 67); most others merged into Cool Options library cooling centers | none | none |
| `queens_library` | 10 | NYC Open Data `kh3d-xhq7` Queens Library branches; name-matched to existing QPL places to add phone + `hours_url`; unmatched ones added with `coord_precision` ~1 km (source rounds lat/lon to 0.01 deg) | URL only | none |
| `osm` | 418 | OpenStreetMap Overpass (base 2026-11-14T06:20Z): library, community_centre, social_centre, mall, department_store, senior outreach. AC-tagged restaurants/shops excluded | `opening_hours` (OSM) | `wheelchair` (OSM) |

Caveats:
- **Official cooling centers are seasonal.** The finder lists the 2026-season sites (operator mix in the PROD view:
  NYC Aging older adult centers 295, NYPL 80, QPL 52, BPL 49, Petco 13, elected officials 3). The app status
  layer read "Open" (last edit 2026-10-21) at access; sites activate only on heat-emergency days. Verify on the day.
- The older NYC Open Data "Cool It! NYC 2020 - Cooling Sites" (`h2bn-gu9k`) is outdoor misting/spray features from
  2020 only; not used.
- NYPL and BPL websites are bot-protected (Incapsula / 403); their branch hours were not scraped. Library hours come
  only via the Cool Options record (when the branch is a cooling center) or OSM `opening_hours`.
- NYC Parks rec centers usually require a membership; flagged in `membership_required`. Rec center manager names in
  the raw feed are not carried into the processed file.
- In the 11 SBH ZIPs (by the record's ZIP field): 38 official cooling centers, 6 rec centers, 6 department stores,
  3 libraries, 1 community centre (indoor; OSM records often lack ZIPs, so use the geometry for spatial joins).

## 7. Hyperlocal Temperature Monitoring (`qdq3-9eqn`)

- Never downloaded in full (2,097,150 hourly rows, 2018-06-15 to 2019-10-15, 423 sensors). Per-sensor SoQL
  aggregates only (`hyperlocal/agg_*.json`).
- `hyperlocal_temp_sensors.csv` / `.geojson`: location, borough, NTA (2010 code), install type, hours, mean/max/min F,
  Jul-Aug afternoon (13-17h) and night (0-5h) means, hours >=90F and >=95F, `in_bronx`.
- `hyperlocal_temp_borough_coverage.csv`. **Bronx coverage:** 136 of 423 sensors are in the Bronx, but only in 6 NTAs
  (2010): BX27 Hunts Point 36, BX39 Mott Haven-Port Morris 33, BX36 University Heights-Morris Heights 29,
  BX03 Eastchester-Edenwald-Baychester 26, BX44 Williamsbridge-Olinville 7, BX41 Mount Hope 5. So the spec's "thin
  Bronx coverage" is true spatially (6 neighborhoods) but not by sensor count. In the SBH area, University Heights
  (10453) and Mount Hope (10457/10453) have sensors; Belmont, East Tremont, West Farms, Fordham, Bathgate (10457/10458/
  10460 core) have none. Data are 2018-2019 only (program ended); sensors were placed in HVI 4-5 neighborhoods.

## 8. Pharmacies in the SBH catchment -> `data/processed/pharmacies_sbh_catchment.geojson`

- No bulk NYS pharmacy registry exists as open data (NYS Office of the Professions offers lookup only). Used:
  1. CMS NPPES NPI Registry API (organization NPIs with a "pharmacy" taxonomy, location address in the 11 ZIPs):
     518 records (`pharmacies/nppes_pharmacy_catchment.json`). The NY taxonomy `license` = NYS pharmacy registration
     number (`nys_registration`). Geocoded with NYC Planning GeoSearch (geosearch.planninglabs.nyc; all >=0.8 conf).
  2. OpenStreetMap pharmacies (Overpass, base 2026-11-14T06:22Z) inside the 11 MODZCTA polygons: 34.
  Matched within 60 m: 32. Output = 520 features (518 NPPES + 2 OSM-only), `source` field on each.
- **Caveat: NPPES over-counts.** NPIs are rarely deactivated when a store closes or changes owner (418 distinct
  addresses for 518 NPIs; `last_updated` ranges 2007-2026). Treat `osm_id` matches and recent `last_updated` as
  stronger evidence that a pharmacy is open. Organization names only; no individual names.

## 9. MTA GTFS (subway)

- https://rrgtfsfeeds.s3.amazonaws.com/gtfs_subway.zip (5.6 MB zipped, 43 MB unzipped; Last-Modified 2026-10-28;
  files dated 2026-07-31). Kept zipped: `gtfs/gtfs_subway.zip` (sha256 acb12271...e1e6).
- `data/processed/subway_stations_nyc.geojson`: 496 parent stations with routes served (`scripts/place_gtfs_stations.py`).
- Not included: bus GTFS (per-borough feeds), elevator/ADA status (separate MTA feeds).

## Boundaries (raw, `boundaries/`)

NTA 2020 (`9nt8-h7nd`, 262 polygons), MODZCTA (`pri4-ifjk`, 178), 2020 census tracts (`63ge-mke6`, 2,325),
PUMA 2020 (`pikk-p9nv`, 55), EHDP UHF42.geojson, GeoLookup.csv, zcta_to_uhf.csv, puma_2020_names.csv.
Socrata returned intermittent 503s; geospatial export endpoints were used where the resource API failed.
