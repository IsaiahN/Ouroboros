#!/bin/bash
# BitterTruth-AI Game Runner (Unix/Linux/macOS)
# Runs the game with Python bytecode compilation disabled

export PYTHONDONTWRITEBYTECODE=1
python3 start_game.py "$@"