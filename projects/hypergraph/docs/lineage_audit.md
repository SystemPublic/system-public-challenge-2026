# Audit of data fetched before registration

This audit was written on 13 November 2026. `data/derived/lineage_audit.json` classifies every early fetch, keyed by claim id. `tools/build_lineage.py` copies each class into `viz/data/lineage.json`, and `viz/evidence.html` colours the early fetches by class in section C.

## What was checked

For each claim, `viz/data/lineage.json` records the fetch time of every data source listed in the outcome's `sources`. In 46 of the 84 claims whose outcomes record a fetch time for city data, at least one source has a fetch time earlier than the registration's `registered_at`. The count excludes reads of the research graph, which the method requires before registration. The 46 claims have 119 early source records between them.

Each early source was classified from the registration's own `already_seen`, `data_seen` or `plan` text, the SoQL in the outcome's source record, the referee report in `critique/<id>.md`, and git history. Two claims, construction2-rows-per-job-dobnow and construction2-rows-per-job-legacy-2000s, have no referee report.

The classes are:

- (a) exposure or treatment only, not the outcome;
- (b) a design, power or calibration read, pre-period data, or metadata, which does not decide the verdict;
- (c) a shared cache: the same query was fetched for an earlier claim and holds this claim's outcome, so the registrant could have seen it;
- (d) the outcome data were read for this claim before registration;
- (e) cannot tell;
- (f) no early read of city data. The fetch time is a date without a clock time, the fetch time was misparsed, or the source is a published benchmark quoted in the registration. This class was added because four records fit none of the others.

## Counts

| Class | Early source records | Claims whose most serious early class is this |
|---|---|---|
| (a) exposure or treatment | 46 | 20 |
| (b) design, pre-period or metadata | 44 | 10 |
| (c) shared cache holding the outcome | 19 | 10 |
| (d) outcome read before registration | 5 | 2 |
| (e) cannot tell | 1 | 1 |
| (f) no early read of city data | 4 | 3 |
| Total | 119 | 46 |

The order of seriousness used in the last column is d, e, c, then a, b and f. Thirty-three of the 46 claims have only early fetches of class a, b or f.

## Claims in classes c, d and e

| Claim | Verdict | Class | Early source | Earlier claim | Did the earlier claim reveal the deciding number? |
|---|---|---|---|---|---|
| afford-gentrification-prevalence | confirmed | d | Furman CoreData workbook | none | Not applicable. A faulty simulation multiplied the real later-year values by noise, and the registrant read its output (k = 6, rho 0.38). The registration discloses this. |
| heat-extremes-downturn | contested | d | Phoenix, Tucson, Dallas and Austin assault counts | none | Not applicable. The four deciding series were built before registration. The registrant states that only yearly totals and mean daily counts were read, and none against temperature. The referee could not confirm this from the repository. |
| afford-poor-count-shift | confirmed | e | Furman CoreData workbook | none | Not applicable. The workbook holds the outcome. The registrant says the simulated output was cut before this claim's numbers. The referee found this consistent "to the line" but not confirmable. |
| construction2-rows-per-job-legacy-2000s | confirmed | c | ipu4-2q9a, legacy NB permits | construction-permit-funnel | Partly. A figure of about 5.1 rows per job for all jobs before 2010 was derived and disclosed; the threshold is 5.0 and the result 5.89. The 2000-2009 cohort means were not computed. |
| ems-taxi-2026-onset | unsettled | c | 76xm-jjuj, EMS 2019-2026 | bridge-crz-ems-travel | No. The weekly slope and the 2026 step were not computed. The January 2026 taxi slowdown was known, so the referee calls the test not blind to the timing of the step. |
| ems-traffic-hourly-elasticity | confirmed | c | 76xm-jjuj, EMS 2019-2026 | bridge-crz-ems-travel | No. A monthly pre-period elasticity of 0.32 was known and disclosed; the hourly elasticity was not computed. |
| ems-traffic-share-2019-2026 | confirmed | c | 76xm-jjuj, EMS 2019-2026 | bridge-crz-ems-travel | Partly. The registrant knew that taxi speed fell 6 to 9% in early 2026 and that EMS travel time rose. The share S1 was not computed. |
| heat-mech-intox | unsettled | c | 5ucz-vwe8, 833y-fsy8, NYPD shootings | heat-shootings | No. The total temperature slope was known; the share removed by the mediator needs the EMS series fetched after registration. |
| heat-mech-outdoors | confirmed | c | 5ucz-vwe8, 833y-fsy8, NYPD shootings | heat-shootings | No. As for heat-mech-intox; the 311 series was fetched after registration. |
| heat-trees-canopy-within-nta | confirmed | c | qdq3-9eqn, hyperlocal temperatures | heat-trees-airtemp-hyperlocal | No. The earlier claim used street-tree counts. The vegetation values at the sensors were computed after registration (file times checked by the referee). |
| stalled-421a-vesting-footings | contested | c | bs8b-p36w, pkdm-hqz6, certificates of occupancy | construction-four-year-completion | Partly. Four-year completion shares by first-permit year were published. The 36-month rates by foundation window were not. |
| stalled-flood-zone-starts | unsettled | c | bs8b-p36w, pkdm-hqz6, certificates of occupancy | stalled-421a-vesting-footings | No. The no-CO status of every job and its borough was seen, but the floodplain flags were fetched later, so the deciding difference was not. |
| transfer-chicago-hot-end | unsettled | c | gumc-mgzr, ijzp-q8t2, Chicago shootings | transfer-chicago-heat-shootings | Partly. Unadjusted daily means by temperature bin were known for the shootings half of part (a). The Divvy half, also deciding, was fetched after registration. |

