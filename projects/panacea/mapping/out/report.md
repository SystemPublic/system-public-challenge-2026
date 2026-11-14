# Concept Map Report

SPG matching universe: 473 challenge-domain concepts (+ lexical supplements from the full 45,721-concept set).
NYC concept rows: 545.

## Coverage

| collection | NYC rows | with >=1 SPG match | coverage |
|---|---|---|---|
| environment-health | 378 | 352 | 93% |
| heat-complaints | 4 | 4 | 100% |
| leading-causes-of-death | 31 | 30 | 97% |
| street-trees | 132 | 0 | 0% |
| **total** | 545 | 386 | 71% |

Match rows: 668 (many-to-many).

By match type:

- broader-narrower: 412
- related-component: 166
- equivalent: 90

By method:

- llm: 662
- anchor: 6

Review queue: 164 rows (low confidence, or medium related-component) -> review_queue.csv

Unmatched NYC rows: 159 -> unmatched_nyc.csv (seed for the research-needed map)

Every row cites: SPG v1 concepts sha256:1d594e97760d; NYC environment-health v1.0.0; leading-causes-of-death v1.0.0; heat-complaints v1.0.0; street-trees v1.0.0
