"""Quick analysis of current system state"""
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface

db = DatabaseInterface()

print("\n" + "="*70)
print("QUICK ANALYSIS")
print("="*70)

# Top agents
agents = db.execute_query("""
    SELECT agent_id, total_games_played, total_games_won, avg_score_per_game, score_efficiency
    FROM agents 
    WHERE total_games_played > 0 
    ORDER BY total_games_won DESC, avg_score_per_game DESC 
    LIMIT 10
""")

print(f"\n[TOP] Top {len(agents)} Agents:")
for i, a in enumerate(agents, 1):
    print(f"  {i}. {a['agent_id'][:16]}: {a['total_games_won']}/{a['total_games_played']} wins, "
          f"avg={a['avg_score_per_game']:.2f}, efficiency={a['score_efficiency']:.2f}")

# Recent games
games = db.execute_query("""
    SELECT game_id, status, final_score, win_detected, total_actions, level_completions
    FROM game_results 
    ORDER BY end_time DESC 
    LIMIT 10
""")

print(f"\n[RECENT] Last {len(games)} Games:")
for g in games:
    win_marker = "[WIN]" if g['win_detected'] else "     "
    print(f"  {win_marker} {g['game_id'][:16]}: {g['status']:10} score={g['final_score']:.1f} "
          f"levels={g['level_completions']} actions={g['total_actions']}")

# Check what's happening with failures
failed = db.execute_query("""
    SELECT COUNT(*) as c 
    FROM game_results 
    WHERE status = 'failed'
""")
completed = db.execute_query("""
    SELECT COUNT(*) as c 
    FROM game_results 
    WHERE status = 'completed'
""")

print(f"\n[STATS] Game Status:")
print(f"  Completed: {completed[0]['c']}")
print(f"  Failed: {failed[0]['c']}")

# Check if any wins
wins = db.execute_query("""
    SELECT COUNT(*) as c 
    FROM game_results 
    WHERE win_detected = TRUE
""")
print(f"  Wins: {wins[0]['c']}")

print("\n" + "="*70)
