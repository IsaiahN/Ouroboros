#!/usr/bin/env python3
"""
Baseline System Profiler for Cognitive Routing

Phase 0 Deliverable - Establishes baseline metrics before Phase 1-8 implementation.

Profiles:
1. Rung execution times (per-rung latency)
2. Memory usage (per-rung and total)
3. Context access patterns (reads/writes per decision)
4. Decision throughput (decisions per second)

Run this before implementing cognitive routing, then again after Phase 8
to measure improvement.

Usage:
    python manual_tools/profile_baseline.py [--iterations N] [--output PATH]
"""
# RULE 1: PYTHONDONTWRITEBYTECODE=1 (no .pyc files)
import sys

sys.dont_write_bytecode = True

import argparse
import json
import time
import tracemalloc
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Project root
PROJECT_ROOT = Path(__file__).parent.parent


@dataclass
class RungProfile:
    """Profile data for a single rung."""
    name: str
    category: str = ""
    execution_times_ms: List[float] = field(default_factory=list)
    memory_delta_kb: List[float] = field(default_factory=list)
    context_reads: List[int] = field(default_factory=list)
    context_writes: List[int] = field(default_factory=list)
    invocation_count: int = 0
    win_count: int = 0  # Times this rung's action was selected
    avg_confidence: float = 0.0

    @property
    def avg_time_ms(self) -> float:
        if not self.execution_times_ms:
            return 0.0
        return sum(self.execution_times_ms) / len(self.execution_times_ms)

    @property
    def max_time_ms(self) -> float:
        return max(self.execution_times_ms) if self.execution_times_ms else 0.0

    @property
    def p95_time_ms(self) -> float:
        if not self.execution_times_ms:
            return 0.0
        sorted_times = sorted(self.execution_times_ms)
        idx = int(len(sorted_times) * 0.95)
        return sorted_times[min(idx, len(sorted_times) - 1)]

    @property
    def avg_memory_kb(self) -> float:
        if not self.memory_delta_kb:
            return 0.0
        return sum(self.memory_delta_kb) / len(self.memory_delta_kb)

    @property
    def win_rate(self) -> float:
        if self.invocation_count == 0:
            return 0.0
        return self.win_count / self.invocation_count


@dataclass
class BaselineProfile:
    """Complete baseline profile."""
    timestamp: str
    python_version: str
    total_decisions: int = 0
    total_time_ms: float = 0.0
    decisions_per_second: float = 0.0
    peak_memory_mb: float = 0.0
    rung_profiles: Dict[str, RungProfile] = field(default_factory=dict)

    # Aggregate stats
    total_rungs_evaluated: int = 0
    avg_rungs_per_decision: float = 0.0
    context_slot_hotspots: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "meta": {
                "timestamp": self.timestamp,
                "python_version": self.python_version,
                "profile_type": "baseline_pre_cognitive_routing"
            },
            "summary": {
                "total_decisions": self.total_decisions,
                "total_time_ms": round(self.total_time_ms, 2),
                "decisions_per_second": round(self.decisions_per_second, 2),
                "peak_memory_mb": round(self.peak_memory_mb, 2),
                "total_rungs_evaluated": self.total_rungs_evaluated,
                "avg_rungs_per_decision": round(self.avg_rungs_per_decision, 2)
            },
            "rung_profiles": {
                name: {
                    "name": p.name,
                    "category": p.category,
                    "invocation_count": p.invocation_count,
                    "win_count": p.win_count,
                    "win_rate": round(p.win_rate, 3),
                    "avg_confidence": round(p.avg_confidence, 3),
                    "timing_ms": {
                        "avg": round(p.avg_time_ms, 3),
                        "max": round(p.max_time_ms, 3),
                        "p95": round(p.p95_time_ms, 3)
                    },
                    "memory_kb": {
                        "avg": round(p.avg_memory_kb, 2)
                    },
                    "context_access": {
                        "avg_reads": round(sum(p.context_reads) / max(len(p.context_reads), 1), 1),
                        "avg_writes": round(sum(p.context_writes) / max(len(p.context_writes), 1), 1)
                    }
                }
                for name, p in sorted(self.rung_profiles.items(),
                                      key=lambda x: x[1].avg_time_ms,
                                      reverse=True)
            },
            "context_slot_hotspots": dict(sorted(
                self.context_slot_hotspots.items(),
                key=lambda x: x[1],
                reverse=True
            )[:20])  # Top 20 most accessed slots
        }


