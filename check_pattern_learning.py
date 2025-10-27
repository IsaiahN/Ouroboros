#!/usr/bin/env python3
"""
Check pattern learning database for specific game
"""
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface

db = DatabaseInterface('core_data.db')

# Check for winning sequences
print("=" * 70)
print("CHECKING PATTERN LEARNING FOR lp85-d265526edbaa")
print("=" * 70)
print()

# Check winning_sequences table
print("1. Checking winning_sequences table:")
sequences = db.execute_query("""
    SELECT sequence_id, game_id, level_number, total_score, total_actions, 
           efficiency_score, discovered_at, times_referenced
    FROM winning_sequences
    WHERE game_id = 'lp85-d265526edbaa'
    ORDER BY discovered_at DESC
""")

if sequences:
    print(f"   Found {len(sequences)} winning sequences:")
    for seq in sequences:
        print(f"   - {seq['sequence_id']}")
        print(f"     Game: {seq['game_id']}, Level: {seq['level_number']}")
        print(f"     Score: {seq['total_score']}, Actions: {seq['total_actions']}")
        print(f"     Efficiency: {seq['efficiency_score']:.3f}")
        print(f"     Discovered: {seq['discovered_at']}")
        print(f"     Referenced: {seq['times_referenced']} times")
        print()
else:
    print("   ❌ No winning sequences found for this game!")
    print()

# Check game_results for wins
print("2. Checking game_results for wins:")
wins = db.execute_query("""
    SELECT game_id, session_id, final_score, total_actions, win_detected, 
           end_time, level_completions
    FROM game_results
    WHERE game_id = 'lp85-d265526edbaa' AND win_detected = 1
    ORDER BY end_time DESC
""")

if wins:
    print(f"   Found {len(wins)} wins:")
    for win in wins:
        print(f"   - Session: {win['session_id']}")
        print(f"     Score: {win['final_score']}, Actions: {win['total_actions']}")
        print(f"     Levels: {win['level_completions']}")
        print(f"     Time: {win['end_time']}")
        print()
else:
    print("   ❌ No wins recorded in game_results!")
    print()

# Check action_traces for this game
print("3. Checking action_traces:")
traces = db.execute_query("""
    SELECT COUNT(*) as count, session_id
    FROM action_traces
    WHERE game_id = 'lp85-d265526edbaa'
    GROUP BY session_id
    ORDER BY count DESC
    LIMIT 5
""")

if traces:
    print(f"   Found action traces in {len(traces)} sessions:")
    for trace in traces:
        print(f"   - Session {trace['session_id']}: {trace['count']} actions")
else:
    print("   ❌ No action traces found!")

print()

# Check pattern learning configuration
print("4. Checking pattern learning status:")
from core_gameplay import GameplayEngine
engine = GameplayEngine()
print(f"   Pattern Learning Enabled: {engine.game_config.get('enable_pattern_learning', False)}")
print(f"   Learning Mode: {engine.game_config.get('learning_mode', 'unknown')}")
print()

# Check if pattern learning captured the win
print("5. Diagnosis:")
if sequences:
    print("   ✅ Pattern was captured in winning_sequences")
    if sequences[0]['times_referenced'] > 0:
        print(f"   ✅ Pattern has been referenced {sequences[0]['times_referenced']} times")
    else:
        print("   ⚠️ Pattern captured but never referenced (replay not attempted)")
elif wins:
    print("   ⚠️ Win was recorded but pattern was NOT captured!")
    print("   Possible reasons:")
    print("   - Pattern learning was disabled")
    print("   - _capture_winning_sequence() failed")
    print("   - No action traces available at capture time")
else:
    print("   ❌ No win recorded at all - game may not have actually won")

print()
print("=" * 70)
