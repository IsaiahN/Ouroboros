"""
Verify Adaptive Scaling Implementation

Shows how population and offspring adapt to available game count
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface

def show_adaptive_scaling():
    """Demonstrate adaptive scaling formula"""
    
    print("=" * 80)
    print("ADAPTIVE POPULATION SCALING")
    print("=" * 80)
    print()
    print("Formula: TARGET_POPULATION = unique_game_types × 10")
    print("         offspring_size = max(5, TARGET_POPULATION ÷ 10)")
    print()
    print("Examples:")
    print("-" * 80)
    print("Game Types | Target Population | Offspring Size | Agents/Type")
    print("-" * 80)
    
    for game_count in [6, 10, 20, 50, 100, 200]:
        target_pop = game_count * 10
        offspring = max(5, target_pop // 10)
        agents_per_type = target_pop // game_count
        print(f"    {game_count:3d}    |      {target_pop:4d}        |      {offspring:3d}       |     {agents_per_type:2d}")
    
    print()
    print("=" * 80)
    print("CURRENT DATABASE STATE")
    print("=" * 80)
    
    db = DatabaseInterface()
    
    # Check active agents
    active_agents = db.execute_query("""
        SELECT COUNT(*) as count
        FROM agents
        WHERE is_active = TRUE
    """)
    
    print(f"\nActive Agents: {active_agents[0]['count']}")
    
    # Get latest generation
    latest_gen = db.execute_query("""
        SELECT MAX(generation) as max_gen
        FROM agents
    """)
    
    if latest_gen and latest_gen[0]['max_gen']:
        max_gen = latest_gen[0]['max_gen']
        print(f"Latest Generation: {max_gen}")
        
        # Agents in latest generation
        gen_agents = db.execute_query("""
            SELECT COUNT(*) as count
            FROM agents
            WHERE generation = ? AND is_active = TRUE
        """, (max_gen,))
        
        print(f"Agents in Gen {max_gen}: {gen_agents[0]['count']}")
    
    # Check unique game types
    game_types = db.execute_query("""
        SELECT DISTINCT SUBSTR(game_id, 1, 4) as game_type
        FROM game_results
        WHERE game_id IS NOT NULL
        ORDER BY game_type
    """)
    
    print(f"\nUnique Game Types Seen: {len(game_types)}")
    for gt in game_types:
        print(f"  - {gt['game_type']}")
    
    print()
    print("=" * 80)
    print("IMPLEMENTATION DETAILS")
    print("=" * 80)
    print()
    print("Location: autonomous_evolution_runner.py")
    print()
    print("1. Game Type Detection (line ~751):")
    print("   - Extracts unique 4-char prefixes from available_games")
    print("   - Dynamically adapts to ARC API game availability")
    print()
    print("2. Target Population Calculation (line ~760):")
    print("   - ADAPTIVE_TARGET_POPULATION = len(game_types) * 10")
    print("   - Stored in self._current_target_population")
    print()
    print("3. Round-Robin Distribution (line ~778):")
    print("   - Rotates starting game type each generation")
    print("   - Assigns agents round-robin across all types")
    print()
    print("4. Adaptive Offspring (line ~1187):")
    print("   - adaptive_offspring_size = max(5, TARGET_POPULATION // 10)")
    print("   - Scales breeding with population target")
    print()
    print("5. Adaptive Pruning (line ~1326):")
    print("   - Uses self._current_target_population")
    print("   - Checks ALL agents (not just worst 200)")
    print("   - Prunes when population > target")
    print()
    print("=" * 80)
    print("BENEFITS")
    print("=" * 80)
    print()
    print("✅ Auto-scales with ARC game availability")
    print("✅ No hardcoded limits - adapts to future growth")
    print("✅ Maintains optimal agents-per-game ratio (10:1)")
    print("✅ Even distribution prevents game dominance (was 94% vc33)")
    print("✅ Population stays manageable at small scale")
    print("✅ Scales up automatically when more games added")
    print()

if __name__ == '__main__':
    show_adaptive_scaling()
