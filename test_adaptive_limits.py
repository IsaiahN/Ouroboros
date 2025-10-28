#!/usr/bin/env python3
"""
Test Adaptive Action Limits
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface
from adaptive_action_limits import AdaptiveActionLimits

print("=" * 80)
print("🧪 TESTING ADAPTIVE ACTION LIMITS")
print("=" * 80)
print()

db = DatabaseInterface()
adaptive = AdaptiveActionLimits(db)

# Check current generation
max_gen = db.execute_query("SELECT MAX(generation) as max_gen FROM agents")
current_gen = max_gen[0]['max_gen'] if max_gen and max_gen[0]['max_gen'] is not None else 0

print(f"Current generation in database: {current_gen}")
print()

# Test adjustments for each generation
for gen in range(max(0, current_gen - 2), current_gen + 2):
    print(f"\n{'='*80}")
    print(f"Testing Generation {gen}")
    print(f"{'='*80}")
    
    # Get performance
    perf = adaptive.calculate_generation_performance(gen)
    
    print(f"\nGeneration {gen} Performance:")
    print(f"  Comprehensive Success: {perf['comprehensive_success']:.2%}")
    print(f"  Avg Actions Used: {perf['avg_actions_used']:.0f}")
    print(f"  Score Rate: {perf['score_rate']:.2%}")
    print(f"  Efficiency: {perf['efficiency']:.6f}")
    print(f"  Sample Size: {perf['sample_size']} games")
    
    # Adjust limits
    actions_per_level, total_actions = adaptive.adjust_limits(gen)
    
    print(f"\nAdjusted Limits for Gen {gen}:")
    print(f"  Actions per level: {actions_per_level}")
    print(f"  Total actions: {total_actions}")

print()
print("=" * 80)
print("✅ ADAPTIVE LIMITS TEST COMPLETE")
print("=" * 80)
print()

print("System will dynamically adjust action limits based on:")
print("  ✓ Comprehensive success rate (wins, levels, scores)")
print("  ✓ Performance trends (improving vs declining)")
print("  ✓ Action utilization (not wasting time)")
print("  ✓ Hard floor: 200 actions/level minimum")
print()

print("Higher success → More time to explore")
print("Low success → Less time (faster evolution cycles)")
print()
