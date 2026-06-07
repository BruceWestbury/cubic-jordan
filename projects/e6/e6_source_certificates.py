"""
projects.e6.e6_source_certificates

E6 source-certificate entry point.

This module handles the E6-specific first step of the source-reduction
pipeline:

1. Reconstruct the *closed* source graph from a ``FiveValentSource``
   (open DartGraph with 5 boundary darts) by adding the missing five-valent
   vertex and its five partner darts.

2. Build the first-step replacement certificates corresponding to the
   E6 seven-term relation at the five-valent vertex.

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

The schema is identical to the F4 schema; only the theory-specific content
of the first step differs.
"""

from __future__ import annotations

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

# ---------------------------------------------------------------------------
# Closed source graph reconstruction  (FiveValentSource → raw closed graph)
# ---------------------------------------------------------------------------


def _closed_source_from_open_e6(source):
    """
    Reconstruct the closed source graph from a ``FiveValentSource``.

    A ``FiveValentSource`` stores an *open* DartGraph (5 boundary darts)
    plus a ``site`` tuple.  This function adds the missing five-valent vertex
    and its five partner darts, then relabels everything to consecutive
    integers so the result can be serialised as a ``ClosedDartGraph``.

    Parameters
    ----------
    source : FiveValentSource
        ``source.graph``: open DartGraph whose boundary darts are the site.
        ``source.site``:  5-tuple of boundary dart labels (in order).

    Returns
    -------
    darts : list[int]           consecutive 0 … N-1
    vertices : list[int]        consecutive 0 … M-1
    vertex_of : dict[int, int]
    edge_of : dict[int, int]
    v5_darts : list[int]        new labels of the 5 darts *at* the five-valent
                                vertex; ``v5_darts[i]`` is paired with the
                                relabelled ``source.site[i]``.
    site_darts : list[int]      new labels of ``source.site`` darts.
    dart_rl : dict[int, int]    old label → new label
    vert_rl : dict[int, int]    old label → new label
    """
    og = source.graph
    v5_old = (max(og.vertices) + 1) if og.vertices else 0
    nd_base = (max(og.darts) + 1) if og.darts else 0

    site_to_nd = {sd: nd_base + i for i, sd in enumerate(source.site)}

    all_darts_old = list(og.darts) + list(site_to_nd.values())
    all_verts_old = list(og.vertices) + [v5_old]

    vof_old = dict(og.vertex_of)
    for nd in site_to_nd.values():
        vof_old[nd] = v5_old

    eof_old = dict(og.edge_of)  # boundary darts have edge_of = None
    for sd, nd in site_to_nd.items():
        eof_old[sd] = nd  # pair site dart ↔ v5 dart
        eof_old[nd] = sd

    dart_rl = {d: i for i, d in enumerate(sorted(all_darts_old))}
    vert_rl = {v: i for i, v in enumerate(sorted(all_verts_old))}

    darts = list(range(len(all_darts_old)))
    vertices = list(range(len(all_verts_old)))
    vertex_of = {dart_rl[d]: vert_rl[vof_old[d]] for d in all_darts_old}
    edge_of = {dart_rl[d]: dart_rl[eof_old[d]] for d in all_darts_old}

    v5_darts = [dart_rl[site_to_nd[sd]] for sd in source.site]
    site_darts = [dart_rl[sd] for sd in source.site]

    return darts, vertices, vertex_of, edge_of, v5_darts, site_darts, dart_rl, vert_rl


# ---------------------------------------------------------------------------
# Serialisation helpers for non-standard closed graphs
# ---------------------------------------------------------------------------


def _source_graph_to_json_e6(darts, vertices, vertex_of, edge_of):
    """
    Serialise a closed graph that may contain a five-valent vertex.

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


def _canonical_bijection_no_validate_e6(darts, vertices, vertex_of, edge_of):
    """
    Canonical bijections for a closed graph, bypassing DartGraph validation.

    Constructs the same dart-incidence auxiliary graph as
    ``canonical_closed_dart_graph``, but works directly on raw data so that
    graphs containing a five-valent vertex (rejected by DartGraph) are
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
# First-step expander (seven-term relation at the five-valent vertex)
# ---------------------------------------------------------------------------


