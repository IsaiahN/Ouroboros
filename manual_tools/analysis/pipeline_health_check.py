"""
Pipeline Health Check — Automated Bug Pattern Detector

Detects the EXACT classes of silent data-pipeline bugs found in sessions 7n-7p:

  1. FITNESS DISCONNECTION: game_results written but agent_arc_performance empty
     → Evolution has zero selection signal (random drift for N generations)

  2. POPULATION BLOAT: active agents >> population_size
     → _update_population_database generation filter leaves zombies

  3. COORDINATE BLACKLISTING: dead_coordinates filtering valid targets
     → visual_analyzer blocks coordinates needed for wins

  4. FALLBACK MONOPOLY: cognitive router returning 100% fallbacks
     → Multiple causes: counter inflation, config mismatch, filter cascades

  5. COUNTER INFLATION: counters incrementing at wrong granularity
     → record_iteration per-rung instead of per-loop-iteration

  6. SESSION ORPHANS: duplicate training_sessions from _store_game_result
     → FK confusion, wasted DB space

Run manually:
    python manual_tools/analysis/pipeline_health_check.py [--fix] [--verbose]

Or import and call from evolution_runner:
    from manual_tools.analysis.pipeline_health_check import run_health_checks
    issues = run_health_checks(db, generation, population_size)

Returns list of issues, each with severity and auto-fix availability.
"""
import argparse
import os
import sqlite3
import sys
from typing import Any, Dict, List, Optional

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


# ---------------------------------------------------------------------------
# Issue dataclass
# ---------------------------------------------------------------------------
class HealthIssue:
    """A detected health issue."""
    __slots__ = ('check_name', 'severity', 'message', 'detail', 'auto_fixable', 'fix_description')

    def __init__(self, check_name: str, severity: str, message: str,
                 detail: str = '', auto_fixable: bool = False, fix_description: str = ''):
        self.check_name = check_name
        self.severity = severity          # CRITICAL, WARNING, INFO
        self.message = message
        self.detail = detail
        self.auto_fixable = auto_fixable
        self.fix_description = fix_description

    def __repr__(self):
        fix_tag = ' [AUTO-FIXABLE]' if self.auto_fixable else ''
        return f"[{self.severity}] {self.check_name}: {self.message}{fix_tag}"


# ---------------------------------------------------------------------------
# Individual health checks
# ---------------------------------------------------------------------------

def check_fitness_pipeline(conn: sqlite3.Connection) -> List[HealthIssue]:
    """
    CHECK 1: Fitness data pipeline — does game_results flow to agent_arc_performance?

    Bug pattern (Session 7p): _store_game_result wrote to game_results but never
    to agent_arc_performance. Evolutionary fitness calculated from agent_arc_performance
    returned 0.0 for all agents. 5000+ generations of zero selection signal.
    """
    issues = []

    # Count rows in each table
    gr_count = conn.execute("SELECT COUNT(*) FROM game_results").fetchone()[0]
    arc_count = conn.execute("SELECT COUNT(*) FROM agent_arc_performance").fetchone()[0]

    if gr_count == 0:
        issues.append(HealthIssue(
            'fitness_pipeline', 'INFO',
            'No game results yet — system has not played any games.',
        ))
        return issues

    if arc_count == 0 and gr_count > 0:
        issues.append(HealthIssue(
            'fitness_pipeline', 'CRITICAL',
            f'game_results has {gr_count} rows but agent_arc_performance has 0! '
            f'Evolutionary fitness will return 0.0 for ALL agents. '
            f'Natural selection has ZERO signal.',
            detail='Bug: _store_game_result does not write to agent_arc_performance.',
        ))
        return issues

    # Check ratio — arc_performance should have roughly 1 row per game_result
    # (some old results may predate the fix, so check recent generations)
    recent_gr = conn.execute("""
        SELECT COUNT(*) FROM game_results
        WHERE generation = (SELECT MAX(generation) FROM game_results)
    """).fetchone()[0]
    recent_arc = conn.execute("""
        SELECT COUNT(*) FROM agent_arc_performance
        WHERE game_timestamp >= datetime('now', '-1 hour')
    """).fetchone()[0]

    if recent_gr > 10 and recent_arc == 0:
        issues.append(HealthIssue(
            'fitness_pipeline', 'CRITICAL',
            f'Recent generation has {recent_gr} game results but 0 recent '
            f'agent_arc_performance rows. Fitness pipeline is disconnected.',
        ))

    # Check if any agent has non-zero fitness signal
    agents_with_score = conn.execute(
        "SELECT COUNT(*) FROM agents WHERE is_active = 1 AND avg_score_per_game > 0"
    ).fetchone()[0]
    active_agents = conn.execute(
        "SELECT COUNT(*) FROM agents WHERE is_active = 1"
    ).fetchone()[0]

    if active_agents > 0 and agents_with_score == 0 and gr_count > 100:
        # Check if this is historical damage or active disconnection
        # Historical: active agents have 0 arc_performance rows (pre-fix data)
        # Active: agents have arc_performance but sync isn't running
        agents_with_arc = conn.execute("""
            SELECT COUNT(DISTINCT a.agent_id) FROM agents a
            JOIN agent_arc_performance ap ON a.agent_id = ap.agent_id
            WHERE a.is_active = 1
        """).fetchone()[0]

        if agents_with_arc == 0:
            issues.append(HealthIssue(
                'fitness_pipeline', 'INFO',
                f'All {active_agents} active agents have 0 arc_performance rows. '
                f'Historical: {gr_count} game_results predate the Session 7p fix '
                f'(no agent_id link). Will self-heal on next evolution run.',
            ))
        else:
            issues.append(HealthIssue(
                'fitness_pipeline', 'WARNING',
                f'All {active_agents} active agents have avg_score_per_game = 0 '
                f'despite {gr_count} game results. '
                f'Check: sync_agent_performance_to_agents_table may not be running.',
            ))

    return issues


