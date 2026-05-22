"""
e6_series.py
"""

from algebra.linear_comb import Graphs
from combinatorics.dart_graph import DartGraph
from combinatorics.small_graphs import (
    A,
    I,
    U,
    _bigon_graph,
    _edge_graph,
    _square_graph,
)
from rewriting.relations import ReductionRule
from sage.all import ZZ
from theory.presentation import Presentation
from theory.theory import Theory

COEFF_RING = ZZ["nn"]
(nn,) = COEFF_RING.gens()

E6_series_free = Theory(
    name="E6 series",
    base_ring=COEFF_RING,
    loop_value=nn,
)


def bigon():
    """
    Return the bigon rule.
    """
    lhs = _bigon_graph()
    graph_module = Graphs(E6_series_free, 2)
    rhs = 2 * (nn + 3) * graph_module.from_graph(_edge_graph())
    return ReductionRule(lhs, rhs)


def square_rule():
    """
    Return the square rule.

    Inserted by hand, as the square relation is not yet derived from the six-term relation.
    """
    lhs = _square_graph()
    graph_module = Graphs(E6_series_free, 4)
    aA = 3 - nn
    aU = 6 * (nn + 3)
    aI = 6 * (nn + 3)
    rhs = (
        aA * graph_module.from_graph(A())
        + aU * graph_module.from_graph(U())
        + aI * graph_module.from_graph(I())
    )
    return ReductionRule(lhs, rhs)


def _five_boundary_internal(boundary: tuple[int, int, int, int, int]) -> DartGraph:
    """
    Construct a DartGraph with two internal edges.

    Parameters
    ----------
    boundary: tuple[int, int, int, int, int]
        An ordering of the five boundary darts.

    Returns
    -------
    DartGraph
        A graph whose boundary consists of five darts and whose interior
        has two edges.
    """
    return DartGraph(
        darts=[0, 1, 2, 3, 4, 5, 6, 7, 8],
        vertices=[0, 1, 2],
        vertex_of={0: 0, 1: 0, 2: 0, 3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 2},
        edge_of={0: None, 1: 3, 2: 6, 3: 1, 4: None, 5: None, 6: 2, 7: None, 8: None},
        boundary=boundary,
    )


def Wa() -> DartGraph:
    """
    Return the 'DartGraph' `Wa`.

    One of the three b = 5 'DartGraph' with two internal edges.
    """
    return _five_boundary_internal(
        (
            0,
            4,
            5,
            7,
            8,
        )
    )


def Wx() -> DartGraph:
    """
    Return the 'DartGraph' `Wx`.

    One of the three b = 5 'DartGraph' with two internal edges.
    """
    return _five_boundary_internal(
        (
            0,
            4,
            7,
            5,
            8,
        )
    )


def Wk() -> DartGraph:
    """
    Return the 'DartGraph' `Wk`.

    One of the three b = 5 'DartGraph' with two internal edges.
    """
    return _five_boundary_internal(
        (
            0,
            4,
            7,
            8,
            5,
        )
    )


def _five_boundary_no_edge(boundary: tuple[int, int, int, int, int]) -> DartGraph:
    """
    Construct a DartGraph with no internal edge.

    Parameters
    ----------
    boundary: tuple[int, int, int, int, int]
        An ordering of the five boundary darts.

    Returns
    -------
    DartGraph
        A graph whose boundary consists of five darts and whose interior
        has no edge.
    """
    return DartGraph(
        darts=[0, 1, 2, 3, 4],
        vertices=[0, 1],
        vertex_of={0: 0, 1: 0, 2: 1, 3: 1, 4: 1},
        edge_of={0: None, 1: None, 2: None, 3: None, 4: None},
        boundary=boundary,
    )


def M1() -> DartGraph:
    """
    Return the 'DartGraph' `M1`.

    One of the three b = 5 'DartGraph' with no internal edge.
    """
    return _five_boundary_no_edge(
        (
            0,
            1,
            2,
            3,
            4,
        )
    )


def M2() -> DartGraph:
    """
    Return the 'DartGraph' `M2`.

    One of the three b = 5 'DartGraph' with no internal edge.
    """
    return _five_boundary_no_edge(
        (
            0,
            2,
            1,
            3,
            4,
        )
    )


def M3() -> DartGraph:
    """
    Return the 'DartGraph' `M3`.

    One of the three b = 5 'DartGraph' with no internal edge.
    """
    return _five_boundary_no_edge(
        (
            0,
            2,
            3,
            1,
            4,
        )
    )


def M4() -> DartGraph:
    """
    Return the 'DartGraph' `M4`.

    One of the three b = 5 'DartGraph' with no internal edge.
    """
    return _five_boundary_no_edge(
        (
            0,
            2,
            3,
            4,
            1,
        )
    )


def seven_term():
    """
    Return the seven-term relation as an element of Graphs(E6_series_free, 5).
    """

    return Graphs(E6_series_free, 5).from_terms(
        [
            (Wk(), 1),
            (Wx(), 1),
            (Wa(), 1),
            (M1(), -6),
            (M2(), -6),
            (M3(), -6),
            (M4(), -6),
        ]
    )


basic_rules = (
    bigon(),
    square_rule(),
)

basic_relations = (seven_term(),)

E6_series_quotient = Presentation(
    theory=E6_series_free,
    relations=basic_relations,
    rules=basic_rules,
)
