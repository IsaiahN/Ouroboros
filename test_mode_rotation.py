"""
Test mode rotation across generations
"""
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface
from evolution_game_scheduler import EvolutionGameScheduler

db = DatabaseInterface()
scheduler = EvolutionGameScheduler(db)

# Simulate 3 generations with same agents
test_agents_gen1 = [
    {'agent_id': f'agent_{i}', 'mode': ['pioneer', 'generalist', 'optimizer'][i % 3], 'generation': 1}
    for i in range(6)
]

test_agents_gen2 = [
    {'agent_id': f'agent_{i}', 'mode': ['pioneer', 'generalist', 'optimizer'][i % 3], 'generation': 2}
    for i in range(6)
]

test_agents_gen3 = [
    {'agent_id': f'agent_{i}', 'mode': ['pioneer', 'generalist', 'optimizer'][i % 3], 'generation': 3}
    for i in range(6)
]

print("=== GENERATION 1 ===")
assignments_gen1 = scheduler.assign_games_to_agents(
    agents=test_agents_gen1,
    total_games_to_play=6
)

gen1_assignments = {}
for agent_id, games in assignments_gen1.items():
    for game in games:
        game_type = game.split('-')[0]
        agent = next(a for a in test_agents_gen1 if a['agent_id'] == agent_id)
        gen1_assignments[game_type] = agent['mode']
        print(f"  {game_type} → {agent['mode']}")

# Release all games
for games in assignments_gen1.values():
    for game in games:
        scheduler.release_game(game)

print("\n=== GENERATION 2 ===")
assignments_gen2 = scheduler.assign_games_to_agents(
    agents=test_agents_gen2,
    total_games_to_play=6
)

gen2_assignments = {}
for agent_id, games in assignments_gen2.items():
    for game in games:
        game_type = game.split('-')[0]
        agent = next(a for a in test_agents_gen2 if a['agent_id'] == agent_id)
        gen2_assignments[game_type] = agent['mode']
        print(f"  {game_type} → {agent['mode']}")

# Release all games
for games in assignments_gen2.values():
    for game in games:
        scheduler.release_game(game)

print("\n=== GENERATION 3 ===")
assignments_gen3 = scheduler.assign_games_to_agents(
    agents=test_agents_gen3,
    total_games_to_play=6
)

gen3_assignments = {}
for agent_id, games in assignments_gen3.items():
    for game in games:
        game_type = game.split('-')[0]
        agent = next(a for a in test_agents_gen3 if a['agent_id'] == agent_id)
        gen3_assignments[game_type] = agent['mode']
        print(f"  {game_type} → {agent['mode']}")

print("\n=== ROTATION ANALYSIS ===")
all_game_types = set(gen1_assignments.keys()) | set(gen2_assignments.keys()) | set(gen3_assignments.keys())
for game_type in sorted(all_game_types):
    gen1_mode = gen1_assignments.get(game_type, 'N/A')
    gen2_mode = gen2_assignments.get(game_type, 'N/A')
    gen3_mode = gen3_assignments.get(game_type, 'N/A')
    
    rotated = len(set([gen1_mode, gen2_mode, gen3_mode]) - {'N/A'}) > 1
    rotation_status = "✓ ROTATED" if rotated else "✗ STUCK"
    
    print(f"{game_type}: Gen1={gen1_mode:10s} Gen2={gen2_mode:10s} Gen3={gen3_mode:10s} {rotation_status}")
