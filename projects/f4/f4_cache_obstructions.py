import marimo

__generated_with = "0.23.5"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Write cache of obstructions for $F_4$
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Run this notebook using

            sage -python -m marimo edit src/closed_graphs/f4_cache_obstructions.py
    """)
    return


@app.cell
def _():
    import sys
    from pathlib import Path

    # Repository containing the Python source code
    SOURCE_ROOT = Path(__file__).resolve().parents[2]

    SRC = SOURCE_ROOT / "src"

    if str(SRC) not in sys.path:
        sys.path.insert(0, str(SRC))
    return


@app.cell
def _():
    from export.catalogue_cache import (
        obstruction_source_record,
        write_f4_obstruction_cache,
    )

    return obstruction_source_record, write_f4_obstruction_cache


@app.cell
def _():
    import json

    from sage.all import QQ

    from theory.examples import f4_series
    from export.paths import catalogue_cache_dir
    from closed_graphs.f4_sources import closed_sources

    from closed_graphs.closed_pipeline import (
        closed_partially_evaluated_relations,
        fully_evaluate_relation_dict,
    )
    #from export.provenance_sources import f4_source_records
    from closed_graphs.closed_pipeline import (
        closed_partially_evaluated_relations_from_source_records,
    )

    from closed_graphs.closed_pipeline import (
        find_evaluation_conflicts,
        extract_singleton_evaluations,
    )

    def load_f4_closed_evaluations_from_cache():
        """
        Load known closed evaluations from the exported catalogue caches.
        """
        presentation = f4_series.F4_series_quotient
        R = presentation.theory.base_ring

        closed_eval = {}

        for t in [10, 12, 14, 16]:
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


    def f4_t16_polynomial_obstruction_witnesses_from_cache():
        """
        Return nonzero obstruction witnesses at t=16.

        Currently this records reduced closed relations rather than
        the original four-valent sources.
        """
        presentation = f4_series.F4_series_quotient
        theory = presentation.theory

        R = theory.base_ring
        (n,) = R.gens()

        closed_eval = load_f4_closed_evaluations_from_cache()

        collected16 = list(
            closed_partially_evaluated_relations(
                16,
                presentation,
                closed_sources,
                closed_eval,
            )
        )

        values16, conflicts16 = find_evaluation_conflicts(
        [d for d, _ in collected16]
        )

        known16 = {k: value for k, (_, value) in values16.items()}
        known16 = extract_singleton_evaluations(
            [d for d, _ in collected16],
            {},
            known16,
        )


        expected = (
            n
            * (n - 26)
            * (n - 14)
            * (n - 8)
            * (n - 5)
            * (n + 1)
            * (n + 2)
            * (n - 2) ** 2
        )

        witnesses = []
        bad_multipliers = []

        for i, (d, reps) in enumerate(collected16):
            scalar, unknowns = fully_evaluate_relation_dict(d, known16)

            if unknowns:
                continue

            if scalar == 0:
                continue

            multiplier = scalar / expected

            if multiplier not in QQ:
                bad_multipliers.append(
                    {
                        "index": i,
                        "scalar": scalar,
                        "quotient": multiplier,
                        "relation": d,
                        "reps": reps,
                    }
                )
                continue

            witnesses.append(
                {
                    "index": i,
                    "relation": d,
                    "reps": reps,
                    "raw_obstruction": scalar,
                    "normalised_obstruction": expected,
                    "rational_multiplier": multiplier,
                }
            )

        print("witnesses:", len(witnesses))
        print("bad multipliers:", len(bad_multipliers))

        if bad_multipliers:
            first = bad_multipliers[0]
            print("first bad index:", first["index"])
            print("scalar =", first["scalar"].factor())
            print("expected =", expected.factor())
            print("quotient =", first["quotient"].factor())

        return witnesses


    return (f4_t16_polynomial_obstruction_witnesses_from_cache,)


@app.cell
def _(f4_t16_polynomial_obstruction_witnesses_from_cache):
    witnesses = f4_t16_polynomial_obstruction_witnesses_from_cache()
    return (witnesses,)


@app.cell
def _(obstruction_source_record, witnesses, write_f4_obstruction_cache):
    records = []

    for witness in witnesses:
        record = obstruction_source_record(
            source_graph=witness["source_graph"],
            source_key=witness["source_key"],
            raw_obstruction=witness["raw_obstruction"],
            normalised_obstruction=witness["normalised_obstruction"],
            substituted_relation=witness["relation"],
        )

        records.append(record)

    path = write_f4_obstruction_cache(records)

    print(path)
    return


@app.cell
def _(witnesses):
    len(witnesses)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
