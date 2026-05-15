"""
algebra.linear_combinations
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from sympy import Expr, S, factor, simplify, sympify

GraphKey = str


def clean_coefficient(expr) -> Expr:
    """Return a simplified SymPy coefficient."""
    return factor(simplify(sympify(expr)))


@dataclass(frozen=True)
class LinearCombination:
    """Sparse linear combination of cached graphs.

    The keys are graph identifiers, usually canonical graph keys or cache ids.
    The values are SymPy coefficients.
    """

    terms: Mapping[GraphKey, Expr]

    def __post_init__(self):
        cleaned = {
            key: clean_coefficient(value)
            for key, value in self.terms.items()
            if clean_coefficient(value) != 0
        }
        object.__setattr__(self, "terms", dict(cleaned))

    @classmethod
    def zero(cls) -> "LinearCombination":
        return cls({})

    @classmethod
    def graph(cls, key: GraphKey, coefficient=S.One) -> "LinearCombination":
        return cls({key: coefficient})

    def is_zero(self) -> bool:
        return not self.terms

    def __add__(self, other: "LinearCombination") -> "LinearCombination":
        terms = dict(self.terms)

        for key, coeff in other.terms.items():
            terms[key] = terms.get(key, S.Zero) + coeff

        return LinearCombination(terms)

    def __neg__(self) -> "LinearCombination":
        return LinearCombination({key: -coeff for key, coeff in self.terms.items()})

    def __sub__(self, other: "LinearCombination") -> "LinearCombination":
        return self + (-other)

    def __rmul__(self, scalar) -> "LinearCombination":
        scalar = clean_coefficient(scalar)
        return LinearCombination(
            {key: scalar * coeff for key, coeff in self.terms.items()}
        )

    def substitute(
        self,
        key: GraphKey,
        replacement: "LinearCombination",
    ) -> "LinearCombination":
        """Substitute one graph key by a linear combination."""
        if key not in self.terms:
            return self

        coefficient = self.terms[key]
        remaining = {
            other_key: other_coeff
            for other_key, other_coeff in self.terms.items()
            if other_key != key
        }

        return LinearCombination(remaining) + coefficient * replacement

    def to_json(self) -> list[list[str]]:
        """Return JSON-friendly data as [[coefficient, graph_key], ...]."""
        return [[str(coeff), key] for key, coeff in sorted(self.terms.items())]

    @classmethod
    def from_json(cls, data: list[list[str]]) -> "LinearCombination":
        """Construct from [[coefficient, graph_key], ...]."""
        return cls({key: sympify(coeff) for coeff, key in data})
