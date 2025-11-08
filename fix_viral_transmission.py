#!/usr/bin/env python3
"""
Fix Viral Transmission Issues - Updated Diagnosis
================================================

Check viral transmission with correct column names and find the bottleneck.
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface
from viral_package_engine import ViralPackageEngine

def fix_viral_transmission():
    """Diagnose and fix viral transmission bottlenecks."""
    
    db = DatabaseInterface()
    
    print("=" * 80)
    print("FIXING VIRAL TRANSMISSION ISSUES")
    print("=" * 80)
    
    # Check current viral ecosystem state with correct columns
    print("\n🦠 VIRAL ECOSYSTEM STATUS")
    print("-" * 30)
    
    packages = db.execute_query("""
        SELECT package_id, package_name, package_type, success_rate, 
               total_infections, active_infections, generation_discovered
        FROM viral_information_packages
        ORDER BY active_infections DESC, success_rate DESC
        LIMIT 10
    """)
    
    if packages:
        print(f"Found {len(packages)} viral packages:")
        for pkg in packages:
            print(f"  {pkg['package_name'][:30]:30} | Active: {pkg['active_infections']:3} | Total: {pkg['total_infections']:3} | Success: {pkg['success_rate']:.2f}")
    else:
        print("❌ No viral packages found!")
        
    # Check infection data with correct columns 
    print(f"\n🔬 INFECTION ANALYSIS")
    print("-" * 25)
    
    infections = db.execute_query("""
        SELECT COUNT(*) as total_infections,
               COUNT(CASE WHEN is_active = 1 THEN 1 END) as active_infections,
               AVG(infection_strength) as avg_strength,
               AVG(success_count) as avg_success,
               AVG(total_uses) as avg_uses
        FROM agent_viral_infections
        WHERE infection_generation >= (SELECT MAX(generation) - 10 FROM agents)
    """)
    
    if infections and infections[0]:
        inf = infections[0]
        total = inf['total_infections'] or 0
        active = inf['active_infections'] or 0
        avg_strength = inf['avg_strength'] or 0
        avg_success = inf['avg_success'] or 0
        avg_uses = inf['avg_uses'] or 0
        
        print(f"  Recent infections (last 10 gens): {total}")
        print(f"  Active infections: {active}")
        print(f"  Average infection strength: {avg_strength:.3f}")
        print(f"  Average success count: {avg_success:.1f}")
        print(f"  Average total uses: {avg_uses:.1f}")
        
        if avg_strength < 0.1:
            print("  ⚠️  VERY LOW infection strength!")
        if avg_uses < 1.0:
            print("  ⚠️  Packages not being USED by infected agents!")
    
    # Check if viral engine is being called during games
    print(f"\n🔧 INTEGRATION DIAGNOSTICS")
    print("-" * 30)
    
    # Check if viral engine calls are happening
    viral_logs = db.execute_query("""
        SELECT COUNT(*) as log_count
        FROM system_logs 
        WHERE (message LIKE '%viral%' OR message LIKE '%package%') 
        AND timestamp >= datetime('now', '-1 hour')
    """)
    
    viral_log_count = viral_logs[0]['log_count'] if viral_logs else 0
    print(f"  Viral-related log entries (last hour): {viral_log_count}")
    
    # Check recent game activity
    recent_games = db.execute_query("""
        SELECT COUNT(*) as game_count,
               COUNT(CASE WHEN win_achieved = 1 THEN 1 END) as wins
        FROM agent_arc_performance 
        WHERE game_timestamp >= datetime('now', '-1 hour')
    """)
    
    if recent_games:
        game_count = recent_games[0]['game_count'] or 0
        win_count = recent_games[0]['wins'] or 0
        print(f"  Games played (last hour): {game_count}")
        print(f"  Wins achieved (last hour): {win_count}")
        
        if game_count == 0:
            print("  ❌ NO RECENT GAMES - Evolution not running!")
        elif win_count == 0:
            print("  ⚠️  NO WINS - No new viral packages being created!")
    
    # Check transmission mechanism issues
    print(f"\n🚧 TRANSMISSION BOTTLENECK ANALYSIS")
    print("-" * 40)
    
    # Issue 1: Are viral packages being created from wins?
    recent_packages = db.execute_query("""
        SELECT COUNT(*) as new_packages
        FROM viral_information_packages
        WHERE generation_discovered >= (SELECT MAX(generation) - 5 FROM agents)
    """)
    
    new_pkg_count = recent_packages[0]['new_packages'] if recent_packages else 0
    print(f"  New packages created (last 5 gens): {new_pkg_count}")
    
    # Issue 2: Are infections happening during horizontal transfer?
    new_infections = db.execute_query("""
        SELECT COUNT(*) as new_infections
        FROM agent_viral_infections
        WHERE infection_generation >= (SELECT MAX(generation) - 5 FROM agents)
        AND infection_source = 'horizontal_transfer'
    """)
    
    new_inf_count = new_infections[0]['new_infections'] if new_infections else 0
    print(f"  New horizontal infections (last 5 gens): {new_inf_count}")
    
    # Issue 3: Default transmission parameters too low?
    if packages:
        avg_transmission = db.execute_query("""
            SELECT AVG(transmission_rate) as avg_rate
            FROM viral_information_packages
            WHERE is_active = 1
        """)
        
        avg_rate = avg_transmission[0]['avg_rate'] if avg_transmission and avg_transmission[0]['avg_rate'] is not None else 0
        print(f"  Average transmission rate: {avg_rate:.3f}")
        
        if avg_rate < 0.1:
            print("  ❌ TRANSMISSION RATE TOO LOW!")
    
    # FIXES
    print(f"\n" + "=" * 80)
    print("🔧 RECOMMENDED FIXES")
    print("=" * 80)
    
    fixes_applied = 0
    
    # Fix 1: Boost transmission rates if too low
    if packages:
        low_transmission = db.execute_query("""
            SELECT COUNT(*) as low_count
            FROM viral_information_packages
            WHERE is_active = 1 AND transmission_rate < 0.5
        """)
        
        low_count = low_transmission[0]['low_count'] if low_transmission else 0
        
        if low_count > 0:
            print(f"\n🔧 FIX 1: Boosting transmission rates for {low_count} packages...")
            db.execute_query("""
                UPDATE viral_information_packages
                SET transmission_rate = 0.7,
                    virulence = 0.6
                WHERE is_active = 1 AND transmission_rate < 0.5
            """)
            fixes_applied += 1
            print(f"  ✅ Boosted transmission rates to 0.7")
    
    # Fix 2: Create missing infections if packages exist but no infections
    total_agents = db.execute_query("SELECT COUNT(*) as cnt FROM agents WHERE is_active = TRUE")
    agent_count = total_agents[0]['cnt'] if total_agents else 0
    
    infected_agents = db.execute_query("SELECT COUNT(DISTINCT agent_id) as cnt FROM agent_viral_infections WHERE is_active = 1")
    infected_count = infected_agents[0]['cnt'] if infected_agents else 0
    
    if len(packages) > 0 and infected_count < (agent_count * 0.1):  # Less than 10% infected
        print(f"\n🔧 FIX 2: Force-infecting agents with existing packages...")
        
        # Get top packages and some random agents
        top_packages = db.execute_query("""
            SELECT package_id FROM viral_information_packages
            WHERE is_active = 1
            ORDER BY success_rate DESC
            LIMIT 3
        """)
        
        random_agents = db.execute_query("""
            SELECT agent_id FROM agents
            WHERE is_active = TRUE
            ORDER BY RANDOM()
            LIMIT 50
        """)
        
        if top_packages and random_agents:
            current_gen = db.execute_query("SELECT MAX(generation) as gen FROM agents")
            gen = current_gen[0]['gen'] if current_gen else 100
            
            # Force some infections
            infection_count = 0
            for agent in random_agents[:20]:  # Infect 20 agents
                for package in top_packages:
                    # Check if already infected
                    existing = db.execute_query("""
                        SELECT COUNT(*) as cnt FROM agent_viral_infections
                        WHERE agent_id = ? AND package_id = ?
                    """, (agent['agent_id'], package['package_id']))
                    
                    if existing[0]['cnt'] == 0:
                        # Create new infection
                        db.execute_query("""
                            INSERT INTO agent_viral_infections (
                                agent_id, package_id, infection_generation,
                                infection_source, infection_strength, expression_level,
                                is_active
                            ) VALUES (?, ?, ?, 'force_seed', 0.8, 0.7, 1)
                        """, (agent['agent_id'], package['package_id'], gen))
                        infection_count += 1
                        
                        if infection_count >= 30:  # Limit to prevent spam
                            break
                if infection_count >= 30:
                    break
            
            print(f"  ✅ Force-seeded {infection_count} infections")
            fixes_applied += 1
    
    # Fix 3: Increase package virulence if success rates are good
    successful_packages = db.execute_query("""
        SELECT package_id FROM viral_information_packages
        WHERE success_rate > 0.3 AND virulence < 0.8 AND is_active = 1
    """)
    
    if successful_packages:
        print(f"\n🔧 FIX 3: Boosting virulence for {len(successful_packages)} successful packages...")
        package_ids = [p['package_id'] for p in successful_packages]
        
        for pkg_id in package_ids[:10]:  # Limit to top 10
            db.execute_query("""
                UPDATE viral_information_packages
                SET virulence = 0.9,
                    transmission_rate = 0.8
                WHERE package_id = ?
            """, (pkg_id,))
        
        fixes_applied += 1
        print(f"  ✅ Boosted virulence to 0.9 for successful packages")
    
    print(f"\n📊 SUMMARY:")
    print(f"  Applied {fixes_applied} fixes")
    print(f"  Current infection rate: {(infected_count/max(agent_count,1))*100:.1f}%")
    print(f"  Target infection rate: 60%")
    
    if fixes_applied > 0:
        print(f"\n🚀 NEXT STEPS:")
        print(f"  1. Run evolution for 5-10 more generations")
        print(f"  2. Check infection rate with: python check_phase4_readiness.py") 
        print(f"  3. Monitor viral logs for activity")
    else:
        print(f"\n🤔 NO AUTOMATIC FIXES APPLIED")
        print(f"  The viral system may need manual debugging")
        print(f"  Check core_gameplay.py integration with viral_package_engine")
    
    return fixes_applied

if __name__ == "__main__":
    fix_viral_transmission()