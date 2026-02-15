"""Observer Dashboard -- single source of truth for system health.

Reads core_data.db and prints a comprehensive report covering:
  1. Generation overview (scores, levels, games)
  2. PTMA loop health (routing traces, action traces, world model)
  3. Knowledge accumulation (winning sequences, lessons, death zones)
  4. Cognitive routing (rung usage, strategy distribution)
  5. Evolutionary health (agents, diversity, modes)
  6. Gap & intervention status
  7. Metacognitive health (predictions, assumptions, theories)
  8. Frame change & action diversity analysis

Usage:
    python manual_tools/observer_dashboard.py [--gens N] [--hours N]
"""
import argparse
import os
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "core_data.db")

# -- helpers -----------------------------------------------------------------


def _conn(db: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    return conn


def _rows(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
    try:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]
    except sqlite3.OperationalError:
        return []


def _one(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> Any:
    try:
        row = conn.execute(sql, params).fetchone()
        return row[0] if row else None
    except sqlite3.OperationalError:
        return None


def _trunc(text: Any, limit: int = 100) -> str:
    v = "" if text is None else str(text)
    return v if len(v) <= limit else v[: limit - 3] + "..."


def _bar(value: float, width: int = 30) -> str:
    filled = int(value * width)
    return "[" + "#" * filled + "-" * (width - filled) + "]"


def _header(title: str) -> None:
    print()
    print("=" * 68)
    print(f"  {title}")
    print("=" * 68)


def _section(title: str) -> None:
    print(f"\n--- {title} ---")


# -- 1. Generation Overview --------------------------------------------------


def section_generation_overview(conn: sqlite3.Connection, num_gens: int) -> None:
    _header("GENERATION OVERVIEW")

    gen = _one(conn, "SELECT MAX(generation) FROM game_results")
    if gen is None:
        print("  No game results found.")
        return

    rows = _rows(
        conn,
        """
        SELECT SUBSTR(game_id, 1, 4) as gtype, COUNT(*) as games,
               COALESCE(SUM(level_completions), 0) as total_levels,
               COALESCE(MAX(level_completions), 0) as best_levels,
               ROUND(AVG(final_score), 4) as avg_score,
               ROUND(MAX(final_score), 4) as best_score,
               ROUND(AVG(total_actions), 1) as avg_actions
        FROM game_results WHERE generation = ?
        GROUP BY gtype
    """,
        (gen,),
    )

    print(f"  Generation: {gen}")
    print(f"  {'Game':<6} {'Games':>6} {'Levels':>7} {'Best':>5} {'AvgScr':>8} {'BestScr':>8} {'AvgActs':>8}")
    print(f"  {'-' * 50}")
    for r in rows:
        print(
            f"  {r['gtype']:<6} {r['games']:>6} {r['total_levels']:>7} "
            f"{r['best_levels']:>5} {r['avg_score']:>8} {r['best_score']:>8} {r['avg_actions']:>8}"
        )

    total = _rows(
        conn,
        """
        SELECT COUNT(*) as games, COALESCE(SUM(level_completions),0) as levels,
               ROUND(AVG(final_score),4) as avg
        FROM game_results WHERE generation = ?
    """,
        (gen,),
    )
    if total:
        t = total[0]
        print(f"  {'TOTAL':<6} {t['games']:>6} {t['levels']:>7}")

    _section(f"Trend (last {num_gens} generations)")
    trend = _rows(
        conn,
        """
        SELECT generation, COUNT(*) as games,
               COALESCE(SUM(level_completions),0) as levels,
               ROUND(AVG(final_score),4) as avg_score,
               ROUND(MAX(final_score),4) as best
        FROM game_results
        WHERE generation > ? - ?
        GROUP BY generation ORDER BY generation DESC
    """,
        (gen, num_gens),
    )
    for t in trend:
        lvl_flag = f" ** {t['levels']} LEVELS **" if t['levels'] > 0 else ""
        print(f"  Gen {t['generation']:>5}: {t['games']:>4} games  avg={t['avg_score']}  best={t['best']}{lvl_flag}")

    winners = _rows(
        conn,
        """
        SELECT game_id, level_completions, final_score, total_actions
        FROM game_results WHERE generation = ? AND level_completions > 0
        ORDER BY level_completions DESC, total_actions ASC LIMIT 10
    """,
        (gen,),
    )
    if winners:
        _section(f"Level completions this gen ({len(winners)} games)")
        for w in winners:
            print(
                f"  {w['game_id']}  levels={w['level_completions']}  "
                f"score={w['final_score']:.4f}  actions={w['total_actions']}"
            )


# -- 2. PTMA Loop Health -----------------------------------------------------


def section_ptma_health(conn: sqlite3.Connection, hours: int) -> None:
    _header("PTMA LOOP HEALTH")

    cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()

    recent_rt = _one(conn, "SELECT COUNT(*) FROM cognitive_routing_traces WHERE timestamp >= ?", (cutoff,)) or 0
    total_rt = _one(conn, "SELECT COUNT(*) FROM cognitive_routing_traces") or 0
    print(f"  Routing traces  (last {hours}h): {recent_rt:>10,}  |  Total: {total_rt:>12,}")

    recent_at = _one(conn, "SELECT COUNT(*) FROM action_traces WHERE timestamp >= ?", (cutoff,)) or 0
    total_at = _one(conn, "SELECT COUNT(*) FROM action_traces") or 0
    print(f"  Action traces   (last {hours}h): {recent_at:>10,}  |  Total: {total_at:>12,}")

    total_wm = _one(conn, "SELECT COUNT(*) FROM world_model_states") or 0
    print(f"  World model states:             {total_wm:>12,}")

    recent_sl = _one(conn, "SELECT COUNT(*) FROM sensation_learning_events WHERE timestamp >= ?", (cutoff,)) or 0
    total_sl = _one(conn, "SELECT COUNT(*) FROM sensation_learning_events") or 0
    print(f"  Sensation events (last {hours}h): {recent_sl:>10,}  |  Total: {total_sl:>12,}")

    total_it = _one(conn, "SELECT COUNT(*) FROM i_thread_history") or 0
    print(f"  I-thread history:               {total_it:>12,}")

    gen = _one(conn, "SELECT MAX(generation) FROM game_results")
    if gen:
        _section("Frame change rates (latest gen)")
        fc = _rows(
            conn,
            """
            SELECT SUBSTR(game_id,1,4) as gtype,
                   ROUND(AVG(CAST(frame_changes AS REAL) / MAX(total_actions,1)) * 100, 1) as pct,
                   ROUND(AVG(frame_changes),0) as avg_fc,
                   ROUND(AVG(total_actions),0) as avg_acts
            FROM game_results WHERE generation = ? AND total_actions > 0
            GROUP BY gtype
        """,
            (gen,),
        )
        for r in fc:
            bar = _bar(float(r["pct"]) / 100.0, 20)
            print(f"  {r['gtype']}: {r['pct']:>5}% {bar}  ({r['avg_fc']:.0f} changes / {r['avg_acts']:.0f} actions)")


# -- 3. Knowledge Accumulation -----------------------------------------------


def section_knowledge(conn: sqlite3.Connection) -> None:
    _header("KNOWLEDGE ACCUMULATION")

    tables = [
        ("winning_sequences", "Winning sequences"),
        ("game_lessons_learned", "Game lessons"),
        ("death_zones", "Death zones"),
        ("action_effectiveness", "Action effectiveness"),
        ("collective_insights", "Collective insights"),
        ("universal_patterns", "Universal patterns"),
        ("viral_information_packages", "Viral packages"),
        ("working_theory_history", "Working theories"),
    ]
    for table, label in tables:
        cnt = _one(conn, f"SELECT COUNT(*) FROM [{table}]") or 0
        print(f"  {label:<25} {cnt:>8,}")

    _section("Winning sequences by game")
    ws = _rows(
        conn,
        """
        SELECT game_type, level_number, COUNT(*) as cnt,
               ROUND(AVG(efficiency_score), 3) as avg_eff
        FROM winning_sequences
        GROUP BY game_type, level_number
        ORDER BY game_type, level_number
    """,
    )
    for r in ws:
        print(f"  {r['game_type']} L{r['level_number']}: {r['cnt']} sequences  avg_efficiency={r['avg_eff']}")

    _section("Recent game lessons")
    lessons = _rows(
        conn,
        """
        SELECT game_type, lesson_text, level_number, created_at
        FROM game_lessons_learned ORDER BY created_at DESC LIMIT 5
    """,
    )
    for r in lessons:
        print(f"  [{r['game_type']} L{r['level_number']}] {_trunc(r['lesson_text'], 80)}  ({r['created_at']})")

    if not lessons:
        print("  (none)")


# -- 4. Cognitive Routing ----------------------------------------------------


def section_routing(conn: sqlite3.Connection, hours: int) -> None:
    _header("COGNITIVE ROUTING")

    cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()

    _section(f"Top actions routed (last {hours}h)")
    rungs = _rows(
        conn,
        """
        SELECT final_action, algorithm_used, COUNT(*) as cnt,
               ROUND(AVG(final_confidence), 3) as avg_conf,
               ROUND(AVG(iterations), 1) as avg_iter
        FROM cognitive_routing_traces
        WHERE timestamp >= ?
        GROUP BY final_action, algorithm_used
        ORDER BY cnt DESC LIMIT 15
    """,
        (cutoff,),
    )
    if rungs:
        max_cnt = rungs[0]["cnt"] if rungs else 1
        for r in rungs:
            bar = _bar(r["cnt"] / max_cnt, 20)
            print(f"  {str(r['final_action']):<20} via {str(r['algorithm_used']):<15} "
                  f"{r['cnt']:>6} {bar}  conf={r['avg_conf']}  iter={r['avg_iter']}")
    else:
        print("  (no recent routing traces)")

    _section("Action proposals by mode (top 10)")
    ops = _rows(
        conn,
        """
        SELECT mode, chosen_action, COUNT(*) as cnt,
               ROUND(AVG(w_A), 3) as avg_wA,
               ROUND(AVG(w_B), 3) as avg_wB
        FROM action_proposals_log
        WHERE created_at >= ?
        GROUP BY mode, chosen_action
        ORDER BY cnt DESC LIMIT 10
    """,
        (cutoff,),
    )
    for r in ops:
        print(f"  {str(r['mode']):<15} action={str(r['chosen_action']):<10} "
              f"{r['cnt']:>6}  wA={r['avg_wA']}  wB={r['avg_wB']}")

    if not ops:
        print("  (no recent action proposals)")


# -- 5. Evolutionary Health --------------------------------------------------


def section_evolutionary(conn: sqlite3.Connection) -> None:
    _header("EVOLUTIONARY HEALTH")

    total_agents = _one(conn, "SELECT COUNT(*) FROM agents") or 0
    active = _one(conn, "SELECT COUNT(*) FROM agents WHERE is_active = 1") or 0
    print(f"  Total agents: {total_agents:,}  |  Active: {active}")

    _section("Agent operating modes (latest generation)")
    latest_gen = _one(conn, "SELECT MAX(generation) FROM agent_operating_modes")
    modes = _rows(
        conn,
        """
        SELECT operating_mode, COUNT(*) as cnt
        FROM agent_operating_modes
        WHERE generation = ?
        GROUP BY operating_mode
        ORDER BY cnt DESC
    """,
        (latest_gen,),
    )
    for r in modes:
        print(f"  {r['operating_mode']:<20} {r['cnt']:>6}")

    if not modes:
        print("  (no active modes)")

    _section("Agent game diversity (top 5 by attempts)")
    diversity = _rows(
        conn,
        """
        SELECT agent_id, game_id, attempts, best_score,
               ROUND(few_shot_improvement, 3) as fsi
        FROM agent_game_diversity
        ORDER BY attempts DESC LIMIT 5
    """,
    )
    for r in diversity:
        print(
            f"  {r['agent_id'][:16]}...  game={r['game_id']}  "
            f"attempts={r['attempts']}  best={r['best_score']:.4f}  fsi={r['fsi']}"
        )

    if not diversity:
        print("  (none)")

    _section("Ecosystem health (latest)")
    eco = _rows(
        conn,
        """
        SELECT generation, health_status, health_score,
               total_sequences, active_agents, knowledge_diversity_index,
               total_levels_completed_this_gen, alignment_velocity_avg
        FROM ecosystem_health_snapshots
        ORDER BY generation DESC
        LIMIT 3
    """,
    )
    for r in eco:
        print(
            f"  Gen {r['generation']:>5}  health={r['health_status']:<20}  score={r['health_score']}  "
            f"agents={r['active_agents']}  seqs={r['total_sequences']}  "
            f"levels={r['total_levels_completed_this_gen']}  velocity={r['alignment_velocity_avg']}"
        )

    if not eco:
        print("  (none)")


# -- 6. Gap & Intervention Status --------------------------------------------


def section_gaps(conn: sqlite3.Connection) -> None:
    _header("GAPS & INTERVENTIONS")

    gaps = _rows(
        conn,
        """
        SELECT gap_type, severity, status, COUNT(*) as cnt
        FROM gap_registry
        GROUP BY gap_type, severity, status
        ORDER BY cnt DESC
    """,
    )
    if gaps:
        print("  Gap Registry:")
        for r in gaps:
            print(f"    {r['gap_type']:<30} {r['severity']:<10} {r['status']:<8} x{r['cnt']}")
    else:
        print("  No gaps registered.")

    interventions = _rows(
        conn,
        """
        SELECT intervention_type, outcome_status, COUNT(*) as cnt
        FROM interventions
        GROUP BY intervention_type, outcome_status
        ORDER BY cnt DESC
    """,
    )
    if interventions:
        print("  Interventions:")
        for r in interventions:
            print(f"    {r['intervention_type']:<25} {r['outcome_status']:<12} x{r['cnt']}")

    _section("Network regulation (recent)")
    reg = _rows(
        conn,
        """
        SELECT signal_type, game_type, severity, action_taken, created_at
        FROM network_regulation_history
        ORDER BY created_at DESC LIMIT 5
    """,
    )
    for r in reg:
        print(
            f"  [{r['severity']}] {r['signal_type']} on {r['game_type']}: "
            f"{_trunc(r['action_taken'], 60)}  ({r['created_at']})"
        )

    if not reg:
        print("  (none)")


# -- 7. Metacognitive Health -------------------------------------------------


def section_metacognition(conn: sqlite3.Connection) -> None:
    _header("METACOGNITIVE HEALTH")

    pred = _rows(
        conn,
        """
        SELECT prediction_correct, COUNT(*) as cnt
        FROM metacognitive_predictions
        GROUP BY prediction_correct
    """,
    )
    if pred:
        total_pred = sum(r["cnt"] for r in pred)
        print("  Prediction outcomes:")
        for r in pred:
            label = {1: "correct", 0: "incorrect"}.get(r["prediction_correct"], "unknown")
            pct = r["cnt"] / total_pred * 100
            print(f"    {label:<12} {r['cnt']:>8,}  ({pct:.1f}%)")

    assumptions = _rows(
        conn,
        """
        SELECT assumption_type, is_valid, COUNT(*) as cnt
        FROM metacognitive_assumptions
        GROUP BY assumption_type, is_valid
        ORDER BY cnt DESC
    """,
    )
    if assumptions:
        _section("Metacognitive assumptions")
        for r in assumptions:
            valid = {1: "valid", 0: "invalid"}.get(r["is_valid"], "untested")
            print(f"  {r['assumption_type']:<15} {valid:<10} x{r['cnt']}")

    _section("Working theory history")
    theories = _rows(
        conn,
        """
        SELECT game_type, level_number, COUNT(*) as revisions,
               ROUND(AVG(confidence), 3) as avg_conf
        FROM working_theory_history
        GROUP BY game_type, level_number
        ORDER BY revisions DESC LIMIT 10
    """,
    )
    for r in theories:
        print(f"  {r['game_type']} L{r['level_number']}: {r['revisions']} revisions  avg_conf={r['avg_conf']}")

    if not theories:
        print("  (none)")


# -- 8. Action Diversity -----------------------------------------------------


def section_action_diversity(conn: sqlite3.Connection) -> None:
    _header("ACTION DIVERSITY")

    gen = _one(conn, "SELECT MAX(generation) FROM game_results")
    if gen is None:
        print("  No data.")
        return

    _section("Coordinate click analysis (latest gen)")
    coord_data = _rows(
        conn,
        """
        SELECT SUBSTR(game_id, 1, 4) as gtype,
               SUM(coordinate_attempts) as total_clicks,
               SUM(coordinate_successes) as successful_clicks,
               ROUND(AVG(CASE WHEN coordinate_attempts > 0
                   THEN CAST(coordinate_successes AS REAL) / coordinate_attempts
                   ELSE 0 END) * 100, 1) as success_pct,
               COUNT(*) as games
        FROM game_results
        WHERE generation = ? AND coordinate_attempts > 0
        GROUP BY gtype
    """,
        (gen,),
    )
    for r in coord_data:
        print(
            f"  {r['gtype']}: {r['total_clicks']} clicks, {r['successful_clicks']} hits "
            f"({r['success_pct']}% success rate across {r['games']} games)"
        )

    if not coord_data:
        print("  (no coordinate data)")

    _section("Fallback activation estimate (latest gen)")
    fb = _rows(
        conn,
        """
        SELECT SUBSTR(game_id,1,4) as gtype,
               COUNT(*) as total,
               SUM(CASE WHEN total_actions > 150 AND level_completions = 0 THEN 1 ELSE 0 END) as likely_fb
        FROM game_results WHERE generation = ?
        GROUP BY gtype
    """,
        (gen,),
    )
    for r in fb:
        pct = r["likely_fb"] / max(r["total"], 1) * 100
        print(f"  {r['gtype']}: {r['likely_fb']}/{r['total']} games likely used fallback ({pct:.0f}%)")


# -- 9. Primitive & Operator Status ------------------------------------------


def section_primitives(conn: sqlite3.Connection) -> None:
    _header("PRIMITIVES & OPERATORS")

    _section("Primitive unlock status")
    prims = _rows(
        conn,
        """
        SELECT status, COUNT(*) as cnt
        FROM primitive_status
        GROUP BY status
        ORDER BY cnt DESC
    """,
    )
    for r in prims:
        print(f"  {r['status']:<15} {r['cnt']:>4}")

    if not prims:
        print("  (none)")

    _section("Composed operators (top 10 by usage)")
    ops = _rows(
        conn,
        """
        SELECT operator_name, times_used, times_effective,
               ROUND(CAST(times_effective AS REAL) / MAX(times_used, 1) * 100, 1) as eff_pct
        FROM composed_operators
        ORDER BY times_used DESC LIMIT 10
    """,
    )
    for r in ops:
        print(
            f"  {r['operator_name']:<30} used={r['times_used']:>4}  "
            f"effective={r['times_effective']:>4}  ({r['eff_pct']}%)"
        )

    if not ops:
        print("  (none)")


# -- 10. Quick DB Summary ---------------------------------------------------


def section_db_summary(conn: sqlite3.Connection) -> None:
    _header("DATABASE SUMMARY")

    key_tables = [
        "game_results",
        "action_traces",
        "cognitive_routing_traces",
        "winning_sequences",
        "agents",
        "world_model_states",
        "sensation_learning_events",
        "working_theory_history",
        "death_zones",
        "action_proposals_log",
        "player_state_history",
        "system_logs",
        "metacognitive_predictions",
    ]
    print(f"  {'Table':<35} {'Rows':>12}")
    print(f"  {'-' * 50}")
    for table in key_tables:
        cnt = _one(conn, f"SELECT COUNT(*) FROM [{table}]") or 0
        print(f"  {table:<35} {cnt:>12,}")

    try:
        size_bytes = os.path.getsize(DB_PATH)
        size_gb = size_bytes / (1024**3)
        print(f"\n  Database file size: {size_gb:.2f} GB")
    except OSError:
        pass


# -- main --------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="BitterTruth-AI Observer Dashboard")
    parser.add_argument("--gens", type=int, default=10, help="Number of recent generations to show in trend")
    parser.add_argument("--hours", type=int, default=24, help="Lookback hours for recency queries")
    args = parser.parse_args()

    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Database not found: {DB_PATH}")
        sys.exit(1)

    conn = _conn()
    try:
        print()
        print("  BITTERTRUTH-AI  --  OBSERVER DASHBOARD")
        print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Lookback: {args.hours}h  |  Trend gens: {args.gens}")

        section_generation_overview(conn, args.gens)
        section_ptma_health(conn, args.hours)
        section_knowledge(conn)
        section_routing(conn, args.hours)
        section_evolutionary(conn)
        section_gaps(conn)
        section_metacognition(conn)
        section_action_diversity(conn)
        section_primitives(conn)
        section_db_summary(conn)

        print("\n" + "=" * 68)
        print("  END OF REPORT")
        print("=" * 68)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
