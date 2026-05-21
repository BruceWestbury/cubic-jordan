"""
theory.examples.f4_series
"""

from sage.all import QQ

from algebra.linear_comb import Graphs
from rewriting.relations import ReductionRule
 
from combinatorics.small_graphs import _lollipop_graph, _bigon_graph, _edge_graph, _triangle_graph, _vertex_graph, _square_graph, K, H, A, U, I, X
from theory.theory import Theory
from theory.presentation import Presentation

COEFF_RING = QQ['n']
(n,) = COEFF_RING.gens()

F4_series_free = Theory(
    name = "F4 series",
    base_ring = COEFF_RING,
    loop_value = n,
)

# -------------------------------------------------------------------
# Basic reduction rules
# -------------------------------------------------------------------

def lollipop():
    """
    Return the lollipop rule.
    """
    lhs = _lollipop_graph()
    graph_module = Graphs(F4_series_free, lhs.num_boundary())
    return ReductionRule(lhs, graph_module.zero())


def bigon():
    """
    Return the bigon rule.
    """
    lhs = _bigon_graph()
    graph_module = Graphs(F4_series_free,2)
    rhs = (n + 2) * graph_module.from_graph(_edge_graph())
    return ReductionRule(lhs, rhs)


def triangle():
    """
    Return the triangle rule.
    """
    lhs = _triangle_graph()
    graph_module = Graphs(F4_series_free, 3)
    rhs = ((-n + 2) / 2) * graph_module.from_graph(_vertex_graph())
    return ReductionRule(lhs, rhs)

def square_rule():
    """
    Return the square rule.

    Inserted by hand, as the square relation is not yet derived from the six-term relation.
    """
    lhs = _square_graph()
    graph_module = Graphs(F4_series_free, 4)
    aA = (6-n)/2
    aX = -(n+6)/2
    aU = (3*n+2)/2
    aI = (3*n+2)/2
    rhs = aA*graph_module.from_graph(A()) + aX*graph_module.from_graph(X()) + aU*graph_module.from_graph(U()) + aI*graph_module.from_graph(I())
    return ReductionRule(lhs, rhs)

# -------------------------------------------------------------------
# Basic relation elements
# -------------------------------------------------------------------

def six_term():
    """
    Return the six-term relation as an element of Graphs(F4_series_free, 4).
    """

    return Graphs(F4_series_free, 4).from_terms([
        (K(), 1),
        (H(), 1),
        (A(), 1),
        (U(), -2),
        (I(), -2),
        (X(), -2),
    ])

basic_rules = (
    lollipop(),
    bigon(),
    triangle(),
    square_rule(),
)

basic_relations = (
    six_term(),
)

F4_series_quotient = Presentation(
    theory = F4_series_free,
    relations=basic_relations,
    rules=basic_rules,
)

#------------------------------------------------------------------------------------
# New reduction rule of girth five
#------------------------------------------------------------------------------------

from combinatorics.dart_graph import DartGraph
from rewriting.apply_relation import FourValentSource, apply_relation_at_source
from rewriting.reduce import reduce_element_fully

def pentagon_site() -> DartGraph:
    return DartGraph(
        darts=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],
        vertices=[0,1,2,3,4,5],
        vertex_of={0:0, 1:5, 2:1, 3:3, 4:4, 5:0, 6:5, 7:2, 8:4, 9:0, 10:1, 11:1, 12:2, 13:2, 14:3, 15:3, 16:4},
        edge_of={0: None, 1: None, 2: None, 3: None, 4: None, 5: None, 6: None, 7: None, 8: None, 9:10, 10:9, 11:12, 12:11, 13:14, 14:13, 15:16, 16:15},
        boundary=tuple([0,1,2,3,4,5,6,7,8]),
    )

def pentagon_rule():
    """
    Return the girth-five reduction rule obtained from inserting the
    six-term relation into the pentagon site and reducing by the basic
    F4-series presentation.
    """
    source = FourValentSource(pentagon_site(), (5, 6, 7, 8))

    rel = apply_relation_at_source(
        six_term(),
        source,
        F4_series_free,
    )

    red = reduce_element_fully(rel, F4_series_quotient)
    coeffs = red.monomial_coefficients(copy=False)

    max_vertices = max(g.num_vertices() for g in coeffs)
    lhs_candidates = [
        g for g in coeffs
        if g.num_vertices() == max_vertices
    ]

    assert max_vertices == 7
    assert len(lhs_candidates) == 1

    lhs = lhs_candidates[0]
    assert coeffs[lhs] == 1

    M = red.parent()
    rhs = M.zero()

    for g, c in coeffs.items():
        if g != lhs:
            rhs += (-c) * M.from_graph(g)

    return ReductionRule(lhs, rhs)

pentagon_reduction_rule = pentagon_rule()

F4_series_pentagons = Presentation(
    theory=F4_series_free,
    relations=basic_relations,
    rules=basic_rules + (pentagon_reduction_rule,),
)

