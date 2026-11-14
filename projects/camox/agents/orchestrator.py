"""Planner -> specialists in parallel -> formatter. Specialists are discovered from agents/roles/*.md:
a role file is frontmatter (name, title, description, section, optional tools, web_search) plus its prompt."""
import asyncio
import json
import re
from pathlib import Path

from agents.contracts import SECTION_MODELS, Answer, Overall, Plan, Task
from agents.harness import DOI, ContractError, check_wording, run_agent
from agents.verifier import WEB, verify

HERE = Path(__file__).parent
RULES = (HERE / "rules.md").read_text()
GRAPH = "System Public Graph (System), cleaned Dataverse copy, July 2026, CC BY-NC 4.0"
LIVE = "System Public Graph API (System, live)"
GRAPH_TOOLS = {"search_concepts", "search_variables", "neighbours", "paths", "get_findings", "summarise_evidence",
               "sql", "subgraph", "get_concept"}
SOURCES = {**dict.fromkeys(["search_openalex", "count_openalex", "lookup_dois"], "OpenAlex API (OurResearch)"),
           "search_pubmed": "PubMed E-utilities (NCBI, US NLM)",
           **dict.fromkeys(["search_worldbank_indicators", "get_worldbank_data"], "World Bank Data360 API (World Bank)")}


def _load_role(path: Path) -> dict:
    _, front, body = path.read_text().split("---", 2)
    meta = {k.strip(): v.strip() for k, v in (line.split(":", 1) for line in front.strip().splitlines())}
    meta["tools"] = [t.strip() for t in meta["tools"].split(",")] if meta.get("tools") else None
    meta["web_search"] = meta.get("web_search") == "yes"
    meta["prompt"] = body.strip()
    return meta


def roles() -> dict[str, dict]:
    return {r["name"]: r for r in map(_load_role, sorted((HERE / "roles").glob("*.md")))}


def list_agents() -> list[dict]:
    return [{k: r[k] for k in ("name", "title", "description", "section")} for r in roles().values()]


def _context(profile: dict, history: list[dict]) -> str:
    """What every agent knows before it starts: who asks, the project's goals, and the last turns."""
    who = f"User: {profile.get('name')}, {profile.get('role')} at {profile.get('organisation')}. {profile.get('about') or ''}"
    project = profile.get("project") or {}
    goals = f"\nProject: {project.get('title')}. Goals and context: {project['goals']}" if project.get("goals") else ""
    past = "\n".join(f"- Q: {h['query']}\n  A: {h['summary']}" for h in history[-5:])
    return who + goals + (f"\nEarlier in this project:\n{past}" if past else "")


def _context_event(profile: dict, history: list[dict]) -> dict:
    project = profile.get("project") or {}
    return {"type": "context", "profile": f"{profile.get('role')}, {profile.get('organisation')}",
            "project_goals": bool(project.get("goals")), "earlier_turns": min(len(history), 5)}


def check_citations(out: Overall, sections_text: str) -> None:
    """The summary may only cite DOIs that the sections carry, must cite one when they have any, and names no
    indicator ids (those stay in the sections)."""
    check_wording(out)
    cited = {d.rstrip(".") for d in DOI.findall(out.summary)}
    available = {d.lower() for d in DOI.findall(sections_text)}
    unknown = [d for d in cited if d.lower().rstrip(".") not in available]
    codes = [i for i in re.findall(r'"indicator_id": "([^"]+)"', sections_text) if i in out.summary]
    if codes:
        raise ContractError(f"Name indicators in words; the ids {codes[:3]} belong in the sections, not the summary.")
    if unknown or (available and not cited):
        raise ContractError(f"Citations: cite DOIs from the sections in [brackets]; not in the sections: {unknown[:5]}"
                            if unknown else "Cite the DOIs behind your main claims in [brackets], e.g. [10.1186/xyz].")


async def make_plan(query: str, profile: dict, history: list[dict], agents: list[str] | None, emit=None) -> Plan:
    """The planner's proposal. The UI can show and edit it, then pass it back to run()."""
    available = roles()
    allowed = [a for a in (agents or available) if a in available] or list(available)
    catalogue = "\n".join(f"- {n}: {available[n]['description']}" for n in allowed)
    plan = await run_agent(
        "planner", f"{(HERE / 'planner.md').read_text()}\n\nAgents you may use:\n{catalogue}",
        f"{_context(profile, history)}\n\nQuery: {query}", Plan, emit or _quiet, tools=["search_concepts"], check=None,
        effort="low")
    plan.tasks = [t for t in plan.tasks if t.agent in allowed] or [Task(agent=allowed[0], instruction=query)]
    return plan


async def _quiet(event: dict) -> None:
    pass


async def run(query: str, profile: dict, history: list[dict], agents: list[str] | None, emit,
              plan: dict | None = None) -> Answer:
    available = roles()
    ctx = _context(profile, history)
    await emit(_context_event(profile, history))
    if plan:
        plan = Plan.model_validate(plan)
        plan.tasks = [t for t in plan.tasks if t.agent in available]
    if not plan or not plan.tasks:
        plan = await make_plan(query, profile, history, agents, emit)
    await emit({"type": "plan", "plan": plan.model_dump()})

    async def specialist(task):
        role = available[task.agent]
        await emit({"type": "agent_started", "agent": task.agent, "instruction": task.instruction})
        used = []

        async def track(event):  # record the tools this agent really called, for its data-source labels
            if event.get("type") == "tool_call":
                used.append(LIVE if event.get("live") else event["tool"])
            await emit(event)
        try:
            section = await run_agent(
                task.agent, f"{role['prompt']}\n\n{RULES}",
                f"{ctx}\n\nOverall question: {plan.question}\nYour task: {task.instruction}",
                SECTION_MODELS[role["section"]], track, tools=role["tools"], web_search=role["web_search"],
                **({"check": None} if role["web_search"] else {}))  # web results aren't in our trace
            await emit({"type": "agent_done", "agent": task.agent, "section_type": role["section"]})
            graph = [LIVE] if LIVE in used else [GRAPH] if GRAPH_TOOLS & set(used) else []
            labels = graph + [SOURCES[t] for t in used if t in SOURCES] + ([WEB] if role["web_search"] else [])
            return section, list(dict.fromkeys(labels))
        except Exception as e:
            await emit({"type": "agent_failed", "agent": task.agent, "error": str(e)[:300]})
            return None

    done = [r for r in await asyncio.gather(*map(specialist, plan.tasks)) if r]
    sections = [s for s, _ in done]
    if not sections:
        raise RuntimeError("Every agent failed; see the run's events for the errors.")

    await emit({"type": "formatting"})
    listing = "\n".join(f"[{i}] {json.dumps(s.model_dump())[:6000]}" for i, s in enumerate(sections))
    overall = await run_agent("formatter", (HERE / "formatter.md").read_text(),
                              f"Question: {plan.question}\n\nSections:\n{listing}", Overall, emit, tools=[], check=lambda out, *_: check_citations(out, listing),
                              effort="low")
    order = [i for i in dict.fromkeys(overall.section_order) if 0 <= i < len(sections)]
    order += [i for i in range(len(sections)) if i not in order]
    answer = Answer(question=plan.question, summary=overall.summary, caveats=overall.caveats, follow_ups=overall.follow_ups,
                    sections=[sections[i] for i in order], section_sources=[done[i][1] for i in order])
    answer.verification = await verify(answer, emit)
    await emit({"type": "answer", "answer": answer.model_dump()})
    return answer
