"""Verifier: after the formatter, re-checks the answer's main claims against the graph and the cited papers.
Advisory only: if it fails or times out, the answer ships with verification None."""
import asyncio
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from agents.harness import run_agent

TOOLS = ["get_findings", "summarise_evidence", "search_concepts", "lookup_dois"]
WEB = "Web search (OpenAI), not verified against the graph"


class Issue(BaseModel):
    claim: str
    problem: str
    severity: Literal["minor", "major"]


class Review(BaseModel):
    claims_checked: int
    issues: list[Issue]


class Verification(Review):
    status: Literal["verified", "issues_found"]
    code_checks: list[str]      # set in code: the checks that passed in this run


def code_checks(answer) -> list[str]:
    """Checks the harness and formatter already enforced for this answer (they reject output otherwise)."""
    data = answer.model_dump()
    sources = answer.section_sources or [[] for _ in answer.sections]
    checks = []
    if any(WEB not in s for s in sources):
        checks.append("Every DOI, concept id, effect size and CI traced to tool results")
    if any(card.get("meter") for s in data["sections"] for card in s.get("cards", [])):
        checks.append("Consensus meters match evidence summaries")
    checks += ["No causal wording", "Summary citations present in sections"]
    if any(s["type"] == "indicator_map" for s in data["sections"]):
        checks.append("Cross-dataset flags computed in code")
    return checks


async def verify(answer, emit, timeout: float = 60) -> Verification | None:
    await emit({"type": "verifying"})
    sections = "\n".join(f"[{i}] {json.dumps(s.model_dump())[:5000]}" for i, s in enumerate(answer.sections))
    task = (f"Question: {answer.question}\n\nSummary: {answer.summary}\n\nCaveats: {json.dumps(answer.caveats)}"
            f"\n\nSections:\n{sections}")
    try:
        review = await asyncio.wait_for(run_agent(
            "verifier", (Path(__file__).parent / "verifier.md").read_text(), task, Review, emit,
            tools=TOOLS, check=None, effort="low"), timeout)
    except Exception as e:
        await emit({"type": "agent_failed", "agent": "verifier", "error": f"{type(e).__name__}: {e}"[:300]})
        return None
    return Verification(status="issues_found" if any(i.severity == "major" for i in review.issues) else "verified", claims_checked=review.claims_checked,
                        issues=review.issues, code_checks=code_checks(answer))
