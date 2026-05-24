import json

import pytest

from projects.f4.f4_evaluations import (
    compute_all_f4_evaluations,
    write_f4_closed_catalogue_cache,
    write_f4_closed_evaluation_cache,
)
from projects.f4.f4_witnesses import write_f4_t16_witness_cache


def test_f4_catalogue_cache_writer_t10():
    path = write_f4_closed_catalogue_cache(10)
    assert path.exists()
    data = json.loads(path.read_text())
    assert data["project"] == "f4"
    assert data["records"]
    assert "id" in data["records"][0]


def test_f4_evaluation_cache_writer_t10():
    closed_eval = compute_all_f4_evaluations()
    path = write_f4_closed_evaluation_cache(10, closed_eval)
    assert path.exists()
    data = json.loads(path.read_text())
    assert data["project"] == "f4"
    assert data["records"]
    assert "evaluation" in data["records"][0]


@pytest.mark.slow
def test_f4_witness_cache_writer():
    path = write_f4_t16_witness_cache()
    assert path.exists()
    data = json.loads(path.read_text())
    assert data["project"] == "f4"
    assert data["records"]
