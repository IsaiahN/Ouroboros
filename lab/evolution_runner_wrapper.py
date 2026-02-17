"""
Evolution Runner Wrapper -- runs evolution trials and collects metrics.

Wraps the existing evolution_runner.py with lab-specific functionality:
- Switches to the target branch before running
- Collects before/after metrics
- Returns structured results

Usage:
    python -m lab.evolution_runner_wrapper --branch lab/mainline --generations 5
    python -m lab.evolution_runner_wrapper --branch experiment/foo --generations 3 --agents 10
"""

import json
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYTHON = str(PROJECT_ROOT / ".venv" / "Scripts" / "python.exe")

# Import sibling for metrics
sys.path.insert(0, str(PROJECT_ROOT))


def _run_cmd(cmd, timeout=None):
    """Run a command and return result."""
    result = subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
        env={**__import__("os").environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    return {
        "returncode": result.returncode,
        "stdout": result.stdout[-5000:] if result.stdout else "",  # last 5KB
        "stderr": result.stderr[-2000:] if result.stderr else "",
    }


def _get_current_branch():
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip()


def _get_latest_generation():
    """Get the latest generation number from game_results."""
    import sqlite3

    db_path = PROJECT_ROOT / "core_data.db"
    conn = sqlite3.connect(str(db_path))
    result = conn.execute("SELECT MAX(generation) FROM game_results").fetchone()
    conn.close()
    return result[0] if result[0] is not None else 0


def collect_metrics(generation=None):
    """Collect metrics for a given generation."""
    from lab.metrics import compute_metrics

    return compute_metrics(generation=generation)


def run_evolution(
    branch=None,
    generations=5,
    population=50,
    agents_per_gen=30,
    games_per_gen=3,
    max_actions=150,
    target_game=None,
    mode="offline",
    timeout_minutes=60,
):
    """
    Run an evolution trial.

    Args:
        branch: git branch to run on (switches and switches back)
        generations: number of generations to evolve
        population: population size
        agents_per_gen: agents selected per generation
        games_per_gen: games per agent per generation
        max_actions: max actions per game
        target_game: specific game to focus on (e.g., 'ls20')
        mode: 'offline' or 'online'
        timeout_minutes: max runtime in minutes

    Returns:
        dict with before/after metrics and trial metadata
    """
    original_branch = _get_current_branch()

    # Switch branch if specified
    if branch and branch != original_branch:
        result = subprocess.run(
            ["git", "checkout", branch],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return {"ok": False, "error": f"Cannot checkout {branch}: {result.stderr}"}

    try:
        # Collect before metrics
        gen_before = _get_latest_generation()
        metrics_before = collect_metrics(generation=gen_before)

        # Build evolution command
        cmd = [
            PYTHON,
            str(PROJECT_ROOT / "evolution_runner.py"),
            f"--mode={mode}",
            f"--population={population}",
            f"--agents-per-gen={agents_per_gen}",
            f"--games-per-gen={games_per_gen}",
            f"--max-generations={generations}",
            f"--max-actions={max_actions}",
        ]
        if target_game:
            cmd.append(f"--game={target_game}")

        # Run evolution
        start_time = time.time()
        result = _run_cmd(cmd, timeout=timeout_minutes * 60)
        elapsed = time.time() - start_time

        # Collect after metrics
        gen_after = _get_latest_generation()
        metrics_after = collect_metrics(generation=gen_after)

        return {
            "ok": result["returncode"] == 0,
            "branch": branch or original_branch,
            "generation_before": gen_before,
            "generation_after": gen_after,
            "generations_run": gen_after - gen_before,
            "elapsed_seconds": round(elapsed, 1),
            "metrics_before": metrics_before,
            "metrics_after": metrics_after,
            "evolution_stdout_tail": result["stdout"][-2000:],
            "evolution_stderr_tail": result["stderr"][-1000:],
            "returncode": result["returncode"],
        }

    finally:
        # Always switch back to original branch
        if branch and branch != original_branch:
            subprocess.run(
                ["git", "checkout", original_branch],
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
                check=False,
            )


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Evolution Runner Wrapper")
    parser.add_argument("--branch", "-b", default=None, help="Git branch to run on")
    parser.add_argument("--generations", "-g", type=int, default=5)
    parser.add_argument("--population", type=int, default=50)
    parser.add_argument("--agents-per-gen", type=int, default=30)
    parser.add_argument("--games-per-gen", type=int, default=3)
    parser.add_argument("--max-actions", type=int, default=150)
    parser.add_argument("--target-game", default=None)
    parser.add_argument("--mode", default="offline")
    parser.add_argument("--timeout", type=int, default=60, help="Timeout in minutes")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show command without running"
    )
    args = parser.parse_args()

    if args.dry_run:
        result = {
            "dry_run": True,
            "branch": args.branch,
            "command": [
                PYTHON,
                "evolution_runner.py",
                f"--mode={args.mode}",
                f"--population={args.population}",
                f"--max-generations={args.generations}",
            ],
        }
    else:
        result = run_evolution(
            branch=args.branch,
            generations=args.generations,
            population=args.population,
            agents_per_gen=args.agents_per_gen,
            games_per_gen=args.games_per_gen,
            max_actions=args.max_actions,
            target_game=args.target_game,
            mode=args.mode,
            timeout_minutes=args.timeout,
        )

    json.dump(result, sys.stdout, indent=2, default=str)
    print()


if __name__ == "__main__":
    main()
