"""
conftest.py

Pytest configuration for cubic-jordan.

Adds trivalent-graphs/src to sys.path so that tests can import
algebra, combinatorics, rewriting, theory, and closed_graphs modules
without explicit path manipulation in each test file.
"""

import sys
from pathlib import Path

_TRIVALENT_SRC = Path(__file__).resolve().parent.parent / "trivalent-graphs" / "src"
if str(_TRIVALENT_SRC) not in sys.path:
    sys.path.insert(0, str(_TRIVALENT_SRC))
