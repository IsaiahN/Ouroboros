#!/usr/bin/env python3
"""Simulate pruning logic for seq_4d2a"""

# Sequence data
seq_id = 'seq_4d2a72bf6b2e4a21'
game_id = 'lp85-d265526edbaa'
total_actions = 1
total_score = 1.0
times_referenced = 25
success_rate = 0.0
generation_discovered = 205
current_generation = 241

# Pruning thresholds (from sequence_pruning_system.py lines 55-59)
min_attempts_before_pruning = 10
min_success_rate = 0.10  # 10%
max_action_count = 10000
min_score_threshold = 2.0
generations_grace_period = 2

# Calculate age
age_generations = current_generation - generation_discovered
print(f"Sequence: {seq_id}")
print(f"Age: {age_generations} generations")
print(f"Current Gen: {current_generation}, Discovered: {generation_discovered}")
print()

# Grace period check (line 103)
if age_generations < generations_grace_period:
    print(f"❌ SKIPPED: Grace period not met (age {age_generations} < {generations_grace_period})")
else:
    print(f"✓ Grace period passed (age {age_generations} >= {generations_grace_period})")
    print()
    
    prune_reason = None
    
    # Rule 1: Excessive actions (line 107)
    print(f"Rule 1 (Excessive Actions):")
    print(f"  {total_actions} > {max_action_count}? {total_actions > max_action_count}")
    if total_actions > max_action_count:
        prune_reason = 'excessive_actions'
        print(f"  ✓ WOULD PRUNE: {prune_reason}")
    else:
        print(f"  ❌ Not triggered")
    print()
    
    # Rule 2: Low success rate (line 113-117)
    print(f"Rule 2 (Low Success Rate):")
    print(f"  elif times_referenced >= min_attempts_before_pruning:")
    print(f"    {times_referenced} >= {min_attempts_before_pruning}? {times_referenced >= min_attempts_before_pruning}")
    
    if not prune_reason:  # This is elif in actual code
        if times_referenced >= min_attempts_before_pruning:
            print(f"    if success_rate < min_success_rate:")
            print(f"      {success_rate} < {min_success_rate}? {success_rate < min_success_rate}")
            if success_rate < min_success_rate:
                prune_reason = 'low_success_rate'
                print(f"  ✓✓✓ SHOULD PRUNE: {prune_reason}")
            else:
                print(f"  ❌ Success rate OK")
        else:
            print(f"  ❌ Not enough attempts")
    else:
        print(f"  SKIPPED (already has prune_reason: {prune_reason})")
    print()
    
    # Rule 3: Low score (line 120-123)
    print(f"Rule 3 (Low Score):")
    print(f"  elif times_referenced >= min_attempts_before_pruning:")
    
    if not prune_reason:  # This is elif in actual code
        if times_referenced >= min_attempts_before_pruning:
            print(f"    if total_score < min_score_threshold:")
            print(f"      {total_score} < {min_score_threshold}? {total_score < min_score_threshold}")
            if total_score < min_score_threshold:
                prune_reason = 'low_score'
                print(f"  ✓ WOULD PRUNE: {prune_reason}")
            else:
                print(f"  ❌ Score OK")
        else:
            print(f"  ❌ Not enough attempts")
    else:
        print(f"  SKIPPED (already has prune_reason: {prune_reason})")
    print()
    
    if prune_reason:
        print(f"✓✓✓ FINAL VERDICT: SHOULD BE PRUNED ({prune_reason})")
    else:
        print(f"❌ FINAL VERDICT: WOULD NOT BE PRUNED")
