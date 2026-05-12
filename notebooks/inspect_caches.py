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
    # Inspecting caches of closed graphs and of sources
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    This notebook exhibits cached closed graphs and source graphs
    for the $F_4$ and $E_6$ computations.
    """)
    return


@app.cell
def _():
    SRC = "/home/brucewestbury/Research/trivalent-graphs/src"

    import sys

    if SRC not in sys.path:
        sys.path.insert(0, SRC)
    return


@app.cell
def _():
    from pathlib import Path

    REPO = Path("/home/brucewestbury/Research/trivalent-graphs")
    return (REPO,)


@app.cell
def _():
    from cache_inspect.inspect import closed_cache_to_dot, source_cache_to_dot
    from visualisation.graphviz_render import dot_to_svg

    return (dot_to_svg,)


@app.cell
def _(mo):
    family = mo.ui.dropdown(
        options=["f4", "e6"],
        value="f4",
        label="Family",
    )

    kind = mo.ui.dropdown(
        options=["closed", "sources"],
        value="closed",
        label="Cache kind",
    )

    mo.hstack([family, kind])
    return family, kind


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Selectors
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Selected cache item

    - Family: `{family.value}`
    - Kind: `{kind.value}`
    - File: `{cache_file.value.name}`
    - Index: `{index.value}`
    - Cache size: `{len(cache)}`
    """)
    return


@app.cell
def _():
    from cache_inspect.inspect import (
        cache_item,
        closed_cache_item_to_dot,
        load_json_cache,
        source_cache_item_to_dot,
    )

    return (
        cache_item,
        closed_cache_item_to_dot,
        load_json_cache,
        source_cache_item_to_dot,
    )


@app.cell
def _(REPO, family, kind, mo):
    cache_dir = REPO / "projects" / family.value / "cache" / kind.value
    cache_files = sorted(cache_dir.glob("*.json"))

    cache_file_names = [p.name for p in cache_files]

    cache_file = mo.ui.dropdown(
        options=cache_file_names,
        value=cache_file_names[0] if cache_file_names else None,
        label="Cache file",
    )

    cache_file
    return cache_dir, cache_file


@app.cell
def _(cache_dir, cache_file, load_json_cache, mo):
    cache_path = cache_dir / cache_file.value
    cache = load_json_cache(cache_path)

    index = mo.ui.slider(
        start=0,
        stop=max(len(cache) - 1, 0),
        value=0,
        label=f"Item index: 0 to {len(cache) - 1}",
    )

    index
    return cache, index


@app.cell
def _(
    cache,
    cache_item,
    closed_cache_item_to_dot,
    index,
    kind,
    source_cache_item_to_dot,
):
    item = cache_item(cache, index.value)

    if kind.value == "closed":
        dot = closed_cache_item_to_dot(item)
    else:
        dot = source_cache_item_to_dot(item)

    dot
    return (dot,)


@app.cell
def _(dot, dot_to_svg):
    svg = dot_to_svg(dot)
    return (svg,)


@app.cell
def _(mo, svg):
    mo.Html(svg)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
