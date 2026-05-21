"""
theory.examples.f4_series_aa
"""

from sage.all import QQ

from algebra.linear_comb import Graphs
from rewriting.relations import ReductionRule
 
from combinatorics.small_graphs import _lollipop_graph, _bigon_graph, _edge_graph, _triangle_graph, _vertex_graph, _square_graph, K, H, A, U, I, X
from theory.theory import Theory
from theory.presentation import Presentation

COEFF_RING = QQ['aa', 'nn']
aa, nn = COEFF_RING.gens()

F4_series_free_aa = Theory(
    name = "F4 series_aa",
    base_ring = COEFF_RING,
    loop_value = nn,
)

# -------------------------------------------------------------------
# Basic reduction rules
# -------------------------------------------------------------------

def lollipop():
    """
    Return the lollipop rule.
    """
    lhs = _lollipop_graph()
    graph_module = Graphs(F4_series_free_aa, lhs.num_boundary())
    return ReductionRule(lhs, graph_module.zero())


def bigon():
    """
    Return the bigon rule.
    """
    lhs = _bigon_graph()
    graph_module = Graphs(F4_series_free_aa,2)
    rhs = ((nn + 2) * aa / 2) * graph_module.from_graph(_edge_graph())
    return ReductionRule(lhs, rhs)


def triangle():
    """
    Return the triangle rule.
    """
    lhs = _triangle_graph()
    graph_module = Graphs(F4_series_free_aa, 3)
    rhs = ((-nn + 2) * aa / 4) * graph_module.from_graph(_vertex_graph())
    return ReductionRule(lhs, rhs)

def square_rule():
    """
    Return the square rule.

    Inserted by hand, as the square relation is not yet derived from the six-term relation.
    """
    lhs = _square_graph()
    graph_module = Graphs(F4_series_free_aa, 4)
    aA = (6-nn)*aa/4
    aX = -(nn+6)*aa*aa/8
    aU = (3*nn+2)*aa*aa/8
    aI = (3*nn+2)*aa*aa/8
    rhs = aA*graph_module.from_graph(A()) + aX*graph_module.from_graph(X()) + aU*graph_module.from_graph(U()) + aI*graph_module.from_graph(I())
    return ReductionRule(lhs, rhs)

# -------------------------------------------------------------------
# Basic relation elements
# -------------------------------------------------------------------

def six_term():
    """
    Return the six-term relation as an element of Graphs(F4_series_free_aa, 4).
    """

    return Graphs(F4_series_free_aa, 4).from_terms([
        (K(), 1),
        (H(), 1),
        (A(), 1),
        (U(), -aa),
        (I(), -aa),
        (X(), -aa),
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

F4_series_quotient_aa = Presentation(
    theory = F4_series_free_aa,
    relations=basic_relations,
    rules=basic_rules,
))