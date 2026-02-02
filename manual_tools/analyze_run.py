"""Analyze evolution run results."""
import sqlite3


def main():
    conn = sqlite3.connect('core_data.db')
    c = conn.cursor()

    print("=" * 60)
    print("ANALYSIS OF 55-GENERATION LS20 EVOLUTION RUN")
    print("=" * 60)

    # Pariahs learned
    print("\n=== PARIAH PATTERNS LEARNED (What NOT to do) ===")
    c.execute("""
        SELECT pariah_name, pariah_type, action_sequence, failure_description,
               toxicity, trigger_count
        FROM pariahs
        WHERE source_game_id='ls20'
        ORDER BY trigger_count DESC LIMIT 15
    """)
    for r in c.fetchall():
        seq = r[2][:30] if r[2] else "N/A"
        print(f"  {r[0]}: type={r[1]} seq={seq} trig={r[5]} tox={r[4]:.2f}")

    # Action traces
    print("\n=== ACTION TRACES (Sample of actions executed) ===")
    c.execute("""
        SELECT action_number, frame_changed, score_change, level_number, resulted_in_game_over
        FROM action_traces WHERE game_id='ls20' LIMIT 10
    """)
    for r in c.fetchall():
        print(f"  ActionNum={r[0]} frame_changed={r[1]} score_chg={r[2]} lvl={r[3]} game_over={r[4]}")

    # Sensation learning events
    print("\n=== SENSATION LEARNING (Object awareness) ===")
    c.execute("SELECT COUNT(*) FROM sensation_learning_events WHERE game_id='ls20'")
    count = c.fetchone()[0]
    print(f"  Total sensation events for ls20: {count}")

    if count > 0:
        c.execute("""
            SELECT object_type, sensation_type, COUNT(*) as cnt
            FROM sensation_learning_events
            WHERE game_id='ls20'
            GROUP BY object_type, sensation_type
            ORDER BY cnt DESC LIMIT 10
        """)
        for r in c.fetchall():
            print(f"    Object={r[0]} Sensation={r[1]} count={r[2]}")

    # Agent population stats
    print("\n=== AGENT POPULATION ===")
    c.execute("SELECT COUNT(*), MAX(generation) FROM agents WHERE is_active=1")
    active, max_gen = c.fetchone()
    print(f"  Active agents: {active}")
    print(f"  Max generation: {max_gen}")

    c.execute("""
        SELECT specialization, COUNT(*) FROM agents
        WHERE is_active=1
        GROUP BY specialization
    """)
    for r in c.fetchall():
        print(f"    Specialization {r[0]}: {r[1]} agents")

    # Exploration tracker
    print("\n=== EXPLORATION TRACKER ===")
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='network_exploration_tracker'")
    if c.fetchone():
        c.execute("""
            SELECT * FROM network_exploration_tracker
            WHERE game_id='ls20' LIMIT 5
        """)
        for r in c.fetchall():
            print(f"  {r}")
    else:
        print("  Table does not exist")

    # Topology memory (action patterns per game state)
    print("\n=== TOPOLOGY MEMORY (State-Action patterns) ===")
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='topology_memory'")
    if c.fetchone():
        c.execute("SELECT COUNT(*) FROM topology_memory WHERE game_id='ls20'")
        topo_count = c.fetchone()[0]
        print(f"  Total topology entries for ls20: {topo_count}")

        if topo_count > 0:
            c.execute("""
                SELECT action, times_observed, times_scored, times_died
                FROM topology_memory
                WHERE game_id='ls20'
                ORDER BY times_observed DESC LIMIT 10
            """)
            for r in c.fetchall():
                print(f"    Action={r[0]} observed={r[1]} scored={r[2]} died={r[3]}")
    else:
        print("  Table does not exist")

    # Game level progress
    print("\n=== GAME LEVEL PROGRESS ===")
    c.execute("""
        SELECT MAX(level_completions), AVG(level_completions),
               COUNT(DISTINCT session_id), MAX(frame_changes)
        FROM game_results WHERE game_id='ls20'
    """)
    row = c.fetchone()
    print(f"  Max level completions: {row[0]}")
    avg_level = f"{row[1]:.2f}" if row[1] else "0"
    print(f"  Avg level completions: {avg_level}")
    print(f"  Total sessions: {row[2]}")
    print(f"  Max frame changes: {row[3]}")

    # Check if any positive scores ever happened
    print("\n=== SCORE ANALYSIS ===")
    c.execute("SELECT MAX(final_score), SUM(final_score) FROM game_results WHERE game_id='ls20'")
    row = c.fetchone()
    print(f"  Best score: {row[0]}")
    print(f"  Total score (sum): {row[1]}")

    c.execute("SELECT COUNT(*) FROM game_results WHERE game_id='ls20' AND final_score > 0")
    positive = c.fetchone()[0]
    print(f"  Games with positive score: {positive}")

    # Check decision rung performance
    print("\n=== DECISION RUNG SYSTEM ===")
    c.execute("""
        SELECT chosen_reason, COUNT(*) as cnt
        FROM action_proposals_log
        WHERE chosen_action LIKE 'ACTION%'
        GROUP BY chosen_reason
        ORDER BY cnt DESC LIMIT 10
    """)
    print("  Top decision reasons:")
    for r in c.fetchall():
        reason = r[0][:60] if r[0] else "N/A"
        print(f"    ({r[1]:5d}x) {reason}")

    conn.close()

    print("\n" + "=" * 60)
    print("DIAGNOSIS")
    print("=" * 60)
    print("""
FINDINGS:
1. ACTION1 dominates (41k uses) - likely UP movement
2. 'performance_stall' is top reason (14k) - hitting plateau fast
3. Pariahs are being learned - system knows what fails
4. No positive scores - not making progress toward game goals
5. TOPOLOGY rung working - tracking action outcomes per state

POTENTIAL ISSUES:
- System may be stuck in exploration loop
- Game mechanics not understood yet
- Need to verify actions are actually moving game state
- May need more diverse action selection early on
""")

if __name__ == "__main__":
    main()
