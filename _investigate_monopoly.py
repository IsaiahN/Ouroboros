"""Temporary investigation script for rung monopoly and coordinate fixation."""
import json
import sqlite3

conn = sqlite3.connect('core_data.db')
c = conn.cursor()

# 1. Recent sessions
print("=== Most recent 20 sessions ===")
rows = c.execute("""
    SELECT session_id, game_id, COUNT(*) as action_count,
           MIN(action_number), MAX(action_number), MAX(created_at) as latest
    FROM action_traces
    GROUP BY session_id
    ORDER BY MAX(created_at) DESC
    LIMIT 20
""").fetchall()
for row in rows:
    sid = row[0][:16] if row[0] else "None"
    print(f"  sess={sid}... game={row[1]} acts={row[2]} range=[{row[3]}-{row[4]}] last={row[5]}")

# 2. Game type distribution
print("\n=== Game type distribution (all time) ===")
rows = c.execute("""
    SELECT
        CASE
            WHEN game_id LIKE '%ft09%' THEN 'FT09'
            WHEN game_id LIKE '%ls20%' THEN 'LS20'
            WHEN game_id LIKE '%vc33%' THEN 'VC33'
            ELSE game_id
        END as game_type,
        COUNT(*) as total_actions,
        COUNT(DISTINCT session_id) as sessions
    FROM action_traces
    GROUP BY game_type
""").fetchall()
for gt, acts, sess in rows:
    avg = acts // max(sess, 1)
    print(f"  {gt}: {acts} actions across {sess} sessions (avg {avg} per session)")

# 3. Coordinate analysis for click games - check recent VC33 and FT09 sessions
print("\n=== Coordinate fixation analysis: Recent VC33 sessions ===")
vc33_sessions = c.execute("""
    SELECT session_id, game_id
    FROM action_traces
    WHERE game_id LIKE '%vc33%'
    GROUP BY session_id
    ORDER BY MAX(created_at) DESC
    LIMIT 10
""").fetchall()

for sid, gid in vc33_sessions:
    coords = c.execute("""
        SELECT coordinates, COUNT(*) as cnt
        FROM action_traces
        WHERE session_id = ?
        GROUP BY coordinates
        ORDER BY cnt DESC
    """, (sid,)).fetchall()
    total = sum(cnt for _, cnt in coords)
    unique = len(coords)
    top3 = coords[:3]
    print(f"  sess={sid[:16]}... total={total} unique_coords={unique} top3={top3}")

print("\n=== Coordinate fixation analysis: Recent FT09 sessions ===")
ft09_sessions = c.execute("""
    SELECT session_id, game_id
    FROM action_traces
    WHERE game_id LIKE '%ft09%'
    GROUP BY session_id
    ORDER BY MAX(created_at) DESC
    LIMIT 10
""").fetchall()

for sid, gid in ft09_sessions:
    coords = c.execute("""
        SELECT coordinates, COUNT(*) as cnt
        FROM action_traces
        WHERE session_id = ?
        GROUP BY coordinates
        ORDER BY cnt DESC
    """, (sid,)).fetchall()
    total = sum(cnt for _, cnt in coords)
    unique = len(coords)
    top3 = coords[:3]
    print(f"  sess={sid[:16]}... total={total} unique_coords={unique} top3={top3}")

print("\n=== Coordinate fixation analysis: Recent LS20 sessions ===")
ls20_sessions = c.execute("""
    SELECT session_id, game_id
    FROM action_traces
    WHERE game_id LIKE '%ls20%'
    GROUP BY session_id
    ORDER BY MAX(created_at) DESC
    LIMIT 10
""").fetchall()

for sid, gid in ls20_sessions:
    coords = c.execute("""
        SELECT coordinates, COUNT(*) as cnt
        FROM action_traces
        WHERE session_id = ?
        GROUP BY coordinates
        ORDER BY cnt DESC
    """, (sid,)).fetchall()
    total = sum(cnt for _, cnt in coords)
    unique = len(coords)
    top3 = coords[:3]
    print(f"  sess={sid[:16]}... total={total} unique_coords={unique} top3={top3}")

