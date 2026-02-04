"""
Validate Inferred Edges - Three-List Validation Tool

Phase 2.5 Implementation - Cognitive Routing

This tool validates edges inferred by EdgeInferenceEngine using three-list categorization:
1. CONFIDENT: Auto-accept (strong evidence from multiple sources)
2. UNCERTAIN: Human review needed (weak evidence or conflicting signals)
3. MISSING: Expected but not found (investigate why)

Usage:
    python manual_tools/validate_inferred_edges.py [--run-inference] [--export FILE]

    --run-inference: Run fresh inference before validation
    --export FILE: Export validated edges to JSON file
    --expected FILE: Load expected patterns from JSON for "missing" detection
"""
# RULE 1: PYTHONDONTWRITEBYTECODE=1 (no .pyc files)
import sys

sys.dont_write_bytecode = True

import argparse
import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from engines.cognition.edge_inference import (
    EdgeInferenceEngine,
    EdgeType,
    EdgeValidationResult,
    InferenceConfidence,
    InferenceSource,
    InferredEdge,
    load_rung_classes_from_module,
)

logger = logging.getLogger(__name__)


# =============================================================================
# EXPECTED PATTERNS
# =============================================================================

# Expected edge patterns (ground truth for validation)
# These are edges we expect to find based on domain knowledge

EXPECTED_DEPENDENCIES = {
    # survey should feed into control_tracker
    'survey': ['control_tracker', 'palette_detection', 'sparse_grid'],
    # control_tracker should feed into action selection
    'control_tracker': ['smart_action_selection', 'frontier_checkpoint'],
    # frame_interpretation should feed into event_understanding
    'frame_interpretation': ['event_understanding'],
    # theory_gate should feed into hypothesis_testing
    'theory_gate': ['hypothesis_testing'],
    # network_wisdom should feed into exploration_phase
    'network_wisdom': ['exploration_phase'],
}

EXPECTED_IMPLICATIONS = {
    # If death_avoidance activates, exploitation should respect it
    'death_avoidance': ['smart_action_selection', 'exploration_phase'],
    # If hypothesis confirmed, exploitation should follow
    'hypothesis_testing': ['discovery_exploitation', 'smart_action_selection'],
}

EXPECTED_FALLBACKS = {
    # If hypothesis fails, fall back to network wisdom
    'hypothesis_testing': 'network_wisdom',
    'discovery_exploitation': 'exploration_phase',
    'theory_gate': 'scientific_method',
}


@dataclass
class ValidationReport:
    """Detailed report from edge validation."""
    timestamp: datetime = field(default_factory=datetime.now)
    total_edges: int = 0
    confident_count: int = 0
    uncertain_count: int = 0
    missing_count: int = 0

    # Breakdown by type
    by_type: Dict[str, Dict[str, int]] = field(default_factory=lambda: defaultdict(lambda: defaultdict(int)))

    # Breakdown by source
    by_source: Dict[str, Dict[str, int]] = field(default_factory=lambda: defaultdict(lambda: defaultdict(int)))

    # Issues detected
    issues: List[str] = field(default_factory=list)

    # Recommendations
    recommendations: List[str] = field(default_factory=list)


def build_expected_patterns() -> Dict[str, Any]:
    """Build expected patterns dict for validation."""
    return {
        'dependencies': EXPECTED_DEPENDENCIES,
        'implications': EXPECTED_IMPLICATIONS,
        'fallbacks': EXPECTED_FALLBACKS
    }


def analyze_confidence_distribution(edges: List[InferredEdge]) -> Dict[str, Any]:
    """Analyze the score distribution of edges."""
    scores = [e.score for e in edges]

    if not scores:
        return {'count': 0}

    return {
        'count': len(scores),
        'min': min(scores),
        'max': max(scores),
        'mean': sum(scores) / len(scores),
        'below_0.5': sum(1 for s in scores if s < 0.5),
        'above_0.7': sum(1 for s in scores if s >= 0.7),
        'above_0.9': sum(1 for s in scores if s >= 0.9)
    }


def check_for_cycles(edges: List[InferredEdge]) -> List[List[str]]:
    """Check for cycles in dependency edges (could cause infinite loops)."""
    # Build adjacency list for dependency edges
    adj: Dict[str, List[str]] = defaultdict(list)
    for edge in edges:
        if edge.edge_type == EdgeType.DEPENDENCY:
            adj[edge.source_rung].append(edge.target_rung)

    # DFS-based cycle detection
    cycles: List[List[str]] = []
    visited = set()
    rec_stack = set()

    def dfs(node: str, path: List[str]) -> None:
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in adj.get(node, []):
            if neighbor not in visited:
                dfs(neighbor, path)
            elif neighbor in rec_stack:
                # Found cycle
                cycle_start = path.index(neighbor)
                cycle = path[cycle_start:] + [neighbor]
                cycles.append(cycle)

        path.pop()
        rec_stack.remove(node)

    for node in adj:
        if node not in visited:
            dfs(node, [])

    return cycles


