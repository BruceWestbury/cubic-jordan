"""
f4_sources.py

Generation of F4 sources from closed trivalent graphs.

This module implements the *combinatorial input layer* for the F4 pipeline.
It produces pairs

    (graph, site)

where:
    - graph is a DartGraph with boundary,
    - site is an ordered 4-tuple of boundary darts.

Pipeline role
-------------
This is Layer 1:

    closed cubic graphs (Sage)
        → contract an edge
        → obtain a graph with one 4-valent vertex
        → convert to (DartGraph, site)
        → deduplicate

No algebraic rewriting or evaluation is performed here.

Interface
---------
The main public generator is:

    closed_sources(n)

which yields (graph, site) pairs suitable for insertion of the
six-term relation.

Design principles
-----------------
- Output is canonicalised to avoid duplicates.
- The representation is theory-agnostic: only (graph, site) is exposed.
- No dependency on rewriting rules or evaluation logic.

Extensibility
-------------
Other theories (e.g. E6) should provide analogous modules that yield
(graph, site) pairs with a different site size and interpretation.
"""

import subprocess
from sage.all import Graph
from combinatorics.dart_graph import DartGraph

    
def closed_cubic_girth5_graphs(n):
    """
    Yield connected simple cubic graphs on ``n`` vertices with girth ≥ 5.

    Parameters
    ----------
    n : int
        Number of vertices (must be even).

    Yields
    ------
    Sage Graph
        Connected, bridgeless cubic graphs with no cycles of length < 5.

    Notes
    -----
    Graphs are generated using geng and filtered for:
    - bridgelessness,
    - girth ≥ 5.
    """
    if n % 2:
        return
    cmd = ["geng", "-q", "-c", "-d3", "-D3", "-t", "-f", str(n)]
    proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line and not line.startswith(">"):
            G = Graph(line, format="graph6")
            if next(G.bridges(), None) is not None:
                continue
            if G.girth() < 5:
                continue
            yield G

def contract_to_four_valent(G, e):
    """
    Contract an edge of a cubic graph to produce a 4-valent vertex.

    Parameters
    ----------
    G : Sage Graph
        A cubic graph.
    e : tuple
        An edge (u, v) of G.

    Returns
    -------
    (H, w)
        H : Sage Graph
            Graph obtained by contracting e.
        w : vertex
            The new 4-valent vertex replacing u and v.

    Notes
    -----
    The endpoints of the edge are removed and replaced by a new vertex
    adjacent to the four former neighbours.
    """
    u, v = e[:2]
    Nu = [x for x in G.neighbors(u) if x != v]
    Nv = [x for x in G.neighbors(v) if x != u]

    H = Graph(G)
    w = ("X", u, v)   # any hashable fresh label
    H.add_vertex(w)

    for x in Nu + Nv:
        H.add_edge(w, x)

    H.delete_vertex(u)
    H.delete_vertex(v)

    return H, w

def four_valent_key(F):
    """
    Return a canonical key for a graph with a distinguished 4-valent vertex.

    Parameters
    ----------
    F : tuple
        Pair (G, v4) where G is a Sage graph and v4 is the 4-valent vertex.

    Returns
    -------
    Sage Graph
        A canonicalised version of G with v4 distinguished via partition.

    Notes
    -----
    This key is used to deduplicate graphs up to isomorphism preserving
    the distinguished vertex.
    """
    G, s = F
    other = [v for v in G.vertices(sort=False) if v != s]
    C = G.canonical_label(partition=[[s], other])
    return Graph(C, immutable=True)

def distinct_four_valent_graphs(closed_graphs):
    """
    Deduplicate four-valent graphs obtained by edge contraction.

    Parameters
    ----------
    closed_graphs : iterable
        Iterable of cubic Sage graphs.

    Yields
    ------
    (G, v4)
        Pair consisting of a Sage graph and its distinguished 4-valent vertex.

    Notes
    -----
    All edge contractions are considered, and duplicates are removed
    using canonical labelling with the 4-valent vertex fixed.
    """
    seen = set()
    for G in closed_graphs:
        for e in G.edges(labels=False):
            F = contract_to_four_valent(G, e)
            k = four_valent_key(F)
            if k in seen:
                continue
            seen.add(k)
            yield F

def four_valent_graph_to_source(F):
    """
    Convert a four-valent Sage graph to a (DartGraph, site) pair.

    Parameters
    ----------
    F : tuple
        Pair (G, v4) where G is a Sage graph with one 4-valent vertex.

    Returns
    -------
    (DartGraph, tuple)
        DG : DartGraph
            Graph obtained by removing the 4-valent vertex.
        site : tuple of int
            Ordered tuple of boundary darts corresponding to the
            neighbours of the removed vertex.

    Raises
    ------
    ValueError
        If the graph does not have exactly one 4-valent vertex or if
        other vertices are not trivalent.

    Notes
    -----
    The boundary of DG is exactly the site. The ordering is induced
    by sorting the neighbours of the removed vertex.
    """
    G, v4 = F

    verts = sorted(G.vertices(sort=False), key=repr)
    deg = {v: G.degree(v) for v in verts}

    if v4 not in deg:
        raise ValueError("special vertex is not a vertex of the graph")

    if deg[v4] != 4:
        raise ValueError("special vertex is not 4-valent")

    bad = [v for v in verts if v != v4 and deg[v] != 3]
    if bad:
        raise ValueError("all non-special vertices should be trivalent")

    internal = [v for v in verts if v != v4]
    relabel = {v: i for i, v in enumerate(internal)}

    darts = []
    vertices = list(relabel.values())
    vertex_of = {}
    edge_of = {}

    next_dart = 0
    seen_edges = set()
    site_by_neighbour = {}

    for u in internal:
        for w in G.neighbor_iterator(u):
            if w == v4:
                d = next_dart
                next_dart += 1
    
                darts.append(d)
                vertex_of[d] = relabel[u]
                edge_of[d] = None
                site_by_neighbour[u] = d
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

    site = tuple(
        site_by_neighbour[nbr]
        for nbr in sorted(G.neighbor_iterator(v4), key=repr)
    )

    if len(site) != 4:
        raise ValueError(f"expected 4 site darts, got {len(site)}")

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
    Generate F4 sources as (DartGraph, site) pairs.

    Parameters
    ----------
    n : int
        Number of vertices in the original cubic graph.

    Yields
    ------
    (DartGraph, tuple)
        Graph and ordered 4-tuple of boundary darts.

    Notes
    -----
    This is the main entry point for the F4 source layer. The output is
    ready for insertion of the six-term relation.
    """
    for F in distinct_four_valent_graphs(closed_cubic_girth5_graphs(n)):
        yield four_valent_graph_to_source(F)
