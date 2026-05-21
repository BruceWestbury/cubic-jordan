"""
src.closed_graphs.f4_closed_evaluations
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
from closed_graphs.f4_sources import closed_sources
from theory.examples.f4_series import F4_series_quotient

presentation = F4_series_quotient
theory = presentation.theory

sources = closed_sources


def seeded_closed_evaluations():
    R = theory.base_ring
    (n,) = R.gens()

    closed_eval = {}

    # t = 10
    closed_eval["I@OZCMgs?"] = (
        n * (n - 2) * (n + 2) * 2**5 * (n**3 - 27 * n**2 + 54 * n + 72) / 128
    )

    # t = 12
    closed_eval["K?HHa`_aSKQC"] = (
        -n
        * (n - 2)
        * (n + 2)
        * 2**6
        * (n**4 - 38 * n**3 + 268 * n**2 - 192 * n - 464)
        / 512
    )

    closed_eval["KG?qPPO_[WQO"] = (
        n
        * (n - 2)
        * (n + 2)
        * 2**6
        * (5 * n**4 - 172 * n**3 + 1316 * n**2 - 864 * n - 2496)
        / 2048
    )

    return closed_eval


def compute_t14_evaluations(closed_eval, sources):
    collected14 = []

    for rel in closed_locally_reduced_relations(
        14,
        presentation,
        sources,
    ):
        d, _ = evaluate_known_closed_relation(rel, closed_eval)
        collected14.append(d)

    known14 = extract_singleton_evaluations(
        collected14,
        {},
        {},
    )

    return known14


def compute_t16_partial_evaluations():
    """
    Compute the partial t=16 closed-graph evaluations.

    Returns
    -------
    known16 : dict
        Mapping graph_key -> polynomial value.
    collected16 : list[dict]
        Partially evaluated t=16 relations.
    conflicts16 : list
        Conflicting singleton evaluations, expected to be empty.
    """

    closed_eval = seeded_closed_evaluations()

    known14 = compute_t14_evaluations(closed_eval, closed_sources)
    closed_eval.update(known14)

    collected16 = [
        d
        for d, _ in closed_partially_evaluated_relations(
            16,
            presentation,
            sources,
            closed_eval,
        )
    ]

    values16, conflicts16 = find_evaluation_conflicts(collected16)

    known16 = {k: value for k, (_, value) in values16.items()}

    known16 = extract_singleton_evaluations(
        collected16,
        {},
        known16,
    )

    return known16, collected16, conflicts16


def compute_t16_obstructions(collected16, known16):
    remainders16 = []
    bad16 = []
    unresolved16 = []

    for d in collected16:
        scalar, unknowns = fully_evaluate_relation_dict(d, known16)

        if unknowns:
            unresolved16.append((scalar, unknowns))
            continue

        remainders16.append(scalar)

        if scalar != 0:
            bad16.append(scalar)

    return remainders16, bad16, unresolved16
