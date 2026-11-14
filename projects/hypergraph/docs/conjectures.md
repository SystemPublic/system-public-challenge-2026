# Rival conjectures for one edge

Written 14 November 2026. Sources for the literature are in `notes/conjecture_sources.md`; every PubMed identifier there was checked, and the abstracts, not the full texts, were read.

The city's records show that shootings rise with temperature (1.15 per 5 °C in New York) and do not show why. A graph of findings is useful here in a second way. It supplies candidate reasons, and it shows which of them have evidence and of what kind. This note sets out five conjectures, a test that narrows them, and two related questions: whether the prescriber's ZIP code can stand in for the patient's, and whether the full moon changes anything.

## Five conjectures

| Conjecture | Evidence in the literature | Our tests | Predicts a rise in shootings inside? |
|---|---|---|---|
| People outdoors. Heat brings people into contact. | Indirect. Larger effect at weekends (Reeping 2020). | Street-noise complaints remove 44% of the slope (confirmed). Bicycle counts remove 4%. | No |
| Alcohol and drugs. | Alcohol hospital visits rise 24.6% from the coldest days to the 75th percentile (Parks 2023). No study links this to violence. | Ambulance dispatches for drugs and alcohol remove 14% (unsettled). | Partly, since people drink at home |
| Short temper. Heat acts directly on mood. | Laboratory meta-analysis finds no reliable effect (Lynott 2023, preprint). Prisons without cooling have about 20% more violence on hot days (Mukherjee 2021, from a secondary source). | None before today. | Yes |
| Sleep loss after hot nights. | Hot nights shorten sleep. Experiments on sleep loss and aggression are not significant (Van Veen 2022). | Night minimum at a fixed maximum: 1.03 (0.96 to 1.11), unsettled. | Yes |
| Medicines that impair cooling. | Antipsychotics raise heat illness (odds ratio 4.6, Martin-Latry 2007). No study of medication, heat and violence. Layton 2020 found no interaction of heat waves and these medicines for admissions. | Psychiatric ambulance calls rise 1.02 per 5 °C, less than shootings, and remove none of the slope. | Yes |

Serotonin (Tiihonen 2017) is a proposed bodily path for the third conjecture and rests on a monthly correlation.

## A test that narrows them

The conjectures that act on the body act on a person wherever the person is. The first conjecture acts only where people meet. The police record whether each shooting happened inside or outside, so the two groups predict different slopes for shootings inside.

Two claims were registered on 14 November before any dated count by location was fetched: `heat-inside-outside` (2022 to 2026) and `heat-inside-outside-2006` (2006 to 2026). The second was added when the year-to-date file turned out to hold the field for every year.

| Window | Outside, per 5 °C | Inside, per 5 °C | Ratio inside to outside |
|---|---|---|---|
| 2006 to 2026 (20,958 outside, 3,471 inside) | 1.174 (1.155 to 1.192) | 1.009 (0.975 to 1.044) | 0.861 (0.828 to 0.896) |
| 2022 to 2026 (3,646 outside, 655 inside) | 1.156 (1.115 to 1.198) | 0.992 (0.917 to 1.072) | 0.860 (0.787 to 0.939) |

Shootings outside rise with heat. Shootings inside do not. Both claims are confirmed by their registered rule, and they are one result on two windows. The registered script understated the standard error of the ratio by a factor of about 1.7; the intervals in the table are the referee's corrected ones (`critique/referee_2026-11-14_moon_inside.md`). The ratio stays between 0.84 and 0.87 with year-by-month terms, in May to September alone, and without 2020 and 2021.

The result is what the first conjecture predicts. It does not separate that conjecture from a direct effect of heat on people who are outdoors: most indoor spaces are cooled, so a direct effect also predicts a smaller rise inside. The referee made this point, and it limits the claim. What the result counts against is a bodily effect that follows people indoors on the same day. Effects that carry over from a hot night, or that depend on medication, were not tested with lags. Flat inside counts are also consistent with a direct rise offset by people leaving their homes, and shootings inside are a different mix of events. The prison result (Mukherjee 2021) remains evidence that heat can raise violence with contact held roughly fixed.

