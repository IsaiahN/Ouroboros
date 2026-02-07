"""Compare two generations from the database. Usage: python manual_tools/gen_compare.py [gen1] [gen2]"""
import sqlite3
import sys

DB = "core_data.db"

def analyze_gen(conn, gen):
    c = conn.cursor()
    print(f"\n{'='*60}")
    print(f"  GENERATION {gen} ANALYSIS")
    print(f"{'='*60}")

    # Game results
    c.execute("""SELECT game_id, COUNT(*) as games, AVG(final_score) as avg_score,
        MAX(final_score) as max_score, AVG(total_actions) as avg_actions,
        SUM(level_completions) as total_levels, SUM(win_detected) as wins
        FROM game_results WHERE generation = ? GROUP BY game_id""", (gen,))
    rows = c.fetchall()

    print(f"\n--- Game Results ---")
    if not rows:
        print(f"  [NO DATA for generation {gen}]")
        return

    total_games = 0
    total_wins = 0
    total_levels = 0
    for r in rows:
        game_id, games, avg_score, max_score, avg_actions, levels, wins = r
        total_games += games
        total_wins += (wins or 0)
        total_levels += (levels or 0)
        print(f"  {game_id}: {games} games, avg_score={avg_score:.4f}, max={max_score:.4f}, "
              f"avg_actions={avg_actions:.0f}, levels={levels}, wins={wins}")

    print(f"  TOTALS: {total_games} games, {total_wins} wins, {total_levels} level completions")

    # Score distribution
    c.execute("""SELECT
        SUM(CASE WHEN final_score = 0 THEN 1 ELSE 0 END) as zero,
        SUM(CASE WHEN final_score > 0 AND final_score < 0.5 THEN 1 ELSE 0 END) as low,
        SUM(CASE WHEN final_score >= 0.5 THEN 1 ELSE 0 END) as high
        FROM game_results WHERE generation = ?""", (gen,))
    zero, low, high = c.fetchone()
    print(f"  Score dist: zero={zero}, low(0-0.5)={low}, high(>=0.5)={high}")

    # Timestamp range
    c.execute("SELECT MIN(created_at), MAX(created_at) FROM game_results WHERE generation = ?", (gen,))
    t_min, t_max = c.fetchone()
    print(f"  Time range: {t_min} -> {t_max}")

    # Get game session_ids for this generation to correlate with traces
    c.execute("SELECT DISTINCT session_id FROM game_results WHERE generation = ?", (gen,))
    session_ids = [r[0] for r in c.fetchall()]

    # Also get game_ids from this gen's results
    c.execute("SELECT DISTINCT game_id FROM game_results WHERE generation = ?", (gen,))
    gen_game_ids = [r[0] for r in c.fetchall()]

    # Cognitive routing traces (correlated by game_id)
    print(f"\n--- Cognitive Routing Traces ---")
    if gen_game_ids:
        placeholders = ",".join(["?"] * len(gen_game_ids))
        c.execute(f"""SELECT initial_quadrant || '->' || final_quadrant as transition,
            COUNT(*) as cnt, AVG(iterations) as avg_iters,
            AVG(final_confidence) as avg_conf,
            AVG(decision_latency_ms) as avg_latency
            FROM cognitive_routing_traces
            WHERE game_id IN ({placeholders})
            GROUP BY transition ORDER BY cnt DESC""", gen_game_ids)
        rows = c.fetchall()
    else:
        rows = []

    if not rows:
        print(f"  [NO TRACE DATA for this generation's games]")
    else:
        total_traces = 0
        for r in rows:
            trans, cnt, avg_iters, avg_conf, avg_lat = r
            total_traces += cnt
            print(f"  {trans}: {cnt} traces, avg_iters={avg_iters:.1f}, "
                  f"avg_conf={avg_conf:.3f}, avg_latency={avg_lat:.1f}ms")
        print(f"  TOTAL: {total_traces} traces")

    # Algorithm usage
    print(f"\n--- Algorithm Usage ---")
    if gen_game_ids:
        c.execute(f"""SELECT algorithm_used, COUNT(*) as cnt
            FROM cognitive_routing_traces
            WHERE game_id IN ({placeholders})
            GROUP BY algorithm_used ORDER BY cnt DESC""", gen_game_ids)
        for r in c.fetchall():
            print(f"  {r[0]}: {r[1]}")

    # Unique agents
    if gen_game_ids:
        c.execute(f"""SELECT COUNT(DISTINCT agent_id) FROM cognitive_routing_traces
            WHERE game_id IN ({placeholders})""", gen_game_ids)
        print(f"\n  Unique agents in traces: {c.fetchone()[0]}")

    # Backtrack stats
    if gen_game_ids:
        c.execute(f"""SELECT AVG(backtrack_count), MAX(backtrack_count), SUM(backtrack_count)
            FROM cognitive_routing_traces
            WHERE game_id IN ({placeholders})""", gen_game_ids)
        row = c.fetchone()
        if row and row[0] is not None:
            print(f"  Backtracks: avg={row[0]:.2f}, max={row[1]}, total={row[2]}")
        else:
            print(f"  Backtracks: [no data]")

    return t_min, t_max


