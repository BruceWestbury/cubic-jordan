"""
e6_witnesses.py

E6 obstruction witnesses and V2 source-reduction certificates.

Two public APIs are provided:

``e6_t22_witnesses(closed_eval)``
    Compute obstruction witnesses at t=22 (pure mathematical result;
    no certificates are written).

``write_e6_source_certificate(source_record, out_path)``
    Write a V2 source-reduction certificate for one E6 source using the
    same V2 machinery as F4.

``write_e6_source_certificates_at_t(t, out_dir, closed_eval)``
    Write one V2 certificate per source at level *t*.

The old V1 ``e6_witness_cache`` format is no longer written.

Obstruction polynomial (degree 12, Thurston 2004):
    (nn-27)(nn-15)(nn-9)(nn-6)(nn-3)^2(nn-1)nn^2(nn+1)(nn+3)^2
"""

from __future__ import annotations

import json
from pathlib import Path

from sage.all import QQ

from projects.export.provenance_sources import e6_source_records


def _project_root(project: str) -> Path:
    return Path(__file__).resolve().parents[1] / project


def _closed_keys(t: int) -> set:
    from projects.e6.e6_sources import closed_bipartite_cubic_graphs

    keys = set()
    for G in closed_bipartite_cubic_graphs(t):
        key = G.canonical_label().graph6_string()
        if isinstance(key, bytes):
            key = key.decode()
        keys.add(key)
    return keys


# ---------------------------------------------------------------------------
# Obstruction-witness computation  (mathematical result, no I/O)
# ---------------------------------------------------------------------------


def e6_t22_witnesses(closed_eval: dict | None = None) -> list[dict]:
    """
    Return obstruction witnesses at t=22.

    Each record identifies a source whose fully-evaluated relation is a
    non-zero rational multiple of the known E6 obstruction polynomial.

    Parameters
    ----------
    closed_eval :
        Pre-computed evaluation dict.  Computed internally if not provided.
    """
    from projects.common.closed_pipeline import (
        closed_partially_evaluated_relations,
        extract_singleton_evaluations,
        find_evaluation_conflicts,
        fully_evaluate_relation_dict,
    )
    from projects.e6.e6_evaluations import compute_all_e6_evaluations
    from projects.e6.e6_series import E6_series_quotient
    from projects.e6.e6_sources import closed_sources

    if closed_eval is None:
        closed_eval = compute_all_e6_evaluations()

    _presentation = E6_series_quotient
    R = _presentation.theory.base_ring
    (nn,) = R.gens()

    collected22 = [
        d
        for d, _ in closed_partially_evaluated_relations(
            22, _presentation, closed_sources, closed_eval
        )
    ]

    values22, conflicts22 = find_evaluation_conflicts(collected22)
    if conflicts22:
        raise ValueError(f"t=22 evaluation conflicts: {conflicts22!r}")

    known22 = {k: value for k, (_, value) in values22.items()}
    known22 = extract_singleton_evaluations(collected22, {}, known22)

    keys22 = _closed_keys(22)
    known22 = {k: v for k, v in known22.items() if k in keys22}

    normalised_obstruction = (
        (nn - 27)
        * (nn - 15)
        * (nn - 9)
        * (nn - 6)
        * (nn - 3) ** 2
        * (nn - 1)
        * nn**2
        * (nn + 1)
        * (nn + 3) ** 2
    )

    source_recs = list(e6_source_records(22))
    if len(source_recs) != len(collected22):
        raise ValueError(
            f"source record count ({len(source_recs)}) does not match "
            f"relation count ({len(collected22)}) — order matching would be wrong"
        )

    witnesses = []
    for i, (d, sr) in enumerate(zip(collected22, source_recs)):
        scalar, unknowns = fully_evaluate_relation_dict(d, known22)
        if unknowns or scalar == 0:
            continue
        multiplier = scalar / normalised_obstruction
        if multiplier not in QQ:
            raise ValueError(f"non-rational multiplier at index {i}: {multiplier}")
        witnesses.append(
            {
                "index": i,
                "source_key": sr.source_key,
                "raw_witness": str(scalar),
                "factorisation": str(scalar.factor()),
                "normalised_obstruction": str(normalised_obstruction),
                "multiplier": str(multiplier),
            }
        )

    for display_index, w in enumerate(witnesses):
        w["display_index"] = display_index

    return witnesses
