"""A small simulator of the weekday toll schedule of Manhattan's congestion zone.

It composes a chain of associations, each a parameter with an interval and a source,
read from data/derived/simulate/parameters.json. It is not a causal model of New York.
See docs/policy_simulation.md.
"""
from sim.model import load, simulate, summarise  # noqa: F401
