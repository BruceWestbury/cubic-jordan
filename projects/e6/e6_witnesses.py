"""
e6_witnesses.py

E6 obstruction witnesses at t=22.

A witness is a source site at which the seven-term relation, after reduction
and full evaluation, leaves a nonzero scalar — a rational multiple of the
known E6 obstruction polynomial.

Obstruction polynomial (degree 12, Thurston 2004):
    (nn-27)(nn-15)(nn-9)(nn-6)(nn-3)^2(nn-1)nn^2(nn+1)(nn+3)^2
"""

from __future__ import annotations

import json
from pathlib import Path

from sage.all import QQ


def _project_root(project: str) -> Path:
    # __file__ is projects/{project}/e6_witnesses.py; parents[1] = projects/
    return Path(__file__).resolve().parents[1] / project


def _witness_cache_path(project: str, t: int) -> Path:
    return _project_root(project) / "cache" / f"witnesses_t{int(t)}.json"


def _closed_keys(t: int) -> set:
    from projects.e6.e6_sources import closed_bipartite_cubic_graphs

    keys = set()
    for G in closed_bipartite_cubic_graphs(t):
        key = G.canonical_label().graph6_string()
        if isinstance(key, bytes):
            key = key.decode()
        keys.add(key)
    return keys


def e6_t22_witnesses(closed_eval: dict | None = None) -> list[dict]:
    """
    Compute E6 obstruction witnesses at t=22.

    Returns a list of witness records, one per source site whose fully
    evaluated relation is a nonzero rational multiple of the obstruction
    polynomial.

    Parameters
    ----------
    closed_eval :
        Pre-computed evaluation dict from compute_all_e6_evaluations().
        Computed internally if not provided.
    """
    from projects.common.closed_pipeline import (
        closed_partially_evaluated_relations,
        extract_singleton_evaluations,
        find_evaluation_conflicts,
        fully_evaluate_relation_dict,
    )
    from projects.e6.e6_evaluations import compute_all_e6_evaluations
    from projects.e6.e6_series import E6_series_quotient
    from projects.e6.e6_sources import closed_sources

    if closed_eval is None:
        closed_eval = compute_all_e6_evaluations()

    _presentation = E6_series_quotient
    R = _presentation.theory.base_ring
    (nn,) = R.gens()

    collected22 = [
        d
        for d, _ in closed_partially_evaluated_relations(
            22, _presentation, closed_sources, closed_eval
        )
    ]

    values22, conflicts22 = find_evaluation_conflicts(collected22)
    if conflicts22:
        raise ValueError(f"t=22 evaluation conflicts: {conflicts22!r}")

    known22 = {k: value for k, (_, value) in values22.items()}
    known22 = extract_singleton_evaluations(collected22, {}, known22)

    keys22 = _closed_keys(22)
    known22 = {k: v for k, v in known22.items() if k in keys22}

    normalised_obstruction = (
        (nn - 27)
        * (nn - 15)
        * (nn - 9)
        * (nn - 6)
        * (nn - 3) ** 2
        * (nn - 1)
        * nn**2
        * (nn + 1)
        * (nn + 3) ** 2
    )

    witnesses = []

    for i, d in enumerate(collected22):
        scalar, unknowns = fully_evaluate_relation_dict(d, known22)

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

    return witnesses


def write_e6_t22_witness_cache(closed_eval: dict | None = None) -> Path:
    """
    Compute and write the E6 t=22 obstruction witness cache.

    Parameters
    ----------
    closed_eval :
        Pre-computed evaluation dict. Computed internally if not provided.
    """
    witnesses = e6_t22_witnesses(closed_eval)

    doc = {
        "format": "e6_witness_cache",
        "version": 1,
        "project": "e6",
        "t": 22,
        "count": len(witnesses),
        "obstruction_polynomial": (
            "(nn-27)(nn-15)(nn-9)(nn-6)(nn-3)^2(nn-1)nn^2(nn+1)(nn+3)^2"
        ),
        "records": witnesses,
    }

    path = _witness_cache_path("e6", 22)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(doc, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path
