"""
e6_evaluations.py

Export E6 closed-graph evaluation caches using the pipeline approach.

The pipeline levels are t = 14, 16, 18, 20, 22.

t=14 is seeded from a pre-computed cache (see e6_closed_evaluations.py).
t=16-22 are derived level by level from the seven-term relation sources.

Run via the e6_cache.py marimo notebook:

    sage -python -m marimo edit projects/e6/e6_cache.py
"""

from __future__ import annotations

import json
from pathlib import Path

from export.cache_wrappers import cache_document
from export.paths import cache_root, evaluation_cache_dir
from e6_series import E6_series_quotient

PROJECT = "e6"
presentation = E6_series_quotient
LEVELS = [16, 18, 20, 22]          # levels written by this module
SEEDED_LEVELS = [14]                # levels with pre-computed caches (not overwritten)


def raw_closed_graph_items(t: int) -> list[dict]:
    path = cache_root(PROJECT) / "closed" / f"closed_bipartite_t{int(t)}.json"
    with path.open("r", encoding="utf-8") as f:
        doc = json.load(f)
    return doc["graphs"]


def _build_all_evaluations() -> dict:
    """
    Run the E6 source pipeline and return all known closed-graph evaluations.

    Returns
    -------
    dict
        Mapping closed_key -> polynomial value in ZZ['nn'].
    """
    from closed_graphs.closed_pipeline import (
        closed_partially_evaluated_relations,
        extract_singleton_evaluations,
        find_evaluation_conflicts,
    )
    from e6_sources import closed_sources
    from e6_closed_evaluations import (
        seeded_closed_evaluations,
        compute_t18_evaluations,
        compute_t20_evaluations,
    )

    # Start with the pre-computed t=14 seed
    closed_eval = seeded_closed_evaluations()

    # t=16: with the t=14 seed, the single t=16 relation is a singleton
    collected16 = [
        d
        for d, _ in closed_partially_evaluated_relations(
            16, presentation, closed_sources, closed_eval
        )
    ]
    known16 = extract_singleton_evaluations(collected16, {}, {})
    closed_eval.update(known16)

    # t=18
    known18 = compute_t18_evaluations(closed_eval, closed_sources)
    closed_eval.update(known18)

    # t=20
    known20 = compute_t20_evaluations(closed_eval, closed_sources)
    closed_eval.update(known20)

    # t=22
    collected22 = [
        d
        for d, _ in closed_partially_evaluated_relations(
            22, presentation, closed_sources, closed_eval
        )
    ]
    values22, _ = find_evaluation_conflicts(collected22)
    known22 = {k: v for k, (_, v) in values22.items()}
    known22 = extract_singleton_evaluations(collected22, {}, known22)
    closed_eval.update(known22)

    return closed_eval


def _evaluation_record(item: dict, all_evals: dict) -> dict:
    key = item["closed_key"]
    value = all_evals.get(key)

    record: dict = {
        "internal": {
            "closed_key": key,
            "graph6": item["graph6"],
        },
    }

    if value is not None:
        record["evaluation"] = str(value).replace("nn", "n")
        record["status"] = "known"
        record["method"] = "E6_series_quotient_pipeline"
    else:
        record["evaluation"] = None
        record["status"] = "unknown"
        record["method"] = "residual"

    return record


def _write_cache_for_level(t: int, all_evals: dict) -> Path:
    items = raw_closed_graph_items(t)
    records = [_evaluation_record(item, all_evals) for item in items]
    records.sort(key=lambda r: r["internal"]["closed_key"])

    known = sum(1 for r in records if r["status"] == "known")

    doc = cache_document(
        format="evaluation_cache",
        version=1,
        project=PROJECT,
        records=records,
        metadata={
            "t": int(t),
            "count": len(records),
            "known_count": known,
            "unknown_count": len(records) - known,
            "method": "E6_series_quotient_pipeline",
        },
    )

    path = evaluation_cache_dir(PROJECT) / f"closed_t{int(t)}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_all_e6_closed_evaluation_caches() -> list[Path]:
    """
    Compute all E6 evaluations once using the pipeline, then write one
    cache file per level in LEVELS.  The t=14 cache is pre-computed and
    not overwritten.
    """
    all_evals = _build_all_evaluations()
    return [_write_cache_for_level(t, all_evals) for t in LEVELS]
