#!/usr/bin/env python3
"""
Dependency Analysis Tool for BitterTruth-AI
Uses pydeps to generate dependency graphs and analyze architecture.

Requires: pip install pydeps
Requires: Graphviz installed (https://graphviz.org/download/)

Usage:
    python analyze_dependencies.py --full          # Full system graph
    python analyze_dependencies.py --cycles        # Show circular imports
    python analyze_dependencies.py --core          # Core gameplay dependencies
    python analyze_dependencies.py --reasoning     # Reasoning system focus
    python analyze_dependencies.py --orphans       # Find orphaned modules
"""

import subprocess
import sys
import os
from pathlib import Path

# Key module groups for focused analysis
REASONING_MODULES = [
    "core_gameplay",
    "agent_self_model",
    "persona_runtime",
    "seed_primitives",
    "cods_engine",
    "concept_discovery_engine",
    "rule_induction_engine",
    "scientific_method_engine",
]

CONSCIOUSNESS_MODULES = [
    "agent_self_model",
    "persona_runtime",
    "agent_operating_mode_system",
    "emotional_gameplay_mixin",
    "sensation_learning",
]

NETWORK_MODULES = [
    "network_intelligence_engine",
    "network_knowledge_synthesis",
    "horizontal_transfer_engine",
    "viral_package_manager",
    "prestige_engine",
]


def check_graphviz():
    """Check if Graphviz is installed."""
    try:
        # Refresh PATH to pick up recently installed tools
        import os
        env = os.environ.copy()
        result = subprocess.run(["dot", "-V"], capture_output=True, text=True, env=env, shell=True)
        return result.returncode == 0
    except FileNotFoundError:
        print("[ERROR] Graphviz not found!")
        print()
        print("Install Graphviz:")
        print("  1. Download: https://graphviz.org/download/")
        print("  2. Or: winget install graphviz")
        print("  3. Or: choco install graphviz")
        print()
        print("After installing, restart your terminal.")
        return False


