"""Evidence agent: OpenAI tool-use loop over the graph tools.  Usage: python agent/agent.py "question" """
import inspect
import json
import os
import sys
import typing
from pathlib import Path

from openai import OpenAI

import tools

for line in (Path(__file__).resolve().parents[1] / ".env").read_text().splitlines():
    if "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"'))

MODEL = os.environ.get("OPENAI_MODEL", "gpt-6-luna")
SYSTEM = (Path(__file__).parent / "system_prompt.md").read_text()
JSON_TYPES = {str: "string", int: "integer", float: "number", bool: "boolean"}


def schema(fn):
    """OpenAI function schema from a tool's signature and docstring."""
    props, required = {}, []
    hints = typing.get_type_hints(fn)
    for name, p in inspect.signature(fn).parameters.items():
        t, args = hints[name], typing.get_args(hints[name])
        if type(None) in args:  # Optional[X] -> X
            t = next(a for a in args if a is not type(None))
        props[name] = {"type": "array", "items": {"type": "string"}} if typing.get_origin(t) is list else {"type": JSON_TYPES[t]}
        if p.default is p.empty:
            required.append(name)
    return {"type": "function", "name": fn.__name__, "description": inspect.getdoc(fn),
            "parameters": {"type": "object", "properties": props, "required": required}}


SCHEMAS = [schema(f) for f in tools.TOOLS]
FNS = {f.__name__: f for f in tools.TOOLS}


def run(question, on_step=lambda name, args, out: None, max_turns=40):
    """Run the agent on one question; on_step(name, args, result) is called after every tool call."""
    client, items = OpenAI(), [{"role": "user", "content": question}]
    for _ in range(max_turns):
        r = client.responses.create(model=MODEL, instructions=SYSTEM, input=items, tools=SCHEMAS)
        items += r.output
        calls = [o for o in r.output if o.type == "function_call"]
        if not calls:
            return r.output_text
        for c in calls:
            try:
                out = FNS[c.name](**json.loads(c.arguments))
            except Exception as e:
                out = {"error": f"{type(e).__name__}: {e}"}
            on_step(c.name, c.arguments, out)
            items.append({"type": "function_call_output", "call_id": c.call_id, "output": json.dumps(out, default=str)})
    return "Stopped: step limit reached before a final answer."


if __name__ == "__main__":
    print(run(" ".join(sys.argv[1:]), on_step=lambda n, a, o: print(f"> {n}({a})", file=sys.stderr)))
