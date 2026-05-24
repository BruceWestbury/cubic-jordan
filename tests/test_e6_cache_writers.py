"""
tests/test_e6_cache_writers.py

Smoke tests for the E6 catalogue and witness cache writers.

The catalogue writer generates everything in memory from e6_sources —
it must not read from or create cache/raw or cache/evaluations directories.

t=14 (the Heawood graph, one graph) is used for the fast tests because it
is the smallest E6 level and requires no prior cached data.
"""

import json

import pytest

from projects.e6.e6_evaluations import (
    _catalogue_cache_dir,
    _project_root,
    compute_all_e6_evaluations,
    write_all_e6_closed_catalogue_caches,
    write_e6_closed_catalogue_cache,
)
from projects.e6.e6_witnesses import write_e6_t22_witness_cache


def test_e6_catalogue_cache_writer_t14():
    """Catalogue writer for t=14 requires no intermediate files.

    Passes closed_eval={} to skip the pipeline; we are testing format only.
    """
    path = write_e6_closed_catalogue_cache(14, closed_eval={})
    assert path.exists()
    data = json.loads(path.read_text())
    assert data["project"] == "e6"
    assert data["records"]
    rec = data["records"][0]
    assert "id" in rec
    assert "evaluation" in rec  # key present; value is None when eval not supplied
    assert "svg" in rec
    # written to cache/closed, not cache/raw or cache/evaluations
    assert path.parent == _catalogue_cache_dir("e6")


def test_e6_catalogue_no_intermediate_dirs():
    """Catalogue writer must not create cache/raw or cache/evaluations."""
    proj = _project_root("e6")
    write_e6_closed_catalogue_cache(14, closed_eval={})
    assert not (proj / "cache" / "raw").exists()
    assert not (proj / "cache" / "evaluations").exists()


@pytest.mark.slow
def test_e6_catalogue_all_levels():
    """All five E6 catalogue caches share one evaluation run."""
    closed_eval = compute_all_e6_evaluations()
    paths = write_all_e6_closed_catalogue_caches(closed_eval)
    assert len(paths) == 5
    for p in paths:
        assert p.exists()
        data = json.loads(p.read_text())
        assert data["project"] == "e6"
        assert data["records"]
        assert "id" in data["records"][0]
        assert p.parent == _catalogue_cache_dir("e6")


@pytest.mark.slow
def test_e6_witness_cache_writer():
    path = write_e6_t22_witness_cache()
    assert path.exists()
    data = json.loads(path.read_text())
    assert data["project"] == "e6"
    assert data["records"]
    # written to cache/obstructions_t22.json (not cache/closed/)
    assert path.name == "obstructions_t22.json"
    assert path.parent.name == "cache"
