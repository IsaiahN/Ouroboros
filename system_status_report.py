#!/usr/bin/env python3
"""
Complete system status check - verify all phases are integrated and working
"""

from database_interface import DatabaseInterface

def main():
    db = DatabaseInterface()
    
    print("\n" + "=" * 80)
    print("BITTERTRUTH-AI SYSTEM STATUS")
    print("=" * 80)
    
    # Population
    pop = db.execute_query("SELECT COUNT(*) as count, MAX(generation) as gen FROM agents WHERE is_active = TRUE")
    print(f"\n📊 POPULATION")
    print(f"   Active Agents: {pop[0]['count']:,}")
    print(f"   Current Generation: {pop[0]['gen']}")
    
    # Phase 1: Prestige
    prestige = db.execute_query("""
        SELECT COUNT(*) as count, 
               AVG(discovery_prestige) as avg_prestige,
               MAX(discovery_prestige) as max_prestige
        FROM agents 
        WHERE is_active = TRUE AND discovery_prestige > 0
    """)
    print(f"\n✅ PHASE 1: PRESTIGE SYSTEM")
    print(f"   Agents with prestige: {prestige[0]['count']:,}")
    print(f"   Avg prestige: {prestige[0]['avg_prestige']:.2f}")
    print(f"   Max prestige: {prestige[0]['max_prestige']:.2f}")
    
    # Phase 2: Action Economy
    economy = db.execute_query("""
        SELECT COUNT(*) as count,
               AVG(action_allowance_per_level) as avg_per_level,
               AVG(action_allowance_total) as avg_total
        FROM agents
        WHERE is_active = TRUE
    """)
    print(f"\n✅ PHASE 2: ACTION ECONOMY")
    print(f"   Agents with budgets: {economy[0]['count']:,}")
    print(f"   Avg per-level budget: {economy[0]['avg_per_level']:.0f}")
    print(f"   Avg total budget: {economy[0]['avg_total']:.0f}")
    
    # Phase 2.5: Knowledge Recombination
    recomb = db.execute_query("SELECT COUNT(*) as count FROM sequence_dependencies")
    print(f"\n✅ PHASE 2.5: KNOWLEDGE RECOMBINATION")
    print(f"   Sequence dependencies: {recomb[0]['count']:,}")
    
    # Phase 3: Viral Packages
    packages = db.execute_query("""
        SELECT COUNT(*) as active_packages FROM viral_information_packages WHERE is_active = TRUE
    """)
    infections = db.execute_query("""
        SELECT COUNT(*) as total_infections FROM agent_viral_infections WHERE is_active = TRUE
    """)
    pariahs = db.execute_query("""
        SELECT COUNT(*) as active_pariahs FROM pariahs WHERE is_active = TRUE
    """)
    awareness = db.execute_query("""
        SELECT COUNT(*) as total_awareness FROM agent_pariah_awareness WHERE is_active = TRUE
    """)
    
    print(f"\n✅ PHASE 3: VIRAL PACKAGES & PARIAHS")
    print(f"   📦 Viral packages: {packages[0]['active_packages']}")
    print(f"   🦠 Package infections: {infections[0]['total_infections']}")
    print(f"   ☠️  Pariahs: {pariahs[0]['active_pariahs']}")
    print(f"   🛡️  Pariah awareness: {awareness[0]['total_awareness']}")
    
    # Knowledge Base
    sequences = db.execute_query("SELECT COUNT(*) as count FROM winning_sequences")
    patterns = db.execute_query("SELECT COUNT(*) as count FROM discovered_patterns")
    print(f"\n📚 KNOWLEDGE BASE")
    print(f"   Winning sequences: {sequences[0]['count']}")
    print(f"   Discovered patterns: {patterns[0]['count']}")
    
    # Recent Activity
    recent_games = db.execute_query("""
        SELECT COUNT(*) as count 
        FROM game_results 
        WHERE end_time > datetime('now', '-1 hour')
    """)
    print(f"\n⏱️  RECENT ACTIVITY (Last Hour)")
    print(f"   Games played: {recent_games[0]['count']}")
    
    # System Health
    print(f"\n🏥 SYSTEM HEALTH")
    
    # Check code integration
    try:
        from viral_package_engine import ViralPackageEngine
        print(f"   ✅ viral_package_engine.py imported successfully")
    except Exception as e:
        print(f"   ❌ viral_package_engine.py import failed: {e}")
    
    # Check core gameplay integration
    with open('core_gameplay.py', 'r', encoding='utf-8') as f:
        gameplay_code = f.read()
        if 'PHASE 3' in gameplay_code and 'create_viral_package_from_sequence' in gameplay_code:
            print(f"   ✅ core_gameplay.py has Phase 3 integration")
        else:
            print(f"   ❌ core_gameplay.py missing Phase 3 integration")
    
    # Check evolution runner integration
    with open('autonomous_evolution_runner.py', 'r', encoding='utf-8') as f:
        runner_code = f.read()
        if 'viral_engine' in runner_code and 'display_viral_ecosystem_dashboard' in runner_code:
            print(f"   ✅ autonomous_evolution_runner.py has Phase 3 integration")
        else:
            print(f"   ❌ autonomous_evolution_runner.py missing Phase 3 integration")
    
    print("\n" + "=" * 80)
    print("VERDICT")
    print("=" * 80)
    
    all_good = True
    
    if prestige[0]['count'] == 0:
        print("⚠️  Phase 1: No agents have prestige yet")
        all_good = False
    else:
        print("✅ Phase 1: Prestige system active")
    
    if economy[0]['count'] == 0:
        print("⚠️  Phase 2: No agents have action budgets")
        all_good = False
    else:
        print("✅ Phase 2: Action economy active")
    
    if recomb[0]['count'] == 0:
        print("⚠️  Phase 2.5: No sequence dependencies yet")
        all_good = False
    else:
        print("✅ Phase 2.5: Knowledge recombination active")
    
    if packages[0]['active_packages'] == 0:
        print("⚠️  Phase 3: No viral packages yet (run evolution to create)")
    else:
        print(f"✅ Phase 3: {packages[0]['active_packages']} viral packages active")
    
    if recent_games[0]['count'] == 0:
        print("\n🔸 NOTE: No games played in last hour")
        print("   → ARC API may be having issues")
        print("   → Or system is idle waiting for next evolution cycle")
    
    print("\n" + "=" * 80)
    
    if all_good:
        print("🎉 ALL SYSTEMS OPERATIONAL")
        print("   Ready to run evolution!")
    else:
        print("⚠️  Some features not yet active")
        print("   Run evolution to activate all systems")
    
    print("=" * 80 + "\n")

if __name__ == '__main__':
    main()
