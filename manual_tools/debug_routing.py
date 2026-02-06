"""Debug script to trace the answers_questions error in cognitive routing."""
import os
import sys

sys.dont_write_bytecode = True

# Ensure project root is on path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(PROJECT_ROOT)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import logging

logging.basicConfig(level=logging.ERROR, format='%(message)s')

import traceback

import engines.cognition.cognitive_router as cr

# Patch _execute_rung to trace what's happening
original_execute = cr.CognitiveRouter._execute_rung
def patched_execute(self, rung_name, game_state, rung_executor):
    result = original_execute(self, rung_name, game_state, rung_executor)
    print(f"  [EXEC] {rung_name}: type={type(result).__module__}.{type(result).__name__}, "
          f"has_answers_q={hasattr(result, 'answers_questions')}")
    return result
cr.CognitiveRouter._execute_rung = patched_execute

# Patch decide to catch errors with full traceback
original_decide = cr.CognitiveRouter.decide
def patched_decide(self, game_state, rung_executor=None):
    try:
        return original_decide(self, game_state, rung_executor)
    except Exception as e:
        print(f"\n=== FULL TRACEBACK ===")
        traceback.print_exc()
        print(f"=== END ===\n")
        raise
cr.CognitiveRouter.decide = patched_decide

from evolution_runner import main

sys.argv = ['evolution_runner.py', '--mode', 'offline', '--max-generations=1', '--game=vc33']
try:
    main()
except SystemExit:
    pass
