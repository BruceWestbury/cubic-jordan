"""
write_caches_script.py

Writes catalogue and obstruction-witness caches for the F4 and E6 pipelines.

Each pipeline's evaluations are computed once in memory and reused for all
catalogue levels and the witness cache, avoiding redundant pipeline runs.

Run with:
    sage -python write_caches_script.py
"""

import sys
from pathlib import Path

CUBIC_JORDAN_ROOT = Path(__file__).resolve().parent
TRIVALENT_SRC = CUBIC_JORDAN_ROOT.parent / "trivalent-graphs" / "src"

for _p in [str(CUBIC_JORDAN_ROOT), str(TRIVALENT_SRC)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


from projects.e6.e6_evaluations import (
    compute_all_e6_evaluations,
    write_all_e6_closed_catalogue_caches,
)
from projects.e6.e6_witnesses import write_e6_t22_witness_cache
from projects.f4.f4_evaluations import (
    compute_all_f4_evaluations,
    write_all_f4_closed_catalogue_caches,
)
from projects.f4.f4_witnesses import write_f4_t16_witness_cache


def main():
    print("=== F4 ===")
    print("Computing evaluations (t=10,12 seeded; pipeline at t=14,16)...")
    f4_eval = compute_all_f4_evaluations()
    print(f"  {len(f4_eval)} evaluations computed")

    print("Writing catalogue caches...")
    for p in write_all_f4_closed_catalogue_caches(f4_eval):
        print(f"  {p}")

    print("Writing obstruction witness cache...")
    print(f"  {write_f4_t16_witness_cache(f4_eval)}")

    print()
    print("=== E6 ===")
    print("Computing evaluations (pipeline at t=14,16,18,20,22)...")
    e6_eval = compute_all_e6_evaluations()
    print(f"  {len(e6_eval)} evaluations computed")

    print("Writing catalogue caches...")
    for p in write_all_e6_closed_catalogue_caches(e6_eval):
        print(f"  {p}")

    print("Writing obstruction witness cache...")
    print(f"  {write_e6_t22_witness_cache(e6_eval)}")


if __name__ == "__main__":
    main()
