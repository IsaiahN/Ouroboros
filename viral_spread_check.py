"""Check if viral spread tracking is working"""
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
from database_interface import DatabaseInterface

db = DatabaseInterface()
print("="*80)
print("VIRAL SPREAD TRACKING VERIFICATION")
print("="*80)

# Check 1: Viral spread in agent_discoveries
print("\n[1/4] Viral Spread in Agent Discoveries:")
viral = db.execute_query("""
    SELECT agent_id, sequence_id, times_used_by_others, success_rate_by_others
    FROM agent_discoveries
    WHERE times_used_by_others > 0
    ORDER BY times_used_by_others DESC
    LIMIT 10
""")
if viral:
    print(f"  ✅ {len(viral)} discoveries have viral spread!")
    for v in viral:
        print(f"    {v['agent_id'][:8]}: {v['times_used_by_others']} uses, {v['success_rate_by_others']:.1%} success")
else:
    print("  ❌ No viral spread yet")

# Check 2: Agent prestige
print("\n[2/4] Agent Prestige:")
prestige = db.execute_query("""
    SELECT agent_id, discovery_prestige, breeding_priority, sequence_discovery_count
    FROM agents WHERE discovery_prestige > 0
    ORDER BY discovery_prestige DESC LIMIT 5
""")
if prestige:
    print(f"  ✅ {len(prestige)} agents have prestige!")
    for p in prestige:
        print(f"    {p['agent_id'][:12]}: prestige={p['discovery_prestige']:.4f}, breeding={p['breeding_priority']:.2f}x")
else:
    print("  ❌ No prestige yet")

# Check 3: Validation attempts
print("\n[3/4] Sequence Validations:")
vals = db.execute_query("""
    SELECT COUNT(*) as count,
           COUNT(DISTINCT agent_id) as unique_agents,
           SUM(CASE WHEN validation_success = 1 THEN 1 ELSE 0 END) as successes
    FROM sequence_validation_attempts
""")
if vals and vals[0]['count'] > 0:
    v = vals[0]
    print(f"  ✅ {v['count']} validations by {v['unique_agents']} agents ({v['successes']} successful)")
else:
    print("  ❌ No validations yet")

# Check 4: Cross-agent usage
print("\n[4/4] Cross-Agent Sequence Usage:")
cross = db.execute_query("""
    SELECT sva.agent_id as user, ws.agent_id as discoverer, 
           sva.validation_success, sva.sequence_id
    FROM sequence_validation_attempts sva
    JOIN winning_sequences ws ON sva.sequence_id = ws.sequence_id
    WHERE sva.agent_id != ws.agent_id
    ORDER BY sva.validation_id DESC
    LIMIT 5
""")
if cross:
    print(f"  ✅ {len(cross)} cross-agent uses detected!")
    for c in cross:
        status = "✓" if c['validation_success'] else "✗"
        print(f"    {status} {c['user'][:8]} used {c['discoverer'][:8]}'s seq")
else:
    print("  ❌ No cross-agent usage (all self-use)")

print("\n" + "="*80)
if viral and prestige:
    print("✅ VIRAL SPREAD TRACKING IS WORKING!")
elif cross:
    print("⚠️  Cross-agent usage detected but not tracked - check logs")
else:
    print("❌ Need more game cycles for agents to use each other's sequences")
print("="*80)
