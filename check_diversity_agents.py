import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface
import json

db = DatabaseInterface()

# Check agents created after 10/28 9:00 PM
print("=" * 80)
print("AGENTS CREATED AFTER 10/28 9:00 PM (Diversity Training Period)")
print("=" * 80)

diversity_agents = db.execute_query("""
    SELECT 
        agent_id,
        datetime(created_at) as created,
        avg_score_per_game,
        total_games_won,
        total_games_played,
        CASE WHEN total_games_played > 0 
             THEN CAST(total_games_won AS FLOAT) / total_games_played 
             ELSE 0 END as win_rate,
        best_single_game_score
    FROM agents 
    WHERE created_at > '2025-10-28 21:00:00'
    ORDER BY avg_score_per_game DESC 
    LIMIT 20
""")

if diversity_agents:
    print(f"\nFound {len(diversity_agents)} agents created during diversity period")
    print("\nTop performers by avg_score:")
    for agent in diversity_agents:
        print(f"  {agent['agent_id'][:12]}: avg={agent['avg_score_per_game']:.3f}, "
              f"best={agent['best_single_game_score']:.1f}, wins={agent['total_games_won']}/{agent['total_games_played']}, "
              f"win_rate={agent['win_rate']:.1%}, created={agent['created']}")
else:
    print("No agents found created after 10/28 9:00 PM")

# Check pre-diversity agents for comparison
print("\n" + "=" * 80)
print("PRE-DIVERSITY AGENTS (Before 10/28 9:00 PM)")
print("=" * 80)

old_agents = db.execute_query("""
    SELECT 
        agent_id,
        datetime(created_at) as created,
        avg_score_per_game,
        total_games_won,
        total_games_played,
        CASE WHEN total_games_played > 0 
             THEN CAST(total_games_won AS FLOAT) / total_games_played 
             ELSE 0 END as win_rate,
        best_single_game_score
    FROM agents 
    WHERE created_at <= '2025-10-28 21:00:00'
    ORDER BY best_single_game_score DESC 
    LIMIT 10
""")

if old_agents:
    print(f"\nTop {len(old_agents)} pre-diversity agents by best_single_game_score:")
    for agent in old_agents:
        print(f"  {agent['agent_id'][:12]}: avg={agent['avg_score_per_game']:.3f}, "
              f"best={agent['best_single_game_score']:.1f}, wins={agent['total_games_won']}/{agent['total_games_played']}, "
              f"win_rate={agent['win_rate']:.1%}, created={agent['created']}")

print("\n" + "=" * 80)
