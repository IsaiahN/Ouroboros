"""Comprehensive performance metrics query."""
import sqlite3
from collections import defaultdict

conn = sqlite3.connect('core_data.db')
cur = conn.cursor()

print('='*100)
print('PERFORMANCE METRICS FROM ACTUAL GAMEPLAY - UPDATED January 27, 2026')
print('='*100)

# Get generation range
cur.execute('SELECT MIN(generation), MAX(generation) FROM agents WHERE is_active=1')
gen_range = cur.fetchone()
print(f'\nGeneration Range: {gen_range[0]} - {gen_range[1]}')

# 1. LEVEL REACHED AND MAX SCORE BY GAME TYPE
print('\n' + '='*100)
print('1. LEVEL REACHED AND SCORE BY GAME TYPE')
print('='*100)

cur.execute('''
    SELECT 
        SUBSTR(game_id, 1, 4) as game_type,
        COUNT(*) as games_played,
        AVG(final_score) as avg_score,
        MAX(final_score) as max_score,
        AVG(level_completions) as avg_levels,
        MAX(level_completions) as max_levels,
        SUM(CASE WHEN win_detected = 1 THEN 1 ELSE 0 END) as wins,
        AVG(total_actions) as avg_actions,
        SUM(CASE WHEN final_score > 0 THEN 1 ELSE 0 END) as positive_scores
    FROM game_results
    GROUP BY game_type
    ORDER BY max_score DESC, avg_score DESC
''')

print(f'\n{"Game":<8} {"Games":<10} {"Avg Score":<12} {"Max Score":<12} {"Avg Lvl":<10} {"Max Lvl":<10} {"Wins":<8} {"Pos Scores":<12} {"Avg Actions":<12}')
print('-'*104)
for row in cur.fetchall():
    game, games, avg_sc, max_sc, avg_lvl, max_lvl, wins, avg_act, pos = row
    print(f'{game:<8} {games:<10} {avg_sc or 0:<12.3f} {max_sc or 0:<12.3f} {avg_lvl or 0:<10.2f} {max_lvl or 0:<10} {wins:<8} {pos:<12} {avg_act or 0:<12.1f}')

# 2. Q-FIELD EQUIVALENT METRICS: Hypothesis/Control Confidence
print('\n' + '='*100)
print('2. Q-FIELD METRICS BY GAME TYPE (from network_object_control_hypotheses)')
print('='*100)

cur.execute('''
    SELECT 
        game_type,
        COUNT(*) as total_hypotheses,
        SUM(CASE WHEN is_active=1 THEN 1 ELSE 0 END) as active_hypotheses,
        AVG(reliability_score) as avg_reliability,
        MAX(reliability_score) as max_reliability,
        AVG(validation_attempts) as avg_validations,
        SUM(CASE WHEN validated_by_win=1 THEN 1 ELSE 0 END) as win_validated
    FROM network_object_control_hypotheses
    GROUP BY game_type
    ORDER BY game_type
''')

print(f'\n{"Game":<8} {"Total Hyp":<12} {"Active":<10} {"Avg Reliab":<12} {"Max Reliab":<12} {"Avg Valid":<12} {"Win Valid":<12}')
print('-'*80)
for row in cur.fetchall():
    game, total, active, avg_rel, max_rel, avg_val, win_val = row
    print(f'{game:<8} {total:<12} {active:<10} {avg_rel or 0:<12.3f} {max_rel or 0:<12.3f} {avg_val or 0:<12.2f} {win_val:<12}')

# 3. SELF-MODEL / CONTROL IDENTIFICATION
print('\n' + '='*100)
print('3. SELF-MODEL / OBJECT CONTROL IDENTIFICATION')
print('='*100)

cur.execute('PRAGMA table_info(self_object_identity)')
cols = [c[1] for c in cur.fetchall()]
print(f'self_object_identity columns: {cols}')

cur.execute('SELECT COUNT(*) FROM self_object_identity')
count = cur.fetchone()[0]
print(f'Total self-identifications: {count}')

if count > 0:
    cur.execute('''
        SELECT SUBSTR(game_id, 1, 4) as game_type, COUNT(*) as identifications, AVG(confidence) as avg_conf
        FROM self_object_identity
        GROUP BY game_type
        ORDER BY game_type
    ''')
    print(f'\n{"Game":<8} {"Identifications":<18} {"Avg Confidence":<15}')
    print('-'*45)
    for row in cur.fetchall():
        print(f'{row[0]:<8} {row[1]:<18} {row[2] or 0:<15.3f}')

# 4. ACTION EFFECTIVENESS (Q2 equivalent - action confidence)
print('\n' + '='*100)
print('4. ACTION EFFECTIVENESS BY GAME TYPE (Q2 equivalent)')
print('='*100)

cur.execute('''
    SELECT 
        SUBSTR(game_id, 1, 4) as game_type,
        COUNT(*) as total_records,
        AVG(success_rate) as avg_success_rate,
        MAX(success_rate) as max_success_rate,
        AVG(avg_score_impact) as avg_score_impact
    FROM action_effectiveness
    GROUP BY game_type
    ORDER BY avg_success_rate DESC
''')

