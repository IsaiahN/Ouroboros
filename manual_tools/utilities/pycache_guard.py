from __future__ import annotations

"""Runtime/CI guard to enforce no __pycache__ and bytecode suppression.

Use: PYTHONDONTWRITEBYTECODE=1 python -B pycache_guard.py
Exits non-zero if any __pycache__ directory is found under repo root.
"""

import os
import sys
from pathlib import Path


def scan_for_pycache(root: Path) -> list[Path]:
    found = []
    for dirpath, dirnames, _ in os.walk(root):
        # Skip virtual envs and VCS metadata
        parts = Path(dirpath).parts
        if any(part in {'.git', '.venv', 'env', 'node_modules'} for part in parts):
            dirnames[:] = []
            continue
        for d in dirnames:
            if d == "__pycache__":
                found.append(Path(dirpath) / d)
    return found


def main() -> int:
    root = Path(__file__).resolve().parent
    hits = scan_for_pycache(root)
    if hits:
        print("Found __pycache__ directories:")
        for h in hits:
            print(f" - {h}")
        return 1
    print("[OK] No __pycache__ directories detected")
    return 0


if __name__ == "__main__":
    sys.exit(main())
