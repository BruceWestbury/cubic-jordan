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

from closed_graphs.closed_pipeline import (
    closed_partially_evaluated_relations,
    extract_singleton_evaluations,
)
from e6_series import E6_series_quotient
from e6_sources import closed_sources
from export.cache_wrappers import cache_document
from export.paths import cache_root, evaluation_cache_dir

PROJECT = "e6"
presentation = E6_series_quotient
sources = closed_sources
LEVELS = [16, 18, 20, 22]


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
    for t in LEVELS:
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
        if key in closed_eval:
            records.append(
                {
                    "graph": key,
                    "status": "known",
                    "value": str(closed_eval[key]),
                    "method": "pipeline",
                }
            )
        else:
            records.append(
                {
                    "graph": key,
                    "status": "unknown",
                    "method": "pipeline",
                }
            )

    records.sort(key=lambda r: r["graph"])

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
    return [write_e6_closed_evaluation_cache(t, closed_eval) for t in LEVELS]
