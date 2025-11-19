import sqlite3

db = sqlite3.connect('core_data.db')
db.row_factory = sqlite3.Row
cursor = db.cursor()

# Find most RECENT games with valid scorecard_id
cursor.execute("""
    SELECT game_id, scorecard_id, total_actions, level_completions, final_score, created_at
    FROM game_results
    WHERE scorecard_id IS NOT NULL
    ORDER BY created_at DESC
    LIMIT 5
""")

results = cursor.fetchall()

if results:
    print(f"Most Recent Games with Scorecard IDs (showing {len(results)}):\n")
    for i, result in enumerate(results, 1):
        game_id = result['game_id']
        scorecard_id = result['scorecard_id']
        total_actions = result['total_actions']
        levels = result['level_completions']
        created_at = result['created_at']
        
        replay_url = f"https://three.arcprize.org/replay/{game_id}/{scorecard_id}"
        
        print(f"{i}. {game_id}: {total_actions} actions, {levels} levels")
        print(f"   Timestamp: {created_at}")
        print(f"   Scorecard: {scorecard_id}")
        print(f"   URL: {replay_url}\n")
else:
    print("No games with scorecard_id found")

db.close()
