"""Check all defensive systems for as66 L5."""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'core_data.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()

print('=== as66 L5 DEFENSIVE SYSTEMS CHECK ===\n')

# 1. Death patterns for L5
print('1. DEATH PATTERNS for as66 L5:')
c.execute('''SELECT fatal_action, bucket_x, bucket_y, death_count, danger_score, is_active
             FROM position_death_patterns 
             WHERE game_type='as66' AND level_number=5
             ORDER BY death_count DESC LIMIT 10''')
rows = c.fetchall()
if rows:
    for r in rows: 
        status = "ACTIVE" if r[5] else "inactive"
        print(f'   ACTION{r[0]} at ({r[1]},{r[2]}): {r[3]} deaths, danger={r[4]:.2f} [{status}]')
else:
    print('   NONE - no death patterns recorded for L5!')

# 2. Checkpoints for L5
print('\n2. FRONTIER CHECKPOINTS for as66 L5:')
c.execute('''SELECT terminal_frame_hash, actions_count, times_used, times_extended, terminal_reason
             FROM frontier_checkpoints 
             WHERE game_type='as66' AND level_number=5''')
rows = c.fetchall()
if rows:
    for r in rows: print(f'   {r[0][:20]}...: {r[1]} actions, used={r[2]}, extended={r[3]}, reason={r[4]}')
else:
    print('   NONE - no checkpoints recorded for L5!')

# 3. Lessons for as66 (no level_number column - lessons are game-wide)
print('\n3. LESSONS LEARNED for as66 (game-wide):')
c.execute('''SELECT lesson_type, lesson_text, times_retrieved, confidence
             FROM game_lessons_learned 
             WHERE game_type='as66'
             ORDER BY times_retrieved DESC LIMIT 5''')
rows = c.fetchall()
if rows:
    for r in rows: 
        content = r[1][:80] if r[1] else 'N/A'
        print(f'   [{r[0]}] retrieved={r[2]}x, conf={r[3]:.2f}: {content}...')
else:
    print('   NONE - no lessons for L5!')

# 4. Topology for L5
print('\n4. FRONTIER TOPOLOGY for as66 L5:')
try:
    c.execute('''SELECT COUNT(*) FROM frontier_topology WHERE game_type='as66' AND level_number=5''')
    count = c.fetchone()[0]
    print(f'   {count} topology records')
except sqlite3.OperationalError:
    print('   TABLE DOES NOT EXIST - frontier_topology not created')

# 5. Winning sequences for L5
print('\n5. WINNING SEQUENCES for as66 L5:')
c.execute('''SELECT sequence_id, total_actions, success_rate_when_reused, times_referenced, is_active
             FROM winning_sequences 
             WHERE game_type='as66' AND level_number=5''')
rows = c.fetchall()
if rows:
    for r in rows:
        status = "ACTIVE" if r[4] else "inactive"
        print(f'   {r[0]}: {r[1]} actions, success={r[2]*100:.1f}%, refs={r[3]} [{status}]')
else:
    print('   NONE - no winning sequences for L5!')

# 6. Check if L5 is even beaten
print('\n6. GAME COMPLETION STATUS:')
c.execute('''SELECT MAX(level_completions), COUNT(*) as games, AVG(final_score) as avg_score
             FROM game_results WHERE game_id LIKE 'as66%' ''')
r = c.fetchone()
print(f'   Max levels completed: {r[0]}')
print(f'   Total games: {r[1]}')
print(f'   Avg score: {r[2]:.1f}' if r[2] else '   Avg score: N/A')

# Check L5 specifically
c.execute('''SELECT COUNT(*) FROM game_results 
             WHERE game_id LIKE 'as66%' AND level_completions >= 5''')
l5_wins = c.fetchone()[0]
print(f'   Games that reached/beat L5: {l5_wins}')

# 7. Recent action traces for L5
print('\n7. RECENT L5 ACTIVITY (last 24h):')
c.execute('''SELECT 
                COUNT(*) as total_actions,
                SUM(CASE WHEN resulted_in_game_over=1 THEN 1 ELSE 0 END) as deaths,
                SUM(CASE WHEN score_change > 0 THEN 1 ELSE 0 END) as positive
             FROM action_traces 
             WHERE game_id LIKE 'as66%' AND level_number=5
             AND created_at > datetime('now', '-24 hours')''')
r = c.fetchone()
if r[0]:
    print(f'   Total actions: {r[0]}')
    print(f'   Deaths: {r[1]} ({100*r[1]/r[0]:.1f}%)')
    print(f'   Positive outcomes: {r[2]} ({100*r[2]/r[0]:.1f}%)')
else:
    print('   No L5 activity in last 24h')

conn.close()
