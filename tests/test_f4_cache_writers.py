"""
tests/test_f4_cache_writers.py

Smoke tests for the F4 catalogue and witness cache writers.

The catalogue writer generates everything in memory from f4_sources —
it must not read from or create cache/raw or cache/evaluations directories.
"""

import json

import pytest

from projects.f4.f4_evaluations import (
    _catalogue_cache_dir,
    _project_root,
    compute_all_f4_evaluations,
    write_all_f4_closed_catalogue_caches,
    write_f4_closed_catalogue_cache,
)
from projects.f4.f4_witnesses import write_f4_t16_witness_cache


def test_f4_catalogue_cache_writer_t10():
    """Catalogue writer for t=10 requires no intermediate files.

    Passes closed_eval={} to skip the pipeline; we are testing format only.
    """
    path = write_f4_closed_catalogue_cache(10, closed_eval={})
    assert path.exists()
    data = json.loads(path.read_text())
    assert data["project"] == "f4"
    assert data["records"]
    rec = data["records"][0]
    assert "id" in rec
    assert "evaluation" in rec  # key present; value is None when eval not supplied
    assert "svg" in rec
    # written to cache/closed, not cache/raw or cache/evaluations
    assert path.parent == _catalogue_cache_dir("f4")


def test_f4_catalogue_no_intermediate_dirs():
    """Catalogue writer must not create cache/raw or cache/evaluations."""
    proj = _project_root("f4")
    write_f4_closed_catalogue_cache(10, closed_eval={})
    assert not (proj / "cache" / "raw").exists()
    assert not (proj / "cache" / "evaluations").exists()


@pytest.mark.slow
def test_f4_catalogue_all_levels():
    """All four F4 catalogue caches share one evaluation run."""
    closed_eval = compute_all_f4_evaluations()
    paths = write_all_f4_closed_catalogue_caches(closed_eval)
    assert len(paths) == 4
    for p in paths:
        assert p.exists()
        data = json.loads(p.read_text())
        assert data["project"] == "f4"
        assert data["records"]
        assert "id" in data["records"][0]
        assert p.parent == _catalogue_cache_dir("f4")


@pytest.mark.slow
def test_f4_witness_cache_writer():
    path = write_f4_t16_witness_cache()
    assert path.exists()
    data = json.loads(path.read_text())
    assert data["project"] == "f4"
    assert data["records"]
    # written to cache/obstructions_t16.json (not cache/closed/)
    assert path.name == "obstructions_t16.json"
    assert path.parent.name == "cache"
