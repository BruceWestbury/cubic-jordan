"""
projects.f4.closed_graph_traces

Traced reductions for small closed F4-series graph computations.
"""

import json
from pathlib import Path
from typing import Any

from algebra.linear_comb import Graphs
from combinatorics.closed_graphs import closed_cubic_sage_graphs
from combinatorics.graph_convert import from_sage_graph
from theory.examples.f4_series import F4_series_quotient
from tracing.export import reduction_trace_document
from tracing.reduce import reduce_element_with_trace


def graph_from_key(key: str):
    """Return the DartGraph with the given canonical key.

    This assumes the graph can be reconstructed by the existing graph-key
    machinery. If your codebase uses a different function name, replace this
    small wrapper only.
    """
    raise NotImplementedError("Replace with the project function for key -> DartGraph.")


def closed_graph_element(graph, presentation=F4_series_quotient):
    """Return the closed graph as an element of the graph module."""
    theory = presentation.theory
    M = Graphs(theory, graph.num_boundary())
    return M.from_graph(graph)


def traced_closed_graph_reduction(
    graph, *, project="f4", presentation=F4_series_quotient
):
    """Reduce a closed graph and return the reduction trace document."""
    expr = closed_graph_element(graph, presentation)
    reduced, trace = reduce_element_with_trace(expr, presentation)

    doc = reduction_trace_document(
        trace=trace,
        project=project,
        input_graph=graph.key(),
    )

    doc["result"] = str(reduced)
    doc["is_zero"] = reduced == expr.parent().zero()

    return doc


def traced_closed_graph_reduction_from_key(
    t: int,
    key: str,
    *,
    project: str = "f4",
    presentation=F4_series_quotient,
) -> dict[str, Any]:
    """Reduce the closed graph identified by vertex count and key."""
    graph = closed_dart_graph_by_key(t, key)
    return traced_closed_graph_reduction(
        graph,
        project=project,
        presentation=presentation,
    )


def write_trace_document(doc: dict, path: Path | str) -> Path:
    """Write a trace document as JSON."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, sort_keys=True)

    return path


def write_closed_graph_trace(
    t: int,
    key: str,
    path: Path | str,
    *,
    project: str = "f4",
    presentation=F4_series_quotient,
) -> Path:
    """Reduce one cached/known closed graph and write its trace JSON."""
    doc = traced_closed_graph_reduction_from_key(
        t,
        key,
        project=project,
        presentation=presentation,
    )
    return write_trace_document(doc, path)


def write_closed_graph_trace_from_key(
    t: int,
    key: str,
    path: Path | str,
    *,
    project="f4",
    presentation=F4_series_quotient,
) -> Path:
    """Reduce a graph identified by key and write its trace document."""
    doc = traced_closed_graph_reduction_from_key(
        t,
        key,
        project=project,
        presentation=presentation,
    )
    return write_trace_document(doc, path)


def closed_dart_graphs_at_t(t: int):
    """Yield closed cubic DartGraphs with t vertices."""
    for G in closed_cubic_sage_graphs(t):
        yield from_sage_graph(G, allow_closed_components=True)


def closed_dart_graph_by_key(t: int, key: str):
    """Return the closed cubic DartGraph with the given canonical key."""
    for g in closed_dart_graphs_at_t(t):
        if g.key() == key:
            return g
    raise KeyError(f"No closed cubic DartGraph with key {key!r} at t={t}")


def closed_graph_by_key(t: int, key: str):
    for g in closed_dart_graphs_at_t(t):
        if g.key() == key:
            return g
    raise KeyError(f"No closed graph with key {key!r} at t={t}")


def first_closed_dart_graph_at_t(t: int):
    """Return the first closed cubic DartGraph at t."""
    return next(closed_dart_graphs_at_t(t))


def write_petersen_trace(path: Path | str) -> Path:
    """Write the first t=10 closed graph trace."""
    graph = first_closed_dart_graph_at_t(10)
    doc = traced_closed_graph_reduction(graph)
    return write_trace_document(doc, path)
