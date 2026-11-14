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
DOI = re.compile(r"10\.\d{4,9}/[^\s\"'<>,;]+", re.I)
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


def summarise_result(text: str) -> str:
    """One line for the live view."""
    try:
        data = json.loads(text)
    except ValueError:
        return text[:100]
    if isinstance(data, dict) and "result" in data and len(data) == 1:
        data = data["result"]
    if isinstance(data, list):
        first = data[0] if data else {}
        name = next((first.get(k) for k in ("label", "title", "concept_label", "path", "name") if isinstance(first, dict) and first.get(k)), None)
        return f"{len(data)} results" + (f", first: {str(name)[:60]}" if name else "")
    if isinstance(data, dict):
        if "total" in data:
            return f"{data['total']} total, {data.get('shown', '?')} shown"
        if "n_findings" in data:
            return f"{data['n_findings']} findings from {data.get('n_studies')} studies"
        if "error" in data:
            return f"error: {str(data['error'])[:80]}"
        return ", ".join(f"{k}: {str(v)[:30]}" for k, v in list(data.items())[:3])
    return str(data)[:100]


async def run_agent(name: str, instructions: str, task: str, output: type[BaseModel], emit,
                    tools: list[str] | None = None, web_search: bool = False,
                    check=check_provenance) -> BaseModel:
    """Run one agent to a validated `output`. Tools come only from the MCP server."""
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
                        "summary": summarise_result(text), "ms": int((time.monotonic() - t0) * 1000)})
            return {"type": "function_call_output", "call_id": c.call_id, "output": text[:MAX_TOOL_CHARS]}

        for attempt in range(MAX_RETRIES + 1):
            for _ in range(MAX_TOOL_ROUNDS):
                r = await _openai.responses.create(model=MODEL, instructions=instructions, input=new_input,
                                                   previous_response_id=prev, tools=specs or None, text=fmt,
                                                   truncation="auto")
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