def run_pydeps(args, output_name):
    """Run pydeps with given arguments."""
    cmd = [sys.executable, "-m", "pydeps"] + args
    print(f"[CMD] {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    if result.returncode != 0:
        print(f"[ERROR] {result.stderr}")
        return False
    print(f"[OK] Generated: {output_name}")
    return True


def analyze_full_system():
    """Generate full dependency graph."""
    print("\n=== Full System Dependency Graph ===")
    run_pydeps([
        ".",
        "-o", "deps_full_system.svg",
        "-T", "svg",
        "--noshow",
        "--max-bacon", "0",  # No limit on depth
        "--cluster",
        "--rankdir", "TB",  # Top to bottom
    ], "deps_full_system.svg")


def analyze_cycles():
    """Find circular imports."""
    print("\n=== Circular Import Analysis ===")
    result = subprocess.run([
        "python", "-m", "pydeps",
        ".",
        "--show-cycles",
        "--no-output",
    ], capture_output=True, text=True)
    
    if "No cycles found" in result.stdout or not result.stdout.strip():
        print("[OK] No circular imports detected")
    else:
        print("[WARNING] Circular imports found:")
        print(result.stdout)
        # Also generate visual
        run_pydeps([
            ".",
            "-o", "deps_cycles.svg",
            "-T", "svg",
            "--noshow",
            "--show-cycles",
        ], "deps_cycles.svg")


def analyze_core_gameplay():
    """Analyze core_gameplay.py dependencies."""
    print("\n=== Core Gameplay Dependencies ===")
    run_pydeps([
        "core_gameplay.py",
        "-o", "deps_core_gameplay.svg",
        "-T", "svg",
        "--noshow",
        "--max-bacon", "2",
        "--reverse",  # Show what imports core_gameplay
    ], "deps_core_gameplay.svg")


def analyze_reasoning_system():
    """Analyze reasoning/consciousness modules."""
    print("\n=== Reasoning System Dependencies ===")
    
    # Check which modules exist
    existing = [m for m in REASONING_MODULES if Path(f"{m}.py").exists()]
    
    for module in existing[:3]:  # Limit to avoid cluttering
        run_pydeps([
            f"{module}.py",
            "-o", f"deps_{module}.svg",
            "-T", "svg",
            "--noshow",
            "--max-bacon", "2",
        ], f"deps_{module}.svg")


def find_orphaned_modules():
    """Find modules that aren't imported by anything."""
    print("\n=== Orphaned Module Analysis ===")
    
    # Get all Python files
    all_py_files = set(p.stem for p in Path(".").glob("*.py") 
                       if not p.name.startswith("__"))
    
    # Get all imports by scanning files
    imported_modules = set()
    for py_file in Path(".").glob("*.py"):
        try:
            content = py_file.read_text(encoding='utf-8', errors='ignore')
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('import '):
                    # import module_name
                    parts = line.split()
                    if len(parts) >= 2:
                        mod = parts[1].split('.')[0]
                        imported_modules.add(mod)
                elif line.startswith('from '):
                    # from module_name import ...
                    parts = line.split()
                    if len(parts) >= 2:
                        mod = parts[1].split('.')[0]
                        imported_modules.add(mod)
        except Exception as e:
            pass
    
    # Find orphans (in project but never imported)
    orphans = all_py_files - imported_modules
    
    # Filter out known entry points
    entry_points = {
        "run_evolution", "autonomous_evolution_runner", 
        "safe_cleanup", "diagnose_reasoning", "analyze_dependencies",
        "check_bugs", "quick_check", "revive_agents",
        "automated_assessment_runner", "fix_sequences",
        "check_sequences", "check_all_sequences", "check_game_ids",
        "reactivate_sequences", "reactivate_best_sequences",
        "cleanup_temp_files", "audit_cods", "evolution_with_parasites",
        "pycache_guard", "theory_alignment_checker",
        "prestige_parasite_detector", "abstraction_schema",
    }
    
    true_orphans = orphans - entry_points
    
    if true_orphans:
        print(f"[WARNING] Potentially orphaned modules ({len(true_orphans)}):")
        for orphan in sorted(true_orphans):
            print(f"  - {orphan}.py")
    else:
        print("[OK] No orphaned modules detected")
    
    print(f"\n[INFO] Entry points not checked: {len(entry_points)}")
    print(f"[INFO] Total modules: {len(all_py_files)}")
    print(f"[INFO] Imported modules: {len(imported_modules)}")


def show_dependency_stats():
    """Show import statistics."""
    print("\n=== Dependency Statistics ===")
    
    stats = {}
    for py_file in Path(".").glob("*.py"):
        if py_file.name.startswith("__"):
            continue
        
        try:
            content = py_file.read_text(encoding='utf-8', errors='ignore')
            import_count = 0
            local_imports = 0
            
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('import ') or line.startswith('from '):
                    import_count += 1
                    # Check if it's a local import
                    parts = line.split()
                    if len(parts) >= 2:
                        mod = parts[1].split('.')[0]
                        if Path(f"{mod}.py").exists():
                            local_imports += 1
            
            stats[py_file.stem] = {
                'total': import_count,
                'local': local_imports,
                'external': import_count - local_imports,
            }
        except Exception:
            pass
    
    # Sort by local imports (most connected)
    sorted_stats = sorted(stats.items(), key=lambda x: x[1]['local'], reverse=True)
    
    print("\nTop 15 Most Connected Modules (by local imports):")
    print("-" * 50)
    for name, data in sorted_stats[:15]:
        print(f"  {name:40} local:{data['local']:3} external:{data['external']:3}")
    
    print("\nModules with ZERO local imports (isolated):")
    print("-" * 50)
    isolated = [(n, d) for n, d in sorted_stats if d['local'] == 0]
    for name, data in isolated[:10]:
        print(f"  {name}.py")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Analyze BitterTruth-AI dependencies")
    parser.add_argument("--full", action="store_true", help="Full system graph")
    parser.add_argument("--cycles", action="store_true", help="Find circular imports")
    parser.add_argument("--core", action="store_true", help="Core gameplay focus")
    parser.add_argument("--reasoning", action="store_true", help="Reasoning system focus")
    parser.add_argument("--orphans", action="store_true", help="Find orphaned modules")
    parser.add_argument("--stats", action="store_true", help="Show dependency statistics")
    parser.add_argument("--all", action="store_true", help="Run all analyses")
    
    args = parser.parse_args()
    
    # Default to stats if no args
    if not any(vars(args).values()):
        args.stats = True
        args.orphans = True
    
    print("=" * 60)
    print("BitterTruth-AI Dependency Analyzer")
    print("=" * 60)
    
    # Check for graphviz for graph operations
    needs_graphviz = args.full or args.cycles or args.core or args.reasoning or args.all
    if needs_graphviz and not check_graphviz():
        print("\n[INFO] Running non-graphviz analyses only...")
        args.full = args.cycles = args.core = args.reasoning = False
    
    if args.stats or args.all:
        show_dependency_stats()
    
    if args.orphans or args.all:
        find_orphaned_modules()
    
    if args.cycles or args.all:
        analyze_cycles()
    
    if args.full or args.all:
        analyze_full_system()
    
    if args.core or args.all:
        analyze_core_gameplay()
    
    if args.reasoning or args.all:
        analyze_reasoning_system()
    
    print("\n" + "=" * 60)
    print("Analysis complete!")
    if needs_graphviz and check_graphviz():
        print("SVG files generated - open in browser to view")
    print("=" * 60)


if __name__ == "__main__":
    main()
