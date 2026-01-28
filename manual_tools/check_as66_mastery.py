"""Quick check of as66 mastery and sequences."""
import sqlite3

conn = sqlite3.connect('core_data.db')
cursor = conn.cursor()

# Check schema
cursor.execute("PRAGMA table_info(level_mastery)")
cols = [c[1] for c in cursor.fetchall()]
print(f"level_mastery columns: {cols}")

# Check mastery
cursor.execute("SELECT * FROM level_mastery WHERE game_type = 'as66' ORDER BY level_number")
rows = cursor.fetchall()
print(f'\n=== Mastery Levels for as66 ({len(rows)} rows) ===')
for m in rows:
    print(f"  {m}")

print()
cursor.execute("""
    SELECT level_number, COUNT(*) as cnt, MIN(total_actions), MAX(total_actions) 
    FROM winning_sequences 
    WHERE game_id LIKE 'as66%' AND is_active = 1 
    GROUP BY level_number 
    ORDER BY level_number
""")
print('=== Active Sequences by Level ===')
for s in cursor.fetchall():
    print(f'  L{s[0]}: {s[1]} sequences ({s[2]}-{s[3]} actions)')

print()
cursor.execute("""
    SELECT level_number, COUNT(*) as cnt 
    FROM winning_sequences 
    WHERE game_id LIKE 'as66%' AND level_number >= 4 AND is_active = 1 
    GROUP BY level_number
""")
l4plus = cursor.fetchall()
total = sum(s[1] for s in l4plus) if l4plus else 0
print(f'=== Level 4+ Active Sequences: {total} total ===')
for s in l4plus:
    print(f'  L{s[0]}: {s[1]} sequences')

if total == 0:
    print()
    print('=== Checking INACTIVE L4+ sequences ===')
    cursor.execute("""
        SELECT level_number, COUNT(*) as cnt, flag_reason
        FROM winning_sequences 
        WHERE game_id LIKE 'as66%' AND level_number >= 4 AND is_active = 0 
        GROUP BY level_number, flag_reason
    """)
    for s in cursor.fetchall():
        print(f'  L{s[0]}: {s[1]} inactive (reason: {s[2]})')

conn.close()