## Does the prescriber's ZIP code stand in for the patient's?

The public data on antipsychotic prescribing in New York (Medicare Part D) give the prescriber's address. The literature search found no study that validates this as a proxy for where patients live, and none that gives the share of antipsychotic prescriptions written in the patient's own ZIP code. The nearest evidence is for buprenorphine in West Virginia Medicaid, where the prescriber used was on average 33.6 miles away when the nearest was 7.1 (Saloner 2022).

A check on our own files (exploratory, not registered) suggests the proxy is weak in New York. If patients saw prescribers in their own ZIP code, Part D claims per resident would vary across ZIP codes about as much as the share of older residents does. Among the 185 ZIP codes with more than 5,000 residents, claims per resident run from 0.35 at the 5th percentile to 17.6 at the 95th, a factor of 50. The rank correlation of claims with population is 0.61. The top tenth of ZIP codes by antipsychotic claims hold 39.5% of those claims and 13.5% of residents. Prescribing is concentrated where hospitals and clinics are.

Suppose the proxy were good. That would make the conjecture testable with public data: `docs/heat_drugs.md` computed that a test by ZIP code could detect a tripled hot-day excess among users. It would not make a positive result readable as a drug effect, for three reasons.

- People who take an antipsychotic have the illness it treats. A steeper rise in high-prescribing areas could come from the illness, from housing without cooling, or from poverty.
- The comparison is between areas, and the conjecture is about persons.
- The size required is large. If people taking antipsychotics were involved in 4% of shootings (a figure quoted from memory of the literature on serious mental illness and violence, not checked today), their rate would have to rise by 75% on a hot day to account for one fifth of the 15% rise.

If the proxy is weak, as the check suggests, the error biases any area comparison toward no difference, so a null result would not count against the conjecture either. The proxy therefore hurts in both directions: a positive result cannot be attributed to the drug, and a null cannot refute it. The test that would decide is within persons: Medicaid pharmacy claims linked to emergency visits or arrests, comparing the same person on hot and cool days (the design of Layton 2020).

One result already in hand counts against the conjecture as an account of shootings: psychiatric ambulance calls rise less with heat than shootings do and remove none of the slope. The inside result adds little here, because it does not test medication.

## The full moon

The belief that a full moon brings more crime, accidents and emergency visits is common among police and hospital staff. The graph holds 60 findings on lunar variables from 36 studies. They include 1.042 (1.021 to 1.063) for ambulance transports after road crashes in Japan (Onozuka 2018), 0.85 (0.77 to 0.94) for homicides in Finland, and 1.007 (0.993 to 1.021) for cardiac arrest.

The claim `moon-full-emergencies` was registered before the test was run, as a prediction of no effect with equivalence bounds. For the three days around each full moon:

| Outcome | Years | Full moon | 23-day placebo cycle |
|---|---|---|---|
| Shootings | 2006 to 2025 | 1.007 (0.966 to 1.049) | 1.008 (0.969 to 1.048) |
| Ambulance incidents | 2017 to 2026 | 0.997 (0.991 to 1.004) | 0.998 (0.993 to 1.003) |
| Injury crashes | 2014 to 2025 | 1.002 (0.987 to 1.018) | 1.002 (0.988 to 1.016) |

All three intervals are inside their registered bounds, so the claim is confirmed, and the referee found the same under other error models and under 5- and 7-day windows. The Japanese estimate of 1.042 is for full-moon nights. Spread over three whole days it would be about 1.004, which the crash interval does not exclude, so the two do not conflict. The referee also found one unexplained pattern outside the registered window: shootings are lower in a window four days before the full moon (0.914, z = -3.9, in both decades). It was found by searching every position in the cycle and decides nothing. The test uses whole days. It cannot see an effect of moonlight on night hours, which is the one path with support elsewhere (Redelmeier 2017 for motorcycle deaths at night).

## Files

- `analyses/heat_inside/`, `analyses/moon/`: registrations, scripts and outcomes.
- `viz/comics.html`: the strips "One edge, five conjectures" and "The full moon".
- `notes/conjecture_sources.md`: the literature tables.
