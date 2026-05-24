"""
tests/test_e6_cache_writers.py

Smoke tests for the E6 cache writer functions.

Mirrors test_f4_cache_writers.py.  t=14 (the Heawood graph, one graph) is
used for the fast tests because it is the smallest E6 level.  The full
pipeline (all five levels) and the witness writer are slow and marked
accordingly.
"""

import json

import pytest

from projects.e6.e6_evaluations import (
    compute_all_e6_evaluations,
    write_e6_closed_catalogue_cache,
    write_e6_closed_evaluation_cache,
)
from projects.e6.e6_witnesses import write_e6_t22_witness_cache


def test_e6_catalogue_cache_writer_t14():
    path = write_e6_closed_catalogue_cache(14)
    assert path.exists()
    data = json.loads(path.read_text())
    assert data["project"] == "e6"
    assert data["records"]
    assert "id" in data["records"][0]


@pytest.mark.slow
def test_e6_evaluation_cache_writer_t14():
    closed_eval = compute_all_e6_evaluations()
    path = write_e6_closed_evaluation_cache(14, closed_eval)
    assert path.exists()
    data = json.loads(path.read_text())
    assert data["project"] == "e6"
    assert data["records"]
    assert "evaluation" in data["records"][0]


@pytest.mark.slow
def test_e6_witness_cache_writer():
    path = write_e6_t22_witness_cache()
    assert path.exists()
    data = json.loads(path.read_text())
    assert data["project"] == "e6"
    assert data["records"]
