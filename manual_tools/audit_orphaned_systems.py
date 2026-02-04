"""
Comprehensive Audit of Orphaned Systems
========================================

This script identifies:
1. Engines registered but never accessed in decision rungs
2. Rungs that read context keys nobody sets
3. Database tables that exist but aren't written to
4. Methods in engines that are never called
5. Features documented but not implemented

Run: python manual_tools/audit_orphaned_systems.py
"""

import os
import re
import sqlite3
from collections import defaultdict
from pathlib import Path

# Change to project root
os.chdir(Path(__file__).parent.parent)


def audit_engine_usage():
    """Check which registered engines are used in decision rungs."""
    print("\n" + "=" * 70)
    print("1. ENGINE REGISTRY USAGE AUDIT")
    print("=" * 70)

    # Get all engines from registry
    with open('engines/registry.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract engine names from ENGINE_CONFIGS
    engines = re.findall(r"'([a-z_]+)':\s*EngineConfig", content)
    print(f"\nTotal registered engines: {len(engines)}")

    # Check usage in decision_rung_system.py
    with open('decision_rung_system.py', 'r', encoding='utf-8') as f:
        drs_content = f.read()

    # Check usage in evolution_runner.py
    with open('evolution_runner.py', 'r', encoding='utf-8') as f:
        er_content = f.read()

    # Check usage in core_gameplay.py
    with open('core_gameplay.py', 'r', encoding='utf-8') as f:
        cg_content = f.read()

    used_in_drs = []
    used_in_er = []
    used_in_cg = []
    not_used = []

    for e in engines:
        pattern = r'self\.engines\.' + e + r'[^a-z_]'
        pattern2 = r'engines\.' + e + r'[^a-z_]'
        pattern3 = r'\.' + e + r'[^a-z_]'

        drs_matches = len(re.findall(pattern, drs_content))
        er_matches = len(re.findall(pattern2, er_content)) + len(re.findall(pattern3, er_content))
        cg_matches = len(re.findall(pattern2, cg_content)) + len(re.findall(pattern3, cg_content))

        if drs_matches:
            used_in_drs.append((e, drs_matches))
        if er_matches:
            used_in_er.append((e, er_matches))
        if cg_matches:
            used_in_cg.append((e, cg_matches))
        if not drs_matches and not er_matches and not cg_matches:
            not_used.append(e)

    print(f"\n[USED in decision_rung_system.py] ({len(used_in_drs)} engines):")
    for e, count in sorted(used_in_drs):
        print(f"  [OK] {e}: {count} references")

    print(f"\n[USED in evolution_runner.py] ({len(used_in_er)} engines):")
    for e, count in sorted(used_in_er):
        print(f"  [OK] {e}: {count} references")

    print(f"\n[ORPHANED - NOT USED ANYWHERE] ({len(not_used)} engines):")
    for e in sorted(not_used):
        print(f"  [ORPHAN] {e}")

    return not_used


def audit_context_keys():
    """Check for context keys that are read but never set."""
    print("\n" + "=" * 70)
    print("2. CONTEXT KEY ORPHAN AUDIT")
    print("=" * 70)

    with open('decision_rung_system.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all context.get() calls
    context_reads = re.findall(r"context\.get\(['\"]([^'\"]+)['\"]", content)
    context_reads += re.findall(r"context\[['\"]([^'\"]+)['\"]\]", content)

    # Find all context[key] = assignments
    context_writes = re.findall(r"context\[['\"]([^'\"]+)['\"]\]\s*=", content)

    # Also check evolution_runner.py for context dictionary literals
    with open('evolution_runner.py', 'r', encoding='utf-8') as f:
        er_content = f.read()
    # Find 'key': value patterns in context = { ... } dictionaries
    context_writes += re.findall(r"['\"]([a-z_]+)['\"]:\s*[^,}]+", er_content)

    # Also check context_builder.py for what fields are defined
    with open('context_builder.py', 'r', encoding='utf-8') as f:
        cb_content = f.read()

    # Extract dataclass fields
    defined_fields = re.findall(r"^\s+([a-z_]+):\s*", cb_content, re.MULTILINE)

    read_set = set(context_reads)
    write_set = set(context_writes)
    defined_set = set(defined_fields)

    # Keys that are read but never written/defined
    orphan_reads = read_set - write_set - defined_set

    print(f"\nContext keys READ: {len(read_set)}")
    print(f"Context keys WRITTEN: {len(write_set)}")
    print(f"Context keys DEFINED in context_builder: {len(defined_set)}")

    print(f"\n[ORPHAN READS - keys read but never set] ({len(orphan_reads)}):")
    for key in sorted(orphan_reads):
        # Find which rungs read this key
        rungs = re.findall(rf"class\s+(\w+Rung).*?context\.get\(['\"]" + key + r"['\"]", content, re.DOTALL)
        if rungs:
            unique_rungs = list(set(rungs))[:3]
            print(f"  [ORPHAN] '{key}' read by: {', '.join(unique_rungs)}")
        else:
            print(f"  [ORPHAN] '{key}'")

    return orphan_reads


def audit_database_tables():
    """Check for database tables that aren't written to."""
    print("\n" + "=" * 70)
    print("3. DATABASE TABLE WRITE AUDIT")
    print("=" * 70)

    # Get all tables from schema
    with open('complete_database_schema.sql', 'r', encoding='utf-8') as f:
        schema = f.read()

    tables = re.findall(r'CREATE TABLE\s+(?:IF NOT EXISTS\s+)?(\w+)', schema)
    print(f"\nTotal tables in schema: {len(tables)}")

    # Search for INSERT INTO statements across all Python files
    insert_patterns = defaultdict(list)

    python_files = list(Path('.').rglob('*.py'))
    python_files = [f for f in python_files if 'deprecated' not in str(f) and '.venv' not in str(f)]

    for py_file in python_files:
        try:
            with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            for table in tables:
                # Check for INSERT INTO table
                if re.search(rf'INSERT\s+INTO\s+{table}', content, re.IGNORECASE):
                    insert_patterns[table].append(str(py_file))
                # Also check for UPDATE table
                if re.search(rf'UPDATE\s+{table}', content, re.IGNORECASE):
                    insert_patterns[table].append(str(py_file) + ' (UPDATE)')
        except Exception:
            pass

    written_tables = set(insert_patterns.keys())
    orphan_tables = set(tables) - written_tables

    print(f"\n[TABLES WITH WRITES] ({len(written_tables)}):")
    for table in sorted(written_tables)[:20]:  # Show first 20
        files = list(set([f.split('\\')[-1].split('/')[- 1] for f in insert_patterns[table]]))[:3]
        print(f"  [OK] {table}: {', '.join(files)}")
    if len(written_tables) > 20:
        print(f"  ... and {len(written_tables) - 20} more")

    print(f"\n[ORPHAN TABLES - no INSERT/UPDATE found] ({len(orphan_tables)}):")
    for table in sorted(orphan_tables):
        print(f"  [ORPHAN] {table}")

    return orphan_tables


def audit_rung_methods():
    """Check for rungs that access engines with methods that don't exist."""
    print("\n" + "=" * 70)
    print("4. RUNG METHOD CALL AUDIT")
    print("=" * 70)

    with open('decision_rung_system.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all engine method calls: self.engines.X.method()
    method_calls = re.findall(r'self\.engines\.(\w+)\.(\w+)\(', content)

    # Group by engine
    engine_methods = defaultdict(set)
    for engine, method in method_calls:
        engine_methods[engine].add(method)

    print(f"\nEngine method calls found:")
    for engine in sorted(engine_methods.keys()):
        methods = sorted(engine_methods[engine])
        print(f"  {engine}: {', '.join(methods)}")

    # Now verify these methods exist
    print("\n[VERIFYING METHOD EXISTENCE]:")

    # Map engine names to their module files
    engine_files = {
        'self_model': 'engines/self_model/cognitive_core.py',
        'visual_analyzer': 'engines/perception/visual_analyzer.py',
        'scientific_method_engine': 'engines/reasoning/scientific_method_engine.py',
        'i_thread': 'engines/consciousness/i_thread.py',
        'sensation_engine': 'engines/consciousness/sensation_engine.py',
        'near_miss_analyzer': 'engines/memory/near_miss_analyzer.py',
        'resonance_detector': 'engines/social/resonance_detector.py',
        'primitive_suggester': 'engines/social/primitive_suggester.py',
        'subgoal_planner': 'engines/planning/subgoal_planner.py',
        'abstraction_engine': 'engines/planning/sequence_abstraction.py',
        'replay_learning_engine': 'engines/planning/replay_learning_engine.py',
        'action6_behavior': 'engines/self_model/action6_behavior.py',
        'hypothesis_system': 'engines/reasoning/hypothesis_system.py',
        'regulatory_engine': 'engines/regulation/regulatory_signal_engine.py',
        'frustration_detector': 'engines/regulation/frustration_detector.py',
    }

    missing_methods = []
    for engine, methods in engine_methods.items():
        if engine in engine_files:
            try:
                with open(engine_files[engine], 'r', encoding='utf-8') as f:
                    engine_content = f.read()

                for method in methods:
                    # Check if def method( exists
                    if not re.search(rf'def\s+{method}\s*\(', engine_content):
                        missing_methods.append((engine, method))
                        print(f"  [MISSING] {engine}.{method}() - not found in {engine_files[engine]}")
            except FileNotFoundError:
                print(f"  [FILE NOT FOUND] {engine_files[engine]}")

    if not missing_methods:
        print("  [OK] All called methods appear to exist")

    return missing_methods


def audit_action6_systems():
    """Specific audit for ACTION6/click systems."""
    print("\n" + "=" * 70)
    print("5. ACTION6/CLICK SYSTEM AUDIT")
    print("=" * 70)

    # Key files for ACTION6
    key_files = [
        'engines/self_model/action6_behavior.py',
        'engines/perception/visual_analyzer.py',
        'decision_rung_system.py',
        'evolution_runner.py',
        'game_loop.py',
    ]

    print("\n[ACTION6 COORDINATE FLOW]:")

    # Check Action6BehaviorEngine methods
    with open('engines/self_model/action6_behavior.py', 'r', encoding='utf-8') as f:
        a6_content = f.read()

    # Extract public methods
    a6_methods = re.findall(r'def\s+([a-z_]+)\s*\(self', a6_content)
    print(f"\n  Action6BehaviorEngine methods ({len(a6_methods)}):")
    for m in a6_methods[:15]:
        print(f"    - {m}()")
    if len(a6_methods) > 15:
        print(f"    ... and {len(a6_methods) - 15} more")

    # Check if these are called anywhere
    all_code = ""
    for f in key_files:
        try:
            with open(f, 'r', encoding='utf-8') as file:
                all_code += file.read()
        except FileNotFoundError:
            pass

    print("\n  [USAGE CHECK]:")
    critical_methods = [
        'get_untried_objects_for_frontier',
        'get_click_targets_for_level',
        'get_pseudo_button_behavior',
        'save_pseudo_button_behavior',
        'classify_pseudo_button_effects',
    ]

    for method in critical_methods:
        if method in all_code:
            print(f"    [OK] {method}() is called somewhere")
        else:
            print(f"    [ORPHAN] {method}() is NEVER called!")

    # Check GridExplorationRung
    print("\n  [GRID EXPLORATION RUNG CHECK]:")
    with open('decision_rung_system.py', 'r', encoding='utf-8') as f:
        drs = f.read()

    if 'class GridExplorationRung' in drs:
        print("    [OK] GridExplorationRung exists")
        if 'get_grid_exploration_targets' in drs:
            print("    [OK] Calls get_grid_exploration_targets()")
        else:
            print("    [ORPHAN] Does NOT call get_grid_exploration_targets()")

    # Check if visual_analyzer.get_grid_exploration_targets exists
    with open('engines/perception/visual_analyzer.py', 'r', encoding='utf-8') as f:
        va_content = f.read()

    if 'def get_grid_exploration_targets' in va_content:
        print("    [OK] visual_analyzer.get_grid_exploration_targets() exists")
    else:
        print("    [MISSING] visual_analyzer.get_grid_exploration_targets() missing!")


def audit_evolution_engine_usage():
    """Check if evolution-level engines are connected."""
    print("\n" + "=" * 70)
    print("6. EVOLUTION-LEVEL ENGINE INTEGRATION AUDIT")
    print("=" * 70)

    evolution_engines = [
        ('EvolutionaryEngine', 'evolutionary_engine.py'),
        ('ViralPackageEngine', 'engines/social/viral_package_engine.py'),
        ('NetworkIntelligenceEngine', 'network_intelligence_engine.py'),
        ('HorizontalTransferEngine', 'horizontal_transfer_engine.py'),
        ('MetaLearningCurriculum', 'meta_learning_curriculum.py'),
        ('AgentLifecycleManager', 'agent_lifecycle_manager.py'),
        ('CollectiveReasoningEngine', 'collective_reasoning_engine.py'),
        ('ConceptDiscoveryEngine', 'concept_discovery_engine.py'),
        ('GamesAsTeachersEngine', 'games_as_teachers'),
    ]

    with open('evolution_runner.py', 'r', encoding='utf-8') as f:
        er_content = f.read()

    print("\n[EVOLUTION ENGINE INTEGRATION]:")
    for engine, file_hint in evolution_engines:
        if engine in er_content:
            # Check if instantiated
            if f'self.{engine.lower()}' in er_content or f'{engine}(' in er_content:
                print(f"  [OK] {engine} - imported and instantiated")
            else:
                print(f"  [PARTIAL] {engine} - imported but not instantiated")
        else:
            print(f"  [ORPHAN] {engine} - NOT in evolution_runner.py")


def generate_audit_report():
    """Generate comprehensive audit report."""
    print("\n" + "=" * 70)
    print("COMPREHENSIVE ORPHANED SYSTEMS AUDIT")
    print("=" * 70)
    print("Date: February 3, 2026")
    print("Purpose: Identify disconnected/orphaned functionality")

    orphan_engines = audit_engine_usage()
    orphan_context = audit_context_keys()
    orphan_tables = audit_database_tables()
    missing_methods = audit_rung_methods()
    audit_action6_systems()
    audit_evolution_engine_usage()

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"\n  Orphaned engines: {len(orphan_engines)}")
    print(f"  Orphaned context keys: {len(orphan_context)}")
    print(f"  Orphaned database tables: {len(orphan_tables)}")
    print(f"  Missing engine methods: {len(missing_methods)}")

    print("\n[CRITICAL ISSUES TO FIX]:")

    critical = []
    if 'action6_behavior' in orphan_engines:
        critical.append("- action6_behavior engine not used (critical for click games)")
    if 'click_behavior' in orphan_engines:
        critical.append("- click_behavior engine not used")
    if 'control_tracker' in orphan_engines:
        critical.append("- control_tracker engine not used (self model)")
    if 'world_model_states' in orphan_tables:
        critical.append("- world_model_states table never written to")

    for c in critical:
        print(f"  {c}")

    if not critical:
        print("  No critical issues found!")

    return {
        'orphan_engines': orphan_engines,
        'orphan_context': orphan_context,
        'orphan_tables': orphan_tables,
        'missing_methods': missing_methods,
    }


if __name__ == '__main__':
    generate_audit_report()
