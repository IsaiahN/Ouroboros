import sqlite3

conn = sqlite3.connect('core_data.db')
cur = conn.cursor()

print('=== Replay System Investigation ===')

# Get winning sequences
cur.execute('''
    SELECT sequence_id, game_type, level_number, success_rate_when_reused, times_referenced
    FROM winning_sequences 
    WHERE is_active=1 AND success_rate_when_reused >= 0.9
    ORDER BY game_type, level_number
''')
sequences = cur.fetchall()
print(f'\nHigh-success sequences ({len(sequences)}):')

# Get level_sequence_usage by extracting game_type from game_id
cur.execute('''
    SELECT SUBSTR(game_id, 1, 4) as game_type, level_number, 
           COUNT(*) as usage_count,
           COUNT(DISTINCT sequence_id) as unique_sequences
    FROM level_sequence_usage
    WHERE used_sequence = 1
    GROUP BY SUBSTR(game_id, 1, 4), level_number
''')
usage_records = {(r[0], r[1]): {'uses': r[2], 'seqs': r[3]} for r in cur.fetchall()}

print('\nSequence vs Usage comparison:')
for seq in sequences:
    seq_id, game_type, level, success, refs = seq
    key = (game_type, level)
    usage = usage_records.get(key, {'uses': 0, 'seqs': 0})
    status = '[OK]' if usage['uses'] > 0 else '[MISSING]'
    print(f'  {status} {game_type} L{level}: seq={seq_id[:20]}... refs={refs}, usage_records={usage["uses"]}')

# Check if sequences are being replayed but not logged
cur.execute('''
    SELECT SUBSTR(game_id, 1, 4) as game_type, level_number, 
           COUNT(*) as game_count
    FROM game_results
    WHERE created_at > datetime('now', '-7 days')
    GROUP BY SUBSTR(game_id, 1, 4), level_number
''')
games_played = {(r[0], r[1]): r[2] for r in cur.fetchall()}

print('\n\nGames played vs sequence usage (last 7 days):')
for seq in sequences:
    seq_id, game_type, level, success, refs = seq
    key = (game_type, level)
    played = games_played.get(key, 0)
    usage = usage_records.get(key, {'uses': 0, 'seqs': 0})
    if usage['uses'] == 0 and played > 0:
        print(f'  [GAP] {game_type} L{level}: {played} games played, 0 replays logged!')

# Check where log_level_sequence_usage is called
print('\n\nSample level_sequence_usage records:')
cur.execute('''
    SELECT SUBSTR(game_id, 1, 4) as game_type, level_number, used_sequence, sequence_id, timestamp
    FROM level_sequence_usage
    ORDER BY timestamp DESC
    LIMIT 10
''')
for r in cur.fetchall():
    print(f'  {r[0]} L{r[1]}: used={r[2]}, seq={r[3][:20] if r[3] else "None"}..., time={r[4]}')

conn.close()
