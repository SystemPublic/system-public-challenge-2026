# thermal_sim parameters

Generated from `params.py` by `python -m thermal_sim.make_docs`. Do not edit by hand.

**Kinds:** `handbook` = engineering handbook / textbook value; `model` = published empirical model; `regulatory` = standard or label definition; `assumption` = our assumption; `free` = assumption, tuned in VALIDATION.md.

Handbook and model references are standard texts cited by name from general knowledge; they were **not re-checked page-by-page in this session**. No journal citation in this table was invented: where we had no source, the row says `assumption`.

## site

| key | value | unit | kind | source | meaning |
|---|---|---|---|---|---|
| `lat_deg` | 40.85 | deg N | assumption | SBH Health System, Bronx (approx.) | Latitude used for sun position |
| `lon_deg` | -73.89 | deg E | assumption | SBH Health System, Bronx (approx.) | Longitude used for sun position |
| `utc_offset_h` | -4 | h | regulatory | US Eastern Daylight Time | Fixed local-time offset (summer). Use -5 in winter. |

## solar

| key | value | unit | kind | source | meaning |
|---|---|---|---|---|---|
| `solar_const` | 1367 | W/m2 | handbook | Duffie & Beckman, Solar Engineering of Thermal Processes | Solar constant for extraterrestrial irradiance |
| `haurwitz_a` | 1098 | W/m2 | model | Haurwitz (1945) clear-sky model, as implemented in pvlib | GHI_clear = a*cosZ*exp(-b/cosZ) |
| `haurwitz_b` | 0.057 | - | model | Haurwitz (1945) clear-sky model, as implemented in pvlib | Haurwitz exponent |
| `kc_a` | 0.75 | - | model | Kasten & Czeplak (1980) cloud correction | GHI = GHI_clear*(1 - a*N^b), N = cloud fraction |
| `kc_b` | 3.4 | - | model | Kasten & Czeplak (1980) cloud correction | Cloud exponent |
| `ground_albedo` | 0.2 | - | handbook | Duffie & Beckman, Solar Engineering of Thermal Processes | Ground reflectance for reflected irradiance on vertical faces |
| `cosz_min` | 0.02 | - | assumption | numerical guard | Below this cos(zenith) beam irradiance is set to zero |

## heat

| key | value | unit | kind | source | meaning |
|---|---|---|---|---|---|
| `R_film_still` | 0.12 | m2K/W | handbook | ASHRAE Handbook - Fundamentals (surface film / sol-air chapter) (still-air film, vertical surface) | Still-air surface film resistance (convection + radiation) indoors/inside enclosures |
| `hc_a` | 5.7 | W/m2K | handbook | McAdams wind correlation, as given in Duffie & Beckman, Solar Engineering of Thermal Processes | Outdoor convection h_c = a + b*v |
| `hc_b` | 3.8 | W s/m3K | handbook | McAdams wind correlation, as given in Duffie & Beckman, Solar Engineering of Thermal Processes | Wind slope of outdoor convection |
| `emissivity` | 0.9 | - | handbook | Incropera & DeWitt, Fundamentals of Heat and Mass Transfer (property tables) (paper, paint, plastics ~0.9) | Long-wave emissivity of package/mailbox surfaces |
| `sigma` | 5.67e-08 | W/m2K4 | handbook | Stefan-Boltzmann constant | Used to linearise radiation h_r = 4*eps*sigma*T^3 |
| `lw_sky_deficit` | 63 | W/m2 | handbook | ASHRAE Handbook - Fundamentals (surface film / sol-air chapter) (sol-air temperature, horizontal surface) | Long-wave sky radiation deficit for an upward face under clear sky; scaled by (1 - cloud) |
| `porch_wind_factor` | 0.3 | - | assumption | sheltering of a doorstep vs the 10 m airport anemometer | Wind at package = factor * station wind |
| `porch_wind_min` | 0.5 | m/s | assumption | residual air movement | Minimum wind at package |
| `R_contact_floor` | 0.05 | m2K/W | assumption | contact of a soft package with a porch floor | Resistance between package bottom and the floor surface |
| `floor_absorptance` | 0.65 | - | assumption | weathered concrete/wood (typical 0.6-0.7) | Solar absorptance of a sunlit porch floor |
| `h_floor_eff` | 25 | W/m2K | assumption | effective loss coefficient incl. conduction into slab | Floor sol-air rise = a_floor*GHI/h_floor_eff |
| `shade_diffuse_factor` | 0.3 | - | assumption | covered porch sees part of the sky | Fraction of diffuse irradiance reaching a package in shade |

## env

