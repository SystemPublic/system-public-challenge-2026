# Referee report: transit-gtrain-substitution

Verdict recorded: unsettled. Recommendation: keep the verdict.

Scratch work is in the session scratchpad under `referee-transit-gtrain-substitution/` (`reest.py`, `var.py`). It uses `data/derived/transit/gtrain_panel.csv`, the saved permutation draws, the cached station table and the taxi zone shapefile. I made no new queries.

## (a) Does the verdict follow from the registered conditions?

Yes. Support needed four conditions. The first stage passes (entries at stations coded closed fell 98.9%), the clustered interval excludes zero (+0.0013 to +0.0844), and the 2023 placebo includes zero. The permutation p-value is 0.189, above the required 0.05, so support fails. Refutation needed the upper end of the interval below +0.02, and it is +0.084. Neither condition is met, and the verdict is unsettled under rule 2. Nothing was decided by a measure chosen after the data. The observation that the effect is largest in Greenpoint is reported as unregistered.

The timestamps are in order. The registration was committed at 20:17:01 on 12 November, and the branch `prereg/transit-gtrain-substitution` exists on GitHub with a commit at 20:17:09 that holds the same file. The subway entries were fetched at 20:27:53 and 20:27:55, and the nine trip files between 20:28:00 and 20:28:29. The outcome was decided at 20:31:21. The stored hash of the registration matches its content. The use of the TLC parquet files is the registered fallback. The analysis scripts were first committed with the outcome; I read them against the plan and they follow it.

## (b) Errors in code, units, joins, dates, geography or uncertainty

I reproduced the primary estimate exactly: +0.0429 (se 0.0212), 7 treated and 32 control zones, 4,680 zone-days. The saved permutation draws give p = 0.189 and a standard deviation of 0.0324. A fresh run of 2,000 draws with another seed gives p = 0.18. The shutdown dates and phases agree with the announcements.

The registration contradicts itself on one zone. Its rule treats a zone when a station "served only by the G (no other line in the station complex)" lost service. Zone 256 (Williamsburg South Side) is listed as treated for Metropolitan Av, which is in complex 629 with the L at Lorimer St. The analysis follows the list, which is the more specific statement. Without zone 256 the estimate is +0.051 (se 0.022) and the permutation p is 0.15.

The zone assignment of stations is fragile. By the shapefile, the Broadway station is 1 metre from the border between zone 80 and zone 256, Classon Av is 6 metres from the border of zone 17, Flushing Av is about 100 metres from zone 217 (a control) and Nassau Av about 130 metres from zone 255 (a control). Riders displaced from these stations are picked up on both sides of the border. The registered sensitivity without adjacent controls (+0.035) covers part of this.

The robustness variants I ran that the registrant did not are these.

| Variant | closed_here | Note |
|---|---|---|
| Registered primary | +0.043 (se 0.021) | permutation p 0.19 |
| Zones weighted by June pickups | +0.020 (se 0.020) | agrees with the registered Poisson, +0.016 |
| Zone-specific linear trends | +0.042 (se 0.022) | |
| Without 8-9 June (weekend closure in the reference period) | +0.048 (se 0.021) | |
| June as the only reference (treated-by-September term added) | +0.057 (se 0.022) | permutation p 0.052; treated zones in September +0.028 (se 0.015) |
| Weekends only | +0.013 (se 0.022) | weekdays, registered, +0.051 |
| Triple difference with 2023, permutation inference | +0.045 (se 0.020) | permutation p 0.047, sd 0.023 (1,000 draws) |

Two of these matter. The weighted estimate is half the primary one, so the result leans on the smaller treated zones and is not a 4 percent rise in pickups overall. In the other direction, the triple difference has a permutation p just under 0.05, because differencing against 2023 removes part of the noise between neighbourhoods. That p-value was not a registered condition, and at 1,000 draws its own sampling error is about 0.007, so it decides nothing; it suggests the registered permutation was the less powerful of two reasonable designs. Treated zones were also 2.8 percent above their June level in September, after service returned, which could be persistence or a difference in trend.

The dashboard stance (0.77, z 2.02) is computed from the clustered interval, which the outcome itself calls too narrow. With the permutation standard deviation z is 1.32. The stance overstates the evidence.

## (c) Is the comparison with the research fair?

The comparison is of direction only, and the outcome does not claim more. The cited studies of ride-hail entry (Hall, Graehler, Diao, Erhardt, Babar) measure the effect of ride-hail on transit ridership across cities over years. This claim measures the reverse direction, the effect of a loss of transit on ride-hail, within zones over weeks. Only Borowski et al. (Chicago rail disruptions) has the same exposure and outcome, and the registration quotes no effect size from it, so there is no published number to compare with +0.043. The predicted range of +0.02 to +0.12 is the registrant's own. There is no graph evidence for this claim, so there was no finding to check against PubMed.

The diversion figure of 4.8 pickups per 100 lost entries uses entries lost at closed stations as the denominator. The outcome notes that this overstates trips lost. It also counts only pickups in the treated zones, and the border problem above means some substitute trips were recorded in control zones.

## (d) Alternative explanation not addressed

The registration names the main ones. The one it does not address is that the reference period is itself affected. Entries on the open part of the line fell 15 to 60 percent while it was cut elsewhere, the weekend of 8-9 June had a closure, and September pickups in treated zones stayed above June. The estimate is a contrast between closure days and a mixture of June and September, and the two reference months give different answers (+0.057 against June alone). A summer trend specific to north Brooklyn is addressed only by the 2023 placebo, which is one year.

## (e) Could the test have failed?

Yes, in both directions. Refutation needed an estimate below about -0.02, which a real fall or a precise null would have produced. Support needed an absolute coefficient of at least 0.064 to reach a permutation p below 0.05. The lower half of the predicted range (+0.02 to +0.06) therefore could not have been confirmed even if true. If the true effect were +0.07, the chance of meeting the permutation condition was about 0.6; at +0.043 it was about 0.25.

This is not an endpoint or transfer test, but for reference: against no effect z is 2.02 with the clustered standard error and 1.32 with the permutation standard deviation. Against the middle of the predicted range (+0.07) z is -1.28 and -0.84. The estimate lies inside the predicted range.

Recommendation: keep. The registered permutation condition fails (p 0.19, 0.18 on re-run), the refutation condition fails, and the variants move the estimate between +0.02 and +0.06 without settling it.
