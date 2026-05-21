import marimo

__generated_with = "0.23.5"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""# Write $E_6$ caches""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Writes evaluation and catalogue caches for closed bipartite cubic graphs
    with girth at least 6 at t = 16, 18, 20, 22 vertices.

    Run this notebook using

        sage -python -m marimo edit projects/e6/e6_cache.py
    """)
    return


@app.cell
def _():
    import sys
    from pathlib import Path

    # projects/e6/e6_cache.py -> parents[2] = cubic-jordan root
    CUBIC_JORDAN_ROOT = Path(__file__).resolve().parents[2]
    PROJECT_DIR = Path(__file__).resolve().parent
    TRIVALENT_SRC = CUBIC_JORDAN_ROOT.parent / "trivalent-graphs" / "src"

    for p in [str(PROJECT_DIR), str(TRIVALENT_SRC)]:
        if p not in sys.path:
            sys.path.insert(0, p)
    return


@app.cell
def _():
    from e6_evaluations import write_all_e6_closed_evaluation_caches

    evaluation_paths = write_all_e6_closed_evaluation_caches()
    for p in evaluation_paths:
        print(p)
    return (evaluation_paths,)


@app.cell
def _():
    from e6_obstructions import write_e6_t22_obstruction_cache

    obstruction_path = write_e6_t22_obstruction_cache()
    print(obstruction_path)
    return (obstruction_path,)


@app.cell
def _(evaluation_paths, obstruction_path, mo):
    mo.md(
        "\n".join([
            "## Written caches",
            "",
            "### Evaluation caches",
            *[f"- `{p}`" for p in evaluation_paths],
            "",
            "### Obstruction cache",
            f"- `{obstruction_path}`",
        ])
    )
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
