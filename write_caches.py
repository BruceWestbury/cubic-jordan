import marimo

__generated_with = "0.23.5"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""# Write F4 and E6 caches""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Writes catalogue and obstruction-witness caches for the F4 and E6 pipelines.

    Each pipeline's evaluations are computed once in memory and reused for all
    catalogue levels and the witness cache.

    **Note:** the authoritative writer is `write_caches_script.py` — Sage imports
    inside Marimo can fail due to cysignals/threading.  Use this notebook for
    interactive inspection only.

    Run the script with:

        sage -python write_caches_script.py
    """)
    return


@app.cell
def _():
    import sys
    from pathlib import Path

    CUBIC_JORDAN_ROOT = Path(__file__).resolve().parent
    TRIVALENT_SRC = CUBIC_JORDAN_ROOT.parent / "trivalent-graphs" / "src"

    for _p in [str(CUBIC_JORDAN_ROOT), str(TRIVALENT_SRC)]:
        if _p not in sys.path:
            sys.path.insert(0, _p)
    return CUBIC_JORDAN_ROOT, TRIVALENT_SRC, Path, sys


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## F4""")
    return


@app.cell
def _():
    from projects.f4.f4_evaluations import compute_all_f4_evaluations

    f4_eval = compute_all_f4_evaluations()
    print(f"F4: {len(f4_eval)} evaluations computed")
    return (f4_eval,)


@app.cell
def _(f4_eval):
    from projects.f4.f4_evaluations import write_all_f4_closed_catalogue_caches

    f4_catalogue_paths = write_all_f4_closed_catalogue_caches(f4_eval)
    for p in f4_catalogue_paths:
        print(p)
    return (f4_catalogue_paths,)


@app.cell
def _(f4_eval):
    from projects.f4.f4_witnesses import write_f4_t16_witness_cache

    f4_witness_path = write_f4_t16_witness_cache(f4_eval)
    print(f4_witness_path)
    return (f4_witness_path,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## E6""")
    return


@app.cell
def _():
    from projects.e6.e6_evaluations import compute_all_e6_evaluations

    e6_eval = compute_all_e6_evaluations()
    print(f"E6: {len(e6_eval)} evaluations computed")
    return (e6_eval,)


@app.cell
def _(e6_eval):
    from projects.e6.e6_evaluations import write_all_e6_closed_catalogue_caches

    e6_catalogue_paths = write_all_e6_closed_catalogue_caches(e6_eval)
    for p in e6_catalogue_paths:
        print(p)
    return (e6_catalogue_paths,)


@app.cell
def _(e6_eval):
    from projects.e6.e6_witnesses import write_e6_t22_witness_cache

    e6_witness_path = write_e6_t22_witness_cache(e6_eval)
    print(e6_witness_path)
    return (e6_witness_path,)


@app.cell
def _(
    e6_catalogue_paths,
    e6_witness_path,
    f4_catalogue_paths,
    f4_witness_path,
    mo,
):
    mo.md(
        "\n".join(
            [
                "## Written caches",
                "",
                "### F4 catalogue caches",
                *[f"- `{p}`" for p in f4_catalogue_paths],
                "",
                "### F4 obstruction witnesses",
                f"- `{f4_witness_path}`",
                "",
                "### E6 catalogue caches",
                *[f"- `{p}`" for p in e6_catalogue_paths],
                "",
                "### E6 obstruction witnesses",
                f"- `{e6_witness_path}`",
            ]
        )
    )
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
