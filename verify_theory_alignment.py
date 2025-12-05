"""
Verify AGI Unified Theory alignment - Check if key systems are actively working.
"""
import sqlite3

conn = sqlite3.connect('core_data.db')
conn.row_factory = sqlite3.Row

print("=" * 60)
print("VERIFICATION: AGI UNIFIED THEORY ALIGNMENT")
print("=" * 60)

# Check self_network_bias distribution (Two-Streams)
print("\n=== 1. SELF/NETWORK BIAS DISTRIBUTION (Two-Streams) ===")
biases = conn.execute('''
    SELECT 
        CASE 
            WHEN self_network_bias IS NULL THEN 'NULL'
            WHEN self_network_bias < 0.3 THEN 'Network-trusting (<0.3)'
            WHEN self_network_bias < 0.5 THEN 'Leaning network (0.3-0.5)'
            WHEN self_network_bias = 0.5 THEN 'Default (0.5)'
            WHEN self_network_bias < 0.7 THEN 'Leaning self (0.5-0.7)'
            ELSE 'Self-trusting (>0.7)'
        END as bias_category,
        COUNT(*) as count
    FROM agents
    WHERE is_active = 1
    GROUP BY bias_category
''').fetchall()

for b in biases:
    print(f"  {b['bias_category']}: {b['count']} agents")

# Check if biases are being updated (not all default)
bias_stats = conn.execute('''
    SELECT 
        MIN(self_network_bias) as min_bias,
        MAX(self_network_bias) as max_bias,
        AVG(self_network_bias) as avg_bias,
        COUNT(DISTINCT ROUND(self_network_bias, 2)) as unique_values
    FROM agents
    WHERE is_active = 1 AND self_network_bias IS NOT NULL
''').fetchone()

print(f"\n  Bias range: {bias_stats['min_bias']:.3f} to {bias_stats['max_bias']:.3f}")
print(f"  Average bias: {bias_stats['avg_bias']:.3f}")
print(f"  Unique values: {bias_stats['unique_values']}")
if bias_stats['unique_values'] > 1:
    print("  [OK] Biases are being personalized")
else:
    print("  [WARN] All biases are the same - update_meta_bias may not be running")

# Check preferred_role distribution  
print("\n=== 2. ROLE DISTRIBUTION (Cognitive Division of Labor) ===")
roles = conn.execute('''
    SELECT COALESCE(preferred_role, 'NULL') as role, COUNT(*) as cnt
    FROM agents
    WHERE is_active = 1
    GROUP BY preferred_role
''').fetchall()
for r in roles:
    print(f"  {r['role']}: {r['cnt']} agents")

null_count = sum(1 for r in roles if r['role'] == 'NULL')
if null_count > 0:
    print(f"  [WARN] {null_count} agents have no preferred_role")

# Check agent_operating_modes (recent)
print("\n=== 3. AGENT OPERATING MODES (Recent 5 Generations) ===")
modes = conn.execute('''
    SELECT operating_mode, COUNT(*) as cnt
    FROM agent_operating_modes
    WHERE generation >= (SELECT MAX(generation) - 5 FROM agent_operating_modes)
    GROUP BY operating_mode
''').fetchall()
for m in modes:
    print(f"  {m['operating_mode']}: {m['cnt']} mode assignments")

if not modes:
    print("  [WARN] No recent operating mode assignments")

# Check sensation_learning_events (Emotional Intelligence)
print("\n=== 4. SENSATION LEARNING (Emotional Intelligence) ===")
events = conn.execute('''
    SELECT COUNT(*) as total,
           SUM(CASE WHEN reward_received > 0 THEN 1 ELSE 0 END) as positive,
           SUM(CASE WHEN reward_received < 0 THEN 1 ELSE 0 END) as negative,
           COUNT(DISTINCT aligned_with_stream) as stream_types
    FROM sensation_learning_events
''').fetchone()
print(f"  Total events: {events['total']}")
print(f"  Positive (rewards): {events['positive'] or 0}")
print(f"  Negative (punishments): {events['negative'] or 0}")
print(f"  Stream alignment types: {events['stream_types']}")

