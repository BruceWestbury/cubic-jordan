"""
evaluation.py

Generation, reduction, and evaluation of relations between closed graphs.

This module implements the *relation + evaluation layer* of the pipeline.
It takes source graphs, inserts local relations, reduces them, and then
extracts and checks closed graph evaluations.

Pipeline role
-------------
This spans Layers 2 and 3:

    (graph, site) sources
        → insert local relation
        → reduce using rewriting rules
        → collect relations (dict form)
        → substitute known evaluations (lower t)
        → extract singleton evaluations
        → iterate to obtain all evaluations at level t
        → substitute all evaluations back
        → check scalar consistency (polynomial obstruction)

Main responsibilities
---------------------
- Generate relations from sources via local substitution.
- Reduce relations using rewriting rules.
- Represent relations as dictionaries:
      {graph_key: coefficient, "?": scalar}
- Substitute known evaluations from previous levels.
- Detect singleton relations:
      coeff * G + scalar = 0  ⇒  G = -scalar / coeff
- Iteratively extract all graph evaluations at a given level.
- Maintain a dictionary:
      closed_eval: graph_key → polynomial value
- Fully evaluate relations once all graph values are known.
- Detect nonzero scalar remainders (consistency conditions).

Key abstractions
----------------
- Relation dictionary:
    Sparse representation of a linear relation between closed graphs.

- Closed evaluation:
    Map from graph keys to elements of the base ring.

- Polynomial obstruction:
    Nonzero scalar remaining after full substitution.

Design notes
------------
- Source generation is external (f4_sources, e6_sources).
- This module handles insertion of relations and reduction.
- Evaluation proceeds level by level (e.g. t = 10, 12, 14, 16).
- Iterative extraction is essential: newly found values simplify
  remaining relations.

Extensibility
-------------
This module is theory-agnostic provided:
- a source generator yielding (graph, site),
- a local relation (in presentation.relations),
- rewriting rules (presentation.rules).
"""

from collections import namedtuple

from algebra.linear_comb import Graphs
from combinatorics.graph_convert import dart_graph_to_sage_graph
from rewriting.apply_relation import apply_relation_at_source
from rewriting.reduce import (
    _replace_by_graph_with_boundary,
    _replace_site_by_graph,
    reduce_element_fully,
)
from sage.graphs.graph import Graph


def closed_sage_key_from_term(term):
    """
    Convert a closed DartGraph term to a canonical Sage graph key.

    Parameters
    ----------
    term : DartGraph or GraphWithLoops
        Closed graph term.

    Returns
    -------
    (key, G) : tuple
        key : str
            Canonical graph6 string.
        G : Sage Graph
            Representative graph.

    Notes
    -----
    - Boundary must be empty.
    - Loop contributions should already be absorbed into scalars.
    """
    # term may be GraphWithLoops or DartGraph
    if hasattr(term, "graph"):
        if term.loop_count != 0:
            raise ValueError("loop_count should be handled as scalar before this stage")
        DG = term.graph
    else:
        DG = term

    if DG.num_boundary() != 0:
        raise ValueError("expected a closed graph")

    G0 = dart_graph_to_sage_graph(DG)[0]
    G = Graph(G0, loops=False, multiedges=False)
    k = G.canonical_label().graph6_string()
    if isinstance(k, bytes):
        k = k.decode()
    return k, G


def sage_collect_relation(rel):
    """
    Convert a linear combination of graphs into dictionary form.

    Parameters
    ----------
    rel : element
        Linear combination in Graphs(0).

    Returns
    -------
    (d, reps) : tuple
        d : dict
            graph_key → coefficient
        reps : dict
            graph_key → Sage graph representative
    """
    coeffs = rel.monomial_coefficients(copy=False)

    out = {}
    reps = {}

    for term, coeff in coeffs.items():
        k, G = closed_sage_key_from_term(term)

        out[k] = out.get(k, 0) + coeff
        reps.setdefault(k, G)

    out = {k: c for k, c in out.items() if c != 0}
    return out, reps


def closed_relations(n, presentation, sources):
    """
    Generate raw relations by inserting the local relation at each site.

    Parameters
    ----------
    n : int
        Level.
    presentation : Presentation
        Contains the defining local relation and theory.
    sources : callable
        Function n ↦ iterable of (graph, site).

    Yields
    ------
    element
        Linear combinations of graphs obtained by substitution.

    Notes
    -----
    This is the entry point from combinatorics into algebra:
        (graph, site) → relation element.
    """
    relation = presentation.relations[0]
    theory = presentation.theory
    G0 = Graphs(theory, 0)

    for graph, site in sources(n):
        out = G0.zero()

        for rhs_graph, coeff in relation.monomial_coefficients(copy=False).items():
            result = _replace_site_by_graph(graph, site, rhs_graph)

            g = result.graph
            loop_factor = theory.loop_value**result.loop_count

            out += G0.from_graph(g, coeff * loop_factor)

        yield out