def _expand_first_step_e6(
    src_darts,
    src_verts,
    src_vof,
    src_eof,
    src_json,
    src_dart_bij,
    src_vert_bij,
    v5_darts,
    relation,
    theory,
):
    """
    Expand the E6 seven-term relation at the five-valent vertex.

    Parameters
    ----------
    src_darts, src_verts, src_vof, src_eof
        Raw data for the closed source graph (consecutive labels).
    src_json : dict
        Pre-serialised JSON for the closed source graph.
    src_dart_bij, src_vert_bij : dict[int, int]
        Canonical bijections for the closed source graph.
    v5_darts : list[int]
        Labels (in the closed source graph) of the five darts at the
        five-valent vertex, in the order they correspond to relation
        boundary positions.
    relation
        The E6 seven-term relation: an element of ``Graphs(theory, 0)``
        whose terms are the seven RHS graphs.
    theory
        The E6 theory object (provides ``loop_value`` and ``base_ring``).

    Returns
    -------
    (after_element, replacement_certs_json, occurrence_json)
        ``after_element``          : linear combination after expanding.
        ``replacement_certs_json`` : list of replacement certificate dicts.
        ``occurrence_json``        : dart map recording how the five-valent
                                     vertex pattern maps into the canonical
                                     source-graph labels.
    """
    parent = Graphs(theory, 0)
    after = parent.zero()
    certs = []

    lhs_bnd = list(range(len(v5_darts)))
    occ_map = {i: v5_darts[i] for i in range(len(v5_darts))}

    before_occ = RawOccurrence(
        {i: src_dart_bij[v5_darts[i]] for i in range(len(v5_darts))}
    )

    for rhs_graph, rhs_coeff in relation.monomial_coefficients(copy=False).items():
        after_ns, ds, vs, kept_d, kept_v = _surgery_raw(
            src_darts,
            src_verts,
            dict(src_vof),
            dict(src_eof),
            occ_map,
            rhs_graph,
            lhs_bnd,
        )

        after_occ = RawOccurrence({d: d + ds for d in rhs_graph.darts})
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
        "dart_map": {str(i): src_dart_bij[v5_darts[i]] for i in range(len(v5_darts))}
    }
    return after, certs, occ_json


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def make_e6_source_certificate_v2(
    source,
    relation,
    presentation,
    *,
    relation_name="e6_seven_term",
    max_steps=10_000,
):
    """
    Generate a V2 source-reduction certificate for an E6 source.

    Parameters
    ----------
    source : FiveValentSource
        Open DartGraph with 5 boundary darts plus a ``site`` 5-tuple.
    relation
        The E6 seven-term relation: an element of ``Graphs(theory, 0)``.
    presentation
        The E6 presentation whose rules drive subsequent reduction.
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
    its five-valent vertex) as a single term with coefficient 1.  This
    graph is not a valid ``DartGraph`` but is accepted by the Lean checker
    as a ``ClosedGraph``.

    The first step applies ``relation`` at the five-valent vertex.
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
        v5_darts,
        _site_darts,
        _dart_rl,
        _vert_rl,
    ) = _closed_source_from_open_e6(source)

    src_json = _source_graph_to_json_e6(src_darts, src_verts, src_vof, src_eof)

    src_dart_bij, src_vert_bij = _canonical_bijection_no_validate_e6(
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

    # 2. First step: expand the seven-term relation at the five-valent vertex.
    first_after, first_certs, first_occ_json = _expand_first_step_e6(
        src_darts,
        src_verts,
        src_vof,
        src_eof,
        src_json,
        src_dart_bij,
        src_vert_bij,
        v5_darts,
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
