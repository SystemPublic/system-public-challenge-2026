"""Shared harness for every agent: an OpenAI Responses tool loop over the product MCP server, strict
Pydantic output, a contract check with retry, and server-side context truncation."""
import asyncio
import json
import os
import re
import time

from mcp import Client
from openai import AsyncOpenAI
from openai.lib._pydantic import to_strict_json_schema
from pydantic import BaseModel, ValidationError

import mcp_server  # imports tools, which loads .env

MODEL = os.environ.get("OPENAI_MODEL", "gpt-6-luna")
MAX_TOOL_ROUNDS = 20
MAX_RETRIES = 2
MAX_TOOL_CHARS = 12_000
DOI = re.compile(r"10\.\d{4,9}/[^\s\"'<>,;\]]+", re.I)
_openai = AsyncOpenAI()


class ContractError(Exception):
    pass


SEARCH_TOOLS = {"search_concepts", "search_variables", "neighbours", "paths"}
METER_KEYS = {"up": "above_null", "down": "below_null", "significant_up": "ci_excludes_null_above",
              "significant_down": "ci_excludes_null_below", "studies": "n_studies"}


def _num_in(v: float, trace: str) -> bool:
    return any(s in trace for s in {repr(v), f"{v:g}", str(int(v)) if float(v).is_integer() else repr(v)})


def check_provenance(out: BaseModel, trace: str, calls: list[str]) -> None:
    """Code-side verification: every DOI, concept id, effect size, CI and meter count in the output must
    appear in this run's tool results, and "no evidence" needs at least 3 searches first."""
    data = out.model_dump()
    problems = [f"DOI {d}" for d in set(DOI.findall(json.dumps(data))) if d.lower().rstrip(".") not in trace]
    problems += [f"concept id {i}" for v in _walk(data, "concept_ids") for i in v if i.lower() not in trace]
    for f in _walk(data, "findings"):
        for row in f if isinstance(f, list) else []:
            problems += [f"{k} {row[k]}" for k in ("value", "ci_lower", "ci_upper")
                         if row.get(k) is not None and not _num_in(row[k], trace)]
    problems += [f"indicator id {i}" for i in _walk(data, "indicator_id") if i.lower() not in trace]
    problems += [f"studies={n} for {l['concept_label']}" for links in _walk(data, "links") for l in links
                 if "studies" in l and f'"n_studies": {l["studies"]}' not in trace]
    for m in _walk(data, "meter"):
        if m:
            problems += [f"meter {k}={m[k]}" for k, key in METER_KEYS.items() if f'"{key}": {m[k]}' not in trace]
    if any(c.get("verdict") == "no evidence" for c in _walk_cards(data)) and sum(c in SEARCH_TOOLS for c in calls) < 3:
        problems.append('a "no evidence" verdict after fewer than 3 searches; search synonyms and neighbours first')
    problems += [f'"supported" with only {c["meter"]["studies"]} studies (needs 3+)' for c in _walk_cards(data)
                 if c.get("verdict") == "supported" and c.get("meter") and c["meter"]["studies"] < 3]
    check_wording(out)
    if problems:
        raise ContractError("Not backed by this run's tool results: " + "; ".join(problems[:8]) +
                            ". Copy values exactly from tool results, search more, or drop the item.")


CAUSAL = re.compile(r"\b(causes|caused|causing|leads? to|led to|drives|results? in)\b", re.I)


def check_wording(out: BaseModel, *_) -> None:
    """The graph holds associations, so the answer may not use causal verbs."""
    hits = sorted({m.group(0).lower() for m in CAUSAL.finditer(json.dumps(out.model_dump()))})
    if hits:
        raise ContractError(f"Causal wording {hits}: the graph shows associations. Rephrase with 'associated with'.")


def _walk_cards(data):
    for cards in _walk(data, "cards"):
        yield from cards


def _walk(obj, key):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from ([v] if k == key else _walk(v, key))
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk(v, key)


def _result_text(res) -> str:
    """One JSON string per tool result: structured output if present, else the text parts
    (a list result arrives as one part per item, so several parts become a JSON list)."""
    if res.structured_content:
        return json.dumps(res.structured_content, default=str)
    parts = [getattr(p, "text", "") for p in res.content]
    if len(parts) == 1:
        return parts[0]
    try:
        return json.dumps([json.loads(p) for p in parts])
    except ValueError:
        return "\n".join(parts)


def summarise_result(tool: str, args: dict, text: str) -> str:
    """One human line for the live view, e.g. 'search_concepts "internet use" -> 10 concepts, top: Internet use
    (382 studies)'."""
    query = next((args[k] for k in ("text", "query") if isinstance(args.get(k), str)), None)
    head = f'{tool} "{query[:50]}"' if query and tool != "sql" else tool
    try:
        data = json.loads(text)
    except ValueError:
        return f"{head} -> {text[:80]}"
    if isinstance(data, dict) and set(data) == {"result"}:
        data = data["result"]
    try:
        return f"{head} -> {_describe(tool, data)}"
    except (KeyError, TypeError, AttributeError, ValueError):  # an unexpected shape never breaks a run
        return f"{head} -> {text[:80]}"


