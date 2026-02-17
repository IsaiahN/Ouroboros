"""
Benchmark Metrics -- computes all 5 metrics from game_results.

Stable contract: depends ONLY on the game_results table schema.
Codebase-agnostic: discovers game types and level counts from data.

Usage:
    python -m lab.metrics                          # latest generation
    python -m lab.metrics --generation 5100        # specific generation
    python -m lab.metrics --range 5100 5120        # generation range
    python -m lab.metrics --all                    # all generations summary
"""

import json
import sqlite3
import statistics
import sys
from collections import defaultdict
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "core_data.db"


def _get_connection(db_path=None):
    path = str(db_path or DB_PATH)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def _discover_columns(conn):
    """Discover game_results columns at runtime."""
    cursor = conn.execute("PRAGMA table_info(game_results)")
    return {row[1] for row in cursor}


def _extract_game_type(game_id):
    """Extract game type from game_id (e.g., 'ft09-abc123' -> 'ft09')."""
    return game_id.split("-")[0] if game_id else "unknown"


def _safe_median(values):
    """Median that handles empty lists."""
    if not values:
        return None
    return statistics.median(values)


def _safe_min(values):
    """Min that handles empty lists."""
    return min(values) if values else None


def compute_metrics(generation=None, gen_start=None, gen_end=None, db_path=None):
    """
    Compute all 5 benchmark metrics.

    Args:
        generation: specific generation to analyze (None = latest)
        gen_start/gen_end: generation range (inclusive)
        db_path: override database path

    Returns:
        dict with per-game metrics and summary
    """
    conn = _get_connection(db_path)
    columns = _discover_columns(conn)

    # Build query based on available columns and filters
    has_generation = "generation" in columns
    query = "SELECT * FROM game_results"
    params = []

    if generation is not None and has_generation:
        query += " WHERE generation = ?"
        params.append(generation)
    elif gen_start is not None and gen_end is not None and has_generation:
        query += " WHERE generation BETWEEN ? AND ?"
        params.extend([gen_start, gen_end])
    elif generation is None and gen_start is None and has_generation:
        # Default: latest generation
        latest = conn.execute(
            "SELECT MAX(generation) FROM game_results"
        ).fetchone()[0]
        if latest is None:
            conn.close()
            return {"error": "No data in game_results"}
        query += " WHERE generation = ?"
        params.append(latest)
        generation = latest

    rows = conn.execute(query, params).fetchall()
    conn.close()

    if not rows:
        return {"error": "No game_results found", "generation": generation}

    # Group by game type
    by_game = defaultdict(list)
    for row in rows:
        game_type = _extract_game_type(row["game_id"])
        by_game[game_type].append(dict(row))

    # Discover max observed levels per game type (across ALL data for context)
    conn2 = _get_connection(db_path)
    max_levels = {}
    for game_type in by_game:
        result = conn2.execute(
            "SELECT MAX(level_completions) FROM game_results WHERE game_id LIKE ?",
            (f"{game_type}%",),
        ).fetchone()
        max_levels[game_type] = result[0] if result[0] else 0
    conn2.close()

    # Compute per-game metrics
    report = {
        "generation": generation,
        "gen_range": [gen_start, gen_end] if gen_start is not None else None,
        "total_sessions": len(rows),
        "games": {},
    }

    for game_type, results in sorted(by_game.items()):
        report["games"][game_type] = _compute_game_metrics(
            game_type, results, max_levels.get(game_type, 0)
        )

    return report


