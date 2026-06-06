"""
tests/test_v2_e6_source_certificate.py

Smoke tests for the V2 E6 source-reduction certificate produced by
``e6_witnesses.write_e6_source_certificate``.

Uses t=14 (the Heawood graph, the smallest E6 level — one source, one
certificate) so the test completes in reasonable time.
"""

import json
import tempfile
from pathlib import Path

import pytest

REQUIRED_STEP_KEYS = frozenset(
    {"term_index", "rule", "occurrence", "replacement_certificates", "after"}
)
REQUIRED_RC_KEYS = frozenset(
    {
        "coefficient",
        "before_graph",
        "before_occurrence",
        "after_raw",
        "after_occurrence",
        "complement_isomorphism",
        "relabelling",
        "after_graph",
    }
)


@pytest.fixture(scope="module")
def e6_t14_cert_path(tmp_path_factory):
    """Generate a V2 certificate for the single t=14 E6 source."""
    from projects.e6.e6_witnesses import write_e6_source_certificate
    from projects.export.provenance_sources import e6_source_records

    sr = next(iter(e6_source_records(14)))
    out = tmp_path_factory.mktemp("e6_cert") / "e6_t14_source_000.json"
    write_e6_source_certificate(sr, out)
    return out


@pytest.fixture(scope="module")
def e6_t14_cert(e6_t14_cert_path):
    return json.loads(e6_t14_cert_path.read_text())


# ---------------------------------------------------------------------------
# 1 & 2. format and version
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_e6_v2_format(e6_t14_cert):
    assert e6_t14_cert["format"] == "source_reduction_certificate"
    assert e6_t14_cert["version"] == 2


# ---------------------------------------------------------------------------
# 3. initial and steps present
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_e6_v2_has_initial_and_steps(e6_t14_cert):
    assert "initial" in e6_t14_cert
    assert "steps" in e6_t14_cert
    assert len(e6_t14_cert["steps"]) > 0


# ---------------------------------------------------------------------------
# 4. first step is the E6 source-expansion step
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_e6_v2_first_step_is_source_expansion(e6_t14_cert):
    s0 = e6_t14_cert["steps"][0]
    assert s0["rule"] == "e6_seven_term"
    assert s0["term_index"] == 0
    assert "dart_map" in s0["occurrence"]
    # Seven-term relation has 7 terms
    assert len(s0["replacement_certificates"]) == 7


# ---------------------------------------------------------------------------
# 5. later graphs are canonical V2 closed DartGraphs
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_e6_v2_later_graphs_are_canonical(e6_t14_cert):
    steps = e6_t14_cert["steps"]
    # Skip first step (source expansion); all subsequent after-graphs are trivalent
    for i, step in enumerate(steps[1:], start=1):
        for term in step["after"]["terms"]:
            g = term["graph"]
            assert g["format"] == "closed_dart_graph", f"step {i}: wrong format"
            assert g["version"] == 2
            nd = g["num_darts"]
            assert len(g["partner"]) == nd
            assert len(g["vertex_of"]) == nd
            # Canonical: all partner values are valid consecutive dart indices
            for p in g["partner"]:
                assert isinstance(p, int) and 0 <= p < nd, (
                    f"step {i}: invalid partner {p}"
                )


# ---------------------------------------------------------------------------
# 6. replacement certificates come from the V2 machinery
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_e6_v2_replacement_cert_schema(e6_t14_cert):
    for i, step in enumerate(e6_t14_cert["steps"]):
        missing = REQUIRED_STEP_KEYS - set(step)
        assert not missing, f"step {i} missing keys: {missing}"
        for j, rc in enumerate(step["replacement_certificates"]):
            missing_rc = REQUIRED_RC_KEYS - set(rc)
            assert not missing_rc, f"step {i} rc {j} missing keys: {missing_rc}"
            ag = rc["after_graph"]
            assert ag["format"] == "closed_dart_graph" and ag["version"] == 2, (
                f"step {i} rc {j}: wrong after_graph format"
            )
            nd = ag["num_darts"]
            for p in ag["partner"]:
                assert isinstance(p, int) and 0 <= p < nd


# ---------------------------------------------------------------------------
# initial LC: single term, source graph with 5-valent vertex
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_e6_v2_initial_single_term(e6_t14_cert):
    terms = e6_t14_cert["initial"]["terms"]
    assert len(terms) == 1
    assert terms[0]["coefficient"] == {"coefficients": ["1"]}
    g = terms[0]["graph"]
    assert g["format"] == "closed_dart_graph"
    assert g["version"] == 2
    assert g["num_darts"] > 0
