"""
f4_evaluations.py

Export F4 closed-graph evaluation caches using the source/relation pipeline.

For t=10 and t=12 the evaluations are seeded directly (the pipeline does not
bootstrap these levels). For t=14 and t=16 the pipeline is run using the
seeded values as prior knowledge.

Note: compute_all_f4_evaluations() and write_all_f4_closed_evaluation_caches()
require trivalent-graphs/src on sys.path (for closed_graphs.closed_pipeline).
All other functions are importable without trivalent-graphs.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import graphviz
from sage.graphs.graph import Graph

PROJECT = "f4"


# ---------------------------------------------------------------------------
# Path helpers (inlined from export.paths to avoid trivalent-graphs dependency)
# ---------------------------------------------------------------------------


def _project_root(project: str) -> Path:
    # __file__ is projects/{project}/f4_evaluations.py; parents[1] = projects/
    return Path(__file__).resolve().parents[1] / project


def _evaluation_cache_dir(project: str) -> Path:
    return _project_root(project) / "cache" / "evaluations"


def _catalogue_cache_dir(project: str) -> Path:
    return _project_root(project) / "cache" / "closed"


def _raw_graph_cache_dir(project: str) -> Path:
    return _project_root(project) / "cache" / "raw" / "closed"


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
# Catalogue utilities
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
# Seeds
# ---------------------------------------------------------------------------


def seeded_closed_evaluations() -> dict:
    """
    Return hardcoded evaluations for t=10 and t=12.

    These values cannot be bootstrapped from the pipeline alone and must
    be supplied as prior knowledge.

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
# Cache I/O
# ---------------------------------------------------------------------------


def raw_closed_graph_items(t: int) -> list[dict]:
    path = _raw_graph_cache_dir(PROJECT) / f"closed_t{int(t)}.json"
    with path.open("r", encoding="utf-8") as f:
        doc = json.load(f)
    return doc["graphs"]


def write_f4_closed_evaluation_cache(t: int, closed_eval: dict) -> Path:
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


def write_all_f4_closed_evaluation_caches() -> list[Path]:
    """
    Compute all F4 evaluations and write one cache file per level.

    Requires trivalent-graphs/src on sys.path (delegates to
    compute_all_f4_evaluations).
    """
    closed_eval = compute_all_f4_evaluations()
    return [write_f4_closed_evaluation_cache(t, closed_eval) for t in [10, 12, 14, 16]]


# ---------------------------------------------------------------------------
# Catalogue cache (SVG + evaluation merged)
# ---------------------------------------------------------------------------


def write_f4_closed_catalogue_cache(t: int) -> Path:
    """Write the web-facing catalogue cache for F4 closed graphs at level t."""
    raw_path = _raw_graph_cache_dir(PROJECT) / f"closed_t{int(t)}.json"
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


def write_all_f4_closed_catalogue_caches() -> list[Path]:
    """Write web-facing catalogue caches for all F4 levels."""
    return [write_f4_closed_catalogue_cache(t) for t in [10, 12, 14, 16]]
