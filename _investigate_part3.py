"""Part 3 - Rung monopoly analysis from cognitive_routing_traces."""
import json
import sqlite3
from collections import Counter, defaultdict

conn = sqlite3.connect('core_data.db')
c = conn.cursor()

max_id = c.execute("SELECT MAX(id) FROM cognitive_routing_traces").fetchone()[0]
print(f"Max cognitive_routing_traces id: {max_id}")

# Get recent 2000 routing traces
print("\n=== Recent 2000 routing traces analysis ===")
recent = c.execute("""
    SELECT game_id, path, algorithm_used, final_action, final_confidence,
           initial_quadrant, final_quadrant, iterations, agent_id
    FROM cognitive_routing_traces
    WHERE id > ?
    ORDER BY id DESC
    LIMIT 2000
""", (max_id - 2000,)).fetchall()

# Analyze path (which rung was used)
game_rung_counts = defaultdict(Counter)
game_algorithm_counts = defaultdict(Counter)
game_action_counts = defaultdict(Counter)
game_confidence = defaultdict(list)
game_quadrants = defaultdict(Counter)
game_total = Counter()

for row in recent:
    gid = row[0] or ""
    if 'ft09' in gid.lower():
        gt = 'FT09'
    elif 'ls20' in gid.lower():
        gt = 'LS20'
    elif 'vc33' in gid.lower():
        gt = 'VC33'
    else:
        gt = gid[:8] if gid else 'UNKNOWN'

    game_total[gt] += 1

    # Parse path - it might be JSON or a string
    path = row[1]
    if path:
        try:
            path_list = json.loads(path) if isinstance(path, str) else path
            if isinstance(path_list, list):
                for rung_name in path_list:
                    game_rung_counts[gt][rung_name] += 1
                # The LAST rung in the path is the one that "won"
                if path_list:
                    game_rung_counts[gt + '_WINNER'] = game_rung_counts.get(gt + '_WINNER', Counter())
                    game_rung_counts[gt + '_WINNER'][path_list[-1]] += 1
        except (json.JSONDecodeError, TypeError):
            game_rung_counts[gt][str(path)[:50]] += 1

    game_algorithm_counts[gt][row[2]] += 1
    game_action_counts[gt][row[3]] += 1
    game_confidence[gt].append(row[4] or 0.0)
    game_quadrants[gt][f"{row[5]}->{row[6]}"] += 1

for gt in sorted(game_total.keys()):
    total = game_total[gt]
    print(f"\n=== {gt} ({total} decisions) ===")

    # Rung usage
    print(f"  Rungs evaluated (all in path):")
    for rung, cnt in game_rung_counts[gt].most_common(10):
        print(f"    {rung}: {cnt} times ({cnt*100//max(total,1)}%)")

    # Winning rung
    winner_key = gt + '_WINNER'
    if winner_key in game_rung_counts:
        print(f"  WINNING rung (last in path):")
        for rung, cnt in game_rung_counts[winner_key].most_common(10):
            print(f"    {rung}: {cnt} wins ({cnt*100//max(total,1)}%)")

    # Algorithm distribution
    print(f"  Algorithms used:")
    for algo, cnt in game_algorithm_counts[gt].most_common(5):
        print(f"    {algo}: {cnt} ({cnt*100//max(total,1)}%)")

    # Action distribution
    print(f"  Actions taken:")
    for action, cnt in game_action_counts[gt].most_common(10):
        print(f"    {action}: {cnt} ({cnt*100//max(total,1)}%)")

    # Confidence stats
    confs = game_confidence[gt]
    if confs:
        avg_conf = sum(confs) / len(confs)
        min_conf = min(confs)
        max_conf = max(confs)
        # Confidence buckets
        buckets = Counter()
        for c_val in confs:
            if c_val < 0.2:
                buckets['<0.2'] += 1
            elif c_val < 0.4:
                buckets['0.2-0.4'] += 1
            elif c_val < 0.6:
                buckets['0.4-0.6'] += 1
            elif c_val < 0.8:
                buckets['0.6-0.8'] += 1
            else:
                buckets['0.8-1.0'] += 1
        print(f"  Confidence: avg={avg_conf:.3f} min={min_conf:.3f} max={max_conf:.3f}")
        print(f"  Confidence buckets: {dict(buckets)}")

    # Quadrant transitions
    print(f"  Quadrant transitions:")
    for qt, cnt in game_quadrants[gt].most_common(5):
        print(f"    {qt}: {cnt} ({cnt*100//max(total,1)}%)")