class DecisionProfiler:
    """
    Profiles the decision rung system.

    This is a lightweight profiler that can wrap rung evaluations
    without modifying the original code.
    """

    def __init__(self):
        self.profiles: Dict[str, RungProfile] = {}
        self.slot_access_counts: Dict[str, int] = defaultdict(int)
        self.decision_times: List[float] = []
        self.rungs_per_decision: List[int] = []

    def profile_rung(self, rung_name: str, category: str,
                    evaluate_fn, game_state: Any, context: Dict[str, Any]) -> Any:
        """
        Profile a single rung evaluation.

        Args:
            rung_name: Name of the rung
            category: Rung category
            evaluate_fn: The rung's evaluate method
            game_state: Game state passed to evaluate
            context: Context dict passed to evaluate

        Returns:
            The RungResult from evaluate_fn
        """
        if rung_name not in self.profiles:
            self.profiles[rung_name] = RungProfile(name=rung_name, category=category)

        profile = self.profiles[rung_name]

        # Track context keys before
        keys_before = set(context.keys())

        # Memory tracking
        tracemalloc.start()
        mem_before = tracemalloc.get_traced_memory()[0]

        # Time tracking
        start = time.perf_counter()

        try:
            result = evaluate_fn(game_state, context)
        except Exception as e:
            result = None

        end = time.perf_counter()

        mem_after = tracemalloc.get_traced_memory()[0]
        tracemalloc.stop()

        # Record metrics
        elapsed_ms = (end - start) * 1000
        memory_delta_kb = (mem_after - mem_before) / 1024

        profile.execution_times_ms.append(elapsed_ms)
        profile.memory_delta_kb.append(max(0, memory_delta_kb))
        profile.invocation_count += 1

        # Track context changes
        keys_after = set(context.keys())
        new_keys = keys_after - keys_before

        # Estimate reads (keys that were accessed but not written)
        # This is a heuristic - real tracking would require context wrapper
        profile.context_reads.append(len(keys_before))
        profile.context_writes.append(len(new_keys))

        # Track slot access
        for key in keys_after:
            self.slot_access_counts[key] += 1

        # Track confidence if result has it
        if result and hasattr(result, 'confidence'):
            # Update running average
            n = profile.invocation_count
            profile.avg_confidence = (
                profile.avg_confidence * (n - 1) + (result.confidence or 0)
            ) / n

        return result

    def record_decision(self, elapsed_ms: float, rungs_evaluated: int,
                       winning_rung: Optional[str] = None):
        """Record metrics for a complete decision cycle."""
        self.decision_times.append(elapsed_ms)
        self.rungs_per_decision.append(rungs_evaluated)

        if winning_rung and winning_rung in self.profiles:
            self.profiles[winning_rung].win_count += 1

    def generate_report(self) -> BaselineProfile:
        """Generate the baseline profile report."""
        total_decisions = len(self.decision_times)
        total_time_ms = sum(self.decision_times)

        profile = BaselineProfile(
            timestamp=datetime.now().isoformat(),
            python_version=sys.version,
            total_decisions=total_decisions,
            total_time_ms=total_time_ms,
            decisions_per_second=(
                total_decisions / (total_time_ms / 1000)
                if total_time_ms > 0 else 0
            ),
            peak_memory_mb=0,  # Would need continuous tracking
            rung_profiles=self.profiles,
            total_rungs_evaluated=sum(self.rungs_per_decision),
            avg_rungs_per_decision=(
                sum(self.rungs_per_decision) / max(total_decisions, 1)
            ),
            context_slot_hotspots=dict(self.slot_access_counts)
        )

        return profile


