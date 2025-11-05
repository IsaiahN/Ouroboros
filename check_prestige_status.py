"""
Quick check of prestige system status
"""
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface

db = DatabaseInterface()

print("="*80)
print("PRESTIGE SYSTEM STATUS CHECK")
print("="*80)

# Check agent prestige values
print("\n[1/5] Agent Prestige Distribution:")
prestige_stats = db.execute_query("""
    SELECT 
        COUNT(*) as total_agents,
        COUNT(CASE WHEN discovery_prestige > 0 THEN 1 END) as agents_with_prestige,
        AVG(discovery_prestige) as avg_prestige,
        MAX(discovery_prestige) as max_prestige,
        AVG(breeding_priority) as avg_breeding,
        MAX(breeding_priority) as max_breeding,
        AVG(survival_protection) as avg_survival
    FROM agents 
    WHERE is_active = 1
""")

if prestige_stats:
    s = prestige_stats[0]
    print(f"  Total Active Agents: {s['total_agents']}")
    print(f"  Agents with Prestige > 0: {s['agents_with_prestige']}")
    print(f"  Avg Prestige: {s['avg_prestige']:.4f}")
    print(f"  Max Prestige: {s['max_prestige']:.4f}")
    print(f"  Avg Breeding Priority: {s['avg_breeding']:.4f}")
    print(f"  Max Breeding Priority: {s['max_breeding']:.4f}")
    print(f"  Avg Survival Protection: {s['avg_survival']:.4f}")

# Check agent_discoveries
print("\n[2/5] Agent Discoveries Tracked:")
discovery_stats = db.execute_query("""
    SELECT 
        COUNT(*) as total_discoveries,
        COUNT(DISTINCT agent_id) as agents_with_discoveries,
        AVG(times_used_by_others) as avg_viral_spread,
        AVG(prestige_contribution) as avg_prestige_contrib
    FROM agent_discoveries
""")

if discovery_stats:
    d = discovery_stats[0]
    print(f"  Total Discoveries: {d['total_discoveries']}")
    print(f"  Agents with Discoveries: {d['agents_with_discoveries']}")
    print(f"  Avg Viral Spread: {d['avg_viral_spread']:.2f}")
    print(f"  Avg Prestige Contribution: {d['avg_prestige_contrib']:.4f}")

# Check recent prestige logs
print("\n[3/5] Recent Prestige System Logs:")
try:
    logs = db.execute_query("""
        SELECT timestamp, level, message
        FROM system_logs 
        WHERE message LIKE '%prestige%'
        ORDER BY timestamp DESC 
        LIMIT 5
    """)
    
    if logs:
        for log in logs:
            print(f"  [{log['level']}] {log['timestamp']}: {log['message'][:100]}")
    else:
        print("  No prestige-related logs found")
except Exception as e:
    print(f"  Could not query logs: {e}")

# Check action economy
print("\n[4/5] Action Economy Status:")
economy_stats = db.execute_query("""
    SELECT 
        COUNT(*) as total_agents,
        AVG(action_allowance_per_level) as avg_allowance,
        MIN(action_allowance_per_level) as min_allowance,
        MAX(action_allowance_per_level) as max_allowance,
        AVG(action_budget_multiplier) as avg_multiplier
    FROM agents 
    WHERE is_active = 1
""")

if economy_stats:
    e = economy_stats[0]
    print(f"  Total Active Agents: {e['total_agents']}")
    print(f"  Avg Action Allowance/Level: {e['avg_allowance']:.2f}")
    print(f"  Min Allowance: {e['min_allowance']}")
    print(f"  Max Allowance: {e['max_allowance']}")
    print(f"  Avg Budget Multiplier: {e['avg_multiplier']:.4f}")
    
    if e['min_allowance'] != e['max_allowance']:
        print(f"  ✅ Per-agent budgets ARE varying (range: {e['min_allowance']}-{e['max_allowance']})")
    else:
        print(f"  ⚠️  All agents have same allowance ({e['avg_allowance']})")

# Check if sequences are being discovered and used
print("\n[5/5] Sequence Usage (Prestige Source):")
sequence_usage = db.execute_query("""
    SELECT 
        COUNT(*) as total_sequences,
        COUNT(DISTINCT agent_id) as agents_with_sequences,
        SUM(CASE WHEN is_recombination = 1 THEN 1 ELSE 0 END) as recombination_sequences
    FROM winning_sequences
""")

if sequence_usage:
    u = sequence_usage[0]
    print(f"  Total Sequences: {u['total_sequences']}")
    print(f"  Agents with Sequences: {u['agents_with_sequences']}")
    print(f"  Recombination Sequences: {u['recombination_sequences']}")

print("\n" + "="*80)
print("DIAGNOSIS:")
print("="*80)

if prestige_stats and prestige_stats[0]['agents_with_prestige'] == 0:
    print("⚠️  NO AGENTS HAVE PRESTIGE YET")
    print("")
    print("Possible reasons:")
    print("1. Prestige calculation is not running in evolution loop")
    print("2. No discoveries are being tracked in agent_discoveries table")
    print("3. Sequences exist but agents haven't used each other's discoveries yet")
    print("4. Prestige engine integration needs verification")
    print("")
    print("Next step: Check if prestige_engine.update_all_agent_prestige() is being called")
elif prestige_stats and prestige_stats[0]['agents_with_prestige'] > 0:
    print("✅ PRESTIGE SYSTEM IS ACTIVE!")
    print(f"   {prestige_stats[0]['agents_with_prestige']} agents have earned prestige")

if economy_stats and economy_stats[0]['min_allowance'] != economy_stats[0]['max_allowance']:
    print("✅ ECONOMIC SYSTEM IS ACTIVE!")
    print(f"   Action budgets vary from {economy_stats[0]['min_allowance']} to {economy_stats[0]['max_allowance']}")
else:
    print("⚠️  Economic system may not be calculating per-agent budgets")

print("="*80)
