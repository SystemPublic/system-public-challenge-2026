"""Project dashboard: a planner reads the project's goals and stored answers and plans 3-6 panels, then one
builder per panel fetches real data in parallel. A panel whose numbers are not in its tool results or the
answers is dropped, never shown."""
import asyncio
import json
import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from agents.contracts import Table
from agents.harness import ContractError, check_wording, run_agent
from agents.orchestrator import RULES, _context

HERE = Path(__file__).parent
PANEL_TOOLS = ["get_worldbank_data", "search_worldbank_indicators", "summarise_evidence", "get_findings", "sql",
               "lookup_dois", "search_concepts"]
NUM = re.compile(r"-?\d[\d,]*(?:\.\d+)?")


class PanelPlan(BaseModel):
    kind: Literal["kpis", "chart", "table"]
    title: str
    purpose: str        # which project goal this panel serves
    data_hint: str      # where the data comes from: indicator ids, countries, years, concept ids, answer sections


class DashboardPlan(BaseModel):
    title: str
    summary: str
    panels: list[PanelPlan]


class Kpi(BaseModel):
    label: str
    value: str
    unit: str
    source: str


class Panel(BaseModel):
    kind: Literal["kpis", "chart", "table"]
    title: str
    caption: str
    kpis: list[Kpi]
    vega_lite_json: str | None
    table: Table | None
    sources: list[str]


class Dashboard(BaseModel):
    title: str
    summary: str
    panels: list[Panel]


def _numbers(text: str) -> list[str]:
    return [n.replace(",", "") for n in NUM.findall(text)]


def _chart_values(spec: str) -> list[str]:
    """Numbers in a chart's inline data rows."""
    try:
        spec = json.loads(spec)
    except ValueError:
        raise ContractError("vega_lite_json is not valid JSON")
    rows = (spec.get("data") or {}).get("values") or [r for v in (spec.get("datasets") or {}).values() for r in v]
    if not rows:
        raise ContractError("the chart has no inline data.values rows")
    return [str(v) for r in rows if isinstance(r, dict) for v in r.values() if isinstance(v, (int, float))]


def check_panel(panel: Panel, source: str) -> None:
    """Every number in the KPIs, chart data and table must appear (allowing rounding) in the source text.
    Small integers pass: they are counts of items the model can see."""
    check_wording(panel)
    known = {float(n) for n in _numbers(source)}
    found = [n for k in panel.kpis for n in _numbers(k.value)]
    if panel.vega_lite_json:
        found += _chart_values(panel.vega_lite_json)
    if panel.table:
        found += [n for row in panel.table.rows for cell in row for n in _numbers(cell)]
    missing = []
    for n in dict.fromkeys(found):
        x, d = float(n), len(n.split(".")[1]) if "." in n else 0
        if not (x.is_integer() and 0 <= x <= 10) and x not in known and not any(round(s, d) == x for s in known):
            missing.append(n)
    if missing:
        raise ContractError(f"Numbers not in your tool results or the answers: {missing[:8]}. "
                            "Fetch the data with a tool and copy values exactly, or drop them.")


def _compact(answers: list[dict], limit: int = 6000) -> str:
    """The stored answers as text for the agents, newest last, charts' specs left out."""
    def strip(o):
        if isinstance(o, dict):
            return {k: strip(v) for k, v in o.items() if k != "vega_lite_json"}
        return [strip(v) for v in o] if isinstance(o, list) else o
    return "\n\n".join(f"Answer {i + 1}: {json.dumps(strip(a))[:limit]}" for i, a in enumerate(answers[-6:]))


async def build_dashboard(project: dict, profile: dict, answers: list[dict], emit) -> Dashboard:
    ctx = _context(profile, [])
    known = _compact(answers)
    await emit({"type": "agent_started", "agent": "dashboard_planner"})
    plan = await run_agent("dashboard_planner", (HERE / "dashboard_planner.md").read_text(),
                           f"{ctx}\n\nStored answers in this project:\n{known}", DashboardPlan, emit,
                           tools=[], check=check_wording)
    await emit({"type": "agent_done", "agent": "dashboard_planner", "panels": len(plan.panels)})

    async def build(p: PanelPlan):
        name = f"panel: {p.title}"
        await emit({"type": "agent_started", "agent": name})
        try:
            panel = await asyncio.wait_for(run_agent(
                name, f"{(HERE / 'panel_builder.md').read_text()}\n\n{RULES}",
                f"{ctx}\n\nPanel to build: {p.model_dump_json()}\n\nStored answers in this project:\n{known}",
                Panel, emit, tools=PANEL_TOOLS,
                check=lambda out, trace, _: check_panel(out, trace + "\n" + known.lower())), 300)
            await emit({"type": "agent_done", "agent": name})
            return panel
        except Exception as e:
            await emit({"type": "agent_failed", "agent": name, "error": str(e)[:300]})
            return None

    panels = [x for x in await asyncio.gather(*map(build, plan.panels[:6])) if x]
    if not panels:
        raise RuntimeError("Every panel failed its data check.")
    return Dashboard(title=plan.title, summary=plan.summary, panels=panels)
