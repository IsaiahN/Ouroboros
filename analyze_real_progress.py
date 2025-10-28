#!/usr/bin/env python3
"""
Deep Progress Analysis - Is Real Learning Happening?
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface
from performance_analyzer import PerformanceAnalyzer
from datetime import datetime, timedelta

print("=" * 80)
print("🔬 DEEP PROGRESS ANALYSIS")
print("=" * 80)
print()

db = DatabaseInterface()
analyzer = PerformanceAnalyzer(db)

# 1. Generation-over-Generation Comparison
print("📊 GENERATION COMPARISON - Is Evolution Improving?")
print("-" * 80)

gen_performance = db.execute_query("""
    SELECT 
        a.generation,
        COUNT(DISTINCT a.agent_id) as agent_count,
        COUNT(DISTINCT ap.performance_id) as total_games,
        AVG(ap.final_score) as avg_score,
        AVG(ap.score_efficiency) as avg_efficiency,
        AVG(ap.win_proximity) as avg_win_proximity,
        SUM(ap.level_progressions) as total_level_progs,
        SUM(CASE WHEN ap.win_achieved THEN 1 ELSE 0 END) as wins
    FROM agents a
    LEFT JOIN agent_arc_performance ap ON a.agent_id = ap.agent_id
    WHERE a.is_active = 1
    GROUP BY a.generation
    ORDER BY a.generation
""")

print()
print("Gen | Agents | Games | Avg Score | Efficiency | Win Prox | Levels | Wins")
print("-" * 80)
for gen in gen_performance:
    print(f" {gen['generation']:2d} |   {gen['agent_count']:2d}   | {gen['total_games']:5d} | "
          f"  {gen['avg_score']:.4f}  |  {gen['avg_efficiency']:.6f} | "
          f" {gen['avg_win_proximity']:.4f}  |   {gen['total_level_progs']:2d}   |  {gen['wins']:2d}")

# Calculate trend
if len(gen_performance) > 1:
    gen0_score = gen_performance[0]['avg_score']
    latest_score = gen_performance[-1]['avg_score']
    
    gen0_efficiency = gen_performance[0]['avg_efficiency']
    latest_efficiency = gen_performance[-1]['avg_efficiency']
    
    gen0_proximity = gen_performance[0]['avg_win_proximity']
    latest_proximity = gen_performance[-1]['avg_win_proximity']
    
    print()
    print("📈 EVOLUTION TREND:")
    if latest_score > gen0_score:
        improvement = ((latest_score - gen0_score) / max(gen0_score, 0.0001)) * 100
        print(f"  ✓ Score improving: Gen-0 {gen0_score:.4f} → Gen-{len(gen_performance)-1} {latest_score:.4f} (+{improvement:.1f}%)")
    else:
        print(f"  ○ Score stable: {gen0_score:.4f} → {latest_score:.4f}")
    
    if latest_efficiency > gen0_efficiency:
        print(f"  ✓ Efficiency improving: {gen0_efficiency:.6f} → {latest_efficiency:.6f}")
    else:
        print(f"  ○ Efficiency stable: {gen0_efficiency:.6f} → {latest_efficiency:.6f}")
    
    if latest_proximity > gen0_proximity:
        improvement = ((latest_proximity - gen0_proximity) / max(gen0_proximity, 0.0001)) * 100
        print(f"  ✓ Win proximity improving: {gen0_proximity:.4f} → {latest_proximity:.4f} (+{improvement:.1f}%)")
    else:
        print(f"  ○ Win proximity: {gen0_proximity:.4f} → {latest_proximity:.4f}")

# 2. Time-based Progress
print()
print("=" * 80)
print("⏱️  TIME-BASED PROGRESS - Are We Getting Better?")
print("-" * 80)

time_buckets = db.execute_query("""
    WITH time_periods AS (
        SELECT 
            CASE 
                WHEN game_timestamp >= datetime('now', '-10 minutes') THEN 'Last 10 min'
                WHEN game_timestamp >= datetime('now', '-30 minutes') THEN 'Last 30 min'
                WHEN game_timestamp >= datetime('now', '-1 hour') THEN 'Last 1 hour'
                ELSE 'Earlier'
            END as period,
            final_score,
            score_efficiency,
            win_proximity,
            level_progressions,
            win_achieved
        FROM agent_arc_performance
    )
    SELECT 
        period,
        COUNT(*) as games,
        AVG(final_score) as avg_score,
        AVG(score_efficiency) as avg_efficiency,
        AVG(win_proximity) as avg_win_proximity,
        SUM(level_progressions) as level_progs,
        SUM(CASE WHEN win_achieved THEN 1 ELSE 0 END) as wins
    FROM time_periods
    GROUP BY period
    ORDER BY 
        CASE period
            WHEN 'Last 10 min' THEN 1
            WHEN 'Last 30 min' THEN 2
            WHEN 'Last 1 hour' THEN 3
            ELSE 4
        END
