#!/bin/sh
# Alerts tab — smoke test. Run: sh smoke-test.sh  (needs $SYSTEM_API_KEY and optionally $RESEND_API_KEY)
set -eu
K="${SYSTEM_API_KEY:-}"
if [ -z "$K" ]; then echo "SYSTEM_API_KEY not set; skipping API smoke test (UI should still load)"; exit 0; fi
H="x-api-key: $K"
B="https://public-api.system.com"
echo "== 1. sanity"
curl -sS "$B/v1/relationships?limit=1&include_total=true" -H "$H" | head -c 400; echo
echo "== 2. has the graph read this paper"
curl -sS "$B/v1/studies?filter=pubmed_id:33684211&include_total=true" -H "$H" | head -c 400; echo
echo "== 3. what the graph extracted from a K540E paper"
curl -sS "$B/v1/studies/Cxsr7UsKD_/associations?limit=50&include_total=true" -H "$H" | head -c 600; echo
echo "== 4. confirm a finding by ID"
curl -sS "$B/v1/associations/489sn1mPQa" -H "$H" | head -c 400; echo
echo "== 5. probe for a K540E variable (today it returns none)"
curl -sS "$B/v1/variables?search=name:K540E&include_total=true" -H "$H" | head -c 300; echo
echo "== 6. sulfadoxine concept relationships"
curl -sS "$B/v1/concepts/bzQO0hAZXK/relationships?sort=num_findings:desc&include_total=true&limit=10" -H "$H" | head -c 600; echo
echo "OK"
