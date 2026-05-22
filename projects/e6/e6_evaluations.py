"""
e6_evaluations.py

Export E6 closed-graph evaluation caches using the source/relation pipeline.

For each level t in [16, 18, 20, 22], source sites are generated from all
closed bipartite cubic graphs, the seven-term relation is inserted at each
site, and the result is reduced using the basic E6 rules (bigon + square).
Relations that reduce to singleton evaluations determine graph values.
Running the pipeline across all four levels yields all known evaluations.

Run via the e6_cache.py marimo notebook.
"""

from __future__ import annotations

import json
from pathlib import Path

import graphviz
from closed_graphs.closed_pipeline import (
    closed_partially_evaluated_relations,
    extract_singleton_evaluations,
)
from e6_series import E6_series_quotient
from e6_sources import closed_sources
from export.cache_wrappers import cache_document
from export.paths import cache_root, catalogue_cache_dir, evaluation_cache_dir
from sage.graphs.graph import Graph

# ---------------------------------------------------------------------------
# Catalogue utilities (SVG / invariants / record building)
# ---------------------------------------------------------------------------


def _sage_to_dot(graph) -> str:
    lines = ["graph {"]
    for v in sorted(graph.vertices()):
        lines.append(f"  {v};")
    for u, v in sorted(tuple(sorted(e[:2])) for e in graph.edges(labels=False)):
        lines.append(f"  {u} -- {v};")
    lines.append("}")
    return "\n".join(lines)


def _dot_to_svg(dot_source: str) -> str:
    return graphviz.Source(dot_source).pipe(format="svg").decode("utf-8")


def _graph_to_svg(graph) -> str:
    return _dot_to_svg(_sage_to_dot(graph))


def _json_value(x):
    if x is None or isinstance(x, (str, bool, int, float)):
        return x
    try:
        return int(x)
    except (TypeError, ValueError):
        pass
    return str(x)


def _safe(fn, default=None):
    try:
        return fn()
    except Exception:
        return default


def _graph_invariants(graph) -> dict:
    return {
        "automorphism_group_order": _json_value(
            _safe(lambda: graph.automorphism_group().order())
        ),
        "diameter": _json_value(_safe(lambda: graph.diameter())),
        "radius": _json_value(_safe(lambda: graph.radius())),
        "chromatic_number": _json_value(_safe(lambda: graph.chromatic_number())),
        "is_hamiltonian": _json_value(_safe(lambda: graph.is_hamiltonian())),
        "num_spanning_trees": _json_value(_safe(lambda: graph.spanning_trees_count())),
    }


