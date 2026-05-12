"""
visualisation.plot

Functions for visualising graphs in DOT format.

"""

from collections import defaultdict


def edges_from_adjacency(adj):
    """
    Convert adjacency dict into sorted undirected edge list.

    Input:
        {u: [v1, v2, ...], ...}

    Output:
        [(u,v), ...] with u < v
    """
    edges = set()

    for u, nbrs in adj.items():
        for v in nbrs:
            if u <= v:
                edges.add((u, v))
            else:
                edges.add((v, u))

    return sorted(edges)


def graph_to_dot(
    adjacency,
    *,
    four_valent=(),
    two_valent=(),
    graph_name="G",
):
    """
    Convert a graph into DOT format.

    Parameters
    ----------
    adjacency:
        dict vertex -> iterable of neighbours

    four_valent:
        iterable of distinguished 4-valent vertices

    two_valent:
        iterable of distinguished 2-valent vertices

    Returns
    -------
    str
        DOT source code
    """

    four_valent = set(four_valent)
    two_valent = set(two_valent)

    lines = []

    lines.append(f"graph {graph_name} {{")
    lines.append("  node [shape=circle];")

    vertices = sorted(adjacency)

    # vertices
    for v in vertices:
        attrs = []

        if v in four_valent:
            attrs.append("shape=doublecircle")
            attrs.append("style=filled")
            attrs.append("fillcolor=lightgray")

        elif v in two_valent:
            attrs.append("shape=box")
            attrs.append("style=filled")
            attrs.append("fillcolor=lightblue")

        attr_string = ""

        if attrs:
            attr_string = " [" + ", ".join(attrs) + "]"

        lines.append(f'  "{v}"{attr_string};')

    # edges
    for u, v in edges_from_adjacency(adjacency):
        lines.append(f'  "{u}" -- "{v}";')

    lines.append("}")

    return "\n".join(lines)


def closed_graph_to_dot(g):
    adjacency = g.to_adjacency_dict()
    return graph_to_dot(adjacency)


def source_graph_to_dot(
    g,
    *,
    four_valent,
    two_valent=(),
):
    adjacency = g.to_adjacency_dict()

    return graph_to_dot(
        adjacency,
        four_valent=four_valent,
        two_valent=two_valent,
    )
