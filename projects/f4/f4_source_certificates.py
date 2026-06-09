"""
projects.f4.f4_source_certificates

F4 source-certificate entry point.

This module handles the F4-specific first step of the source-reduction
pipeline:

1. Reconstruct the *closed* source graph from a ``FourValentSource``
   (open DartGraph with 4 boundary darts) by adding the missing four-valent
   vertex and its four partner darts.

2. Build the first-step replacement certificates corresponding to the
   F4 six-term relation at the four-valent vertex.

3. Return the linear combination that results from expanding the relation.

4. Hand off to the generic ``reduce_with_certificate_v2`` for all subsequent
   reduction steps.

JSON schema
-----------
The produced certificate matches the V2 schema::

    {
      "format":  "source_reduction_certificate",
      "version": 2,
      "initial": <LinearCombination>,    # single term, coefficient 1
      "steps":   [<ReductionStep>, ...]  # first step + subsequent steps
    }

No schema changes from the original ``make_f4_source_certificate_v2``; this is
a pure module-boundary refactor.
"""

from __future__ import annotations

import json
from pathlib import Path

from algebra.linear_comb import Graphs
from certificates.json_linear_combination import linear_combination_to_json
from certificates.json_polynomial import polynomial_to_json
from certificates.replace import ComplementIsomorphism, RawOccurrence
from certificates.source_certificate import (
    _one_replacement_cert_json,
    _surgery_raw,
    reduce_with_certificate_v2,
)
from sage.graphs.graph import Graph as _SageGraph

from projects.export.provenance_sources import f4_source_records

# ---------------------------------------------------------------------------
# Closed source graph reconstruction  (FourValentSource → raw closed graph)
# ---------------------------------------------------------------------------


def _closed_source_from_open(source):
    """
    Reconstruct the closed source graph from a ``FourValentSource``.

    A ``FourValentSource`` stores an *open* DartGraph (4 boundary darts)
    plus a ``site`` tuple.  This function adds the missing four-valent vertex
    and its four partner darts, then relabels everything to consecutive
    integers so the result can be serialised as a ``ClosedDartGraph``.

    Parameters
    ----------
    source : FourValentSource
        ``source.graph``: open DartGraph whose boundary darts are the site.
        ``source.site``:  4-tuple of boundary dart labels (in order).

    Returns
    -------
    darts : list[int]           consecutive 0 … N-1
    vertices : list[int]        consecutive 0 … M-1
    vertex_of : dict[int, int]
    edge_of : dict[int, int]
    v4_darts : list[int]        new labels of the 4 darts *at* the four-valent
                                vertex; ``v4_darts[i]`` is paired with the
                                relabelled ``source.site[i]``.
    site_darts : list[int]      new labels of ``source.site`` darts.
    dart_rl : dict[int, int]    old label → new label
    vert_rl : dict[int, int]    old label → new label
    """
    og = source.graph
    v4_old = (max(og.vertices) + 1) if og.vertices else 0
    nd_base = (max(og.darts) + 1) if og.darts else 0

    site_to_nd = {sd: nd_base + i for i, sd in enumerate(source.site)}

    all_darts_old = list(og.darts) + list(site_to_nd.values())
    all_verts_old = list(og.vertices) + [v4_old]

    vof_old = dict(og.vertex_of)
    for nd in site_to_nd.values():
        vof_old[nd] = v4_old

    eof_old = dict(og.edge_of)  # boundary darts have edge_of = None
    for sd, nd in site_to_nd.items():
        eof_old[sd] = nd  # pair site dart ↔ v4 dart
        eof_old[nd] = sd

    dart_rl = {d: i for i, d in enumerate(sorted(all_darts_old))}
    vert_rl = {v: i for i, v in enumerate(sorted(all_verts_old))}

    darts = list(range(len(all_darts_old)))
    vertices = list(range(len(all_verts_old)))
    vertex_of = {dart_rl[d]: vert_rl[vof_old[d]] for d in all_darts_old}
    edge_of = {dart_rl[d]: dart_rl[eof_old[d]] for d in all_darts_old}

    v4_darts = [dart_rl[site_to_nd[sd]] for sd in source.site]
    site_darts = [dart_rl[sd] for sd in source.site]

    return darts, vertices, vertex_of, edge_of, v4_darts, site_darts, dart_rl, vert_rl


# ---------------------------------------------------------------------------
# Serialisation helpers for non-standard closed graphs
# ---------------------------------------------------------------------------


def _source_graph_to_json(darts, vertices, vertex_of, edge_of):
    """
    Serialise a closed graph that may contain a four-valent vertex.

    Bypasses DartGraph validation, which rejects vertices of degree other
    than 2 or 3.  Requires consecutive 0 … N-1 labels.
    """
    n = len(darts)
    m = len(vertices)
    return {
        "format": "closed_dart_graph",
        "version": 2,
        "num_darts": n,
        "num_vertices": m,
        "vertex_of": [int(vertex_of[d]) for d in range(n)],
        "partner": [int(edge_of[d]) for d in range(n)],
    }


