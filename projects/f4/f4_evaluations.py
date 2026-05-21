"""
export.f4_evaluations

Export F4 closed-graph evaluation caches using the pentagon presentation.
"""

from __future__ import annotations

import json
from pathlib import Path

from sage.graphs.graph import Graph

from algebra.linear_comb import Graphs
from combinatorics.graph_convert import from_sage_graph
from export.cache_wrappers import cache_document
from visualisation.dot import dart_graph_to_dot
from export.paths import evaluation_cache_dir, raw_graph_cache_dir
from rewriting.reduce import reduce_element_fully
from theory.examples.f4_series import F4_series_pentagons

PROJECT = "f4"
presentation = F4_series_pentagons


def raw_closed_graph_items(t: int) -> list[dict]:
    path = raw_graph_cache_dir(PROJECT) / f"closed_t{int(t)}.json"

    with path.open("r", encoding="utf-8") as f:
        doc = json.load(f)

    return doc["graphs"]


def reduced_closed_graph_evaluation(graph6: str):
    """
    Reduce a closed graph using F4_series_pentagons.

    Returns the scalar value if the graph reduces to a multiple of the
    empty graph, otherwise returns None.
    """
    sage_graph = Graph(graph6)
    dart_graph = from_sage_graph(
        sage_graph,
        allow_closed_components=True,
    )

    theory = presentation.theory
    element = Graphs(theory, 0).from_graph(dart_graph)
    reduced = reduce_element_fully(element, presentation)

    coeffs = reduced.monomial_coefficients(copy=False)

    if len(coeffs) != 1:
        return None

    graph, coeff = next(iter(coeffs.items()))

    if graph.num_vertices() == 0:
        return coeff

    return None


def evaluation_record(item: dict) -> dict:
    value = reduced_closed_graph_evaluation(item["graph6"])

    if value is None:
        return {
            "graph": item["closed_key"],
            "status": "unknown",
            "method": "residual",
        }

    return {
        "graph": item["closed_key"],
        "status": "known",
        "value": str(value),
        "method": "F4_series_pentagons",
    }


def f4_closed_evaluation_records(t: int) -> list[dict]:
    records = [evaluation_record(item) for item in raw_closed_graph_items(t)]

    records.sort(key=lambda record: record["graph"])
    return records


def closed_graph_record(G, value=None):
    """Return one JSON record for a closed graph."""
    return {
        "key": G.key(),
        "graph": dart_graph_to_json(G),
        "dot": dart_graph_to_dot(G),
        "invariants": {
            "num_vertices": G.num_vertices(),
            "num_edges": G.num_edges(),
            "boundary_size": len(G.boundary_darts()),
        },
        "value": str(value) if value is not None else None,
    }


def write_f4_closed_evaluation_cache(t: int) -> Path:
    records = f4_closed_evaluation_records(t)

    doc = cache_document(
        format="evaluation_cache",
        version=1,
        project=PROJECT,
        records=records,
        metadata={
            "t": int(t),
            "count": len(records),
            "known_count": sum(r["status"] == "known" for r in records),
            "unknown_count": sum(r["status"] == "unknown" for r in records),
            "method": "F4_series_pentagons",
        },
    )

    path = evaluation_cache_dir(PROJECT) / f"closed_t{int(t)}.json"
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(doc, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return path


def write_all_f4_closed_evaluation_caches() -> list[Path]:
    return [write_f4_closed_evaluation_cache(t) for t in [10, 12, 14, 16]]
