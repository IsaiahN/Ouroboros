"""Performance audit script for action decision system analysis."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "core_data.db"

def run_audit():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    print("=" * 70)
    print("ACTION DECISION SYSTEM PERFORMANCE AUDIT")
    print("=" * 70)

    # 1. Overall game performance
    print("\n[1] OVERALL GAME PERFORMANCE (Last 7 Days)")
    print("-" * 50)
    cur = conn.execute("""
        SELECT
            game_type,
            COUNT(*) as total_games,
            ROUND(AVG(final_score), 1) as avg_score,
            MAX(final_score) as max_score,
            ROUND(AVG(actions_taken), 0) as avg_actions,
            MAX(levels_completed) as max_levels,
            SUM(CASE WHEN final_score > 0 THEN 1 ELSE 0 END) as positive_games
        FROM game_results
        WHERE created_at > datetime('now', '-7 days')
        GROUP BY game_type
        ORDER BY total_games DESC
        LIMIT 15
    """)
    rows = list(cur)
    if rows:
        for row in rows:
            pos_rate = (row['positive_games'] / row['total_games'] * 100) if row['total_games'] > 0 else 0
            print(f"  {row['game_type']}: {row['total_games']} games, avg={row['avg_score']}, max={row['max_score']}, pos={pos_rate:.0f}%, max_lvl={row['max_levels']}")
    else:
        print("  No game results in last 7 days")

    # 2. Winning sequences status
    print("\n[2] WINNING SEQUENCES STATUS")
    print("-" * 50)
    cur = conn.execute("SELECT COUNT(*) FROM winning_sequences WHERE is_active = 1")
    level_seq = cur.fetchone()[0]
    cur = conn.execute("SELECT COUNT(DISTINCT game_type) FROM winning_sequences WHERE is_active = 1")
    games_w_lvl = cur.fetchone()[0]
    cur = conn.execute("SELECT COUNT(*) FROM winning_sequences_full_game WHERE is_active = 1")
    full_wins = cur.fetchone()[0]
    cur = conn.execute("SELECT COUNT(DISTINCT game_type) FROM winning_sequences_full_game WHERE is_active = 1")
    games_beaten = cur.fetchone()[0]
    print(f"  Level sequences: {level_seq}")
    print(f"  Games with level wins: {games_w_lvl}")
    print(f"  Full game wins: {full_wins}")
    print(f"  Games fully beaten: {games_beaten}")

    # 3. Level progression analysis
    print("\n[3] LEVEL PROGRESSION (Where Do Agents Stop?)")
    print("-" * 50)
    cur = conn.execute("""
        SELECT
            levels_completed,
            COUNT(*) as count,
            ROUND(AVG(final_score), 1) as avg_score,
            ROUND(AVG(actions_taken), 0) as avg_actions
        FROM game_results
        WHERE created_at > datetime('now', '-7 days')
        GROUP BY levels_completed
        ORDER BY levels_completed
    """)
    rows = list(cur)
    if rows:
        for row in rows:
            print(f"  Level {row['levels_completed']}: {row['count']} games, avg_score={row['avg_score']}, avg_actions={row['avg_actions']}")
    else:
        print("  No level data")

    # 4. Action decision sources
    print("\n[4] ACTION DECISION SOURCES (What's Making Decisions?)")
    print("-" * 50)
    cur = conn.execute("""
        SELECT
            decision_source,
            COUNT(*) as count,
            ROUND(AVG(COALESCE(score_delta, 0)), 4) as avg_delta,
            SUM(CASE WHEN score_delta > 0 THEN 1 ELSE 0 END) as positive
        FROM action_traces
        WHERE created_at > datetime('now', '-3 days')
        AND decision_source IS NOT NULL AND decision_source != ''
        GROUP BY decision_source
        ORDER BY count DESC
        LIMIT 20
    """)
    rows = list(cur)
    if rows:
        for row in rows:
            pos_rate = (row['positive'] / row['count'] * 100) if row['count'] > 0 else 0
            print(f"  {row['decision_source']}: {row['count']} actions, delta={row['avg_delta']}, pos={pos_rate:.1f}%")
    else:
        print("  No decision source tracking")

    # 5. Hypothesis system health
    print("\n[5] HYPOTHESIS SYSTEM HEALTH")
    print("-" * 50)
    cur = conn.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN validation_attempts >= 3 THEN 1 ELSE 0 END) as validated,
            SUM(CASE WHEN validated_by_win = 1 THEN 1 ELSE 0 END) as win_val,
            ROUND(AVG(reliability_score), 3) as avg_rel,
            SUM(CASE WHEN times_used > 0 THEN 1 ELSE 0 END) as ever_used
        FROM network_object_control_hypotheses
        WHERE is_active = 1
    """)
    row = cur.fetchone()
    print(f"  Total hypotheses: {row['total']}")
    print(f"  Validated (3+ attempts): {row['validated']}")
    print(f"  Win-validated: {row['win_val']}")
    print(f"  Avg reliability: {row['avg_rel']}")
    print(f"  Ever used: {row['ever_used']}")

    # 6. Agent weights (wA vs wB)
    print("\n[6] TWO-STREAMS WEIGHTS (wA/wB)")
    print("-" * 50)
    try:
        cur = conn.execute("""
            SELECT
                ROUND(AVG(COALESCE(w_a, 0.5)), 3) as avg_w_a,
                ROUND(AVG(COALESCE(w_b, 0.5)), 3) as avg_w_b,
                COUNT(*) as agent_count
            FROM agents
            WHERE is_active = 1
        """)
        row = cur.fetchone()
        print(f"  Active agents: {row['agent_count']}")
        print(f"  Avg wA (private): {row['avg_w_a']}")
        print(f"  Avg wB (network): {row['avg_w_b']}")
    except Exception as e:
        print(f"  Error: {e}")

    # 7. Action distribution
    print("\n[7] ACTION DISTRIBUTION")
    print("-" * 50)
    cur = conn.execute("""
        SELECT
            action_taken,
            COUNT(*) as count,
            ROUND(AVG(COALESCE(score_delta, 0)), 4) as avg_delta
        FROM action_traces
        WHERE created_at > datetime('now', '-3 days')
        GROUP BY action_taken
        ORDER BY count DESC
    """)
    rows = list(cur)
    if rows:
        for row in rows:
            print(f"  {row['action_taken']}: {row['count']} times, avg_delta={row['avg_delta']}")
    else:
        print("  No action data")

    # 8. Death patterns
    print("\n[8] DEATH AVOIDANCE PATTERNS")
    print("-" * 50)
    cur = conn.execute("""
        SELECT
            COUNT(*) as total_patterns,
            ROUND(AVG(danger_score), 3) as avg_danger,
            SUM(death_count) as total_deaths
        FROM position_death_patterns
    """)
    row = cur.fetchone()
    print(f"  Death patterns recorded: {row['total_patterns']}")
    print(f"  Avg danger score: {row['avg_danger']}")
    print(f"  Total deaths tracked: {row['total_deaths']}")

    # 9. CODS primitive usage
    print("\n[9] CODS PRIMITIVE USAGE")
    print("-" * 50)
    try:
        cur = conn.execute("""
            SELECT primitive_id, usage_count, success_rate
            FROM cods_primitives
            WHERE usage_count > 0
            ORDER BY usage_count DESC
            LIMIT 10
        """)
        rows = list(cur)
        if rows:
            for row in rows:
                print(f"  {row['primitive_id']}: used={row['usage_count']}, success={row['success_rate']}%")
        else:
            print("  No primitive usage recorded")
    except Exception as e:
        print(f"  Table may not exist: {e}")

    # 10. Recent reasoning log sample
    print("\n[10] RECENT GAME SAMPLE")
    print("-" * 50)
    cur = conn.execute("""
        SELECT game_type, final_score, actions_taken, levels_completed, created_at
        FROM game_results
        ORDER BY created_at DESC
        LIMIT 5
    """)
    rows = list(cur)
    if rows:
        for row in rows:
            print(f"  {row['game_type']}: score={row['final_score']}, actions={row['actions_taken']}, levels={row['levels_completed']}")
    else:
        print("  No recent games")

    conn.close()
    print("\n" + "=" * 70)
    print("AUDIT COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    run_audit()
