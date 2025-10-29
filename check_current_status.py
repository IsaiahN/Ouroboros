#!/usr/bin/env python3
"""
Current System Status Check
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface
from datetime import datetime, timedelta

print("=" * 80)
print("📊 CURRENT SYSTEM STATUS")
print("=" * 80)
print()

db = DatabaseInterface()

# Check database size
db_size = os.path.getsize('core_data.db') / (1024*1024)
print(f"Database Size: {db_size:.2f} MB")
print()

# Check when last game was played
last_game = db.execute_query("""
    SELECT end_time, game_id, final_score, total_actions
    FROM game_results
    ORDER BY end_time DESC
    LIMIT 1
""")

if last_game:
    print(f"Last Game Played: {last_game[0]['end_time']}")
    print(f"  Game: {last_game[0]['game_id'][:24]}")
    print(f"  Score: {last_game[0]['final_score']:.2f}")
    print(f"  Actions: {last_game[0]['total_actions']}")
    
    # Calculate time since last game
    try:
        last_time = datetime.fromisoformat(last_game[0]['end_time'].replace('Z', '+00:00'))
        time_since = datetime.now() - last_time
        hours_since = time_since.total_seconds() / 3600
        print(f"  Time since: {hours_since:.1f} hours ago")
    except:
        pass
else:
    print("No games found in database")

print()

# Current population
agents = db.get_active_agents()
print(f"Active Agents: {len(agents)}")

if agents:
    # Group by generation
    by_gen = {}
    for agent in agents:
        gen = agent['generation']
        by_gen[gen] = by_gen.get(gen, 0) + 1
    
    print("\nPopulation by Generation:")
    for gen in sorted(by_gen.keys()):
        print(f"  Gen-{gen}: {by_gen[gen]} agents")

print()

# Total games and performance
total_games = db.execute_query("SELECT COUNT(*) as c FROM game_results")[0]['c']
print(f"Total Games Played: {total_games:,}")

# Recent performance (last 50 games)
recent = db.execute_query("""
    SELECT 
        AVG(final_score) as avg_score,
        MAX(final_score) as max_score,
        AVG(total_actions) as avg_actions
    FROM game_results
    ORDER BY end_time DESC
    LIMIT 50
""")

if recent:
    print(f"\nRecent Performance (last 50 games):")
    print(f"  Avg Score: {recent[0]['avg_score']:.4f}")
    print(f"  Max Score: {recent[0]['max_score']:.2f}")
    print(f"  Avg Actions: {recent[0]['avg_actions']:.0f}")

print()

# Check for wins
wins = db.execute_query("""
    SELECT COUNT(*) as win_count
    FROM game_results
    WHERE win_detected = TRUE
""")[0]['win_count']

print(f"Total Wins: {wins}")

# Check high scores
high_scores = db.execute_query("""
    SELECT game_id, final_score, total_actions, end_time
    FROM game_results
    WHERE final_score > 0.5
    ORDER BY final_score DESC
    LIMIT 5
""")

if high_scores:
    print(f"\nTop {len(high_scores)} Scoring Games:")
    for game in high_scores:
        print(f"  {game['game_id'][:24]}: {game['final_score']:.2f} in {game['total_actions']} actions")

print()

# Check system logs for recent activity
recent_logs = db.execute_query("""
    SELECT message, timestamp
    FROM system_logs
    WHERE logger_name IN ('AdaptiveActionLimits', 'AutonomousEvolutionRunner', 'EvolutionaryEngine')
    ORDER BY timestamp DESC
    LIMIT 5
""")

if recent_logs:
    print("Recent System Activity:")
    for log in recent_logs:
        print(f"  [{log['timestamp']}] {log['message'][:80]}")

print()
print("=" * 80)
print("🎯 SUMMARY")
print("=" * 80)
print()

if not last_game:
    print("⚠️  No games found - system may not have been run yet")
elif hours_since > 1:
    print(f"⚠️  System idle for {hours_since:.1f} hours")
    print("   Run 'python run_evolution.py' to continue training")
else:
    print("✓ System recently active")
    if wins > 0:
        print(f"✓ {wins} wins achieved!")
    else:
        print("○ No wins yet, but system is learning")

print()
print("=" * 80)