def _compute_game_metrics(game_type, results, max_observed_levels):
    """Compute all 5 metrics for a single game type."""
    total = len(results)
    if total == 0:
        return {"error": "no sessions"}

    # --- Metric 1: Level Completion Rate ---
    # For each level N, what % of sessions completed at least N levels?
    level_rates = {}
    for level in range(1, max_observed_levels + 1):
        completed = sum(1 for r in results if r.get("level_completions", 0) >= level)
        level_rates[f"L{level}"] = {
            "completed": completed,
            "total": total,
            "rate": round(completed / total, 4),
        }

    # Also report distribution
    level_dist = defaultdict(int)
    for r in results:
        level_dist[r.get("level_completions", 0)] += 1

    # --- Metric 2: Full Game Completion ---
    # Has any session achieved win_detected = True?
    wins = [r for r in results if r.get("win_detected")]
    full_completion = {
        "achieved": len(wins) > 0,
        "count": len(wins),
    }

    # --- Metric 3: Completion Frequency ---
    # Per generation, how many sessions completed the full game?
    by_gen = defaultdict(lambda: {"total": 0, "wins": 0})
    for r in results:
        gen = r.get("generation", 0)
        by_gen[gen]["total"] += 1
        if r.get("win_detected"):
            by_gen[gen]["wins"] += 1

    completion_freq = {}
    for gen in sorted(by_gen):
        g = by_gen[gen]
        completion_freq[gen] = {
            "wins": g["wins"],
            "total": g["total"],
            "rate": round(g["wins"] / g["total"], 4) if g["total"] > 0 else 0,
        }

    # --- Metric 4: Action Efficiency per Level ---
    # For sessions completing at least N levels, what's their total_actions?
    efficiency_per_level = {}
    for level in range(1, max_observed_levels + 1):
        actions = [
            r["total_actions"]
            for r in results
            if r.get("level_completions", 0) >= level
            and r.get("total_actions") is not None
        ]
        efficiency_per_level[f"L{level}"] = {
            "sample_size": len(actions),
            "median_actions": _safe_median(actions),
            "min_actions": _safe_min(actions),
        }

    # --- Metric 5: Aggregate Efficiency ---
    # For full game completions, total actions
    win_actions = [
        r["total_actions"]
        for r in results
        if r.get("win_detected") and r.get("total_actions") is not None
    ]
    aggregate_efficiency = {
        "sample_size": len(win_actions),
        "median_actions": _safe_median(win_actions),
        "min_actions": _safe_min(win_actions),
    }

    return {
        "sessions": total,
        "max_observed_levels": max_observed_levels,
        "metric_1_level_completion": level_rates,
        "metric_1_distribution": dict(level_dist),
        "metric_2_full_completion": full_completion,
        "metric_3_completion_frequency": completion_freq,
        "metric_4_efficiency_per_level": efficiency_per_level,
        "metric_5_aggregate_efficiency": aggregate_efficiency,
    }


def compute_trend(gen_start, gen_end, db_path=None):
    """Compute metrics for each generation in a range, for trend analysis."""
    conn = _get_connection(db_path)
    gens = conn.execute(
        "SELECT DISTINCT generation FROM game_results "
        "WHERE generation BETWEEN ? AND ? ORDER BY generation",
        (gen_start, gen_end),
    ).fetchall()
    conn.close()

    trend = {}
    for (gen,) in gens:
        trend[gen] = compute_metrics(generation=gen, db_path=db_path)

    return trend


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Compute benchmark metrics")
    parser.add_argument("--generation", "-g", type=int, default=None)
    parser.add_argument("--range", "-r", nargs=2, type=int, metavar=("START", "END"))
    parser.add_argument("--all", action="store_true", help="Summary across all data")
    parser.add_argument("--db", type=str, default=None, help="Database path override")
    parser.add_argument(
        "--trend", action="store_true", help="Per-generation breakdown (with --range)"
    )
    args = parser.parse_args()

    if args.all:
        result = compute_metrics(
            generation=None, gen_start=0, gen_end=999999, db_path=args.db
        )
    elif args.range:
        if args.trend:
            result = compute_trend(args.range[0], args.range[1], db_path=args.db)
        else:
            result = compute_metrics(
                gen_start=args.range[0], gen_end=args.range[1], db_path=args.db
            )
    else:
        result = compute_metrics(generation=args.generation, db_path=args.db)

    json.dump(result, sys.stdout, indent=2, default=str)
    print()


if __name__ == "__main__":
    main()
