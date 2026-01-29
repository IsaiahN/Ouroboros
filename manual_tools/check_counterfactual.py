"""Check if counterfactual_learnings table should be kept or discarded."""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'core_data.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()

print("=== COUNTERFACTUAL LEARNINGS TABLE ANALYSIS ===\n")

# Check what tables exist with "lesson" in name
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
all_tables = [r[0] for r in c.fetchall()]
lesson_tables = [t for t in all_tables if 'lesson' in t.lower() or 'counterfactual' in t.lower()]
print(f"Tables with 'lesson' or 'counterfactual': {lesson_tables}")

# Check counterfactual_learnings stats
c.execute("""
    SELECT 
        COUNT(*) as total,
        MIN(learned_at) as first,
        MAX(learned_at) as last,
        SUM(times_applied) as times_applied,
        COUNT(DISTINCT learning_type) as unique_types,
        COUNT(DISTINCT agent_id) as unique_agents
    FROM counterfactual_learnings
""")
stats = c.fetchone()
print(f"\ncounterfactual_learnings stats:")
print(f"  Total records: {stats[0]}")
print(f"  Date range: {stats[1]} to {stats[2]}")
print(f"  Times applied: {stats[3]}")
print(f"  Unique types: {stats[4]}")
print(f"  Unique agents: {stats[5]}")

# Check if lessons_learned table exists
if 'lessons_learned' in all_tables:
    c.execute("SELECT COUNT(*), MAX(learned_at), SUM(times_retrieved) FROM lessons_learned")
    lesson_stats = c.fetchone()
    print(f"\nlessons_learned table (replacement):")
    print(f"  Total: {lesson_stats[0]}, Last: {lesson_stats[1]}, Retrieved: {lesson_stats[2]}")
else:
    print("\nlessons_learned table does NOT exist")

# Check if any code reads from counterfactual_learnings
import subprocess
result = subprocess.run(
    ['grep', '-r', 'SELECT.*FROM.*counterfactual_learnings', '--include=*.py', '.'],
    capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__))
)
print(f"\nCode that reads counterfactual_learnings:")
if result.stdout.strip():
    print(result.stdout)
else:
    print("  NONE - table is orphaned (no code reads from it)")

print("\n=== RECOMMENDATION ===")
if stats[3] == 0:  # times_applied == 0
    print("DISCARD: Data was never used and old system was deprecated on Jan 17, 2026")
    print(f"  -> Would free up space from {stats[0]:,} records")
else:
    print("KEEP: Data has been applied {stats[3]} times")
