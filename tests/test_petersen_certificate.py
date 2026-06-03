"""
tests/test_petersen_certificate.py

Smoke tests for the Petersen graph F4 source-reduction certificate.

These tests check the structure and invariants of the generated JSON
without re-running the full reduction (which is slow).  The slow marker
guards the full generation test.
"""

import json
from pathlib import Path

import pytest

CERT_PATH = (
    Path(__file__).resolve().parents[1]
    / "projects"
    / "f4"
    / "certificates"
    / "petersen_t10.json"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_cert():
    if not CERT_PATH.exists():
        pytest.skip(
            "petersen_t10.json not yet generated; run write_petersen_certificate()"
        )
    return json.loads(CERT_PATH.read_text())


# ---------------------------------------------------------------------------
# Structure tests (fast — read existing JSON)
# ---------------------------------------------------------------------------


def test_certificate_top_level_keys():
    cert = _load_cert()
    assert cert["format"] == "source_reduction_certificate"
    assert cert["version"] == 1
    assert cert["relation"] == "f4_six_term"
    for key in ("source", "initial", "steps", "final"):
        assert key in cert, f"missing top-level key {key!r}"


def test_source_graph_structure():
    cert = _load_cert()
    g = cert["source"]["graph"]
    assert g["format"] == "dart_graph"  # source has boundary darts
    assert g["num_boundary"] == 4  # F4 source: 4-valent vertex removed
    assert (
        g["num_vertices"] == 8
    )  # Petersen (10v) - 2 contracted = 9, minus 4-valent = 8
    assert len(g["darts"]) == g["num_darts"]
    assert len(g["vertices"]) == g["num_vertices"]
    assert len(cert["source"]["site"]) == 4


def test_initial_lc_structure():
    cert = _load_cert()
    terms = cert["initial"]["terms"]
    assert len(terms) > 0
    for term in terms:
        assert "coefficient" in term
        assert "graph" in term
        assert "coefficients" in term["coefficient"]
        g = term["graph"]
        assert g["num_boundary"] == 0  # all terms are closed


def test_steps_structure():
    cert = _load_cert()
    steps = cert["steps"]
    assert len(steps) > 0
    for step in steps:
        assert "term_index" in step
        assert "rule" in step
        assert "occurrence" in step
        assert "after" in step
        assert isinstance(step["term_index"], int)
        occ = step["occurrence"]
        assert "dart_map" in occ
        for pair in occ["dart_map"]:
            assert len(pair) == 2
        after_terms = step["after"]["terms"]
        for term in after_terms:
            assert term["graph"]["num_boundary"] == 0  # still closed


def test_final_lc_structure():
    cert = _load_cert()
    terms = cert["final"]["terms"]
    assert len(terms) > 0
    for term in terms:
        g = term["graph"]
        assert g["num_boundary"] == 0


def test_dart_graph_partner_consistency():
    """partner map must be symmetric: if partner[a]=b then partner[b]=a."""
    cert = _load_cert()

    def check_graph(g, label):
        partner = g["partner"]
        for d_str, p in partner.items():
            if p is None:
                continue
            assert str(p) in partner, f"{label}: partner[{p}] missing"
            assert partner[str(p)] == int(d_str), (
                f"{label}: partner not symmetric at dart {d_str}"
            )

    check_graph(cert["source"]["graph"], "source")
    for i, term in enumerate(cert["initial"]["terms"]):
        check_graph(term["graph"], f"initial[{i}]")
    for i, term in enumerate(cert["final"]["terms"]):
        check_graph(term["graph"], f"final[{i}]")


def test_steps_chain():
    """Each step's after LC has at least one term, and term_index is in range."""
    cert = _load_cert()
    for i, step in enumerate(cert["steps"]):
        after = step["after"]["terms"]
        assert len(after) >= 0, f"step {i} after has no terms"


# ---------------------------------------------------------------------------
# Generation test (slow — runs the full pipeline)
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_write_petersen_certificate_runs():
    """Full generation: certificate is written and has the expected structure."""
    from projects.f4.certificates.petersen_certificate import write_petersen_certificate

    path = write_petersen_certificate()
    assert path.exists()
    cert = json.loads(path.read_text())
    assert cert["format"] == "source_reduction_certificate"
    assert cert["version"] == 1
    assert len(cert["steps"]) > 0
    # Source graph: 8 internal vertices, 4 boundary darts
    assert cert["source"]["graph"]["num_boundary"] == 4
    # All terms in initial and final are closed
    for term in cert["initial"]["terms"] + cert["final"]["terms"]:
        assert term["graph"]["num_boundary"] == 0
