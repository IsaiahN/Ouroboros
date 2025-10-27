import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface

db = DatabaseInterface()

print("=== Checking for 'unhashable' errors ===")
logs = db.execute_query("""
    SELECT timestamp, message 
    FROM system_logs 
    WHERE message LIKE ?
    ORDER BY timestamp DESC 
    LIMIT 20
""", ('%unhashable%',))

if logs:
    print(f"Found {len(logs)} 'unhashable' errors:")
    for log in logs[:5]:
        print(f"  {log['timestamp']}: {log['message'][:100]}")
else:
    print("✓ No 'unhashable' errors found in recent logs!")

print("\n=== Checking pattern learning ===")
sequences = db.execute_query("""
    SELECT sequence_id, game_id, total_actions, efficiency_score, pattern_tags
    FROM winning_sequences
    ORDER BY discovered_at DESC
    LIMIT 5
""")

if sequences:
    print(f"Found {len(sequences)} winning sequences captured:")
    for seq in sequences:
        print(f"  {seq['game_id']}: {seq['total_actions']} actions, efficiency {seq['efficiency_score']:.3f}")
else:
    print("No winning sequences captured yet (no wins)")
