#!/usr/bin/env python3
"""
Simple Data Analysis - What's Next Decision 
==========================================
Based on 1.18GB of evolution data, determine if we have enough for analysis
or need to continue data collection.
"""

from database_interface import DatabaseInterface

def main():
    print("🎯 WHAT'S NEXT - DATA ANALYSIS")
    print("=" * 60)
    
    db = DatabaseInterface()
    
    # Basic data stats
    print("📊 DATA COLLECTED:")
    games = db.execute_query("SELECT COUNT(*) as count FROM game_results")[0]["count"]
    agents = db.execute_query("SELECT COUNT(*) as count FROM agents")[0]["count"] 
    generations = db.execute_query("SELECT MAX(generation) as max FROM agents")[0]["max"] or 0
    sequences = db.execute_query("SELECT COUNT(*) as count FROM winning_sequences")[0]["count"]
    
    print(f"  Games: {games:,}")
    print(f"  Agents: {agents:,}")
    print(f"  Generations: {generations}")
    print(f"  Sequences: {sequences}")
    
    # Performance analysis
    print("\n🎮 ARC PERFORMANCE:")
    
    # Check for any wins
    wins = db.execute_query("SELECT COUNT(*) as count FROM game_results WHERE win_detected = 1")[0]["count"]
    
    # Best performances
    best_scores = db.execute_query("""
        SELECT final_score, level_completions 
        FROM game_results 
        WHERE final_score > 0 OR level_completions > 0
        ORDER BY level_completions DESC, final_score DESC 
        LIMIT 5
    """)
    
    print(f"  Total Wins: {wins}")
    print(f"  Best Performances:")
    for i, game in enumerate(best_scores, 1):
        print(f"    {i}. Score: {game['final_score']}, Levels: {game['level_completions']}")
    
    # System status
    print(f"\n🧬 SYSTEM STATUS:")
    
    # Check if phases are active
    prestige_agents = db.execute_query("SELECT COUNT(*) as count FROM agents WHERE discovery_prestige > 0")[0]["count"]
    dependencies = db.execute_query("SELECT COUNT(*) as count FROM sequence_dependencies")[0]["count"]
    
    try:
        health_snapshots = db.execute_query("SELECT COUNT(*) as count FROM ecosystem_health_snapshots")[0]["count"]
    except:
        health_snapshots = 0
    
    print(f"  Prestige Active: {prestige_agents:,} agents")
    print(f"  Recombination: {dependencies:,} dependencies") 
    print(f"  Network Health: {health_snapshots} snapshots")
    
    # Check evolution status
    try:
        latest_game = db.execute_query("""
            SELECT end_time FROM game_results 
            WHERE end_time IS NOT NULL 
            ORDER BY end_time DESC LIMIT 1
        """)[0]["end_time"]
        print(f"  Last Activity: {latest_game}")
        
        from datetime import datetime
        if latest_game:
            # Parse the timestamp - handle different formats
            try:
                if '.' in latest_game:
                    last_time = datetime.fromisoformat(latest_game.replace('T', ' ').split('.')[0])
                else:
                    last_time = datetime.fromisoformat(latest_game.replace('T', ' '))
                
                hours_since = (datetime.now() - last_time).total_seconds() / 3600
                if hours_since < 1:
                    status = "🟢 ACTIVE"
                elif hours_since < 24:
                    status = f"🟡 IDLE ({hours_since:.1f}h ago)"
                else:
                    status = f"🔴 STOPPED ({hours_since/24:.1f}d ago)"
                print(f"  Status: {status}")
            except:
                print(f"  Status: 🟡 UNKNOWN")
        
    except:
        print(f"  Status: 🔴 NO GAMES")
    
    # Decision matrix
    print(f"\n🎯 DECISION MATRIX:")
    print("=" * 40)
    
    sufficient_data = games >= 1000 and generations >= 50 and agents >= 10000
    has_wins = wins > 0
    system_active = prestige_agents > 100 and dependencies > 1000
    
    print(f"Data Sufficient: {'✅' if sufficient_data else '❌'}")
    print(f"Has ARC Wins: {'✅' if has_wins else '❌'}")
    print(f"System Active: {'✅' if system_active else '❌'}")
    
    # Recommendation
    print(f"\n🚀 WHAT'S NEXT:")
    print("=" * 40)
    
    if sufficient_data and system_active:
        if has_wins:
            print("✅ ANALYSIS PHASE - System has wins, analyze patterns")
            print("   → Run comprehensive analysis on successful strategies")
            print("   → Optimize based on winning patterns")
        else:
            print("⚠️ BREAKTHROUGH PHASE - Good data, no wins yet") 
            print("   → Focus evolution on ARC breakthrough")
            print("   → Use 87 generations of data to optimize for wins")
            print("   → Don't need more data collection, need better strategy")
        
        next_action = "BREAKTHROUGH" if not has_wins else "ANALYSIS"
    else:
        print("🔄 CONTINUE DATA COLLECTION")
        print("   → Need more evolution data before analysis")
        
        next_action = "CONTINUE"
    
    print(f"\n🎯 RECOMMENDATION: {next_action}")
    
    db.close()
    return next_action

if __name__ == "__main__":
    main()