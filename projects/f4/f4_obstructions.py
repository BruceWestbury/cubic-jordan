"""
closed_graphs/f4_obstructions.py
"""

import json

from sage.all import QQ

from closed_graphs.closed_pipeline import (
    closed_partially_evaluated_relations,
    extract_singleton_evaluations,
    find_evaluation_conflicts,
    fully_evaluate_relation_dict,
)
from closed_graphs.f4_closed_evaluations import (
    compute_t14_evaluations,
    seeded_closed_evaluations,
)
from closed_graphs.f4_sources import closed_cubic_girth5_graphs, closed_sources
from export.paths import catalogue_cache_dir
from export.provenance_sources import f4_source_records
from theory.examples.f4_series import F4_series_quotient


def load_closed_evaluations_from_cache(project: str = "f4") -> dict:
    closed_eval = {}

    for t in [10, 12, 14, 16]:
        path = catalogue_cache_dir(project) / f"closed_t{t}.json"

        with path.open("r", encoding="utf-8") as f:
            doc = json.load(f)

        for record in doc.get("records", []):
            key = record["internal"]["closed_key"]
            value = record.get("evaluation")

            if value is not None:
                closed_eval[key] = value

    return closed_eval


def load_f4_closed_evaluations_from_cache(levels=(10, 12, 14)):
    presentation = F4_series_quotient
    R = presentation.theory.base_ring

    closed_eval = {}

    for t in levels:
        path = catalogue_cache_dir("f4") / f"closed_t{t}.json"

        with path.open("r", encoding="utf-8") as f:
            doc = json.load(f)

        for record in doc.get("records", []):
            value = record.get("evaluation")
            if value is None:
                continue

            key = record["internal"]["closed_key"]
            closed_eval[key] = R(value)

    return closed_eval


def _construction_to_json(c):
    out = {
        "closed_key": c.closed_key,
        "operation": c.operation,
    }

    if hasattr(c, "closed_class"):
        out["closed_class"] = c.closed_class

    return out


def _source_record_to_json(source):
    return {
        "source_key": source.source_key,
        "site": [int(x) for x in source.site],
        "constructions": [_construction_to_json(c) for c in source.constructions],
    }


def _relation_dict_to_json(d):
    terms = [[str(coeff), str(graph_key)] for graph_key, coeff in d.items()]
    terms.sort(key=lambda term: term[1])
    return terms


def _closed_keys(t):
    keys = set()

    for G in closed_cubic_girth5_graphs(t):
        key = G.canonical_label().graph6_string()

        if isinstance(key, bytes):
            key = key.decode()

        keys.add(key)

    return keys


def f4_t16_obstruction_witnesses_from_cache():
    presentation = F4_series_quotient
    theory = presentation.theory

    R = theory.base_ring
    (n,) = R.gens()

    closed_eval = seeded_closed_evaluations()
    known14 = compute_t14_evaluations(closed_eval, closed_sources)
    closed_eval.update(known14)

    collected16 = [
        d
        for d, _ in closed_partially_evaluated_relations(
            16,
            presentation,
            closed_sources,
            closed_eval,
        )
    ]

    values16, conflicts16 = find_evaluation_conflicts(collected16)
    if conflicts16:
        raise ValueError(f"t=16 evaluation conflicts: {conflicts16!r}")

    known16 = {k: value for k, (_, value) in values16.items()}
    known16 = extract_singleton_evaluations(collected16, {}, known16)

    keys16 = _closed_keys(16)
    known16 = {k: v for k, v in known16.items() if k in keys16}

    if len(collected16) != 335:
        raise ValueError(f"expected 335 t=16 relations, got {len(collected16)}")

    if len(known16) != 49:
        raise ValueError(f"expected 49 t=16 evaluations, got {len(known16)}")

    source_records = list(f4_source_records(16))

    if len(source_records) != len(collected16):
        raise ValueError(
            "source/provenance count does not match relation count: "
            f"{len(source_records)} sources, {len(collected16)} relations"
        )

    normalised_obstruction = (
        n * (n - 26) * (n - 14) * (n - 8) * (n - 5) * (n + 1) * (n + 2) * (n - 2) ** 2
    )

    witnesses = []

    for source, d in zip(source_records, collected16, strict=True):
        scalar, unknowns = fully_evaluate_relation_dict(d, known16)

        if unknowns:
            continue

        if scalar == 0:
            continue

        multiplier = scalar / normalised_obstruction

        if multiplier not in QQ:
            raise ValueError(
                f"non-rational multiplier for {source.source_key}: {multiplier}"
            )

        witnesses.append(
            {
                "source_key": source.source_key,
                "provenance": _source_record_to_json(source),
                "relation": _relation_dict_to_json(d),
                "raw_obstruction": str(scalar),
                "factorisation": str(scalar.factor()),
                "normalised_obstruction": str(normalised_obstruction),
                "multiplier": str(multiplier),
            }
        )

    witnesses.sort(key=lambda r: r["source_key"])

    for display_index, witness in enumerate(witnesses):
        witness["display_index"] = display_index

    if len(witnesses) != 38:
        raise ValueError(f"expected 38 obstruction witnesses, got {len(witnesses)}")

    return witnesses


def f4_t16_closed_evaluations():
    presentation = F4_series_quotient

    closed_eval = seeded_closed_evaluations()
    known14 = compute_t14_evaluations(closed_eval, closed_sources)
    closed_eval.update(known14)

    collected16 = [
        d
        for d, _ in closed_partially_evaluated_relations(
            16,
            presentation,
            closed_sources,
            closed_eval,
        )
    ]

    values16, conflicts16 = find_evaluation_conflicts(collected16)
    if conflicts16:
        raise ValueError(f"t=16 evaluation conflicts: {conflicts16!r}")

    known16 = {k: value for k, (_, value) in values16.items()}
    known16 = extract_singleton_evaluations(collected16, {}, known16)

    keys16 = _closed_keys(16)
    known16 = {k: v for k, v in known16.items() if k in keys16}

    if len(known16) != 49:
        raise ValueError(f"expected 49 t=16 evaluations, got {len(known16)}")

    return known16


def write_f4_t16_closed_evaluation_cache():
    import json

    known16 = f4_t16_closed_evaluations()

    path = catalogue_cache_dir("f4") / "closed_t16.json"

    with path.open("r", encoding="utf-8") as f:
        doc = json.load(f)

    for record in doc["records"]:
        key = record["internal"]["closed_key"]
        if key in known16:
            record["evaluation"] = str(known16[key]).replace("nn", "n")

    missing = [
        record["internal"]["closed_key"]
        for record in doc["records"]
        if record.get("evaluation") is None
    ]

    if missing:
        raise ValueError(f"missing {len(missing)} t=16 evaluations: {missing}")

    path.write_text(
        json.dumps(doc, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return path


def write_f4_t16_obstruction_cache():
    import json

    witnesses = f4_t16_obstruction_witnesses_from_cache()

    path = catalogue_cache_dir("f4") / "obstructions_t16.json"

    doc = {
        "format": "f4_obstruction_witness_cache",
        "version": 1,
        "project": "f4",
        "t": 16,
        "count": len(witnesses),
        "records": witnesses,
    }

    path.write_text(
        json.dumps(doc, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return path
