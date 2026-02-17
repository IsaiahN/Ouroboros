"""
Branch Breeder -- combinatorial search across successful experiments.

Uses git for all branch operations. Reads Trend Tracker for successful
experiments. Entirely codebase-agnostic -- manages branches, not code.

Usage:
    python -m lab.branch_breeder list                  # list successful experiments
    python -m lab.branch_breeder combine exp/a exp/b   # create crossbred branch
    python -m lab.branch_breeder status                # show all crossbred branches
"""

import json
import subprocess
import sys
from itertools import combinations
from pathlib import Path

# Import sibling module
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _run_git(*args, check=True):
    """Run a git command and return stdout."""
    cmd = ["git"] + list(args)
    result = subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    if check and result.returncode != 0:
        return {"ok": False, "error": result.stderr.strip()}
    return {"ok": True, "output": result.stdout.strip()}


def list_experiment_branches():
    """List all experiment/* branches."""
    result = _run_git("branch", "--list", "experiment/*", check=False)
    if not result["ok"]:
        return []
    branches = [b.strip().lstrip("* ") for b in result["output"].split("\n") if b.strip()]
    return branches


def list_crossbred_branches():
    """List all crossbred/* branches."""
    result = _run_git("branch", "--list", "crossbred/*", check=False)
    if not result["ok"]:
        return []
    branches = [b.strip().lstrip("* ") for b in result["output"].split("\n") if b.strip()]
    return branches


def get_current_branch():
    """Get current branch name."""
    result = _run_git("rev-parse", "--abbrev-ref", "HEAD")
    return result.get("output", "unknown") if result["ok"] else "unknown"


def branch_exists(branch_name):
    """Check if a branch exists."""
    result = _run_git("rev-parse", "--verify", branch_name, check=False)
    return result["ok"]


def create_crossbred_branch(branch_a, branch_b, base_branch="lab/mainline"):
    """
    Create a crossbred branch by merging two experiment branches.

    Returns merge result with conflict status.
    """
    # Validate inputs
    if not branch_exists(branch_a):
        return {"ok": False, "error": f"Branch {branch_a} does not exist"}
    if not branch_exists(branch_b):
        return {"ok": False, "error": f"Branch {branch_b} does not exist"}

    # Generate crossbred branch name
    name_a = branch_a.replace("experiment/", "").replace("/", "-")
    name_b = branch_b.replace("experiment/", "").replace("/", "-")
    crossbred_name = f"crossbred/{name_a}_x_{name_b}"

    if branch_exists(crossbred_name):
        return {
            "ok": False,
            "error": f"Crossbred branch {crossbred_name} already exists",
        }

    # Save current branch
    original_branch = get_current_branch()

    # Create crossbred branch from base
    base = base_branch if branch_exists(base_branch) else branch_a
    result = _run_git("checkout", "-b", crossbred_name, base)
    if not result["ok"]:
        return {"ok": False, "error": f"Failed to create branch: {result['error']}"}

    # Merge branch_a (if base wasn't branch_a)
    if base != branch_a:
        result = _run_git("merge", branch_a, "--no-edit", check=False)
        if not result["ok"]:
            # Check for merge conflicts
            status = _run_git("status", "--porcelain", check=False)
            if "UU" in status.get("output", ""):
                _run_git("merge", "--abort", check=False)
                _run_git("checkout", original_branch, check=False)
                _run_git("branch", "-D", crossbred_name, check=False)
                return {
                    "ok": False,
                    "error": f"Merge conflict merging {branch_a}",
                    "needs_resolution": True,
                    "branch_a": branch_a,
                    "branch_b": branch_b,
                }

    # Merge branch_b
    result = _run_git("merge", branch_b, "--no-edit", check=False)
    if not result["ok"]:
        status = _run_git("status", "--porcelain", check=False)
        if "UU" in status.get("output", ""):
            _run_git("merge", "--abort", check=False)
            _run_git("checkout", original_branch, check=False)
            _run_git("branch", "-D", crossbred_name, check=False)
            return {
                "ok": False,
                "error": f"Merge conflict merging {branch_b}",
                "needs_resolution": True,
                "branch_a": branch_a,
                "branch_b": branch_b,
            }

    # Return to original branch
    _run_git("checkout", original_branch, check=False)

    return {
        "ok": True,
        "crossbred_branch": crossbred_name,
        "parents": [branch_a, branch_b],
        "base": base,
    }


def generate_combinations(branches, max_pairs=10):
    """Generate pair combinations from successful branches."""
    pairs = list(combinations(branches, 2))
    return pairs[:max_pairs]


def get_breeding_candidates(db_path=None):
    """Get successful experiments from Trend Tracker for breeding."""
    from lab.trend_tracker import get_successful_experiments

    experiments = get_successful_experiments(db_path)
    branches = [e["branch_name"] for e in experiments if e.get("branch_name")]

    # Filter to branches that still exist
    existing = [b for b in branches if branch_exists(b)]

    return {
        "total_successful": len(experiments),
        "branches_exist": len(existing),
        "branches": existing,
        "combinations": generate_combinations(existing),
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Branch Breeder")
    subparsers = parser.add_subparsers(dest="command")

    # list
    subparsers.add_parser("list", help="List experiment branches")

    # combine
    comb = subparsers.add_parser("combine", help="Create crossbred branch")
    comb.add_argument("branch_a", help="First experiment branch")
    comb.add_argument("branch_b", help="Second experiment branch")
    comb.add_argument("--base", default="lab/mainline", help="Base branch")

    # status
    subparsers.add_parser("status", help="Show all crossbred branches")

    # candidates
    subparsers.add_parser("candidates", help="Show breeding candidates from Trend Tracker")

    parser.add_argument("--db", type=str, default=None)
    args = parser.parse_args()

    if args.command == "list":
        result = {
            "experiment_branches": list_experiment_branches(),
            "crossbred_branches": list_crossbred_branches(),
        }
    elif args.command == "combine":
        result = create_crossbred_branch(
            args.branch_a, args.branch_b, base_branch=args.base
        )
    elif args.command == "status":
        result = {
            "crossbred_branches": list_crossbred_branches(),
            "current_branch": get_current_branch(),
        }
    elif args.command == "candidates":
        result = get_breeding_candidates(args.db)
    else:
        parser.print_help()
        return

    json.dump(result, sys.stdout, indent=2, default=str)
    print()


if __name__ == "__main__":
    main()
