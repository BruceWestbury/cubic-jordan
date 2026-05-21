"""
e6_sources.py

Generation of E6 sources from closed bipartite trivalent graphs.

This module implements the combinatorial input layer for the E6 pipeline.
It produces pairs

    (graph, site)

where:
    - graph is a DartGraph with boundary,
    - site is an ordered 5-tuple of boundary darts,
    - site[0] is the distinguished boundary dart.

Construction
------------
Start with a closed bipartite cubic graph. Choose an interval

    a -- b -- c

of length two. Identify the two endpoints a and c. The resulting auxiliary
Sage graph has:
    - one vertex incident to four external site edges and to b,
    - one adjacent 2-valent vertex b,
    - all other vertices trivalent.

The two special vertices are then removed to form a DartGraph with five
boundary darts. The boundary dart coming from the 2-valent vertex is placed
first in the site tuple.

No algebraic rewriting or evaluation is performed here.
"""

import subprocess
from combinatorics.dart_graph import DartGraph

from sage.all import Graph


# ---------------------------------------------------------------------------
# Data structure
# ---------------------------------------------------------------------------




# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def closed_bipartite_cubic_graphs(n):
    """
    Yield connected simple bipartite cubic graphs on n vertices.

    Uses geng with:
      - degree exactly 3
      - connected
      - bipartite (-b)

    Then filters:
      - bridgeless
      - girth >= 6 (no 4-cycles)
    """
    if n % 2:
        return

    cmd = ["geng", "-q", "-c", "-d3", "-D3", "-b", "-f", str(n)]
    proc = subprocess.run(cmd, check=True, capture_output=True, text=True)

    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line or line.startswith(">"):
            continue

        G = Graph(line, format="graph6")

        if next(G.bridges(), None) is not None:
            continue

        if G.girth() < 6:
            continue

        yield G


# ---------------------------------------------------------------------------
# Interval → E6 auxiliary source.
# ---------------------------------------------------------------------------

def intervals_of_length_two(G):
    """
    Yield unordered intervals (a, b, c) with edges a-b and b-c.
    """
    for b in G.vertices(sort=False):
        nbrs = list(G.neighbor_iterator(b))
        for i, a in enumerate(nbrs):
            for c in nbrs[i + 1:]:
                yield a, b, c

def contract_interval_to_five_valent(G, a, b, c):
    """
    Identify the endpoints of an interval a-b-c.

    Parameters
    ----------
    G : Sage Graph
        A closed bipartite cubic graph.
    a, b, c
        Vertices forming an interval a-b-c.

    Returns
    -------
    Sage Graph
        Graph obtained by identifying a and c. The new vertex is incident
        to four external edges and to b; the middle vertex b becomes
        2-valent.
    """
    H = Graph(G)

    a_out = [u for u in G.neighbor_iterator(a) if u != b]
    c_out = [u for u in G.neighbor_iterator(c) if u != b]

    special = ("X5", a, c, b)

    H.delete_vertices([a, c])
    H.add_vertex(special)

    for u in a_out + c_out:
        H.add_edge(special, u)

    H.add_edge(special, b)

    return H


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

def five_valent_key(F):
    """
    Canonical key using Sage canonical labelling.

    No marking needed: degree pattern uniquely identifies the site.
    """
    G = Graph(F, loops=False, multiedges=False)
    k = G.canonical_label().graph6_string()
    if isinstance(k, bytes):
        k = k.decode()
    return k


def validate_five_valent_graph(G):
    """
    Check the auxiliary E6 source degree pattern.

    The expected pattern is:
        - one vertex of degree 5,
        - one adjacent vertex of degree 2,
        - all remaining vertices of degree 3.

    The degree-5 vertex consists of four external site edges plus the
    distinguished edge to the 2-valent vertex.
    """
    deg = dict(G.degree(labels=True))

    deg5 = [v for v, d in deg.items() if d == 5]
    deg2 = [v for v, d in deg.items() if d == 2]
    bad = [v for v, d in deg.items() if d not in (2, 3, 5)]

    if len(deg5) != 1:
        raise ValueError("expected exactly one 5-valent vertex")
    if len(deg2) != 1:
        raise ValueError("expected exactly one 2-valent vertex")
    if bad:
        raise ValueError(f"unexpected degrees at {bad}")

    if not G.has_edge(deg5[0], deg2[0]):
        raise ValueError("2-valent vertex must be adjacent to 5-valent vertex")


