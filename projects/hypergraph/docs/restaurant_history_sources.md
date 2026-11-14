# Sources for New York City restaurant inspection history

Compiled 13 November 2026. The live DOHMH table (43nn-pn8j) holds only restaurants that are active on the record date, with inspections from the last three years before each restaurant's most recent inspection (data.gov catalog description). It carries no licence statement in the catalog record ("Access Level: public").

## Internet Archive captures of the export

The CDX listing for `data.cityofnewyork.us/api/views/43nn-pn8j/rows.csv*` returned 36 rows, 33 of them distinct export captures (all HTTP 200, text/csv). Sizes are the compressed transfer lengths reported by CDX. The listing is saved in `~/opt/nyc-concordance/restaurant_history/cdx_data_cityofnewyork_us_api_views_43nn_pn8j_rows_csv_.json`. Captures of `resource/43nn-pn8j.csv` exist only from 2025-03-16 onward and are 78-117 KB (a default 1000-row page), so they are not usable as history. The CDX query for `xx67-kt59` returned no captures; I found no evidence that this id exists. The Internet Archive was offline during part of the session, so queries on `nycopendata.socrata.com` (the pre-2016 host) failed and should be repeated.

Dates (YYYYMMDD, size in MB): 20150908 (9.6), 20161210 (24.0), 20170115 (23.6), 20170422 (22.8), 20170426 (22.8, two captures), 20201106 (36.2), 20210529 (35.0), 20221130 (21.6), 20230510 (19.0), 20230603 (18.9), 20230810 (19.2), 20231117 (11.5), 20240708 (13.1), 20240928 (24.1), 20241205 (25.3), 20241217 (25.4), 20241218 (25.6), 20250201 (26.0), 20250502 (27.1), 20250722 (27.9), 20250802 (27.7), 20250819 (28.0), 20250913 (28.0), 20251115 (30.7), 20260121 (31.2), 20260312 (31.2), 20260323 (29.2), 20260403 (31.1). Three further captures of 2022-06-26 (14 MB) have different URL variants. No capture exceeds 50 MB.

Earliest inspection date in each of the ten files already downloaded to `~/opt/nyc-concordance/restaurants_wayback/` (read locally, no new download; 1900-01-01 placeholder dates excluded):

| Capture | Earliest inspection | Note |
|---|---|---|
| 2015-09-08 | 2007-09-10 | 7 rows in 2007-09, 1 in 2008, 1 in 2009, 5 in 2010, 3,607 in 2011; bulk starts 2012 (76,034 rows) |
| 2016-12-10 | 2011-08-23 | bulk starts 2013 |
| 2017-04-26 | 2011-10-07 | bulk starts 2013 |
| 2020-11-06 | 2012-02-14 | bulk starts 2016 |
| 2021-05-29 | 2011-04-19 | |
| 2022-11-30 | 2011-10-07 | |
| 2023-11-17 | 2015-09-24 | |
| 2024-12-18 | 2015-09-24 | |
| 2025-11-15 | 2015-09-24 | |
| 2026-04-03 | 2007-08-28 | 26 rows in 2007; sparse before 2016 |

The 2015 capture is the earliest. Its rows before 2012 are leftovers attached to restaurants still open in 2015, so they are not a sample of inspections in those years. Counts of distinct restaurants by inspection year in that capture are 885 (2011), 12,227 (2012) and 18,195 (2013), against about 24,000 active restaurants in 2015.

## Table of sources

