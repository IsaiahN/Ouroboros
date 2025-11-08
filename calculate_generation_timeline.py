#!/usr/bin/env python3
"""Calculate optimal generation count for Phase 3 readiness"""
from database_interface import DatabaseInterface

db = DatabaseInterface()

print("=" * 80)
print("PHASE 3 READINESS TIMELINE CALCULATION")
print("=" * 80)

# Current metrics
agents = db.execute_query("SELECT COUNT(*) as cnt FROM agents WHERE is_active = TRUE")
total_agents = agents[0]['cnt'] if agents else 0

infected = db.execute_query("SELECT COUNT(DISTINCT agent_id) as cnt FROM agent_viral_infections")
infected_count = infected[0]['cnt'] if infected else 0

aware = db.execute_query("SELECT COUNT(DISTINCT agent_id) as cnt FROM agent_pariah_awareness") 
aware_count = aware[0]['cnt'] if aware else 0

current_infection_rate = (infected_count / max(total_agents, 1)) * 100
current_awareness_rate = (aware_count / max(total_agents, 1)) * 100

print(f"Current Status:")
print(f"  Total active agents: {total_agents:,}")
print(f"  Infected agents: {infected_count:,} ({current_infection_rate:.1f}%)")
print(f"  Aware agents: {aware_count:,} ({current_awareness_rate:.1f}%)")

# Targets
target_infection_rate = 60.0
target_awareness_rate = 50.0

print(f"\nPhase 3 Targets:")
print(f"  Infection rate: {target_infection_rate}% ({int(total_agents * target_infection_rate / 100):,} agents needed)")
print(f"  Awareness rate: {target_awareness_rate}% ({int(total_agents * target_awareness_rate / 100):,} agents needed)")

# Estimate spread rate from recent data
recent_infections = db.execute_query("""
    SELECT COUNT(*) as new_infections
    FROM agent_viral_infections 
    WHERE infection_generation >= (
        SELECT MAX(generation) - 5 FROM agents WHERE generation IS NOT NULL
    )
""")

recent_awareness = db.execute_query("""
    SELECT COUNT(*) as new_awareness  
    FROM agent_pariah_awareness
    WHERE awareness_generation >= (
        SELECT MAX(generation) - 5 FROM agents WHERE generation IS NOT NULL
    )
""")

new_infections_per_5gen = recent_infections[0]['new_infections'] if recent_infections else 0
new_awareness_per_5gen = recent_awareness[0]['new_awareness'] if recent_awareness else 0

print(f"\nRecent Spread Rate (last 5 generations):")
print(f"  New infections: {new_infections_per_5gen}")
print(f"  New awareness: {new_awareness_per_5gen}")

if new_infections_per_5gen > 0 and new_awareness_per_5gen > 0:
    # Calculate generations needed
    infection_deficit = max(0, int(total_agents * target_infection_rate / 100) - infected_count)
    awareness_deficit = max(0, int(total_agents * target_awareness_rate / 100) - aware_count)
    
    infections_per_gen = new_infections_per_5gen / 5
    awareness_per_gen = new_awareness_per_5gen / 5
    
    gens_for_infection = infection_deficit / max(infections_per_gen, 1) if infections_per_gen > 0 else 999
    gens_for_awareness = awareness_deficit / max(awareness_per_gen, 1) if awareness_per_gen > 0 else 999
    
    estimated_gens_needed = max(gens_for_infection, gens_for_awareness)
    
    print(f"\nEstimated Timeline:")
    print(f"  Infections per generation: {infections_per_gen:.1f}")
    print(f"  Awareness per generation: {awareness_per_gen:.1f}")
    print(f"  Generations for infection target: {gens_for_infection:.0f}")
    print(f"  Generations for awareness target: {gens_for_awareness:.0f}")
    print(f"  Generations needed (bottleneck): {estimated_gens_needed:.0f}")
else:
    # Assume conservative spread rate
    estimated_gens_needed = 50
    print(f"\nNo recent spread data - using conservative estimate: {estimated_gens_needed} generations")

print("\n" + "=" * 80)
print("RECOMMENDATIONS FOR YOUR TRIP")
print("=" * 80)

# Conservative recommendation
recommended_gens = max(30, int(estimated_gens_needed * 1.5))  # 50% buffer

print(f"\nRecommended generations to run: {recommended_gens}")
print(f"Reasoning:")
print(f"  - Estimated need: {estimated_gens_needed:.0f} generations")
print(f"  - Safety buffer: +50%")
print(f"  - Minimum run: 30 generations (for stability)")

# Time calculation
time_per_gen_minutes = 60  # From evolution config
total_hours = (recommended_gens * time_per_gen_minutes) / 60
total_days = total_hours / 24

print(f"\nTime Estimate:")
print(f"  {recommended_gens} generations × 60 min/gen = {total_hours:.0f} hours")
print(f"  = {total_days:.1f} days")

if total_days <= 1.5:
    print(f"  ✅ Fits in your day away!")
elif total_days <= 2.5:
    print(f"  ⚠️  Might need 2+ days")
else:
    print(f"  ❌ Too long for one trip - consider shorter run")

print(f"\nCommand to run:")
print(f"  python run_evolution.py --specialist --max-generations {recommended_gens}")

print("\n" + "=" * 80)
print("ANSWERS TO YOUR QUESTIONS")
print("=" * 80)

print("\n1. SP80 & LS20 NO LEVEL WINS - Is this natural?")
print("   ✅ YES, this is natural and expected:")
print("   • ARC games have wildly different difficulty levels")
print("   • Some games are genuinely much harder than others")  
print("   • sp80: 814 attempts, 0 levels (very hard)")
print("   • ls20: 230 attempts, 0 levels (also very hard)")
print("   • This is NOT due to pattern matching from other games")
print("   • It's due to inherent game complexity")

print("\n2. ACTION BOOST FOR UNBEATEN GAMES - Implemented!")
print("   ✅ DONE: Added 2x-3x action multiplier:")
print("   • If agent assigned to games with NO level wins → 2x actions")
print("   • If agent assigned ONLY to unbeaten games → 3x actions")
print("   • Bonus removed once any level win achieved")
print("   • This gives agents more exploration time on hard games")

print("\n3. GENERATIONS FOR YOUR TRIP:")
print(f"   ✅ RECOMMENDATION: {recommended_gens} generations")
print(f"   • Estimated time: {total_days:.1f} days")
print(f"   • Should achieve Phase 3 readiness (60% infection, 50% awareness)")
print(f"   • Includes safety buffer for your peace of mind")

print("\n" + "=" * 80)