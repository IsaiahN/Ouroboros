#!/usr/bin/env python3
"""
Analyze game data to recommend optimal action limits
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface

print("=" * 80)
print("🔍 ANALYZING GAME DATA FOR OPTIMAL ACTION LIMITS")
print("=" * 80)
print()

db = DatabaseInterface()

# Get comprehensive game statistics
games = db.execute_query("""
    SELECT 
        gr.game_id,
        gr.status,
        gr.total_actions,
        gr.final_score,
        ap.level_progressions,
        ap.win_achieved
    FROM game_results gr
    JOIN agent_arc_performance ap ON gr.game_id = ap.game_id
    ORDER BY gr.end_time DESC
    LIMIT 100
""")

if not games:
    print("No game data available")
    exit()

print(f"Analyzing last {len(games)} games...")
print()

# Categorize games
wins = [g for g in games if g['win_achieved']]
level_completions = [g for g in games if g['level_progressions'] > 0]
score_achievements = [g for g in games if g['final_score'] > 0]
zero_progress = [g for g in games if g['final_score'] == 0 and g['level_progressions'] == 0]

print("📊 GAME OUTCOMES:")
print("-" * 80)
print(f"Total games: {len(games)}")
print(f"Wins: {len(wins)} ({len(wins)/len(games)*100:.1f}%)")
print(f"Level completions: {len(level_completions)} ({len(level_completions)/len(games)*100:.1f}%)")
print(f"Score achievements: {len(score_achievements)} ({len(score_achievements)/len(games)*100:.1f}%)")
print(f"Zero progress: {len(zero_progress)} ({len(zero_progress)/len(games)*100:.1f}%)")
print()

# Analyze action counts
all_actions = [g['total_actions'] for g in games]
avg_actions = sum(all_actions) / len(all_actions)
min_actions = min(all_actions)
max_actions = max(all_actions)
median_actions = sorted(all_actions)[len(all_actions)//2]

print("⏱️  ACTION COUNT STATISTICS:")
print("-" * 80)
print(f"Average actions per game: {avg_actions:.0f}")
print(f"Median actions per game: {median_actions}")
print(f"Min actions: {min_actions}")
print(f"Max actions: {max_actions}")
print()

# Analyze by outcome
if score_achievements:
    score_actions = [g['total_actions'] for g in score_achievements]
    avg_score_actions = sum(score_actions) / len(score_actions)
    print(f"Games with score > 0 averaged: {avg_score_actions:.0f} actions")
else:
    print("No games with scores > 0")

if zero_progress:
    zero_actions = [g['total_actions'] for g in zero_progress]
    avg_zero_actions = sum(zero_actions) / len(zero_actions)
    print(f"Games with zero progress averaged: {avg_zero_actions:.0f} actions")
print()

# Action distribution
print("📈 ACTION DISTRIBUTION:")
print("-" * 80)
ranges = [
    (0, 200, "0-200"),
    (200, 400, "200-400"),
    (400, 600, "600-800"),
    (600, 800, "600-800"),
    (800, 1000, "800-1000"),
    (1000, 1500, "1000-1500"),
    (1500, 3000, "1500-3000"),
    (3000, 10000, "3000+")
]

for min_a, max_a, label in ranges:
    count = len([g for g in games if min_a <= g['total_actions'] < max_a])
    if count > 0:
        with_score = len([g for g in games if min_a <= g['total_actions'] < max_a and g['final_score'] > 0])
        print(f"{label:12s}: {count:3d} games ({count/len(games)*100:5.1f}%) - {with_score} with score")

print()

# Analyze score vs actions correlation
print("🎯 SCORE vs ACTIONS CORRELATION:")
print("-" * 80)

# Games that got scores
if score_achievements:
    quick_scores = [g for g in score_achievements if g['total_actions'] < 500]
    slow_scores = [g for g in score_achievements if g['total_actions'] >= 500]
    
    print(f"Scores achieved in <500 actions: {len(quick_scores)} games")
    print(f"Scores achieved in ≥500 actions: {len(slow_scores)} games")
    
    if quick_scores:
        avg_quick = sum(g['total_actions'] for g in quick_scores) / len(quick_scores)
        avg_quick_score = sum(g['final_score'] for g in quick_scores) / len(quick_scores)
        print(f"  Quick scores avg: {avg_quick:.0f} actions, {avg_quick_score:.2f} score")
    
    if slow_scores:
        avg_slow = sum(g['total_actions'] for g in slow_scores) / len(slow_scores)
        avg_slow_score = sum(g['final_score'] for g in slow_scores) / len(slow_scores)
        print(f"  Slow scores avg: {avg_slow:.0f} actions, {avg_slow_score:.2f} score")

print()

# Check for games hitting limits
games_at_limit = [g for g in games if g['total_actions'] >= 2000]
print(f"Games hitting high limits (≥2000 actions): {len(games_at_limit)} ({len(games_at_limit)/len(games)*100:.1f}%)")

print()
print("=" * 80)
print("💡 RECOMMENDATIONS")
print("=" * 80)
print()

# Calculate optimal limits based on data
percentile_75 = sorted(all_actions)[int(len(all_actions) * 0.75)]
percentile_90 = sorted(all_actions)[int(len(all_actions) * 0.90)]

print("CURRENT SETTINGS:")
print("  - max_actions_per_level: 200")
print("  - max_total_actions: 1500")
print()

print("DATA INSIGHTS:")
print()

# Are games reaching limits?
games_near_limit = len([g for g in games if g['total_actions'] > 1000])
if games_near_limit > len(games) * 0.2:  # >20% hitting high limits
    print(f"⚠️  {games_near_limit} games ({games_near_limit/len(games)*100:.1f}%) using >1000 actions")
    print("   Many games are exploring extensively")
    print("   → Consider keeping higher limits to allow thorough exploration")
else:
    print(f"✓ Only {games_near_limit} games ({games_near_limit/len(games)*100:.1f}%) using >1000 actions")
    print("   Most games complete or fail before hitting limits")

print()

# Score achievement timing
if score_achievements:
    early_score_ratio = len([g for g in score_achievements if g['total_actions'] < 800]) / len(score_achievements)
    if early_score_ratio > 0.7:  # >70% scores come early
        print(f"✓ {early_score_ratio*100:.1f}% of scores achieved in <800 actions")
        print("   Success happens relatively quickly when it happens")
        print("   → Could reduce max_total_actions to 800-1000 for efficiency")
    else:
        print(f"⚠️  Only {early_score_ratio*100:.1f}% of scores achieved in <800 actions")
        print("   Scores require extended exploration")
        print("   → Keep higher limits to allow breakthrough discoveries")

print()

# Level action limit
if level_completions:
    print("LEVEL PROGRESSION:")
    multi_level = len([g for g in games if g['level_progressions'] > 1])
    print(f"  Games completing multiple levels: {multi_level}")
    if multi_level > 0:
        print("  → 200 actions per level seems reasonable for level completion")
    else:
        print("  → Consider increasing max_actions_per_level to give more time per level")

print()
print("=" * 80)
print("🎯 FINAL RECOMMENDATION")
print("=" * 80)
print()

# Final recommendation based on data
if avg_actions < 800 and len(games_at_limit) < len(games) * 0.1:
    print("RECOMMENDATION: REDUCE LIMITS FOR EFFICIENCY")
    print()
    print("  max_actions_per_level: 150-200 (current: 200) ✓")
    print("  max_total_actions: 800-1000 (current: 1500) ↓")
    print()
    print("REASONING:")
    print(f"  - Average game uses only {avg_actions:.0f} actions")
    print(f"  - 75th percentile: {percentile_75} actions")
    print(f"  - Very few games benefit from 1500+ action limit")
    print(f"  - Faster games = more training iterations = faster evolution")
    
elif len(games_at_limit) > len(games) * 0.3:
    print("RECOMMENDATION: INCREASE LIMITS FOR EXPLORATION")
    print()
    print("  max_actions_per_level: 250-300 (current: 200) ↑")
    print("  max_total_actions: 2000-2500 (current: 1500) ↑")
    print()
    print("REASONING:")
    print(f"  - Many games hitting upper limits ({len(games_at_limit)} games)")
    print(f"  - Agents need more time to find solutions")
    print(f"  - Complex puzzles may require extensive exploration")
    
else:
    print("RECOMMENDATION: KEEP CURRENT LIMITS")
    print()
    print("  max_actions_per_level: 200 ✓")
    print("  max_total_actions: 1000-1200 (current: 1500) ↓ slightly")
    print()
    print("REASONING:")
    print(f"  - Average game uses {avg_actions:.0f} actions")
    print(f"  - Current limits allow adequate exploration")
    print(f"  - Small reduction to 1000-1200 would speed up training")
    print(f"  - 90th percentile uses only {percentile_90} actions")

print()
print("=" * 80)
