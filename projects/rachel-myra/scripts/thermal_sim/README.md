# thermal_sim: the Heat-Safe Delivery engine

A small, transparent physics model of **the drug in the box**: how hot a mailed
medicine gets as it moves pharmacy → carrier truck → sorting hub → doorstep or
mailbox → home, and what that means for the patient, in three plain tiers.

> **Honesty rule.** The engine reports temperatures, time above thresholds and
> mean kinetic temperature (MKT). Its advice has exactly three tiers:
> **use as normal** (within label), **check with your pharmacist** (beyond label,
> but within what a study tested), and **request a replacement** (beyond what
> studies tested, or at a level where a study found problems). It **never**
> outputs a "% potency left". We quantify the drug in the box, not the drug in
> the body.

## Pitch summary (5 lines)

1. We simulate a mailed medicine's temperature minute by minute from the pharmacy shelf to the patient's kitchen, using real hourly NYC weather and the sun's position.
2. On the hottest day of the June 2025 heat-wave replay (95 °F at 1:12 PM), an epinephrine auto-injector in a plain mailer on a sunny doorstep reaches about 52 °C (126 °F) within 30 minutes. In shade it stays near 36–38 °C (97–100 °F).
3. Each drug is judged against its own label and against the published studies that tested it in heat. Insulin pens tolerated 37 °C for 3 weeks in a trial, while test strips misread after 15 minutes at 42 °C.
4. Before shipping, the pharmacy sees a risk tier and one action: ship, upgrade to next-day, pack it insulated with temperature packs, reroute to pickup, or hold.
5. We never claim "% potency left". The tool says "within label", "within what studies tested" or "beyond what studies tested", and checks itself against published mail-order logger studies.

## What it models

**Product node** (drug + containers + pharmacy bag, `m·c`), heated or cooled
through each package face by a series of thermal resistances:

```
C dT/dt = Σ_faces U_f A_f (T_sa,f − T)
1/U_f   = 1/h_o + R_wall + R_film,in              (outside film, packaging, still air inside)
T_sa,f  = T_air + α q_f / h_o − ε ΔR (1−cloud)/h_o (sol-air temperature, ASHRAE; sky term on top face only)
```

With no packaging resistance this is exactly `m c dT/dt = h A (T_env − T) + α A_sun G`.
The sol-air form lets insulation correctly reject most of the absorbed sun.

* **Packaging** (`params.PACKAGING`): poly mailer, padded mailer, 38 mm EPS box
  (its wall heat capacity is a mid-wall node, 2R1C), and EPS box + gel packs:
  refrigerated 5 °C, frozen −10 °C, frozen with a buffer around the product, or
  22 °C phase-change packs for room-temperature drugs. Packs are an enthalpy
  node, so the latent heat of melting is included.
* **Environments**: climate-controlled pharmacy, pharmacy fridge, delivery truck
  or trailer cargo area (outdoor air plus a sun-driven offset, lagged), sorting
  hub (lagged outdoor air, partly conditioned), porch in shade, porch in direct
  sun (beam, diffuse and ground-reflected sun on top and sides, long-wave sky
  loss, sun-heated floor under the package), metal mailbox in sun (its own steel
  node), lobby/locker, apartment with AC, apartment without AC (6 h lag behind
  outdoor air plus gains), top-floor apartment without AC.
* **Sun**: NOAA solar-position equations for the Bronx, Haurwitz clear-sky
  irradiance, Kasten–Czeplak cloud correction, Erbs diffuse split. Cloud cover
  comes from the hourly LaGuardia observations.
* **Outputs per trace**: product temperature, peak, minutes above 25/30/37/40 °C,
  MKT (USP <1079.2>; ΔH = 83.144 kJ/mol by default, configurable per drug), and
  the advice tier with its reasons.
* **Pre-ship check** (`preship.py`): simulates the plan for every delivery hour
  in the window, keeps the worst case, and escalates in this order: ship as-is →
  next-day → insulated + packs → pickup → hold. It recommends the first plan that
  stays within label.

Every number is in `PARAMETERS.md`, which is generated from `params.py`. Each row
is marked handbook, model, regulatory, assumption or free. Drug limits and
evidence are in `data/processed/drug_storage_profiles.json`, and each citation
carries a status: verified, listing-only, unconfirmed, unverified-id, or
label-general-knowledge.

## What it does NOT model (read before quoting numbers)

* **No drug degradation kinetics and no potency.** MKT is reported as the
  industry exposure metric, not turned into a potency estimate.