""")

print()
print("Period       | Games | Avg Score | Efficiency | Win Prox | Levels | Wins")
print("-" * 80)
for bucket in time_buckets:
    print(f"{bucket['period']:12s} | {bucket['games']:5d} | {bucket['avg_score']:9.4f} | "
          f"{bucket['avg_efficiency']:10.6f} | {bucket['avg_win_proximity']:8.4f} | "
          f"  {bucket['level_progs']:4d} |  {bucket['wins']:2d}")

# 3. Individual Agent Improvement
print()
print("=" * 80)
print("👤 TOP AGENT DETAILED ANALYSIS")
print("-" * 80)

# Get top 3 agents by comprehensive success
top_agents = []
for agent in db.get_active_agents()[:5]:
    success = analyzer.calculate_comprehensive_success_rate(agent['agent_id'])
    if success['total_games'] > 0:
        top_agents.append({
            'agent_id': agent['agent_id'],
            'agent_type': agent['agent_type'],
            'generation': agent['generation'],
            'success': success
        })

top_agents.sort(key=lambda x: x['success']['comprehensive_success_rate'], reverse=True)

for i, agent_info in enumerate(top_agents[:3], 1):
    agent_id = agent_info['agent_id']
    success = agent_info['success']
    
    print(f"\n{i}. {agent_id} (Gen-{agent_info['generation']} {agent_info['agent_type']})")
    print(f"   Comprehensive Success: {success['comprehensive_success_rate']:.2%}")
    print(f"   Games: {success['total_games']}, Wins: {success['game_wins']}, "
          f"Levels: {success['level_completions']}, Scores: {success['score_achievements']}")
    
    # Get game-by-game progression
    progression = db.execute_query("""
        SELECT 
            final_score,
            score_efficiency,
            win_proximity,
            level_progressions,
            game_timestamp
        FROM agent_arc_performance
        WHERE agent_id = ?
        ORDER BY game_timestamp ASC
        LIMIT 20
    """, (agent_id,))
    
    if len(progression) > 5:
        # Check if improving over time
        first_5 = progression[:5]
        last_5 = progression[-5:]
        
        avg_score_first = sum(g['final_score'] for g in first_5) / len(first_5)
        avg_score_last = sum(g['final_score'] for g in last_5) / len(last_5)
        
        avg_proximity_first = sum(g['win_proximity'] for g in first_5) / len(first_5)
        avg_proximity_last = sum(g['win_proximity'] for g in last_5) / len(last_5)
        
        print(f"   First 5 games: Score {avg_score_first:.4f}, Proximity {avg_proximity_first:.4f}")
        print(f"   Last 5 games:  Score {avg_score_last:.4f}, Proximity {avg_proximity_last:.4f}")
        
        if avg_score_last > avg_score_first * 1.1:
            improvement = ((avg_score_last - avg_score_first) / max(avg_score_first, 0.0001)) * 100
            print(f"   ✓ IMPROVING: +{improvement:.1f}% score increase")
        elif avg_proximity_last > avg_proximity_first * 1.1:
            print(f"   ✓ IMPROVING: Getting closer to wins")
        else:
            print(f"   ○ Stable performance (learning may be plateauing)")

# 4. Action Diversity Analysis
print()
print("=" * 80)
print("🎯 ACTION DIVERSITY - Are Agents Exploring?")
print("-" * 80)

action_diversity = db.execute_query("""
    SELECT 
        a.generation,
        COUNT(DISTINCT ap.action_sequence) as unique_sequences,
        COUNT(*) as total_games,
        CAST(COUNT(DISTINCT ap.action_sequence) AS FLOAT) / COUNT(*) as diversity_ratio
    FROM agents a
    JOIN agent_arc_performance ap ON a.agent_id = ap.agent_id
    WHERE a.is_active = 1 AND ap.action_sequence IS NOT NULL
    GROUP BY a.generation
    ORDER BY a.generation
