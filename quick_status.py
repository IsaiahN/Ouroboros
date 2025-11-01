#!/usr/bin/env python3
"""
Quick Status Check
==================

Single snapshot of evolution progress (doesn't loop).

Usage:
    python quick_status.py
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from datetime import datetime, timedelta
from database_interface import DatabaseInterface

db = DatabaseInterface()

print("\n" + "="*80)
print("🐍 OUROBOROS QUICK STATUS")
print("="*80)
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# Population
pop = db.execute_query("""
    SELECT 
        COUNT(*) as total,
        MAX(generation) as max_gen
    FROM agents WHERE is_active = 1
""")

if pop:
    row = pop[0]
    total = row['total'] if isinstance(row, dict) else row[0]
    max_gen = row['max_gen'] if isinstance(row, dict) else row[1]
    print(f"Population: {total} active agents")
    print(f"Generation: {max_gen}")

# Recent activity
recent = db.execute_query("""
    SELECT 
        COUNT(*) as games,
        SUM(level_completions) as levels,
        MAX(end_time) as last_game
    FROM game_results
    WHERE end_time > datetime('now', '-1 hour')
""")

if recent:
    row = recent[0]
    games = row['games'] if isinstance(row, dict) else row[0]
    levels = row['levels'] if isinstance(row, dict) else row[1]
    last_game = row['last_game'] if isinstance(row, dict) else row[2]
    
    print(f"\nLast Hour:")
    print(f"  Games: {games}")
    print(f"  Levels: {levels or 0}")
    
    if last_game:
        last = datetime.fromisoformat(last_game)
        mins_ago = (datetime.now() - last).total_seconds() / 60
        print(f"  Last game: {mins_ago:.0f} minutes ago")

# Top performer
top = db.execute_query("""
    SELECT agent_id, generation, avg_score_per_game, total_games_played
    FROM agents 
    WHERE is_active = 1 AND total_games_played > 5
    ORDER BY avg_score_per_game DESC
    LIMIT 1
""")

if top:
    row = top[0]
    agent_id = row['agent_id'] if isinstance(row, dict) else row[0]
    gen = row['generation'] if isinstance(row, dict) else row[1]
    avg_score = row['avg_score_per_game'] if isinstance(row, dict) else row[2]
    games = row['total_games_played'] if isinstance(row, dict) else row[3]
    
    print(f"\nTop Performer:")
    print(f"  {agent_id[:20]} (Gen {gen})")
    print(f"  {avg_score:.3f} avg levels/game in {games} games")

print("\n" + "="*80 + "\n")
