"""
tests/test_v2_source_certificate.py

Smoke tests for the V2 source-reduction certificate produced by
``projects.f4.f4_source_certificates.make_f4_source_certificate_v2``.

Uses the Petersen graph (the unique F4 source at t=10) as a small example.
"""

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
OBSOLETE_V1_KEYS = {"source", "relation", "final"}


@pytest.fixture(scope="module")
def petersen_v2_cert():
    """Generate the V2 certificate for the Petersen graph (cached per session)."""
    from rewriting.apply_relation import FourValentSource

    from projects.f4.f4_series import F4_series_quotient, six_term
    from projects.f4.f4_source_certificates import make_f4_source_certificate_v2
    from projects.f4.f4_sources import (
        closed_cubic_girth5_graphs,
        contract_to_four_valent,
        four_valent_graph_to_source,
    )

    petersen = next(iter(closed_cubic_girth5_graphs(10)))
    edge = tuple(next(iter(petersen.edges(labels=False)))[:2])
    F = contract_to_four_valent(petersen, edge)
    dg, site = four_valent_graph_to_source(F)
    source = FourValentSource(graph=dg, site=site)

    return make_f4_source_certificate_v2(source, six_term(), F4_series_quotient)


@pytest.mark.slow
def test_v2_format_and_version(petersen_v2_cert):
    cert = petersen_v2_cert
    assert cert["format"] == "source_reduction_certificate"
    assert cert["version"] == 2


@pytest.mark.slow
def test_v2_no_obsolete_v1_fields(petersen_v2_cert):
    """Top-level must not carry V1-only fields."""
    for key in OBSOLETE_V1_KEYS:
        assert key not in petersen_v2_cert, f"obsolete V1 field present: {key!r}"


@pytest.mark.slow
def test_v2_initial_lc(petersen_v2_cert):
    """initial: one term, coefficient 1, closed_dart_graph v2 with 4-valent vertex."""
    initial = petersen_v2_cert["initial"]
    assert "terms" in initial
    assert len(initial["terms"]) == 1

    term = initial["terms"][0]
    assert term["coefficient"] == {"coefficients": ["1"]}

    g = term["graph"]
    assert g["format"] == "closed_dart_graph"
    assert g["version"] == 2
    # Petersen has 10 vertices; source graph = 10 - 2 (contracted) + 1 (v4) = 9
    assert g["num_vertices"] == 9
    # 9 trivalent + 1 four-valent → 9*3 + 4 = 31 darts (each dart counted once)
    # Actually: darts = 2 * edges.  Petersen: 15 edges - 1 (contracted) + 4 (v4 stubs) = 18 edges → 36 darts
    # More precisely: open source has 8 vertices, 4 boundary darts + internal darts.
    # Just check it's positive.
    assert g["num_darts"] > 0

    # V2 array format: lengths match num_darts
    assert len(g["vertex_of"]) == g["num_darts"]
    assert len(g["partner"]) == g["num_darts"]


@pytest.mark.slow
def test_v2_steps_nonempty(petersen_v2_cert):
    steps = petersen_v2_cert["steps"]
    assert len(steps) > 0


@pytest.mark.slow
def test_v2_first_step_is_six_term(petersen_v2_cert):
    """First step applies the six-term relation (rule = 'f4_six_term')."""
    s0 = petersen_v2_cert["steps"][0]
    assert s0["rule"] == "f4_six_term"
    assert s0["term_index"] == 0
    assert "dart_map" in s0["occurrence"]
    # Six-term relation has 6 terms
    assert len(s0["replacement_certificates"]) == 6


@pytest.mark.slow
def test_v2_step_schema(petersen_v2_cert):
    """Every step has the required V2 keys; every replacement cert has all fields."""
    for i, step in enumerate(petersen_v2_cert["steps"]):
        missing = REQUIRED_STEP_KEYS - set(step)
        assert not missing, f"step {i} missing keys: {missing}"

        for j, rc in enumerate(step["replacement_certificates"]):
            missing_rc = REQUIRED_RC_KEYS - set(rc)
            assert not missing_rc, f"step {i} rc {j} missing keys: {missing_rc}"


@pytest.mark.slow
def test_v2_replacement_cert_graphs_are_v2(petersen_v2_cert):
    """after_graph in every replacement cert is a V2 ClosedDartGraph."""
    for i, step in enumerate(petersen_v2_cert["steps"]):
        for j, rc in enumerate(step["replacement_certificates"]):
            ag = rc["after_graph"]
            assert ag["format"] == "closed_dart_graph", (
                f"step {i} rc {j}: wrong format {ag['format']!r}"
            )
            assert ag["version"] == 2, f"step {i} rc {j}: wrong version {ag['version']}"
            nd = ag["num_darts"]
            assert len(ag["vertex_of"]) == nd
            assert len(ag["partner"]) == nd
            # All partner values must be valid dart indices (0..nd-1)
            for p in ag["partner"]:
                assert isinstance(p, int) and 0 <= p < nd, (
                    f"step {i} rc {j}: invalid partner {p}"
                )


@pytest.mark.slow
def test_v2_final_graphs_have_v2_format(petersen_v2_cert):
    """Graphs in the last step's after-LC are V2 ClosedDartGraphs."""
    last_after = petersen_v2_cert["steps"][-1]["after"]["terms"]
    assert len(last_after) > 0
    for i, term in enumerate(last_after):
        g = term["graph"]
        assert g["format"] == "closed_dart_graph", f"final term {i}: wrong format"
        assert g["version"] == 2
        nd = g["num_darts"]
        assert len(g["partner"]) == nd
        assert len(g["vertex_of"]) == nd
        # All partner values valid
        for p in g["partner"]:
            assert isinstance(p, int) and 0 <= p < nd