def check_orphan_rungs(
    edges: List[InferredEdge],
    all_rungs: List[str]
) -> Tuple[List[str], List[str]]:
    """
    Check for rungs with no incoming or outgoing edges.

    Returns:
        (no_incoming, no_outgoing) - Lists of orphaned rungs
    """
    sources = set()
    targets = set()

    for edge in edges:
        sources.add(edge.source_rung)
        targets.add(edge.target_rung)

    all_rung_set = set(all_rungs)

    no_incoming = [r for r in all_rung_set if r not in targets]
    no_outgoing = [r for r in all_rung_set if r not in sources]

    return (no_incoming, no_outgoing)


def check_contradicting_edges(edges: List[InferredEdge]) -> List[Dict[str, Any]]:
    """
    Check for contradicting edges (A->B dependency and A->B contradiction).
    """
    edge_map: Dict[Tuple[str, str], List[InferredEdge]] = defaultdict(list)

    for edge in edges:
        key = (edge.source_rung, edge.target_rung)
        edge_map[key].append(edge)

    conflicts = []
    for key, edge_list in edge_map.items():
        if len(edge_list) > 1:
            types = set(e.edge_type for e in edge_list)

            # Check for conflicting types
            if EdgeType.DEPENDENCY in types and EdgeType.CONTRADICTION in types:
                conflicts.append({
                    'source': key[0],
                    'target': key[1],
                    'conflict_types': [e.edge_type.value for e in edge_list],
                    'scores': [e.score for e in edge_list]
                })

    return conflicts


def generate_report(
    validation_result: EdgeValidationResult,
    engine: EdgeInferenceEngine,
    all_rungs: List[str]
) -> ValidationReport:
    """Generate comprehensive validation report."""
    report = ValidationReport(
        total_edges=len(validation_result.confident) + len(validation_result.uncertain),
        confident_count=len(validation_result.confident),
        uncertain_count=len(validation_result.uncertain),
        missing_count=len(validation_result.missing)
    )

    all_edges = validation_result.confident + validation_result.uncertain

    # Analyze by type
    for edge in all_edges:
        category = 'confident' if edge.confidence == InferenceConfidence.CONFIDENT else 'uncertain'
        report.by_type[edge.edge_type.value][category] += 1
        report.by_source[edge.source.value][category] += 1

    # Check for cycles
    cycles = check_for_cycles(all_edges)
    if cycles:
        for cycle in cycles:
            report.issues.append(f"CYCLE: {' -> '.join(cycle)}")
        report.recommendations.append("Review dependency cycles - may cause infinite loops")

    # Check for orphans
    no_incoming, no_outgoing = check_orphan_rungs(all_edges, all_rungs)

    # Entry rungs (no incoming) are expected for orientation
    unexpected_no_incoming = [r for r in no_incoming if not r.startswith('survey') and r not in ['questioning', 'death_avoidance']]
    if unexpected_no_incoming:
        report.issues.append(f"ORPHAN (no incoming): {unexpected_no_incoming}")
        report.recommendations.append("Review orphan rungs - may never be reached")

    # Terminal rungs (no outgoing) are expected for actions
    unexpected_no_outgoing = [r for r in no_outgoing if 'action' not in r.lower() and r not in ['death_avoidance']]
    if unexpected_no_outgoing:
        report.issues.append(f"ORPHAN (no outgoing): {unexpected_no_outgoing}")

    # Check for conflicts
    conflicts = check_contradicting_edges(all_edges)
    if conflicts:
        for conflict in conflicts:
            report.issues.append(f"CONFLICT: {conflict['source']} -> {conflict['target']}: {conflict['conflict_types']}")
        report.recommendations.append("Resolve conflicting edge types")

    # Analyze confidence distribution
    conf_dist = analyze_confidence_distribution(all_edges)
    if conf_dist.get('below_0.5', 0) > len(all_edges) * 0.3:
        report.recommendations.append(
            f"Many low-confidence edges ({conf_dist['below_0.5']}/{conf_dist['count']}). "
            "Consider adding more heuristic rules or runtime observations."
        )

    # Check missing edges
    if validation_result.missing:
        for missing in validation_result.missing:
            report.issues.append(
                f"MISSING: {missing['source']} -> {missing['target']} ({missing['expected_type']})"
            )
        report.recommendations.append("Investigate missing expected edges")

    return report


