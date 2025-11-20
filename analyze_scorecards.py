"""
Per-Generation Scorecard Analysis
Automates the recurring task of analyzing ARC scorecards for system-level issues.
"""

import sqlite3
import requests
from datetime import datetime
import json
import os

DB_PATH = "core_data.db"
SCORECARDS_URL = "https://three.arcprize.org/scorecards"


def analyze_recent_scorecards(max_scorecards=10):
    """
    Analyze recent scorecards for system-level issues.

    This implements the recurring task from task.md lines 175-206:
    - Identifies problem scorecards (0 levels, high actions)
    - Compares with database sequences
    - Generates analysis report

    Args:
        max_scorecards: Maximum number of scorecards to analyze
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print(f"🔍 Per-Generation Scorecard Analysis")
    print("=" * 70)
    print(f"Analyzing up to {max_scorecards} recent scorecards...")
    print()

    # Get recent game results from database
    cursor.execute(
        """
        SELECT 
            gr.scorecard_id,
            gr.game_id,
            gr.final_score,
            gr.total_actions,
            gr.level_completions,
            gr.status,
            gr.created_at,
            aom.operating_mode
        FROM game_results gr
        LEFT JOIN agent_operating_modes aom ON gr.scorecard_id = aom.agent_id
        ORDER BY gr.created_at DESC
        LIMIT ?
    """,
        (max_scorecards,),
    )

    recent_games = cursor.fetchall()

    if not recent_games:
        print("No recent game results found.")
        conn.close()
        return

    # Identify problem scorecards
    problem_scorecards = []
    for game in recent_games:
        is_problem = False
        problem_type = []

        # Problem criteria
        if game["level_completions"] == 0 and game["total_actions"] > 50:
            is_problem = True
            problem_type.append(f"0 levels with {game['total_actions']} actions")

        if game["total_actions"] > 200:
            is_problem = True
            problem_type.append(f"excessive actions ({game['total_actions']})")

        if game["total_actions"] == 0:
            is_problem = True
            problem_type.append("0 actions taken")

        if is_problem:
            problem_scorecards.append(
                {
                    "scorecard_id": game["scorecard_id"],
                    "game_id": game["game_id"],
                    "score": game["final_score"],
                    "actions": game["total_actions"],
                    "levels": game["level_completions"],
                    "mode": game["operating_mode"],
                    "problems": problem_type,
                    "created_at": game["created_at"],
                }
            )

    print(f"📊 Analysis Results:")
    print(f"  Total scorecards analyzed: {len(recent_games)}")
    print(f"  Problem scorecards found: {len(problem_scorecards)}")
    print()

    if problem_scorecards:
        print("⚠️  PROBLEM SCORECARDS:")
        print("-" * 70)

        for i, sc in enumerate(problem_scorecards, 1):
            print(f"\n{i}. Scorecard: {sc['scorecard_id']}")
            print(f"   Game: {sc['game_id']}")
            print(f"   Mode: {sc['mode']}")
            print(
                f"   Score: {sc['score']}, Actions: {sc['actions']}, Levels: {sc['levels']}"
            )
            print(f"   Issues: {', '.join(sc['problems'])}")

            # Check for sequences in database
            game_type = (
                sc["game_id"].split("-")[0] if "-" in sc["game_id"] else sc["game_id"]
            )
            cursor.execute(
                """
                SELECT COUNT(*) as seq_count
                FROM winning_sequences
                WHERE game_id LIKE ?
            """,
                (f"{game_type}-%",),
            )

            seq_count = cursor.fetchone()["seq_count"]

            if seq_count == 0:
                print(f"   🔴 No sequences found for game type {game_type}")
            else:
                print(
                    f"   ✅ {seq_count} sequences available for game type {game_type}"
                )

                # Check if sequence was attempted
                cursor.execute(
                    """
                    SELECT COUNT(*) as attempt_count
                    FROM action_traces
                    WHERE game_id = ? AND session_id IN (
                        SELECT session_id FROM game_results WHERE scorecard_id = ?
                    )
                """,
                    (sc["game_id"], sc["scorecard_id"]),
                )

                attempt_count = cursor.fetchone()["attempt_count"]

                if attempt_count > 0:
                    print(
                        f"   📝 {attempt_count} actions traced (sequence may have failed)"
                    )
                else:
                    print(f"   ⚠️  No action traces found (sequence not attempted?)")

        # Generate recommendations
        print("\n" + "=" * 70)
        print("🔧 RECOMMENDATIONS:")
        print("-" * 70)

        zero_level_count = sum(1 for sc in problem_scorecards if sc["levels"] == 0)
        zero_action_count = sum(1 for sc in problem_scorecards if sc["actions"] == 0)
        excessive_action_count = sum(
            1 for sc in problem_scorecards if sc["actions"] > 200
        )

        if zero_level_count > 0:
            print(f"• {zero_level_count} scorecards with 0 level completions")
            print(f"  → Check if sequences are being retrieved correctly")
            print(f"  → Verify sequence replay logic is working")
            print(f"  → Run: python validate_sequences.py --max 10")

        if zero_action_count > 0:
            print(f"• {zero_action_count} scorecards with 0 actions")
            print(f"  → Critical: Agents not taking actions")
            print(f"  → Check for exceptions in play_single_game")
            print(f"  → Verify API connectivity")

        if excessive_action_count > 0:
            print(
                f"• {excessive_action_count} scorecards with excessive actions (>200)"
            )
            print(f"  → Agents may be stuck in loops")
            print(f"  → Check sensation engine for stuck states")
            print(f"  → Review action selection logic")

        # Store analysis
        cursor.execute(
            """
            INSERT INTO scorecard_analysis_history (
                analysis_date, total_scorecards, problem_count,
                zero_levels, zero_actions, excessive_actions, details
            ) VALUES (CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?)
        """,
            (
                len(recent_games),
                len(problem_scorecards),
                zero_level_count,
                zero_action_count,
                excessive_action_count,
                json.dumps(problem_scorecards),
            ),
        )

        conn.commit()

    else:
        print("✅ No problem scorecards found - system performing well!")

    conn.close()
    print("\n" + "=" * 70)


def create_analysis_table_if_needed():
    """Create scorecard_analysis_history table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scorecard_analysis_history (
            analysis_id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_scorecards INTEGER,
            problem_count INTEGER,
            zero_levels INTEGER,
            zero_actions INTEGER,
            excessive_actions INTEGER,
            details TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analytics_snapshots (
            snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_type TEXT,
            data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze recent scorecards for system issues"
    )
    parser.add_argument(
        "--max", type=int, default=10, help="Maximum scorecards to analyze"
    )
    args = parser.parse_args()

    create_analysis_table_if_needed()
    analyze_recent_scorecards(args.max)
