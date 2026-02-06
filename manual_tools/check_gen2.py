"""Quick analysis of latest generation routing traces."""
import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import sqlite3

conn = sqlite3.connect('core_data.db')
conn.row_factory = sqlite3.Row

# Check epistemic quadrants in latest traces
print('=== EPISTEMIC QUADRANTS (latest gen) ===')
rows = conn.execute("""
    SELECT initial_quadrant, final_quadrant, COUNT(*) as cnt
    FROM cognitive_routing_traces
    WHERE timestamp > datetime('now', '-1 hour')
    GROUP BY initial_quadrant, final_quadrant
    ORDER BY cnt DESC
""").fetchall()
for r in rows:
    print(f"  {r['initial_quadrant']} -> {r['final_quadrant']}: {r['cnt']}")

total_traces = sum(r['cnt'] for r in rows)
print(f"  TOTAL: {total_traces} traces")

# Check confidence distribution
print()
print('=== CONFIDENCE DISTRIBUTION (latest gen) ===')
rows = conn.execute("""
    SELECT
        CASE
            WHEN final_confidence < 0.3 THEN '<0.3'
            WHEN final_confidence < 0.5 THEN '0.3-0.5'
            WHEN final_confidence < 0.65 THEN '0.5-0.65'
            WHEN final_confidence < 0.8 THEN '0.65-0.8'
            ELSE '0.8+'
        END as bucket,
        COUNT(*) as cnt,
        ROUND(AVG(final_confidence), 3) as avg_conf
    FROM cognitive_routing_traces
    WHERE timestamp > datetime('now', '-1 hour')
    GROUP BY bucket
    ORDER BY bucket
""").fetchall()
for r in rows:
    print(f"  {r['bucket']}: {r['cnt']} traces (avg={r['avg_conf']})")

# Check backtrack counts
print()
print('=== BACKTRACK COUNTS (latest gen) ===')
rows = conn.execute("""
    SELECT backtrack_count, COUNT(*) as cnt
    FROM cognitive_routing_traces
    WHERE timestamp > datetime('now', '-1 hour')
    GROUP BY backtrack_count
    ORDER BY backtrack_count
""").fetchall()
for r in rows:
    print(f"  backtracks={r['backtrack_count']}: {r['cnt']} traces")

# Check iteration counts (are decisions committing early now?)
print()
print('=== ITERATIONS DISTRIBUTION (latest gen) ===')
rows = conn.execute("""
    SELECT
        CASE
            WHEN iterations <= 5 THEN '1-5'
            WHEN iterations <= 15 THEN '6-15'
            WHEN iterations <= 30 THEN '16-30'
            WHEN iterations <= 49 THEN '31-49'
            ELSE '50'
        END as bucket,
        COUNT(*) as cnt,
        ROUND(AVG(iterations), 1) as avg_iter
    FROM cognitive_routing_traces
    WHERE timestamp > datetime('now', '-1 hour')
    GROUP BY bucket
    ORDER BY bucket
""").fetchall()
for r in rows:
    print(f"  {r['bucket']} iters: {r['cnt']} traces (avg={r['avg_iter']})")

# Check path diversity (are rung paths varied now?)
print()
print('=== RUNG PATH DIVERSITY (latest gen, sample 20) ===')
rows = conn.execute("""
    SELECT path, COUNT(*) as cnt
    FROM cognitive_routing_traces
    WHERE timestamp > datetime('now', '-1 hour')
    GROUP BY path
    ORDER BY cnt DESC
    LIMIT 20
""").fetchall()
unique_paths = conn.execute("""
    SELECT COUNT(DISTINCT path) as cnt
    FROM cognitive_routing_traces
    WHERE timestamp > datetime('now', '-1 hour')
""").fetchone()
print(f"  Unique paths: {unique_paths['cnt']}")
for r in rows:
    path_str = r['path'][:80] + '...' if len(str(r['path'])) > 80 else r['path']
    print(f"  x{r['cnt']}: {path_str}")

# Game results from this run
print()
print('=== GAME RESULTS (latest gen) ===')
rows = conn.execute("""
    SELECT
        SUBSTR(game_id, 1, 4) as game_type,
        COUNT(*) as games,
        SUM(CASE WHEN score > 0 THEN 1 ELSE 0 END) as nonzero,
        ROUND(AVG(score), 4) as avg_score,
        MAX(levels_completed) as max_levels,
        ROUND(AVG(actions_taken), 1) as avg_actions
    FROM game_results
    WHERE timestamp > datetime('now', '-1 hour')
    GROUP BY game_type
""").fetchall()
for r in rows:
    print(f"  {r['game_type']}: {r['games']} games, {r['nonzero']} nonzero, avg={r['avg_score']}, max_levels={r['max_levels']}, avg_actions={r['avg_actions']}")

# vc33 click coordinate sources
print()
print('=== VC33 ACTION6 COORDINATE SOURCES ===')
rows = conn.execute("""
    SELECT
        json_extract(action_metadata, '$.source') as source,
        COUNT(*) as cnt
    FROM action_traces
    WHERE game_id LIKE 'vc33%'
      AND action_taken = 'ACTION6'
      AND timestamp > datetime('now', '-1 hour')
    GROUP BY source
    ORDER BY cnt DESC
""").fetchall()
for r in rows:
    print(f"  {r['source']}: {r['cnt']}")

conn.close()