def cross_gen_knowledge_transfer(conn, gen1, gen2):
    """Check if knowledge transfers between generations."""
    c = conn.cursor()
    print(f"\n{'='*60}")
    print(f"  KNOWLEDGE TRANSFER: Gen {gen1} -> Gen {gen2}")
    print(f"{'='*60}")

    # Compare transition distributions
    for gen in [gen1, gen2]:
        c.execute("SELECT DISTINCT game_id FROM game_results WHERE generation = ?", (gen,))
        game_ids = [r[0] for r in c.fetchall()]
        if not game_ids:
            print(f"  [Gen {gen}: NO DATA]")
            continue

        placeholders = ",".join(["?"] * len(game_ids))
        c.execute(f"""SELECT initial_quadrant, COUNT(*) as cnt
            FROM cognitive_routing_traces
            WHERE game_id IN ({placeholders})
            GROUP BY initial_quadrant ORDER BY cnt DESC""", game_ids)
        rows = c.fetchall()
        total = sum(r[1] for r in rows) if rows else 0
        print(f"\n  Gen {gen} - Starting quadrants (total={total}):")
        for r in rows:
            pct = r[1] / total * 100 if total else 0
            print(f"    {r[0]}: {r[1]} ({pct:.1f}%)")

    # Check if KK iterations improve
    for gen in [gen1, gen2]:
        c.execute("SELECT DISTINCT game_id FROM game_results WHERE generation = ?", (gen,))
        game_ids = [r[0] for r in c.fetchall()]
        if not game_ids:
            continue

        placeholders = ",".join(["?"] * len(game_ids))
        c.execute(f"""SELECT AVG(iterations), MIN(iterations), MAX(iterations), COUNT(*)
            FROM cognitive_routing_traces
            WHERE game_id IN ({placeholders})
            AND final_quadrant = 'KK'""", game_ids)
        row = c.fetchone()
        if row and row[0]:
            print(f"\n  Gen {gen} - KK decisions: count={row[3]}, avg_iters={row[0]:.1f}, min={row[1]}, max={row[2]}")

    # Compare scores
    print(f"\n  Score comparison:")
    for gen in [gen1, gen2]:
        c.execute("SELECT AVG(final_score), MAX(final_score), SUM(level_completions) FROM game_results WHERE generation = ?", (gen,))
        row = c.fetchone()
        if row:
            print(f"    Gen {gen}: avg={row[0]:.4f}, max={row[1]:.4f}, total_levels={row[2]}")


def main():
    gens = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else []

    conn = sqlite3.connect(DB)

    if not gens:
        # Auto-detect last 2 generations
        c = conn.cursor()
        c.execute("SELECT DISTINCT generation FROM game_results ORDER BY generation DESC LIMIT 3")
        gens = [r[0] for r in c.fetchall()]
        gens.reverse()
        print(f"Auto-detected generations: {gens}")

    for gen in gens:
        analyze_gen(conn, gen)

    if len(gens) >= 2:
        cross_gen_knowledge_transfer(conn, gens[-2], gens[-1])

    conn.close()


if __name__ == "__main__":
    main()
