"""
e6_closed_evaluations.py

Pipeline for deriving E6 closed-graph evaluations level by level.

E6 levels and closed graph / source counts:
    t=16:  1 closed graph,   1 source
    t=18:  3 closed graphs,  6 sources
    t=20: 10 closed graphs, 47 sources
    t=22: 28 closed graphs, 406 sources  (obstruction level)

At t=16 there is a single source and a single closed graph.  The one
resulting relation is a singleton and determines the t=16 evaluation
directly — no seeded values are required.
"""

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


def seeded_closed_evaluations():
    """
    Return seed evaluations for the E6 pipeline.

    No seeds are required: the singleton relation at t=16 bootstraps
    the entire computation.
    """
    return {}


def compute_t18_evaluations(closed_eval, sources):
    """
    Derive t=18 evaluations using known t=16 values.
    """
    collected18 = []

    for rel in closed_locally_reduced_relations(18, presentation, sources):
        d, _ = evaluate_known_closed_relation(rel, closed_eval)
        collected18.append(d)

    known18 = extract_singleton_evaluations(collected18, {}, {})
    return known18


def compute_t20_evaluations(closed_eval, sources):
    """
    Derive t=20 evaluations using known t=16 and t=18 values.
    """
    collected20 = []

    for rel in closed_locally_reduced_relations(20, presentation, sources):
        d, _ = evaluate_known_closed_relation(rel, closed_eval)
        collected20.append(d)

    known20 = extract_singleton_evaluations(collected20, {}, {})
    return known20


def compute_t22_partial_evaluations():
    """
    Compute the partial t=22 closed-graph evaluations.

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

    # t=16: 1 closed graph, 1 source — singleton determines evaluation
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


def compute_t22_obstructions(collected22, known22):
    remainders22 = []
    bad22 = []
    unresolved22 = []

    for d in collected22:
        scalar, unknowns = fully_evaluate_relation_dict(d, known22)

        if unknowns:
            unresolved22.append((scalar, unknowns))
            continue

        remainders22.append(scalar)

        if scalar != 0:
            bad22.append(scalar)

    return remainders22, bad22, unresolved22