def _describe(tool: str, data) -> str:
    if isinstance(data, dict) and "error" in data:
        return f"error: {str(data['error'])[:80]}"
    if tool == "summarise_evidence":
        fams = data["by_family"].values()
        up, down = (sum(f[k] for f in fams) for k in ("ci_excludes_null_above", "ci_excludes_null_below"))
        return f"{data['n_findings']} findings from {data['n_studies']} studies, {up} up and {down} down (CI excludes null)"
    if tool == "get_findings":
        return f"{data['total']} findings" + (f", {data['shown']} shown" if data["shown"] < data["total"] else "")
    if tool == "get_concept":
        return f"{data.get('wikidata_label')} ({data.get('wikidata_id')}, {data.get('source')})"
    if tool == "get_worldbank_data":
        years = [r["year"] for r in data["rows"]]
        span = f", {min(years)}-{max(years)}" if years else ""
        return f"{data['total']} values ({data['source']}{span})"
    noun, label = LIST_SUMMARIES.get(tool, ("rows", lambda r: ""))
    if isinstance(data, dict) and tool in LIST_SUMMARIES:
        data = [data]  # a one-item list arrives as a single object
    if not isinstance(data, list):
        return ", ".join(f"{k}: {str(v)[:30]}" for k, v in list(data.items())[:3]) if isinstance(data, dict) else str(data)[:80]
    if not data:
        return "nothing found"
    if tool == "search_worldbank_indicators":
        return f"{len(data)} indicators ({', '.join(dict.fromkeys(i['database'].removeprefix('WB_') for i in data[:5]))})"
    return f"{len(data)} {noun}" + (f", top: {label(data[0])}" if label(data[0]) else "")


LIST_SUMMARIES = {  # tool -> (what the rows are, how to name the top row)
    "search_concepts": ("concepts", lambda r: f"{r['label']} ({r['n_studies']} studies)"),
    "neighbours": ("linked concepts", lambda r: f"{r['label']} ({r['n_studies']} studies)"),
    "search_variables": ("concepts by wording", lambda r: f"{r['concept_label']} ({r['n_variables']} variables)"),
    "paths": ("paths", lambda r: " -> ".join(r["path"])),
    "search_worldbank_indicators": ("indicators", None),
    "search_openalex": ("papers", lambda r: f"{r['title'][:60]} ({r['year']})"),
    "search_pubmed": ("papers", lambda r: f"{r['title'][:60]} ({r['year']})"),
    "lookup_dois": ("papers", lambda r: f"{r['title'][:60]} ({r['year']})"),
}


async def run_agent(name: str, instructions: str, task: str, output: type[BaseModel], emit,
                    tools: list[str] | None = None, web_search: bool = False,
                    check=check_provenance, effort: str | None = None) -> BaseModel:
    """Run one agent to a validated `output`. Tools come only from the MCP server. `effort` sets the
    model's reasoning effort (its default when None)."""
    async with Client(mcp_server.server) as mcp:
        listed = (await mcp.list_tools()).tools
        specs = [{"type": "function", "name": t.name, "description": t.description or "", "parameters": t.input_schema}
                 for t in listed if tools is None or t.name in tools]
        if web_search:
            specs.append({"type": "web_search"})
        fmt = {"format": {"type": "json_schema", "name": output.__name__, "strict": True,
                          "schema": to_strict_json_schema(output)}}
        trace, calls_made, prev, new_input = [], [], None, [{"role": "user", "content": task}]

        async def call(c):
            t0 = time.monotonic()
            try:
                res = await mcp.call_tool(c.name, json.loads(c.arguments or "{}"))
                text = _result_text(res)
            except Exception as e:  # tool errors go back to the model
                text = json.dumps({"error": f"{type(e).__name__}: {e}"})
            trace.append(text.lower())
            calls_made.append(c.name)
            await emit({"type": "tool_call", "agent": name, "tool": c.name, "args": json.loads(c.arguments or "{}"),
                        "summary": summarise_result(c.name, json.loads(c.arguments or "{}"), text), "ms": int((time.monotonic() - t0) * 1000),
                        **({"live": True} if '"source": "live"' in text else {})})
            return {"type": "function_call_output", "call_id": c.call_id, "output": text[:MAX_TOOL_CHARS]}

        for attempt in range(MAX_RETRIES + 1):
            for _ in range(MAX_TOOL_ROUNDS):
                r = await _openai.responses.create(model=MODEL, instructions=instructions, input=new_input,
                                                   previous_response_id=prev, tools=specs or None, text=fmt,
                                                   truncation="auto",
                                                   **({"reasoning": {"effort": effort}} if effort else {}))
                prev = r.id
                calls = [o for o in r.output if o.type == "function_call"]
                if not calls:
                    break
                new_input = await asyncio.gather(*(call(c) for c in calls))
            try:
                result = output.model_validate_json(r.output_text)
                if check:
                    check(result, "\n".join(trace), calls_made)
                return result
            except (ValidationError, ContractError, ValueError) as e:
                err = str(e)[:600]
                await emit({"type": "retry", "agent": name, "error": err[:200]})
                new_input = [{"role": "user", "content": f"Your output failed the contract check: {err}\nFix it and answer again."}]
        raise ContractError(f"{name}: output failed the contract after {MAX_RETRIES} retries")