| Name | URL | Date range | Coverage | Format | Licence | How verified |
|---|---|---|---|---|---|---|
| NYC Open Data, DOHMH Restaurant Inspection Results (live) | https://data.cityofnewyork.us/d/43nn-pn8j | rolling three years, daily refresh | five boroughs; active restaurants only; all inspection types in window | CSV, JSON, XML, GeoJSON | none stated in catalog; NYC Open Data terms of use | catalog.data.gov record read; CDX captures |
| Wayback Machine captures of rows.csv | https://web.archive.org/web/2015*/data.cityofnewyork.us/api/views/43nn-pn8j/rows.csv* | snapshots 2015-09 to 2026-04; inspection dates from 2007 (sparse), dense from 2012 (2015 capture) | five boroughs; survivors only (open on the capture date) | CSV | underlying data as above; Archive adds none | CDX API queried; ten files read locally |
| Kaggle, sdawar, "DOHMH New York City Restaurant Inspection Results" | https://www.kaggle.com/datasets/sdawar (listed via baselight mirror) | described as 2013-2020 | five boroughs; active restaurants only | CSV | not checked | search snippet only; page not retrieved |
| Kaggle, minisam, "New York City Restaurant Inspection 2017-2021" | listed via baselight mirror | about 2017 to March 2022 | five boroughs; active only | CSV | not checked | search snippet only |
| NYC DOHMH ABC Eats | https://a816-health.nyc.gov/ABCEatsRestaurants/ | current grades and recent inspections | active restaurants | web lookup, no bulk download | none stated | FAQ page read; it states no date range |
| lettergrades.nyc | https://www.lettergrades.nyc/about | not established | not established | web | not established | fetch failed (socket closed); not read |
| Wong et al. 2015, Am J Public Health 105(3):e81-e87 | https://doi.org/10.2105/AJPH.2014.302404 | inspections 2007-2013 | 43,448 restaurants; authors are DOHMH staff; internal records | not published | none; no replication file found | abstract and news summary read |
| Ho, Ashwood, Handan-Nader, replication of Jin and Leslie (2003) and Simon et al. (2005) | https://topcat.aeaweb.org/articles/materials/11743 | Los Angeles County, 1990s-2000s | Los Angeles only, not New York | PDF appendix | AEA data policy | first page of PDF read |
| Jin and Leslie 2003; Simon et al. 2005 | not retrieved | Los Angeles County | Los Angeles only | | | known from the Ho appendix; not New York |
| Makofske 2020 or later | none found | | | | | two searches found no paper by this name; not verified |
| Open Restaurants Inspections (Historical) | https://catalog.data.gov/dataset/open-restaurants-inspections | outdoor dining programme | not the DOHMH food inspections | CSV | | catalog listing only |
| data.world, Harvard Dataverse | none found | | | | | searched; no NYC restaurant inspection history found |
| GitHub, eigenfoo/nyc-restaurant-violations | https://github.com/eigenfoo/nyc-restaurant-violations | scraped from the live table | active only; the README notes there is no full history | code and CSV | not checked | search snippet only |
| NYC FOIL request to DOHMH | https://www.nyc.gov/site/doh/about/foil.page (not verified) | any | any | any | | not attempted; no result is known |

## Before July 2010

Letter grading began on 27 July 2010. Before that the Department of Health scored inspections numerically and published the scores online (Food Safety News, March and August 2010, state that grades replace numerical ratings that had been available online). I could not establish from what date the online scores existed, whether the earlier database can be downloaded, or whether it was archived. The Wong et al. paper shows that DOHMH holds electronic inspection records from at least January 2007 (2007-2013, 43,448 restaurants), but the data are internal. The 2015 Wayback capture contains 15 rows dated 2007-2010, which are the only pre-2011 public inspection rows I found. Tedium (28 April 2021) says inspection results were confidential in the early 1970s and that newspapers published lists of offenders from 1972; I found no public dataset of inspections before 2007.

## Earliest and reliable

The earliest public rows are from September 2007 (Wayback capture of 2015-09-08), but they are an unrepresentative remnant. The earliest period with usable coverage in a public file is calendar year 2012, where the 2015 capture holds 12,227 restaurants and 76,034 rows. It is incomplete, because restaurants that closed before September 2015 are missing, so counts of restaurants and openings are biased toward survivors. For 2013 onward, the 2015, 2016 and 2017 captures together give the most complete public record, with more than 135,000 rows in 2013. Records from 2010 to 2011 and earlier would require a FOIL request or a data-sharing request to DOHMH, and that has not been tried.
