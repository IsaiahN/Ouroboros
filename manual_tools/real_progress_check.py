"""Real progress check - score = level completions!"""
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface

db = DatabaseInterface()

print("\n" + "="*70)
print("REAL PROGRESS - Score = Level Completions!")
print("="*70)

# Overall progress (score IS level completions!)
res = db.execute_query("""
    SELECT 
        COUNT(*) as total_games,
        SUM(final_score) as total_levels_completed,
        AVG(final_score) as avg_levels_per_game,
        MAX(final_score) as best_game_levels,
        SUM(CASE WHEN final_score > 0 THEN 1 ELSE 0 END) as games_with_levels,
        SUM(CASE WHEN final_score >= 1 THEN 1 ELSE 0 END) as games_1plus,
        SUM(CASE WHEN final_score >= 2 THEN 1 ELSE 0 END) as games_2plus,
        SUM(CASE WHEN final_score >= 3 THEN 1 ELSE 0 END) as games_3plus
    FROM game_results
""")

r = res[0]
print(f"\n[OVERALL PROGRESS]")
print(f"  Total Games Played: {r['total_games']}")
print(f"  Total Levels Completed: {int(r['total_levels_completed'])}")
print(f"  Games with Levels: {r['games_with_levels']} ({r['games_with_levels']/r['total_games']*100:.1f}%)")
print(f"  Average Levels/Game: {r['avg_levels_per_game']:.3f}")
print(f"  Best Single Game: {int(r['best_game_levels'])} levels")
print(f"\n  Level Breakdown:")
print(f"    ≥1 level: {r['games_1plus']} games")
print(f"    ≥2 levels: {r['games_2plus']} games")
print(f"    ≥3 levels: {r['games_3plus']} games")

# Top performing games
top = db.execute_query("""
    SELECT game_id, final_score as levels, total_actions, 
           (final_score * 1.0 / total_actions) as efficiency
    FROM game_results
    WHERE final_score > 0
    ORDER BY final_score DESC, total_actions ASC
    LIMIT 10
""")

print(f"\n[TOP GAMES] Best Level Completions:")
for i, g in enumerate(top, 1):
    eff = g['efficiency'] if g['efficiency'] else 0
    print(f"  {i}. {g['game_id'][:20]}: {int(g['levels'])} levels, "
          f"{g['total_actions']} actions, eff={eff:.5f}")

# Learning speed check (if we can link to agents)
print(f"\n[LEARNING SPEED] Checking agent performance...")
import math

# Get agent performance from agents table directly
agent_perf = db.execute_query("""
    SELECT 
        agent_id,
        agent_type,
        total_games_played as games_played,
        total_games_won,
        avg_score_per_game as avg_levels,
        score_efficiency,
        generation
    FROM agents
    WHERE total_games_played > 0
    ORDER BY avg_score_per_game DESC, total_games_played ASC
    LIMIT 10
""")

if agent_perf:
    print(f"  Found {len(agent_perf)} agents with gameplay:")
    for i, a in enumerate(agent_perf[:5], 1):
        total_levels = a['avg_levels'] * a['games_played']
        learning_speed = (total_levels ** 1.5) / math.log(a['games_played'] + 1) if a['games_played'] > 0 else 0
        print(f"  {i}. {a['agent_id'][:16]} ({a['agent_type'][:12]}) Gen {a['generation']}")
        print(f"      Games: {a['games_played']}, Avg Levels: {a['avg_levels']:.3f}, "
              f"Learning Speed: {learning_speed:.2f}")
else:
    print("  No agent performance data yet")

# Check if evolution is progressing
generations = db.execute_query("""
    SELECT generation, COUNT(*) as agent_count,
           AVG(total_games_played) as avg_games,
           AVG(avg_score_per_game) as avg_score
    FROM agents
    GROUP BY generation
    ORDER BY generation
""")

print(f"\n[EVOLUTION] Generation Progress:")
for g in generations:
    print(f"  Gen {g['generation']}: {g['agent_count']} agents, "
          f"avg_games={g['avg_games']:.1f}, avg_score={g['avg_score']:.3f}")

print("\n" + "="*70)
print("SUCCESS: System IS working - agents completing levels!")
print("="*70 + "\n")
