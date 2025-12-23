"""
Pytest configuration for the Ouroboros test suite.

This conftest properly sets up sys.path to import modules directly
without triggering the root __init__.py which uses relative imports.
"""

import os
import sys

# Disable pycache - per project rules
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

# Add the project root to sys.path BEFORE pytest collects tests
# This allows tests to import modules directly (e.g., from trigger_controller import ...)
# without going through the package's __init__.py
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
