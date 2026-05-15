"""
algebra.symbolic
"""

from sympy import Symbol, factor, simplify

n_f4 = Symbol("n")
n_e6 = Symbol("n")


def canonical_expr(expr):
    return simplify(factor(expr))