if events['total'] > 0:
    print("  [OK] Sensation learning is active")
else:
    print("  [WARN] No sensation learning events")

# Check navigation_state distribution (Q2 Reward/Punishment)
print("\n=== 5. NAVIGATION STATE (Q2: Reward/Punishment) ===")
nav_states = conn.execute('''
    SELECT 
        CASE 
            WHEN navigation_state < -0.5 THEN 'Very negative (<-0.5)'
            WHEN navigation_state < 0 THEN 'Negative (-0.5 to 0)'
            WHEN navigation_state = 0 THEN 'Neutral (0)'
            WHEN navigation_state < 0.5 THEN 'Positive (0 to 0.5)'
            ELSE 'Very positive (>0.5)'
        END as state_category,
        COUNT(*) as count
    FROM agents
    WHERE is_active = 1 AND navigation_state IS NOT NULL
    GROUP BY state_category
''').fetchall()
for s in nav_states:
    print(f"  {s['state_category']}: {s['count']} agents")

# Check learned_rules (Q4: Cross-Context Abstraction)
print("\n=== 6. LEARNED RULES (Q4: Cross-Context Rules) ===")
rules = conn.execute('''
    SELECT COUNT(*) as cnt, 
           AVG(confidence) as avg_conf,
           SUM(success_count) as total_success,
           SUM(failure_count) as total_fail
    FROM learned_rules
''').fetchone()
print(f"  Total rules: {rules['cnt']}")
if rules['cnt'] > 0:
    print(f"  Average confidence: {rules['avg_conf']:.3f}")
    print(f"  Success validations: {rules['total_success'] or 0}")
    print(f"  Failure validations: {rules['total_fail'] or 0}")
    print("  [OK] Rule abstraction is working")
else:
    print("  [WARN] No learned rules - rule induction may not be active")

# Check viral_information_packages (Viral Exchange Principle)
print("\n=== 7. VIRAL PACKAGES (Horizontal Transfer) ===")
viral = conn.execute('''
    SELECT COUNT(*) as cnt,
           SUM(total_infections) as total_infections,
           AVG(success_rate) as avg_success
    FROM viral_information_packages
    WHERE is_active = 1
''').fetchone()
print(f"  Active packages: {viral['cnt']}")
print(f"  Total infections: {viral['total_infections'] or 0}")
if viral['avg_success']:
    print(f"  Average success rate: {viral['avg_success']:.3f}")

if viral['total_infections'] and viral['total_infections'] > 0:
    print("  [OK] Viral packages are spreading")
else:
    print("  [INFO] Packages exist but no infections yet")

# Check agent_role_performance (Role Self-Determination)
print("\n=== 8. ROLE FIT SCORES (Self-Determination) ===")
role_perf = conn.execute('''
    SELECT role, 
           COUNT(DISTINCT agent_id) as agents,
           AVG(role_fit_score) as avg_fit,
           SUM(games_played) as total_games
    FROM agent_role_performance
    GROUP BY role
''').fetchall()
for rp in role_perf:
    print(f"  {rp['role']}: {rp['agents']} agents, avg fit={rp['avg_fit']:.3f}, {rp['total_games']} games")

if not role_perf:
    print("  [WARN] No role performance data - update_role_fit_after_game not running")

# Check level_progressions_detected (our fix!)
print("\n=== 9. LEVEL PROGRESSIONS (Our Fix) ===")
progressions = conn.execute('''
    SELECT 
        SUM(level_progressions_detected) as total_progressions,
        COUNT(*) as total_agents,
        SUM(CASE WHEN level_progressions_detected > 0 THEN 1 ELSE 0 END) as agents_with_progress
    FROM agents
    WHERE is_active = 1
''').fetchone()
print(f"  Total progressions recorded: {progressions['total_progressions'] or 0}")
print(f"  Agents with level progressions: {progressions['agents_with_progress'] or 0}/{progressions['total_agents']}")

if (progressions['total_progressions'] or 0) == 0:
    print("  [INFO] Zero progressions - run evolution to test the fix")
else:
    print("  [OK] Level progressions being tracked")

conn.close()

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
