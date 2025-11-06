"""Manually trigger prestige calculation for current generation."""
from database_interface import DatabaseInterface
from prestige_engine import PrestigeEngine

db = DatabaseInterface()
prestige_engine = PrestigeEngine(db)

# Get current generation
current_gen_result = db.execute_query("""
    SELECT MAX(generation) as current_gen 
    FROM agents 
    WHERE is_active = TRUE
""")

if current_gen_result:
    current_gen = current_gen_result[0]['current_gen']
    print(f"🎯 Calculating prestige for generation {current_gen}")
    
    # Run prestige calculation
    benefits_map = prestige_engine.update_all_agent_prestige(current_gen)
    
    print(f"✅ Prestige calculated for {len(benefits_map)} agents")
    
    if benefits_map:
        # Show top 5 agents by prestige
        sorted_agents = sorted(benefits_map.items(), key=lambda x: x[1]['prestige'], reverse=True)[:5]
        print("\n🏆 Top 5 Agents by Prestige:")
        for agent_id, benefits in sorted_agents:
            print(f"  {agent_id}: {benefits['prestige']:.4f}")
            print(f"    Breeding priority: {benefits['breeding_priority']:.2f}x")
            print(f"    Survival protection: {benefits['survival_protection']:.1f}%")
            print(f"    Bonus game slots: {benefits['bonus_game_slots']}")
    
    # Verify agents table was updated
    agents_with_prestige = db.execute_query("""
        SELECT COUNT(*) as count 
        FROM agents 
        WHERE discovery_prestige > 0
    """)
    
    if agents_with_prestige:
        print(f"\n💰 Agents with prestige in table: {agents_with_prestige[0]['count']}")
        
        if agents_with_prestige[0]['count'] > 0:
            print("🎉 PRESTIGE SYSTEM FULLY WORKING!")
        else:
            print("⚠️ Prestige calculated but not persisted to agents table")
else:
    print("❌ No agents found")
