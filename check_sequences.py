"""Check sequence coverage for games with level completions.

SOURCE OF TRUTH: winning_sequences table (not game_results which can have stale data)
"""
import sqlite3

conn = sqlite3.connect('core_data.db')
c = conn.cursor()

print("=" * 60)
print("WINNING SEQUENCES BY GAME (Source of Truth)")
print("=" * 60)

# Get all sequences grouped by game
games = c.execute("""
    SELECT 
        SUBSTR(game_id, 1, 4) as game_prefix,
        COUNT(DISTINCT level_number) as levels_with_seqs,
        MAX(level_number) as max_level,
        COUNT(*) as total_seqs,
        MIN(total_actions) as best_actions
    FROM winning_sequences 
    WHERE is_active = 1
    GROUP BY SUBSTR(game_id, 1, 4)
    ORDER BY max_level DESC, total_seqs DESC
""").fetchall()

for prefix, levels_count, max_level, total_seqs, best in games:
    # Get level breakdown
    level_info = c.execute("""
        SELECT level_number, COUNT(*), MIN(total_actions)
        FROM winning_sequences 
        WHERE game_id LIKE ? AND is_active = 1
        GROUP BY level_number
        ORDER BY level_number
    """, (f"{prefix}%",)).fetchall()
    
    level_str = ", ".join([f"L{l[0]}({l[1]}x,best={l[2]})" for l in level_info])
    print(f"{prefix}: {levels_count} levels, max L{max_level}, {total_seqs} seqs - {level_str}")

print("\n" + "=" * 60)
print("SEQUENCE GAPS (Levels missing between 1 and max)")
print("=" * 60)

for prefix, levels_count, max_level, total_seqs, best in games:
    if max_level > 1:
        # Check for gaps
        existing_levels = set(r[0] for r in c.execute("""
            SELECT DISTINCT level_number FROM winning_sequences 
            WHERE game_id LIKE ? AND is_active = 1
        """, (f"{prefix}%",)).fetchall())
        
        expected = set(range(1, max_level + 1))
        missing = expected - existing_levels
        
        if missing:
            print(f"{prefix}: Has L1-L{max_level} but MISSING {sorted(missing)}")
        else:
            print(f"{prefix}: Complete coverage L1-L{max_level} [OK]")

print("\n" + "=" * 60)
print("USER'S 6 SCORECARDS - CHECKING SEQUENCES")
print("=" * 60)
# User's scorecards with their game info from user
scorecard_info = [
    ('579d8564', 'ft09', 1, 'generalist'),
    ('db6ed9eb', 'ft09', 1, 'exploiter'),
    ('4fc7b02b', 'sp80', 1, 'pioneer'),
    ('14f6264d', 'ft09', 1, 'optimizer'),
    ('34ddeb14', 'ft09', 1, 'optimizer'),
    ('b59f3d08', 'as66', 2, 'generalist'),
]
for sc, game_prefix, levels, role in scorecard_info:
    # Check if sequences exist for this game/level
    seqs = c.execute("""
        SELECT game_id, level_number, total_actions, total_score
        FROM winning_sequences 
        WHERE game_id LIKE ? AND level_number = ? AND is_active = 1
        ORDER BY total_actions ASC
    """, (f"{game_prefix}%", levels)).fetchall()
    
    if seqs:
        print(f"{sc} ({game_prefix} L{levels}, {role}): [OK] {len(seqs)} seqs, best={seqs[0][2]} actions")
    else:
        # Check if ANY sequences exist for this game
        any_seqs = c.execute("""
            SELECT level_number, COUNT(*) as cnt, MIN(total_actions) as best
            FROM winning_sequences 
            WHERE game_id LIKE ? AND is_active = 1
            GROUP BY level_number
        """, (f"{game_prefix}%",)).fetchall()
        if any_seqs:
            available = ", ".join([f"L{r[0]}" for r in any_seqs])
            print(f"{sc} ({game_prefix} L{levels}, {role}): [MISSING] Only have: {available}")
        else:
            print(f"{sc} ({game_prefix} L{levels}, {role}): [NO SEQS]")

conn.close()
