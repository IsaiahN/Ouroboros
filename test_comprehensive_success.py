#!/usr/bin/env python3
"""
Test Comprehensive Success Rate Calculation
Shows how game wins + level completions + score achievements are weighted
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from performance_analyzer import PerformanceAnalyzer
from database_interface import DatabaseInterface

print("=" * 80)
print("COMPREHENSIVE SUCCESS RATE - NEW METRIC")
print("=" * 80)
print()
print("Formula:")
print("  Comprehensive Success = (Game Wins × 70%) + (Level Completions × 20%) + (Score Achievements × 10%)")
print()
print("Where:")
print("  • Game Wins = Full game victories")
print("  • Level Completions = Any level progression")
print("  • Score Achievements = Reached 50%+ of win score")
print()
print("=" * 80)
print()

db = DatabaseInterface()
analyzer = PerformanceAnalyzer(db)

# Get active agents
agents = db.execute_query('SELECT agent_id FROM agents WHERE is_active = 1')

if not agents:
    print("No active agents found")
else:
    print(f"Analyzing {len(agents)} active agents:")
    print()
    
    for agent in agents[:5]:  # Show first 5
        agent_id = agent['agent_id']
        success = analyzer.calculate_comprehensive_success_rate(agent_id)
        
        print(f"Agent: {agent_id}")
        print(f"  Games Played: {success['total_games']}")
        print(f"  ├─ Game Wins: {success['game_wins']} ({success['game_win_rate']:.1%})")
        print(f"  ├─ Level Completions: {success['level_completions']} ({success['level_success_rate']:.1%})")
        print(f"  └─ Score Achievements: {success['score_achievements']} ({success['score_achievement_rate']:.1%})")
        print(f"  → Comprehensive Success: {success['comprehensive_success_rate']:.1%}")
        print()
    
    # Population average
    print("=" * 80)
    print("POPULATION ANALYSIS")
    print("=" * 80)
    
    analysis = analyzer.analyze_population_performance()
    pop_stats = analysis.get('population_stats', {})
    
    print(f"\nPopulation Size: {pop_stats.get('population_size', 0)} agents")
    print(f"\nOld Metric (Game Wins Only):")
    print(f"  Average Win Rate: {pop_stats.get('average_win_rate', 0):.2%}")
    print(f"  Best Win Rate: {pop_stats.get('best_win_rate', 0):.2%}")
    print()
    print(f"New Metric (Comprehensive Success):")
    print(f"  Average Success: {pop_stats.get('average_comprehensive_success', 0):.2%}")
    print(f"  Best Success: {pop_stats.get('best_comprehensive_success', 0):.2%}")
    print()
    print("=" * 80)
    print()
    print("✅ Evolution decisions now based on comprehensive success!")
    print("   Rewards partial progress, not just full victories")
    print("=" * 80)
