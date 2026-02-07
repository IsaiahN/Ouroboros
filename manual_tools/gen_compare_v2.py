"""Cross-generation comparison analysis.

Usage: python manual_tools/gen_compare_v2.py [gen1] [gen2] [gen3]
If no args, analyzes the 3 most recent generations.
"""
import sqlite3
import sys
from collections import defaultdict

DB_PATH = "core_data.db"


def analyze_generation(conn, gen_id):
    """Analyze a single generation's game results."""
    c = conn.cursor()

    c.execute("""
        SELECT game_id, final_score, level_completions, total_actions
        FROM game_results WHERE generation = ?
    """, (gen_id,))
    rows = c.fetchall()

    if not rows:
        return None

    games = defaultdict(list)
    for game_id, score, levels, actions in rows:
        game_type = game_id[:4] if game_id else "unknown"
        games[game_type].append({
            'score': score or 0.0,
            'levels': levels or 0,
            'actions': actions or 0
        })

    total_games = len(rows)
    total_scores = [r[1] or 0.0 for r in rows]
    non_zero = [s for s in total_scores if s > 0]
    total_levels = sum(r[2] or 0 for r in rows)

    result = {
        'gen_id': gen_id,
        'total_games': total_games,
        'avg_score': sum(total_scores) / max(1, len(total_scores)),
        'max_score': max(total_scores) if total_scores else 0,
        'non_zero_count': len(non_zero),
        'total_levels': total_levels,
        'zero_count': total_games - len(non_zero),
        'by_game': {},
    }

    for game_type, game_list in games.items():
        scores = [g['score'] for g in game_list]
        result['by_game'][game_type] = {
            'count': len(game_list),
            'avg_score': sum(scores) / max(1, len(scores)),
            'max_score': max(scores) if scores else 0,
            'non_zero': sum(1 for s in scores if s > 0),
            'avg_actions': sum(g['actions'] for g in game_list) / max(1, len(game_list)),
            'total_levels': sum(g['levels'] for g in game_list),
        }

    return result


def analyze_traces(conn, gen_id):
    """Analyze cognitive routing traces for a generation time window."""
    c = conn.cursor()

    # Get time window from game_results
    c.execute("""
        SELECT MIN(created_at), MAX(created_at)
        FROM game_results WHERE generation = ?
    """, (gen_id,))
    row = c.fetchone()
    if not row or not row[0]:
        return None

    # Traces use different timestamp format, query all available
    c.execute("SELECT COUNT(*) FROM cognitive_routing_traces")
    total_traces = c.fetchone()[0]

    if total_traces == 0:
        return None

    c.execute("""
        SELECT initial_quadrant, final_quadrant, COUNT(*) as cnt
        FROM cognitive_routing_traces
        GROUP BY initial_quadrant, final_quadrant
        ORDER BY cnt DESC
    """)
    transitions = c.fetchall()

    c.execute("""
        SELECT iterations, COUNT(*) as cnt
        FROM cognitive_routing_traces
        GROUP BY iterations ORDER BY cnt DESC LIMIT 10
    """)
    iter_dist = c.fetchall()

    c.execute("""
        SELECT final_action, COUNT(*) as cnt
        FROM cognitive_routing_traces
        GROUP BY final_action ORDER BY cnt DESC
    """)
    action_dist = c.fetchall()

    c.execute("""
        SELECT algorithm_used, COUNT(*) as cnt
        FROM cognitive_routing_traces
        GROUP BY algorithm_used ORDER BY cnt DESC
    """)
    algo_dist = c.fetchall()

    c.execute("SELECT AVG(final_confidence) FROM cognitive_routing_traces")
    avg_conf = c.fetchone()[0] or 0.0

    return {
        'total_traces': total_traces,
        'transitions': transitions,
        'iter_dist': iter_dist,
        'action_dist': action_dist,
        'algo_dist': algo_dist,
        'avg_confidence': avg_conf,
    }


def print_comparison(gens):
    """Print side-by-side comparison."""
    print("=" * 70)
    print("  CROSS-GENERATION COMPARISON")
    print("=" * 70)

    # Header
    gen_ids = [g['gen_id'] for g in gens]
    header = f"{'Metric':<25}" + "".join(f"{'Gen ' + str(g):>15}" for g in gen_ids)
    print(header)
    print("-" * 70)

    # Game results comparison
    metrics = [
        ('Total Games', 'total_games'),
        ('Avg Score', 'avg_score'),
        ('Max Score', 'max_score'),
        ('Non-Zero Scores', 'non_zero_count'),
        ('Zero Scores', 'zero_count'),
        ('Total Levels', 'total_levels'),
    ]

    for label, key in metrics:
        vals = []
        for g in gens:
            v = g.get(key, 0)
            if isinstance(v, float):
                vals.append(f"{v:.4f}")
            else:
                vals.append(str(v))
        print(f"  {label:<23}" + "".join(f"{v:>15}" for v in vals))

    # Per-game breakdown
    all_game_types = set()
    for g in gens:
        all_game_types.update(g.get('by_game', {}).keys())

    for gt in sorted(all_game_types):
        print(f"\n  --- {gt} ---")
        for label, key in [('Count', 'count'), ('Avg Score', 'avg_score'),
                          ('Max Score', 'max_score'), ('Non-Zero', 'non_zero'),
                          ('Avg Actions', 'avg_actions'), ('Levels', 'total_levels')]:
            vals = []
            for g in gens:
                bg = g.get('by_game', {}).get(gt, {})
                v = bg.get(key, 0)
                if isinstance(v, float):
                    vals.append(f"{v:.4f}")
                else:
                    vals.append(str(v))
            print(f"    {label:<21}" + "".join(f"{v:>15}" for v in vals))


def main():
    conn = sqlite3.connect(DB_PATH)

    if len(sys.argv) > 1:
        gen_ids = [int(x) for x in sys.argv[1:]]
    else:
        c = conn.cursor()
        c.execute("SELECT DISTINCT generation FROM game_results ORDER BY generation DESC LIMIT 3")
        gen_ids = sorted([r[0] for r in c.fetchall()])

    print(f"Analyzing generations: {gen_ids}")

    gens = []
    for gid in gen_ids:
        result = analyze_generation(conn, gid)
        if result:
            gens.append(result)
        else:
            print(f"  [WARN] No data for generation {gid}")

    if gens:
        print_comparison(gens)

    # Trace analysis (only for current/latest traces in DB)
    traces = analyze_traces(conn, gen_ids[-1] if gen_ids else 0)
    if traces:
        print(f"\n--- Trace Analysis (current DB traces: {traces['total_traces']}) ---")
        print("  Quadrant transitions:")
        for t in traces['transitions']:
            print(f"    {t[0]} -> {t[1]}: {t[2]}")
        print("  Top iteration counts:")
        for i in traces['iter_dist']:
            print(f"    iters={i[0]}: {i[1]}")
        print("  Action distribution:")
        total_acts = sum(a[1] for a in traces['action_dist'])
        for a in traces['action_dist']:
            print(f"    {a[0]}: {a[1]} ({a[1]/max(1,total_acts)*100:.1f}%)")
        print("  Algorithm distribution:")
        for a in traces['algo_dist']:
            print(f"    {a[0]}: {a[1]}")
        print(f"  Avg confidence: {traces['avg_confidence']:.3f}")

    conn.close()


if __name__ == '__main__':
    main()
