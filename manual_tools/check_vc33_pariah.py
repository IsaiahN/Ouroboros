"""Check VC33 pariah data."""
import sqlite3

conn = sqlite3.connect('core_data.db')
conn.row_factory = sqlite3.Row

# Check pariah tables
print('=== Pariah Tables ===')
tables = [t[0] for t in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%pariah%'").fetchall()]
print(f'Tables: {tables}')

for table in tables:
    try:
        # Try to find vc33 data
        r = conn.execute(f"SELECT * FROM {table} LIMIT 5").fetchall()
        if r:
            print(f'\n{table} sample:')
            for row in r[:2]:
                print(dict(row))
    except Exception as e:
        print(f'{table}: {e}')

# Also check viral packages that might have pariah info
print('\n=== Viral Pariah Packages for VC33 ===')
try:
    r = conn.execute("""
        SELECT * FROM viral_packages 
        WHERE game_type = 'vc33' AND is_pariah = 1
        ORDER BY created_at DESC
        LIMIT 10
    """).fetchall()
    print(f'Found {len(r)} pariah packages')
    for row in r:
        print(dict(row))
except Exception as e:
    print(f'Error: {e}')

conn.close()
