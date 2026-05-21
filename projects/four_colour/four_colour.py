"""
examples/four_colour.py
"""

from sage.rings.rational_field import QQ
from theory.theory import Theory
from theory.presentation import Presentation

four_colour_free = Theory(
    name="Four colour",
    base_ring=QQ,
    loop_value=3,
)

four_colour_quotient = Presentation(
    theory=four_colour_free,
    rules=(),
    relations=(),
)