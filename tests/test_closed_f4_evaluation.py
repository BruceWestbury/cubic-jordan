"""
Regression test for the closed-graph F4 evaluation pipeline.

Obsolete: this test was written against a two-variable ring (aa, nn) and
the modules closed_graphs.local_relations / closed_graphs.closed_evaluation,
which no longer exist.  The current pipeline uses a single-variable ring
QQ['n'] and projects.common.closed_pipeline.

Run with: sage -python -m pytest tests/test_closed_f4_evaluation.py -m slow
"""

import pytest

pytest.skip(
    "Obsolete: tests a two-variable (aa, nn) ring and closed_graphs.local_relations "
    "API that no longer exists.  Rewrite against projects.f4 and "
    "projects.common.closed_pipeline.",
    allow_module_level=True,
)


@pytest.mark.slow
def test_f4_closed_t16_polynomial_obstruction():
    presentation = f4_series.F4_series_quotient
    theory = presentation.theory

    R = theory.base_ring
    aa, nn = R.gens()

    closed_eval = {}

    # t = 10
    closed_eval["I@OZCMgs?"] = (
        nn * (nn - 2) * (nn + 2) * aa**5 * (nn**3 - 27 * nn**2 + 54 * nn + 72) / 128
    )

    # t = 12
    closed_eval["K?HHa`_aSKQC"] = (
        -nn
        * (nn - 2)
        * (nn + 2)
        * aa**6
        * (nn**4 - 38 * nn**3 + 268 * nn**2 - 192 * nn - 464)
        / 512
    )

    closed_eval["KG?qPPO_[WQO"] = (
        nn
        * (nn - 2)
        * (nn + 2)
        * aa**6
        * (5 * nn**4 - 172 * nn**3 + 1316 * nn**2 - 864 * nn - 2496)
        / 2048
    )

    # t = 14
    collected14 = []

    for rel in closed_reduced_relations(14, presentation):
        d, reps = evaluate_known_closed_relation_dict(
            *__import__(
                "closed_graphs.local_relations",
                fromlist=["sage_collect_relation"],
            ).sage_collect_relation(rel),
            closed_eval,
        )
        collected14.append(d)

    assert len(collected14) == 31

    known14 = extract_singleton_evaluations(collected14, {}, {})
    assert len(known14) == 9

    closed_eval.update(known14)

    # t = 16
    collected16 = [
        d
        for d, _ in closed_partially_evaluated_relations(16, presentation, closed_eval)
    ]

    assert len(collected16) == 335

    values16, conflicts16 = find_evaluation_conflicts(collected16)

    assert len(values16) == 39
    assert conflicts16 == []

    known16 = {k: value for k, (_, value) in values16.items()}
    known16 = extract_singleton_evaluations(collected16, {}, known16)

    assert len(known16) == 49

    rem16 = unresolved_relations(collected16, known16)

    assert len(rem16) == 38
    assert all(not unknowns for unknowns, _ in rem16)

    remainders16 = []

    for d in collected16:
        scalar, unknowns = fully_evaluate_relation_dict(d, known16)
        assert not unknowns
        remainders16.append(scalar)

    bad = [r for r in remainders16 if r != 0]

    assert len(bad) == 38

    expected = (
        nn
        * (nn - 26)
        * (nn - 14)
        * (nn - 8)
        * (nn - 5)
        * (nn + 1)
        * (nn + 2)
        * (nn - 2) ** 2
        * aa**8
    )

    assert all(r / expected in QQ for r in bad)