* **Humidity**, which matters for test strips and tablets.
* **Body heat**: a pump worn on the body, or a pen in a pocket.
* **Measured truck and porch temperatures.** No porch study exists
  (docs/supply-chain.md calls this a gap). The truck offset and hub conditioning
  are free parameters, set in VALIDATION.md and still the weakest assumptions.
  The calibrated values sit at the coolest corner of the grid: truck cargo at
  outdoor air temperature and hubs at 22 °C. That is probably cool for NYC. Under
  the physically plausible alternative (sun-heated trucks, unconditioned hubs),
  the package reaches the door already at ~48 °C during the heat wave. Both cases
  are in `thermal_scenarios.json` (`hero` and `hero.sensitivity_hot_truck`).
* **Bronx microclimate.** Weather is from LaGuardia; urban heat-island
  differences between the airport and a Bronx stoop are not modeled.
* **Air-cargo legs** (treated as hub time), real carrier routes, package
  orientation changing over time, shading that moves across the day, and
  radiation from hot walls next to the porch.
* **The carry home** after a pharmacy or locker pickup.
* **Temperature inside the product.** The product is one lumped node; a
  multi-pen box is not resolved.
* **Daylight saving**: one fixed UTC offset is used (−4 h, summer).

## How to run

System Python is 3.9, so use uv (`~/.local/bin/uv`) with Python 3.12. Run from
`scripts/`:

```bash
cd scripts
UV="$HOME/.local/bin/uv run -q --python 3.12 --with numpy,pandas"
PYTHONPATH=. $UV python -m thermal_sim.make_docs     # PARAMETERS.md + lib/thermal/params.ts
PYTHONPATH=. $UV python -m thermal_sim.validation    # Monte-Carlo + grid search (~5 min) -> validation_results.json
PYTHONPATH=. $UV python -m thermal_sim.write_validation_md   # VALIDATION.md tables from the json
PYTHONPATH=. $UV python -m thermal_sim.scenarios     # data/processed/thermal_scenarios.json (~1 min)
PYTHONPATH=. $UV --with pytest python -m pytest thermal_sim/tests -q
cd .. && node --experimental-strip-types lib/thermal/test/compare.ts   # TS port == Python
```

Order matters after a parameter change: run `make_docs`, then `validation` (if
the free parameters or the physics changed), then `scenarios`, then the tests.
`test_generated_artifacts_match_params` fails if a generated file is stale.

### TypeScript port (`lib/thermal/`)

A dependency-free, line-by-line port: `model.ts` (weather, sun, package step),
`metrics.ts` (MKT, thresholds), `advice.ts`, `itinerary.ts`, `preship.ts`, and
`params.ts` (generated). Imports use `.ts` extensions so Node 24 runs them
directly. In Next.js, set `"allowImportingTsExtensions": true` in tsconfig
(Next already uses `noEmit`). See `lib/thermal/index.ts` for usage.

## Files

| file | what |
|---|---|
| `params.py` | every parameter (value, unit, kind, source) and packaging definitions |
| `model.py` | weather container, sun, vectorised package model (`run`, `simulate_legs`) |
| `metrics.py` | MKT, minutes above thresholds, summary |
| `advice.py` | three-tier advice from a trace and a drug profile |
| `itinerary.py` | next-day / 3-day ground leg templates (clock times are assumptions) |
| `preship.py` | pre-ship risk check |
| `weather_io.py` | NCEI ISD parsing, replay CSV loader |
| `batch.py` | many itineraries at once |
| `validation.py`, `write_validation_md.py` | Monte-Carlo validation and its report |
| `scenarios.py` | demo scenarios for the app |
| `make_docs.py` | generates `PARAMETERS.md` and `lib/thermal/params.ts` |
| `tests/test_model.py` | physics and honesty-rule tests |

## Data

* `data/raw/thermal_sim/isd_{central_park,laguardia}_{2024,2025}_JJA.csv`:
  NCEI Global Hourly (ISD) extracts (TMP, DEW, WND, GF1, GA1–GA3) for June–August,
  fetched 14 Nov 2026 from
  `https://www.ncei.noaa.gov/access/services/data/v1?dataset=global-hourly&stations=<USAF+WBAN>&startDate=…&endDate=…&format=csv`
  (Central Park 72505394728, LaGuardia 72503014732). They are treated as
  untrusted: values are range-checked and QC codes 3/7 are dropped. They drive
  the Monte-Carlo and supply cloud cover for the replay.
* `data/processed/replay_heatwave_hourly.csv` (written by another agent): the
  19–28 June 2025 heat-wave replay. LaGuardia temperature and wind are used,
  with 48 h of spin-up before it.
