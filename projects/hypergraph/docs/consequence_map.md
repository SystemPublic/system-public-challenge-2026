# The re-timed week: a map of consequences

This is the plan for the main line of work at the hackathon on 13 and 14 November 2026. It takes one change in the city that the data measure well, asks the System Public Graph (a database of published research findings, called the graph below) what that change should do to people, and tests each prediction against the city's own records, area by area.

## The change

Subway entries show that the work week in the business district has shifted in time (`transit-weekday-pattern`, a claim already tested and confirmed). Tuesday to Thursday entries are within 2.8 percentage points of each other. Monday is 16% below midweek and Friday is 11% below. The combined Monday and Friday deficit relative to midweek was 5.1% in 2019 and is 13.8% now. The deficit grew by 15 points in the morning peak and by 5 points at midday. It did not grow in the evening, and Friday evening entries are now 9% above midweek.

The data measure the change but say nothing about its effects on each part of the city. A neighbourhood that sends fewer commuters downtown on Mondays keeps them at home, and a station area that receives fewer of them loses their lunches, their taxi rides and their presence on the street.

## The method

The method has four steps. Steps 1 and 4 use city data, step 2 uses the graph, and step 3 combines the two.

1. Measure the change for each area. For each of the 424 station complexes, and each weekday and hour band, compute entries now as a ratio of entries in 2019. This gives every area a dose, meaning how much its ridership thinned or thickened, and when. The data are the MTA hourly ridership files already used. The dose is the exposure the graph's findings describe, so computing it before registration reveals no outcome.
2. Ask the graph for consequences. Starting from the exposures the change alters, list every outcome the graph links to them, with the findings' sizes and how many have each sign. The graph files these exposures under study variables (the measures named in each paper), not under concepts: a variable search for "commute time" returns 19 findings on mental health and 16 on sleep, while a concept search returns nothing. The searches to run are commute time, commuting, telework or working from home, sedentary time, walking, physical activity, social isolation, loneliness, sleep duration, alcohol use by day of week, and crowding. Each result is checked against its abstract, because about a fifth of the graph's findings are mis-extracted.
3. Compose a prediction for each area. The dose from step 1 times the effect size from step 2 gives an expected change in the outcome for each neighbourhood, with an interval (`kit/bridge.py`, the project's bridge composer). The composer also reports whether a test of that size could fail. Predictions too small to detect are recorded as such and not tested.
4. Register, then test. Registering means writing the prediction, with the result that would support or refute it, to a file committed and pushed to the repository. Each prediction is registered before its outcome data are queried, as with every other claim in this project.

The map itself is the product: a diagram with the change at the centre and the consequences around it, and on each arrow what the research predicts and what the city data show. An arrow with no research in the graph is drawn as a gap. The causal view already draws this form.

## Candidate consequences

The graph is mostly biomedical, so it will supply the health arrows. The commercial and safety arrows have little research behind them in the graph, and several will be gaps. That contrast is a finding about what research exists.

| Consequence | Prediction to register | City data | Research side |
|---|---|---|---|
| Taxi and ride-hail demand | Pickups in the business district follow the Tuesday-to-Thursday shape, and Monday and Friday pickups rose in residential zones relative to 2019 | TLC trip records by zone, weekday and hour | Expected gap in the graph |
| Lunch trade | Midday entries fell less than commuting did, so restaurant closures in the business district since 2019 are no higher than in residential areas with similar rents | Restaurant inspection records (`43nn-pn8j`) for openings and closures | Expected gap |
| Drinking moved to Thursday | Alcohol-related emergency visits and EMS calls shifted from Friday toward Thursday relative to 2019 | Syndromic emergency visits by day; EMS dispatches (`76xm-jjuj`) | Graph findings on alcohol use and work schedules |
| Less walking | Areas with the largest fall in commute days show a rise in inactivity or obesity relative to others | Community Health Survey by neighbourhood | Graph findings on active commuting and weight |
| Sleep and mood | The same areas show better sleep or lower distress, as the commute findings predict | Community Health Survey | Graph: commute time to sleep (16 findings) and to mental health (19) |
| Crashes | Weekday crashes in the business district fell on Mondays and Fridays in proportion to entries, or by less, which would mean more risk per person | Crash records (`h9gi-nx95`) | Graph findings on traffic volume and injury |
| Safety in thinner crowds | Felonies per entry are higher in the station areas and hours that thinned most | NYPD complaints over hourly entries | Graph findings on crowding or guardianship, probably few |
| Daytime at home | Daytime residential burglaries fell most where commute days fell most | NYPD complaints by time and premise | Expected gap |

Six of these can be registered on Friday evening. The two health survey rows depend on the survey's latest year and may have to be registered as prospective claims, to be tested when newer data appear.

## What each machine does

The laptop has the System API key and the downloaded graph deposit, so steps 2 and 3 run there. Step 1 and the tests can run on either machine. Before Friday evening the dose map of step 1 can be built, and the eight predictions can be drafted as registration files with their graph evidence left open.

## What this adds to the work so far

The 44 claims registered so far each compare one published statement with one dataset. This line uses the graph for what a literature search cannot do: listing the consequences of a change, showing where no research exists, and giving each prediction an expected size before the data are seen. It also answers the third part of the hackathon challenge directly, because the gaps on the map are the research that is needed.

## Limits

Subway entries are a proxy for people present, and they miss those who walk, cycle or drive. The comparison with 2019 spans the pandemic, so some differences between areas come from population change and not from the change in the work week. Service cuts on Mondays and Fridays since 2023 are not separated from hybrid work. Health survey data are annual and cover large areas, so those tests will have little power. An area-level test cannot show what happened to individuals.
