"""Check why recombination isn't triggering"""
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
from database_interface import DatabaseInterface

db = DatabaseInterface()

print("Checking why recombination isn't triggering...\n")

# Check recent games
print("1. Recent game completions:")
games = db.execute_query("""
    SELECT game_id, status, final_score, end_time, win_detected
    FROM game_results
    ORDER BY end_time DESC
    LIMIT 5
""")

if games:
    for g in games:
        win_str = "WIN" if g['win_detected'] else "LOSS"
        print(f"   {g['game_id']}: {g['status']} [{win_str}] (score: {g['final_score']}) at {g['end_time'][:19]}")
else:
    print("   ❌ No games found!")

# Check if recombination errors in logs
print("\n2. Recent recombination errors:")
errors = db.execute_query("""
    SELECT timestamp, message
    FROM system_logs
    WHERE message LIKE '%recombination%'
    ORDER BY timestamp DESC
    LIMIT 5
""")

if errors:
    for e in errors:
        print(f"   [{e['timestamp'][:19]}] {e['message'][:100]}")
else:
    print("   ℹ️  No recombination-related logs")

# Check sequences by game/level
print("\n3. Sequences available for recombination:")
seq_by_game = db.execute_query("""
    SELECT game_id, level_number, COUNT(*) as seq_count
    FROM winning_sequences
    GROUP BY game_id, level_number
    HAVING COUNT(*) >= 2
    ORDER BY seq_count DESC
    LIMIT 10
""")

if seq_by_game:
    print(f"   Games with 2+ sequences (can be recombined):")
    for row in seq_by_game:
        print(f"   - {row['game_id']} Level {row['level_number']}: {row['seq_count']} sequences")
else:
    print("   ❌ No game/level combos have 2+ sequences!")

# Check if agents played games recently
print("\n4. Recent agent gameplay:")
recent_plays = db.execute_query("""
    SELECT DISTINCT gr.game_id, gr.status, gr.end_time, gr.win_detected
    FROM game_results gr
    WHERE gr.end_time > datetime('now', '-2 hours')
    ORDER BY gr.end_time DESC
    LIMIT 10
""")

if recent_plays:
    print(f"   {len(recent_plays)} games in last 2 hours")
    for p in recent_plays:
        win_str = "WIN" if p['win_detected'] else "LOSS"
        print(f"   - {p['game_id']}: {p['status']} [{win_str}] at {p['end_time'][:19]}")
else:
    print("   ⚠️  No games in last 2 hours")

# Check core_gameplay errors
print("\n5. Checking for core_gameplay errors:")
gameplay_errors = db.execute_query("""
    SELECT timestamp, level, message
    FROM system_logs
    WHERE logger_name LIKE '%core_gameplay%'
    AND level = 'ERROR'
    ORDER BY timestamp DESC
    LIMIT 5
""")

if gameplay_errors:
    print("   Recent errors:")
    for e in gameplay_errors:
        print(f"   [{e['timestamp'][:19]}] {e['message'][:120]}")
else:
    print("   ✅ No recent core_gameplay errors")

print("\n" + "=" * 80)
