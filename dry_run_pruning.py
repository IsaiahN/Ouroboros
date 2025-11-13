#!/usr/bin/env python3
"""Dry run of pruning logic to see what would be pruned"""
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import random
from database_interface import DatabaseInterface

db = DatabaseInterface()

# Get current population size
population = db.execute_query("SELECT COUNT(*) as cnt FROM agents WHERE is_active = TRUE")
population_size = population[0]['cnt']

print(f"\n=== PRUNING DRY RUN ===")
print(f"Current population: {population_size} agents")

# Calculate adaptive target based on available games
# Get distinct game types from agent_arc_performance table
game_types_result = db.execute_query("""
    SELECT DISTINCT SUBSTR(game_id, 1, 4) as game_type
    FROM agent_arc_performance
    WHERE game_id IS NOT NULL
""")
game_types = [row['game_type'] for row in game_types_result if row['game_type']]

if not game_types:
    # Fallback to common game types if no data yet
    game_types = ['sp80', 'ls20', 'lp85', 'ft09', 'as66', 'vc33']
    print(f"  [WARN] No game data found, using default game types")

TARGET_POPULATION = len(game_types) * 10  # 10 agents per game type
print(f"Target population: {TARGET_POPULATION} agents ({len(game_types)} game types × 10)")

if population_size <= TARGET_POPULATION:
    print(f"\n✅ No pruning needed - population is at or below target")
    db.close()
    exit(0)

target_pruned = population_size - TARGET_POPULATION
print(f"Target to prune: {target_pruned} agents")

# STEP 1: Get prestige protection map
agents_with_prestige = db.execute_query("""
    SELECT agent_id, survival_protection
    FROM agents
    WHERE is_active = TRUE
""")

protection_map = {
    agent['agent_id']: agent.get('survival_protection', 0.0) or 0.0
    for agent in agents_with_prestige
}

print(f"\n=== PROTECTION ANALYSIS ===")
print(f"Agents with prestige protection: {len([p for p in protection_map.values() if p > 0])}")
avg_protection = sum(protection_map.values()) / len(protection_map) if protection_map else 0
print(f"Average protection level: {avg_protection:.2%}")

# STEP 2: Identify top 10 performers per game type
top_performers_by_game = {}
total_specialists = set()

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
    
    top_performers_by_game[game_type] = [a['agent_id'] for a in top_agents]
    for agent in top_agents:
        total_specialists.add(agent['agent_id'])

print(f"\nTop 10 specialists per game type:")
for game_type in game_types:
    count = len(top_performers_by_game.get(game_type, []))
    print(f"  {game_type}: {count} protected specialists")
print(f"Total unique specialists: {len(total_specialists)}")

# STEP 3: Get all agents sorted by performance (worst first)
all_agents_sorted = db.execute_query("""
    SELECT agent_id, avg_score_per_game, total_games_won, score_efficiency, survival_protection
    FROM agents
    WHERE is_active = TRUE
    ORDER BY avg_score_per_game ASC, total_games_won ASC, score_efficiency ASC
""")

# STEP 4: Calculate adaptive prestige dampening
overpopulation_ratio = population_size / TARGET_POPULATION
if overpopulation_ratio > 10:
    prestige_dampening = 0.1
elif overpopulation_ratio > 5:
    prestige_dampening = 0.3
elif overpopulation_ratio > 2:
    prestige_dampening = 0.6
else:
    prestige_dampening = 1.0

print(f"\n=== ADAPTIVE DAMPENING ===")
print(f"Overpopulation ratio: {overpopulation_ratio:.1f}x target")
print(f"Prestige dampening: {prestige_dampening:.0%} effectiveness")
print(f"Example: 40% base protection → {40 * prestige_dampening:.0f}% effective protection")

# STEP 5: Simulate pruning
print(f"\n=== PRUNING SIMULATION ===")
pruned_count = 0
protected_by_prestige = 0
protected_by_specialist = 0
would_prune = []

random.seed(42)  # Consistent results for dry run

for agent in all_agents_sorted:
    agent_id = agent['agent_id']
    
    # Check specialist protection
    if agent_id in total_specialists:
        protected_by_specialist += 1
        continue
    
    # Check prestige protection (with adaptive dampening)
    base_protection = protection_map.get(agent_id, 0.0)
    effective_protection = base_protection * prestige_dampening
    if random.random() < effective_protection:
        protected_by_prestige += 1
        continue
    
    # Would be pruned
    would_prune.append({
        'agent_id': agent_id,
        'avg_score': agent['avg_score_per_game'],
        'wins': agent['total_games_won'],
        'efficiency': agent['score_efficiency'],
        'protection': agent.get('survival_protection', 0.0)
    })
    pruned_count += 1
    
    if pruned_count >= target_pruned:
        break

print(f"Would prune: {pruned_count} agents (target: {target_pruned})")
print(f"Protected by specialist status: {protected_by_specialist} agents")
print(f"Protected by prestige: {protected_by_prestige} agents")
print(f"Final population: {population_size - pruned_count} agents")

# Show sample of agents that would be pruned
print(f"\n=== SAMPLE OF AGENTS TO PRUNE (first 10) ===")
for i, agent in enumerate(would_prune[:10], 1):
    print(f"{i}. {agent['agent_id'][:12]}... score={agent['avg_score']:.3f}, wins={agent['wins']}, eff={agent['efficiency']:.3f}, prestige={agent['protection']:.0%}")

if len(would_prune) > 10:
    print(f"... and {len(would_prune) - 10} more")

# Show protection distribution of agents that would be pruned
print(f"\n=== PROTECTION DISTRIBUTION OF PRUNED AGENTS ===")
protection_levels = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
for i in range(len(protection_levels) - 1):
    low = protection_levels[i]
    high = protection_levels[i + 1]
    count = len([a for a in would_prune if low <= a['protection'] < high])
    pct = (count / len(would_prune) * 100) if would_prune else 0
    print(f"  {low:.0%}-{high:.0%}: {count} agents ({pct:.1f}%)")

db.close()
print(f"\n✅ Dry run complete - no agents were actually pruned")
