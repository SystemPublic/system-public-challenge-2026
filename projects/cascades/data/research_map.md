# Where to collect data: worldwide source map (Eric, Nov 14)

Use this to compare against Christina's list. Every source has a `source_id` row in `data/sources.csv` (46 sources total, now also in the `sources` table in `retrofit.duckdb`).

**Rule for worldwide data:** use it, but tag every number with country/region and a transferability label:
- **High**: UK, or temperate high-income housing (Ireland, NZ, Northern Europe, northern US). Can stand in for the UK with a caveat.
- **Medium**: other high-income settings (US South, Australia, East Asia). Fine for mechanism, weaker for effect size.
- **Low**: LMIC solid-fuel or very different housing stock. Report it, but don't use it for UK decisions.

## Matrix: the client's 3 indicators × 8 groups

| Group | 1. Burden (health outcome) | 2. Prevention (does the fix work?) | 3. System cost | Biggest gap |
|---|---|---|---|---|
| Moisture & mould | EHS_LA, EHS_HH (UK); EUSILC_DAMP (Europe) | COCHRANE_MOULD (moderate to very low certainty); WAP_ORNL (US) | BRE (£38m/yr NHS) | No UK intervention trial; school evidence inconsistent |
| Building fabric | EHS, EPC (UK stock) | **WALES_NEST** (UK, linked GP records); COCHRANE_WARMTH; WHO_HHGL (conditional); WAP_ORNL; NZ_HHH | BRE; NICE_NG6 (>£100k/QALY untargeted, good when targeted) | Effects on carbon/energy are measured (NEED); health effects mostly modelled |
| Ventilation & source capture | SAMHE (UK schools); CLASP_GAS_EU | MENDELL_VENT (US); GAIHRE_SCOT (UK, small effect) | none | No trials. Only observational school studies |
| Particle filtration | UK_AIR (outdoor) | HAPI_HEPA (US RCT, small); CN_PURIFIER | none | No UK trials; classroom filter studies aren't in the graph |
| Clean cooking | WHO_GHO_HAP (solid fuel, global); CLASP_GAS_EU; US_GAS_ASTHMA (12%–12.7% PAF) | HAPIN (LMIC, **null**) | none | Gas→induction swap has no trial anywhere. Burden numbers are modelled and contested |
| Indoor temperature | FT_WINTER, UKHSA_HEAT (UK); GBD21 | COCHRANE_WARMTH; WHO_HHGL; EFUS (temps) | BRE (£540m–£857m cold); NICE_NG6 | Overheating: WHO couldn't set a threshold; almost no cooling-intervention evidence |
| Radon | RADON_ATLAS; GBD21 (82k deaths globally); GRAY_RADON (~1,100 UK deaths/yr) | none measured on health (only radon level drops) | GRAY_RADON (£36.8k/QALY retrofit vs £11.4k new-build); EPA_RADON_BCA | 0 intervention studies in the graph; cost-effectiveness is modelled |
| Allergen & pest | AHS23 (US) | COCHRANE_HDM (**null**, out of date) | none | Strong evidence that single measures don't work; multi-trigger programmes not reviewed |

## What this means for collection

1. **Strongest data for "where to invest"** (burden, fix and cost all present, UK or high-transfer): building fabric/heating (Wales Nest + Cochrane + NICE + BRE) and radon (burden + cost, but no measured health effect).
2. **Natural gap stories**: clean cooking in UK homes (large modelled burden, no intervention trial), school ventilation and filtration (sensors exist via SAMHE, outcomes don't), overheating (rising burden, no threshold).
3. **Null results are data too**: HAPIN and dust-mite control show that cutting exposure didn't change outcomes. Worth showing so the tool doesn't oversell.

## Still to fetch (open, downloadable)
- `GBD21`: IHME results tool, CSV (needs a free account; Christina or Eric can sign in)
- `EUSILC_DAMP`: Eurostat CSV
- `WHO_GHO_HAP`: OWID CSV
- `UKHSA_HEAT`: gov.uk spreadsheet
- Eric: run `./external/fetch_external2.sh` (raw2 is still empty)

## Caveats
- CLASP_GAS_EU isn't peer reviewed. The US/EU 12% figures are association-based attributable fractions, and researchers disagree about them.
- GAIHRE_SCOT: we took the effect size from a secondary review (AIVC). The original paper still needs checking.
- COCHRANE_HDM carries an editorial note saying it predates current standards.
