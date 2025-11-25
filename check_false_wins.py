"""Check for games incorrectly marked as won (score >= 20)"""
import sqlite3

conn = sqlite3.connect('core_data.db')
cursor = conn.cursor()

# Find games with score >= 20
cursor.execute("""
    SELECT game_id, scorecard_id, final_score, status, start_time, win_detected
    FROM game_results 
    WHERE final_score >= 20 
    ORDER BY final_score DESC 
    LIMIT 10
""")

print("Games with final_score >= 20:")
rows = cursor.fetchall()
if rows:
    for row in rows:
        print(f"  Game: {row[0]}")
        print(f"    Scorecard: {row[1]}")
        print(f"    Score: {row[2]}")
        print(f"    Status: {row[3]}")
        print(f"    Time: {row[4]}")
        print(f"    Win Detected: {row[5]}")
        print()
else:
    print("  None found")

# Also check winning_sequences_full_game table
cursor.execute("""
    SELECT game_id, sequence_id, total_actions, scorecard_id, discovered_at
    FROM winning_sequences_full_game 
    WHERE is_active = 1
    LIMIT 10
""")

print("\nFull game winning sequences:")
rows = cursor.fetchall()
if rows:
    for row in rows:
        print(f"  Game: {row[0]}")
        print(f"    Sequence ID: {row[1]}")
        print(f"    Actions: {row[2]}")
        print(f"    Scorecard: {row[3]}")
        print(f"    Discovered: {row[4]}")
        print()
else:
    print("  None found")

# Check what the phase detection query is actually finding
cursor.execute("""
    SELECT COUNT(DISTINCT game_id) as beaten_games
    FROM game_results
    WHERE win_detected = TRUE
""")
row = cursor.fetchone()
print(f"\nGames with win_detected = TRUE: {row[0]}")

# List the actual games marked as won
cursor.execute("""
    SELECT game_id, scorecard_id, final_score, status, start_time
    FROM game_results
    WHERE win_detected = TRUE
    ORDER BY start_time DESC
""")
print("\nGames marked as won (win_detected = TRUE):")
for row in cursor.fetchall():
    print(f"  Game: {row[0]}")
    print(f"    Scorecard: {row[1]}")
    print(f"    Score: {row[2]}")
    print(f"    Status: {row[3]}")
    print(f"    Time: {row[4]}")
    print()

print("\n" + "="*60)
print("CLEANUP: Removing test game false positives...")
print("="*60)

# Delete the test game records
cursor.execute("DELETE FROM game_results WHERE game_id LIKE 'test_game_%'")
deleted = cursor.rowcount
print(f"Deleted {deleted} test game records from game_results")

# Also check for test sequences
cursor.execute("DELETE FROM winning_sequences WHERE game_id LIKE 'test_game_%'")
deleted = cursor.rowcount
print(f"Deleted {deleted} test sequences from winning_sequences")

cursor.execute("DELETE FROM winning_sequences_full_game WHERE game_id LIKE 'test_game_%'")
deleted = cursor.rowcount
print(f"Deleted {deleted} test sequences from winning_sequences_full_game")

conn.commit()
print("\n✓ Cleanup complete - test data removed")

conn.close()
