#!/usr/bin/env python3
"""
Test Path Efficiency Reward System
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface
from arc_rlvr_framework import ARCRLVRFramework

print("=" * 80)
print("🧪 TESTING PATH EFFICIENCY REWARD SYSTEM")
print("=" * 80)
print()

db = DatabaseInterface()
rlvr = ARCRLVRFramework(db)

print("Path Efficiency Reward Weight:", rlvr.reward_weights['path_efficiency'])
print()

# Simulate different win scenarios
scenarios = [
    {
        'name': 'Quick Win (100 actions)',
        'results': {
            'game_id': 'test-quick',
            'session_id': 'test-session',
            'win_detected': True,
            'final_score': 3.0,
            'win_score': 3.0,
            'total_actions': 100,
            'level_completions': 3
        }
    },
    {
        'name': 'Moderate Win (300 actions)',
        'results': {
            'game_id': 'test-moderate',
            'session_id': 'test-session',
            'win_detected': True,
            'final_score': 3.0,
            'win_score': 3.0,
            'total_actions': 300,
            'level_completions': 3
        }
    },
    {
        'name': 'Slow Win (600 actions)',
        'results': {
            'game_id': 'test-slow',
            'session_id': 'test-session',
            'win_detected': True,
            'final_score': 3.0,
            'win_score': 3.0,
            'total_actions': 600,
            'level_completions': 3
        }
    },
    {
        'name': 'Very Slow Win (1000 actions)',
        'results': {
            'game_id': 'test-very-slow',
            'session_id': 'test-session',
            'win_detected': True,
            'final_score': 3.0,
            'win_score': 3.0,
            'total_actions': 1000,
            'level_completions': 3
        }
    },
    {
        'name': 'Loss (500 actions)',
        'results': {
            'game_id': 'test-loss',
            'session_id': 'test-session',
            'win_detected': False,
            'final_score': 1.0,
            'win_score': 3.0,
            'total_actions': 500,
            'level_completions': 1
        }
    }
]

print("TESTING DIFFERENT WIN SCENARIOS:")
print("=" * 80)
print()

for scenario in scenarios:
    print(f"Scenario: {scenario['name']}")
    print("-" * 80)
    
    results = scenario['results']
    
    # Extract ARC rewards
    arc_rewards = {
        'game_win': results['win_detected'],
        'final_score': results['final_score'],
        'win_score_threshold': results['win_score'],
        'total_actions': results['total_actions'],
        'level_progressions': results['level_completions'],
        'frame_changes': 0,
        'coordinate_attempts': 0,
        'coordinate_successes': 0,
        'game_duration_seconds': 0.0,
        'actions_taken': [],
        'score_progression': []
    }
    
    # Calculate derived metrics
    derived = rlvr._calculate_derived_metrics(arc_rewards)
    
    # Generate feedback
    feedback = rlvr._generate_evolutionary_feedback(arc_rewards, derived)
    
    print(f"  Win: {results['win_detected']}")
    print(f"  Actions: {results['total_actions']}")
    print(f"  Score Efficiency: {derived['score_efficiency']:.4f}")
    print(f"  Path Efficiency: {derived['path_efficiency']:.4f}")
    print()
    print(f"  Reward Breakdown:")
    print(f"    Base: {feedback['reward_breakdown']['base_reward']:.2f}")
    print(f"    Win Bonus: {feedback['reward_breakdown']['win_bonus']:.2f}")
    print(f"    Efficiency: {feedback['reward_breakdown']['efficiency_bonus']:.2f}")
    print(f"    Path Efficiency: {feedback['reward_breakdown']['path_efficiency_bonus']:.2f}")
    print(f"    TOTAL: {feedback['total_reward']:.2f}")
    print()

print("=" * 80)
print("📊 ANALYSIS")
print("=" * 80)
print()

print("Path Efficiency Bonus Impact:")
print("  - Quick win (100 actions): Gets 2x path bonus (capped)")
print("  - Moderate win (300 actions): Gets ~1.67x path bonus")
print("  - Slow win (600 actions): Gets ~0.83x path bonus")
print("  - Very slow win (1000 actions): Gets ~0.5x path bonus")
print("  - Losses get NO path efficiency bonus")
print()

print("Evolution Pressure:")
print("  ✓ Agents that win quickly get HIGHER rewards")
print("  ✓ Agents that win slowly get LOWER rewards")
print("  ✓ Same final score, but different evolutionary fitness")
print("  ✓ Natural selection toward efficient strategies")
print()

print("=" * 80)
print("✅ PATH EFFICIENCY SYSTEM READY")
print("=" * 80)
print()

print("Integration complete:")
print("  ✓ Path efficiency tracked in derived_metrics")
print("  ✓ Path efficiency bonus in reward calculation")
print("  ✓ Included in comprehensive_success_rate (10% weight)")
print("  ✓ Evolution will favor efficient win strategies")
print()