def print_report(report: ValidationReport) -> None:
    """Print validation report to console."""
    print("\n" + "=" * 70)
    print("EDGE VALIDATION REPORT")
    print("=" * 70)
    print(f"Generated: {report.timestamp.isoformat()}")
    print()

    # Summary
    print("SUMMARY:")
    print(f"  Total Edges: {report.total_edges}")
    print(f"  Confident:   {report.confident_count} (auto-accept)")
    print(f"  Uncertain:   {report.uncertain_count} (human review)")
    print(f"  Missing:     {report.missing_count} (investigate)")
    print()

    # By type
    print("BY EDGE TYPE:")
    for edge_type, counts in sorted(report.by_type.items()):
        total = sum(counts.values())
        print(f"  {edge_type:15s}: {total:4d} (confident: {counts.get('confident', 0)}, uncertain: {counts.get('uncertain', 0)})")
    print()

    # By source
    print("BY INFERENCE SOURCE:")
    for source, counts in sorted(report.by_source.items()):
        total = sum(counts.values())
        print(f"  {source:20s}: {total:4d}")
    print()

    # Issues
    if report.issues:
        print("ISSUES DETECTED:")
        for issue in report.issues:
            print(f"  [!] {issue}")
        print()

    # Recommendations
    if report.recommendations:
        print("RECOMMENDATIONS:")
        for rec in report.recommendations:
            print(f"  -> {rec}")
        print()

    print("=" * 70)


def export_validation_result(
    validation_result: EdgeValidationResult,
    filepath: str
) -> None:
    """Export validation result to JSON."""
    data = {
        'timestamp': datetime.now().isoformat(),
        'confident': [e.to_dict() for e in validation_result.confident],
        'uncertain': [e.to_dict() for e in validation_result.uncertain],
        'missing': validation_result.missing
    }

    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"Exported validation result to {filepath}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate inferred cognitive edges")
    parser.add_argument('--run-inference', action='store_true',
                       help='Run fresh inference before validation')
    parser.add_argument('--export', type=str,
                       help='Export validated edges to JSON file')
    parser.add_argument('--expected', type=str,
                       help='Load expected patterns from JSON')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')

    args = parser.parse_args()

    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='[%(levelname)s] %(message)s'
    )

    # Create engine
    engine = EdgeInferenceEngine()

    # Load rung classes
    try:
        import decision_rung_system
        rung_classes = load_rung_classes_from_module(decision_rung_system)
        print(f"Loaded {len(rung_classes)} rung classes")
    except ImportError as e:
        print(f"Error loading decision_rung_system: {e}")
        return 1

    # Analyze rungs
    count = engine.analyze_rungs(rung_classes)
    print(f"Analyzed {count} rungs")

    # Get all rung names
    all_rungs = [getattr(r, 'name', r.__name__.lower()) for r in rung_classes]

    # Run inference
    if args.run_inference:
        print("Running edge inference...")
        edges = engine.infer_all_edges()
        print(f"Inferred {len(edges)} edges")

    # Load expected patterns
    if args.expected:
        with open(args.expected, 'r') as f:
            expected_patterns = json.load(f)
    else:
        expected_patterns = build_expected_patterns()

    # Validate
    print("\nValidating edges...")
    validation_result = engine.validate_edges(expected_patterns)

    # Generate and print report
    report = generate_report(validation_result, engine, all_rungs)
    print_report(report)

    # Print slot dataflow summary
    print("\nSLOT DATAFLOW SUMMARY:")
    dataflow = engine.get_slot_dataflow()
    for slot_name, info in sorted(dataflow.items())[:20]:  # Top 20 slots
        writers = ', '.join(info['writers'][:3])
        readers = ', '.join(info['readers'][:3])
        print(f"  {slot_name:25s}: writers=[{writers}...] readers=[{readers}...]")
    if len(dataflow) > 20:
        print(f"  ... and {len(dataflow) - 20} more slots")

    # Export if requested
    if args.export:
        export_validation_result(validation_result, args.export)

    # Print stats
    print("\nENGINE STATISTICS:")
    stats = engine.get_stats()
    for key, value in stats.items():
        if isinstance(value, dict):
            print(f"  {key}:")
            for k, v in value.items():
                print(f"    {k}: {v}")
        else:
            print(f"  {key}: {value}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
