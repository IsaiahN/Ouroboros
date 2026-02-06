"""Quick analysis of latest generation - corrected column names."""
import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
import sqlite3

c = sqlite3.connect('core_data.db')
c.row_factory = sqlite3.Row

# Game results
print('=== GAME RESULTS (latest gen) ===')
rows = c.execute("""
    SELECT
        SUBSTR(game_id, 1, 4) as game_type,
        COUNT(*) as games,
        SUM(CASE WHEN final_score > 0 THEN 1 ELSE 0 END) as nonzero,
        ROUND(AVG(final_score), 4) as avg_score,
        MAX(level_completions) as max_levels,
        ROUND(AVG(total_actions), 1) as avg_actions
    FROM game_results
    WHERE created_at > datetime('now', '-2 hours')
    GROUP BY game_type
""").fetchall()
for r in rows:
    print(f"  {r['game_type']}: {r['games']} games, {r['nonzero']} nonzero, avg_score={r['avg_score']}, max_lvl={r['max_levels']}, avg_actions={r['avg_actions']}")

# Check if frame_changed data was recorded for vc33
print()
print('=== VC33 FRAME CHANGES (latest gen) ===')
rows = c.execute("""
    SELECT
        frame_changed,
        COUNT(*) as cnt
    FROM action_traces
    WHERE game_id LIKE 'vc33%'
      AND created_at > datetime('now', '-2 hours')
    GROUP BY frame_changed
""").fetchall()
for r in rows:
    print(f"  frame_changed={r['frame_changed']}: {r['cnt']} actions")

# Check coordinate diversity for vc33
print()
print('=== VC33 COORDINATE DIVERSITY (latest gen) ===')
total = c.execute("""
    SELECT COUNT(*) as cnt FROM action_traces
    WHERE game_id LIKE 'vc33%' AND created_at > datetime('now', '-2 hours')
""").fetchone()
unique = c.execute("""
    SELECT COUNT(DISTINCT coordinates) as cnt FROM action_traces
    WHERE game_id LIKE 'vc33%' AND created_at > datetime('now', '-2 hours')
""").fetchone()
print(f"  Total vc33 actions: {total['cnt']}")
print(f"  Unique coordinates: {unique['cnt']}")

# Sample some vc33 coordinates
print()
print('=== VC33 TOP COORDINATES (latest gen) ===')
rows = c.execute("""
    SELECT coordinates, COUNT(*) as cnt, SUM(frame_changed) as successes
    FROM action_traces
    WHERE game_id LIKE 'vc33%' AND created_at > datetime('now', '-2 hours')
    GROUP BY coordinates
    ORDER BY cnt DESC
    LIMIT 15
""").fetchall()
for r in rows:
    print(f"  {r['coordinates']}: {r['cnt']}x (frame_changed: {r['successes']})")

# Check ls20 action diversity
print()
print('=== LS20 ACTION DISTRIBUTION (latest gen) ===')
rows = c.execute("""
    SELECT coordinates as action_taken, COUNT(*) as cnt,
           SUM(frame_changed) as changes
    FROM action_traces
    WHERE game_id LIKE 'ls20%' AND created_at > datetime('now', '-2 hours')
    GROUP BY action_taken
    ORDER BY cnt DESC
""").fetchall()
for r in rows:
    print(f"  {r['action_taken']}: {r['cnt']}x (frame_changed: {r['changes']})")

# Check cognitive routing trace: how many different algorithms used?
print()
print('=== ALGORITHM DISTRIBUTION (latest gen) ===')
rows = c.execute("""
    SELECT algorithm_used, COUNT(*) as cnt
    FROM cognitive_routing_traces
    WHERE timestamp > datetime('now', '-2 hours')
    GROUP BY algorithm_used
    ORDER BY cnt DESC
""").fetchall()
for r in rows:
    print(f"  {r['algorithm_used']}: {r['cnt']}")

# Confidence histogram more granular
print()
print('=== CONFIDENCE GRANULAR (latest gen) ===')
rows = c.execute("""
    SELECT ROUND(final_confidence, 2) as conf, COUNT(*) as cnt
    FROM cognitive_routing_traces
    WHERE timestamp > datetime('now', '-2 hours')
    GROUP BY conf
    ORDER BY cnt DESC
    LIMIT 10
""").fetchall()
for r in rows:
    print(f"  confidence={r['conf']}: {r['cnt']} traces")

c.close()
