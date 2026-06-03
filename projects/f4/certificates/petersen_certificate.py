"""
projects.f4.certificates.petersen_certificate

Generate a source-reduction certificate for the Petersen graph
under the F4-series theory.

The Petersen graph is the unique closed cubic girth-5 graph on 10
vertices.  We pick one edge, contract it to obtain the unique
FourValentSource at t=10, insert the six-term relation, and reduce
with the F4_series_quotient rules, recording every step.

The result is written to ``petersen_t10.json`` in this directory.

Usage
-----
Run from the cubic-jordan repo root::

    PYTHONPATH=.:../trivalent-graphs/src sage -python \\
        projects/f4/certificates/petersen_certificate.py

or import and call::

    from projects.f4.certificates.petersen_certificate import write_petersen_certificate
    write_petersen_certificate()
"""

from __future__ import annotations

import json
from pathlib import Path


def write_petersen_certificate(out_path: Path | None = None) -> Path:
    """
    Generate and write the F4 source-reduction certificate for the
    Petersen graph.

    Parameters
    ----------
    out_path :
        Destination file.  Defaults to ``petersen_t10.json`` alongside
        this module.

    Returns
    -------
    Path
        The path of the written JSON file.

    Notes
    -----
    The certificate format is defined in ``CERTIFICATE_FORMAT.md`` and
    implemented in ``trivalent-graphs/src/certificates/``.

    * ``source.graph`` is the DartGraph obtained by removing the
      contracted vertex from the Petersen graph; it has 4 boundary darts.
    * ``source.site`` is the ordered 4-tuple of boundary darts that
      correspond to the four edges of the contracted vertex.
    * ``initial`` is the linear combination of closed DartGraphs
      produced by inserting the six-term relation at the site.
    * ``steps`` records every application of a reduction rule until no
      rule fires.
    * ``final`` is the irreducible linear combination.

    Version 1 does not include evaluation cache lookup; the final linear
    combination may still contain non-trivial closed graphs.
    """
    # --- imports from trivalent-graphs (must be on PYTHONPATH) ----------
    from certificates.source_certificate import make_source_certificate
    from rewriting.apply_relation import FourValentSource

    # --- imports from this repo -----------------------------------------
    from projects.f4.f4_series import F4_series_quotient, six_term
    from projects.f4.f4_sources import (
        closed_cubic_girth5_graphs,
        contract_to_four_valent,
        four_valent_graph_to_source,
    )

    # -----------------------------------------------------------------------
    # 1. Obtain the Petersen graph (the unique closed cubic girth-5 graph
    #    on 10 vertices).
    # -----------------------------------------------------------------------
    petersen = next(iter(closed_cubic_girth5_graphs(10)))

    # -----------------------------------------------------------------------
    # 2. Contract the first edge to produce a FourValentSource.
    #    contract_to_four_valent returns (H, w) where H is a Sage graph
    #    with the 4-valent vertex w still present.
    #    four_valent_graph_to_source removes w and returns (DartGraph, site).
    # -----------------------------------------------------------------------
    first_edge = tuple(next(iter(petersen.edges(labels=False)))[:2])
    F = contract_to_four_valent(petersen, first_edge)
    dart_graph, site = four_valent_graph_to_source(F)
    source = FourValentSource(graph=dart_graph, site=site)

    # -----------------------------------------------------------------------
    # 3. Build the certificate.
    # -----------------------------------------------------------------------
    cert = make_source_certificate(
        source,
        six_term(),
        F4_series_quotient,
        relation_name="f4_six_term",
    )

    # -----------------------------------------------------------------------
    # 4. Write to disk.
    # -----------------------------------------------------------------------
    if out_path is None:
        out_path = Path(__file__).resolve().parent / "petersen_t10.json"

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(cert, indent=2) + "\n",
        encoding="utf-8",
    )
    return out_path


if __name__ == "__main__":
    path = write_petersen_certificate()
    print(f"Written: {path}")
