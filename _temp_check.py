"""Temporary system state check - delete after use."""
import os
import sqlite3

db_path = 'core_data.db'
print(f"DB Size: {os.path.getsize(db_path) / 1024 / 1024:.1f} MB")

conn = sqlite3.connect(db_path)
c = conn.cursor()

# Critical tables
tables = [
    'game_results', 'agent_arc_performance', 'agent_game_diversity',
    'agent_meta_learning', 'winning_sequences', 'viral_information_packages',
    'resonance_patterns', 'level_mastery', 'collective_reasoning_sessions',
    'action_traces', 'system_logs', 'navigation_state_history',
    'sensation_learning_events', 'agent_operating_modes'
]

print("\n=== CRITICAL TABLE COUNTS ===")
for table in tables:
    try:
        count = c.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table}: {count:,} rows")
    except Exception as e:
        print(f"  {table}: MISSING")

# Total tables
total = c.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
print(f"\nTotal tables in DB: {total}")

# Latest generation info
print("\n=== GENERATION STATS ===")
try:
    gen = c.execute("SELECT MAX(generation) FROM game_results").fetchone()[0]
    if gen:
        print(f"Latest generation: {gen}")
        for g in range(max(1, gen - 4), gen + 1):
            row = c.execute(
                "SELECT COUNT(*), SUM(CASE WHEN levels_completed>0 THEN 1 ELSE 0 END), "
                "AVG(total_score), GROUP_CONCAT(DISTINCT game_type) "
                "FROM game_results WHERE generation=?", [g]
            ).fetchone()
            if row[0]:
                print(f"  Gen {g}: {row[0]} games, {row[1] or 0} wins, avg_score={row[2]:.2f}, types={row[3]}")
    else:
        print("No game results yet")
except Exception as e:
    print(f"Error: {e}")

# Check for winning sequences
print("\n=== WINNING KNOWLEDGE ===")
try:
    ws = c.execute("SELECT COUNT(*) FROM winning_sequences").fetchone()[0]
    print(f"Winning sequences: {ws}")
except:
    print("winning_sequences: MISSING")

try:
    vp = c.execute("SELECT COUNT(*) FROM viral_information_packages").fetchone()[0]
    print(f"Viral packages: {vp}")
except:
    print("viral_information_packages: MISSING")

# Check event bus / feedback
print("\n=== PIPELINE HEALTH INDICATORS ===")
try:
    recent_actions = c.execute(
        "SELECT COUNT(*) FROM action_traces WHERE generation >= ?",
        [max(1, (gen or 1) - 2)]
    ).fetchone()[0]
    print(f"Recent action traces (last 2 gens): {recent_actions}")
except:
    print("action_traces: not available")

try:
    recent_logs = c.execute(
        "SELECT COUNT(*) FROM system_logs WHERE generation >= ?",
        [max(1, (gen or 1) - 2)]
    ).fetchone()[0]
    print(f"Recent system logs (last 2 gens): {recent_logs}")
except:
    print("system_logs: not available")

# Check agents
print("\n=== AGENT STATUS ===")
try:
    agents = c.execute("SELECT COUNT(*) FROM agents WHERE is_active=1").fetchone()[0]
    print(f"Active agents: {agents}")
except:
    try:
        agents = c.execute("SELECT COUNT(*) FROM agents").fetchone()[0]
        print(f"Total agents: {agents}")
    except:
        print("agents table: MISSING")

conn.close()
