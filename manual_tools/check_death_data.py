"""Check death-related data in database for as66."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_interface import DatabaseInterface

db = DatabaseInterface()

print("=== ACTION TRACES for as66 Level 5 (first 5 actions) ===")
r = db.execute_query("""
    SELECT 
        action_number,
        COUNT(*) as total_uses,
        SUM(CASE WHEN score_change < 0 THEN 1 ELSE 0 END) as score_drops
    FROM action_traces
    WHERE game_id LIKE 'as66-%'
      AND level_number = 5
      AND action_number BETWEEN 1 AND 7
    GROUP BY action_number
    ORDER BY score_drops DESC
""")
if r:
    for row in r:
        print(f"  ACTION{row['action_number']}: {row['total_uses']} uses, {row['score_drops']} deaths")
else:
    print("  NO DATA for level 5!")

print()
print("=== LESSONS LEARNED for as66 (death patterns) ===")
r2 = db.execute_query("""
    SELECT lesson_text, caused_death, occurrence_count, severity
    FROM game_lessons_learned 
    WHERE game_type = 'as66' AND (caused_death = 1 OR severity >= 3)
    ORDER BY severity DESC, occurrence_count DESC
    LIMIT 10
""")
if r2:
    for row in r2:
        death_flag = row.get('caused_death', 0)
        count = row.get('occurrence_count', 0)
        sev = row.get('severity', 0)
        txt = row.get('lesson_text', '')[:60]
        print(f"  [sev={sev}] {txt}... (deaths={death_flag}, count={count})")
else:
    print("  NO death lessons for as66!")

print()
print("=== DANGEROUS OBJECTS for as66 ===")
r3 = db.execute_query("""
    SELECT object_color, object_shape, danger_score, times_caused_death, level_specific
    FROM dangerous_objects
    WHERE game_type = 'as66'
    ORDER BY times_caused_death DESC
    LIMIT 10
""")
if r3:
    for row in r3:
        color = row.get('object_color', '?')
        shape = row.get('object_shape', '?')
        danger = row.get('danger_score', 0)
        deaths = row.get('times_caused_death', 0)
        lvl_spec = row.get('level_specific', '?')
        print(f"  {color} {shape}: danger={danger:.2f}, deaths={deaths}, level_specific={lvl_spec}")
else:
    print("  NO dangerous objects recorded!")

print()
print("=== Total action_traces for as66 ===")
r4 = db.execute_query("""
    SELECT level_number, COUNT(*) as cnt
    FROM action_traces
    WHERE game_id LIKE 'as66-%'
    GROUP BY level_number
    ORDER BY level_number
""")
if r4:
    for row in r4:
        print(f"  Level {row['level_number']}: {row['cnt']} traces")
else:
    print("  NO action traces!")

print()
print("=== Recent as66 game results (last 50) ===")
r5 = db.execute_query("""
    SELECT levels_completed, actions_taken, final_score, created_at
    FROM game_results
    WHERE game_type = 'as66'
    ORDER BY created_at DESC
    LIMIT 50
""")
if r5:
    level_counts = {}
    for row in r5:
        lvl = row.get('levels_completed', 0)
        level_counts[lvl] = level_counts.get(lvl, 0) + 1
    print(f"  Level completion distribution: {level_counts}")
else:
    print("  NO game results!")
