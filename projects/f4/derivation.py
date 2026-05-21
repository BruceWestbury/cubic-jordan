from algebra.linear_comb import Graphs
from combinatorics.dart_graph import DartGraph
from combinatorics.small_graphs import H, I, K, U, X
from rewriting.apply_relation import FourValentSource, apply_relation_at_source
from theory.examples.f4_series import F4_series_free

M4 = Graphs(F4_series_free, 4)
idempotent = M4.from_terms([(I(), 2), (U(), -2), (X(), -6), (H(), 2), (K(), 1)])

grapha = DartGraph(
    darts=[0, 1, 2, 3, 4, 5, 6, 7, 8],
    vertices=[0, 1, 2, 3],
    vertex_of={0: 0, 1: 0, 2: 1, 3: 1, 4: 2, 5: 2, 6: 3, 7: 3, 8: 3},
    edge_of={
        0: None,
        1: None,
        2: None,
        3: None,
        4: None,
        5: None,
        6: None,
        7: None,
        8: None,
    },
    boundary=[0, 1, 2, 3, 4, 5, 6, 7, 8],
)

D_xy = FourValentSource(grapha, (1, 3, 8, 5))
Dx_y = FourValentSource(grapha, (1, 3, 5, 8))

graphb = DartGraph(
    darts=[0, 1, 2, 3, 4, 5, 6, 7, 8],
    vertices=[0, 1, 2, 3],
    vertex_of={0: 0, 1: 0, 2: 1, 3: 1, 4: 3, 5: 2, 6: 2, 7: 3, 8: 3},
    edge_of={
        0: None,
        1: None,
        2: None,
        3: None,
        4: None,
        5: None,
        6: None,
        7: None,
        8: None,
    },
    boundary=[0, 1, 2, 3, 4, 5, 6, 7, 8],
)

x_Dy = FourValentSource(graphb, (1, 3, 6, 8))

eqn = (
    apply_relation_at_source(idempotent, x_Dy, theory=F4_series_free)
    + apply_relation_at_source(idempotent, Dx_y, theory=F4_series_free)
    - apply_relation_at_source(idempotent, D_xy, theory=F4_series_free)
)
