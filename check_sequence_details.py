"""Check winning sequence details."""
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface

db = DatabaseInterface()

seq_id = "seq_68ac92c327984d29"
seq = db.execute_query('SELECT * FROM winning_sequences WHERE sequence_id = ?', (seq_id,))

if seq:
    s = seq[0]
    print("=== Winning Sequence Details ===")
    print(f"Sequence ID: {s['sequence_id']}")
    print(f"Game ID: {s['game_id']}")
    print(f"Level Number: {s['level_number']}")
    print(f"Total Score: {s['total_score']}")
    print(f"Total Actions: {s['total_actions']}")
    print(f"Efficiency Score: {s['efficiency_score']}")
    print(f"Pattern Tags: {s['pattern_tags']}")
    print(f"Difficulty Level: {s['difficulty_level']}")
    print(f"Game Type: {s['game_type']}")
    print(f"Times Referenced: {s['times_referenced']}")
    print(f"Success Rate When Reused: {s['success_rate_when_reused']}")
    print(f"Discovered At: {s['discovered_at']}")
else:
    print(f"No sequence found with ID: {seq_id}")
