from dataclasses import dataclass

from combinatorics.dart_graph import DartGraph
from rewriting.apply_relation import apply_relation_at_source


@dataclass(frozen=True)
class FiveValentSource:
    graph: DartGraph
    site: tuple[int, int, int, int, int]


def five_valent_graph_to_source(F):
    """
    Convert an E6 Sage five-valent graph to a DartGraph source.

    The Sage graph has:
      - one 5-valent vertex s,
      - one adjacent 2-valent vertex m.

    Remove both s and m. The five dangling darts become the boundary.
    The first boundary dart is the one formerly incident to m.
    """
    G = F.graph

    deg = dict(G.degree(labels=True))
    s = next(v for v, d in deg.items() if d == 5)
    m = next(v for v, d in deg.items() if d == 2)

    if not G.has_edge(s, m):
        raise ValueError("2-valent vertex must be adjacent to 5-valent vertex")

    internal = [v for v in G.vertices(sort=False) if v not in (s, m)]
    relabel = {v: i for i, v in enumerate(internal)}

    darts = []
    vertices = list(relabel.values())
    vertex_of = {}
    edge_of = {}

    next_dart = 0
    seen_edges = set()

    middle_site = None
    special_sites = []

    for u in internal:
        for w in G.neighbor_iterator(u):
            if w == m:
                d = next_dart
                next_dart += 1

                darts.append(d)
                vertex_of[d] = relabel[u]
                edge_of[d] = None
                middle_site = d
                continue

            if w == s:
                d = next_dart
                next_dart += 1

                darts.append(d)
                vertex_of[d] = relabel[u]
                edge_of[d] = None
                special_sites.append(d)
                continue

            # Ordinary internal edge
            if w not in relabel:
                continue

            a = relabel[u]
            b = relabel[w]
            e = tuple(sorted((a, b)))

            if e in seen_edges:
                continue

            seen_edges.add(e)

            du = next_dart
            dv = next_dart + 1
            next_dart += 2

            darts.extend([du, dv])
            vertex_of[du] = a
            vertex_of[dv] = b
            edge_of[du] = dv
            edge_of[dv] = du

    if middle_site is None:
        raise ValueError("did not find distinguished middle boundary dart")

    if len(special_sites) != 4:
        raise ValueError(f"expected 4 special boundary darts, got {len(special_sites)}")

    site = (middle_site, *sorted(special_sites))

    DG = DartGraph(
        darts=darts,
        vertices=vertices,
        boundary=site,
        vertex_of=vertex_of,
        edge_of=edge_of,
    )

    return FiveValentSource(graph=DG, site=site)
