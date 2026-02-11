"""Fast investigation - uses indexed queries on smaller subsets."""
import json
import sqlite3

conn = sqlite3.connect('core_data.db')
c = conn.cursor()

# Check what indexes exist
print("=== Indexes on action_traces ===")
rows = c.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='action_traces'").fetchall()
for name, sql in rows:
    print(f"  {name}: {sql}")

# Use id-based queries instead of ORDER BY created_at
print("\n=== Max id in action_traces ===")
max_id = c.execute("SELECT MAX(id) FROM action_traces").fetchone()[0]
print(f"  max_id = {max_id}")

# Get recent 1000 actions (by id, which is indexed)
print("\n=== Recent 1000 actions - coordinate analysis ===")
recent = c.execute("""
    SELECT game_id, coordinates, context_mode, question_tier,
           score_before, score_after, score_change, frame_changed,
           level_number, session_id
    FROM action_traces
    WHERE id > ?
    ORDER BY id DESC
    LIMIT 1000
""", (max_id - 1000,)).fetchall()

# Analyze by game type
from collections import Counter, defaultdict

game_coords = defaultdict(list)
game_context_modes = defaultdict(Counter)
game_question_tiers = defaultdict(Counter)
game_frame_changes = defaultdict(lambda: {'changed': 0, 'unchanged': 0})
game_score_changes = defaultdict(list)
game_sessions = defaultdict(set)

for row in recent:
    gid = row[0]
    if 'ft09' in gid.lower():
        gt = 'FT09'
    elif 'ls20' in gid.lower():
        gt = 'LS20'
    elif 'vc33' in gid.lower():
        gt = 'VC33'
    else:
        gt = gid[:8]

    game_coords[gt].append(row[1])
    game_context_modes[gt][row[2]] += 1
    game_question_tiers[gt][row[3]] += 1
    if row[7]:  # frame_changed
        game_frame_changes[gt]['changed'] += 1
    else:
        game_frame_changes[gt]['unchanged'] += 1
    game_score_changes[gt].append(row[6] or 0.0)
    game_sessions[gt].add(row[9])

for gt in sorted(game_coords.keys()):
    coords = game_coords[gt]
    unique_coords = set(coords)
    coord_counter = Counter(coords)
    total = len(coords)
    print(f"\n  --- {gt} ({total} actions, {len(game_sessions[gt])} sessions) ---")
    print(f"  Unique coordinates: {len(unique_coords)}")
    print(f"  Top 5 coordinates:")
    for coord, cnt in coord_counter.most_common(5):
        print(f"    {coord}: {cnt} times ({cnt*100//max(total,1)}%)")
    print(f"  Frame changes: {game_frame_changes[gt]}")
    pos_scores = sum(1 for s in game_score_changes[gt] if s > 0)
    neg_scores = sum(1 for s in game_score_changes[gt] if s < 0)
    print(f"  Score: {pos_scores} positive, {neg_scores} negative, {total-pos_scores-neg_scores} zero")
    print(f"  Context modes: {dict(game_context_modes[gt])}")
    print(f"  Question tiers: {dict(game_question_tiers[gt])}")

# Now look at SPECIFIC sessions for VC33 coordinate fixation
print("\n\n=== VC33 Session-level coordinate analysis (recent sessions) ===")
vc33_sessions = c.execute("""
    SELECT DISTINCT session_id
    FROM action_traces
    WHERE id > ? AND game_id LIKE '%vc33%'
    LIMIT 10
""", (max_id - 5000,)).fetchall()

for (sid,) in vc33_sessions:
    rows = c.execute("""
        SELECT coordinates, frame_changed, score_change, level_number, action_number
        FROM action_traces
        WHERE session_id = ?
        ORDER BY action_number
    """, (sid,)).fetchall()
    coords = [r[0] for r in rows]
    unique = set(coords)
    changed = sum(1 for r in rows if r[1])
    print(f"\n  Session {sid[:20]}... ({len(rows)} actions)")
    print(f"    Unique coordinates: {len(unique)}")
    print(f"    Frame changes: {changed}/{len(rows)}")
    coord_counter = Counter(coords)
    print(f"    Top coords: {coord_counter.most_common(5)}")
    # Show first 10 actions
    print(f"    First 10 actions:")
    for r in rows[:10]:
        print(f"      act={r[4]} coords={r[0]} frame_changed={r[1]} score_change={r[2]} level={r[3]}")

# Same for FT09
print("\n\n=== FT09 Session-level coordinate analysis (recent sessions) ===")
ft09_sessions = c.execute("""
    SELECT DISTINCT session_id
    FROM action_traces
    WHERE id > ? AND game_id LIKE '%ft09%'
    LIMIT 5
""", (max_id - 5000,)).fetchall()

for (sid,) in ft09_sessions:
    rows = c.execute("""
        SELECT coordinates, frame_changed, score_change, level_number, action_number
        FROM action_traces
        WHERE session_id = ?
        ORDER BY action_number
    """, (sid,)).fetchall()
    coords = [r[0] for r in rows]
    unique = set(coords)
    changed = sum(1 for r in rows if r[1])
    print(f"\n  Session {sid[:20]}... ({len(rows)} actions)")
    print(f"    Unique coordinates: {len(unique)}")
    print(f"    Frame changes: {changed}/{len(rows)}")
    coord_counter = Counter(coords)
    print(f"    Top coords: {coord_counter.most_common(5)}")

