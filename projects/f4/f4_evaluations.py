"""
f4_evaluations.py

Computes and writes F4 closed-graph catalogue caches directly in memory,
without intermediate raw or evaluation JSON files.

Public API:
    seeded_closed_evaluations() -> dict
    compute_all_f4_evaluations() -> dict
    write_f4_closed_catalogue_cache(t, closed_eval=None) -> Path
    write_all_f4_closed_catalogue_caches(closed_eval=None) -> list[Path]
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import graphviz
from sage.graphs.graph import Graph

PROJECT = "f4"


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------


def _project_root(project: str) -> Path:
    # __file__ is projects/{project}/f4_evaluations.py; parents[1] = projects/
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

    Wraps all exponents in braces so that e.g. n^12 becomes n^{12}.
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
# Seeds
# ---------------------------------------------------------------------------


def seeded_closed_evaluations() -> dict:
    """
    Return hardcoded evaluations for t=10 and t=12.

    These values cannot be bootstrapped from the pipeline alone.
    Requires trivalent-graphs/src on sys.path (for f4_series polynomial ring).
    """
    from projects.f4.f4_series import F4_series_quotient

    R = F4_series_quotient.theory.base_ring
    (n,) = R.gens()

    closed_eval = {}

    # t = 10
    closed_eval["I@OZCMgs?"] = (
        n * (n - 2) * (n + 2) * 2**5 * (n**3 - 27 * n**2 + 54 * n + 72) / 128
    )

    # t = 12
    closed_eval["K?HHa`_aSKQC"] = (
        -n
        * (n - 2)
        * (n + 2)
        * 2**6
        * (n**4 - 38 * n**3 + 268 * n**2 - 192 * n - 464)
        / 512
    )

    closed_eval["KG?qPPO_[WQO"] = (
        n
        * (n - 2)
        * (n + 2)
        * 2**6
        * (5 * n**4 - 172 * n**3 + 1316 * n**2 - 864 * n - 2496)
        / 2048
    )

    return closed_eval


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


def compute_all_f4_evaluations() -> dict:
    """
    Return all known F4 closed-graph evaluations.

    Seeds t=10 and t=12 directly, then runs the pipeline at t=14 and t=16.
    Requires trivalent-graphs/src on sys.path.
    """
    from projects.common.closed_pipeline import (
        closed_partially_evaluated_relations,
        extract_singleton_evaluations,
    )
    from projects.f4.f4_series import F4_series_quotient
    from projects.f4.f4_sources import closed_sources

    _presentation = F4_series_quotient
    _sources = closed_sources

    closed_eval = seeded_closed_evaluations()
    for t in [14, 16]:
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


def _f4_catalogue_records(t: int, closed_eval: dict) -> list[dict]:
    """
    Build catalogue records for all closed cubic girth>=5 graphs at level t.

    Generates graph data directly from f4_sources without reading any
    intermediate JSON files.
    """
    from projects.f4.f4_sources import closed_cubic_girth5_graphs

    entries = []
    for G in closed_cubic_girth5_graphs(t):
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
            "id": f"f4_closed_t{int(t)}_{i:03d}",
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


def write_f4_closed_catalogue_cache(t: int, closed_eval: dict | None = None) -> Path:
    """
    Write the F4 closed-graph catalogue cache for level t.

    Computes everything in memory; does not read from cache/raw or
    cache/evaluations.

    Parameters
    ----------
    t :
        Vertex count (10, 12, 14, or 16).
    closed_eval :
        Pre-computed evaluation dict from compute_all_f4_evaluations().
        Computed internally if not provided.
    """
    if closed_eval is None:
        closed_eval = compute_all_f4_evaluations()

    records = _f4_catalogue_records(t, closed_eval)

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


def write_all_f4_closed_catalogue_caches(
    closed_eval: dict | None = None,
) -> list[Path]:
    """
    Write F4 catalogue caches for all levels.

    Evaluations are computed once and reused across all levels.
    """
    if closed_eval is None:
        closed_eval = compute_all_f4_evaluations()
    return [write_f4_closed_catalogue_cache(t, closed_eval) for t in [10, 12, 14, 16]]
