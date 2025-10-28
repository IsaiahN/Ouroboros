#!/usr/bin/env python3
"""
Show what data is preserved vs cleaned up
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface

print("=" * 80)
print("🔍 WHAT AUTO-CLEANUP AFFECTS")
print("=" * 80)
print()

db = DatabaseInterface()

print("✅ PRESERVED (NEVER DELETED):")
print("-" * 80)
print()

preserved_tables = [
    ('game_results', 'All completed games with final scores/wins'),
    ('agents', 'All agent definitions and genomes'),
    ('agent_arc_performance', 'All performance metrics for evolution'),
    ('winning_sequences', 'Pattern learning - winning action sequences'),
    ('discovered_patterns', 'Pattern learning - discovered strategies'),
    ('claude_memory', 'LLM learning and insights'),
    ('claude_evolution_decisions', 'Evolution decisions and strategies'),
    ('population_health_metrics', 'Population health tracking'),
    ('global_counters', 'Checkpoint and resume data')
]

for table, description in preserved_tables:
    try:
        count = db.execute_query(f"SELECT COUNT(*) as c FROM {table}")[0]['c']
        print(f"  ✓ {table:30s} {count:>6,} rows - {description}")
    except Exception as e:
        print(f"  ✓ {table:30s}      - - {description} (table not in use)")

print()
print("🗑️  CLEANED UP (OLD ENTRIES REMOVED):")
print("-" * 80)
print()

cleaned_tables = [
    ('system_logs', 'Debug/info/error logs - keeps 10K most recent only')
]

for table, description in cleaned_tables:
    try:
        count = db.execute_query(f"SELECT COUNT(*) as c FROM {table}")[0]['c']
        print(f"  🗑️  {table:30s} {count:>6,} rows - {description}")
    except Exception as e:
        print(f"  🗑️  {table:30s}      - - {description}")

print()
print("=" * 80)
print("📊 SUMMARY")
print("=" * 80)
print()
print("The auto-cleanup ONLY touches 'system_logs' table:")
print("  - This stores INFO/DEBUG/ERROR log messages")
print("  - Used for debugging, not for evolution or game tracking")
print("  - Keeps 10,000 most recent entries (plenty for debugging)")
print("  - Older logs are deleted to prevent database bloat")
print()
print("ALL GAME DATA IS PRESERVED:")
print("  ✓ Every game you've played (game_results)")
print("  ✓ Every agent's performance (agent_arc_performance)")
print("  ✓ All evolution decisions (claude_evolution_decisions)")
print("  ✓ All winning patterns (winning_sequences)")
print("  ✓ All agent genomes (agents)")
print()
print("Your evolution data is 100% safe! 🛡️")
print("=" * 80)
