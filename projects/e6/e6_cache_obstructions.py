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
    # Write cache of obstructions for $E_6$
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Computes and writes the E6 obstruction witnesses at $t = 22$.

    The E6 obstruction polynomial (Thurston 2004) is
    $$
        (n-27)(n-15)(n-9)(n-6)(n-3)^2(n-1)\,n^2(n+1)(n+3)^2 = 0.
    $$

    Run this notebook using

        sage -python -m marimo edit projects/e6/e6_cache_obstructions.py
    """)
    return


@app.cell
def _():
    import sys
    from pathlib import Path

    # projects/e6/e6_cache_obstructions.py  ->  parents[2] = cubic-jordan root
    CUBIC_JORDAN_ROOT = Path(__file__).resolve().parents[2]
    PROJECT_DIR = Path(__file__).resolve().parent
    TRIVALENT_SRC = CUBIC_JORDAN_ROOT.parent / "trivalent-graphs" / "src"

    for p in [str(PROJECT_DIR), str(TRIVALENT_SRC)]:
        if p not in sys.path:
            sys.path.insert(0, p)
    return


@app.cell
def _():
    from e6_obstructions import write_e6_t22_obstruction_cache

    path = write_e6_t22_obstruction_cache()
    print(f"Written: {path}")
    return (path,)


@app.cell
def _(path, mo):
    mo.md(f"Cache written to `{path}`.")
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
