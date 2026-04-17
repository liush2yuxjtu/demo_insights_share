from __future__ import annotations

import sys
from pathlib import Path


DEMO_CODES = Path(__file__).resolve().parents[1] / "demo_codes"

if str(DEMO_CODES) not in sys.path:
    sys.path.insert(0, str(DEMO_CODES))
