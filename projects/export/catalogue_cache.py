"""
export.catalogue_cache

Export web-facing catalogue caches for the public trivalent-graphs site.
"""

import json
from pathlib import Path

import graphviz
from sage.graphs.graph import Graph

from export.cache_wrappers import cache_document
from export.paths import (
    cache_root,
    catalogue_cache_dir,
    evaluation_cache_dir,
    raw_graph_cache_dir,
)


def write_closed_catalogue_cache(
    *,
    project: str,
    t: int,
    records: list[dict],
) -> Path:
    """
    Write a closed graph catalogue cache.

    Parameters
    ----------
    project:
        Project name such as "f4" or "e6".

    t:
        Number of trivalent vertices.

    records:
        Catalogue records ready for web presentation.
    """

    path = cache_root(project) / f"closed_t{int(t)}.json"

    doc = cache_document(
        format="closed_graph_catalogue",
        version=1,
        project=project,
        records=records,
        metadata={
            "t": t,
            "count": len(records),
        },
    )

    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(doc, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return path


def closed_catalogue_record(
    *,
    item: dict,
    svg: str,
    evaluation: str | None = None,
    dot: str | None = None,
    invariants: dict | None = None,
) -> dict:
    """
    Build one web-facing closed graph catalogue record.
    """
    return {
        "id": item["id"],
        "svg": svg,
        "dot": dot,
        "evaluation": evaluation,
        "invariants": invariants or {},
        "internal": {
            "closed_key": item["closed_key"],
            "graph6": item["graph6"],
        },
    }


def dot_to_svg(dot_source: str) -> str:
    src = graphviz.Source(dot_source)
    return src.pipe(format="svg").decode("utf-8")


def graph_to_svg(graph: Graph) -> str:
    """
    SVG renderer.
    """
    dot = sage_to_dot(graph)
    return dot_to_svg(dot)


def safe_value(fn, default=None):
    """
    Safely evaluate a graph invariant.

    If the computation raises an exception, return ``default``.
    """
    try:
        return fn()
    except Exception:
        return default


def json_value(x):
    """
    Convert Sage/Python values to JSON-friendly values.
    """
    if x is None:
        return None

    if isinstance(x, (str, bool, int, float)):
        return x

    try:
        return int(x)
    except (TypeError, ValueError):
        pass

    return str(x)


def graph_invariants(graph) -> dict:
    return {
        "automorphism_group_order": json_value(
            safe_value(lambda: graph.automorphism_group().order())
        ),
        "diameter": json_value(safe_value(lambda: graph.diameter())),
        "radius": json_value(safe_value(lambda: graph.radius())),
        "chromatic_number": json_value(safe_value(lambda: graph.chromatic_number())),
        "chromatic_polynomial": json_value(
            safe_value(lambda: graph.chromatic_polynomial())
        ),
        "is_hamiltonian": json_value(safe_value(lambda: graph.is_hamiltonian())),
        "num_spanning_trees": json_value(
            safe_value(lambda: graph.spanning_trees_count())
        ),
        "crossing_number": json_value(safe_value(lambda: graph.crossing_number())),
    }


def load_evaluation_lookup(path: Path) -> dict[str, str]:
    """
    Load an evaluation cache as a closed_key -> value string dictionary.

    If the cache does not exist, return an empty dictionary.
    """

    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as f:
        doc = json.load(f)

    lookup = {}

    for record in doc.get("records", []):
        key = record.get("closed_key") or record.get("key") or record.get("graph")
        value = record.get("value") or record.get("evaluation")

        if key is not None:
            lookup[key] = value

    return lookup


def export_closed_catalogue_for_t(
    *,
    project: str,
    t: int,
) -> Path:
    """
    Export a web-facing closed graph catalogue cache.
    """

    raw_path = raw_graph_cache_dir(project) / f"closed_t{int(t)}.json"

    with raw_path.open("r", encoding="utf-8") as f:
        raw_doc = json.load(f)

    evaluation_path = evaluation_cache_dir(project) / f"closed_t{int(t)}.json"

    evaluations = load_evaluation_lookup(evaluation_path)

    records = []

    for item in raw_doc["graphs"]:
        graph = Graph(item["graph6"])

        svg = graph_to_svg(graph)
        dot = sage_to_dot(graph)
        invariants = graph_invariants(graph)

        evaluation = evaluations.get(item["closed_key"])

        record = closed_catalogue_record(
            item=item,
            svg=svg,
            dot=dot,
            evaluation=evaluation,
            invariants=invariants,
        )

        records.append(record)

    doc = cache_document(
        format="closed_graph_catalogue",
        version=1,
        project=project,
        records=records,
        metadata={
            "t": t,
            "count": len(records),
        },
    )

    out_path = catalogue_cache_dir(project) / f"closed_t{int(t)}.json"

    out_path.parent.mkdir(parents=True, exist_ok=True)

    out_path.write_text(
        json.dumps(doc, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return out_path


def sage_to_dot(graph) -> str:
    """
    Return a simple DOT representation of a Sage graph.

    The output is deliberately plain so that it is stable and easy to
    inspect in the browser.
    """
    lines = ["graph {"]

    for v in sorted(graph.vertices()):
        lines.append(f"  {v};")

    for u, v in sorted(tuple(sorted(e[:2])) for e in graph.edges(labels=False)):
        lines.append(f"  {u} -- {v};")

    lines.append("}")

    return "\n".join(lines)


def source_graph_to_dot(graph) -> str:
    """
    Return DOT for a source graph with one four-valent vertex.

    The four-valent vertex is drawn as a box, to distinguish it from
    a crossing.
    """
    four_valent = [v for v in graph.vertices() if graph.degree(v) == 4]

    if len(four_valent) != 1:
        raise ValueError(f"expected one four-valent vertex, got {four_valent}")

    special = four_valent[0]

    lines = ["graph {"]

    for v in sorted(graph.vertices()):
        if v == special:
            lines.append(f'  {v} [shape=box, style=filled, label="{v}"];')
        else:
            lines.append(f'  {v} [shape=circle, label="{v}"];')

    for u, v in sorted(tuple(sorted(e[:2])) for e in graph.edges(labels=False)):
        lines.append(f"  {u} -- {v};")

    lines.append("}")
    return "\n".join(lines)


def source_graph_to_svg(graph) -> str:
    """
    Return SVG for a source graph with one four-valent vertex.
    """
    return dot_to_svg(source_graph_to_dot(graph))


def obstruction_source_record(
    *,
    source_graph,
    source_key: str,
    raw_obstruction,
    normalised_obstruction,
    substituted_relation=None,
    witness_id: str = "f4_t16_obstruction_witness",
) -> dict:
    """
    Build one web-facing obstruction witness record.
    """
    dot = source_graph_to_dot(source_graph)

    return {
        "id": witness_id,
        "t": 16,
        "source": {
            "key": source_key,
            "dot": dot,
            "svg": dot_to_svg(dot),
            "four_valent_vertex": [
                v for v in source_graph.vertices() if source_graph.degree(v) == 4
            ][0],
        },
        "relation": "six_term",
        "reduction_rules": "basic_rules",
        "substituted_relation": json_value(substituted_relation),
        "raw_obstruction": json_value(raw_obstruction),
        "normalised_obstruction": json_value(normalised_obstruction),
        "normalisation": "monic polynomial in n",
    }


def write_f4_obstruction_cache(records: list[dict]) -> Path:
    """
    Write the one-off F4 obstruction witness cache.
    """
    project = "f4"

    doc = cache_document(
        format="obstruction_witness",
        version=1,
        project=project,
        records=records,
        metadata={
            "t": 16,
            "count": len(records),
            "normalisation": "monic polynomial in n",
            "reduction_rules": "basic_rules",
        },
    )

    out_path = cache_root(project) / "obstruction.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    tmp_path = out_path.with_suffix(out_path.suffix + ".tmp")
    tmp_path.write_text(
        json.dumps(doc, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    tmp_path.replace(out_path)

    return out_path
