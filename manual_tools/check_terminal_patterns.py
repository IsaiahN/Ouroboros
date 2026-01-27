"""Check terminal patterns table."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_interface import DatabaseInterface

db = DatabaseInterface()

print("=== Terminal patterns for as66 Level 5 ===")
try:
    r = db.execute_query("""
        SELECT game_type, level_number, frame_hash, fatal_action, occurrence_count, is_active
        FROM terminal_patterns 
        WHERE game_type = 'as66' AND level_number = 5
        ORDER BY occurrence_count DESC
        LIMIT 20
    """)
    if r:
        for x in r:
            fh = x.get('frame_hash', 'NULL')
            fh_str = fh[:30] if fh else 'NULL'
            print(f"  L{x['level_number']}: hash={fh_str}... fatal_action={x['fatal_action']}, count={x['occurrence_count']}, active={x['is_active']}")
    else:
        print("  No terminal patterns for as66!")
except Exception as e:
    print(f"  Error: {e}")

print()
print("=== Schema of terminal_patterns ===")
try:
    r2 = db.execute_query("PRAGMA table_info(terminal_patterns)")
    if r2:
        for col in r2:
            print(f"  {col['name']} ({col['type']})")
except Exception as e:
    print(f"  Error: {e}")
