# Edges as objects: the hypergraph page

This note describes `viz/hypergraph.html`, built on 13 November 2026 by `tools/build_hypergraph.py` from the cache of the System Public Graph (a database of findings extracted from published research, called the graph below), the registered claims and `data/derived/`. Figures are in `figures/hypergraph/`.

## What the page shows

A graph of research is usually drawn as variables joined by lines. The page reverses the emphasis. Each link between two variables, called an edge, is drawn as an object with contents: the findings the graph holds for it, the design of each study where one is known, whether this project read the abstract, and the city's registered test where there is one. A registered test is a prediction committed to the repository before its outcome data were read.

The page has four parts. Part A is a field of 69 edges with 1,123 findings from 625 papers, grouped by the variable they share. Part B opens one edge as a forest plot, a table of studies with one row for each finding. Part C shows four relations among edges: a chain of two tested edges whose product predicted a third, two bodies of research that predict opposite signs for the same change, edges that rest on the same paper, and an edge whose size depends on a third variable. Part D is a matrix of 25 interventions by 8 outcome domains, shaded by the number of studies, in which 110 of 200 cells are empty.

## How to read a glyph

Each edge is a horizontal bar between two variable names. The bar is a log-ratio axis from 0.25 to 4, and the centre line is no effect. Each mark is one finding, placed by its stored ratio. Findings on another scale, such as correlations and mean differences, are counted in the box at the left end when negative and at the right end when positive.

The shape of a mark gives the study design: a square for an experiment or trial, a diamond for a quasi-experiment, a triangle for a cohort, case-control or case-crossover study, and a circle for a cross-section. A thin grey tick is a finding whose design the graph does not record and whose abstract this project did not read for design. A filled mark is a finding checked against its abstract and found correct. A hollow mark was not read. A mark with a slash was read and found wrong or missing a qualifier. A dashed mark is a study that the graph does not hold. The coloured capsule is the city's estimate, the line under it is the 95% interval, and the colour is the verdict. A hollow capsule in an end box is a city estimate on another scale, of which only the sign can be compared.

## What is and is not in the graph's records

A finding record gives two variable names, a statistic type, a value, usually an interval or a p value, and a PubMed identifier. A study record gives a population and a DOI. The study record has a `study_type` field, and it was filled for 20 of the 615 studies looked up. The graph therefore gave a design for 25 of the 1,123 findings, and this project's reading gave one for 117 more. Authors and years on the page come from PubMed.

The records do not say which variable is the exposure, whether a variable name is negated, or what contrast a ratio refers to (per degree, per quintile, high against low). For that reason the sign of a mark follows each study's own wording, and the page gives a pooled value for one edge only, temperature and homicide, where the abstracts gave a common contrast. For three edges the relationship record counts findings (2, 6 and 14) and the API returns none. Of the 139 findings on the page that were checked against an abstract, 27 were wrong or had lost a qualifier. The four records for temperature and homicide store percent changes as odds ratios, and the page plots the values from the abstracts.

## Limits

The edges were chosen by hand from those cited in registrations. The edges for commuting, city interventions and medicines were assembled by variable name, because the graph has no concept for them. Positions on the log-ratio axis mix contrasts and should be read for sign and rough size only. Part D marks the cells in which the city registered a test; the repository has no coding of which other cells the city's data could measure.

## Three questions the view raises

1. Does the split of signs within an edge reflect disagreement among studies or the wording of variables? Temperature and mortality has 88 positive and 20 negative findings. Coding the exposure and contrast of each would show how much of the split is cold against heat.
2. How much of the evidence on neighbouring edges is the same evidence? Forty-four papers supply findings to two or more of the 69 edges, and the edges from nitrogen dioxide and from particulates to asthma share several. A count of independent studies for each hub would be smaller than the count of findings.
3. Where the city tested an edge that the graph leaves empty, which design would the literature need in order to check the city? Street trees and housing cost, air conditioning and violence, and congestion charging and health are empty in the graph and have a registered city estimate.