def check_population_health(conn: sqlite3.Connection,
                            expected_population: int = 100) -> List[HealthIssue]:
    """
    CHECK 2: Population size — active agents should match population_size.

    Bug pattern (Session 7p): _update_population_database used
    WHERE generation = ? which only deactivated same-generation agents.
    Agents from all other generations stayed active forever.
    100-agent population bloated to 2,280.
    """
    issues = []

    active = conn.execute("SELECT COUNT(*) FROM agents WHERE is_active = 1").fetchone()[0]

    if active == 0:
        issues.append(HealthIssue(
            'population_health', 'WARNING',
            'No active agents. Population may not be initialized yet.',
        ))
        return issues

    # Check for bloat
    bloat_ratio = active / max(expected_population, 1)
    if bloat_ratio > 2.0:
        # Check if bloat comes from old generations
        gen_dist = conn.execute("""
            SELECT generation, COUNT(*) as cnt
            FROM agents WHERE is_active = 1
            GROUP BY generation ORDER BY cnt DESC LIMIT 5
        """).fetchall()
        gen_detail = ', '.join(f'gen {r[0]}: {r[1]}' for r in gen_dist)

        issues.append(HealthIssue(
            'population_health', 'CRITICAL',
            f'Population bloat: {active} active agents vs expected {expected_population} '
            f'({bloat_ratio:.1f}x). Top generations: {gen_detail}',
            detail='Bug: _update_population_database may only deactivate same-generation agents.',
            auto_fixable=True,
            fix_description='Deactivate all agents not in the most recent generation.',
        ))
    elif bloat_ratio > 1.5:
        issues.append(HealthIssue(
            'population_health', 'WARNING',
            f'Population slightly bloated: {active} active vs {expected_population} expected.',
        ))

    # Check generation spread — healthy population should be in 1-2 generations
    unique_gens = conn.execute("""
        SELECT COUNT(DISTINCT generation) FROM agents WHERE is_active = 1
    """).fetchone()[0]
    if unique_gens > 5:
        issues.append(HealthIssue(
            'population_health', 'WARNING',
            f'Active agents span {unique_gens} generations. '
            f'Healthy culling should keep agents in 1-2 generations.',
        ))

    return issues