def _load_evaluation_lookup(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        doc = json.load(f)
    lookup = {}
    for record in doc.get("records", []):
        key = record.get("closed_key") or record.get("key") or record.get("graph")
        value = record.get("value") or record.get("evaluation")
        if key is not None:
            lookup[key] = value
    return lookup


def _closed_catalogue_record(
    *,
    item: dict,
    svg: str,
    dot: str | None = None,
    evaluation: str | None = None,
    invariants: dict | None = None,
) -> dict:
    return {
        "id": item["id"],
        "svg": svg,
        "dot": dot,
        "evaluation": evaluation,
        "invariants": invariants or {},
        "internal": {
            "closed_key": item["closed_key"],
            "graph6": item["graph6"],
        },
    }


PROJECT = "e6"
presentation = E6_series_quotient
sources = closed_sources

# t=14 (Heawood graph) is needed to bootstrap: the t=16 relation is not a
# singleton on its own — it also involves the t=14 graph. Processing t=14
# first gives a singleton evaluation that unlocks all subsequent levels.
PIPELINE_LEVELS = [14, 16, 18, 20, 22]
CACHE_LEVELS = [16, 18, 20, 22]


def raw_closed_graph_items(t: int) -> list[dict]:
    path = cache_root(PROJECT) / "closed" / f"closed_bipartite_t{int(t)}.json"
    with path.open("r", encoding="utf-8") as f:
        doc = json.load(f)
    return doc["graphs"]


def compute_all_e6_evaluations() -> dict:
    """
    Run the level-by-level pipeline and return all known evaluations.

    For each level t, source sites are generated from the closed bipartite
    cubic graphs, the seven-term relation is inserted at each site, and the
    result is reduced using E6_series_quotient (bigon + square rules).
    Relations that are singletons immediately yield a graph evaluation.
    Evaluations found at earlier levels are substituted into later ones.

    Returns
    -------
    dict
        Mapping graph_key -> polynomial value for every graph whose
        evaluation was determined by the pipeline.
    """
    closed_eval = {}
    for t in PIPELINE_LEVELS:
        collected = [
            d
            for d, _ in closed_partially_evaluated_relations(
                t, presentation, sources, closed_eval
            )
        ]
        new_evals = extract_singleton_evaluations(collected, {}, {})
        closed_eval.update(new_evals)
    return closed_eval


def write_e6_closed_evaluation_cache(t: int, closed_eval: dict) -> Path:
    """
    Write the evaluation cache for closed bipartite cubic graphs at level t.

    Parameters
    ----------
    t : int
        Vertex count (16, 18, 20, or 22).
    closed_eval : dict
        Full evaluation dict from ``compute_all_e6_evaluations()``.

    Returns
    -------
    Path
        Path to the written cache file.
    """
    items = raw_closed_graph_items(t)
    records = []

    for item in items:
        key = item["closed_key"]
        graph = Graph(item["graph6"])
        svg = _graph_to_svg(graph)
        dot = _sage_to_dot(graph)
        invariants = _graph_invariants(graph)

        record = {
            "id": item["id"],
            "graph": key,
            "graph6": item["graph6"],
            "svg": svg,
            "dot": dot,
            "invariants": invariants,
            "method": "pipeline",
        }

        if key in closed_eval:
            record["status"] = "known"
            record["evaluation"] = str(closed_eval[key])
        else:
            record["status"] = "unknown"
            record["evaluation"] = None

        records.append(record)

    records.sort(key=lambda r: r["graph"])

    doc = cache_document(
        format="evaluation_cache",
        version=1,
        project=PROJECT,
        records=records,
        metadata={
            "t": int(t),
            "count": len(records),
            "known_count": sum(r["evaluation"] is not None for r in records),
            "unknown_count": sum(r["evaluation"] is None for r in records),
            "method": "pipeline",
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
    """
    Compute all E6 evaluations and write one cache file per level.

    Returns
    -------
    list[Path]
        Paths to the written cache files, one per level in LEVELS.
    """
    closed_eval = compute_all_e6_evaluations()
    return [write_e6_closed_evaluation_cache(t, closed_eval) for t in CACHE_LEVELS]


def write_e6_closed_catalogue_cache(t: int) -> Path:
    """
    Write the web-facing catalogue cache for E6 closed graphs at level t.

    Reads raw graphs from cache/closed/closed_bipartite_t{t}.json,
    looks up evaluations from cache/evaluations/closed_t{t}.json,
    generates SVG and graph invariants, and writes the combined record
    to cache/closed/closed_t{t}.json.

    Returns
    -------
    Path
        Path to the written catalogue file.
    """
    raw_path = cache_root(PROJECT) / "closed" / f"closed_bipartite_t{int(t)}.json"
    with raw_path.open("r", encoding="utf-8") as f:
        raw_doc = json.load(f)

    evaluation_path = evaluation_cache_dir(PROJECT) / f"closed_t{int(t)}.json"
    evaluations = _load_evaluation_lookup(evaluation_path)

    records = []
    for item in raw_doc["graphs"]:
        graph = Graph(item["graph6"])
        svg = _graph_to_svg(graph)
        dot = _sage_to_dot(graph)
        invariants = _graph_invariants(graph)
        evaluation = evaluations.get(item["closed_key"])

        record = _closed_catalogue_record(
            item=item,
            svg=svg,
            dot=dot,
            evaluation=evaluation,
            invariants=invariants,
        )
        records.append(record)

    doc = cache_document(
        format="closed_graph_catalogue",
        version=1,
        project=PROJECT,
        records=records,
        metadata={
            "t": int(t),
            "count": len(records),
        },
    )

    out_path = catalogue_cache_dir(PROJECT) / f"closed_t{int(t)}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    out_path.write_text(
        json.dumps(doc, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return out_path


def write_all_e6_closed_catalogue_caches() -> list[Path]:
    """
    Write web-facing catalogue caches for all E6 levels.

    Evaluation caches must already exist (run
    ``write_all_e6_closed_evaluation_caches`` first).

    Returns
    -------
    list[Path]
        Paths to the written catalogue files.
    """
    return [write_e6_closed_catalogue_cache(t) for t in CACHE_LEVELS]
