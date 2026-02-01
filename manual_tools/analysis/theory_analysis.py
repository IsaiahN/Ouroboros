#!/usr/bin/env python3
"""Comprehensive theory alignment analysis"""
import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import sqlite3

conn = sqlite3.connect('core_data.db')
conn.row_factory = sqlite3.Row

print('='*70)
print('COMPREHENSIVE THEORY ALIGNMENT ANALYSIS')
print('='*70)

# 1. Two-Stream Consciousness
print('\n1. TWO-STREAM CONSCIOUSNESS')
print('   Theory: Private Memory (Stream A) + Network Wisdom (Stream B)')
try:
    osm = conn.execute('SELECT COUNT(*) FROM object_sensation_mappings').fetchone()[0]
    sle = conn.execute('SELECT COUNT(*) FROM sensation_learning_events').fetchone()[0]
    print(f'   [OK] Private Memory: object_sensation_mappings={osm}, sensation_learning_events={sle}')
except Exception as e:
    print(f'   [FAIL] Stream A: {e}')

try:
    vip = conn.execute('SELECT COUNT(*) FROM viral_information_packages').fetchone()[0]
    avi = conn.execute('SELECT COUNT(*) FROM agent_viral_infections').fetchone()[0]
    print(f'   [OK] Network Wisdom: viral_packages={vip}, infections={avi}')
except Exception as e:
    print(f'   [FAIL] Stream B: {e}')

# 2. Agent Self-Model
print('\n2. AGENT SELF-MODEL (I am this object)')
try:
    aoc = conn.execute('SELECT COUNT(*) FROM agent_object_control').fetchone()[0]
    noc = conn.execute('SELECT COUNT(*) FROM network_object_control_hypotheses').fetchone()[0]
    print(f'   [OK] agent_object_control={aoc}, network_hypotheses={noc}')
except Exception as e:
    print(f'   [FAIL] {e}')

# 3. Pariah System Health
print('\n3. PARIAH SYSTEM HEALTH')
active = conn.execute('SELECT COUNT(*) FROM pariahs WHERE is_active = TRUE').fetchone()[0]
inactive = conn.execute('SELECT COUNT(*) FROM pariahs WHERE is_active = FALSE').fetchone()[0]
tox_1 = conn.execute('SELECT COUNT(*) FROM pariahs WHERE is_active = TRUE AND toxicity >= 0.99').fetchone()[0]
print(f'   Active pariahs: {active} (toxicity=1.0: {tox_1})')
print(f'   Inactive pariahs: {inactive}')
if active < 50:
    print(f'   [WARN] Too few active pariahs! Obsolescence check may be too aggressive')

# 4. Winning Sequences
print('\n4. WINNING SEQUENCES (Network Knowledge)')
seqs = conn.execute('SELECT COUNT(*) FROM winning_sequences WHERE is_active = 1').fetchone()[0]
total = conn.execute('SELECT COUNT(*) FROM winning_sequences').fetchone()[0]
print(f'   Active: {seqs}, Total: {total}')

# 5. Agent Population
print('\n5. AGENT POPULATION')
active = conn.execute('SELECT COUNT(*) FROM agents WHERE is_active = TRUE').fetchone()[0]
total_agents = conn.execute('SELECT COUNT(*) FROM agents').fetchone()[0]
print(f'   Active agents: {active}, Total ever: {total_agents}')

# 6. Level Progression (All Time)
print('\n6. LEVEL PROGRESSION (All Time)')
levels = conn.execute('SELECT level_completions, COUNT(*) as cnt FROM game_results GROUP BY level_completions ORDER BY level_completions LIMIT 10').fetchall()
total_games = sum(l['cnt'] for l in levels)
for l in levels:
    pct = (l['cnt'] / total_games * 100) if total_games > 0 else 0
    lvl = l['level_completions']
    cnt = l['cnt']
    print(f'   Level {lvl}: {cnt} games ({pct:.1f}%)')

# 7. Check if decay was ever called
print('\n7. PARIAH DECAY EVIDENCE')
decayed = conn.execute('SELECT COUNT(*) FROM pariahs WHERE toxicity < 0.99 AND toxicity > 0.1').fetchone()[0]
print(f'   Pariahs with toxicity between 0.1-0.99 (showing decay): {decayed}')

# 8. Network Failure Hypotheses
print('\n8. NETWORK FAILURE HYPOTHESES')
hyp = conn.execute('SELECT COUNT(*), AVG(confidence) FROM network_failure_hypotheses').fetchone()
avg_conf = hyp[1] if hyp[1] else 0
print(f'   Total: {hyp[0]}, Avg confidence: {avg_conf:.2f}')

# 9. Viral Package Activity
print('\n9. VIRAL PACKAGE ACTIVITY')
vip_active = conn.execute('SELECT COUNT(*) FROM viral_information_packages WHERE is_active = 1').fetchone()[0]
vip_total = conn.execute('SELECT COUNT(*) FROM viral_information_packages').fetchone()[0]
print(f'   Active packages: {vip_active}, Total: {vip_total}')

# 10. Game Concentration
print('\n10. GAME CONCENTRATION CHECK')
top_games = conn.execute('''
    SELECT game_id, COUNT(*) as cnt
    FROM game_results
    GROUP BY game_id
    ORDER BY cnt DESC
    LIMIT 5
''').fetchall()
total_g = conn.execute('SELECT COUNT(*) FROM game_results').fetchone()[0]
for g in top_games:
    pct = (g['cnt'] / total_g * 100) if total_g > 0 else 0
    gid = g['game_id'][:30]
    print(f'   {gid}: {g["cnt"]} ({pct:.1f}%)')

conn.close()

print('\n' + '='*70)
print('ANALYSIS COMPLETE')
print('='*70)
