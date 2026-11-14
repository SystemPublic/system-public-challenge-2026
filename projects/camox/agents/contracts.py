"""Pydantic contracts for every hand-off in the agent loop. Every field is required (OpenAI strict output);
use None or [] for "nothing". Free-form JSON (Vega-Lite specs) travels as a string."""
from typing import Literal

from pydantic import BaseModel

Verdict = Literal["supported", "contested", "mixed", "thin", "no evidence"]


# Planner -----------------------------------------------------------------------------------------
class Task(BaseModel):
    agent: str          # name of an agent role from agents/roles/
    instruction: str    # what this agent should find out, in one or two sentences


class Plan(BaseModel):
    question: str       # the user's query restated as a clear question
    tasks: list[Task]


# Specialist sections (one type per agent role) ---------------------------------------------------
class Finding(BaseModel):
    variable_1: str
    variable_2: str
    stat_type: str
    value: float | None
    ci_lower: float | None
    ci_upper: float | None
    population: str | None
    doi: str | None


class Meter(BaseModel):
    """Consensus meter, copied from summarise_evidence for the main effect family."""
    family: str                 # ratio, difference or correlation
    findings: int
    studies: int
    up: int                     # above_null
    down: int                   # below_null
    significant_up: int         # ci_excludes_null_above
    significant_down: int       # ci_excludes_null_below


class EvidenceCard(BaseModel):
    claim: str
    verdict: Verdict
    meter: Meter | None         # None only when there are no findings
    basis: str                  # counts from summarise_evidence: studies, direction split, CIs excluding null
    findings: list[Finding]     # 2-4 key findings, only as returned by tools
    populations: str            # who was studied, and mismatches with the user's population
    gaps: str                   # what the graph does not cover, where to look next
    concept_ids: list[str]      # graph concepts this card rests on (drives the graph view)


class EvidenceSection(BaseModel):
    type: Literal["evidence"]
    title: str
    cards: list[EvidenceCard]


class Table(BaseModel):
    title: str
    columns: list[str]
    rows: list[list[str]]


class Chart(BaseModel):
    title: str
    vega_lite_json: str         # a complete Vega-Lite v5 spec with inline data, as a JSON string


class EdaSection(BaseModel):
    type: Literal["eda"]
    title: str
    summary: str
    tables: list[Table]
    charts: list[Chart]
    concept_ids: list[str]


class ChainLink(BaseModel):
    cause: str
    effect: str
    via: list[str]              # intermediate concepts, if the link is indirect
    support: Literal["backed", "partial", "unbacked"]
    n_studies: int
    note: str
    dois: list[str]


class PolicySection(BaseModel):
    type: Literal["policy"]
    title: str
    policy: str                 # the intervention or policy being mapped
    links: list[ChainLink]      # the theory-of-change chain, in order
    gaps: str
    concept_ids: list[str]


class Source(BaseModel):
    title: str
    year: int | None
    venue: str | None
    doi: str | None
    url: str | None
    why_relevant: str


class ResearchSection(BaseModel):
    type: Literal["research"]
    title: str
    summary: str
    sources: list[Source]


Section = EvidenceSection | EdaSection | PolicySection | ResearchSection
SECTION_MODELS = {m.model_fields["type"].annotation.__args__[0]: m
                  for m in (EvidenceSection, EdaSection, PolicySection, ResearchSection)}


# Formatter and final answer ----------------------------------------------------------------------
class Overall(BaseModel):
    summary: str                # 3-6 sentence answer to the question, built only from the sections
    section_order: list[int]    # indices into the sections, most useful first
    caveats: list[str]


class Answer(BaseModel):
    question: str
    summary: str
    caveats: list[str]
    sections: list[Section]