# Now check: do VC33 sessions ALWAYS get 0 score?
print("\n\n=== game_results: level_completions by game type ===")
for pattern, label in [('%vc33%', 'VC33'), ('%ls20%', 'LS20'), ('%ft09%', 'FT09')]:
    stats = c.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN level_completions > 0 THEN 1 ELSE 0 END) as with_levels,
            MAX(level_completions) as max_levels,
            AVG(final_score) as avg_score,
            MAX(final_score) as max_score,
            AVG(total_actions) as avg_actions
        FROM game_results
        WHERE game_id LIKE ?
    """, (pattern,)).fetchone()
    print(f"  {label}: {stats[0]} games, {stats[1]} with levels, max={stats[2]}, avg_score={stats[3]:.6f}, max_score={stats[4]}, avg_actions={stats[5]:.1f}")

# Check frame_changes column specifically
print("\n=== frame_changes column analysis ===")
for pattern, label in [('%vc33%', 'VC33'), ('%ls20%', 'LS20'), ('%ft09%', 'FT09')]:
    stats = c.execute("""
        SELECT
            SUM(frame_changes) as total_frame_changes,
            AVG(frame_changes) as avg_frame_changes,
            MAX(frame_changes) as max_frame_changes,
            SUM(CASE WHEN frame_changes > 0 THEN 1 ELSE 0 END) as games_with_changes,
            COUNT(*) as total_games
        FROM game_results
        WHERE game_id LIKE ?
    """, (pattern,)).fetchone()
    print(f"  {label}: total_changes={stats[0]} avg={stats[1]:.2f} max={stats[2]} games_with_changes={stats[3]}/{stats[4]}")

# Check action_traces frame_changed vs game_results frame_changes
print("\n=== action_traces frame_changed verification (recent 5000) ===")
recent_traces = c.execute("""
    SELECT
        CASE
            WHEN game_id LIKE '%ft09%' THEN 'FT09'
            WHEN game_id LIKE '%ls20%' THEN 'LS20'
            WHEN game_id LIKE '%vc33%' THEN 'VC33'
            ELSE 'OTHER'
        END as game_type,
        SUM(CASE WHEN frame_changed = 1 THEN 1 ELSE 0 END) as changed,
        SUM(CASE WHEN frame_changed = 0 THEN 1 ELSE 0 END) as unchanged,
        COUNT(*) as total
    FROM action_traces
    WHERE id > (SELECT MAX(id) FROM action_traces) - 5000
    GROUP BY game_type
""").fetchall()
for gt, changed, unchanged, total in recent_traces:
    print(f"  {gt}: {changed}/{total} frames changed ({changed*100//max(total,1)}%)")

# Check LS20 games with level completions - what makes them different?
print("\n=== LS20 games WITH level completions (sample) ===")
rows = c.execute("""
    SELECT game_id, session_id, final_score, level_completions, total_actions,
           generation, frame_changes, coordinate_attempts, coordinate_successes
    FROM game_results
    WHERE game_id LIKE '%ls20%' AND level_completions > 0
    ORDER BY generation DESC
    LIMIT 10
""").fetchall()
for r in rows:
    print(f"  gen={r[5]} score={r[2]:.4f} levels={r[3]} actions={r[4]} frames={r[6]} coord_att={r[7]} coord_succ={r[8]}")

# Check VC33 games - are they all 0 level completions and 0 score?
print("\n=== VC33 games (recent by generation) ===")
rows = c.execute("""
    SELECT generation, COUNT(*) as games,
           SUM(CASE WHEN level_completions > 0 THEN 1 ELSE 0 END) as with_levels,
           AVG(final_score) as avg_score,
           AVG(total_actions) as avg_actions,
           AVG(frame_changes) as avg_frames
    FROM game_results
    WHERE game_id LIKE '%vc33%'
    GROUP BY generation
    ORDER BY generation DESC
    LIMIT 20
""").fetchall()
for r in rows:
    print(f"  gen={r[0]}: {r[1]} games, {r[2]} with_levels, avg_score={r[3]:.4f}, avg_actions={r[4]:.1f}, avg_frames={r[5]:.1f}")

# CRITICAL: Check what VC33 available_actions are
print("\n=== VC33 available_actions in game_results ===")
rows = c.execute("""
    SELECT available_actions, COUNT(*)
    FROM game_results
    WHERE game_id LIKE '%vc33%'
    GROUP BY available_actions
""").fetchall()
for aa, cnt in rows:
    print(f"  '{aa}': {cnt} games")

# Same for LS20
print("\n=== LS20 available_actions in game_results ===")
rows = c.execute("""
    SELECT available_actions, COUNT(*)
    FROM game_results
    WHERE game_id LIKE '%ls20%'
    GROUP BY available_actions
""").fetchall()
for aa, cnt in rows:
    print(f"  '{aa}': {cnt} games")

# Same for FT09
print("\n=== FT09 available_actions in game_results ===")
rows = c.execute("""
    SELECT available_actions, COUNT(*)
    FROM game_results
    WHERE game_id LIKE '%ft09%'
    GROUP BY available_actions
""").fetchall()
for aa, cnt in rows:
    print(f"  '{aa}': {cnt} games")

conn.close()
print("\n=== DONE ===")
