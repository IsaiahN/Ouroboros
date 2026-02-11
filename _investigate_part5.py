"""Part 5 - VC33 cognitive routing rung monopoly deep dive."""
import json
import sqlite3
from collections import Counter

conn = sqlite3.connect('core_data.db')
c = conn.cursor()

crt_max = c.execute("SELECT MAX(id) FROM cognitive_routing_traces").fetchone()[0]

# Get VC33-specific routing traces - wider search
print("=== VC33 cognitive routing traces (searching wider) ===")
vc33_routes = c.execute("""
    SELECT path, final_action, final_confidence, algorithm_used, agent_id
    FROM cognitive_routing_traces
    WHERE game_id LIKE '%vc33%'
    AND id > ?
    LIMIT 500
""", (crt_max - 100000,)).fetchall()

print(f"Found {len(vc33_routes)} VC33 routing traces")

final_rungs = Counter()
all_rungs_in_path = Counter()
algorithms = Counter()
actions = Counter()
confidences = []
path_lengths = []

for path, action, conf, algo, agent in vc33_routes:
    if path:
        try:
            pl = json.loads(path) if isinstance(path, str) else path
            if isinstance(pl, list):
                path_lengths.append(len(pl))
                if pl:
                    final_rungs[pl[-1]] += 1
                for r in pl:
                    all_rungs_in_path[r] += 1
        except:
            pass
    actions[action] += 1
    algorithms[algo] += 1
    confidences.append(conf or 0.0)

total = len(vc33_routes)
print(f"\nFINAL (winning) rungs for VC33:")
for rung, cnt in final_rungs.most_common(15):
    pct = cnt * 100 // max(total, 1)
    print(f"  {rung}: {cnt} wins ({pct}%)")

print(f"\nALL rungs evaluated in paths:")
for rung, cnt in all_rungs_in_path.most_common(15):
    print(f"  {rung}: {cnt} evals")

print(f"\nActions: {dict(actions.most_common(10))}")
print(f"Algorithms: {dict(algorithms.most_common(5))}")
if confidences:
    print(f"Confidence: avg={sum(confidences)/len(confidences):.3f} min={min(confidences):.3f} max={max(confidences):.3f}")
if path_lengths:
    print(f"Path lengths: avg={sum(path_lengths)/len(path_lengths):.1f} min={min(path_lengths)} max={max(path_lengths)}")

# Now also check FT09 rung details
print("\n\n=== FT09 cognitive routing traces ===")
ft09_routes = c.execute("""
    SELECT path, final_action, final_confidence, algorithm_used
    FROM cognitive_routing_traces
    WHERE game_id LIKE '%ft09%'
    AND id > ?
    LIMIT 500
""", (crt_max - 100000,)).fetchall()

print(f"Found {len(ft09_routes)} FT09 routing traces")

ft_final = Counter()
ft_all = Counter()
ft_actions = Counter()
ft_algos = Counter()
ft_confs = []

for path, action, conf, algo in ft09_routes:
    if path:
        try:
            pl = json.loads(path) if isinstance(path, str) else path
            if isinstance(pl, list):
                if pl:
                    ft_final[pl[-1]] += 1
                for r in pl:
                    ft_all[r] += 1
        except:
            pass
    ft_actions[action] += 1
    ft_algos[algo] += 1
    ft_confs.append(conf or 0.0)

print(f"\nFINAL (winning) rungs for FT09:")
for rung, cnt in ft_final.most_common(15):
    pct = cnt * 100 // max(len(ft09_routes), 1)
    print(f"  {rung}: {cnt} wins ({pct}%)")

print(f"\nALL rungs evaluated:")
for rung, cnt in ft_all.most_common(15):
    print(f"  {rung}: {cnt} evals")

print(f"\nActions: {dict(ft_actions.most_common(10))}")
if ft_confs:
    print(f"Confidence: avg={sum(ft_confs)/len(ft_confs):.3f}")

# Check LS20 - how does it achieve level completions?
print("\n\n=== LS20 cognitive routing traces ===")
ls20_routes = c.execute("""
    SELECT path, final_action, final_confidence, algorithm_used
    FROM cognitive_routing_traces
    WHERE game_id LIKE '%ls20%'
    AND id > ?
    LIMIT 500
""", (crt_max - 100000,)).fetchall()

print(f"Found {len(ls20_routes)} LS20 routing traces")

ls_final = Counter()
ls_all = Counter()
ls_actions = Counter()
ls_confs = []

for path, action, conf, algo in ls20_routes:
    if path:
        try:
            pl = json.loads(path) if isinstance(path, str) else path
            if isinstance(pl, list):
                if pl:
                    ls_final[pl[-1]] += 1
                for r in pl:
                    ls_all[r] += 1
        except:
            pass
    ls_actions[action] += 1
    ls_confs.append(conf or 0.0)

print(f"\nFINAL (winning) rungs for LS20:")
for rung, cnt in ls_final.most_common(15):
    pct = cnt * 100 // max(len(ls20_routes), 1)
    print(f"  {rung}: {cnt} wins ({pct}%)")

print(f"\nActions: {dict(ls_actions.most_common(10))}")
if ls_confs:
    print(f"Confidence: avg={sum(ls_confs)/len(ls_confs):.3f}")

# KEY QUESTION: What's the score pattern for VC33?
# VC33 has ZERO level completions, what is the score trajectory?
print("\n\n=== VC33 score trajectory (single session example) ===")
at_max = c.execute("SELECT MAX(id) FROM action_traces").fetchone()[0]
vc33_session = c.execute("""
    SELECT DISTINCT session_id FROM action_traces
    WHERE game_id LIKE '%vc33%' AND id > ?
    LIMIT 1
""", (at_max - 50000,)).fetchone()

if vc33_session:
    sid = vc33_session[0]
    actions = c.execute("""
        SELECT action_number, coordinates, score_before, score_after,
               score_change, frame_changed, level_number
        FROM action_traces
        WHERE session_id = ?
        ORDER BY action_number
    """, (sid,)).fetchall()
    print(f"Session {sid[:20]}... ({len(actions)} actions)")
    for a in actions:
        fc = "[CHANGED]" if a[5] else ""
        print(f"  #{a[0]:2d} coords={a[1]:30s} score={a[2]:.4f}->{a[3]:.4f} delta={a[4]:.4f} level={a[6]} {fc}")

conn.close()
print("\n=== DONE ===")
