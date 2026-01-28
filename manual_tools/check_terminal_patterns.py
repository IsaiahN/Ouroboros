"""Check position_death_patterns table (formerly terminal_patterns).

NOTE: terminal_patterns table was REMOVED in Jan 2026.
All death tracking now uses position_death_patterns (fuzzy position-bucket matching).
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_interface import DatabaseInterface

db = DatabaseInterface()

print("=== Position death patterns for as66 Level 5 ===")
try:
    r = db.execute_query("""
        SELECT game_type, level_number, bucket_x, bucket_y, bucket_size,
               fatal_action, death_count, danger_score, is_active
        FROM position_death_patterns 
        WHERE game_type = 'as66' AND level_number = 5
        ORDER BY death_count DESC
        LIMIT 20
    """)
    if r:
        for x in r:
            bx = x.get('bucket_x', 0)
            by = x.get('bucket_y', 0)
            bs = x.get('bucket_size', 8)
            print(f"  L{x['level_number']}: bucket=({bx*bs},{by*bs}) fatal_action={x['fatal_action']}, deaths={x['death_count']}, danger={x['danger_score']:.2f}, active={x['is_active']}")
    else:
        print("  No position death patterns for as66 L5!")
except Exception as e:
    print(f"  Error: {e}")

print()
print("=== Schema of position_death_patterns ===")
try:
    r2 = db.execute_query("PRAGMA table_info(position_death_patterns)")
    if r2:
        for col in r2:
            print(f"  {col['name']} ({col['type']})")
except Exception as e:
    print(f"  Error: {e}")
