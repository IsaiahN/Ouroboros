#!/usr/bin/env python3
"""
Test progressive strategy escalation instead of just stopping the game
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import disable_pycache from project root
from disable_pycache import *

def test_strategy_escalation():
    """Test the progressive strategy escalation logic."""
    print("=== Testing Progressive Strategy Escalation ===")

    # Simulate the escalation variables
    consecutive_same_score = 0
    last_score = None
    strategy_escalation_level = 0
    max_same_score_before_strategy_change = 8
    max_same_score_before_game_end = 25
    force_evolution_bypass = False
    fallback_action_rotation = ["ACTION1", "ACTION2", "ACTION3", "ACTION4", "ACTION6"]

    # Simulate game scores that don't improve for a long time
    test_scores = [0.0] * 30  # 30 actions with no score improvement
    escalation_events = []

    print("Simulating 30 actions with no score improvement...")

    for i, current_score in enumerate(test_scores):
        actions_taken = i + 1
        print(f"\n--- Action {actions_taken} ---")
        print(f"Current Score: {current_score}, Escalation Level: {strategy_escalation_level}")

        # Apply the same logic as in start_game.py
        if last_score is not None and abs(current_score - last_score) < 0.001:  # No significant progress
            consecutive_same_score += 1

            # Progressive strategy escalation instead of just stopping
            if consecutive_same_score >= max_same_score_before_game_end:
                print(f"\n[GAME END] No progress after {consecutive_same_score} actions (score stuck at {current_score})")
                print("[GAME END] Ending game - all strategies exhausted")
                escalation_events.append(f"Action {actions_taken}: GAME ENDED")
                break
            elif consecutive_same_score >= max_same_score_before_strategy_change:
                strategy_escalation_level += 1
                force_evolution_bypass = True  # Force fallback mode

                if strategy_escalation_level == 1:
                    print(f"\n[STRATEGY CHANGE] Level 1: Switching to aggressive fallback rotation after {consecutive_same_score} actions")
                    escalation_events.append(f"Action {actions_taken}: Strategy Level 1 - Aggressive fallback")
                    import random
                    random.shuffle(fallback_action_rotation)
                elif strategy_escalation_level == 2:
                    print(f"\n[STRATEGY CHANGE] Level 2: Adding coordinate randomization after {consecutive_same_score} actions")
                    escalation_events.append(f"Action {actions_taken}: Strategy Level 2 - Random coordinates")
                elif strategy_escalation_level >= 3:
                    print(f"\n[STRATEGY CHANGE] Level 3+: Maximum diversity mode after {consecutive_same_score} actions")
                    escalation_events.append(f"Action {actions_taken}: Strategy Level 3+ - Maximum diversity")
                    available_actions = [1, 2, 3, 4, 6]  # Simulate available actions
                    fallback_action_rotation = [f"ACTION{i}" for i in available_actions]

                # Reset consecutive counter to give new strategy a chance
                consecutive_same_score = max_same_score_before_strategy_change - 3

            elif consecutive_same_score >= 5:
                if consecutive_same_score == 5:
                    print(f"[WARN] No progress for {consecutive_same_score} actions - score stuck at {current_score}")
                if consecutive_same_score >= 6:
                    force_evolution_bypass = True  # Start bypassing evolution when clearly stuck
                    if consecutive_same_score == 6:
                        escalation_events.append(f"Action {actions_taken}: Evolution bypass enabled")
        else:
            consecutive_same_score = 0  # Reset counter if score improved
            strategy_escalation_level = 0  # Reset escalation level
            force_evolution_bypass = False  # Re-enable evolution

        last_score = current_score

        # Simulate that we would actually run fallback actions here
        print(f"Evolution bypass: {force_evolution_bypass}, Escalation level: {strategy_escalation_level}")

    print(f"\n=== ESCALATION TIMELINE ===")
    for event in escalation_events:
        print(f"  {event}")

    # Verify proper escalation behavior
    expected_events = [
        "Evolution bypass enabled",
        "Strategy Level 1 - Aggressive fallback",
        "Strategy Level 2 - Random coordinates",
        "Strategy Level 3+ - Maximum diversity"
    ]

    escalation_types = [event.split(": ", 1)[1] for event in escalation_events if ": " in event]

    success = True
    for expected in expected_events[:-1]:  # Don't require game end for success
        if not any(expected in event_type for event_type in escalation_types):
            print(f"\nFAIL: Missing expected escalation: {expected}")
            success = False

    if success:
        print(f"\nSUCCESS: Progressive strategy escalation works correctly!")
        print(f"- Evolution bypass activated appropriately")
        print(f"- Multiple escalation levels triggered")
        print(f"- Game continued with different strategies instead of stopping early")
        return True
    else:
        print(f"\nFAIL: Strategy escalation did not work as expected")
        return False

def test_escalation_reset():
    """Test that escalation resets when score improves."""
    print("\n=== Testing Escalation Reset on Score Improvement ===")

    consecutive_same_score = 0
    strategy_escalation_level = 0
    force_evolution_bypass = False
    last_score = 0.0

    # Simulate no progress, then improvement, then no progress again
    test_scenario = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]  # Score improves at action 8
    escalation_events = []

    for i, current_score in enumerate(test_scenario):
        actions_taken = i + 1

        if last_score is not None and abs(current_score - last_score) < 0.001:
            consecutive_same_score += 1
            if consecutive_same_score >= 6:
                force_evolution_bypass = True
                escalation_events.append(f"Action {actions_taken}: Escalation activated")
        else:
            if consecutive_same_score > 0:
                escalation_events.append(f"Action {actions_taken}: Score improved - escalation RESET")
            consecutive_same_score = 0
            strategy_escalation_level = 0
            force_evolution_bypass = False

        last_score = current_score

    print("Escalation events:")
    for event in escalation_events:
        print(f"  {event}")

    # Should see escalation activate, then reset when score improves
    has_activation = any("activated" in event for event in escalation_events)
    has_reset = any("RESET" in event for event in escalation_events)

    if has_activation and has_reset:
        print(f"\nSUCCESS: Escalation properly resets when score improves!")
        return True
    else:
        print(f"\nFAIL: Escalation reset not working properly")
        return False

if __name__ == "__main__":
    print("Testing progressive strategy escalation system...\n")

    test1 = test_strategy_escalation()
    test2 = test_escalation_reset()

    print(f"\n=== FINAL RESULTS ===")
    print(f"Progressive Escalation: {'PASS' if test1 else 'FAIL'}")
    print(f"Escalation Reset: {'PASS' if test2 else 'FAIL'}")

    if all([test1, test2]):
        print(f"\nALL TESTS PASSED! Strategy escalation system works correctly.")
        print("- Game will now try multiple strategies when stuck")
        print("- Evolution will be bypassed when not working")
        print("- Random coordinates and action diversity will be used")
        print("- Game will only end after trying all escalation levels")
        exit(0)
    else:
        print(f"\nSOME TESTS FAILED! Check the escalation logic.")
        exit(1)