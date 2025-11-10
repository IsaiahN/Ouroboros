#!/usr/bin/env python3
"""
Quick data sufficiency check for analysis readiness.
"""

from database_interface import DatabaseInterface

def check_data_sufficiency():
    """Check if we have enough data for comprehensive analysis."""
    db = DatabaseInterface()
    
    print("DATA SUFFICIENCY ANALYSIS")
    print("=" * 50)
    
    # Games and generations 
    games = db.execute_query("SELECT COUNT(*) as count FROM game_results")[0]["count"]
    generations = db.execute_query("SELECT MAX(generation) as max FROM agents")[0]["max"] or 0
    agents = db.execute_query("SELECT COUNT(*) as count FROM agents")[0]["count"]
    
    print(f"Total Games: {games:,}")
    print(f"Generations: {generations}")  
    print(f"Total Agents: {agents:,}")
    
    # Knowledge base
    sequences = db.execute_query("SELECT COUNT(*) as count FROM winning_sequences")[0]["count"]
    patterns = db.execute_query("SELECT COUNT(*) as count FROM discovered_patterns")[0]["count"]
    dependencies = db.execute_query("SELECT COUNT(*) as count FROM sequence_dependencies")[0]["count"]
    
    print(f"Win Sequences: {sequences}")
    print(f"Patterns: {patterns}")
    print(f"Dependencies: {dependencies:,}")
    
    # Phase data
    prestige_agents = db.execute_query("SELECT COUNT(*) as count FROM agents WHERE discovery_prestige > 0")[0]["count"]
    
    try:
        viral_packages = db.execute_query("SELECT COUNT(*) as count FROM viral_packages")[0]["count"]
    except:
        viral_packages = 0
    
    try:
        pariahs = db.execute_query("SELECT COUNT(*) as count FROM pariah_agents")[0]["count"]
    except:
        pariahs = 0
    
    print(f"Agents with Prestige: {prestige_agents:,}")
    print(f"Viral Packages: {viral_packages}")
    print(f"Pariahs: {pariahs}")
    
    # Evolution events
    try:
        transfer_events = db.execute_query("SELECT COUNT(*) as count FROM horizontal_transfer_events")[0]["count"]
    except:
        transfer_events = 0
    
    try:
        health_snapshots = db.execute_query("SELECT COUNT(*) as count FROM ecosystem_health_snapshots")[0]["count"] 
    except:
        health_snapshots = 0
    
    print(f"Transfer Events: {transfer_events}")
    print(f"Health Snapshots: {health_snapshots}")
    
    # Database size
    import os
    db_size_mb = os.path.getsize("core_data.db") / (1024 * 1024)
    print(f"Database Size: {db_size_mb:.1f} MB")
    
    print("\nSUFFICIENCY ASSESSMENT:")
    print("=" * 50)
    
    # Thresholds for meaningful analysis
    sufficient_games = games >= 1000
    sufficient_generations = generations >= 50
    sufficient_sequences = sequences >= 50
    sufficient_agents = agents >= 10000
    sufficient_data_diversity = (prestige_agents > 100 and dependencies > 1000)
    
    print(f"Games (≥1000): {'✅' if sufficient_games else '❌'} {games:,}")
    print(f"Generations (≥50): {'✅' if sufficient_generations else '❌'} {generations}")
    print(f"Sequences (≥50): {'✅' if sufficient_sequences else '❌'} {sequences}")  
    print(f"Agents (≥10k): {'✅' if sufficient_agents else '❌'} {agents:,}")
    print(f"Data Diversity: {'✅' if sufficient_data_diversity else '❌'} P:{prestige_agents}, D:{dependencies}")
    
    all_sufficient = all([
        sufficient_games, 
        sufficient_generations, 
        sufficient_sequences, 
        sufficient_agents,
        sufficient_data_diversity
    ])
    
    print(f"\nOVERALL: {'✅ SUFFICIENT FOR ANALYSIS' if all_sufficient else '❌ MORE DATA NEEDED'}")
    
    if all_sufficient:
        print("\n🎯 READY FOR:")
        print("  - Network intelligence analysis")
        print("  - Evolution pattern analysis") 
        print("  - Phase system effectiveness analysis")
        print("  - ARC performance optimization")
    else:
        print("\n⚠️ RECOMMENDATIONS:")
        if not sufficient_games:
            print(f"  - Need {1000 - games:,} more games")
        if not sufficient_generations:
            print(f"  - Need {50 - generations} more generations")
        if not sufficient_sequences:
            print(f"  - Need {50 - sequences} more winning sequences")
        if not sufficient_agents:
            print(f"  - Need {10000 - agents:,} more agents")
    
    db.close()
    return all_sufficient

if __name__ == "__main__":
    check_data_sufficiency()