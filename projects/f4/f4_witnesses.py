"""
f4_witnesses.py

F4 obstruction witnesses at t=16.

A witness is a source site at which the six-term relation, after reduction
and full evaluation, leaves a nonzero scalar — a rational multiple of the
known F4 obstruction polynomial.

Obstruction polynomial (degree 9):
    n(n-26)(n-14)(n-8)(n-5)(n+1)(n+2)(n-2)^2
"""

from __future__ import annotations

import json
from pathlib import Path

from sage.all import QQ


def _project_root(project: str) -> Path:
    # __file__ is projects/{project}/f4_witnesses.py; parents[1] = projects/
    return Path(__file__).resolve().parents[1] / project


def _witness_cache_path(project: str, t: int) -> Path:
    return _project_root(project) / "cache" / f"witnesses_t{int(t)}.json"


def _closed_keys(t: int) -> set:
    from projects.f4.f4_sources import closed_cubic_girth5_graphs

    keys = set()
    for G in closed_cubic_girth5_graphs(t):
        key = G.canonical_label().graph6_string()
        if isinstance(key, bytes):
            key = key.decode()
        keys.add(key)
    return keys


def f4_t16_witnesses(closed_eval: dict | None = None) -> list[dict]:
    """
    Compute F4 obstruction witnesses at t=16.

    Returns a list of witness records, one per source site whose fully
    evaluated relation is a nonzero rational multiple of the obstruction
    polynomial.

    Parameters
    ----------
    closed_eval :
        Pre-computed evaluation dict from compute_all_f4_evaluations().
        Computed internally if not provided.
    """
    from projects.common.closed_pipeline import (
        closed_partially_evaluated_relations,
        extract_singleton_evaluations,
        find_evaluation_conflicts,
        fully_evaluate_relation_dict,
    )
    from projects.f4.f4_evaluations import compute_all_f4_evaluations
    from projects.f4.f4_series import F4_series_quotient
    from projects.f4.f4_sources import closed_sources

    if closed_eval is None:
        closed_eval = compute_all_f4_evaluations()

    _presentation = F4_series_quotient
    R = _presentation.theory.base_ring
    (n,) = R.gens()

    collected16 = [
        d
        for d, _ in closed_partially_evaluated_relations(
            16, _presentation, closed_sources, closed_eval
        )
    ]

    if len(collected16) != 335:
        raise ValueError(f"expected 335 t=16 relations, got {len(collected16)}")

    values16, conflicts16 = find_evaluation_conflicts(collected16)
    if conflicts16:
        raise ValueError(f"t=16 evaluation conflicts: {conflicts16!r}")

    keys16 = _closed_keys(16)
    known16 = {k: v for k, v in closed_eval.items() if k in keys16}

    if len(known16) != 49:
        raise ValueError(f"expected 49 t=16 evaluations, got {len(known16)}")

    normalised_obstruction = (
        n * (n - 26) * (n - 14) * (n - 8) * (n - 5) * (n + 1) * (n + 2) * (n - 2) ** 2
    )

    witnesses = []

    for i, d in enumerate(collected16):
        scalar, unknowns = fully_evaluate_relation_dict(d, known16)

        if unknowns or scalar == 0:
            continue

        multiplier = scalar / normalised_obstruction

        if multiplier not in QQ:
            raise ValueError(f"non-rational multiplier at index {i}: {multiplier}")

        witnesses.append(
            {
                "index": i,
                "raw_obstruction": str(scalar),
                "factorisation": str(scalar.factor()),
                "normalised_obstruction": str(normalised_obstruction),
                "multiplier": str(multiplier),
            }
        )

    witnesses.sort(key=lambda r: r["index"])

    for display_index, witness in enumerate(witnesses):
        witness["display_index"] = display_index

    if not witnesses:
        raise ValueError("expected at least one obstruction witness, got none")

    return witnesses


def write_f4_t16_witness_cache(closed_eval: dict | None = None) -> Path:
    """
    Compute and write the F4 t=16 obstruction witness cache.

    Parameters
    ----------
    closed_eval :
        Pre-computed evaluation dict. Computed internally if not provided.
    """
    witnesses = f4_t16_witnesses(closed_eval)

    doc = {
        "format": "f4_witness_cache",
        "version": 1,
        "project": "f4",
        "t": 16,
        "count": len(witnesses),
        "obstruction_polynomial": "n(n-26)(n-14)(n-8)(n-5)(n+1)(n+2)(n-2)^2",
        "records": witnesses,
    }

    path = _witness_cache_path("f4", 16)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(doc, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return path