def distinct_five_valent_graphs(n):
    """
    Yield distinct auxiliary E6 source graphs.

    Each graph is obtained from a closed bipartite cubic graph by choosing
    an interval a-b-c and identifying a with c. The resulting graph has one
    degree-5 vertex, one adjacent degree-2 vertex, and all remaining vertices
    trivalent.
    """
    seen = set()

    for G in closed_bipartite_cubic_graphs(n):
        for a, b, c in intervals_of_length_two(G):
            F = contract_interval_to_five_valent(G, a, b, c)
            validate_five_valent_graph(F)

            k = five_valent_key(F)
            if k in seen:
                continue

            seen.add(k)
            yield F


# ---------------------------------------------------------------------------
# Public API (parallel to F4)
# ---------------------------------------------------------------------------

def five_valent_graph_to_source(F):
    """
    Convert an auxiliary E6 Sage graph to a (DartGraph, site) pair.

    Parameters
    ----------
    F : Sage Graph
        Graph with one degree-5 vertex, one adjacent degree-2 vertex,
        and all remaining vertices trivalent.

    Returns
    -------
    (DartGraph, tuple)
        DG : DartGraph
            Graph obtained by removing the degree-5 and degree-2 vertices.
        site : tuple[int, int, int, int, int]
            Ordered boundary tuple. The first entry is the distinguished
            boundary dart coming from the 2-valent vertex; the remaining
            four entries come from the four external edges incident to the
            degree-5 vertex.

    Notes
    -----
    This convention matches the E6 seven-term relation, whose boundary
    point 0 is distinguished and whose remaining four boundary points are
    symmetric.
    """
    G = F.graph if hasattr(F, "graph") else F

    verts = sorted(G.vertices(sort=False), key=repr)
    deg = {v: G.degree(v) for v in verts}

    deg5 = [v for v in verts if deg[v] == 5]
    deg2 = [v for v in verts if deg[v] == 2]

    if len(deg5) != 1:
        raise ValueError("expected exactly one 5-valent vertex")
    if len(deg2) != 1:
        raise ValueError("expected exactly one 2-valent vertex")

    v5 = deg5[0]
    v2 = deg2[0]

    if not G.has_edge(v5, v2):
        raise ValueError("2-valent vertex must be adjacent to 5-valent vertex")

    bad = [v for v in verts if v not in (v5, v2) and deg[v] != 3]
    if bad:
        raise ValueError("all non-special vertices should be trivalent")

    internal = [v for v in verts if v not in (v5, v2)]
    relabel = {v: i for i, v in enumerate(internal)}

    darts = []
    vertices = list(relabel.values())
    vertex_of = {}
    edge_of = {}

    next_dart = 0
    seen_edges = set()

    distinguished = None
    site_from_v5 = []

    for u in internal:
        for w in G.neighbor_iterator(u):
            if w == v2:
                d = next_dart
                next_dart += 1
                darts.append(d)
                vertex_of[d] = relabel[u]
                edge_of[d] = None
                distinguished = d
                continue

            if w == v5:
                d = next_dart
                next_dart += 1
                darts.append(d)
                vertex_of[d] = relabel[u]
                edge_of[d] = None
                site_from_v5.append((u, d))
                continue

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

    if distinguished is None:
        raise ValueError("did not find distinguished boundary dart")

    site_rest = tuple(d for _, d in sorted(site_from_v5, key=lambda x: repr(x[0])))

    if len(site_rest) != 4:
        raise ValueError(f"expected 4 non-distinguished site darts, got {len(site_rest)}")

    site = (distinguished,) + site_rest

    DG = DartGraph(
        darts=darts,
        vertices=vertices,
        boundary=site,
        vertex_of=vertex_of,
        edge_of=edge_of,
    )

    return DG, site

def closed_sources(n):
    """
    Generate E6 closed sources as (DartGraph, site) pairs.

    Parameters
    ----------
    n : int
        Number of vertices in the original closed bipartite cubic graph.

    Yields
    ------
    (DartGraph, tuple)
        Source graph and ordered 5-tuple of boundary darts, with site[0]
        distinguished.
    """
    for F in distinct_five_valent_graphs(n):
        yield five_valent_graph_to_source(F)