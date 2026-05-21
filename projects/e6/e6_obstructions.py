"""
e6_obstructions.py

E6 obstruction witness computation at t=22.

Obstruction polynomial (Thurston 2004, "The F4 and E6 families have a
finite number of points"):

    (nn-27)(nn-15)(nn-9)(nn-6)(nn-3)^2 (nn-1) nn^2 (nn+1)(nn+3)^2 = 0

This is a degree-12 polynomial in nn.  The roots correspond to known
members of the E6 family:

    nn=27  E6
    nn=15  A5 / SL(6)/+-1
    nn=9   2A2
    nn=6   A2
    nn=3   2C  (double root)
    nn=1   0
    nn=0   0   (double root)
    nn=-1  OSp(1|2)
    nn=-3  A2  (double root)
"""

import json
from pathlib import Path

from sage.all import QQ

from closed_graphs.closed_pipeline import (
    closed_partially_evaluated_relations,
    extract_singleton_evaluations,
    find_evaluation_conflicts,
    fully_evaluate_relation_dict,
)
from e6_closed_evaluations import (
    compute_t18_evaluations,
    compute_t20_evaluations,
    seeded_closed_evaluations,
)
from e6_sources import closed_bipartite_cubic_graphs, closed_sources
from export.paths import catalogue_cache_dir
from e6_series import E6_series_quotient


def _closed_keys(t):
    keys = set()

    for G in closed_bipartite_cubic_graphs(t):
        key = G.canonical_label().graph6_string()

        if isinstance(key, bytes):
            key = key.decode()

        keys.add(key)

    return keys


def e6_t22_obstruction_witnesses():
    presentation = E6_series_quotient
    theory = presentation.theory

    R = theory.base_ring
    (nn,) = R.gens()

    closed_eval = seeded_closed_evaluations()

    # t=16
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
        * nn ** 2
        * (nn + 1)
        * (nn + 3) ** 2
    )

    witnesses = []

    for i, d in enumerate(collected22):
        scalar, unknowns = fully_evaluate_relation_dict(d, known22)

        if unknowns:
            continue

        if scalar == 0:
            continue

        multiplier = scalar / normalised_obstruction

        if multiplier not in QQ:
            raise ValueError(
                f"non-rational multiplier at index {i}: {multiplier}"
            )

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


def write_e6_t22_obstruction_cache() -> Path:
    witnesses = e6_t22_obstruction_witnesses()

    path = catalogue_cache_dir("e6") / "obstructions_t22.json"
    path.parent.mkdir(parents=True, exist_ok=True)

    doc = {
        "format": "e6_obstruction_witness_cache",
        "version": 1,
        "project": "e6",
        "t": 22,
        "count": len(witnesses),
        "obstruction_polynomial": (
            "(nn-27)(nn-15)(nn-9)(nn-6)(nn-3)^2(nn-1)nn^2(nn+1)(nn+3)^2"
        ),
        "records": witnesses,
    }

    path.write_text(
        json.dumps(doc, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return path
