"""Check VC33 viral packages and action penalty sources."""
import sqlite3

conn = sqlite3.connect('core_data.db')
conn.row_factory = sqlite3.Row

# Check viral package tables
print('=== Tables with "viral" or "package" ===')
tables = [t[0] for t in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name LIKE '%viral%' OR name LIKE '%package%')").fetchall()]
print(f'Tables: {tables}')

# Check viral_knowledge_packages
print('\n=== Viral Knowledge Packages for VC33 ===')
try:
    r = conn.execute("""
        SELECT * FROM viral_knowledge_packages 
        WHERE game_id LIKE 'vc33%' 
        ORDER BY created_at DESC
        LIMIT 15
    """).fetchall()
    print(f'Found {len(r)} packages')
    for row in r:
        d = dict(row)
        print(f"\nPackage {d.get('package_id', '?')[:12]}:")
        print(f"  action_code: {d.get('action_code')}, is_pariah: {d.get('is_pariah')}")
        print(f"  level: {d.get('level_number')}, effectiveness: {d.get('effectiveness_score')}")
        print(f"  spread_count: {d.get('spread_count')}, adoptions: {d.get('successful_adoptions')}")
except Exception as e:
    print(f'Error: {e}')

# Check pariah_package_interactions
print('\n=== Pariah Package Interactions for VC33 ===')
try:
    r = conn.execute("""
        SELECT p.*, pa.pariah_name 
        FROM pariah_package_interactions p
        LEFT JOIN pariahs pa ON p.pariah_id = pa.pariah_id
        WHERE pa.source_game_id LIKE 'vc33%'
        LIMIT 10
    """).fetchall()
    print(f'Found {len(r)} interactions')
    for row in r:
        print(dict(row))
except Exception as e:
    print(f'Error: {e}')

# Check if there's a per-action penalty table
print('\n=== Action Penalty Sources ===')
tables = [t[0] for t in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name LIKE '%action%' OR name LIKE '%penalty%')").fetchall()]
print(f'Action-related tables: {tables}')

conn.close()