# Same for LS20
print("\n\n=== LS20 Session-level coordinate analysis (recent sessions) ===")
ls20_sessions = c.execute("""
    SELECT DISTINCT session_id
    FROM action_traces
    WHERE id > ? AND game_id LIKE '%ls20%'
    LIMIT 5
""", (max_id - 5000,)).fetchall()

for (sid,) in ls20_sessions:
    rows = c.execute("""
        SELECT coordinates, frame_changed, score_change, level_number, action_number
        FROM action_traces
        WHERE session_id = ?
        ORDER BY action_number
    """, (sid,)).fetchall()
    coords = [r[0] for r in rows]
    unique = set(coords)
    changed = sum(1 for r in rows if r[1])
    actions_list = [r[4] for r in rows]  # action_number here is actually the ACTION type
    print(f"\n  Session {sid[:20]}... ({len(rows)} actions)")
    print(f"    Unique coordinates: {len(unique)}")
    print(f"    Frame changes: {changed}/{len(rows)}")
    # Show action distribution (for movement games it should be ACTION1-4)
    action_counter = Counter([r[0] for r in rows])  # coords here might be null for movement
    print(f"    Coordinate distribution: {action_counter.most_common(5)}")

# Check game_results for VC33 vs LS20 level completions
print("\n\n=== game_results comparison ===")
for pattern, label in [('%vc33%', 'VC33'), ('%ls20%', 'LS20'), ('%ft09%', 'FT09')]:
    stats = c.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN levels_completed > 0 THEN 1 ELSE 0 END) as with_levels,
            MAX(levels_completed) as max_levels,
            AVG(final_score) as avg_score,
            MAX(final_score) as max_score,
            SUM(actions_taken) as total_actions
        FROM game_results
        WHERE game_id LIKE ?
    """, (pattern,)).fetchone()
    print(f"  {label}: {stats[0]} games, {stats[1]} with levels, max={stats[2]}, avg_score={stats[3]:.4f}, max_score={stats[4]}, total_actions={stats[5]}")

# Check what game_results looks like for LS20 games that completed levels
print("\n=== LS20 games that completed levels ===")
rows = c.execute("""
    SELECT game_id, agent_id, final_score, levels_completed, actions_taken, generation, is_win
    FROM game_results
    WHERE game_id LIKE '%ls20%' AND levels_completed > 0
    ORDER BY levels_completed DESC, final_score DESC
    LIMIT 10
""").fetchall()
for r in rows:
    print(f"  game={r[0]} agent={r[1][:16]}... score={r[2]} levels={r[3]} actions={r[4]} gen={r[5]} win={r[6]}")

# Check VC33 - what are the BEST scoring games?
print("\n=== VC33 best scoring games (even if 0 levels) ===")
rows = c.execute("""
    SELECT game_id, agent_id, final_score, levels_completed, actions_taken, generation
    FROM game_results
    WHERE game_id LIKE '%vc33%'
    ORDER BY final_score DESC
    LIMIT 10
""").fetchall()
for r in rows:
    print(f"  game={r[0]} agent={r[1][:16]}... score={r[2]} levels={r[3]} actions={r[4]} gen={r[5]}")

# Check the available_actions in observations - what actions are available for VC33?
print("\n=== Check response_data for VC33 (sample) ===")
sample = c.execute("""
    SELECT response_data
    FROM action_traces
    WHERE game_id LIKE '%vc33%' AND response_data IS NOT NULL
    AND id > ?
    LIMIT 3
""", (max_id - 5000,)).fetchall()
for (rd,) in sample:
    if rd:
        print(f"  {rd[:300]}")

# Check deliberation_audit if it exists
print("\n=== Checking for deliberation/rung tracking tables ===")
for tbl in ['deliberation_audit', 'rung_deliberation_audit', 'deliberation_records', 'rung_selection_log']:
    try:
        cnt = c.execute(f"SELECT COUNT(*) FROM [{tbl}]").fetchone()[0]
        print(f"  {tbl}: {cnt} rows")
        # Show schema
        cols = [r[1] for r in c.execute(f"PRAGMA table_info([{tbl}])")]
        print(f"    columns: {cols}")
    except:
        print(f"  {tbl}: does not exist")

# Also check for any table that might track rung decisions
print("\n=== Tables that might track rung/decision data ===")
tables = c.execute("""
    SELECT name FROM sqlite_master
    WHERE type='table' AND (
        name LIKE '%deliber%' OR name LIKE '%rung%' OR name LIKE '%decision%'
        OR name LIKE '%routing%' OR name LIKE '%cognitive%'
    )
""").fetchall()
for (t,) in tables:
    cnt = c.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
    cols = [r[1] for r in c.execute(f"PRAGMA table_info([{t}])")]
    print(f"  {t}: {cnt} rows, columns={cols}")

conn.close()
print("\n=== DONE ===")