def check_cognitive_router_health(conn: sqlite3.Connection) -> List[HealthIssue]:
    """
    CHECK 3: Cognitive router fallback rate.

    Bug patterns (Sessions 7n, 7o):
    - Survey fallback monopoly: 100% fallback from config mismatches
    - Catastrophic fallback inflation: counter per-rung instead of per-iteration
    - _handle_fallback ignoring best_actionable_result
    """
    issues = []

    # Check action_traces for fallback patterns
    try:
        recent_actions = conn.execute("""
            SELECT COUNT(*) FROM action_traces
            WHERE created_at >= datetime('now', '-1 hour')
        """).fetchone()[0]

        if recent_actions == 0:
            return issues  # No recent data to analyze

        # Check system_logs for fallback messages
        # NOTE: system_logs uses 'timestamp' column, not 'created_at'
        fallback_count = conn.execute("""
            SELECT COUNT(*) FROM system_logs
            WHERE timestamp >= datetime('now', '-1 hour')
              AND (message LIKE '%Fallback%' OR message LIKE '%CATASTROPHIC%')
        """).fetchone()[0]

        if recent_actions > 0 and fallback_count > 0:
            fallback_rate = fallback_count / max(recent_actions, 1)
            if fallback_rate > 0.5:
                issues.append(HealthIssue(
                    'cognitive_router', 'CRITICAL',
                    f'High fallback rate: {fallback_rate:.0%} '
                    f'({fallback_count}/{recent_actions} recent actions). '
                    f'Cognitive router may be misconfigured.',
                ))
            elif fallback_rate > 0.2:
                issues.append(HealthIssue(
                    'cognitive_router', 'WARNING',
                    f'Elevated fallback rate: {fallback_rate:.0%}. '
                    f'Some routing paths may be broken.',
                ))
    except Exception:
        pass  # system_logs table may not have the right schema

    return issues


def check_session_integrity(conn: sqlite3.Connection) -> List[HealthIssue]:
    """
    CHECK 4: Training session integrity — orphan/duplicate sessions.

    Bug pattern (Session 7p): _store_game_result created a new training_session
    with a random UUID even though play_game already created one. Caused
    duplicate sessions and FK confusion.
    """
    issues = []

    # Count training sessions vs game results
    ts_count = conn.execute("SELECT COUNT(*) FROM training_sessions").fetchone()[0]
    gr_count = conn.execute("SELECT COUNT(*) FROM game_results").fetchone()[0]

    if ts_count > 0 and gr_count > 0:
        # Check for orphaned sessions (no matching game_result).
        # Use LEFT JOIN (faster than NOT EXISTS on large tables) with
        # the idx_game_results_session_id index created by _ensure_indices.
        orphaned = conn.execute("""
            SELECT COUNT(*) FROM training_sessions ts
            LEFT JOIN game_results gr ON gr.session_id = ts.session_id
            WHERE gr.session_id IS NULL
        """).fetchone()[0]

        if orphaned > ts_count * 0.3:
            issues.append(HealthIssue(
                'session_integrity', 'WARNING',
                f'{orphaned}/{ts_count} training sessions have no matching game_result. '
                f'Possible duplicate session creation.',
                detail='Historical damage from pre-7p session duplication bug. '
                       'Run: python safe_cleanup.py --execute to clean.',
                auto_fixable=True,
                fix_description='python safe_cleanup.py --execute (step 27)',
            ))

    return issues


def check_winning_sequence_utilization(conn: sqlite3.Connection) -> List[HealthIssue]:
    """
    CHECK 5: Are winning sequences being saved and reused?

    Bug pattern: Level subsequences not saved, so knowledge never transfers.
    """
    issues = []

    # Check winning sequences exist
    ws_count = conn.execute(
        "SELECT COUNT(*) FROM winning_sequences WHERE is_active = 1"
    ).fetchone()[0]
    ws_full = conn.execute(
        "SELECT COUNT(*) FROM winning_sequences_full_game WHERE is_active = 1"
    ).fetchone()[0]

    gr_count = conn.execute("SELECT COUNT(*) FROM game_results").fetchone()[0]

    if gr_count > 500 and ws_count == 0 and ws_full == 0:
        issues.append(HealthIssue(
            'sequence_utilization', 'WARNING',
            f'{gr_count} games played but 0 winning sequences saved. '
            f'No knowledge transfer possible.',
        ))

    # Check if sequences are being referenced
    if ws_count > 0:
        referenced = conn.execute("""
            SELECT COUNT(*) FROM winning_sequences
            WHERE is_active = 1 AND times_referenced > 0
        """).fetchone()[0]

        if referenced == 0 and ws_count > 5:
            issues.append(HealthIssue(
                'sequence_utilization', 'INFO',
                f'{ws_count} winning sequences saved but none have been referenced. '
                f'Replay pipeline may not be loading them.',
            ))

    return issues


