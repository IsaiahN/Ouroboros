"""Clean up agent awareness of inactive pariahs."""
import sqlite3

conn = sqlite3.connect('core_data.db')
conn.row_factory = sqlite3.Row

print('=== Checking Agent Awareness of Inactive Pariahs ===')

# Find awareness records pointing to inactive pariahs
r = conn.execute("""
    SELECT COUNT(*) as cnt
    FROM agent_pariah_awareness pa
    JOIN pariahs p ON pa.pariah_id = p.pariah_id
    WHERE pa.is_active = 1 AND p.is_active = 0
""").fetchone()

print(f'Found {r["cnt"]} awareness records pointing to inactive pariahs')

if r['cnt'] > 0:
    # Deactivate awareness of inactive pariahs
    conn.execute("""
        UPDATE agent_pariah_awareness
        SET is_active = 0
        WHERE pariah_id IN (
            SELECT pariah_id FROM pariahs WHERE is_active = 0
        )
    """)
    conn.commit()
    print(f'Deactivated {r["cnt"]} stale awareness records')

# Check VC33 specific issues
print('\n=== VC33 Pariah Awareness Status ===')
r = conn.execute("""
    SELECT pa.agent_id, pa.pariah_id, pa.is_active as awareness_active, 
           p.is_active as pariah_active, p.action_sequence
    FROM agent_pariah_awareness pa
    JOIN pariahs p ON pa.pariah_id = p.pariah_id
    WHERE p.source_game_id LIKE 'vc33%'
    AND pa.is_active = 1
    LIMIT 10
""").fetchall()

print(f'Active VC33 pariah awareness records: {len(r)}')
for row in r:
    print(f"  Agent {row['agent_id'][:12]} -> Pariah (active={row['pariah_active']})")

# Final verification
print('\n=== Final Verification ===')
r = conn.execute("""
    SELECT COUNT(*) as cnt
    FROM agent_pariah_awareness pa
    JOIN pariahs p ON pa.pariah_id = p.pariah_id
    WHERE pa.is_active = 1 
    AND p.is_active = 1
    AND p.source_game_id LIKE 'vc33%'
""").fetchone()

print(f'ACTIVE VC33 pariah awareness: {r["cnt"]}')

if r['cnt'] == 0:
    print('[OK] No active VC33 pariah awareness - agents can use ACTION6!')
else:
    print('[WARN] Still have active VC33 pariah awareness')
    
conn.close()
