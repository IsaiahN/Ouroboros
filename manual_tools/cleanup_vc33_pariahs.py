"""Clean up false positive VC33 pariahs.

These pariahs have action sequences like [6,6,6...6] 100-800 times.
They were created when agents spammed ACTION6 without score changes,
but ACTION6 is actually the CORE mechanic for VC33 (all winning sequences use it).

This script deactivates these false positive pariahs.
"""
import sqlite3

conn = sqlite3.connect('core_data.db')
conn.row_factory = sqlite3.Row

print('=== Cleaning VC33 False Positive Pariahs ===')

# Find pariahs with long ACTION6 sequences from VC33
r = conn.execute("""
    SELECT pariah_id, pariah_name, action_sequence, source_game_id, is_active
    FROM pariahs
    WHERE source_game_id LIKE 'vc33%'
    AND action_sequence LIKE '[6%'
    AND LENGTH(action_sequence) > 50
""").fetchall()

print(f'Found {len(r)} pariahs with long ACTION6 sequences from VC33')

deactivated = 0
for row in r:
    d = dict(row)
    print(f"\n  {d['pariah_id']}: len={len(d['action_sequence'])}, active={d['is_active']}")
    
    if d['is_active'] == 1:
        # Deactivate this pariah
        conn.execute("""
            UPDATE pariahs SET is_active = 0, 
            deactivated_reason = 'False positive - ACTION6 is core mechanic for VC33'
            WHERE pariah_id = ?
        """, (d['pariah_id'],))
        deactivated += 1
        print(f"    -> Deactivated")

# Also deactivate awareness of these pariahs
if deactivated > 0:
    conn.execute("""
        UPDATE agent_pariah_awareness
        SET is_active = 0
        WHERE pariah_id IN (
            SELECT pariah_id FROM pariahs
            WHERE source_game_id LIKE 'vc33%'
            AND action_sequence LIKE '[6%'
            AND LENGTH(action_sequence) > 50
        )
    """)
    
conn.commit()
print(f'\nDeactivated {deactivated} false positive pariahs')

# Verify ACTION6 penalty is now reasonable
print('\n=== Verifying penalty reduction ===')

# Simulate penalty calculation for a vc33 agent
r = conn.execute("""
    SELECT 
        pa.agent_id,
        COUNT(*) as pariah_count,
        SUM(pa.awareness_level * pa.avoidance_priority * p.toxicity) as total_base_penalty
    FROM agent_pariah_awareness pa
    JOIN pariahs p ON pa.pariah_id = p.pariah_id
    WHERE p.source_game_id LIKE 'vc33%' 
    AND pa.is_active = 1 
    AND p.is_active = 1
    GROUP BY pa.agent_id
    LIMIT 5
""").fetchall()

if r:
    print(f'Remaining active VC33 pariah awareness:')
    for row in r:
        print(f"  Agent {row['agent_id'][:12]}: {row['pariah_count']} pariahs, base_penalty={row['total_base_penalty']:.2f}")
else:
    print('No active VC33 pariah awareness remaining - agents can use ACTION6 freely!')

conn.close()
print('\nDone!')