def closed_relations_from_source_records(n, presentation, source_records):
    """
    Generate raw relations from provenance-aware source records.

    Yields
    ------
    (SourceRecord, element)
        The provenance-aware source record and the raw relation obtained
        by inserting the local relation at its site.
    """
    relation = presentation.relations[0]
    theory = presentation.theory
    G0 = Graphs(theory, 0)

    for source_record in source_records(n):
        graph = source_record.graph
        site = source_record.site

        out = G0.zero()

        for rhs_graph, coeff in relation.monomial_coefficients(copy=False).items():
            result = _replace_site_by_graph(graph, site, rhs_graph)

            g = result.graph
            loop_factor = theory.loop_value**result.loop_count

            out += G0.from_graph(g, coeff * loop_factor)

        yield source_record, out


def closed_locally_reduced_relations_from_source_records(
    n,
    presentation,
    source_records,
):
    """
    Generate locally reduced relations from provenance-aware source records.
    """
    for source_record, rel in closed_relations_from_source_records(
        n,
        presentation,
        source_records,
    ):
        yield source_record, reduce_element_fully(rel, presentation)


def closed_partially_evaluated_relations_from_source_records(
    n,
    presentation,
    source_records,
    closed_eval,
):
    """
    Generate partially evaluated relations from provenance-aware source records.
    """
    for source_record, rel in closed_locally_reduced_relations_from_source_records(
        n,
        presentation,
        source_records,
    ):
        d, reps = evaluate_known_closed_relation(rel, closed_eval)
        yield d, reps, source_record


def evaluate_known_closed_relation(rel, closed_eval):
    """
    Substitute known closed graph evaluations into a relation.

    Parameters
    ----------
    rel : element
        A reduced relation between closed graphs (typically a linear
        combination in the Graphs(0) module).
    closed_eval : dict
        Mapping graph_key → value in the base ring.

    Returns
    -------
    (d, reps) : tuple
        d : dict
            Relation dictionary of the form
                {graph_key: coefficient, "?": scalar}
            where all known graph values have been substituted.
        reps : dict
            Mapping graph_key → Sage graph representative.

    Notes
    -----
    This is a thin wrapper around `evaluate_known_closed_relation_dict`,
    converting a linear combination into dictionary form first.
    """
    d, reps = sage_collect_relation(rel)
    return evaluate_known_closed_relation_dict(d, reps, closed_eval)


def closed_locally_reduced_relations(n, presentation, sources):
    """
    Generate locally reduced relations at level n.

    Parameters
    ----------
    n : int
        Level.
    presentation : Presentation
        Local rewriting rules.
    sources : callable
        Source generator (e.g. f4_sources.closed_sources).

    Yields
    ------
    element
        Reduced linear combinations of closed graphs.

    Notes
    -----
    Each relation is obtained by:
        source → insert local relation → reduce fully.
    """
    for rel in closed_relations(n, presentation, sources):
        yield reduce_element_fully(rel, presentation)


def extract_singleton_evaluations(collected, reps, known):
    """
    Iteratively extract graph evaluations from singleton relations.

    Parameters
    ----------
    collected : list of dict
        Relations in dictionary form.
    reps : dict
        (Unused; present for compatibility with earlier interface.)
    known : dict
        Existing mapping graph_key → value.

    Returns
    -------
    dict
        Updated mapping including all values deduced from singleton relations.

    Notes
    -----
    A singleton relation has the form:
        coeff * G + scalar = 0
    and determines:
        G = -scalar / coeff

    Extraction is iterative: newly found values are immediately used
    to simplify other relations.
    """
    changed = True

    while changed:
        changed = False

        for d in collected:
            scalar = d.get("?", 0)
            unknowns = {}

            for k, coeff in d.items():
                if k == "?":
                    continue
                if k in known:
                    scalar += coeff * known[k]
                else:
                    unknowns[k] = coeff

            if len(unknowns) == 1:
                k, coeff = next(iter(unknowns.items()))
                value = -scalar / coeff

                if k not in known:
                    known[k] = value
                    changed = True

    return known


def evaluate_known_closed_relation_dict(d, reps, closed_eval):
    """
    Substitute known evaluations into a relation dictionary.

    Parameters
    ----------
    d : dict
        Relation dictionary {graph_key: coefficient, "?": scalar}.
    reps : dict
        Mapping graph_key → graph representative.
    closed_eval : dict
        Mapping graph_key → value in the base ring.

    Returns
    -------
    (out, new_reps) : tuple
        out : dict
            Updated relation dictionary with known graphs eliminated.
        new_reps : dict
            Representatives restricted to remaining graph keys.

    Notes
    -----
    - Closed graphs of order 0 contribute directly to the scalar term.
    - Known graph values are substituted into the scalar.
    - Unknown graphs are retained.
    """
    out = {}
    new_reps = {}

    for k, coeff in d.items():
        G = reps[k]

        if G.order() == 0:
            out["?"] = out.get("?", 0) + coeff
            new_reps["?"] = G

        elif k in closed_eval:
            out["?"] = out.get("?", 0) + coeff * closed_eval[k]

        else:
            out[k] = out.get(k, 0) + coeff
            new_reps[k] = G

    out = {k: c for k, c in out.items() if c != 0}
    return out, new_reps


