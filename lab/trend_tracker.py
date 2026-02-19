"""
Trend Tracker -- perfect memory across all lab experiments.

Maintains a lab_experiments table in core_data.db to record every experiment,
its hypothesis, metrics before/after, and outcome. Detects convergence,
plateaus, and cross-game patterns.

Codebase-agnostic by nature: tracks experiment outcomes, not code structure.

Usage:
    python -m lab.trend_tracker record --branch exp/foo --hypothesis "..." --before metrics.json --after metrics.json
    python -m lab.trend_tracker status                    # current state-of-lab
    python -m lab.trend_tracker ready                     # is there enough signal for new hypothesis?
    python -m lab.trend_tracker convergence               # convergence detection
"""

import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "core_data.db"

# Schema for the lab's internal experiment ledger
_SCHEMA = """
CREATE TABLE IF NOT EXISTS lab_experiments (
    experiment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    branch_name TEXT NOT NULL,
    hypothesis TEXT NOT NULL,
    target_game TEXT,
    seal_addressed TEXT,
    metrics_before TEXT,
    metrics_after TEXT,
    generation_start INTEGER,
    generation_end INTEGER,
    outcome TEXT CHECK(outcome IN ('confirmed', 'refuted', 'inconclusive', 'pending')),
    improvement_details TEXT,
    regression_details TEXT,
    created_at TEXT NOT NULL,
    completed_at TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS lab_metric_snapshots (
    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    generation INTEGER NOT NULL,
    game_type TEXT NOT NULL,
    metric_1_l1_rate REAL,
    metric_2_achieved INTEGER,
    metric_3_win_rate REAL,
    metric_4_median_actions REAL,
    metric_4_min_actions REAL,
    metric_5_median_total REAL,
    metric_5_min_total REAL,
    recorded_at TEXT NOT NULL
);
"""


def _get_connection(db_path=None):
    path = str(db_path or DB_PATH)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_schema(db_path=None):
    """Create lab tables if they don't exist."""
    conn = _get_connection(db_path)
    conn.executescript(_SCHEMA)
    conn.commit()
    conn.close()


def record_experiment(
    branch_name,
    hypothesis,
    metrics_before,
    metrics_after=None,
    target_game=None,
    seal_addressed=None,
    generation_start=None,
    generation_end=None,
    outcome="pending",
    notes=None,
    db_path=None,
):
    """Record a new experiment or update an existing one."""
    ensure_schema(db_path)
    conn = _get_connection(db_path)

    before_json = json.dumps(metrics_before) if isinstance(metrics_before, dict) else metrics_before
    after_json = (
        json.dumps(metrics_after) if isinstance(metrics_after, dict) else metrics_after
    )

    # Check for improvements and regressions
    improvements, regressions = _diff_metrics(metrics_before, metrics_after)

    conn.execute(
        """INSERT INTO lab_experiments
        (branch_name, hypothesis, target_game, seal_addressed,
         metrics_before, metrics_after, generation_start, generation_end,
         outcome, improvement_details, regression_details, created_at, completed_at, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            branch_name,
            hypothesis,
            target_game,
            seal_addressed,
            before_json,
            after_json,
            generation_start,
            generation_end,
            outcome,
            json.dumps(improvements) if improvements else None,
            json.dumps(regressions) if regressions else None,
            datetime.now().isoformat(),
            datetime.now().isoformat() if outcome != "pending" else None,
            notes,
        ),
    )
    conn.commit()
    experiment_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()

    return experiment_id


def _diff_metrics(before, after):
    """Compare before/after metrics, find improvements and regressions."""
    if not isinstance(before, dict) or not isinstance(after, dict):
        return None, None

    improvements = {}
    regressions = {}

    for game_type in set(list(before.get("games", {}).keys()) + list(after.get("games", {}).keys())):
        b_game = before.get("games", {}).get(game_type, {})
        a_game = after.get("games", {}).get(game_type, {})

        # Compare L1 completion rate (Metric 1)
        b_l1 = (b_game.get("metric_1_level_completion", {}).get("L1", {}).get("rate", 0))
        a_l1 = (a_game.get("metric_1_level_completion", {}).get("L1", {}).get("rate", 0))

        if a_l1 > b_l1:
            improvements[f"{game_type}_L1_rate"] = {"before": b_l1, "after": a_l1}
        elif a_l1 < b_l1:
            regressions[f"{game_type}_L1_rate"] = {"before": b_l1, "after": a_l1}

        # Compare win count (Metric 2/3)
        b_wins = b_game.get("metric_2_full_completion", {}).get("count", 0)
        a_wins = a_game.get("metric_2_full_completion", {}).get("count", 0)

        if a_wins > b_wins:
            improvements[f"{game_type}_wins"] = {"before": b_wins, "after": a_wins}
        elif a_wins < b_wins:
            regressions[f"{game_type}_wins"] = {"before": b_wins, "after": a_wins}

    return improvements or None, regressions or None


def record_metric_snapshot(generation, metrics_report, db_path=None):
    """Record a metric snapshot for convergence tracking."""
    ensure_schema(db_path)
    conn = _get_connection(db_path)

    for game_type, game_data in metrics_report.get("games", {}).items():
        l1 = game_data.get("metric_1_level_completion", {}).get("L1", {})
        m2 = game_data.get("metric_2_full_completion", {})
        m4 = game_data.get("metric_4_efficiency_per_level", {}).get("L1", {})
        m5 = game_data.get("metric_5_aggregate_efficiency", {})

        # Best completion frequency across this gen
        freq = game_data.get("metric_3_completion_frequency", {})
        win_rate = 0
        for gen_data in freq.values():
            if isinstance(gen_data, dict):
                win_rate = max(win_rate, gen_data.get("rate", 0))

        conn.execute(
            """INSERT INTO lab_metric_snapshots
            (generation, game_type, metric_1_l1_rate, metric_2_achieved,
             metric_3_win_rate, metric_4_median_actions, metric_4_min_actions,
             metric_5_median_total, metric_5_min_total, recorded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                generation,
                game_type,
                l1.get("rate"),
                1 if m2.get("achieved") else 0,
                win_rate,
                m4.get("median_actions"),
                m4.get("min_actions"),
                m5.get("median_actions"),
                m5.get("min_actions"),
                datetime.now().isoformat(),
            ),
        )

    conn.commit()
    conn.close()


