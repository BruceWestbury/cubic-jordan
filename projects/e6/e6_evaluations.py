"""
e6_evaluations.py

Export E6 closed-graph evaluation caches using E6_series_quotient.

Each closed bipartite cubic graph is reduced directly as a closed element.
If it reduces to a scalar multiple of the empty graph the value is recorded;
otherwise the graph is marked as unknown.

Run via the e6_cache.py marimo notebook.
"""

from __future__ import annotations

import json
from pathlib import Path

from sage.graphs.graph import Graph

from algebra.linear_comb import Graphs
from combinatorics.graph_convert import from_sage_graph
from export.cache_wrappers import cache_document
from export.paths import cache_root, evaluation_cache_dir
from rewriting.reduce import reduce_element_fully
from e6_series import E6_series_quotient

PROJECT = "e6"
presentation = E6_series_quotient
LEVELS = [16, 18, 20, 22]


def raw_closed_graph_items(t: int) -> list[dict]:
    path = cache_root(PROJECT) / "closed" / f"closed_bipartite_t{int(t)}.json"
    with path.open("r", encoding="utf-8") as f:
        doc = json.load(f)
    return doc["graphs"]


def reduced_closed_graph_evaluation(graph6: str):
    """
    Reduce a closed graph using E6_series_quotient.

    Returns the scalar value if the graph reduces to a multiple of the
    empty graph, otherwise returns None.
    """
    sage_graph = Graph(graph6)
    dart_graph = from_sage_graph(sage_graph, allow_closed_components=True)

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
        "method": "E6_series_quotient",
    }


def e6_closed_evaluation_records(t: int) -> list[dict]:
    records = [evaluation_record(item) for item in raw_closed_graph_items(t)]
    records.sort(key=lambda record: record["graph"])
    return records


def write_e6_closed_evaluation_cache(t: int) -> Path:
    records = e6_closed_evaluation_records(t)

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
            "method": "E6_series_quotient",
        },
    )

    path = evaluation_cache_dir(PROJECT) / f"closed_t{int(t)}.json"
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(doc, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return path


def write_all_e6_closed_evaluation_caches() -> list[Path]:
    return [write_e6_closed_evaluation_cache(t) for t in LEVELS]
