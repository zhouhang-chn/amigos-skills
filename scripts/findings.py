#!/usr/bin/env python3
"""Thin wrapper: `python scripts/findings.py ...` == `amigos findings ...`."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from amigos.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main(["findings", *sys.argv[1:]]))
