"""
Provenance-aware source generators for public cache export.

These generators record how each source arises before deduplication.
They are intended for the public/static repository export layer.
"""

from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator


@dataclass(frozen=True)
class SourceConstruction:
    closed_key: str
    operation: dict[str, Any]
    closed_class: str  # "pentagon_evaluable" or "residual"


@dataclass
class SourceRecord:
    source_key: str
    graph: Any
    site: tuple[int, ...]
    constructions: list[SourceConstruction] = field(default_factory=list)


def _sage_graph_key(G) -> str:
    key = G.canonical_label().graph6_string()
    if isinstance(key, bytes):
        key = key.decode()
    return key


# ---------------------------------------------------------------------
# F4
# ---------------------------------------------------------------------


def f4_source_records(n: int) -> Iterator[SourceRecord]:
    """
    Yield provenance-aware F4 source records.

    Each source is obtained from a closed cubic girth >= 5 graph by
    contracting one edge to a four-valent vertex, then deleting that
    vertex to form a DartGraph with a 4-element site.
    """
    from closed_graphs.f4_sources import (
        closed_cubic_girth5_graphs,
        contract_to_four_valent,
        four_valent_graph_to_source,
        four_valent_key,
    )

    records: dict[str, SourceRecord] = {}

    for G in closed_cubic_girth5_graphs(n):
        closed_key = _sage_graph_key(G)

        for e in G.edges(labels=False):
            edge = tuple(e[:2])

            F = contract_to_four_valent(G, edge)

            K = four_valent_key(F)
            source_key = K.graph6_string()
            if isinstance(source_key, bytes):
                source_key = source_key.decode()

            graph, site = four_valent_graph_to_source(F)

            closed_class = "unknown"

            construction = SourceConstruction(
                closed_key=closed_key,
                operation={
                    "type": "contract_edge",
                    "edge": list(edge),
                },
                closed_class=closed_class,
            )

            if source_key not in records:
                records[source_key] = SourceRecord(
                    source_key=source_key,
                    graph=graph,
                    site=tuple(site),
                    constructions=[construction],
                )
            else:
                records[source_key].constructions.append(construction)

    yield from records.values()


# ---------------------------------------------------------------------
# E6
# ---------------------------------------------------------------------


def e6_source_records(n: int) -> Iterator[SourceRecord]:
    """
    Yield provenance-aware E6 source records.

    Each source is obtained from a closed bipartite cubic graph by choosing
    an interval a-b-c, identifying a and c, and deleting the resulting
    five-valent/two-valent source structure.
    """
    from closed_graphs.e6_sources import (
        closed_bipartite_cubic_graphs,
        contract_interval_to_five_valent,
        five_valent_graph_to_source,
        five_valent_key,
        intervals_of_length_two,
        validate_five_valent_graph,
    )

    records: dict[str, SourceRecord] = {}

    for G in closed_bipartite_cubic_graphs(n):
        closed_key = _sage_graph_key(G)

        for a, b, c in intervals_of_length_two(G):
            F = contract_interval_to_five_valent(G, a, b, c)
            validate_five_valent_graph(F)

            source_key = five_valent_key(F)

            graph, site = five_valent_graph_to_source(F)

            construction = SourceConstruction(
                closed_key=closed_key,
                operation={
                    "type": "contract_interval",
                    "interval": [a, b, c],
                },
            )

            if source_key not in records:
                records[source_key] = SourceRecord(
                    source_key=source_key,
                    graph=graph,
                    site=tuple(site),
                    constructions=[construction],
                )
            else:
                records[source_key].constructions.append(construction)

    yield from records.values()
