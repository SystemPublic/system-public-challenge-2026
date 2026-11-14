CLAUDE.md

Repo-level agent instructions. Read before writing anything. Lane specs: docs/LEARN.md. Domain facts: docs/SCIENCE.md.

The product

System Public Challenge, Build Challenge 3: when does new evidence change the picture for a malaria drug resistance marker?

A site with a front page and four tabs:

Home — scroll-driven explainer: the problem, the scale, the gap.
Learn — what the marker is, which drug, why it matters, one diagram.
Forecast — map of where the marker has been observed over time.
Alert — save a watch; new qualifying evidence fires an alert with a plain explanation and a link to the real paper.
Data — long-form educational deep dive: history, timeline, glossary.

Three builders: Solayman owns Home, Learn, Data, the shell and deployment. David owns Alert. Benjamin owns Forecast.

Stack

Next.js App Router, Tailwind, deployed to Vercel. No new library or service without saying so in the response. No paid services.

Shared selection state

One React context at the app root. Every tab reads and writes it.

ts
{ markerId: string | null,
  timeRange: [number, number] | null,
  selectedFindingId: string | null }

Exported as useSelection(). Mirrored to URL query params so a link restores state. Moving between tabs must never require re-selecting anything.

Placeholder pages for /forecast and /alert stay trivially overwritable — David and Benjamin replace them wholesale.

Hard rules
Never fabricate figures. No invented death tolls, prevalence numbers, effect sizes, dates, or percentages. Every number in UI copy is a named constant in lib/stats.ts prefixed PLACEHOLDER_ until a human sources it. List them in a TODO block in the README.
Never fabricate science. If a biological claim is not in docs/SCIENCE.md, do not write it. Ask instead.
"Associated with", never "causes". A marker association does not establish clinical treatment failure.
"Partial resistance" is the correct term for artemisinin, not "resistance".
Name the drug whenever the marker is named. A marker without its drug context is meaningless.
No clinical advice. Never recommend a treatment or present a threshold as a clinical action rule.
No implied endorsement. No WHO integration, endorsement, or operational readiness framing.
Alert explanations are templates, filled from matched fields. No LLM in the matching path.
Every finding keeps its system_id, pubmed_id and doi end to end. A user must always be able to click through to the real paper.
No secrets in the repo. Keys in .env, gitignored.
No localStorage for app data. URL params only.
Where data comes from
System Public Graph — v2.1, July 1 2026 snapshot, CC BY-NC 4.0. API v1.0, https://public-api.system.com/v1/, header x-api-key, 10,000 req/day/key. Default limit is 10 — always set it. The atomic unit is an association: two variables linked by a statistic. The graph has no geography field and no per-finding publication date.
OpenAlex — resolves pubmed_id/doi to publication dates.
Forecast's map data comes from Benjamin's separate source, not the graph. Any location shown on the map is attributed to that source, never to the System graph. Do not build graph queries that assume a location field.
~20% of API associations are known-bad extractions per System's own docs. Findings shown in the demo should be verified against the Dataverse CSV or spot-checked against the source paper. Note what was done in the README.
Honesty about what this is

The graph is a frozen snapshot, so the alert demo replays real publication history: findings are played forward in the order they were actually published, and the matcher reacts as if they were new.

Say this plainly in UI copy, README and deck. The logic is tested on real history; the feed is a snapshot. Never imply live surveillance.

Accessibility
Colour is never the only encoding. Pair with position, shape, or label.
Respect prefers-reduced-motion: every animation has a legible static state.
Diagram labels are real <text>, not paths.
Keyboard-operable controls, readable legends.
Working style
Commit after every step and push. Small commits.
Deploy on the first commit so the URL exists from the start.
Build against placeholder data rather than blocking on a teammate.
Prefer cutting scope to shipping something that overclaims.
Deadline
Submission closes 3:00 PM ET, Saturday November 14. Stop pushing then.
Submission is a pull request into System's hackathon repo, under projects/<team-name>/.
README must list every data source and disclose AI coding tool use. Required by the rules.
Work deriving from the graph inherits CC BY-NC.