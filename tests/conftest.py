"""
Pytest configuration for the Ouroboros test suite.

This conftest properly sets up sys.path to import modules directly
without triggering the root __init__.py which uses relative imports.
"""

import os
import sys
from pathlib import Path

# Disable pycache - per project rules
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

# Add the project root to sys.path BEFORE pytest collects tests
# This allows tests to import modules directly (e.g., from trigger_controller import ...)
# without going through the package's __init__.py
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def _find_pycache(root: str):
    for dirpath, dirnames, _ in os.walk(root):
        parts = set(dirpath.split(os.sep))
        if '.venv' in parts or '.git' in parts:
            continue
        for d in list(dirnames):
            if d == "__pycache__":
                yield os.path.join(dirpath, d)


def pytest_sessionfinish(session, exitstatus):
    """Fail the session if any __pycache__ directories remain after tests."""
    pycaches = list(_find_pycache(project_root))
    if not pycaches:
        return

    # Attempt cleanup first
    for path in pycaches:
        try:
            import shutil
            shutil.rmtree(path, ignore_errors=True)
        except Exception:
            pass

    remaining = [p for p in pycaches if Path(p).exists()]
    if remaining:
        import pytest as _pytest
        _pytest.exit(
            f"Detected __pycache__ inside repo (enforce PYTHONDONTWRITEBYTECODE=1):\n{os.linesep.join(sorted(remaining))}\nRemove them and rerun."
        )
    else:
        print(f"Removed __pycache__ directories:{os.linesep}{os.linesep.join(sorted(pycaches))}")
