"""
tests/test_pentagons_rule.py

Tests for the pentagons rule in the F4 series.
"""

import pytest
from algebra.linear_comb import Graphs
from combinatorics.graph_convert import from_sage_graph
from combinatorics.small_graphs import _empty_graph
from rewriting.reduce import reduce_element_fully

import projects.f4.f4_series as f4_series
from projects.f4.f4_sources import closed_cubic_girth5_graphs

THEORY = f4_series.F4_series_free
PRESENTATION = f4_series.F4_series_pentagons
M0 = Graphs(THEORY, 0)
EMPTY = M0.from_graph(_empty_graph())
n = THEORY.loop_value

EXPECTED = {
    (10, "I@OZCMgs?"): (
        1 / 4 * n**6 - 27 / 4 * n**5 + 25 / 2 * n**4 + 45 * n**3 - 54 * n**2 - 72 * n
    ),
    (12, "K?HHa`_aSKQC"): (
        -1 / 8 * n**7
        + 19 / 4 * n**6
        - 33 * n**5
        + 5 * n**4
        + 192 * n**3
        - 96 * n**2
        - 232 * n
    ),
    (12, "KG?qPPO_[WQO"): (
        5 / 32 * n**7
        - 43 / 8 * n**6
        + 81 / 2 * n**5
        - 11 / 2 * n**4
        - 485 / 2 * n**3
        + 108 * n**2
        + 312 * n
    ),
}


def from_closed_sage_graph(G):
    """Convert a closed Sage graph to a closed DartGraph."""
    return from_sage_graph(G, allow_closed_components=True)


@pytest.mark.parametrize("t", [10, 12])
def test_pentagons_rule_evaluates_closed_graphs_at_t_10_12(t):
    """Check the known pentagons-rule evaluations for t=10 and t=12."""
    for G in closed_cubic_girth5_graphs(t):
        g = from_closed_sage_graph(G)
        key = g.key()
        y = reduce_element_fully(M0.from_graph(g), PRESENTATION)

        if (t, key) in EXPECTED:
            assert y == EXPECTED[(t, key)] * EMPTY