| key | value | unit | kind | source | meaning |
|---|---|---|---|---|---|
| `pharmacy_c` | 22 | degC | assumption | pharmacy HVAC; inside USP controlled room temperature 20-25 C | Pharmacy / dispensing area temperature |
| `fridge_c` | 5 | degC | regulatory | label 2-8 C refrigerated storage (midpoint) | Dispense temperature for refrigerated products |
| `truck_beta` | 0 (prior 10) | degC per kW/m2 | free | assumption; calibrated in VALIDATION.md (best fit to JAPhA 2023, 20-25 C reading; at the grid bound) | Cargo-area rise above ambient per kW/m2 of horizontal sun |
| `truck_tau_min` | 30 | min | assumption | thermal lag of a box truck cargo area | First-order lag of cargo air towards its target |
| `hub_f` | 0 (prior 1) | - | free | assumption; calibrated in VALIDATION.md (best fit to JAPhA 2023, 20-25 C reading; at the grid bound) | Fraction of the outdoor swing that reaches a sorting hub (0 = fully conditioned at hub_set_c, 1 = unconditioned) |
| `hub_set_c` | 22 | degC | assumption | conditioned-building reference | Hub temperature if fully conditioned |
| `hub_tau_h` | 4 | h | assumption | large unconditioned building lag | Lag of hub air behind outdoor air |
| `hub_gain_c` | 1 | degC | assumption | roof gain / equipment | Offset of an unconditioned hub above lagged outdoor air |
| `home_tau_h` | 6 | h | assumption | masonry apartment thermal lag (order of hours) | Lag of indoor air behind outdoor air without AC |
| `home_gain_c` | 1.5 | degC | assumption | internal + solar gains | Indoor offset above lagged outdoor air without AC |
| `home_topfloor_c` | 2.5 | degC | assumption | roof solar gain on top-floor units | Extra offset for a top-floor apartment |
| `home_ac_set_c` | 24 | degC | assumption | typical cooling setpoint | Apartment with working AC: min(setpoint, no-AC temperature) |
| `lobby_c` | 24 | degC | assumption | conditioned lobby / package room / pickup locker | Indoor drop point temperature |

## mailbox

| key | value | unit | kind | source | meaning |
|---|---|---|---|---|---|
| `L` | 0.48 | m | assumption | standard curbside (T1-size) mailbox, approx. | Length |
| `W` | 0.165 | m | assumption | standard curbside (T1-size) mailbox, approx. | Width |
| `H` | 0.23 | m | assumption | standard curbside (T1-size) mailbox, approx. | Height |
| `mass_kg` | 1.8 | kg | assumption | thin galvanised/painted steel shell | Shell mass |
| `c` | 490 | J/kgK | handbook | Incropera & DeWitt, Fundamentals of Heat and Mass Transfer (property tables) (carbon steel) | Specific heat of steel |
| `absorptance` | 0.9 | - | assumption | dark painted metal (black paint 0.9-0.97) | Solar absorptance of shell |

## num

| key | value | unit | kind | source | meaning |
|---|---|---|---|---|---|
| `dt_s` | 60 | s | assumption | numerical | Integration step (exponential integrator, unconditionally stable) |

## mkt

| key | value | unit | kind | source | meaning |
|---|---|---|---|---|---|
| `delta_h_kj_mol` | 83.144 | kJ/mol | regulatory | USP <1079.2> default activation energy for MKT | Default activation energy (configurable per drug) |
| `R_gas` | 8.3144 | J/molK | handbook | gas constant | Universal gas constant |

## coolant (shared)

| key | value | unit | kind | source | meaning |
|---|---|---|---|---|---|
| `wall_fraction` | 0.8 | - | assumption | standard pack-out: packs placed around the payload (top, bottom, sides) | Share of wall heat flow intercepted by the coolant before it reaches the product |

## coolant type `water_gel`

| key | value | unit | kind | source | meaning |
|---|---|---|---|---|---|
| `melt_c` | 0 | degC | handbook | water-based gel packs melt near 0 C | Melting point of gel/ice packs |
| `latent_j_kg` | 334000 | J/kg | handbook | Incropera & DeWitt, Fundamentals of Heat and Mass Transfer (property tables) (latent heat of fusion of water) | Latent heat of fusion |
| `c_solid` | 2050 | J/kgK | handbook | Incropera & DeWitt, Fundamentals of Heat and Mass Transfer (property tables) (ice) | Specific heat, frozen |
| `c_liquid` | 4186 | J/kgK | handbook | Incropera & DeWitt, Fundamentals of Heat and Mass Transfer (property tables) (water) | Specific heat, liquid (gel packs ~ water) |

## coolant type `pcm_22`

| key | value | unit | kind | source | meaning |
|---|---|---|---|---|---|
| `melt_c` | 22 | degC | assumption | room-temperature phase-change packs sold for controlled-room-temperature shipping (melt ~20-22 C) | Melting point of a CRT phase-change pack |
| `latent_j_kg` | 180000 | J/kg | assumption | paraffin / salt-hydrate PCMs are typically 150-250 kJ/kg | Latent heat of the PCM |
| `c_solid` | 2000 | J/kgK | assumption | paraffin-type PCM | Specific heat, solid |
| `c_liquid` | 2200 | J/kgK | assumption | paraffin-type PCM | Specific heat, liquid |

## packaging

