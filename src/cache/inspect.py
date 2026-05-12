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
    """Load a JSON cache whose top-level object is a list."""
    path = Path(path)

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise TypeError(f"Expected top-level JSON list in {path}")

    return data


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
    """
    Extract an adjacency dictionary from a cache item.

    Accepted shapes include:

        {"adjacency": {...}}
        {"adj": {...}}
        {"edges": [[0, 1], [1, 2], ...]}
        [[0, 1], [1, 2], ...]        # bare edge list
    """

    if isinstance(item, dict):
        if "adjacency" in item:
            return normalise_adjacency(item["adjacency"])

        if "adj" in item:
            return normalise_adjacency(item["adj"])

        if "edges" in item:
            return adjacency_from_edges(item["edges"])

    if isinstance(item, list):
        # Assume bare edge list.
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
