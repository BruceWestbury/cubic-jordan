"""
cache.inspect

Cache inspection utilities.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from visualisation.dot import graph_to_dot


def load_json_cache(path: str | Path) -> list[Any]:
    path = Path(path)

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        for key in ["graphs", "records", "sources", "items", "data"]:
            if key in data and isinstance(data[key], list):
                return data[key]

        raise TypeError(
            f"Expected a list-valued key such as graphs/sources/items/data in {path}; "
            f"found keys {list(data.keys())}"
        )

    raise TypeError(f"Expected JSON list or dict in {path}")


def cache_item(cache: list[Any], index: int) -> Any:
    """Return one item from a loaded cache, with a clearer error."""
    try:
        return cache[index]
    except IndexError as exc:
        raise IndexError(
            f"Cache index {index} out of range; cache has {len(cache)} items"
        ) from exc


def adjacency_from_edges(
    edges: list[list[Any]] | list[tuple[Any, Any]],
) -> dict[Any, list[Any]]:
    """Build an undirected adjacency dictionary from an edge list."""
    adjacency: dict[Any, list[Any]] = {}

    for edge in edges:
        if len(edge) != 2:
            raise ValueError(f"Expected edge of length 2, got {edge!r}")

        u, v = edge

        adjacency.setdefault(u, []).append(v)
        adjacency.setdefault(v, []).append(u)

    return {v: sorted(nbrs) for v, nbrs in adjacency.items()}


def adjacency_from_cache_item(item: Any) -> dict[Any, list[Any]]:
    if isinstance(item, dict):
        if "vertex_of" in item and "edge_of" in item and "vertices" in item:
            return adjacency_from_dart_graph_dict(item)

        if "graph" in item:
            return adjacency_from_cache_item(item["graph"])

        if "adjacency" in item:
            return normalise_adjacency(item["adjacency"])

        if "adj" in item:
            return normalise_adjacency(item["adj"])

        if "edges" in item:
            return adjacency_from_edges(item["edges"])

        if "graph6" in item:
            return adjacency_from_graph6(item["graph6"])

    if isinstance(item, list):
        return adjacency_from_edges(item)

    raise TypeError(f"Cannot extract adjacency from cache item: {item!r}")


def normalise_adjacency(raw: dict[Any, Any]) -> dict[Any, list[Any]]:
    """
    Normalise JSON adjacency.

    JSON object keys are strings, so this tries to convert integer-looking
    vertex labels back to ints.
    """

    def normalise_vertex(v: Any) -> Any:
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                return v
        return v

    adjacency: dict[Any, list[Any]] = {}

    for u, nbrs in raw.items():
        u = normalise_vertex(u)
        adjacency[u] = [normalise_vertex(v) for v in nbrs]

    return {v: sorted(nbrs) for v, nbrs in adjacency.items()}


def distinguished_vertices_from_degrees(
    adjacency: dict[Any, list[Any]],
) -> tuple[list[Any], list[Any]]:
    """
    Infer distinguished vertices from degrees.

    Returns:
        (four_valent, two_valent)
    """
    four_valent = []
    two_valent = []

    for v, nbrs in adjacency.items():
        degree = len(nbrs)

        if degree == 4:
            four_valent.append(v)
        elif degree == 2:
            two_valent.append(v)

    return sorted(four_valent), sorted(two_valent)


def closed_cache_item_to_dot(item: Any) -> str:
    """Convert one closed graph cache item to DOT."""
    adjacency = adjacency_from_cache_item(item)

    return graph_to_dot(adjacency)


def source_cache_item_to_dot(item: Any) -> str:
    """
    Convert one source cache item to DOT.

    Distinguished vertices are inferred by degree:
        F4 source: one 4-valent vertex.
        E6 source: one 4-valent vertex and one 2-valent vertex.
    """
    adjacency = adjacency_from_cache_item(item)
    four_valent, two_valent = distinguished_vertices_from_degrees(adjacency)

    return graph_to_dot(
        adjacency,
        four_valent=four_valent,
        two_valent=two_valent,
    )


def closed_cache_to_dot(path: str | Path, index: int) -> str:
    """Load a closed graph cache and convert one item to DOT."""
    cache = load_json_cache(path)
    item = cache_item(cache, index)

    return closed_cache_item_to_dot(item)


def source_cache_to_dot(path: str | Path, index: int) -> str:
    """Load a source cache and convert one item to DOT."""
    cache = load_json_cache(path)
    item = cache_item(cache, index)

    return source_cache_item_to_dot(item)


def adjacency_from_graph6(s: str) -> dict[int, list[int]]:
    """Decode small graph6 strings into an adjacency dict.

    This handles the ordinary graph6 format for n <= 62.
    """
    data = [ord(c) - 63 for c in s.strip()]

    if not data:
        raise ValueError("Empty graph6 string")

    n = data[0]
    if n >= 63:
        raise NotImplementedError("Only graph6 with n <= 62 is supported for now")

    bits = []
    for x in data[1:]:
        for k in range(5, -1, -1):
            bits.append((x >> k) & 1)

    adjacency = {i: [] for i in range(n)}

    bit_index = 0
    for j in range(1, n):
        for i in range(j):
            if bits[bit_index]:
                adjacency[i].append(j)
                adjacency[j].append(i)
            bit_index += 1

    return {v: sorted(nbrs) for v, nbrs in adjacency.items()}


def adjacency_from_dart_graph_dict(g: dict[str, Any]) -> dict[int, list[int]]:
    vertex_of = {int(d): v for d, v in g["vertex_of"].items()}
    edge_of = {int(d): (None if e is None else int(e)) for d, e in g["edge_of"].items()}

    adjacency = {v: [] for v in g["vertices"]}

    for d, e in edge_of.items():
        if e is None:
            continue

        if d > e:
            continue

        u = vertex_of[d]
        v = vertex_of[e]

        adjacency[u].append(v)
        adjacency[v].append(u)

    return {v: sorted(nbrs) for v, nbrs in adjacency.items()}
