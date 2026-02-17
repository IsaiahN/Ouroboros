"""
Code Tracer -- discovers subsystem engagement from trace data.

Two data sources (uses whichever is available):
1. traces/ directory (standard trace contract: traces/{gen}/{agent}/{step}.json)
2. cognitive_routing_traces table (existing DB-based traces)

Codebase-agnostic: discovers all subsystem names at runtime.

Usage:
    python -m lab.code_tracer                          # latest generation
    python -m lab.code_tracer --generation 5100        # specific generation
"""

import json
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "core_data.db"
TRACES_DIR = Path(__file__).resolve().parent.parent / "traces"


def _get_connection(db_path=None):
    path = str(db_path or DB_PATH)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def _table_exists(conn, table_name):
    result = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    return result[0] > 0


def scan_trace_files(generation=None):
    """
    Scan traces/ directory for subsystem data.
    Returns per-agent subsystem engagement reports.
    """
    if not TRACES_DIR.exists():
        return {"source": "trace_files", "available": False, "agents": {}}

    # Discover generation dirs
    if generation is not None:
        gen_dirs = [TRACES_DIR / str(generation)]
        gen_dirs = [d for d in gen_dirs if d.exists()]
    else:
        gen_dirs = sorted(
            [d for d in TRACES_DIR.iterdir() if d.is_dir()],
            key=lambda d: d.name,
        )
        if gen_dirs:
            gen_dirs = [gen_dirs[-1]]  # latest only

    if not gen_dirs:
        return {"source": "trace_files", "available": True, "agents": {}}

    agents = {}
    all_subsystems = set()

    for gen_dir in gen_dirs:
        for agent_dir in gen_dir.iterdir():
            if not agent_dir.is_dir():
                continue

            agent_id = agent_dir.name
            steps = []
            subsystem_counts = defaultdict(lambda: {"fired": 0, "silent": 0})
            decision_paths = defaultdict(int)

            for trace_file in sorted(agent_dir.glob("step_*.json")):
                try:
                    data = json.loads(trace_file.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    continue

                steps.append(data)
                subsystem = data.get("subsystem", "unknown")
                all_subsystems.add(subsystem)

                if data.get("produced_output", False):
                    subsystem_counts[subsystem]["fired"] += 1
                else:
                    subsystem_counts[subsystem]["silent"] += 1

                path = data.get("decision_path", [])
                if path:
                    path_key = " -> ".join(str(p) for p in path)
                    decision_paths[path_key] += 1

            total_steps = len(steps)
            if total_steps == 0:
                continue

            # Compute engagement rates
            engagement = {}
            for sub, counts in subsystem_counts.items():
                total = counts["fired"] + counts["silent"]
                engagement[sub] = {
                    "fired": counts["fired"],
                    "silent": counts["silent"],
                    "engagement_rate": round(counts["fired"] / total, 4)
                    if total > 0
                    else 0,
                }

            # Action diversity from traces
            actions = [s.get("action_selected") for s in steps if s.get("action_selected")]
            unique_actions = set(actions)

            agents[agent_id] = {
                "generation": gen_dir.name,
                "total_steps": total_steps,
                "subsystem_engagement": engagement,
                "decision_path_patterns": dict(
                    sorted(decision_paths.items(), key=lambda x: -x[1])[:20]
                ),
                "unique_actions": len(unique_actions),
                "total_actions": len(actions),
            }

    return {
        "source": "trace_files",
        "available": True,
        "all_subsystems_discovered": sorted(all_subsystems),
        "agents": agents,
    }


def scan_routing_traces(generation=None, db_path=None):
    """
    Scan cognitive_routing_traces table for subsystem data.
    Fallback when trace files don't exist yet.
    """
    conn = _get_connection(db_path)

    if not _table_exists(conn, "cognitive_routing_traces"):
        conn.close()
        return {"source": "cognitive_routing_traces", "available": False, "agents": {}}

    # Discover columns dynamically
    columns = {
        row[1] for row in conn.execute("PRAGMA table_info(cognitive_routing_traces)")
    }

    # Build query
    query = "SELECT * FROM cognitive_routing_traces"
    params = []

    if generation is not None and "agent_id" in columns:
        # Find agent_ids from this generation via game_results
        query += (
            " WHERE agent_id IN "
            "(SELECT DISTINCT agent_id FROM cognitive_routing_traces "
        )
        # Filter by game_id matching generation's sessions
        if _table_exists(conn, "game_results"):
            sessions = conn.execute(
                "SELECT DISTINCT session_id FROM game_results WHERE generation = ?",
                (generation,),
            ).fetchall()
            if sessions:
                # Try to match via game_id
                pass
        # Simpler: just get all recent traces
        query = "SELECT * FROM cognitive_routing_traces ORDER BY timestamp DESC LIMIT 5000"
        params = []

    rows = conn.execute(query, params).fetchall()
    conn.close()

    if not rows:
        return {
            "source": "cognitive_routing_traces",
            "available": True,
            "agents": {},
        }

    # Discover routing patterns
    agents = defaultdict(
        lambda: {
            "traces": 0,
            "algorithms_used": defaultdict(int),
            "quadrants": defaultdict(int),
            "avg_confidence": [],
            "avg_iterations": [],
            "backtrack_counts": [],
            "actions": set(),
        }
    )

    for row in rows:
        row_dict = dict(row)
        agent_id = row_dict.get("agent_id", "unknown")
        a = agents[agent_id]
        a["traces"] += 1

        if row_dict.get("algorithm_used"):
            a["algorithms_used"][row_dict["algorithm_used"]] += 1
        if row_dict.get("final_quadrant"):
            a["quadrants"][row_dict["final_quadrant"]] += 1
        if row_dict.get("final_confidence") is not None:
            a["avg_confidence"].append(row_dict["final_confidence"])
        if row_dict.get("iterations") is not None:
            a["avg_iterations"].append(row_dict["iterations"])
        if row_dict.get("backtrack_count") is not None:
            a["backtrack_counts"].append(row_dict["backtrack_count"])
        if row_dict.get("final_action"):
            a["actions"].add(row_dict["final_action"])

    # Compile per-agent reports
    compiled = {}
    all_algorithms = set()
    for agent_id, a in agents.items():
        all_algorithms.update(a["algorithms_used"].keys())
        conf = a["avg_confidence"]
        iters = a["avg_iterations"]
        compiled[agent_id] = {
            "traces": a["traces"],
            "algorithms_used": dict(a["algorithms_used"]),
            "quadrant_distribution": dict(a["quadrants"]),
            "avg_confidence": round(sum(conf) / len(conf), 4) if conf else None,
            "avg_iterations": round(sum(iters) / len(iters), 2) if iters else None,
            "avg_backtracks": (
                round(sum(a["backtrack_counts"]) / len(a["backtrack_counts"]), 2)
                if a["backtrack_counts"]
                else None
            ),
            "unique_actions": len(a["actions"]),
        }

    return {
        "source": "cognitive_routing_traces",
        "available": True,
        "all_algorithms_discovered": sorted(all_algorithms),
        "agents": compiled,
    }


def scan_behavioral_data(generation=None, db_path=None):
    """
    Extract behavioral features from game_results for the comparative analyst.
    These are the features the analyst will use for cohort comparison.
    """
    conn = _get_connection(db_path)

    query = "SELECT * FROM game_results"
    params = []
    if generation is not None:
        query += " WHERE generation = ?"
        params.append(generation)
    else:
        latest = conn.execute(
            "SELECT MAX(generation) FROM game_results"
        ).fetchone()[0]
        if latest is None:
            conn.close()
            return {"source": "game_results_behavioral", "agents": {}}
        query += " WHERE generation = ?"
        params.append(latest)
        generation = latest

    rows = conn.execute(query, params).fetchall()
    conn.close()

    # Group by session (proxy for agent attempt)
    sessions = {}
    for row in rows:
        r = dict(row)
        sid = r["session_id"]
        game_type = r["game_id"].split("-")[0] if r.get("game_id") else "unknown"

        # Compute behavioral features from available data
        total_actions = r.get("total_actions", 0) or 0
        coord_attempts = r.get("coordinate_attempts", 0) or 0
        coord_successes = r.get("coordinate_successes", 0) or 0
        frame_changes = r.get("frame_changes", 0) or 0
        level_completions = r.get("level_completions", 0) or 0

        sessions[sid] = {
            "game_type": game_type,
            "game_id": r.get("game_id"),
            "generation": r.get("generation"),
            "level_completions": level_completions,
            "win_detected": bool(r.get("win_detected")),
            "final_score": r.get("final_score", 0),
            "total_actions": total_actions,
            # Derived behavioral features
            "coord_success_rate": (
                round(coord_successes / coord_attempts, 4)
                if coord_attempts > 0
                else None
            ),
            "frame_change_rate": (
                round(frame_changes / total_actions, 4) if total_actions > 0 else None
            ),
            "actions_per_level": (
                round(total_actions / level_completions, 2)
                if level_completions > 0
                else None
            ),
        }

    return {
        "source": "game_results_behavioral",
        "generation": generation,
        "sessions": sessions,
    }


def run_full_trace(generation=None, db_path=None):
    """Run all trace sources and compile a unified report."""
    file_traces = scan_trace_files(generation)
    routing_traces = scan_routing_traces(generation, db_path)
    behavioral = scan_behavioral_data(generation, db_path)

    # Failure pattern detection from behavioral data
    failure_patterns = _detect_failure_patterns(behavioral.get("sessions", {}))

    return {
        "generation": generation,
        "trace_files": file_traces,
        "routing_traces": routing_traces,
        "behavioral": behavioral,
        "failure_patterns": failure_patterns,
    }


def _detect_failure_patterns(sessions):
    """
    Detect known failure patterns from behavioral data.
    Based on copilot-instructions Parts 3.2, 3.3, 3.5.
    """
    patterns = {
        "coordinate_fixation": [],
        "dead_clicks": [],
        "zero_frame_changes": [],
        "maxed_out_no_progress": [],
    }

    for sid, s in sessions.items():
        # Coordinate fixation: very low coord success rate on click games
        if s.get("coord_success_rate") is not None and s["coord_success_rate"] < 0.05:
            patterns["dead_clicks"].append(
                {
                    "session": sid,
                    "game": s["game_type"],
                    "rate": s["coord_success_rate"],
                }
            )

        # Zero frame changes despite many actions
        if (
            s.get("frame_change_rate") is not None
            and s["frame_change_rate"] < 0.05
            and s["total_actions"] > 20
        ):
            patterns["zero_frame_changes"].append(
                {
                    "session": sid,
                    "game": s["game_type"],
                    "rate": s["frame_change_rate"],
                    "actions": s["total_actions"],
                }
            )

        # Maxed out actions with zero level progress
        if s["level_completions"] == 0 and s["total_actions"] >= 100:
            patterns["maxed_out_no_progress"].append(
                {
                    "session": sid,
                    "game": s["game_type"],
                    "actions": s["total_actions"],
                }
            )

    # Summarize
    summary = {}
    for pattern_name, instances in patterns.items():
        summary[pattern_name] = {
            "count": len(instances),
            "examples": instances[:5],  # limit output
        }

    return summary


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Code Tracer - subsystem discovery")
    parser.add_argument("--generation", "-g", type=int, default=None)
    parser.add_argument("--db", type=str, default=None)
    parser.add_argument(
        "--source",
        choices=["all", "files", "routing", "behavioral"],
        default="all",
    )
    args = parser.parse_args()

    if args.source == "files":
        result = scan_trace_files(args.generation)
    elif args.source == "routing":
        result = scan_routing_traces(args.generation, args.db)
    elif args.source == "behavioral":
        result = scan_behavioral_data(args.generation, args.db)
    else:
        result = run_full_trace(args.generation, args.db)

    json.dump(result, sys.stdout, indent=2, default=str)
    print()


if __name__ == "__main__":
    main()
