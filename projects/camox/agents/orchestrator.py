"""Planner -> specialists in parallel -> formatter. Specialists are discovered from agents/roles/*.md:
a role file is frontmatter (name, title, description, section, optional tools, web_search) plus its prompt."""
import asyncio
import json
from pathlib import Path

from agents.contracts import SECTION_MODELS, Answer, Overall, Plan, Task
from agents.harness import check_wording, run_agent

HERE = Path(__file__).parent
RULES = (HERE / "rules.md").read_text()


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
    who = f"User: {profile.get('name')}, {profile.get('role')} at {profile.get('organisation')}. {profile.get('about') or ''}"
    past = "\n".join(f"- Q: {h['query']}\n  A: {h['summary']}" for h in history[-5:])
    return who + (f"\nEarlier in this project:\n{past}" if past else "")


async def make_plan(query: str, profile: dict, history: list[dict], agents: list[str] | None, emit=None) -> Plan:
    """The planner's proposal. The UI can show and edit it, then pass it back to run()."""
    available = roles()
    allowed = [a for a in (agents or available) if a in available] or list(available)
    catalogue = "\n".join(f"- {n}: {available[n]['description']}" for n in allowed)
    plan = await run_agent(
        "planner", f"{(HERE / 'planner.md').read_text()}\n\nAgents you may use:\n{catalogue}",
        f"{_context(profile, history)}\n\nQuery: {query}", Plan, emit or _quiet, tools=["search_concepts"], check=None)
    plan.tasks = [t for t in plan.tasks if t.agent in allowed] or [Task(agent=allowed[0], instruction=query)]
    return plan


async def _quiet(event: dict) -> None:
    pass


async def run(query: str, profile: dict, history: list[dict], agents: list[str] | None, emit,
              plan: dict | None = None) -> Answer:
    available = roles()
    ctx = _context(profile, history)
    if plan:
        plan = Plan.model_validate(plan)
        plan.tasks = [t for t in plan.tasks if t.agent in available]
    if not plan or not plan.tasks:
        plan = await make_plan(query, profile, history, agents, emit)
    await emit({"type": "plan", "plan": plan.model_dump()})

    async def specialist(task):
        role = available[task.agent]
        await emit({"type": "agent_started", "agent": task.agent, "instruction": task.instruction})
        try:
            section = await run_agent(
                task.agent, f"{role['prompt']}\n\n{RULES}",
                f"{ctx}\n\nOverall question: {plan.question}\nYour task: {task.instruction}",
                SECTION_MODELS[role["section"]], emit, tools=role["tools"], web_search=role["web_search"],
                **({"check": None} if role["web_search"] else {}))  # web results aren't in our trace
            await emit({"type": "agent_done", "agent": task.agent, "section_type": role["section"]})
            return section
        except Exception as e:
            await emit({"type": "agent_failed", "agent": task.agent, "error": str(e)[:300]})
            return None

    sections = [s for s in await asyncio.gather(*map(specialist, plan.tasks)) if s]
    if not sections:
        raise RuntimeError("Every agent failed; see the run's events for the errors.")

    await emit({"type": "formatting"})
    listing = "\n".join(f"[{i}] {json.dumps(s.model_dump())[:6000]}" for i, s in enumerate(sections))
    overall = await run_agent("formatter", (HERE / "formatter.md").read_text(),
                              f"Question: {plan.question}\n\nSections:\n{listing}", Overall, emit, tools=[], check=check_wording)
    order = [i for i in dict.fromkeys(overall.section_order) if 0 <= i < len(sections)]
    order += [i for i in range(len(sections)) if i not in order]
    answer = Answer(question=plan.question, summary=overall.summary, caveats=overall.caveats,
                    sections=[sections[i] for i in order])
    await emit({"type": "answer", "answer": answer.model_dump()})
    return answer
