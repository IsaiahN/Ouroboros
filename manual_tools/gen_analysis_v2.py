"""Proper generation analysis using correct timestamp correlation."""
import sqlite3
import sys

DB = "core_data.db"
# game_results.created_at is ~6 hours ahead of cognitive_routing_traces.timestamp
# traces use ISO format (T), game_results use space format
# We'll use trace timestamps directly with known offset

def get_trace_window(conn, gen):
    """Get the trace timestamp window for a generation by applying 6hr offset."""
    c = conn.cursor()
    c.execute("SELECT MIN(created_at), MAX(created_at) FROM game_results WHERE generation = ?", (gen,))
    row = c.fetchone()
    if not row or not row[0]:
        return None, None

    # game_results timestamps are in format "2026-02-06 23:34:45" (UTC+6?)
    # traces timestamps are in format "2026-02-06T17:34:00" (local/UTC?)
    # We need to find the actual trace boundary by looking around the gen's game_results

    # Strategy: find all gens and their game_result time ranges, then identify
    # trace boundaries by the gap between gens
    return row[0], row[1]


def analyze_gen(conn, gen, trace_start=None, trace_end=None):
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

    # Traces by time window
    if trace_start and trace_end:
        print(f"\n--- Cognitive Routing Traces (time window: {trace_start} to {trace_end}) ---")
        c.execute("""SELECT initial_quadrant || '->' || final_quadrant as transition,
            COUNT(*) as cnt, AVG(iterations) as avg_iters,
            AVG(final_confidence) as avg_conf,
            AVG(decision_latency_ms) as avg_latency
            FROM cognitive_routing_traces
            WHERE timestamp >= ? AND timestamp <= ?
            GROUP BY transition ORDER BY cnt DESC""", (trace_start, trace_end))
        rows = c.fetchall()

        if not rows:
            print(f"  [NO TRACE DATA in window]")
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
        c.execute("""SELECT algorithm_used, COUNT(*) as cnt
            FROM cognitive_routing_traces
            WHERE timestamp >= ? AND timestamp <= ?
            GROUP BY algorithm_used ORDER BY cnt DESC""", (trace_start, trace_end))
        for r in c.fetchall():
            print(f"  {r[0]}: {r[1]}")

        # Starting quadrants
        print(f"\n--- Starting Quadrant Distribution ---")
        c.execute("""SELECT initial_quadrant, COUNT(*) as cnt
            FROM cognitive_routing_traces
            WHERE timestamp >= ? AND timestamp <= ?
            GROUP BY initial_quadrant ORDER BY cnt DESC""", (trace_start, trace_end))
        total = 0
        rows = c.fetchall()
        total = sum(r[1] for r in rows)
        for r in rows:
            pct = r[1] / total * 100 if total else 0
            print(f"  {r[0]}: {r[1]} ({pct:.1f}%)")

        # KK-specific analysis
        print(f"\n--- KK Algorithm Performance ---")
        c.execute("""SELECT AVG(iterations), MIN(iterations), MAX(iterations), COUNT(*)
            FROM cognitive_routing_traces
            WHERE timestamp >= ? AND timestamp <= ?
            AND initial_quadrant = 'KK'""", (trace_start, trace_end))
        row = c.fetchone()
        if row and row[0]:
            print(f"  KK decisions: count={row[3]}, avg_iters={row[0]:.1f}, min={row[1]}, max={row[2]}")
        else:
            print(f"  KK decisions: [none]")

        # Unique agents
        c.execute("""SELECT COUNT(DISTINCT agent_id) FROM cognitive_routing_traces
            WHERE timestamp >= ? AND timestamp <= ?""", (trace_start, trace_end))
        print(f"\n  Unique agents: {c.fetchone()[0]}")

        # Backtrack stats
        c.execute("""SELECT AVG(backtrack_count), MAX(backtrack_count), SUM(backtrack_count)
            FROM cognitive_routing_traces
            WHERE timestamp >= ? AND timestamp <= ?""", (trace_start, trace_end))
        row = c.fetchone()
        if row and row[0] is not None:
            print(f"  Backtracks: avg={row[0]:.2f}, max={row[1]}, total={row[2]}")


def find_gen_trace_windows(conn):
    """Find trace timestamp windows by analyzing gaps in trace timestamps."""
    c = conn.cursor()

    # Get all generation time ranges from game_results
    c.execute("""SELECT generation, MIN(created_at), MAX(created_at), COUNT(*)
        FROM game_results GROUP BY generation ORDER BY generation""")
    gens = c.fetchall()

    # Get trace timestamp boundaries
    c.execute("SELECT MIN(timestamp), MAX(timestamp) FROM cognitive_routing_traces")
    trace_min, trace_max = c.fetchone()

    print(f"Trace range: {trace_min} -> {trace_max}")
    print(f"Generations in DB: {len(gens)}")

    # Find significant time gaps in traces (>30 seconds = generation boundary)
    c.execute("""
        WITH ordered AS (
            SELECT timestamp, ROW_NUMBER() OVER (ORDER BY timestamp) as rn
            FROM cognitive_routing_traces
        ),
        gaps AS (
            SELECT a.timestamp as gap_start, b.timestamp as gap_end,
                   julianday(b.timestamp) - julianday(a.timestamp) as gap_days
            FROM ordered a JOIN ordered b ON b.rn = a.rn + 1
            WHERE julianday(b.timestamp) - julianday(a.timestamp) > 0.0003  -- ~30 seconds
        )
        SELECT gap_start, gap_end, gap_days * 86400 as gap_seconds
        FROM gaps ORDER BY gap_start
        LIMIT 20
    """)
    gaps = c.fetchall()
    print(f"\nSignificant gaps (>30s) in traces:")
    for g in gaps:
        print(f"  {g[0]} -> {g[1]} ({g[2]:.0f}s)")

    return gens, gaps


def main():
    conn = sqlite3.connect(DB)

    if len(sys.argv) > 1 and sys.argv[1] == '--windows':
        find_gen_trace_windows(conn)
        conn.close()
        return

    gens = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else []

    if not gens:
        c = conn.cursor()
        c.execute("SELECT DISTINCT generation FROM game_results ORDER BY generation DESC LIMIT 3")
        gens = [r[0] for r in c.fetchall()]
        gens.reverse()
        print(f"Auto-detected: {gens}")

    # For now, use known gen 5013 window from terminal logs
    # Gen 5013 ran 17:34-17:40 local time
    known_windows = {
        5013: ('2026-02-06T17:34:00', '2026-02-06T17:40:00'),
    }

    for gen in gens:
        window = known_windows.get(gen)
        if window:
            analyze_gen(conn, gen, window[0], window[1])
        else:
            analyze_gen(conn, gen)

    conn.close()


if __name__ == "__main__":
    main()
