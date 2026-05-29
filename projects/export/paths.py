"""
projects.export.paths
"""

import sys
from pathlib import Path

CUBIC_JORDAN_ROOT = Path(__file__).resolve().parents[2]
RESEARCH_ROOT = CUBIC_JORDAN_ROOT.parent
TRIVALENT_GRAPHS_ROOT = RESEARCH_ROOT / "trivalent-graphs"
TRIVALENT_GRAPHS_SRC = TRIVALENT_GRAPHS_ROOT / "src"

for path in [CUBIC_JORDAN_ROOT, TRIVALENT_GRAPHS_SRC]:
    s = str(path)
    if s not in sys.path:
        sys.path.insert(0, s)