| id | outer L x W x H (m) | R_wall (m2K/W) | solar absorptance | contents (kg x J/kgK) | wall heat capacity (J/m2K) | coolant | sources / assumptions |
|---|---|---|---|---|---|---|---|
| `poly_mailer` | 0.25 x 0.18 x 0.05 | 0.002 | 0.4 | 0.25 x 1500 | 0 | none | R_wall: assumption: 0.07 mm LDPE + thin paper bag, k~0.3 W/mK -> negligible; absorptance: assumption: white/grey film 0.3-0.5; dims: assumption: typical pharmacy mailer 25x18x5 cm; contents: assumption: 0.25 kg of bottles/pens/paper, c ~1500 J/kgK (plastic 1500-1900, glass 840, paper 1340) |
| `padded_mailer` | 0.25 x 0.18 x 0.05 | 0.1 | 0.75 | 0.25 x 1500 | 0 | none | R_wall: assumption: ~4 mm bubble lining, k~0.04 W/mK -> 0.1 m2K/W; absorptance: assumption: kraft paper 0.7-0.8 |
| `insulated_box` | 0.3 x 0.25 x 0.25 | 1.15 | 0.75 | 0.25 x 1500 | 988 | none | wall_c: 38 mm EPS, density 20 kg/m3 (handbook range 15-30), c 1300 J/kgK -> 988 J/m2K, modeled as a mid-wall node (2R1C); R_wall: 38 mm (1.5 in) EPS, k=0.035 W/mK (handbook range 0.033-0.040) -> 1.09, + corrugated carton ~0.06; absorptance: assumption: brown corrugated carton 0.7-0.8; dims: assumption: small pharmacy cold-chain shipper 30x25x25 cm |
| `insulated_box_cold_pack` | 0.3 x 0.25 x 0.25 | 1.15 | 0.75 | 0.25 x 1500 | 988 | 1.5 kg water_gel from 5 C, product-coolant 1 W/K | coolant: assumption: 3 x 0.5 kg gel packs conditioned in a 2-8 C fridge (no latent heat available); product-coolant conductance 1.0 W/K (assumption) |
| `insulated_box_frozen_pack` | 0.3 x 0.25 x 0.25 | 1.15 | 0.75 | 0.25 x 1500 | 988 | 1.5 kg water_gel from -10 C, product-coolant 1 W/K | coolant: assumption: 3 x 0.5 kg gel packs from a freezer at -10 C (uses latent heat of melting); payload in contact with packs through a thin divider (product-coolant conductance 1.0 W/K, assumption) |
| `insulated_box_frozen_pack_buffered` | 0.3 x 0.25 x 0.25 | 1.15 | 0.75 | 0.25 x 1500 | 988 | 1.5 kg water_gel from -0.5 C, product-coolant 0.15 W/K | coolant: assumption: frozen packs 'conditioned' at room temperature until they start to melt (-0.5 C, still solid: full latent heat available) and a bubble-wrap/cardboard buffer around the payload (product-coolant conductance 0.15 W/K), the usual way to avoid freezing insulin |
| `insulated_box_crt_pcm` | 0.3 x 0.25 x 0.25 | 1.15 | 0.75 | 0.25 x 1500 | 988 | 1.5 kg pcm_22 from 18 C, product-coolant 1 W/K | coolant: assumption: 3 x 0.5 kg 22 C phase-change packs conditioned solid at 18 C, so a room-temperature drug is neither heated above ~22 C nor chilled below 15 C while they melt |

## environments

| code | meaning | how it is modeled |
|---|---|---|
| `pharmacy` | Climate-controlled pharmacy | constant `env.pharmacy_c`, still air, no sun |
| `fridge` | Pharmacy refrigerator | constant `env.fridge_c` (only used as the dispense point of cold-chain drugs) |
| `truck` | Delivery truck / trailer cargo area | cargo air lags `T_out + truck_beta * GHI/1000` with time constant `truck_tau_min`; still air, no sun on the package |
| `hub` | Carrier sorting hub | `hub_set_c + hub_f * (lag_hub_tau_h(T_out) + hub_gain_c - hub_set_c)`; still air |
| `porch_shade` | Doorstep in shade | outdoor air, porch-level wind, `shade_diffuse_factor` of diffuse light, floor at air temperature |
| `porch_sun` | Doorstep in direct sun | outdoor air, porch-level wind, beam + diffuse + ground-reflected sun on top and (random-azimuth) sides, long-wave sky loss on top, bottom on a sun-heated floor |
| `mailbox_sun` | Metal mailbox in sun | steel shell node heated by sun and cooled by wind; package inside sees the shell temperature through still air |
| `lobby` | Building lobby / package room / pickup locker | constant `env.lobby_c` (conditioned lobby, package room or locker) |
| `home_ac` | Apartment with AC | `min(home_ac_set_c, no-AC temperature)` |
| `home_noac` | Apartment without AC | `lag_home_tau_h(T_out) + home_gain_c` |
| `home_noac_top` | Top-floor apartment without AC | no-AC temperature + `home_topfloor_c` |
