"""Check VC33 viral information packages - the actual source of pariah penalties."""
import sqlite3

conn = sqlite3.connect('core_data.db')
conn.row_factory = sqlite3.Row

# Check viral_information_packages schema
print('=== viral_information_packages schema ===')
r = conn.execute("PRAGMA table_info(viral_information_packages)").fetchall()
for col in r:
    print(f"  {col['name']}: {col['type']}")

# Get VC33 viral packages
print('\n=== VC33 Viral Packages (last 20) ===')
r = conn.execute("""
    SELECT * FROM viral_information_packages 
    WHERE game_id LIKE 'vc33%'
    ORDER BY created_at DESC
    LIMIT 20
""").fetchall()
print(f'Found {len(r)} packages')
for row in r:
    d = dict(row)
    print(f"\nPkg {d.get('package_id', '?')[:12]}:")
    print(f"  action: {d.get('action_code')}, level: {d.get('level_number')}")
    print(f"  is_pariah: {d.get('is_pariah')}, effectiveness: {d.get('effectiveness_score')}")
    print(f"  infections: {d.get('infection_count')}, active: {d.get('is_active')}")
    print(f"  context: {d.get('context_description', '')[:80]}")

# Check action_effectiveness for ACTION6
print('\n=== Action Effectiveness for VC33 ACTION6 ===')
r = conn.execute("""
    SELECT * FROM action_effectiveness 
    WHERE game_id LIKE 'vc33%' AND action_code = 6
    ORDER BY level_number
    LIMIT 20
""").fetchall()
print(f'Found {len(r)} records')
for row in r:
    print(dict(row))

conn.close()