def singleton_evaluation_from_relation(d):
    """
    Extract a graph evaluation from a singleton relation.

    Parameters
    ----------
    d : dict
        Relation dictionary.

    Returns
    -------
    (graph_key, value) or None

    Notes
    -----
    If the relation has exactly one graph term:
        coeff * G + scalar = 0
    then:
        G = -scalar / coeff

    If d has exactly one non-empty graph key plus '?', return (key, value).
    Relation convention: coeff*G + scalar*[] = 0.
    """
    scalar = d.get("?", 0)
    graph_terms = [(k, c) for k, c in d.items() if k != "?"]

    if len(graph_terms) != 1:
        return None

    k, coeff = graph_terms[0]
    return k, -scalar / coeff


def find_evaluation_conflicts(collected):
    """
    Detect conflicting evaluations from singleton relations.

    Parameters
    ----------
    collected : list of dict
        Relations in dictionary form.

    Returns
    -------
    (values, conflicts) : tuple
        values : dict
            graph_key → (relation_index, value)
        conflicts : list
            Entries of the form
                (graph_key, i1, i2, value1, value2, difference)

    Notes
    -----
    A conflict occurs when two singleton relations assign different
    values to the same graph.
    """
    values = {}
    conflicts = []

    for i, d in enumerate(collected):
        item = singleton_evaluation_from_relation(d)
        if item is None:
            continue

        k, value = item

        if k in values:
            old_i, old_value = values[k]
            diff = value - old_value

            if diff != 0:
                conflicts.append((k, old_i, i, old_value, value, diff))
        else:
            values[k] = (i, value)

    return values, conflicts


def unresolved_relations(collected, known):
    """
    Identify relations that are not fully resolved.

    Parameters
    ----------
    collected : list of dict
        Relations in dictionary form.
    known : dict
        Known graph evaluations.

    Returns
    -------
    list
        List of pairs (unknowns, scalar), where:
            unknowns : dict of remaining graph terms
            scalar : accumulated scalar term

    Notes
    -----
    A relation is unresolved if it still contains unknown graph terms
    or has a nonzero scalar after substitution.
    """
    out = []
    for d in collected:
        scalar = d.get("?", 0)
        unknowns = {}

        for k, coeff in d.items():
            if k == "?":
                continue
            if k in known:
                scalar += coeff * known[k]
            else:
                unknowns[k] = coeff

        if unknowns or scalar != 0:
            out.append((unknowns, scalar))

    return out


def fully_evaluate_relation_dict(d, known):
    """
    Fully evaluate a relation using known graph values.

    Parameters
    ----------
    d : dict
        Relation dictionary.
    known : dict
        Mapping graph_key → value.

    Returns
    -------
    (scalar, unknowns) : tuple
        scalar : value in the base ring
        unknowns : dict of remaining graph terms

    Notes
    -----
    If `unknowns` is empty, the relation reduces to a scalar condition:
        scalar = 0
    which gives a consistency constraint (polynomial obstruction).
    """
    scalar = d.get("?", 0)

    unknowns = {}
    for k, coeff in d.items():
        if k == "?":
            continue
        if k in known:
            scalar += coeff * known[k]
        else:
            unknowns[k] = coeff

    return scalar, unknowns


def closed_partially_evaluated_relations(n, presentation, sources, closed_eval):
    """
    Generate reduced relations with known evaluations substituted.

    Parameters
    ----------
    n : int
        Level.
    presentation : Presentation
        Local reduction rules.
    sources : callable
        Source generator.
    closed_eval : dict
        Known graph evaluations from previous levels.

    Yields
    ------
    (d, reps) : tuple
        Relation dictionary and representatives after substitution.

    Notes
    -----
    Pipeline stage:
        sources → relations → reduction → partial evaluation
    """
    for rel in closed_locally_reduced_relations(n, presentation, sources):
        d, reps = evaluate_known_closed_relation(rel, closed_eval)
        yield d, reps


def closed_partially_evaluated_source_records(n, presentation, closed_eval):
    from closed_graphs.local_relations import closed_relation_from_source
    from export.provenance_sources import f4_source_records
    from rewriting.reduce import reduce_element_fully

    from projects.common.closed_pipeline import evaluate_known_closed_relation

    for source_record in f4_source_records(n):
        source = (source_record.graph, source_record.site)
        rel = closed_relation_from_source(source, presentation)
        reduced = reduce_element_fully(rel, presentation)
        d, reps = evaluate_known_closed_relation(reduced, closed_eval)

        yield d, reps, source_record
