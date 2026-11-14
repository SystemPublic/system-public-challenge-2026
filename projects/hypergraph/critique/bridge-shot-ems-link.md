# Referee report: bridge-shot-ems-link

Verdict recorded: confirmed. Recommendation: keep the verdict, but record it as a check on the structure of the records rather than a research link. Set the stance to null, and note that the coefficient is confounded by common daily drivers.

## (a) Was the prediction fixed before the data were queried?

Mostly. The registration (`f012e8d`, 16:04:50 on 12 November) precedes the daily EMS fetch (`76xm-jjuj-2ccf…`, 16:08:40). Before registration the registrant had fetched two summaries of the same dataset: the 2023 count by call type (`76xm-jjuj-961b…`, 15:59:20, showing 3,164 SHOT dispatches) and the date range (15:59:25). The 2023 NYPD count (974 incidents) was also known. The ratio of these, about 3.2 dispatches per incident, was known before the registered range of 0.6 to 1.6 was set. The registered quantity is a daily marginal slope, not the annual ratio, so this knowledge does not fix the answer. It was disclosed in the companion registration.

## (b) Errors in the model

The OLS regression of daily SHOT dispatches on daily NYPD incidents controls for day of week, month, year and holidays, but not for temperature, rain or time of night. Heat raises both shootings and shots-fired reports without a victim. The slope therefore includes part of the non-victim gradient that the companion bridge treats as the unknown k. For a link whose purpose is to separate victim dispatches from the rest, this confounding matters. Adding the day's TMAX and rain terms to the regression would show how much of the 1.25 is the common driver.

The two series are joined by calendar date: `occur_date` for the NYPD and the date of `incident_datetime` for EMS. Shootings shortly before midnight can generate dispatches dated the next day. This attenuates the slope slightly. A model with the next day's incidents as a second regressor would show the size of the effect.

The count is incidents, not victims. The NYPD's 5ucz-vwe8 file has one row per incident in the cache (`victims` equals `inc` in `5ucz-vwe8-cc5d…`). A slope of 1.25 per incident is close to the usual ratio of victims to incidents, which is consistent with about one dispatch per victim.

## (c) Independence

The link is estimated on the endpoint dataset of the companion bridge, on the same 7,548 days. The registration says this. The link's estimate was not used in the composition: the composition used w drawn from U(0.25, 0.5), fixed before the link was estimated. So the endpoint test of bridge-heat-shootings-ems is not circular through this link's number. But a link estimated on the endpoint data cannot be counted as an independent leg of the chain.

## (d) Is the test informative?

Not much. A person shot in New York is almost always reached by an ambulance, so a positive slope near one is a property of the records. The registered range, 0.6 to 1.6, is wide, and the only plausible refutation would be a slope near zero. The precision is high (standard error 0.026), so the test had full power against zero, but nobody expected zero. The graph has no finding on this link; `graph_effect` is null. A stance of 1.0 with z = 48 presents a record-keeping identity as strong agreement with research that does not exist.

## (e) Alternative not addressed

Duplicate dispatches for one victim (several callers, or a transfer between units) and dispatches for victims the NYPD does not record (self-inflicted wounds, wounds found later) both raise the slope. Neither can be separated without linked records, as the outcome's `settle` says.

## Recommendation

Keep confirmed. Under rule 6, set the stance to null, since there is no research estimate for the city effect to agree with. Report the slope with temperature and rain added, and with the next day's incidents, as sensitivity analyses.
