#!/usr/bin/env python3
"""Execute real pruning with adaptive prestige dampening"""
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import random
from database_interface import DatabaseInterface

db = DatabaseInterface()

# Get current population size
population = db.execute_query("SELECT COUNT(*) as cnt FROM agents WHERE is_active = TRUE")
population_size = population[0]['cnt']

print(f"\n=== REAL PRUNING EXECUTION ===")
print(f"Current population: {population_size} agents")

# Calculate adaptive target based on available games
game_types_result = db.execute_query("""
    SELECT DISTINCT SUBSTR(game_id, 1, 4) as game_type
    FROM agent_arc_performance
    WHERE game_id IS NOT NULL
""")
game_types = [row['game_type'] for row in game_types_result if row['game_type']]

if not game_types:
    game_types = ['sp80', 'ls20', 'lp85', 'ft09', 'as66', 'vc33']
    print(f"  [WARN] No game data found, using default game types")

TARGET_POPULATION = len(game_types) * 10
print(f"Target population: {TARGET_POPULATION} agents ({len(game_types)} game types × 10)")

if population_size <= TARGET_POPULATION:
    print(f"\n✅ No pruning needed - population is at or below target")
    db.close()
    exit(0)

target_pruned = population_size - TARGET_POPULATION
print(f"Target to prune: {target_pruned} agents")

# Get prestige protection map
agents_with_prestige = db.execute_query("""
    SELECT agent_id, survival_protection
    FROM agents
    WHERE is_active = TRUE
""")

protection_map = {
    agent['agent_id']: agent.get('survival_protection', 0.0) or 0.0
    for agent in agents_with_prestige
}

print(f"\nAgents with prestige protection: {len([p for p in protection_map.values() if p > 0])}")

# Identify top 10 performers per game type
top_performers_by_game = set()

for game_type in game_types:
    top_agents = db.execute_query("""
        SELECT DISTINCT aap.agent_id, 
               AVG(aap.final_score) as avg_score,
               COUNT(*) as games_played
        FROM agent_arc_performance aap
        WHERE aap.game_id LIKE ?
          AND aap.agent_id IN (SELECT agent_id FROM agents WHERE is_active = TRUE)
        GROUP BY aap.agent_id
        HAVING games_played >= 1
        ORDER BY avg_score DESC, games_played DESC
        LIMIT 10
    """, (f"{game_type}-%",))
    
    for agent in top_agents:
        top_performers_by_game.add(agent['agent_id'])

print(f"Protected specialists (top 10/game): {len(top_performers_by_game)} agents")

# Calculate adaptive prestige dampening
overpopulation_ratio = population_size / TARGET_POPULATION
if overpopulation_ratio > 10:
    prestige_dampening = 0.1
elif overpopulation_ratio > 5:
    prestige_dampening = 0.3
elif overpopulation_ratio > 2:
    prestige_dampening = 0.6
else:
    prestige_dampening = 1.0

print(f"\nAdaptive dampening:")
print(f"  Overpopulation ratio: {overpopulation_ratio:.1f}x")
print(f"  Prestige dampening: {prestige_dampening:.0%}")

# Get all agents sorted by performance (worst first)
all_agents_sorted = db.execute_query("""
    SELECT agent_id, avg_score_per_game, total_games_won, score_efficiency
    FROM agents
    WHERE is_active = TRUE
    ORDER BY avg_score_per_game ASC, total_games_won ASC, score_efficiency ASC
""")

# Execute pruning
print(f"\n🔪 EXECUTING PRUNING...")
pruned_count = 0
protected_by_prestige = 0
protected_by_specialist = 0
pruned_agents = []

random.seed()  # Use real randomness

for agent in all_agents_sorted:
    agent_id = agent['agent_id']
    
    # ABSOLUTE PROTECTION: Top 10 performers per game type
    if agent_id in top_performers_by_game:
        protected_by_specialist += 1
        continue
    
    # Check prestige protection (with adaptive dampening)
    base_protection = protection_map.get(agent_id, 0.0)
    effective_protection = base_protection * prestige_dampening
    if random.random() < effective_protection:
        protected_by_prestige += 1
        continue
    
    # Deactivate agent (not deleted - just marked inactive)
    db.execute_query(
        "UPDATE agents SET is_active = 0 WHERE agent_id = ?",
        (agent_id,)
    )
    pruned_agents.append(agent_id)
    pruned_count += 1
    
    # Stop after reaching target
    if pruned_count >= target_pruned:
        break

# Get final population
final_population = db.execute_query("SELECT COUNT(*) as cnt FROM agents WHERE is_active = TRUE")
final_count = final_population[0]['cnt']

print(f"\n=== PRUNING COMPLETE ===")
print(f"  Pruned: {pruned_count} agents")
print(f"  Protected by specialist status: {protected_by_specialist} agents")
print(f"  Protected by prestige: {protected_by_prestige} agents")
print(f"  Starting population: {population_size}")
print(f"  Final population: {final_count}")
print(f"  Target population: {TARGET_POPULATION}")

if final_count > TARGET_POPULATION:
    overage = final_count - TARGET_POPULATION
    print(f"\n⚠️  Still {overage} agents over target (prestige protection prevented reaching target)")
else:
    print(f"\n✅ Population at or below target!")

db.close()
print(f"\n✅ Real pruning executed successfully")
