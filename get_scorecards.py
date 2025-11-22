import sqlite3
conn = sqlite3.connect('core_data.db')
print("Scorecards with non-zero scores:")
for row in conn.execute("""
    SELECT scorecard_id, game_id, final_score, total_actions 
    FROM game_results 
    WHERE scorecard_id IS NOT NULL 
    AND final_score > 0 
    ORDER BY created_at DESC 
    LIMIT 5
"""):
    print(f"{row[0]} | {row[1]} | Score: {row[2]} | Actions: {row[3]}")
conn.close()
