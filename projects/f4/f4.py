"""
examples/f4.py
"""

from sage.all import QQ

from algebra.linear_comb import Graphs
from rewriting.relations import ReductionRule
 
from combinatorics.dart_graph import _lollipop_graph, _bigon_graph, _edge_graph, _triangle_graph, _vertex_graph, _square_graph, K, H, A, U, I, X
from theory.theory import Theory
from theory.presentation import Presentation

COEFF_RING = QQ['aa']
aa, = COEFF_RING.gens()

F4_free = Theory(
    name = "F4",
    base_ring = COEFF_RING,
    loop_value = 26,
)

# -------------------------------------------------------------------
# Basic reduction rules
# -------------------------------------------------------------------

def lollipop():
    """
    Return the lollipop rule.
    """
    lhs = _lollipop_graph()
    M = Graphs(F4_free, lhs.num_boundary())
    return ReductionRule(lhs, M.zero())


def bigon():
    """
    Return the bigon rule.
    """
    lhs = _bigon_graph()
    M = Graphs(F4_free, 2)
    rhs = 14 * aa * M.from_graph(_edge_graph())
    return ReductionRule(lhs, rhs)


def triangle():
    """
    Return the triangle rule.
    """
    lhs = _triangle_graph()
    M = Graphs(F4_free, 3)
    rhs = -6 * aa * M.from_graph(_vertex_graph())
    return ReductionRule(lhs, rhs)

def square_rule():
    """
    Return the square rule.

    Inserted by hand, as the square relation is not yet derived from the six-term relation.
    """
    lhs = _square_graph()
    M = Graphs(F4_free, 4)
    aA = -5*aa
    aX = -4*aa*aa
    aU = 10*aa*aa
    aI = 10*aa*aa
    rhs = aA*M.from_graph(A()) + aX*M.from_graph(X()) + aU*M.from_graph(U()) + aI*M.from_graph(I())
    return ReductionRule(lhs, rhs)

# -------------------------------------------------------------------
# Basic relation elements
# -------------------------------------------------------------------

def six_term():
    """
    Return the six-term relation as an element of Graphs(F4_free, 4).
    """

    return Graphs(F4_free, 4).from_terms([
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

F4_quotient = Presentation(
    theory=F4_free,
    relations=basic_relations,
    rules=basic_rules,
)