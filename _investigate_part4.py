"""Part 4 - VC33 why always 50 actions, and deeper rung analysis."""
import json
import sqlite3
from collections import Counter

conn = sqlite3.connect('core_data.db')
c = conn.cursor()

# Check if VC33 games are dying/game_over at action 50
print("=== VC33 action_traces: max action_number per session ===")
max_id = c.execute("SELECT MAX(id) FROM action_traces").fetchone()[0]
vc33_sessions = c.execute("""
    SELECT session_id, MAX(action_number) as max_act,
           COUNT(*) as total,
           MAX(resulted_in_game_over) as game_over
    FROM action_traces
    WHERE id > ? AND game_id LIKE '%vc33%'
    GROUP BY session_id
    ORDER BY max_act DESC
    LIMIT 20
""", (max_id - 50000,)).fetchall()
for sid, max_act, total, go in vc33_sessions:
    print(f"  session={sid[:20]}... max_action={max_act} total_actions={total} game_over={go}")

# Check game_results for VC33 - is there a total_actions pattern?
print("\n=== VC33 game_results action distribution ===")
rows = c.execute("""
    SELECT total_actions, COUNT(*) as cnt
    FROM game_results
    WHERE game_id LIKE '%vc33%'
    GROUP BY total_actions
    ORDER BY cnt DESC
    LIMIT 10
""").fetchall()
for ta, cnt in rows:
    print(f"  total_actions={ta}: {cnt} games")

# Check LS20 action distribution
print("\n=== LS20 game_results action distribution ===")
rows = c.execute("""
    SELECT total_actions, COUNT(*) as cnt
    FROM game_results
    WHERE game_id LIKE '%ls20%'
    GROUP BY total_actions
    ORDER BY cnt DESC
    LIMIT 10
""").fetchall()
for ta, cnt in rows:
    print(f"  total_actions={ta}: {cnt} games")

# Check if VC33 always gets game_over at action 50
print("\n=== VC33: last action resulted_in_game_over? ===")
vc33_last = c.execute("""
    SELECT
        SUM(CASE WHEN resulted_in_game_over = 1 THEN 1 ELSE 0 END) as game_over,
        SUM(CASE WHEN resulted_in_game_over = 0 THEN 1 ELSE 0 END) as not_over,
        SUM(CASE WHEN resulted_in_game_over IS NULL THEN 1 ELSE 0 END) as null_val,
        COUNT(*) as total
    FROM action_traces
    WHERE id > ? AND game_id LIKE '%vc33%'
    AND action_number = (
        SELECT MAX(at2.action_number)
        FROM action_traces at2
        WHERE at2.session_id = action_traces.session_id
    )
""", (max_id - 100000,)).fetchone()
print(f"  game_over={vc33_last[0]} not_over={vc33_last[1]} null={vc33_last[2]} total={vc33_last[3]}")

# Check VC33 level_number progression in action_traces
print("\n=== VC33 level_number distribution in action_traces ===")
rows = c.execute("""
    SELECT level_number, COUNT(*) as cnt
    FROM action_traces
    WHERE id > ? AND game_id LIKE '%vc33%'
    GROUP BY level_number
    ORDER BY level_number
""", (max_id - 100000,)).fetchall()
for level, cnt in rows:
    print(f"  level={level}: {cnt} actions")

# For comparison, LS20 level progression
print("\n=== LS20 level_number distribution in action_traces ===")
rows = c.execute("""
    SELECT level_number, COUNT(*) as cnt
    FROM action_traces
    WHERE id > ? AND game_id LIKE '%ls20%'
    GROUP BY level_number
    ORDER BY level_number
""", (max_id - 100000,)).fetchall()
for level, cnt in rows:
    print(f"  level={level}: {cnt} actions")

# Check VC33 score changes in detail
print("\n=== VC33 score_before/score_after distribution ===")
rows = c.execute("""
    SELECT
        ROUND(score_before, 4) as sb,
        ROUND(score_after, 4) as sa,
        COUNT(*) as cnt
    FROM action_traces
    WHERE id > ? AND game_id LIKE '%vc33%'
    GROUP BY sb, sa
    ORDER BY cnt DESC
    LIMIT 10
""", (max_id - 100000,)).fetchall()
for sb, sa, cnt in rows:
    print(f"  score: {sb} -> {sa} ({cnt} times)")

# Check what the cognitive routing traces say about VC33 rung path composition
print("\n=== VC33 cognitive routing: path analysis ===")
crt_max = c.execute("SELECT MAX(id) FROM cognitive_routing_traces").fetchone()[0]
vc33_routes = c.execute("""
    SELECT path, final_action, final_confidence, algorithm_used
    FROM cognitive_routing_traces
    WHERE id > ? AND game_id LIKE '%vc33%'
    LIMIT 200
""", (crt_max - 5000,)).fetchall()

path_lengths = []
final_rungs = Counter()
algorithms = Counter()
actions = Counter()
all_rungs = Counter()

for path, action, conf, algo in vc33_routes:
    if path:
        try:
            pl = json.loads(path) if isinstance(path, str) else path
            if isinstance(pl, list):
                path_lengths.append(len(pl))
                if pl:
                    final_rungs[pl[-1]] += 1
                for r in pl:
                    all_rungs[r] += 1
        except:
            pass
    actions[action] += 1
    algorithms[algo] += 1

print(f"  Total VC33 routing decisions analyzed: {len(vc33_routes)}")
if path_lengths:
    print(f"  Path lengths: avg={sum(path_lengths)/len(path_lengths):.1f} min={min(path_lengths)} max={max(path_lengths)}")
print(f"  Final (winning) rungs:")
for rung, cnt in final_rungs.most_common(10):
    print(f"    {rung}: {cnt} times ({cnt*100//max(len(vc33_routes),1)}%)")
print(f"  All rungs in paths:")
for rung, cnt in all_rungs.most_common(10):
    print(f"    {rung}: {cnt} times")
print(f"  Actions: {dict(actions.most_common(10))}")
print(f"  Algorithms: {dict(algorithms.most_common(5))}")

# Now check: does VC33 EVER have frame_changed=1 AND score_change != 0?
print("\n=== VC33: frame_changed=1 actions analysis ===")
rows = c.execute("""
    SELECT coordinates, score_change, level_number, action_number, session_id
    FROM action_traces
    WHERE id > ? AND game_id LIKE '%vc33%' AND frame_changed = 1
    LIMIT 30
""", (max_id - 100000,)).fetchall()
print(f"  Found {len(rows)} frame-changed VC33 actions")
for r in rows[:15]:
    print(f"    coords={r[0]} score_change={r[1]} level={r[2]} action={r[3]} session={r[4][:16]}...")

# Compare: LS20 frame_changed=1 actions
print("\n=== LS20: frame_changed=1 actions analysis ===")
rows = c.execute("""
    SELECT coordinates, score_change, level_number, action_number, session_id
    FROM action_traces
    WHERE id > ? AND game_id LIKE '%ls20%' AND frame_changed = 1
    LIMIT 30
""", (max_id - 100000,)).fetchall()
print(f"  Found {len(rows)} frame-changed LS20 actions")
for r in rows[:15]:
    print(f"    coords={r[0]} score_change={r[1]} level={r[2]} action={r[3]} session={r[4][:16]}...")

conn.close()
print("\n=== DONE ===")
