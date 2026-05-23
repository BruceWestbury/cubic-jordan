"""
e6_evaluations.py

Export E6 closed-graph evaluation caches using the source/relation pipeline.

For each level t in [14, 16, 18, 20, 22], source sites are generated from all
closed bipartite cubic graphs, the seven-term relation is inserted at each
site, and the result is reduced using the basic E6 rules (bigon + square).
Relations that reduce to singleton evaluations determine graph values.
Running the pipeline across all five levels yields all known evaluations.

t=14 (Heawood graph) is the bootstrap level: its singleton relation is
resolved first, unlocking all subsequent levels.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import graphviz
from sage.graphs.graph import Graph

PROJECT = "e6"

# t=14 (Heawood graph) bootstraps the pipeline; pipeline runs at all five levels.
PIPELINE_LEVELS = [14, 16, 18, 20, 22]
CACHE_LEVELS = [14, 16, 18, 20, 22]


# ---------------------------------------------------------------------------
# Path / cache helpers (inlined to avoid trivalent-graphs dependency at import)
# ---------------------------------------------------------------------------


def _project_root(project: str) -> Path:
    # __file__ is projects/{project}/e6_evaluations.py; parents[1] = projects/
    return Path(__file__).resolve().parents[1] / project


def _cache_root(project: str) -> Path:
    return _project_root(project) / "cache"


def _evaluation_cache_dir(project: str) -> Path:
    return _cache_root(project) / "evaluations"


def _catalogue_cache_dir(project: str) -> Path:
    return _cache_root(project) / "closed"


def _cache_document(
    *, format: str, version: int, project: str, records, metadata=None
) -> dict:
    doc = {"format": format, "version": version, "project": project, "records": records}
    if metadata is not None:
        doc["metadata"] = metadata
    return doc


# ---------------------------------------------------------------------------
# Polynomial formatting
# ---------------------------------------------------------------------------

_EXPONENT_RE = re.compile(r"\^(\d+)")


def _format_polynomial(poly: str) -> str:
    """Normalise a Sage polynomial string for web display.

    - Replaces the internal variable name ``nn`` with ``n``.
    - Wraps all exponents in braces so ``n^12`` becomes ``n^{12}``.
    """
    s = poly.replace("nn", "n")
    s = _EXPONENT_RE.sub(r"^{\1}", s)
    return s


# ---------------------------------------------------------------------------
# Catalogue utilities (SVG / invariants / record building)
# ---------------------------------------------------------------------------


def _sage_to_dot(graph) -> str:
    lines = ["graph {"]
    for v in sorted(graph.vertices()):
        lines.append(f"  {v};")
    for u, v in sorted(tuple(sorted(e[:2])) for e in graph.edges(labels=False)):
        lines.append(f"  {u} -- {v};")
    lines.append("}")
    return "\n".join(lines)


def _dot_to_svg(dot_source: str) -> str:
    return graphviz.Source(dot_source).pipe(format="svg").decode("utf-8")


def _graph_to_svg(graph) -> str:
    return _dot_to_svg(_sage_to_dot(graph))


def _json_value(x):
    if x is None or isinstance(x, (str, bool, int, float)):
        return x
    try:
        return int(x)
    except (TypeError, ValueError):
        pass
    return str(x)


def _safe(fn, default=None):
    try:
        return fn()
    except Exception:
        return default


def _graph_invariants(graph) -> dict:
    return {
        "automorphism_group_order": _json_value(
            _safe(lambda: graph.automorphism_group().order())
        ),
        "diameter": _json_value(_safe(lambda: graph.diameter())),
        "radius": _json_value(_safe(lambda: graph.radius())),
        "chromatic_number": _json_value(_safe(lambda: graph.chromatic_number())),
        "is_hamiltonian": _json_value(_safe(lambda: graph.is_hamiltonian())),
        "num_spanning_trees": _json_value(_safe(lambda: graph.spanning_trees_count())),
    }


def _load_evaluation_lookup(path: Path) -> dict:
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


def _closed_catalogue_record(
    *,
    item: dict,
    svg: str,
    dot: str | None = None,
    evaluation: str | None = None,
    invariants: dict | None = None,
) -> dict:
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


# ---------------------------------------------------------------------------
# Raw graph cache
# ---------------------------------------------------------------------------


def _write_raw_closed_graph_cache(t: int) -> Path:
    """Generate and write the raw closed graph cache for level t.

    Used for t=14 (Heawood graph) which has no pre-existing cache file.
    """
    from e6_sources import closed_bipartite_cubic_graphs

    graphs = []
    for i, G in enumerate(closed_bipartite_cubic_graphs(t)):
        g6 = G.graph6_string()
        if isinstance(g6, bytes):
            g6 = g6.decode()
        closed_key = G.canonical_label().graph6_string()
        if isinstance(closed_key, bytes):
            closed_key = closed_key.decode()
        graphs.append(
            {
                "id": f"e6_closed_bipartite_t{int(t)}_{i:03d}",
                "closed_key": closed_key,
                "graph6": g6,
                "num_vertices": G.order(),
                "num_edges": G.size(),
            }
        )

    doc = {
        "format": "closed_graph_cache",
        "version": 1,
        "project": PROJECT,
        "name": f"closed_bipartite_t{int(t)}",
        "graph_type": "closed_bipartite_cubic_girth6",
        "count": len(graphs),
        "graphs": graphs,
    }

    path = cache_root(PROJECT) / "closed" / f"closed_bipartite_t{int(t)}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def raw_closed_graph_items(t: int) -> list[dict]:
    path = _cache_root(PROJECT) / "closed" / f"closed_bipartite_t{int(t)}.json"
    if not path.exists():
        _write_raw_closed_graph_cache(t)
    with path.open("r", encoding="utf-8") as f:
        doc = json.load(f)
    return doc["graphs"]


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


def compute_all_e6_evaluations() -> dict:
    """
    Run the level-by-level pipeline and return all known evaluations.

    t=14 (Heawood graph) gives a singleton relation directly and bootstraps
    the computation. Evaluations found at earlier levels are substituted into
    later ones.

    Returns
    -------
    dict
        Mapping graph_key -> polynomial value for every graph whose
        evaluation was determined by the pipeline.
    """
    from projects.common.closed_pipeline import (
        closed_partially_evaluated_relations,
        extract_singleton_evaluations,
    )
    from projects.e6.e6_series import E6_series_quotient
    from projects.e6.e6_sources import closed_sources

    _presentation = E6_series_quotient
    _sources = closed_sources

    closed_eval = {}
    for t in PIPELINE_LEVELS:
        collected = [
            d
            for d, _ in closed_partially_evaluated_relations(
                t, _presentation, _sources, closed_eval
            )
        ]
        new_evals = extract_singleton_evaluations(collected, {}, {})
        closed_eval.update(new_evals)
    return closed_eval


# ---------------------------------------------------------------------------
# Evaluation cache
# ---------------------------------------------------------------------------


def write_e6_closed_evaluation_cache(t: int, closed_eval: dict) -> Path:
    """Write the evaluation cache for closed bipartite cubic graphs at level t."""
    items = raw_closed_graph_items(t)
    records = []

    for item in items:
        key = item["closed_key"]
        graph = Graph(item["graph6"])
        svg = _graph_to_svg(graph)
        dot = _sage_to_dot(graph)
        invariants = _graph_invariants(graph)

        record = {
            "id": item["id"],
            "graph": key,
            "graph6": item["graph6"],
            "svg": svg,
            "dot": dot,
            "invariants": invariants,
            "method": "pipeline",
        }

        if key in closed_eval:
            record["status"] = "known"
            record["evaluation"] = _format_polynomial(str(closed_eval[key]))
        else:
            record["status"] = "unknown"
            record["evaluation"] = None

        records.append(record)

    records.sort(key=lambda r: r["graph"])

    doc = _cache_document(
        format="evaluation_cache",
        version=1,
        project=PROJECT,
        records=records,
        metadata={
            "t": int(t),
            "count": len(records),
            "known_count": sum(r["evaluation"] is not None for r in records),
            "unknown_count": sum(r["evaluation"] is None for r in records),
            "method": "pipeline",
        },
    )

    path = _evaluation_cache_dir(PROJECT) / f"closed_t{int(t)}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(doc, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def write_all_e6_closed_evaluation_caches() -> list[Path]:
    """Compute all E6 evaluations and write one cache file per level."""
    closed_eval = compute_all_e6_evaluations()
    return [write_e6_closed_evaluation_cache(t, closed_eval) for t in CACHE_LEVELS]


# ---------------------------------------------------------------------------
# Catalogue cache (SVG + evaluation merged)
# ---------------------------------------------------------------------------


def write_e6_closed_catalogue_cache(t: int) -> Path:
    """Write the web-facing catalogue cache for E6 closed graphs at level t."""
    raw_path = _cache_root(PROJECT) / "closed" / f"closed_bipartite_t{int(t)}.json"
    with raw_path.open("r", encoding="utf-8") as f:
        raw_doc = json.load(f)

    evaluation_path = _evaluation_cache_dir(PROJECT) / f"closed_t{int(t)}.json"
    evaluations = _load_evaluation_lookup(evaluation_path)

    records = []
    for item in raw_doc["graphs"]:
        graph = Graph(item["graph6"])
        svg = _graph_to_svg(graph)
        dot = _sage_to_dot(graph)
        invariants = _graph_invariants(graph)
        evaluation = evaluations.get(item["closed_key"])

        record = _closed_catalogue_record(
            item=item,
            svg=svg,
            dot=dot,
            evaluation=evaluation,
            invariants=invariants,
        )
        records.append(record)

    doc = _cache_document(
        format="closed_graph_catalogue",
        version=1,
        project=PROJECT,
        records=records,
        metadata={"t": int(t), "count": len(records)},
    )

    out_path = _catalogue_cache_dir(PROJECT) / f"closed_t{int(t)}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(doc, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return out_path


def write_all_e6_closed_catalogue_caches() -> list[Path]:
    """Write web-facing catalogue caches for all E6 levels."""
    return [write_e6_closed_catalogue_cache(t) for t in CACHE_LEVELS]