def get_experiment_history(limit=20, db_path=None):
    """Get recent experiment history."""
    ensure_schema(db_path)
    conn = _get_connection(db_path)
    rows = conn.execute(
        "SELECT * FROM lab_experiments ORDER BY experiment_id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def check_readiness(db_path=None):
    """
    Is there enough signal to warrant a new hypothesis?
    Returns readiness status and reasoning.
    """
    ensure_schema(db_path)
    conn = _get_connection(db_path)

    # Detect actual column name (legacy: 'outcome', current: 'verdict')
    col_info = conn.execute("PRAGMA table_info(lab_experiments)").fetchall()
    col_names = [c[1] for c in col_info]
    verdict_col = "verdict" if "verdict" in col_names else "outcome"

    # Check pending experiments
    pending = conn.execute(
        f"SELECT COUNT(*) FROM lab_experiments WHERE {verdict_col} = 'pending'"
    ).fetchone()[0]

    # Check recent verdicts
    recent = conn.execute(
        f"SELECT {verdict_col}, COUNT(*) FROM lab_experiments "
        f"GROUP BY {verdict_col} ORDER BY {verdict_col}"
    ).fetchall()

    # Check consecutive failures
    last_5 = conn.execute(
        f"SELECT {verdict_col} FROM lab_experiments ORDER BY experiment_id DESC LIMIT 5"
    ).fetchall()

    conn.close()

    consecutive_failures = 0
    for row in last_5:
        if row[0] == "refuted":
            consecutive_failures += 1
        else:
            break

    ready = True
    reasons = []

    if pending > 0:
        ready = False
        reasons.append(f"{pending} experiments still pending -- complete them first")

    if consecutive_failures >= 5:
        reasons.append(
            "[WARN] 5+ consecutive refuted hypotheses -- Theorist should rethink approach"
        )

    if not recent:
        reasons.append("No experiment history -- first experiment, proceed")

    return {
        "ready": ready,
        "pending_experiments": pending,
        "consecutive_failures": consecutive_failures,
        "verdict_summary": {r[0]: r[1] for r in recent} if recent else {},
        "reasons": reasons,
    }


def detect_convergence(db_path=None):
    """
    Detect whether metrics are converging (stabilization check).
    Looks at metric snapshots over time.
    """
    ensure_schema(db_path)
    conn = _get_connection(db_path)

    snapshots = conn.execute(
        "SELECT * FROM lab_metric_snapshots ORDER BY generation"
    ).fetchall()
    conn.close()

    if len(snapshots) < 10:
        return {
            "converged": False,
            "reason": f"Only {len(snapshots)} snapshots -- need at least 10 for convergence detection",
        }

    # Group by game type
    by_game = {}
    for s in snapshots:
        s = dict(s)
        gt = s["game_type"]
        if gt not in by_game:
            by_game[gt] = []
        by_game[gt].append(s)

    convergence = {}
    for game_type, game_snapshots in by_game.items():
        if len(game_snapshots) < 5:
            convergence[game_type] = {"converged": False, "reason": "insufficient data"}
            continue

        # Check L1 rate trend (last 5 vs previous 5)
        recent = game_snapshots[-5:]
        earlier = game_snapshots[-10:-5]

        recent_l1 = [s["metric_1_l1_rate"] or 0 for s in recent]
        earlier_l1 = [s["metric_1_l1_rate"] or 0 for s in earlier]

        recent_avg = sum(recent_l1) / len(recent_l1)
        earlier_avg = sum(earlier_l1) / len(earlier_l1)

        improvement_rate = abs(recent_avg - earlier_avg)

        convergence[game_type] = {
            "converged": improvement_rate < 0.001,
            "improvement_rate": round(improvement_rate, 6),
            "recent_l1_avg": round(recent_avg, 4),
            "earlier_l1_avg": round(earlier_avg, 4),
            "metric_2_achieved": any(s["metric_2_achieved"] for s in game_snapshots),
        }

    all_converged = all(g.get("converged", False) for g in convergence.values())
    all_completed = all(
        g.get("metric_2_achieved", False) for g in convergence.values()
    )

    return {
        "converged": all_converged and all_completed,
        "all_games_completed": all_completed,
        "per_game": convergence,
    }


def get_successful_experiments(db_path=None):
    """Get confirmed experiments for the Branch Breeder."""
    ensure_schema(db_path)
    conn = _get_connection(db_path)
    col_info = conn.execute("PRAGMA table_info(lab_experiments)").fetchall()
    col_names = [c[1] for c in col_info]
    verdict_col = "verdict" if "verdict" in col_names else "outcome"
    rows = conn.execute(
        f"SELECT * FROM lab_experiments WHERE {verdict_col} = 'confirmed' "
        "ORDER BY experiment_id DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Trend Tracker")
    subparsers = parser.add_subparsers(dest="command", help="Sub-command")

    # record
    rec = subparsers.add_parser("record", help="Record an experiment")
    rec.add_argument("--branch", required=True)
    rec.add_argument("--hypothesis", required=True)
    rec.add_argument("--before", required=True, help="Path to before-metrics JSON")
    rec.add_argument("--after", default=None, help="Path to after-metrics JSON")
    rec.add_argument("--outcome", default="pending")
    rec.add_argument("--target-game", default=None)
    rec.add_argument("--seal", default=None)
    rec.add_argument("--notes", default=None)

    # status
    subparsers.add_parser("status", help="Show experiment history")

    # ready
    subparsers.add_parser("ready", help="Check readiness for new hypothesis")

    # convergence
    subparsers.add_parser("convergence", help="Detect metric convergence")

    # successful
    subparsers.add_parser("successful", help="List successful experiments")

    parser.add_argument("--db", type=str, default=None)
    args = parser.parse_args()

    if args.command == "record":
        before = json.loads(Path(args.before).read_text(encoding="utf-8"))
        after = None
        if args.after:
            after = json.loads(Path(args.after).read_text(encoding="utf-8"))
        exp_id = record_experiment(
            branch_name=args.branch,
            hypothesis=args.hypothesis,
            metrics_before=before,
            metrics_after=after,
            target_game=args.target_game,
            seal_addressed=args.seal,
            outcome=args.outcome,
            notes=args.notes,
            db_path=args.db,
        )
        result = {"recorded": True, "experiment_id": exp_id}

    elif args.command == "status":
        result = {"experiments": get_experiment_history(db_path=args.db)}

    elif args.command == "ready":
        result = check_readiness(db_path=args.db)

    elif args.command == "convergence":
        result = detect_convergence(db_path=args.db)

    elif args.command == "successful":
        result = {"successful_experiments": get_successful_experiments(db_path=args.db)}

    else:
        parser.print_help()
        return

    json.dump(result, sys.stdout, indent=2, default=str)
    print()


if __name__ == "__main__":
    main()
