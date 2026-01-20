import sqlite3

db = sqlite3.connect('core_data.db')
db.row_factory = sqlite3.Row

print('='*70)
print('LS20 KEY DISCOVERIES (What agents learned about the game)')
print('='*70)

# Get unique discoveries
discoveries = db.execute('''
    SELECT DISTINCT 
        substr(message, instr(message, '[DISCOVERY]'), 120) as discovery
    FROM system_logs
    WHERE message LIKE '%ls20%' AND message LIKE '%DISCOVERY%'
    ORDER BY timestamp DESC
    LIMIT 100
''').fetchall()

print('\n--- OBJECT CONTROL DISCOVERIES ---')
for d in discoveries:
    print(f"  {d['discovery']}")

# Get action reasoning logs with correct columns
print('\n' + '='*70)
print('ACTION REASONING LOGS (How agents decided what to do)')
print('='*70)

reasoning = db.execute('''
    SELECT log_id, agent_id, game_id, level, action_number, 
           action_taken, cods_operator, reasoning_summary, action_source
    FROM action_reasoning_logs
    WHERE game_id LIKE '%ls20%'
    ORDER BY log_id DESC
    LIMIT 200
''').fetchall()

for r in reasoning:
    print(f"\nAgent {r['agent_id'][:15]} | Level {r['level']} | Action #{r['action_number']}")
    print(f"  Took: {r['action_taken']} | Source: {r['action_source']}")
    if r['cods_operator']:
        print(f"  CODS operator: {r['cods_operator']}")
    if r['reasoning_summary']:
        summary = r['reasoning_summary'][:100] if r['reasoning_summary'] else ''
        print(f"  Reasoning: {summary}")

if not reasoning:
    print('No action reasoning logs for ls20')

# Get CODS operator usage
print('\n' + '='*70)
print('CODS OPERATORS USED ON LS20')
print('='*70)

cods = db.execute('''
    SELECT cods_operator, COUNT(*) as times_used, 
           SUM(CASE WHEN action_source = 'cods' THEN 1 ELSE 0 END) as cods_source
    FROM action_reasoning_logs
    WHERE game_id LIKE '%ls20%' AND cods_operator IS NOT NULL
    GROUP BY cods_operator
    ORDER BY times_used DESC
    LIMIT 50
''').fetchall()

for c in cods:
    print(f"  {c['cods_operator']}: used {c['times_used']}x (source={c['cods_source']}x)")

if not cods:
    print('No CODS operators logged for ls20')

# Check what the network knows
print('\n' + '='*70)
print('NETWORK KNOWLEDGE ABOUT LS20')
print('='*70)

# Control hypotheses
hyps = db.execute('''
    SELECT controlled_color, action_response_map, reliability_score,
           validation_attempts, validated_by_win
    FROM network_object_control_hypotheses
    WHERE game_type LIKE '%ls20%' AND action_response_map != '{}'
    ORDER BY reliability_score DESC
    LIMIT 50
''').fetchall()

print('\n--- Object Control Hypotheses ---')
for h in hyps:
    print(f"  Color {h['controlled_color']}: reliability={h['reliability_score']:.2f}, validated={h['validated_by_win']}")
    arm = str(h['action_response_map'])[:80]
    print(f"    Actions: {arm}")

if not hyps:
    print('  No non-empty control hypotheses')