For the three EMS claims, the recorded fetch time (13:10:56) belongs to a 2017-2018 calibration query. The same source record also covers the 2019-2026 EMS rows. Those were fetched between 07:56 and 08:09 for bridge-crz-ems-travel and committed at 08:44:57, before these claims were registered at 13:27:12.

## What the timestamps show and do not show

The fetch times show when a query was first sent and when its result was cached. They do not show when, or whether, a person or agent looked at the result. A fetch before registration shows that the registrant could have seen the data, not that the registrant did. In class (c) the data were on disk because an earlier claim needed them. Whether the registrant opened them rests on the registration's own statement and, where one exists, on the referee's checks of file times and git history.

In 33 of the 46 claims, the timestamps support registration before data. In those claims every early fetch was exposure or treatment data, a design or pre-period read, metadata, or a record with no clock time.

In two claims the outcome data were read for that claim before registration. Both registrants disclosed this in the registration. In afford-gentrification-prevalence a noisy copy of the outcome was read. In heat-extremes-downturn the deciding series were built and summarised, and the registrant states that no model against temperature was fitted. Neither verdict can be presented as a blind test.

For afford-poor-count-shift, the record cannot settle whether the outcome was seen. In ten claims the outcome data were in a shared cache, and in four of these an earlier result partly revealed the deciding quantity.

The check covers only sources with a recorded fetch time. Several sources have none and are not checked. Examples found in this audit are the Local Law 84 file reused by further-datacentre-share-manhattan-v2 (fetched at 20:26:27 for the first data-centre claim), the 2023 EMS totals by call type known to bridge-shot-ems-link, and the rent variable `d_logrent` on disk before all-boats-trees-rent. Each of the three registrations discloses the case.

Two further limits apply. The comparison uses `registered_at`, the time written into the hashed registration file. That time can differ from the first commit of the file on `main`. For bridge-crz-ems-travel, for example, the `prereg/` branch commit is at 08:05:20, while the file first appears on `main` at 08:44:57. The page now draws its registration line at `registered_at` and marks the commit on `main` separately. Second, fetch times recorded as a date only (`2026-11-12`) or as a range (`2026-11-12/13`) are read as midnight or as a misparsed hour. For further-zonej-demand-growth this made data fetched at 20:23 appear to come before the registration at 20:23:09; it is class (f).

Under the registered_at rule, sim-crz-holdout-2026 has no early fetch. Its fetches at 08:06 and 08:08 come after its registered_at (08:05:49) and before its commit on `main` (08:44:57), so the page marked them orange under the old rule.
