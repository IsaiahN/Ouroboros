@echo off
REM BitterTruth-AI Game Runner (Windows)
REM Runs the game with Python bytecode compilation disabled

set PYTHONDONTWRITEBYTECODE=1
python start_game.py %*