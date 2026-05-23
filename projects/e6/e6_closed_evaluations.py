"""
e6_closed_evaluations.py

Pipeline for deriving E6 closed-graph evaluations level by level.

E6 levels and closed graph / source counts:
    t=14:  1 closed graph  (seeded from pre-computed cache)
    t=16:  1 closed graph,   1 source
    t=18:  3 closed graphs,  6 sources
    t=20: 10 closed graphs, 47 sources
    t=22: 28 closed graphs, 406 sources  (obstruction level)

The t=14 bipartite graph is the seed.  Its value was computed separately
and is stored in the evaluations cache.  With that seed, the t=16 source
relation becomes a singleton and the bootstrap proceeds level by level.
"""

from __future__ import annotations

import json
import re

from closed_graphs.closed_pipeline import (
    closed_locally_reduced_relations,
    closed_partially_evaluated_relations,
    evaluate_known_closed_relation,
    extract_singleton_evaluations,
    find_evaluation_conflicts,
    fully_evaluate_relation_dict,
    unresolved_relations,
)
from e6_sources import closed_sources
from e6_series import E6_series_quotient

presentation = E6_series_quotient
theory = presentation.theory

sources = closed_sources


def seeded_closed_evaluations() -> dict:
    """
    Return seed evaluations for the E6 pipeline.

    The t=14 bipartite cubic graph evaluation is loaded from the
    pre-computed evaluations cache.  Its key is M??haPOEB?OB`G_o?.
    All higher-level values are derived from it via the pipeline.
    """
    from pathlib import Path
    from export.paths import evaluation_cache_dir

    R = theory.base_ring
    (nn,) = R.gens()

    closed_eval = {}

    path = evaluation_cache_dir("e6") / "closed_t14.json"
    if not path.exists():
        return closed_eval

    with path.open(encoding="utf-8") as f:
        doc = json.load(f)

    for record in doc.get("records", []):
        if record.get("status") != "known":
            continue

        # Support both 'graph' key (old format) and 'internal.closed_key' (new format)
        key = record.get("graph") or (
            record.get("internal", {}) or {}
        ).get("closed_key")
        raw = record.get("evaluation")

        if not key or not raw:
            continue

        # Convert LaTeX exponents n^{k} -> n**k, then evaluate with n -> nn
        expr = re.sub(r"\^\{(\d+)\}", r"**\1", raw)
        closed_eval[key] = R(eval(expr, {"n": nn}))  # noqa: S307

    return closed_eval


def compute_t18_evaluations(closed_eval: dict, sources) -> dict:
    """Derive t=18 evaluations using known t=14 and t=16 values."""
    collected = []
    for rel in closed_locally_reduced_relations(18, presentation, sources):
        d, _ = evaluate_known_closed_relation(rel, closed_eval)
        collected.append(d)
    return extract_singleton_evaluations(collected, {}, {})


def compute_t20_evaluations(closed_eval: dict, sources) -> dict:
    """Derive t=20 evaluations using known t=14, t=16, and t=18 values."""
    collected = []
    for rel in closed_locally_reduced_relations(20, presentation, sources):
        d, _ = evaluate_known_closed_relation(rel, closed_eval)
        collected.append(d)
    return extract_singleton_evaluations(collected, {}, {})


def compute_t22_partial_evaluations() -> tuple[dict, list, list]:
    """
    Compute partial t=22 closed-graph evaluations.

    Returns
    -------
    known22 : dict
        Mapping graph_key -> polynomial value.
    collected22 : list[dict]
        Partially evaluated t=22 relations.
    conflicts22 : list
        Conflicting singleton evaluations, expected to be empty.
    """
    closed_eval = seeded_closed_evaluations()

    # t=16: with t=14 seeded, the single t=16 relation is a singleton
    collected16 = [
        d
        for d, _ in closed_partially_evaluated_relations(
            16, presentation, sources, closed_eval
        )
    ]
    known16 = extract_singleton_evaluations(collected16, {}, {})
    closed_eval.update(known16)

    # t=18
    known18 = compute_t18_evaluations(closed_eval, sources)
    closed_eval.update(known18)

    # t=20
    known20 = compute_t20_evaluations(closed_eval, sources)
    closed_eval.update(known20)

    # t=22
    collected22 = [
        d
        for d, _ in closed_partially_evaluated_relations(
            22, presentation, sources, closed_eval
        )
    ]
    values22, conflicts22 = find_evaluation_conflicts(collected22)
    known22 = {k: value for k, (_, value) in values22.items()}
    known22 = extract_singleton_evaluations(collected22, {}, known22)

    return known22, collected22, conflicts22


def compute_t22_obstructions(
    collected22: list, known22: dict
) -> tuple[list, list, list]:
    remainders22, bad22, unresolved22 = [], [], []
    for d in collected22:
        scalar, unknowns = fully_evaluate_relation_dict(d, known22)
        if unknowns:
            unresolved22.append((scalar, unknowns))
            continue
        remainders22.append(scalar)
        if scalar != 0:
            bad22.append(scalar)
    return remainders22, bad22, unresolved22
