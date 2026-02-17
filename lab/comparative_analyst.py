"""
Comparative Analyst -- discovers what differentiates success from failure.

Takes Code Tracer output + metrics, splits into cohorts, ranks features by effect size.
Codebase-agnostic: measures every discovered feature, ranks by statistical effect.

Usage:
    python -m lab.comparative_analyst                      # latest generation
    python -m lab.comparative_analyst --generation 5100    # specific generation
"""

import json
import math
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


def _cohens_d(group_a, group_b):
    """
    Compute Cohen's d effect size between two groups.
    Positive d means group_a > group_b.
    """
    if len(group_a) < 2 or len(group_b) < 2:
        return None

    mean_a = statistics.mean(group_a)
    mean_b = statistics.mean(group_b)
    var_a = statistics.variance(group_a)
    var_b = statistics.variance(group_b)
    n_a = len(group_a)
    n_b = len(group_b)

    # Pooled standard deviation
    pooled_var = ((n_a - 1) * var_a + (n_b - 1) * var_b) / (n_a + n_b - 2)
    pooled_sd = math.sqrt(pooled_var) if pooled_var > 0 else 0

    if pooled_sd == 0:
        return 0.0

    return round((mean_a - mean_b) / pooled_sd, 4)


def _extract_numeric_features(session_data):
    """Extract all numeric features from a session dict."""
    features = {}
    for key, value in session_data.items():
        if isinstance(value, (int, float)) and value is not None:
            features[key] = value
    return features


def run_analysis(generation=None, db_path=None):
    """
    Run full comparative analysis.

    1. Load game_results for the generation
    2. Split into success/failure cohorts per game type
    3. Discover all numeric features
    4. Compute effect size for each feature
    5. Rank by absolute effect size
    """
    conn = _get_connection(db_path)

    # Get generation
    if generation is None:
        generation = conn.execute(
            "SELECT MAX(generation) FROM game_results"
        ).fetchone()[0]
        if generation is None:
            conn.close()
            return {"error": "No data in game_results"}

    # Load all sessions for this generation
    rows = conn.execute(
        "SELECT * FROM game_results WHERE generation = ?", (generation,)
    ).fetchall()
    conn.close()

    if not rows:
        return {"error": f"No data for generation {generation}"}

    # Group by game type
    by_game = defaultdict(list)
    for row in rows:
        r = dict(row)
        game_type = r["game_id"].split("-")[0] if r.get("game_id") else "unknown"

        # Compute derived features
        total_actions = r.get("total_actions", 0) or 0
        coord_attempts = r.get("coordinate_attempts", 0) or 0
        coord_successes = r.get("coordinate_successes", 0) or 0
        frame_changes = r.get("frame_changes", 0) or 0
        level_completions = r.get("level_completions", 0) or 0

        session = {
            "session_id": r["session_id"],
            "game_type": game_type,
            "level_completions": level_completions,
            "win_detected": 1 if r.get("win_detected") else 0,
            "final_score": r.get("final_score", 0) or 0,
            "total_actions": total_actions,
            "frame_changes": frame_changes,
            "coordinate_attempts": coord_attempts,
            "coordinate_successes": coord_successes,
            # Derived features
            "coord_success_rate": (
                round(coord_successes / coord_attempts, 4)
                if coord_attempts > 0
                else 0
            ),
            "frame_change_rate": (
                round(frame_changes / total_actions, 4) if total_actions > 0 else 0
            ),
            "action_effectiveness": (
                round(coord_successes / total_actions, 4) if total_actions > 0 else 0
            ),
        }
        by_game[game_type].append(session)

    # Run per-game analysis
    report = {
        "generation": generation,
        "total_sessions": len(rows),
        "games": {},
    }

    for game_type, sessions in sorted(by_game.items()):
        report["games"][game_type] = _analyze_game(game_type, sessions)

    # Cross-game summary
    report["cross_game_summary"] = _cross_game_summary(report["games"])

    return report


