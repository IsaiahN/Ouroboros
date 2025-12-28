"""Check VC33 viral information packages - corrected query."""
import sqlite3

conn = sqlite3.connect('core_data.db')
conn.row_factory = sqlite3.Row

# Get VC33 viral packages using correct columns
print('=== VC33 Viral Packages ===')
r = conn.execute("""
    SELECT * FROM viral_information_packages 
    WHERE frontier_game_type = 'vc33' OR source_sequence_id LIKE 'vc33%'
    ORDER BY discovery_generation DESC
    LIMIT 20
""").fetchall()
print(f'Found {len(r)} packages')
for row in r:
    d = dict(row)
    print(f"\nPkg {d.get('package_id', '?')[:12]}:")
    print(f"  action_seq: {d.get('action_sequence')}")
    print(f"  type: {d.get('package_type')}, level: {d.get('frontier_level')}")
    print(f"  success_rate: {d.get('success_rate')}, virulence: {d.get('virulence')}")
    print(f"  active: {d.get('is_active')}, obsolete: {d.get('obsolescence_score')}")

# Check action_effectiveness schema
print('\n=== action_effectiveness schema ===')
r = conn.execute("PRAGMA table_info(action_effectiveness)").fetchall()
for col in r:
    print(f"  {col['name']}: {col['type']}")

# Check action_effectiveness for VC33
print('\n=== Action Effectiveness for VC33 ===')
r = conn.execute("""
    SELECT * FROM action_effectiveness 
    WHERE game_type = 'vc33' OR game_id LIKE 'vc33%'
    LIMIT 20
""").fetchall()
print(f'Found {len(r)} records')
for row in r:
    print(dict(row))

# Check agent_viral_infections for pariah packages
print('\n=== Agent Viral Infections (pariah-like) ===')
r = conn.execute("""
    SELECT vi.*, vp.action_sequence, vp.package_type
    FROM agent_viral_infections vi
    JOIN viral_information_packages vp ON vi.package_id = vp.package_id
    WHERE vp.frontier_game_type = 'vc33'
    LIMIT 10
""").fetchall()
print(f'Found {len(r)} infections')
for row in r:
    print(dict(row))

conn.close()
