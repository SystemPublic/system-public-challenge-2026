---
name: agent-workflow
description: Use when designing or changing the multi-agent workflow in agents/: adding or editing a role, changing the planner or formatter, moving a rule from prompt to code, setting step and retry budgets, or checking a change against the standing test questions.
---

# Agent workflow: planner, specialists, formatter

The flow is fixed: **planner → specialists in parallel → formatter**. Every hand-off is a Pydantic model in `agents/contracts.py`. Every tool comes from our MCP server. Change prompts and roles freely; change the flow or the contracts only after asking the lead.

## Where things live

| Change | File |
|---|---|
| Rules every agent keeps (verdicts, no causation, provenance) | `agents/rules.md`, the single source |
| How the plan is made | `agents/planner.md` |
| How the answer is arranged | `agents/formatter.md` |
| A specialist | `agents/roles/<name>.md` |
| Loop, retries, provenance check | `agents/harness.py` (`run_agent`, `check_provenance`) |
| Output shapes | `agents/contracts.py` (ask the lead) |

## Adding a specialist

A specialist is one file in `agents/roles/`. The orchestrator discovers it and the planner can pick it with no other change.

```markdown
---
name: skeptic                      # id the planner uses
title: Skeptic                     # shown in the UI
description: One line. The planner chooses agents from this line alone, so say when to use it.
section: evidence                  # an existing section type: evidence, eda, policy, research
tools: search_concepts, get_findings   # optional; omit for all tools
web_search: yes                    # optional
---
Prompt body.
```

- **Reuse a section type.** A new type means a new contract and a new renderer in `web/sections.js`, so ask first.
- **Prompt body:**
  - one job, in one sentence
  - numbered steps that name the tools to call
  - which contract field each result fills
  - when to stop
  - don't repeat `rules.md`; the harness adds it
- **The description is routing.** If the planner picks the wrong agents, fix the descriptions before you touch `planner.md`.

## Prompt or code?

If a rule can be checked in code, check it in code and keep the prompt sentence short. The model will break prose rules under pressure; the code check makes it retry.

Already in code (`check_provenance`):
- DOIs, ids and numbers must appear in this run's tool results
- the minimum searches before "no evidence"

Good next candidates, each a few lines in the check:
- the `Meter` fields equal the last `summarise_evidence` result for that card
- a "supported" verdict has `meter.studies >= 3`
- no causal verbs ("causes", "leads to", "drives", "results in") in any string field

Keep in prompts only what needs judgement:
- splitting claims
- reading variable wording for direction
- spotting population mismatch
- naming gaps

## Budgets

- **Rounds and retries:** `MAX_TOOL_ROUNDS`, `MAX_RETRIES` and `MAX_TOOL_CHARS` in `harness.py` cap each agent. Raise one only with a run that shows why.
- **Row caps:** tools cap rows themselves. An agent that needs more should narrow its filters, not get a bigger cap.
- **Parallel tool calls:** the model's calls within one round already run with `asyncio.gather`. Prompts should say "search these synonyms together" so they arrive in one round.
- **Demo target:** a 3-agent run finishes in under 90 s. Record time, tool calls and retries for every test run. Investigate any jump.

## Failure modes and the first fix to try

| Symptom | First fix |
|---|---|
| Planner picks every agent | Tighten the role descriptions. Add "usually 2 to 4" examples to `planner.md` |
| An agent repeats the same search | Add "if a search returns nothing, try a shorter term or `search_variables`, never the same text" to the role |
| "No evidence" too early | The code check already counts searches; make sure the role's steps list `neighbours` |
| Retry storms (2+ retries per agent) | Read the `retry` errors. Usually a field the prompt never mentions; name it in the role's steps |
| Wrong effect direction | Make the role quote both variable names in `basis` before stating a direction |
| Formatter restates the cards | `formatter.md`: the overall answer is at most 3 sentences, leads with the weakest or most surprising verdict, adds no new numbers |

## Test loop: run it after every workflow change

Standing questions:
1. "Validate: girls under 12 are more vulnerable to malaria because of sexism in malaria-endemic countries." Expected: sexism sub-claim = no evidence; girls-more-affected = mixed or thin.
2. The three B2 demo queries and what each must show: `.claude/build/b2-demo.md`, section "Demo path".
3. One question from a different challenge, to prove the layer stays general.

For each run, write to `.claude/scratch/runs.md` (gitignored): the date, the question, which agents ran, verdicts, time, tool calls, retries, and anything that broke. A change is done when the expected verdicts still hold and time and retries didn't grow without a reason.

## Don't build today

Agent-to-agent chat, a framework (LangGraph, CrewAI), long-term memory, vector search, self-improving prompts. The flow above plus code checks is the product.
