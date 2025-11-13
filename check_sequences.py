#!/usr/bin/env python3
"""Quick check of winning sequences and agent modes"""
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface

db = DatabaseInterface()

# Check sequences
seqs = db.execute_query('SELECT COUNT(*) as cnt FROM winning_sequences')
print(f'\n=== WINNING SEQUENCES ===')
print(f'Total sequences: {seqs[0]["cnt"]}')

recent = db.execute_query('''
    SELECT game_id, level_number, total_actions, times_referenced
    FROM winning_sequences 
    ORDER BY sequence_id DESC LIMIT 10
''')
print(f'\nRecent sequences:')
for s in recent:
    print(f'  {s["game_id"]} Level {s["level_number"]}: {s["total_actions"]} actions, used {s["times_referenced"]}x')

# Check agent mode assignments
print(f'\n=== AGENT MODE ASSIGNMENTS ===')
modes = db.execute_query('''
    SELECT 
        operating_mode,
        COUNT(DISTINCT agent_id) as agent_count
    FROM agent_operating_modes
    WHERE assigned_timestamp > datetime('now', '-1 day')
    GROUP BY operating_mode
    ORDER BY agent_count DESC
''')
for m in modes:
    print(f'  {m["operating_mode"]}: {m["agent_count"]} agents')

# Check recent performance by mode
print(f'\n=== RECENT PERFORMANCE BY MODE ===')
perf = db.execute_query('''
    SELECT 
        aom.operating_mode,
        COUNT(*) as games_played,
        AVG(aap.final_score) as avg_score,
        SUM(aap.win_achieved) as wins
    FROM agent_arc_performance aap
    JOIN agent_operating_modes aom ON aap.agent_id = aom.agent_id
    WHERE aap.game_timestamp > datetime('now', '-1 hour')
    GROUP BY aom.operating_mode
    ORDER BY games_played DESC
''')
for p in perf:
    win_rate = (p['wins'] / p['games_played'] * 100) if p['games_played'] > 0 else 0
    print(f'  {p["operating_mode"]}: {p["games_played"]} games, avg score {p["avg_score"]:.2f}, {p["wins"]} wins ({win_rate:.1f}%)')

# Check if sequences are being referenced
print(f'\n=== SEQUENCE USAGE STATS ===')
usage = db.execute_query('''
    SELECT 
        COUNT(*) as total_seqs,
        SUM(times_referenced) as total_refs,
        AVG(times_referenced) as avg_refs,
        MAX(times_referenced) as max_refs
    FROM winning_sequences
''')
if usage:
    u = usage[0]
    print(f'  Total sequences: {u["total_seqs"]}')
    print(f'  Total references: {u["total_refs"]}')
    print(f'  Average refs per sequence: {u["avg_refs"]:.1f}')
    print(f'  Most referenced: {u["max_refs"]}x')

db.close()