def check_evolution_signal(conn: sqlite3.Connection) -> List[HealthIssue]:
    """
    CHECK 6: Is evolution actually producing improvement over generations?

    Detects random drift — if avg score hasn't improved in 50+ generations,
    something is broken in the selection pipeline.
    """
    issues = []

    # Get score trend across recent generations
    try:
        rows = conn.execute("""
            SELECT generation, AVG(final_score) as avg_score, COUNT(*) as games
            FROM game_results
            WHERE generation >= (SELECT MAX(generation) - 50 FROM game_results)
            GROUP BY generation
            HAVING games >= 5
            ORDER BY generation
        """).fetchall()

        if len(rows) >= 10:
            early_scores = [r[1] for r in rows[:5]]
            late_scores = [r[1] for r in rows[-5:]]

            early_avg = sum(early_scores) / len(early_scores)
            late_avg = sum(late_scores) / len(late_scores)

            if late_avg <= early_avg and early_avg == 0.0:
                issues.append(HealthIssue(
                    'evolution_signal', 'CRITICAL',
                    f'Score has been 0.0 for {len(rows)}+ generations. '
                    f'Evolution is producing zero improvement. '
                    f'Check fitness pipeline and selection mechanism.',
                ))
            elif len(rows) >= 30 and late_avg <= early_avg * 1.01:
                issues.append(HealthIssue(
                    'evolution_signal', 'WARNING',
                    f'No improvement over {len(rows)} generations '
                    f'(early avg: {early_avg:.4f}, late avg: {late_avg:.4f}). '
                    f'Evolution may lack selection signal.',
                ))
    except Exception:
        pass  # Not enough data

    return issues


def check_visual_analyzer_state() -> List[HealthIssue]:
    """
    CHECK 7: Visual analyzer dead_coordinates system.

    Bug pattern (Session 7p): dead_coordinates blacklisted coordinates after 5
    "failed" clicks based on unreliable frame hashing. Filtered out winning
    coordinates at 3 separate points. Never reset between games/levels.
    """
    issues = []

    # Check if the dead_coordinates attribute still exists in the code
    try:
        va_path = os.path.join(project_root, 'engines', 'perception', 'visual_analyzer.py')
        if os.path.exists(va_path):
            with open(va_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for dead_coordinates (excluding comments/docstrings)
            lines = content.split('\n')
            active_dead_refs = 0
            for line in lines:
                stripped = line.strip()
                if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
                    continue
                if 'dead_coordinates' in stripped and 'NOTE:' not in stripped and 'REMOVED' not in stripped:
                    active_dead_refs += 1

            if active_dead_refs > 0:
                issues.append(HealthIssue(
                    'visual_analyzer', 'CRITICAL',
                    f'dead_coordinates system still active ({active_dead_refs} code references). '
                    f'This blacklists valid coordinates and prevents wins.',
                    auto_fixable=False,
                    fix_description='Remove dead_coordinates tracking from visual_analyzer.py',
                ))
    except Exception:
        pass

    return issues


# ---------------------------------------------------------------------------
# Auto-fix functions
# ---------------------------------------------------------------------------

def fix_population_bloat(conn: sqlite3.Connection) -> str:
    """Fix: Deactivate all agents not in the most recent generation."""
    max_gen = conn.execute(
        "SELECT MAX(generation) FROM agents WHERE is_active = 1"
    ).fetchone()[0]

    if max_gen is None:
        return "No active agents to fix."

    result = conn.execute("""
        UPDATE agents SET is_active = 0
        WHERE is_active = 1 AND generation != ?
    """, (max_gen,))
    deactivated = result.rowcount
    conn.commit()

    return f"Deactivated {deactivated} zombie agents from non-current generations."


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def run_health_checks(
    db_path: str = 'core_data.db',
    expected_population: int = 100,
    generation: Optional[int] = None,
    verbose: bool = False,
) -> List[HealthIssue]:
    """
    Run all health checks and return list of issues.

    Can be called from evolution_runner or standalone.
    """
    import time as _time
    all_issues: List[HealthIssue] = []

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    # Match main app connection settings — WAL allows concurrent reads,
    # busy_timeout prevents indefinite blocking if evolution_runner holds a lock.
    try:
        conn.execute("PRAGMA journal_mode=WAL")
    except Exception:
        pass
    conn.execute("PRAGMA busy_timeout=5000")

    # Ensure critical indices exist (prevents multi-billion-row scans)
    _ensure_indices(conn, verbose=verbose)

    checks = [
        ("Fitness pipeline",       lambda: check_fitness_pipeline(conn)),
        ("Population health",      lambda: check_population_health(conn, expected_population)),
        ("Cognitive router",       lambda: check_cognitive_router_health(conn)),
        ("Session integrity",      lambda: check_session_integrity(conn)),
        ("Winning seq utilization", lambda: check_winning_sequence_utilization(conn)),
        ("Evolution signal",       lambda: check_evolution_signal(conn)),
        ("Visual analyzer",        lambda: check_visual_analyzer_state()),
    ]

    try:
        for name, fn in checks:
            if verbose:
                print(f"  Running: {name}...", end=" ", flush=True)
            t0 = _time.perf_counter()
            all_issues.extend(fn())
            elapsed = _time.perf_counter() - t0
            if verbose:
                print(f"({elapsed:.2f}s)")
    finally:
        conn.close()

    return all_issues


def _ensure_indices(conn: sqlite3.Connection, verbose: bool = False) -> None:
    """Create missing indices that prevent catastrophic query performance."""
    needed = [
        ("idx_game_results_session_id", "game_results", "session_id"),
        ("idx_game_results_generation", "game_results", "generation"),
    ]
    for idx_name, table, column in needed:
        try:
            conn.execute(
                f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table}({column})"
            )
            conn.commit()
        except Exception as e:
            if verbose:
                print(f"  [!] Could not create index {idx_name}: {e}")


