"""
tests.test_linear_combinations

Obsolete: LinearCombination was an early prototype class that no longer
exists.  The current API uses algebra.linear_comb.Graphs.
"""

import pytest

pytest.skip(
    "LinearCombination class is obsolete; current API uses algebra.linear_comb.Graphs",
    allow_module_level=True,
)


def test_linear_combination_arithmetic():
    n = symbols("n")

    x = LinearCombination.graph("g1", n)
    y = LinearCombination.graph("g1", 2) + LinearCombination.graph("g2", 3)

    assert (x + y).terms["g1"] == n + 2
    assert (x + y).terms["g2"] == 3


def test_substitution():
    n = symbols("n")

    expr = LinearCombination.graph("g1", 2) + LinearCombination.graph("g2", 1)
    replacement = LinearCombination.graph("g3", n)

    result = expr.substitute("g1", replacement)

    assert result.terms == {
        "g2": 1,
        "g3": 2 * n,
    }


def test_json_round_trip():
    n = symbols("n")

    expr = LinearCombination.graph("g1", n - 2)
    assert LinearCombination.from_json(expr.to_json()) == expr
