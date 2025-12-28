"""Find exactly where the 6.26 penalty comes from for VC33 ACTION6."""
import sqlite3
import json

conn = sqlite3.connect('core_data.db')
conn.row_factory = sqlite3.Row

# Check ALL active pariahs for vc33
print('=== Active Pariahs for VC33 ===')
r = conn.execute("""
    SELECT * FROM pariahs 
    WHERE source_game_id LIKE 'vc33%' AND is_active = 1
""").fetchall()
print(f'Found {len(r)} active pariahs')
for row in r:
    d = dict(row)
    print(f"\n{d['pariah_id']}:")
    print(f"  sequence: {d['action_sequence']}")
    print(f"  toxicity: {d['toxicity']}, level: {d['source_level_number']}")

# Check agent_pariah_awareness for current agents
print('\n=== Agent Pariah Awareness for VC33 pariahs ===')
r = conn.execute("""
    SELECT pa.*, p.action_sequence, p.toxicity, p.source_level_number
    FROM agent_pariah_awareness pa
    JOIN pariahs p ON pa.pariah_id = p.pariah_id
    WHERE p.source_game_id LIKE 'vc33%' AND pa.is_active = 1
""").fetchall()
print(f'Found {len(r)} active awareness records')
for row in r:
    d = dict(row)
    awareness = d['awareness_level']
    priority = d['avoidance_priority']
    toxicity = d['toxicity']
    base_penalty = awareness * priority * toxicity
    # Parse action sequence
    actions = json.loads(d['action_sequence'])
    print(f"\nAgent {d['agent_id'][:12]} -> Pariah {d['pariah_id'][:12]}:")
    print(f"  awareness: {awareness}, priority: {priority}, toxicity: {toxicity}")
    print(f"  base_penalty = {awareness} * {priority} * {toxicity} = {base_penalty:.2f}")
    print(f"  actions: {actions}, level: {d['source_level_number']}")
    # Count ACTION6 entries
    action6_count = actions.count(6)
    print(f"  ACTION6 in sequence: {action6_count} times")
    print(f"  Total ACTION6 penalty contribution: {base_penalty * action6_count:.2f}")

# Check if there are many pariahs with ACTION6
print('\n=== All Pariahs containing ACTION6 ===')
r = conn.execute("""
    SELECT pariah_id, action_sequence, toxicity, source_game_id, source_level_number, is_active
    FROM pariahs
    WHERE action_sequence LIKE '%6%'
    LIMIT 20
""").fetchall()
print(f'Found {len(r)} pariahs with action 6')
for row in r:
    d = dict(row)
    actions = json.loads(d['action_sequence'])
    action6_count = actions.count(6)
    print(f"  {d['pariah_id'][:12]}: {actions} (x{action6_count} 6s), game={d['source_game_id'][:8]}, active={d['is_active']}")

conn.close()