results = cur.fetchall()
if results:
    print(f'\n{"Game":<8} {"Records":<12} {"Avg Success":<15} {"Max Success":<15} {"Avg Score Impact":<18}')
    print('-'*70)
    for row in results:
        game, records, avg_succ, max_succ, avg_impact = row
        print(f'{game:<8} {records:<12} {avg_succ or 0:<15.3f} {max_succ or 0:<15.3f} {avg_impact or 0:<18.3f}')
else:
    print('No action_effectiveness data found.')

# 5. AGENT ROLE PERFORMANCE (w_A/w_B equivalent - trust self)
print('\n' + '='*100)
print('5. AGENT ROLE PERFORMANCE')
print('='*100)

cur.execute('''
    SELECT 
        preferred_role,
        COUNT(*) as agent_count,
        AVG(avg_score_per_game) as avg_score,
        MAX(best_single_game_score) as max_score,
        AVG(discovery_prestige) as avg_prestige,
        AVG(self_network_bias) as avg_self_trust
    FROM agents
    WHERE is_active = 1
    GROUP BY preferred_role
    ORDER BY preferred_role
''')

results = cur.fetchall()
if results:
    print(f'\n{"Role":<15} {"Count":<10} {"Avg Score":<15} {"Max Score":<15} {"Avg Prestige":<15} {"Self Trust (w)":<15}')
    print('-'*90)
    for row in results:
        role, count, avg_sc, max_sc, avg_pres, self_trust = row
        print(f'{role or "Unknown":<15} {count:<10} {avg_sc or 0:<15.4f} {max_sc or 0:<15.4f} {avg_pres or 0:<15.4f} {self_trust or 0.5:<15.3f}')

# 6. Check agent_operating_modes for w_A/w_B data
print('\n' + '='*100)
print('6. AGENT OPERATING MODES (Trust Self / w_A)')
print('='*100)

cur.execute('PRAGMA table_info(agent_operating_modes)')
cols = [c[1] for c in cur.fetchall()]
print(f'agent_operating_modes columns: {cols}')

cur.execute('SELECT COUNT(*) FROM agent_operating_modes')
print(f'Total records: {cur.fetchone()[0]}')

if 'trust_self' in cols or 'w_a' in cols:
    trust_col = 'trust_self' if 'trust_self' in cols else 'w_a'
    cur.execute(f'''
        SELECT 
            operating_mode,
            COUNT(*) as count,
            AVG({trust_col}) as avg_trust
        FROM agent_operating_modes
        GROUP BY operating_mode
    ''')
    for row in cur.fetchall():
        print(f'  {row}')

# 7. SALIENCE / ATTENTION DATA (Q3 equivalent)
print('\n' + '='*100)
print('7. ATTENTION/SALIENCE DATA (Q3 equivalent)')
print('='*100)

cur.execute('''
    SELECT 
        game_type,
        COUNT(*) as observations,
        COUNT(DISTINCT attention_pattern) as unique_patterns
    FROM attention_windows
    GROUP BY game_type
    ORDER BY observations DESC
''')

results = cur.fetchall()
if results:
    print(f'\n{"Game":<8} {"Observations":<15} {"Unique Patterns":<18}')
    print('-'*45)
    for row in results:
        print(f'{row[0]:<8} {row[1]:<15} {row[2]:<18}')
else:
    print('No attention_windows data found.')

# 8. COMPREHENSIVE SUMMARY TABLE (matching original format)
print('\n' + '='*100)
print('8. SUMMARY TABLE BY GAME TYPE (Matching Original Format)')
print('='*100)

# Get hypothesis reliability as Q1 confidence proxy
cur.execute('''
    SELECT game_type, AVG(reliability_score) as q1_confidence
    FROM network_object_control_hypotheses 
    WHERE is_active=1
    GROUP BY game_type
''')
q1_data = {row[0]: row[1] for row in cur.fetchall()}

# Get action effectiveness as Q2 confidence proxy
cur.execute('''
    SELECT SUBSTR(game_id, 1, 4) as game_type, AVG(success_rate) as q2_confidence
    FROM action_effectiveness
    GROUP BY game_type
''')
q2_data = {row[0]: row[1] or 0 for row in cur.fetchall()}

# Get game results
cur.execute('''
    SELECT 
        SUBSTR(game_id, 1, 4) as game_type,
        MAX(level_completions) as max_level,
        MAX(final_score) as max_score
    FROM game_results
    GROUP BY game_type
''')
game_data = {row[0]: (row[1], row[2]) for row in cur.fetchall()}

print(f'\n{"Game":<8} {"Max Level":<12} {"Max Score":<12} {"Q1 (Hyp Conf)":<15} {"Q2 (Act Eff)":<15}')
print('-'*70)
for game in sorted(game_data.keys()):
    max_lvl, max_sc = game_data[game]
    q1 = q1_data.get(game, 0) or 0
    q2 = q2_data.get(game, 0) or 0
    print(f'{game:<8} {max_lvl or 0:<12} {max_sc or 0:<12.2f} {q1:<15.3f} {q2:<15.3f}')

conn.close()

print('\n' + '='*100)
print('Query completed successfully.')
print('='*100)

conn.close()
