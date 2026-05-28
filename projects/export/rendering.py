"""
projects.export.rendering

Rendering utilities for source graphs.
"""

from sage.all import Graph


def dot_to_svg(dot_source: str) -> str:
    import subprocess

    proc = subprocess.run(
        ["dot", "-Tsvg"],
        input=dot_source,
        text=True,
        capture_output=True,
        check=True,
    )
    return proc.stdout


def _special_vertex_graph_to_dot(G, special_degree: int) -> str:
    """
    Return DOT for a Sage graph with one vertex of degree *special_degree*.

    The special vertex is rendered as a filled box; all others as circles.
    """
    special_verts = [v for v in G.vertices() if G.degree(v) == special_degree]
    if len(special_verts) != 1:
        raise ValueError(
            f"expected exactly one {special_degree}-valent vertex, got {special_verts}"
        )
    special = special_verts[0]

    lines = ["graph {"]
    for v in sorted(G.vertices(), key=repr):
        if v == special:
            lines.append(f'  "{v}" [shape=box, style=filled, label=""];')
        else:
            lines.append(f'  "{v}" [shape=circle, label=""];')
    for u, v in sorted(
        (tuple(sorted((repr(a), repr(b)))) for a, b, *_ in G.edges(labels=False)),
    ):
        lines.append(f'  "{u}" -- "{v}";')
    lines.append("}")
    return "\n".join(lines)


def source_graph_to_dot(G) -> str:
    """
    Return DOT for an F4 source graph (one 4-valent vertex, rest trivalent).

    *G* is the Sage graph with the 4-valent vertex still present —
    the Sage graph stored in ``SourceRecord.display_graph``.
    """
    return _special_vertex_graph_to_dot(G, 4)


def e6_source_graph_to_dot(G) -> str:
    """
    Return DOT for an E6 source graph (one 5-valent vertex, one 2-valent).

    *G* is the Sage graph with the 5-valent vertex still present —
    the Sage graph stored in ``SourceRecord.display_graph``.
    """
    return _special_vertex_graph_to_dot(G, 5)


def source_graph_to_svg(G) -> str:
    """Return SVG for an F4 source graph (convenience wrapper)."""
    return dot_to_svg(source_graph_to_dot(G))


def e6_source_graph_to_svg(G) -> str:
    """Return SVG for an E6 source graph (convenience wrapper)."""
    return dot_to_svg(e6_source_graph_to_dot(G))
