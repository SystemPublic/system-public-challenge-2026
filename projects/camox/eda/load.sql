-- Build data/graph.duckdb from the Dataverse CSVs. Run from repo root: duckdb data/graph.duckdb < eda/load.sql
CREATE OR REPLACE TABLE associations  AS SELECT * FROM read_csv('data/associations.csv',  sample_size=-1);
CREATE OR REPLACE TABLE relationships AS SELECT * FROM read_csv('data/relationships.csv', sample_size=-1);
CREATE OR REPLACE TABLE studies       AS SELECT * FROM read_csv('data/studies.csv',       sample_size=-1);
CREATE OR REPLACE TABLE variables     AS SELECT * FROM read_csv('data/variables.csv',     sample_size=-1);
CREATE OR REPLACE TABLE concepts      AS SELECT * FROM read_csv('data/concepts.csv',      sample_size=-1);
