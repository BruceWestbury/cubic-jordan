"""
e6_evaluations.py

Computes and writes E6 closed-graph catalogue caches directly in memory,
without intermediate raw or evaluation JSON files.

t=14 (Heawood graph) is the bootstrap level: its singleton relation is
resolved first, unlocking all subsequent levels.

Public API:
    compute_all_e6_evaluations() -> dict
    write_e6_closed_catalogue_cache(t, closed_eval=None) -> Path
    write_all_e6_closed_catalogue_caches(closed_eval=None) -> list[Path]
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import graphviz
from sage.graphs.graph import Graph

PROJECT = "e6"
PIPELINE_LEVELS = [14, 16, 18, 20, 22]
CACHE_LEVELS = [14, 16, 18, 20, 22]


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------


def _project_root(project: str) -> Path:
    # __file__ is projects/{project}/e6_evaluations.py; parents[1] = projects/
    return Path(__file__).resolve().parents[1] / project


def _catalogue_cache_dir(project: str) -> Path:
    return _project_root(project) / "cache" / "closed"


def _cache_document(
    *, format: str, version: int, project: str, records, metadata=None
) -> dict:
    doc = {
        "format": format,
        "version": version,
        "project": project,
        "records": records,
    }
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
# SVG / invariant helpers
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
# Pipeline
# ---------------------------------------------------------------------------


def compute_all_e6_evaluations() -> dict:
    """
    Run the level-by-level pipeline and return all known evaluations.

    t=14 (Heawood graph) gives a singleton relation directly and bootstraps
    the computation. Evaluations found at earlier levels are substituted into
    later ones.

    Requires trivalent-graphs/src on sys.path.
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
# Catalogue
# ---------------------------------------------------------------------------


def _e6_catalogue_records(t: int, closed_eval: dict) -> list[dict]:
    """
    Build catalogue records for all closed bipartite cubic girth>=6 graphs
    at level t.

    Generates graph data directly from e6_sources without reading any
    intermediate JSON files.
    """
    from projects.e6.e6_sources import closed_bipartite_cubic_graphs

    entries = []
    for G in closed_bipartite_cubic_graphs(t):
        g6 = G.graph6_string()
        if isinstance(g6, bytes):
            g6 = g6.decode()
        closed_key = G.canonical_label().graph6_string()
        if isinstance(closed_key, bytes):
            closed_key = closed_key.decode()
        entries.append((closed_key, g6, G))

    entries.sort(key=lambda x: x[0])

    records = []
    for i, (closed_key, g6, G) in enumerate(entries):
        item = {
            "id": f"e6_closed_bipartite_t{int(t)}_{i:03d}",
            "closed_key": closed_key,
            "graph6": g6,
        }
        evaluation = closed_eval.get(closed_key)
        record = _closed_catalogue_record(
            item=item,
            svg=_graph_to_svg(G),
            dot=_sage_to_dot(G),
            evaluation=(
                _format_polynomial(str(evaluation)) if evaluation is not None else None
            ),
            invariants=_graph_invariants(G),
        )
        records.append(record)

    return records


def write_e6_closed_catalogue_cache(t: int, closed_eval: dict | None = None) -> Path:
    """
    Write the E6 closed-graph catalogue cache for level t.

    Computes everything in memory; does not read from cache/raw or
    cache/evaluations.

    Parameters
    ----------
    t :
        Vertex count (14, 16, 18, 20, or 22).
    closed_eval :
        Pre-computed evaluation dict from compute_all_e6_evaluations().
        Computed internally if not provided.
    """
    if closed_eval is None:
        closed_eval = compute_all_e6_evaluations()

    records = _e6_catalogue_records(t, closed_eval)

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


def write_all_e6_closed_catalogue_caches(
    closed_eval: dict | None = None,
) -> list[Path]:
    """
    Write E6 catalogue caches for all levels.

    Evaluations are computed once and reused across all levels.
    """
    if closed_eval is None:
        closed_eval = compute_all_e6_evaluations()
    return [write_e6_closed_catalogue_cache(t, closed_eval) for t in CACHE_LEVELS]
