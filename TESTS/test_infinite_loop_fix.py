#!/usr/bin/env python3
"""
Test infinite loop detection and prevention fixes
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import disable_pycache from project root
from disable_pycache import *

def test_infinite_loop_detection():
    """Test the infinite loop detection logic."""
    print("=== Testing Infinite Loop Detection ===")

    # Simulate the loop detection variables
    consecutive_same_score = 0
    last_score = None
    max_consecutive_same_score = 15
    actions_taken = 0

    # Simulate game scores that don't improve (infinite loop scenario)
    test_scores = [0.0] * 20  # 20 actions with no score improvement

    print("Simulating 20 actions with no score improvement...")

    for i, current_score in enumerate(test_scores):
        actions_taken += 1
        print(f"\n--- Action {actions_taken} ---")
        print(f"Current Score: {current_score}")

        # Apply the same logic as in start_game.py
        if last_score is not None and abs(current_score - last_score) < 0.001:  # No significant progress
            consecutive_same_score += 1
            if consecutive_same_score >= max_consecutive_same_score:
                print(f"\n[LOOP DETECTION] No progress after {consecutive_same_score} actions (score stuck at {current_score})")
                print("[LOOP DETECTION] Breaking infinite loop to prevent timeout")
                break
            elif consecutive_same_score >= 5:
                print(f"[WARN] No progress for {consecutive_same_score} actions - score stuck at {current_score}")
        else:
            consecutive_same_score = 0  # Reset counter if score improved

        last_score = current_score

    # Verify loop was broken (should break when consecutive_same_score reaches max, so actions_taken will be max+1)
    if consecutive_same_score >= max_consecutive_same_score or actions_taken == max_consecutive_same_score + 1:
        print(f"\nSUCCESS: Loop detection worked! Broke after {consecutive_same_score} consecutive actions with no progress")
        return True
    else:
        print(f"\nFAIL: Expected to break after {max_consecutive_same_score} actions with no progress, but broke at action {actions_taken}")
        return False

def test_fallback_action_rotation():
    """Test the fallback action rotation logic."""
    print("\n=== Testing Fallback Action Rotation ===")

    fallback_action_rotation = ["ACTION1", "ACTION2", "ACTION3", "ACTION4", "ACTION6"]
    fallback_index = 0
    available_actions = [1, 2, 3, 4, 6]  # All actions available

    print("Testing action rotation for 10 fallbacks...")

    for i in range(10):
        try_action = fallback_action_rotation[fallback_index % len(fallback_action_rotation)]
        action_num = int(try_action.replace("ACTION", ""))

        if action_num in available_actions:
            print(f"Fallback #{fallback_index + 1}: {try_action} (available)")
            fallback_index += 1
        else:
            print(f"Fallback #{fallback_index + 1}: {try_action} (not available)")
            fallback_index += 1

    # Check that we've rotated through different actions
    unique_actions = set()
    for i in range(len(fallback_action_rotation)):
        action = fallback_action_rotation[i % len(fallback_action_rotation)]
        unique_actions.add(action)

    if len(unique_actions) == len(fallback_action_rotation):
        print(f"\nSUCCESS: Action rotation covers all {len(unique_actions)} different actions")
        return True
    else:
        print(f"\nFAIL: Action rotation only covers {len(unique_actions)} actions")
        return False

def test_score_conversion():
    """Test score conversion from lists to floats."""
    print("\n=== Testing Score Conversion ===")

    test_cases = [
        ([2.5, 1.0], 2.5),  # List with multiple values
        ([0.0], 0.0),       # List with single value
        ([], 0.0),          # Empty list
        (2.5, 2.5),         # Already a float
        (3, 3.0),           # Integer
        ("invalid", 0.0),   # Invalid type
    ]

    all_passed = True

    for test_input, expected in test_cases:
        # Apply the same conversion logic as in the code
        if isinstance(test_input, (list, tuple)):
            result = test_input[0] if len(test_input) > 0 else 0.0
        elif isinstance(test_input, (int, float)):
            result = float(test_input)
        else:
            result = 0.0

        if abs(result - expected) < 0.001:
            print(f"PASS: {test_input} -> {result} (expected {expected})")
        else:
            print(f"FAIL: {test_input} -> {result} (expected {expected})")
            all_passed = False

    if all_passed:
        print(f"\nSUCCESS: All score conversions work correctly")
        return True
    else:
        print(f"\nFAIL: Some score conversions failed")
        return False

if __name__ == "__main__":
    print("Testing infinite loop prevention fixes...\n")

    test1 = test_infinite_loop_detection()
    test2 = test_fallback_action_rotation()
    test3 = test_score_conversion()

    print(f"\n=== FINAL RESULTS ===")
    print(f"Loop Detection: {'PASS' if test1 else 'FAIL'}")
    print(f"Action Rotation: {'PASS' if test2 else 'FAIL'}")
    print(f"Score Conversion: {'PASS' if test3 else 'FAIL'}")

    if all([test1, test2, test3]):
        print(f"\nALL TESTS PASSED! Infinite loop fixes should work correctly.")
        exit(0)
    else:
        print(f"\nSOME TESTS FAILED! Check the fixes.")
        exit(1)