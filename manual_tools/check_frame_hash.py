"""Check frame_hash data for death events."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_interface import DatabaseInterface

db = DatabaseInterface()

print("=== Death actions with frame_hash on level 5 ===")
r = db.execute_query("""
    SELECT frame_hash, action_number, score_change, resulted_in_game_over
    FROM action_traces 
    WHERE game_id LIKE 'as66-%' 
      AND level_number = 5 
      AND score_change < 0 
    LIMIT 15
""")
if r:
    for x in r:
        fh = x.get('frame_hash')
        fh_str = fh[:20] if fh else 'NULL'
        print(f"  ACTION{x['action_number']}: hash={fh_str}... death={x['resulted_in_game_over']}")
else:
    print("  No death data!")

print()
print("=== Distinct frame_hashes for deaths on level 5 ===")
r2 = db.execute_query("""
    SELECT frame_hash, action_number, COUNT(*) as death_count
    FROM action_traces 
    WHERE game_id LIKE 'as66-%' 
      AND level_number = 5 
      AND score_change < 0
      AND frame_hash IS NOT NULL
    GROUP BY frame_hash, action_number
    ORDER BY death_count DESC
    LIMIT 10
""")
if r2:
    for x in r2:
        fh = x.get('frame_hash', 'NULL')
        print(f"  hash={fh[:30] if fh else 'NULL'}... ACTION{x['action_number']} -> {x['death_count']} deaths")
else:
    print("  No frame_hash data for deaths!")

print()
print("=== How many death traces have frame_hash vs NULL? ===")
r3 = db.execute_query("""
    SELECT 
        SUM(CASE WHEN frame_hash IS NOT NULL THEN 1 ELSE 0 END) as with_hash,
        SUM(CASE WHEN frame_hash IS NULL THEN 1 ELSE 0 END) as without_hash
    FROM action_traces 
    WHERE game_id LIKE 'as66-%' 
      AND level_number = 5 
      AND score_change < 0
""")
if r3 and r3[0]:
    print(f"  With hash: {r3[0]['with_hash']}, Without hash: {r3[0]['without_hash']}")