# 4. Check context_mode distribution (may indicate which rung/strategy was used)
print("\n=== context_mode distribution (recent 50k actions) ===")
rows = c.execute("""
    SELECT context_mode, COUNT(*) as cnt
    FROM (SELECT context_mode FROM action_traces ORDER BY id DESC LIMIT 50000)
    GROUP BY context_mode
    ORDER BY cnt DESC
""").fetchall()
for mode, cnt in rows:
    print(f"  {mode}: {cnt} ({cnt*100//50000}%)")

# 5. Check question_tier distribution
print("\n=== question_tier distribution (recent 50k actions) ===")
rows = c.execute("""
    SELECT question_tier, COUNT(*) as cnt
    FROM (SELECT question_tier FROM action_traces ORDER BY id DESC LIMIT 50000)
    GROUP BY question_tier
    ORDER BY cnt DESC
""").fetchall()
for tier, cnt in rows:
    print(f"  {tier}: {cnt} ({cnt*100//50000}%)")

# 6. Check score_change distribution for VC33 vs LS20
print("\n=== Score changes by game type ===")
for game_type, pattern in [("VC33", "%vc33%"), ("LS20", "%ls20%"), ("FT09", "%ft09%")]:
    stats = c.execute(f"""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN score_change > 0 THEN 1 ELSE 0 END) as positive,
            SUM(CASE WHEN score_change < 0 THEN 1 ELSE 0 END) as negative,
            SUM(CASE WHEN score_change = 0 THEN 1 ELSE 0 END) as zero,
            SUM(CASE WHEN frame_changed = 1 THEN 1 ELSE 0 END) as frame_changed_count,
            AVG(score_change) as avg_change
        FROM action_traces
        WHERE game_id LIKE ?
    """, (pattern,)).fetchone()
    print(f"  {game_type}: total={stats[0]} pos_score={stats[1]} neg_score={stats[2]} zero_score={stats[3]} frames_changed={stats[4]} avg_change={stats[5]}")

# 7. Check if there's a rung selection table
print("\n=== Looking for rung-related tables ===")
tables = c.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name LIKE '%rung%' OR name LIKE '%decision%' OR name LIKE '%cognitive%' OR name LIKE '%routing%')").fetchall()
for t in tables:
    cnt = c.execute(f"SELECT COUNT(*) FROM [{t[0]}]").fetchone()[0]
    print(f"  {t[0]}: {cnt} rows")

# 8. Check game_results for level completion details
print("\n=== game_results: Level completions by game type ===")
for game_type, pattern in [("VC33", "%vc33%"), ("LS20", "%ls20%"), ("FT09", "%ft09%")]:
    stats = c.execute(f"""
        SELECT
            COUNT(*) as total_games,
            SUM(CASE WHEN levels_completed > 0 THEN 1 ELSE 0 END) as games_with_progress,
            MAX(levels_completed) as max_levels,
            AVG(final_score) as avg_score,
            MAX(final_score) as max_score
        FROM game_results
        WHERE game_id LIKE ?
    """, (pattern,)).fetchone()
    print(f"  {game_type}: games={stats[0]} with_progress={stats[1]} max_levels={stats[2]} avg_score={stats[3]:.4f} max_score={stats[4]}")

# 9. Check response_data for a sample VC33 action to understand what happens
print("\n=== Sample VC33 response_data (last 3 actions of a recent session) ===")
if vc33_sessions:
    sid = vc33_sessions[0][0]
    samples = c.execute("""
        SELECT action_number, coordinates, score_before, score_after, score_change,
               frame_changed, response_data, level_number
        FROM action_traces
        WHERE session_id = ?
        ORDER BY action_number DESC
        LIMIT 3
    """, (sid,)).fetchall()
    for s in samples:
        resp = s[6][:200] if s[6] else "None"
        print(f"  act={s[0]} coords={s[1]} score={s[2]}->{s[3]} change={s[4]} frame_changed={s[5]} level={s[7]}")
        print(f"    response_data (truncated): {resp}")

conn.close()
