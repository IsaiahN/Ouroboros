import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface

db = DatabaseInterface()

# Check very recent games
print("\n[RECENT GAMES CHECK]")

recent = db.execute_query("""
    SELECT COUNT(*) as total,
           MAX(end_time) as last_game,
           MIN(start_time) as first_game
    FROM game_results
    WHERE end_time >= datetime('now', '-1 hour')
""")

print(f"  Last 1 hour: {recent[0]['total']} games")
if recent[0]['last_game']:
    print(f"  Last game ended: {recent[0]['last_game']}")

# Check if generation 13 or 14 agents played games
gen13_games = db.execute_query("""
    SELECT COUNT(DISTINCT aap.game_id) as game_count,
           COUNT(DISTINCT aap.agent_id) as agent_count,
           MAX(aap.game_timestamp) as last_game
    FROM agent_arc_performance aap
    JOIN agents a ON aap.agent_id = a.agent_id
    WHERE a.generation = 13
""")

print(f"\n[GEN 13 ACTIVITY]")
print(f"  Agents: {gen13_games[0]['agent_count']}")
print(f"  Games: {gen13_games[0]['game_count']}")
print(f"  Last game: {gen13_games[0]['last_game']}")

# Check if any Gen 14 exists
gen14 = db.execute_query("""
    SELECT COUNT(*) as count 
    FROM agents 
    WHERE generation = 14
""")

print(f"\n[GEN 14 CHECK]")
print(f"  Gen 14 agents exist: {'YES' if gen14[0]['count'] > 0 else 'NO'}")
if gen14[0]['count'] > 0:
    print(f"  Count: {gen14[0]['count']}")
