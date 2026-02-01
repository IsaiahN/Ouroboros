import os
import sys
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: No pycache
sys.dont_write_bytecode = True

"""
Test Theory-Gated Scoring Implementation

Verifies that the MOST CRITICAL constraint from the architecture documents
is working correctly - every action should be scored against the working theory.
"""

import sqlite3

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engines.reasoning.scientific_method_engine import ScientificMethodEngine, Theory, TheoryStatus, TheoryType
from datetime import datetime


def test_theory_gating():
    """Test that theory-gated scoring works correctly."""
    print("=" * 60)
    print("THEORY-GATED SCORING TEST")
    print("=" * 60)
    
    # Create a test database
    conn = sqlite3.connect(':memory:')
    
    # Initialize engine
    engine = ScientificMethodEngine(conn)
    
    # Create a test theory in CONFIDENT state
    theory = Theory(
        theory_id='test_theory_1',
        description='Blue objects move with directional actions',
        theory_type=TheoryType.ACTION_EFFECT,  # Use enum, not string
        game_type='test_game',
        level_number=1,
        formal_statement={'action': 'ACTION1', 'consequence': 'progress'},
        status=TheoryStatus.SUPPORTED,
        confidence=0.8
    )
    theory.tests_conducted = 5
    theory.tests_successful = 4
    engine._active_theories['test_theory_1'] = theory
    
    # Test 1: get_working_theory returns correct stage
    print("\n[TEST 1] Get working theory stage")
    wt = engine.get_working_theory('test_game', 1)
    stage = wt.get('stage') if wt else None
    print(f"  Working theory stage: {stage}")
    print(f"  Working theory confidence: {wt.get('confidence') if wt else 'N/A'}")
    assert stage in ('confident', 'partial_confirmation'), f"Expected confident/partial_confirmation, got {stage}"
    print("  [OK] Stage is correct")
    
    # Test 2: score_action_with_theory rewards theory-aligned actions
    print("\n[TEST 2] Score theory-aligned vs non-aligned actions")
    score1 = engine.score_action_with_theory('ACTION1', 'test_game', 1)
    score6 = engine.score_action_with_theory('ACTION6', 'test_game', 1)
    print(f"  Score for ACTION1 (theory action): {score1:+.3f}")
    print(f"  Score for ACTION6 (non-theory action): {score6:+.3f}")
    assert score1 > score6, f"Theory action should score higher: {score1} vs {score6}"
    print("  [OK] Theory-aligned action scores higher")
    
    # Test 3: Contradicted theory penalizes original action
    print("\n[TEST 3] Contradicted theory behavior")
    theory.contradicting_observations.append('test contradiction 1')
    theory.contradicting_observations.append('test contradiction 2')
    theory.supporting_observations = []  # Clear supports
    theory.status = TheoryStatus.REFUTED
    
    wt2 = engine.get_working_theory('test_game', 1)
    stage2 = wt2.get('stage') if wt2 else None
    print(f"  After contradiction - Stage: {stage2}")
    assert stage2 == 'contradicted', f"Expected contradicted, got {stage2}"
    
    score_contradicted = engine.score_action_with_theory('ACTION1', 'test_game', 1)
    score_explore = engine.score_action_with_theory('ACTION6', 'test_game', 1)
    print(f"  Score for ACTION1 (contradicted theory action): {score_contradicted:+.3f}")
    print(f"  Score for ACTION6 (exploration): {score_explore:+.3f}")
    assert score_contradicted < 0, f"Contradicted action should be negative: {score_contradicted}"
    assert score_explore > score_contradicted, f"Exploration should score higher than contradicted: {score_explore} vs {score_contradicted}"
    print("  [OK] Contradicted theory penalizes original action")
    
    # Test 4: No theory means exploration is boosted
    # When no active theories AND no game_type provided, the function returns early
    # with exploration scoring 0.1 and other actions scoring 0.0
    print("\n[TEST 4] No theory behavior (exploration boosted)")
    engine._active_theories.clear()
    
    # Call with empty game_type to avoid database query (tests the "no active theories" branch)
    score_no_theory_explore = engine.score_action_with_theory('ACTION6', '', 0)
    score_no_theory_action = engine.score_action_with_theory('ACTION1', '', 0)
    print(f"  Score for ACTION6 (no theory, exploration): {score_no_theory_explore:+.3f}")
    print(f"  Score for ACTION1 (no theory, directional): {score_no_theory_action:+.3f}")
    assert score_no_theory_explore >= score_no_theory_action, \
        f"Exploration should be >= other actions when no theory: {score_no_theory_explore} vs {score_no_theory_action}"
    assert score_no_theory_explore == 0.1, f"ACTION6 should get +0.1 boost: {score_no_theory_explore}"
    assert score_no_theory_action == 0.0, f"ACTION1 should be neutral (0.0): {score_no_theory_action}"
    print("  [OK] Exploration boosted when no theory")
    
    print("\n" + "=" * 60)
    print("ALL THEORY-GATING TESTS PASSED!")
    print("=" * 60)
    
    conn.close()


if __name__ == '__main__':
    test_theory_gating()
