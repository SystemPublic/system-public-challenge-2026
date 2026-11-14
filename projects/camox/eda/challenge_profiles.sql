-- Per-challenge coverage + quality from eda/challenge_terms.csv. Run from repo root:
--   duckdb -readonly data/graph.duckdb < eda/challenge_profiles.sql  (replace OUTDIR with an output folder)
CREATE TEMP TABLE terms AS SELECT row_number() OVER () ord, * FROM read_csv('eda/challenge_terms.csv', all_varchar=true, header=true);
CREATE TEMP TABLE t AS SELECT a.system_id, a.study_id, a.system_statistic_type st, a.ci_lower, a.p_value, a.variable_1_concept_id c1, a.variable_2_concept_id c2,
  lower(a.variable_1_name||' | '||a.variable_2_name||' | '||k1.wikidata_label||' | '||k2.wikidata_label) txt
  FROM associations a JOIN concepts k1 ON k1.system_id=a.variable_1_concept_id JOIN concepts k2 ON k2.system_id=a.variable_2_concept_id;
CREATE TEMP TABLE m AS SELECT terms.challenge, terms.subtopic, terms.rx, t.* FROM terms JOIN t ON regexp_matches(t.txt, terms.rx)
  AND (terms.rx2 IS NULL OR regexp_matches(t.txt, terms.rx2)) AND (terms.exclude IS NULL OR NOT regexp_matches(t.txt, terms.exclude));
CREATE TEMP TABLE sp AS SELECT study_id,
  regexp_matches(coalesce(population_string,''), '\b(United States|USA|U\.S\.|American|Canad|Mexic|Brazil|Argentin|Chile|Colombia|Peru|Ecuador|Bolivia|Guatemala|Haiti|Cuba|Jamaica|UK|United Kingdom|England|English|Scotland|Wales|Ireland|Irish|France|French|German|Ital|Spain|Spanish|Portug|Netherlands|Dutch|Belgi|Swed|Norw|Denmark|Danish|Finland|Finnish|Swiss|Switzerland|Austria|Polish|Poland|Greece|Greek|Turk|Russia|Ukrain|Israel|Iran|Iraq|Saudi|Emirat|Qatar|Kuwait|Jordan|Leban|Egypt|Moroc|Tunisia|Algeria|Nigeria|Ghana|Kenya|Ethiopia|Uganda|Tanzania|Malawi|Mali|Burkina|Senegal|Zambia|Zimbabwe|Mozambique|Cameroon|Congo|Rwanda|Sudan|South Africa|Botswana|Gambia|Benin|Niger|Guinea|Sierra Leone|Liberia|Madagascar|Africa|India|Pakistan|Bangladesh|Nepal|Sri Lanka|China|Chinese|Hong Kong|Taiwan|Japan|Korea|Mongolia|Vietnam|Thailand|Thai|Cambodia|Laos|Myanmar|Malaysia|Singapore|Indonesia|Philippin|Australia|New Zealand|Europe|Asia|Latin America|[A-Z][a-z]+ (Province|County|State|City))')::int has_place,
  regexp_matches(coalesce(population_string,''), '\b(Mexic|Brazil|Colombia|Peru|Ecuador|Bolivia|Guatemala|Haiti|Honduras|Nicaragua|Iran|Iraq|Jordan|Leban|Egypt|Moroc|Tunisia|Algeria|Nigeria|Ghana|Kenya|Ethiopia|Uganda|Tanzania|Malawi|Mali\b|Burkina|Senegal|Zambia|Zimbabwe|Mozambique|Cameroon|Congo|Rwanda|Sudan|South Africa|Botswana|Gambia|Benin|Niger|Guinea|Sierra Leone|Liberia|Madagascar|Africa|India|Pakistan|Bangladesh|Nepal|Sri Lanka|China|Chinese|Mongolia|Vietnam|Thailand|Thai|Cambodia|Laos|Myanmar|Indonesia|Philippin|Turk|Ukrain|low.income countr|middle.income countr|LMIC)')::int lmic
  FROM studies WHERE study_id IN (SELECT DISTINCT study_id FROM m);
CREATE TEMP TABLE sub AS SELECT m.challenge, m.subtopic, count(*) findings, count(DISTINCT m.study_id) studies,
  round(100*avg((ci_lower IS NOT NULL)::int),0) pct_with_ci, round(100*avg((st LIKE '%ratio%')::int),0) pct_ratio_type,
  round(100*count(DISTINCT m.study_id) FILTER (WHERE sp.has_place=1)/count(DISTINCT m.study_id),0) pct_studies_place,
  round(100*count(DISTINCT m.study_id) FILTER (WHERE sp.lmic=1)/count(DISTINCT m.study_id),0) pct_studies_lmic
  FROM m JOIN sp USING(study_id) GROUP BY 1,2;
COPY (SELECT t.challenge, t.subtopic, coalesce(findings,0) findings, coalesce(studies,0) studies, pct_with_ci, pct_ratio_type, pct_studies_place, pct_studies_lmic
  FROM terms t LEFT JOIN sub USING(challenge, subtopic) ORDER BY t.ord) TO 'OUTDIR/challenge_subtopics.csv';
COPY (WITH pairs AS (SELECT DISTINCT challenge, c1||'|'||c2 rid FROM m)
  SELECT m.challenge, count(DISTINCT m.system_id) findings, count(DISTINCT m.study_id) studies,
  round(100*avg((ci_lower IS NOT NULL)::int),0) pct_with_ci, round(100*avg((p_value IS NOT NULL)::int),0) pct_with_p,
  round(100*avg((st LIKE '%ratio%')::int),0) pct_ratio_type,
  (SELECT round(100*avg((r.num_studies=1)::int),0) FROM pairs p JOIN relationships r ON r.relationship_id=p.rid WHERE p.challenge=m.challenge) pct_single_study_links,
  (SELECT count(*) FROM pairs p WHERE p.challenge=m.challenge) concept_links,
  round(100*count(DISTINCT m.study_id) FILTER (WHERE sp.has_place=1)/count(DISTINCT m.study_id),0) pct_studies_place,
  round(100*count(DISTINCT m.study_id) FILTER (WHERE sp.lmic=1)/count(DISTINCT m.study_id),0) pct_studies_lmic
  FROM m JOIN sp USING(study_id) GROUP BY 1 ORDER BY 1) TO 'OUTDIR/challenge_quality.csv';
COPY (WITH side AS (SELECT challenge, subtopic, rx, study_id, c1 cid FROM m UNION ALL SELECT challenge, subtopic, rx, study_id, c2 FROM m),
  agg AS (SELECT challenge, subtopic, k.wikidata_label partner, count(DISTINCT study_id) studies FROM side JOIN concepts k ON k.system_id=side.cid
          WHERE NOT regexp_matches(lower(k.wikidata_label), rx) GROUP BY 1,2,3)
  SELECT challenge, subtopic, partner, studies FROM (SELECT *, row_number() OVER (PARTITION BY challenge, subtopic ORDER BY studies DESC, partner) rn FROM agg) WHERE rn<=5 ORDER BY 1,2,4 DESC) TO 'OUTDIR/challenge_partners.csv';
