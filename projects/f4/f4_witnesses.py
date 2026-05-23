"""
f4_witnesses.py

F4 obstruction witnesses at t=16.

A witness is a source site at which the seven-term relation, after reduction
and full evaluation, leaves a nonzero scalar — a rational multiple of the
known F4 obstruction polynomial.

Obstruction polynomial (degree 9):
    n(n-26)(n-14)(n-8)(n-5)(n+1)(n+2)(n-2)^2
"""

from __future__ import annotations

import json
from pathlib import Path

from sage.all import QQ


def _catalogue_cache_dir(project: str) -> Path:
    return Path(__file__).resolve().parents[2] / project / "cache" / "closed"


def _closed_keys(t: int) -> set:
    from projects.f4.f4_sources import closed_cubic_girth5_graphs

    keys = set()
    for G in closed_cubic_girth5_graphs(t):
        key = G.canonical_label().graph6_string()
        if isinstance(key, bytes):
            key = key.decode()
        keys.add(key)
    return keys


def f4_t16_witnesses() -> list[dict]:
    """
    Compute F4 obstruction witnesses at t=16.

    Returns a list of witness records, one per source site whose fully
    evaluated relation is a nonzero rational multiple of the obstruction
    polynomial.
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

    _presentation = F4_series_quotient
    R = _presentation.theory.base_ring
    (n,) = R.gens()

    closed_eval = compute_all_f4_evaluations()

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

    known16 = {k: value for k, (_, value) in values16.items()}
    known16 = extract_singleton_evaluations(collected16, {}, known16)

    keys16 = _closed_keys(16)
    known16 = {k: v for k, v in known16.items() if k in keys16}

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

    if len(witnesses) != 38:
        raise ValueError(f"expected 38 obstruction witnesses, got {len(witnesses)}")

    return witnesses


def write_f4_t16_witness_cache() -> Path:
    witnesses = f4_t16_witnesses()

    doc = {
        "format": "f4_witness_cache",
        "version": 1,
        "project": "f4",
        "t": 16,
        "count": len(witnesses),
        "obstruction_polynomial": "n(n-26)(n-14)(n-8)(n-5)(n+1)(n+2)(n-2)^2",
        "records": witnesses,
    }

    path = _catalogue_cache_dir("f4") / "witnesses_t16.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(doc, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path