def _canonical_bijection_no_validate(darts, vertices, vertex_of, edge_of):
    """
    Canonical bijections for a closed graph, bypassing DartGraph validation.

    Constructs the same dart-incidence auxiliary graph as
    ``canonical_closed_dart_graph``, but works directly on raw data so that
    graphs containing a four-valent vertex (rejected by DartGraph) are
    accepted.

    Returns
    -------
    dart_bij : dict[int, int]   old label → canonical 0-based label
    vert_bij : dict[int, int]   old label → canonical 0-based label
    """
    d_nodes = [("d", d) for d in darts]
    v_nodes = [("v", v) for v in vertices]

    aux = _SageGraph(multiedges=False, loops=False)
    aux.add_vertices(d_nodes + v_nodes)
    for d in darts:
        aux.add_edge(("d", d), ("v", vertex_of[d]))
    for d in darts:
        e = edge_of[d]
        if e is not None and d < e:
            aux.add_edge(("d", d), ("d", e))

    partition = [p for p in (d_nodes, v_nodes) if p]
    _, cert = aux.canonical_label(partition=partition, certificate=True)

    sorted_d = sorted(darts, key=lambda d: cert[("d", d)])
    sorted_v = sorted(vertices, key=lambda v: cert[("v", v)])

    dart_bij = {old: new for new, old in enumerate(sorted_d)}
    vert_bij = {old: new for new, old in enumerate(sorted_v)}
    return dart_bij, vert_bij


# ---------------------------------------------------------------------------
# First-step expander (six-term relation at the four-valent vertex)
# ---------------------------------------------------------------------------


def _expand_first_step(
    src_darts,
    src_verts,
    src_vof,
    src_eof,
    src_json,
    src_dart_bij,
    src_vert_bij,
    v4_darts,
    relation,
    theory,
):
    """
    Expand the F4 six-term relation at the four-valent vertex.

    Parameters
    ----------
    src_darts, src_verts, src_vof, src_eof
        Raw data for the closed source graph (consecutive labels).
    src_json : dict
        Pre-serialised JSON for the closed source graph.
    src_dart_bij, src_vert_bij : dict[int, int]
        Canonical bijections for the closed source graph.
    v4_darts : list[int]
        Labels (in the closed source graph) of the four darts at the
        four-valent vertex, in the order they correspond to relation
        boundary positions.
    relation
        The F4 six-term relation: an element of ``Graphs(theory, 0)``
        whose terms are the six RHS graphs.
    theory
        The F4 theory object (provides ``loop_value`` and ``base_ring``).

    Returns
    -------
    (after_element, replacement_certs_json, occurrence_json)
        ``after_element``          : linear combination after expanding.
        ``replacement_certs_json`` : list of replacement certificate dicts.
        ``occurrence_json``        : dart map recording how the four-valent
                                     vertex pattern maps into the canonical
                                     source-graph labels.
    """
    parent = Graphs(theory, 0)
    after = parent.zero()
    certs = []

    lhs_bnd = list(range(len(v4_darts)))
    occ_map = {i: v4_darts[i] for i in range(len(v4_darts))}

    before_occ = RawOccurrence(
        {i: src_dart_bij[v4_darts[i]] for i in range(len(v4_darts))}
    )

    for rhs_graph, rhs_coeff in relation.monomial_coefficients(copy=False).items():
        after_ns, ds, vs, kept_d, kept_v, rhs_dart_image = _surgery_raw(
            src_darts,
            src_verts,
            dict(src_vof),
            dict(src_eof),
            occ_map,
            rhs_graph,
            lhs_bnd,
        )

        after_occ = RawOccurrence(rhs_dart_image)
        comp_iso = ComplementIsomorphism(
            dart_map={src_dart_bij[d]: d for d in kept_d},
            vertex_map={src_vert_bij[v]: v for v in kept_v},
        )

        cert_json, after_canonical, actual_coeff = _one_replacement_cert_json(
            src_json,
            before_occ,
            after_ns,
            after_occ,
            comp_iso,
            rhs_coeff,
            loop_value=theory.loop_value,
        )
        certs.append(cert_json)
        after += parent.from_graph(after_canonical, actual_coeff)

    occ_json = {
        "dart_map": {str(i): src_dart_bij[v4_darts[i]] for i in range(len(v4_darts))}
    }
    return after, certs, occ_json


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def make_f4_source_certificate_v2(
    source,
    relation,
    presentation,
    *,
    relation_name="f4_six_term",
    max_steps=10_000,
):
    """
    Generate a V2 source-reduction certificate for an F4 source.

    Parameters
    ----------
    source : FourValentSource
        Open DartGraph with 4 boundary darts plus a ``site`` 4-tuple.
    relation
        The F4 six-term relation: an element of ``Graphs(theory, 0)``.
    presentation
        The F4 presentation whose rules drive subsequent reduction.
    relation_name : str
        Label stored in the first step's ``"rule"`` field.
    max_steps : int
        Safety bound on total reduction steps after the first step.

    Returns
    -------
    dict
        JSON-serialisable V2 certificate::

            {
              "format":  "source_reduction_certificate",
              "version": 2,
              "initial": <LinearCombination>,
              "steps":   [<ReductionStep>, ...]
            }

    Notes
    -----
    The initial linear combination contains the closed source graph (with
    its four-valent vertex) as a single term with coefficient 1.  This
    graph is not a valid ``DartGraph`` but is accepted by the Lean checker
    as a ``ClosedGraph``.

    The first step applies ``relation`` at the four-valent vertex.
    All subsequent steps apply reduction rules from ``presentation``.
    Every step carries full ``replacement_certificates``.
    """
    theory = presentation.theory
    one = theory.base_ring(1)

    # 1. Build the closed source graph (relabelled to 0 … N-1).
    (
        src_darts,
        src_verts,
        src_vof,
        src_eof,
        v4_darts,
        _site_darts,
        _dart_rl,
        _vert_rl,
    ) = _closed_source_from_open(source)

    src_json = _source_graph_to_json(src_darts, src_verts, src_vof, src_eof)

    src_dart_bij, src_vert_bij = _canonical_bijection_no_validate(
        src_darts, src_verts, src_vof, src_eof
    )

    initial_lc = {
        "terms": [
            {
                "coefficient": polynomial_to_json(one),
                "graph": src_json,
            }
        ]
    }

    # 2. First step: expand the six-term relation at the four-valent vertex.
    first_after, first_certs, first_occ_json = _expand_first_step(
        src_darts,
        src_verts,
        src_vof,
        src_eof,
        src_json,
        src_dart_bij,
        src_vert_bij,
        v4_darts,
        relation,
        theory,
    )

    first_step = {
        "term_index": 0,
        "rule": relation_name,
        "occurrence": first_occ_json,
        "replacement_certificates": first_certs,
        "after": linear_combination_to_json(first_after),
    }

    # 3. Reduce the expanded linear combination using presentation rules.
    _final, remaining_steps = reduce_with_certificate_v2(
        first_after, presentation, max_steps=max_steps
    )

    return {
        "format": "source_reduction_certificate",
        "version": 2,
        "initial": initial_lc,
        "steps": [first_step] + remaining_steps,
    }


