"""Analyze evolution run results with correct game_id."""
import sqlite3


def main():
    conn = sqlite3.connect('core_data.db')
    c = conn.cursor()

    print("=" * 60)
    print("ANALYSIS OF 55-GENERATION LS20 EVOLUTION RUN")
    print("=" * 60)

    # Game results
    print("\n=== GAME RESULTS ===")
    c.execute("""
        SELECT COUNT(*), SUM(total_actions), MAX(total_actions), MIN(total_actions),
               MAX(final_score), MAX(level_completions), MAX(frame_changes)
        FROM game_results WHERE game_id LIKE 'ls20%'
    """)
    r = c.fetchone()
    print(f"  Total games: {r[0]}")
    print(f"  Total actions: {r[1]}")
    print(f"  Max actions/game: {r[2]}")
    print(f"  Min actions/game: {r[3]}")
    print(f"  Best score: {r[4]}")
    print(f"  Max level completions: {r[5]}")
    print(f"  Max frame changes: {r[6]}")

    # Action distribution per game
    print("\n=== ACTIONS PER GAME DISTRIBUTION ===")
    c.execute("""
        SELECT total_actions, COUNT(*) as games
        FROM game_results WHERE game_id LIKE 'ls20%'
        GROUP BY total_actions ORDER BY games DESC LIMIT 10
    """)
    for r in c.fetchall():
        print(f"  {r[0]} actions: {r[1]} games")

    # Action traces
    print("\n=== ACTION TRACES ===")
    c.execute("SELECT COUNT(*) FROM action_traces WHERE game_id LIKE 'ls20%'")
    print(f"  Total action traces: {c.fetchone()[0]}")

    c.execute("""
        SELECT frame_changed, COUNT(*)
        FROM action_traces WHERE game_id LIKE 'ls20%'
        GROUP BY frame_changed
    """)
    for r in c.fetchall():
        print(f"    frame_changed={r[0]}: {r[1]}")

    # Score changes in action traces
    c.execute("""
        SELECT MIN(score_change), MAX(score_change), AVG(score_change)
        FROM action_traces WHERE game_id LIKE 'ls20%'
    """)
    r = c.fetchone()
    print(f"  Score changes: min={r[0]} max={r[1]} avg={r[2]}")

    # Pariahs
    print("\n=== PARIAHS (Learned failures) ===")
    c.execute("SELECT COUNT(*) FROM pariahs WHERE source_game_id LIKE 'ls20%'")
    total_pariahs = c.fetchone()[0]
    print(f"  Total pariahs: {total_pariahs}")

    if total_pariahs > 0:
        c.execute("""
            SELECT pariah_name, pariah_type, toxicity, trigger_count
            FROM pariahs WHERE source_game_id LIKE 'ls20%'
            ORDER BY trigger_count DESC LIMIT 10
        """)
        for r in c.fetchall():
            print(f"    {r[0]}: type={r[1]} tox={r[2]:.2f} triggers={r[3]}")

    # Action proposals analysis
    print("\n=== ACTION SELECTION (Decision System) ===")
    c.execute("""
        SELECT chosen_action, COUNT(*) as cnt
        FROM action_proposals_log
        WHERE chosen_action LIKE 'ACTION%'
        GROUP BY chosen_action ORDER BY cnt DESC
    """)
    for r in c.fetchall():
        print(f"  {r[0]}: {r[1]} times")

    # Why ACTION1 so dominant?
    print("\n=== WHY ACTION1? (Top reasons for ACTION1) ===")
    c.execute("""
        SELECT chosen_reason, COUNT(*) as cnt
        FROM action_proposals_log
        WHERE chosen_action = 'ACTION1'
        GROUP BY chosen_reason ORDER BY cnt DESC LIMIT 10
    """)
    for r in c.fetchall():
        reason = r[0][:70] if r[0] else "N/A"
        print(f"  ({r[1]:5d}x) {reason}")

    # Agent stats
    print("\n=== AGENT STATISTICS ===")
    c.execute("SELECT COUNT(*), MAX(generation) FROM agents WHERE is_active=1")
    active, max_gen = c.fetchone()
    print(f"  Active agents: {active}")
    print(f"  Max generation: {max_gen}")

    c.execute("SELECT MAX(total_games_played), AVG(total_games_played) FROM agents")
    r = c.fetchone()
    print(f"  Max games by one agent: {r[0]}")
    avg_games = f"{r[1]:.1f}" if r[1] else "0"
    print(f"  Avg games per agent: {avg_games}")

    # Check training sessions
    print("\n=== TRAINING SESSIONS ===")
    c.execute("SELECT COUNT(*) FROM training_sessions")
    print(f"  Total sessions: {c.fetchone()[0]}")

    c.execute("""
        SELECT MAX(actions_taken), SUM(wins), SUM(total_score)
        FROM training_sessions
    """)
    r = c.fetchone()
    print(f"  Max actions in session: {r[0]}")
    print(f"  Total wins across all: {r[1]}")
    print(f"  Total score across all: {r[2]}")

    conn.close()

    print("\n" + "=" * 60)
    print("DIAGNOSIS")
    print("=" * 60)
    print("""
KEY FINDINGS:
1. 625 games played over 55 generations
2. Consistent 129 actions per game (some limit being hit)
3. ZERO positive scores, ZERO level completions
4. ZERO frame changes - THIS IS THE CRITICAL ISSUE
5. ACTION1 massively dominates (41k uses)

CRITICAL ISSUE: ZERO FRAME CHANGES
This means the game state is NOT changing when actions are sent.
Possible causes:
1. Actions not being sent to API correctly
2. Wrong action format for this game
3. Game requires specific sequence to start
4. SDK offline mode may not update frames properly

RECOMMENDATION:
Run with --verbose flag to see actual action->response cycle
Check if the game environment is properly initialized
Verify that env.step() is returning new observations
""")

if __name__ == "__main__":
    main()
