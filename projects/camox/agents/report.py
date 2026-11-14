"""Project report: a planner outlines it, then one writer turns the project's goals, stored answers and dashboard into a cited report.
The references and the data-provenance appendix are built in code from the stored answers and runs, never by
the model."""
import asyncio
import json
import re
from pathlib import Path

from pydantic import BaseModel

from agents.dashboard import _compact
from agents.harness import DOI, ContractError, check_wording, run_agent
from agents.orchestrator import _context
from agents.verifier import check, major
from tools import literature

HERE = Path(__file__).parent
MARK = re.compile(r"\[(\d+)\]")
GRAPH = {"search_concepts", "search_variables", "neighbours", "paths", "get_findings", "summarise_evidence", "sql",
         "get_concept"}
CHECKS = ["Every DOI traced to the stored answers", "Every [n] marker has a reference", "No causal wording"]
SOURCES = {  # source -> licence
    "System Public Graph (Dataverse release)": "CC BY-NC 4.0",
    "World Bank": "CC BY 4.0",
    "OpenAlex": "CC0",
    "PubMed": "NCBI terms of use",
}


class ReportSection(BaseModel):
    heading: str
    paragraphs: list[str]


class PlannedSection(BaseModel):
    heading: str
    key_points: list[str]   # findings and numbers copied from the answers or dashboard
    sources: list[str]      # DOIs and indicator ids copied from the answers


class ReportPlan(BaseModel):
    decision: str           # the decision this report serves
    sections: list[PlannedSection]
    main_gap: str


class Report(BaseModel):
    title: str
    purpose: str
    executive_summary: str
    sections: list[ReportSection]
    limitations: list[str]
    cited_dois: list[str]       # [n] in the text is cited_dois[n-1]


def _doi(d: str) -> str:
    return d.lower().strip().removeprefix("https://doi.org/").rstrip(".")


def check_report(report: Report, known: str) -> None:
    """Every DOI must come from the stored answers, and every [n] must point into cited_dois."""
    check_wording(report)
    text = json.dumps(report.model_dump(exclude={"cited_dois"}))
    problems = [f"DOI {d} is not in the stored answers" for d in {*report.cited_dois, *DOI.findall(text)}
                if _doi(d) not in known]
    problems += [f"marker [{n}] has no entry in cited_dois" for n in sorted(set(MARK.findall(text)), key=int)
                 if not 1 <= int(n) <= len(report.cited_dois)]
    if problems:
        raise ContractError("; ".join(problems[:8]) + ". Cite only DOIs that appear in the stored answers.")


def provenance(calls: list[dict]) -> list[dict]:
    """One entry per data source from the runs' tool_call events: what was retrieved, when, and its licence."""
    out = {}
    for c in calls:
        tool, args = c.get("tool", ""), c.get("args") or {}
        if tool in GRAPH:
            src = "System Public Graph (Dataverse release)"
            items = [f"concept {i}" for k in ("concept_id", "concept_a", "concept_b", "concepts_a", "concepts_b")
                     for i in ([args[k]] if isinstance(args.get(k), str) else args.get(k) or [])]
            items += [f'search "{args["text"]}"'] if isinstance(args.get("text"), str) else []
        elif "worldbank" in tool:
            src = "World Bank"
            ind = args.get("indicator_id")
            items = [f"indicator {ind} (dataset {'_'.join(ind.split('_')[:2])})"] if ind else []
            items += [f'search "{args["text"]}"'] if args.get("text") else []
        elif tool in ("search_openalex", "count_openalex", "lookup_dois"):
            src = "OpenAlex"
            items = [f'query "{args["query"]}"'] if args.get("query") else [f"DOI lookup ({len(args.get('dois') or [])})"]
        elif tool == "search_pubmed":
            src, items = "PubMed", [f'query "{args.get("query", "")}"']
        else:
            continue
        e = out.setdefault(src, {"source": src, "licence": SOURCES[src], "calls": 0, "items": [], "first": c.get("t"),
                                 "last": c.get("t")})
        e["calls"] += 1
        e["items"] = list(dict.fromkeys(e["items"] + items))
        if c.get("t"):
            e["first"], e["last"] = min(filter(None, [e["first"], c["t"]])), max(filter(None, [e["last"], c["t"]]))
    return list(out.values())


async def build_report(project: dict, profile: dict, answers: list[dict], instruction: str | None,
                       calls: list[dict], emit) -> dict:
    """A new report version: the model's Report plus references and provenance computed here."""
    known = json.dumps(answers).lower()
    task = f"{_context(profile, [])}\n\nStored answers in this project:\n{_compact(answers, 8000)}"
    if project.get("dashboard"):
        d = {**project["dashboard"], "panels": [{**p, "vega_lite_json": None} for p in project["dashboard"]["panels"]]}
        task += f"\n\nProject dashboard:\n{json.dumps(d)[:6000]}"
    if project.get("reports"):
        task += (f"\n\nPrevious report version:\n{json.dumps(project['reports'][-1]['report'])}\n\n"
                 f"Revise it following this instruction: {instruction or 'update it with the latest answers'}")
    elif instruction:
        task += f"\n\nInstruction from the user: {instruction}"
    await emit({"type": "planning", "agent": "report_planner"})
    try:  # the outline helps the writer; without it the report is still written
        plan = await run_agent("report_planner", (HERE / "report_planner.md").read_text(), task, ReportPlan, emit,
                               tools=[], check=None, effort="low")
        task += f"\n\nReport outline to follow:\n{plan.model_dump_json()}"
    except Exception as e:
        await emit({"type": "agent_failed", "agent": "report_planner", "error": f"{type(e).__name__}: {e}"[:300]})

    async def write(extra=""):
        await emit({"type": "agent_started", "agent": "report_writer"})
        report = await run_agent("report_writer", (HERE / "report_writer.md").read_text(), task + extra, Report, emit,
                                 tools=[], check=lambda out, *_: check_report(out, known))
        review = (f"A project report, checked against the stored answers it was written from. Its executive summary "
                  f"is the summary; [n] cites cited_dois[n-1].\n\nStored answers:\n{_compact(answers, 8000)}\n\n"
                  f"Report:\n{json.dumps(report.model_dump())}")
        return report, await check(review, CHECKS, emit, 90)
    report, verification = await write()
    if issues := major(verification):  # one revision pass, then the report ships with whatever remains
        try:
            report, verification = await write(f"\n\nYour draft:\n{json.dumps(report.model_dump())}\n\nA verifier found "
                                               f"these major problems in it. Fix them and keep the rest:\n{issues}")
        except Exception as e:
            await emit({"type": "agent_failed", "agent": "report_writer", "error": f"Revision: {type(e).__name__}: {e}"[:300]})
    dois = [_doi(d) for d in report.cited_dois]
    try:
        found = {_doi(w["doi"]): w for w in await asyncio.to_thread(literature.lookup_dois, dois)}
    except Exception:
        found = {}
    refs = [{"n": i + 1, "doi": d, "url": f"https://doi.org/{d}", **{k: found.get(d, {}).get(k) for k in ("title", "year", "venue")}}
            for i, d in enumerate(dois)]
    return {"instruction": instruction, "report": report.model_dump(), "references": refs,
            "provenance": provenance(calls),
            "verification": verification.model_dump() if verification else {"status": "not_verified"}}
