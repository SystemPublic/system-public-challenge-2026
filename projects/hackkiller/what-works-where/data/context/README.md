# Context data for the five-country showcase

Core: TZA, BEN, BFA, MLI, NGA. Supporting country metadata: GHA, GMB, TCD, UGA, KEN, SEN.

- `countries.csv`: 11 countries. Region/seasonality are coarse national grouping labels supplied by the team, not study-site facts. Nigeria: north seasonal, south perennial. Availability flags describe the downloaded data actually present.
- `context_country_year.csv`: 721 rows, WHO 331 + MAP 390. No unit conversions. WHO percentages and MAP proportions remain distinct. WHO IRS is people protected, not a percentage. MAP release 202608, 2000–2025. National context is not a trial-site observation or a cause of a trial effect.
- `pf8_sp_country_year.csv`: 332 country/year/drug rows for eight countries. Pf8 has **no amodiaquine classification**, so these classifications cover only the SP half of SMC (SP+AQ). Values describe sampled cases, **not national prevalence and not SMC efficacy**. Burkina Faso has **only 2008**; do not extrapolate to later trial years. Sample sizes are retained. Resistant share uses Resistant + Sensitive as denominator; Undetermined is separate.
- `pf8_aq_markers_country_year.csv`: optional raw-marker carrier summaries for crt K76T and mdr1 N86Y. Mixed calls containing the variant count as carriers; all mixed calls are counted separately. Missing/invalid calls are excluded from the determined denominator. These are marker-carriage shares, not a validated amodiaquine-resistance classification or SMC-effect estimate.

Rebuild after updating the raw download manifest:

```sh
python3 scripts/clean_data.py
python3 scripts/validate_processed.py
python3 scripts/build_context_contracts.py
python3 scripts/build_pf8_aq_marker_context.py
python3 scripts/check_context_fulltexts.py
python3 scripts/validate_context_contracts.py
```

Full-text checks and context discrepancies are recorded in `../verified/fulltext_checks.csv`, `reports/fulltext_check_audit.json` and the AI-2 Requests in `COORDINATION.md`. The evidence owner's tables and site JSON have not been modified.