""")

print()
print("Gen | Games | Unique Sequences | Diversity Ratio")
print("-" * 80)
for div in action_diversity:
    print(f" {div['generation']:2d} | {div['total_games']:5d} |      {div['unique_sequences']:5d}      | {div['diversity_ratio']:7.3f}")

# 5. Recent Best Scores
print()
print("=" * 80)
print("🏆 BEST RECENT PERFORMANCES")
print("-" * 80)

best_scores = db.execute_query("""
    SELECT 
        ap.agent_id,
        a.generation,
        a.agent_type,
        ap.game_id,
        ap.final_score,
        ap.score_efficiency,
        ap.win_proximity,
        ap.level_progressions,
        ap.total_actions,
        ap.game_timestamp
    FROM agent_arc_performance ap
    JOIN agents a ON ap.agent_id = a.agent_id
    WHERE ap.game_timestamp >= datetime('now', '-1 hour')
    ORDER BY ap.final_score DESC, ap.win_proximity DESC
    LIMIT 10
""")

print()
for i, score in enumerate(best_scores, 1):
    print(f"{i:2d}. Gen-{score['generation']} {score['agent_type'][:15]:15s} | "
          f"Score: {score['final_score']:.4f} | Proximity: {score['win_proximity']:.3f} | "
          f"Efficiency: {score['score_efficiency']:.6f}")

# 6. Final Assessment
print()
print("=" * 80)
print("🎯 REAL PROGRESS ASSESSMENT")
print("=" * 80)
print()

progress_indicators = []
issues = []

# Check generation improvement
if len(gen_performance) > 1:
    if gen_performance[-1]['avg_score'] > gen_performance[0]['avg_score']:
        progress_indicators.append("✓ Newer generations scoring higher")
    else:
        issues.append("⚠ No score improvement between generations")
    
    if gen_performance[-1]['avg_win_proximity'] > gen_performance[0]['avg_win_proximity']:
        progress_indicators.append("✓ Getting closer to winning threshold")
    else:
        issues.append("⚠ Win proximity not improving")

# Check if any agent is learning
learning_agents = 0
for agent_info in top_agents[:5]:
    agent_id = agent_info['agent_id']
    progression = db.execute_query("""
        SELECT final_score FROM agent_arc_performance
        WHERE agent_id = ?
        ORDER BY game_timestamp ASC
    """, (agent_id,))
    
    if len(progression) > 10:
        first_half_avg = sum(g['final_score'] for g in progression[:len(progression)//2]) / (len(progression)//2)
        second_half_avg = sum(g['final_score'] for g in progression[len(progression)//2:]) / (len(progression) - len(progression)//2)
        
        if second_half_avg > first_half_avg * 1.1:
            learning_agents += 1

if learning_agents > 0:
    progress_indicators.append(f"✓ {learning_agents} agents showing improvement over time")
else:
    issues.append("⚠ No individual agents showing clear improvement")

# Check diversity
if action_diversity and len(action_diversity) > 1:
    if action_diversity[-1]['diversity_ratio'] > 0.3:
        progress_indicators.append("✓ Good action diversity (exploring strategies)")
    else:
        issues.append("⚠ Low action diversity (may be stuck)")

# Display results
print("POSITIVE INDICATORS:")
for indicator in progress_indicators:
    print(f"  {indicator}")

if issues:
    print()
    print("CONCERNS:")
    for issue in issues:
        print(f"  {issue}")

print()
print("=" * 80)

if len(progress_indicators) > len(issues):
    print("✅ YES, REAL PROGRESS IS BEING MADE!")
    print("   Evolution is working, agents are improving")
elif len(progress_indicators) > 0:
    print("⚠️  SOME PROGRESS, BUT SLOW")
    print("   System working but may need more time/tuning")
else:
    print("❌ LIMITED PROGRESS DETECTED")
    print("   System running but not yet showing clear improvement")

print("=" * 80)
