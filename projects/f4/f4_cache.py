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
    # Write $F_4$ caches
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Writes the caches for closed graphs with $t=10, 12, 14, 16$ vertices.

    Not all graphs with 16 vertices are evaluated.

    Run this notebook using

        sage -python -m marimo edit src/export/f4_cache.py
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
    from export.f4_evaluations import (
        write_all_f4_closed_evaluation_caches,
    )

    paths = write_all_f4_closed_evaluation_caches()
    return


@app.cell
def _():
    from export.catalogue_cache import export_closed_catalogue_for_t

    catalogue_paths = [
        export_closed_catalogue_for_t(project="f4", t=t) for t in [10, 12, 14, 16]
    ]
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    "\n".join(
            [
                "# Exported caches",
                "\",
                "## Evaluation caches",
                *[f"- `{p}`" for p in paths],
                "\",
                "## Catalogue caches",
                *[f"- `{p}`" for p in catalogue_paths],
            ]
        )
    )
    """)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