def _analyze_game(game_type, sessions):
    """Analyze a single game type: cohort split + feature ranking."""
    total = len(sessions)

    # Define success: any level completion (adaptive threshold)
    success = [s for s in sessions if s["level_completions"] > 0]
    failure = [s for s in sessions if s["level_completions"] == 0]

    # If no successes, try softer criteria: above-median score
    if not success and sessions:
        scores = [s["final_score"] for s in sessions]
        median_score = statistics.median(scores) if scores else 0
        if median_score > 0:
            success = [s for s in sessions if s["final_score"] > median_score]
            failure = [s for s in sessions if s["final_score"] <= median_score]

    if not success or not failure:
        return {
            "sessions": total,
            "success_count": len(success),
            "failure_count": len(failure),
            "feature_rankings": [],
            "note": "Cannot compare -- need both success and failure cohorts",
        }

    # Discover all numeric features
    all_features = set()
    for s in sessions:
        all_features.update(_extract_numeric_features(s).keys())

    # Remove non-analytical fields
    skip_fields = {"win_detected"}
    all_features -= skip_fields

    # Compute effect size for each feature
    rankings = []
    for feature in sorted(all_features):
        success_vals = [
            s[feature] for s in success if feature in s and s[feature] is not None
        ]
        failure_vals = [
            s[feature] for s in failure if feature in s and s[feature] is not None
        ]

        d = _cohens_d(success_vals, failure_vals)
        if d is None:
            continue

        rankings.append(
            {
                "feature": feature,
                "effect_size_d": d,
                "abs_effect": abs(d),
                "direction": "success > failure" if d > 0 else "failure > success",
                "success_mean": round(statistics.mean(success_vals), 4)
                if success_vals
                else None,
                "failure_mean": round(statistics.mean(failure_vals), 4)
                if failure_vals
                else None,
                "success_n": len(success_vals),
                "failure_n": len(failure_vals),
            }
        )

    # Sort by absolute effect size (largest gaps first)
    rankings.sort(key=lambda x: x["abs_effect"], reverse=True)

    # Flag zero-variance features
    zero_variance = []
    for feature in sorted(all_features):
        vals = [s.get(feature) for s in sessions if s.get(feature) is not None]
        if vals and len(set(vals)) <= 1:
            zero_variance.append(feature)

    return {
        "sessions": total,
        "success_count": len(success),
        "failure_count": len(failure),
        "success_criteria": "level_completions > 0",
        "feature_rankings": rankings,
        "zero_variance_features": zero_variance,
    }


def _cross_game_summary(game_reports):
    """Identify features that matter across multiple games."""
    # Collect top features per game
    top_features = defaultdict(list)
    for game_type, report in game_reports.items():
        for rank in report.get("feature_rankings", [])[:5]:
            top_features[rank["feature"]].append(
                {
                    "game": game_type,
                    "effect_size": rank["effect_size_d"],
                    "direction": rank["direction"],
                }
            )

    # Features appearing in multiple games are candidates for general improvements
    cross_game = []
    for feature, games in top_features.items():
        if len(games) >= 2:
            cross_game.append(
                {
                    "feature": feature,
                    "games_count": len(games),
                    "per_game": games,
                    "consistent_direction": len(set(g["direction"] for g in games))
                    == 1,
                }
            )

    cross_game.sort(key=lambda x: x["games_count"], reverse=True)

    return {
        "cross_game_features": cross_game,
        "note": "Features ranking high across multiple games suggest general cognitive improvements, not game-specific hacks",
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Comparative Analyst")
    parser.add_argument("--generation", "-g", type=int, default=None)
    parser.add_argument("--db", type=str, default=None)
    args = parser.parse_args()

    result = run_analysis(args.generation, args.db)
    json.dump(result, sys.stdout, indent=2, default=str)
    print()


if __name__ == "__main__":
    main()