def apply_auto_fixes(db_path: str = 'core_data.db') -> List[str]:
    """Apply all available auto-fixes. Returns list of fix descriptions."""
    fixes_applied = []
    conn = sqlite3.connect(db_path)

    try:
        # Check and fix population bloat
        pop_issues = check_population_health(conn)
        for issue in pop_issues:
            if issue.auto_fixable and issue.check_name == 'population_health':
                result = fix_population_bloat(conn)
                fixes_applied.append(result)
    finally:
        conn.close()

    return fixes_applied


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Pipeline Health Check - Detect silent data disconnections'
    )
    parser.add_argument('--db', default='core_data.db', help='Database path')
    parser.add_argument('--population', type=int, default=100, help='Expected population size')
    parser.add_argument('--fix', action='store_true', help='Apply auto-fixes')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    args = parser.parse_args()

    db_path = args.db
    if not os.path.exists(db_path):
        print(f"[ERROR] Database not found: {db_path}")
        sys.exit(1)

    print("=" * 60)
    print("PIPELINE HEALTH CHECK")
    print("=" * 60)
    print(f"Database: {db_path}")
    print(f"Expected population: {args.population}")
    print()

    issues = run_health_checks(
        db_path=db_path,
        expected_population=args.population,
        verbose=args.verbose,
    )

    # Print results grouped by severity
    critical = [i for i in issues if i.severity == 'CRITICAL']
    warnings = [i for i in issues if i.severity == 'WARNING']
    info = [i for i in issues if i.severity == 'INFO']

    if critical:
        print("[!!!] CRITICAL ISSUES:")
        for issue in critical:
            print(f"  {issue}")
            if issue.detail:
                print(f"      Detail: {issue.detail}")
            if issue.auto_fixable:
                print(f"      Fix: {issue.fix_description}")
        print()

    if warnings:
        print("[!] WARNINGS:")
        for issue in warnings:
            print(f"  {issue}")
            if args.verbose and issue.detail:
                print(f"      Detail: {issue.detail}")
        print()

    if info:
        print("[i] INFO:")
        for issue in info:
            print(f"  {issue}")
        print()

    if not issues:
        print("[OK] All pipeline health checks passed!")
    else:
        print(f"\nTotal: {len(critical)} critical, {len(warnings)} warnings, {len(info)} info")

    # Apply fixes if requested
    if args.fix:
        fixable = [i for i in issues if i.auto_fixable]
        if fixable:
            print(f"\n{'='*60}")
            print(f"APPLYING {len(fixable)} AUTO-FIXES")
            print(f"{'='*60}")
            fixes = apply_auto_fixes(db_path=db_path)
            for fix in fixes:
                print(f"  [FIXED] {fix}")
        else:
            print("\nNo auto-fixable issues found.")

    # Exit code: 1 if critical issues
    sys.exit(1 if critical else 0)


if __name__ == '__main__':
    main()
