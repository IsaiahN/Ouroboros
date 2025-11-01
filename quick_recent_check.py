#!/usr/bin/env python3
"""Quick check of recent games."""
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface
from datetime import datetime, timedelta

db = DatabaseInterface()

print("\n" + "="*80)
print("RECENT GAMES CHECK")
print("="*80)

games = db.execute_query("""
    SELECT game_id, level_completions, total_actions, end_time
    FROM game_results
    ORDER BY end_time DESC
    LIMIT 20
""")

if not games:
    print("\nNo games in database!")
else:
    print(f"\nLast 20 games:")
    print(f"{'Game ID':25s} | {'Levels':>6} | {'Actions':>8} | {'Time':19s}")
    print("-" * 80)
    
    for row in games:
        game_id = row[0] if not isinstance(row, dict) else row['game_id']
        levels = row[1] if not isinstance(row, dict) else row['level_completions']
        actions = row[2] if not isinstance(row, dict) else row['total_actions']
        end_time = row[3] if not isinstance(row, dict) else row['end_time']
        
        emoji = "✅" if levels > 0 else "  "
        print(f"{emoji} {game_id[:23]:23s} | {levels:6d} | {actions:8d} | {end_time[:19]}")
    
    # Stats
    total = len(games)
    with_levels = sum(1 for r in games if (r[1] if not isinstance(r, dict) else r['level_completions']) > 0)
    total_levels = sum((r[1] if not isinstance(r, dict) else r['level_completions']) for r in games)
    
    print(f"\nStats (last 20):")
    print(f"  Games with levels: {with_levels}/{total} ({with_levels/total*100:.1f}%)")
    print(f"  Total levels: {total_levels}")

print("\n" + "="*80 + "\n")
