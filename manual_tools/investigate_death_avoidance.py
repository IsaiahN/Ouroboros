import sqlite3

conn = sqlite3.connect('core_data.db')
cur = conn.cursor()

print('=== Death pattern vs action trace analysis (as66 L1) ===')

# Death patterns
cur.execute('''
    SELECT fatal_action, death_count, bucket_x, bucket_y, danger_score
    FROM position_death_patterns 
    WHERE game_type="as66" AND level_number=1 AND is_active=1 
    ORDER BY death_count DESC LIMIT 10
''')
print('\nDeath patterns:')
for r in cur.fetchall():
    print(f'  ACTION{r[0]}: {r[1]} deaths at bucket ({r[2]},{r[3]}), danger={r[4]:.2f}')

# Action usage in last 24h - BY LEVEL
cur.execute('''
    SELECT level_number, action_number, 
           COUNT(*) as uses, 
           SUM(CASE WHEN score_change < 0 THEN 1 ELSE 0 END) as deaths_24h,
           AVG(score_change) as avg_score
    FROM action_traces 
    WHERE game_id LIKE "as66%" 
      AND timestamp > datetime("now", "-24 hours") 
    GROUP BY level_number, action_number 
    ORDER BY level_number, uses DESC
''')
print('\nActions in last 24h BY LEVEL:')
current_level = None
for r in cur.fetchall():
    if current_level != r[0]:
        current_level = r[0]
        print(f'\n  Level {current_level}:')
    print(f'    ACTION{r[1]}: {r[2]} uses, {r[3]} deaths, avg={r[4]:.2f}')

# KEY CHECK: Actions on L1 ONLY (where deaths occur)
cur.execute('''
    SELECT action_number, 
           COUNT(*) as uses, 
           SUM(CASE WHEN score_change < 0 THEN 1 ELSE 0 END) as deaths_24h
    FROM action_traces 
    WHERE game_id LIKE "as66%" 
      AND level_number = 1
      AND timestamp > datetime("now", "-24 hours") 
    GROUP BY action_number 
    ORDER BY uses DESC
''')
print('\n\n=== CRITICAL: L1-ONLY usage (where death patterns exist) ===')
for r in cur.fetchall():
    print(f'  ACTION{r[0]}: {r[1]} uses, {r[2]} deaths')

# Check if position was known when actions taken
cur.execute('''
    SELECT action_number, 
           SUM(CASE WHEN position_x IS NULL THEN 1 ELSE 0 END) as pos_unknown,
           SUM(CASE WHEN position_x IS NOT NULL THEN 1 ELSE 0 END) as pos_known,
           COUNT(*) as total
    FROM action_traces 
    WHERE game_id LIKE "as66%" 
      AND level_number = 1
      AND timestamp > datetime("now", "-24 hours") 
    GROUP BY action_number 
    ORDER BY total DESC
''')
print('\n=== Position known vs unknown (L1) ===')
for r in cur.fetchall():
    print(f'  ACTION{r[0]}: pos_unknown={r[1]}, pos_known={r[2]}, total={r[3]}')

conn.close()

