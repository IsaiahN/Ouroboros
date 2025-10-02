#!/usr/bin/env python3
"""
Disable Python bytecode compilation globally.
This script sets the PYTHONDONTWRITEBYTECODE environment variable
and modifies Python behavior to prevent .pyc file creation.
"""

import os
import sys

# Set environment variable to disable bytecode compilation
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

# Also disable for current Python session
sys.dont_write_bytecode = True

print("Python bytecode compilation disabled")
print("PYTHONDONTWRITEBYTECODE =", os.environ.get('PYTHONDONTWRITEBYTECODE', 'Not set'))
print("sys.dont_write_bytecode =", sys.dont_write_bytecode)