# ---------------------------------------------------------------------------
# V2 source-reduction certificates
# ---------------------------------------------------------------------------


def write_f4_source_certificate(source_record, out_path: Path) -> Path:
    """
    Write a V2 source-reduction certificate for one F4 source.

    Delegates entirely to ``make_f4_source_certificate_v2`` from
    ``cubic-jordan/projects/f4/``.  The F4 source has a
    4-valent vertex; the generalised V2 machinery handles any site width.

    Parameters
    ----------
    source_record :
        A ``SourceRecord`` from ``f4_source_records(t)``.
        Must have ``.graph`` (DartGraph, 4 boundary darts) and
        ``.site`` (4-tuple of boundary dart labels).
    out_path :
        Destination file.

    Returns
    -------
    Path
        The path of the written JSON file.
    """
    from projects.f4.f4_series import F4_series_quotient, six_term
    from projects.f4.f4_source_certificates import make_f4_source_certificate_v2

    cert = make_f4_source_certificate_v2(
        source_record,
        six_term(),
        F4_series_quotient,
        relation_name="f4_six_term",
    )
    cert["source_key"] = source_record.source_key

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(cert, indent=2) + "\n",
        encoding="utf-8",
    )
    return out_path


def write_f4_source_certificates_at_t(
    t: int,
    out_dir: Path | None = None,
) -> list[Path]:
    """
    Write one V2 source-reduction certificate per source at level *t*.

    Files are named ``sources_{i:04d}.json`` (0-indexed), matching the
    convention used by ``projects/f4/certificates/generate.py``.

    Parameters
    ----------
    t :
        Vertex count (10, 12, 14 or 16).
    out_dir :
        Directory to write into.  Defaults to
        ``projects/f4/certificates/t{t}/``.

    Returns
    -------
    list[Path]
        Paths of all written certificate files.
    """
    if out_dir is None:
        out_dir = Path(__file__).resolve().parent / "certificates" / f"t{t}"
    out_dir = Path(out_dir)

    paths = []
    for i, sr in enumerate(f4_source_records(t)):
        path = write_f4_source_certificate(sr, out_dir / f"sources_{i:04d}.json")
        print(f"  t={t} [{i:04d}] {sr.source_key!r} → {path.name}")
        paths.append(path)
    return paths
