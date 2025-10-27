"""Comprehensive diagnosis of pattern learning failure."""
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import json
from database_interface import DatabaseInterface

db = DatabaseInterface()

game_id = "lp85-d265526edbaa"
seq_id = "seq_68ac92c327984d29"

print("="*80)
print("PATTERN LEARNING FAILURE DIAGNOSIS")
print("="*80)

# 1. Get the winning sequence
seq = db.execute_query('SELECT * FROM winning_sequences WHERE sequence_id = ?', (seq_id,))[0]

print(f"\n1. CAPTURED PATTERN:")
print(f"   Sequence ID: {seq['sequence_id']}")
print(f"   Game: {seq['game_id']}, Level: {seq['level_number']}")
print(f"   Score: {seq['total_score']}, Actions: {seq['total_actions']}")
print(f"   Efficiency: {seq['efficiency_score']:.4f}")
print(f"   Times Referenced: {seq['times_referenced']}")
print(f"   Success Rate When Reused: {seq['success_rate_when_reused']}")

actions = json.loads(seq['action_sequence'])
print(f"   Action Sequence: {actions[:20]}... (showing first 20)")

# 2. Check game_results for actual wins
wins = db.execute_query("""
    SELECT COUNT(*) as win_count 
    FROM game_results 
    WHERE game_id = ? AND win_detected = TRUE
""", (game_id,))

print(f"\n2. ACTUAL GAME WINS:")
print(f"   Total wins for {game_id}: {wins[0]['win_count']}")
print(f"   ❌ PROBLEM: Pattern captured but NO ACTUAL WINS recorded!")

# 3. Check when pattern was referenced
refs = db.execute_query("""
    SELECT session_id, start_time, end_time, final_score, status, total_actions
    FROM game_results 
    WHERE game_id = ?
    ORDER BY start_time DESC
    LIMIT 5
""", (game_id,))

print(f"\n3. RECENT GAME ATTEMPTS:")
for i, r in enumerate(refs, 1):
    print(f"   {i}. Session: {r['session_id']}")
    print(f"      Time: {r['start_time']}")
    print(f"      Status: {r['status']}, Score: {r['final_score']}, Actions: {r['total_actions']}")

# 4. Identify the root cause
print(f"\n4. ROOT CAUSE ANALYSIS:")
print(f"   ❌ Pattern captured based on SCORE INCREASE (score went 0 → 1.0)")
print(f"   ❌ Not captured based on actual WIN state")
print(f"   ❌ Pattern replayed 3 times with 0% success rate")
print(f"   ❌ No verification that initial frame matches before replay")
print(f"   ❌ Replay doesn't track actions in database for debugging")

print(f"\n5. REQUIRED FIXES:")
print(f"   1. Only capture patterns when game_state.state == 'WIN'")
print(f"   2. Verify initial frame matches before replaying sequence")
print(f"   3. Track replay attempts in action_traces for debugging")
print(f"   4. Update success_rate_when_reused after each replay attempt")
print(f"   5. Store why replay failed (mismatch, timeout, error)")

print("="*80)