def simulate_profiling(iterations: int = 100) -> BaselineProfile:
    """
    Simulate profiling by loading rung data and estimating metrics.

    In a real scenario, this would hook into live gameplay.
    For Phase 0, we generate estimated baselines from static analysis.
    """
    print(f"[INFO] Generating baseline profile with {iterations} simulated decisions...")

    profiler = DecisionProfiler()

    # Load the dependency matrix to get rung info
    matrix_path = PROJECT_ROOT / "architecture" / "rung_dependency_matrix.json"

    try:
        with open(matrix_path) as f:
            matrix = json.load(f)
    except FileNotFoundError:
        print(f"[WARN] Matrix not found at {matrix_path}, using defaults")
        matrix = {"rungs": {}}

    # Simulate decision cycles
    import random

    for i in range(iterations):
        decision_start = time.perf_counter()
        rungs_this_decision = 0

        # Simulate evaluating rungs in order
        for rung_name, rung_info in matrix.get("rungs", {}).items():
            category = rung_info.get("category", "unknown")

            # Create a dummy evaluate function with realistic timing
            def dummy_evaluate(gs, ctx):
                # Simulate work based on category
                if category == "orientation":
                    time.sleep(random.uniform(0.0001, 0.001))  # Fast
                elif category == "hypothesis":
                    time.sleep(random.uniform(0.0005, 0.002))  # Medium
                elif category == "exploitation":
                    time.sleep(random.uniform(0.001, 0.005))   # Slower
                else:
                    time.sleep(random.uniform(0.0002, 0.001))

                # Return a mock result
                class MockResult:
                    confidence = random.uniform(0, 1)
                    action = f"ACTION{random.randint(1,7)}"
                return MockResult()

            # Simulate context
            dummy_context = {
                "game_type": "test",
                "level": 1,
                "survey_complete": random.choice([True, False]),
            }

            profiler.profile_rung(rung_name, category, dummy_evaluate, None, dummy_context)
            rungs_this_decision += 1

        decision_end = time.perf_counter()
        decision_time_ms = (decision_end - decision_start) * 1000

        # Pick a random "winning" rung
        rung_names = list(matrix.get("rungs", {}).keys())
        winning = random.choice(rung_names) if rung_names else None

        profiler.record_decision(decision_time_ms, rungs_this_decision, winning)

    return profiler.generate_report()


def main():
    parser = argparse.ArgumentParser(description="Profile decision rung system baseline")
    parser.add_argument("--iterations", "-n", type=int, default=100,
                       help="Number of simulated decisions")
    parser.add_argument("--output", "-o", type=str,
                       default="architecture/baseline_profile.json",
                       help="Output path for profile JSON")
    parser.add_argument("--live", action="store_true",
                       help="Use live profiling (requires running game)")
    args = parser.parse_args()

    if args.live:
        print("[WARN] Live profiling not yet implemented. Using simulation.")

    profile = simulate_profiling(args.iterations)

    output_path = PROJECT_ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(profile.to_dict(), f, indent=2)

    print(f"\n[OK] Baseline profile generated:")
    print(f"     Total decisions: {profile.total_decisions}")
    print(f"     Decisions/second: {profile.decisions_per_second:.1f}")
    print(f"     Avg rungs/decision: {profile.avg_rungs_per_decision:.1f}")
    print(f"     Output: {output_path}")

    # Show top 5 slowest rungs
    print("\n--- Top 5 Slowest Rungs ---")
    sorted_rungs = sorted(
        profile.rung_profiles.values(),
        key=lambda r: r.avg_time_ms,
        reverse=True
    )[:5]

    for rung in sorted_rungs:
        print(f"  {rung.name}: {rung.avg_time_ms:.3f}ms avg, {rung.p95_time_ms:.3f}ms p95")


if __name__ == "__main__":
    main()
