import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

"""Audit CODS and self-model status across all game types."""
import sqlite3

conn = sqlite3.connect('core_data.db')
conn.row_factory = sqlite3.Row

print("=" * 70)
print("CODS AND SELF-MODEL AUDIT")
print("=" * 70)

print("\n=== CODS COMPOSED OPERATORS STATUS ===")
ops = conn.execute('''
    SELECT operator_id, name, status, success_rate, times_tested 
    FROM composed_operators 
    WHERE status != 'deprecated' 
    ORDER BY success_rate DESC LIMIT 20
''').fetchall()
if ops:
    for o in ops:
        rate = o['success_rate'] or 0
        print(f"  {o['name']}: status={o['status']}, success_rate={rate:.1%}, tests={o['times_tested']}")
else:
    print("  [EMPTY] No active composed operators")

print("\n=== CODS OPERATOR TEST RESULTS (recent) ===")
try:
    tests = conn.execute('''
        SELECT operator_id, game_id, success, execution_time_ms, tested_at 
        FROM cods_operator_test_results 
        ORDER BY tested_at DESC LIMIT 10
    ''').fetchall()
    if tests:
        for t in tests:
            print(f"  {t['game_id']}: success={t['success']}, time={t['execution_time_ms']:.1f}ms")
    else:
        print("  [EMPTY] No test results found")
except sqlite3.OperationalError:
    print("  [TABLE NOT FOUND] cods_operator_test_results")

print("\n=== OBJECT SELECTION STATE (by game_type) ===")
sel = conn.execute('''
    SELECT game_type, COUNT(*) as cnt, 
           SUM(is_selectable) as selectable, 
           SUM(is_moveable) as moveable, 
           SUM(is_button) as button 
    FROM object_selection_state 
    GROUP BY game_type
''').fetchall()
if sel:
    for s in sel:
        print(f"  {s['game_type']}: {s['cnt']} objects, selectable={s['selectable']}, moveable={s['moveable']}, button={s['button']}")
else:
    print("  [EMPTY] No object selection state data")

print("\n=== NETWORK OBJECT CONTROL HYPOTHESES ===")
hyp = conn.execute('''
    SELECT game_type, level_number, reliability_score, validation_attempts, validated_by_win 
    FROM network_object_control_hypotheses 
    WHERE is_active = 1 
    ORDER BY reliability_score DESC LIMIT 10
''').fetchall()
if hyp:
    for h in hyp:
        print(f"  {h['game_type']} L{h['level_number']}: reliability={h['reliability_score']:.2f}, attempts={h['validation_attempts']}, won={h['validated_by_win']}")
else:
    print("  [EMPTY] No network control hypotheses")

print("\n=== COLLISION EFFECTS (learned patterns) ===")
coll = conn.execute('''
    SELECT game_type, level_number, controlled_object_color, target_object_color, effect_type, occurrence_count
    FROM collision_effects
    ORDER BY occurrence_count DESC LIMIT 10
''').fetchall()
if coll:
    for c in coll:
        print(f"  {c['game_type']} L{c['level_number']}: color{c['controlled_object_color']} + color{c['target_object_color']} -> {c['effect_type']} ({c['occurrence_count']}x)")
else:
    print("  [EMPTY] No collision effects learned")

print("\n=== ACTION5 BEHAVIOR MAP ===")
act5 = conn.execute('''
    SELECT game_type, level_number, behavior_type, effect_description, confidence
    FROM action5_behavior_map
    ORDER BY confidence DESC LIMIT 10
''').fetchall()
if act5:
    for a in act5:
        print(f"  {a['game_type']} L{a['level_number']}: {a['behavior_type']} ({a['confidence']:.0%})")
else:
    print("  [EMPTY] No ACTION5 behaviors mapped")

print("\n=== PSEUDO BUTTON BEHAVIOR (ACTION6 click targets) ===")
btn = conn.execute('''
    SELECT game_type, level_number, region_x, region_y, movement_direction, produces_action
    FROM pseudo_button_behavior
    ORDER BY confidence DESC LIMIT 10
''').fetchall()
if btn:
    for b in btn:
        print(f"  {b['game_type']} L{b['level_number']} ({b['region_x']},{b['region_y']}): {b['produces_action']} / dir={b['movement_direction']}")
else:
    print("  [EMPTY] No pseudo button behaviors mapped")

print("\n=== GAMEPLAY DATA BY GAME TYPE ===")
for game_type in ['ft09', 'sp80', 'as66', 'lp85', 'ls20', 'vc33']:
    games = conn.execute('''
        SELECT game_id, final_score, total_actions, win_achieved, level_progressions
        FROM agent_arc_performance
        WHERE game_id LIKE ?
        ORDER BY final_score DESC
        LIMIT 3
    ''', (f'{game_type}%',)).fetchall()
    
    if games:
        print(f"\n  {game_type.upper()}:")
        for g in games:
            print(f"    {g['game_id']}: score={g['final_score']}, actions={g['total_actions']}, won={g['win_achieved']}, levels={g['level_progressions']}")
    else:
        print(f"\n  {game_type.upper()}: [No gameplay data]")

print("\n=== AGENT REASONING PAYLOADS (recent) ===")
# Check if there's a reasoning_payload column anywhere
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
reasoning_found = False
for t in tables:
    try:
        cols = conn.execute(f"PRAGMA table_info({t['name']})").fetchall()
        for c in cols:
            if 'reason' in c['name'].lower() or 'hypothesis' in c['name'].lower():
                reasoning_found = True
                print(f"  Found reasoning column: {t['name']}.{c['name']}")
    except:
        pass

if not reasoning_found:
    print("  [WARNING] No reasoning_payload columns found in schema!")

conn.close()
print("\n[OK] Audit complete")
