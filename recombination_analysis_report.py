"""
Analyze Phase 2.5 Recombination Results
Query sequence_dependencies and recombination_attempts to see viral knowledge acceleration.
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface
from datetime import datetime

def analyze_recombination():
    """Analyze recombination attempts and dependency chains."""
    
    db = DatabaseInterface()
    
    print("=" * 80)
    print("PHASE 2.5 RECOMBINATION ANALYSIS")
    print("=" * 80)
    print(f"Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Overall recombination statistics
    print("\n" + "=" * 80)
    print("[1/7] RECOMBINATION ATTEMPTS OVERVIEW")
    print("=" * 80)
    
    attempts_stats = db.execute_query("""
        SELECT 
            COUNT(*) as total_attempts,
            SUM(CASE WHEN was_successful THEN 1 ELSE 0 END) as successful,
            COUNT(DISTINCT agent_id) as unique_agents,
            COUNT(DISTINCT game_id) as unique_games,
            MIN(attempt_timestamp) as first_attempt,
            MAX(attempt_timestamp) as last_attempt
        FROM recombination_attempts
    """)
    
    if attempts_stats and attempts_stats[0]['total_attempts'] > 0:
        stats = attempts_stats[0]
        success_rate = (stats['successful'] / stats['total_attempts']) * 100
        
        print(f"Total Attempts: {stats['total_attempts']}")
        print(f"Successful: {stats['successful']} ({success_rate:.1f}%)")
        print(f"Failed: {stats['total_attempts'] - stats['successful']}")
        print(f"Unique Agents: {stats['unique_agents']}")
        print(f"Unique Games: {stats['unique_games']}")
        print(f"First Attempt: {stats['first_attempt']}")
        print(f"Last Attempt: {stats['last_attempt']}")
    else:
        print("❌ No recombination attempts found!")
        print("   Recombination may not have triggered or sequences don't exist yet.")
    
    # 2. Recombination attempts by generation
    print("\n" + "=" * 80)
    print("[2/7] ATTEMPTS BY GENERATION")
    print("=" * 80)
    
    by_generation = db.execute_query("""
        SELECT 
            generation,
            COUNT(*) as attempts,
            SUM(CASE WHEN was_successful THEN 1 ELSE 0 END) as successful,
            COUNT(DISTINCT agent_id) as agents
        FROM recombination_attempts
        GROUP BY generation
        ORDER BY generation DESC
        LIMIT 10
    """)
    
    if by_generation:
        print(f"{'Gen':<6} {'Attempts':<10} {'Success':<10} {'Agents':<8} {'Rate'}")
        print("-" * 50)
        for row in by_generation:
            rate = (row['successful'] / row['attempts'] * 100) if row['attempts'] > 0 else 0
            print(f"{row['generation']:<6} {row['attempts']:<10} {row['successful']:<10} "
                  f"{row['agents']:<8} {rate:.1f}%")
    else:
        print("No generation data available.")
    
    # 3. Top recombination agents
    print("\n" + "=" * 80)
    print("[3/7] TOP RECOMBINATION AGENTS")
    print("=" * 80)
    
    top_agents = db.execute_query("""
        SELECT 
            agent_id,
            COUNT(*) as total_attempts,
            SUM(CASE WHEN was_successful THEN 1 ELSE 0 END) as successful,
            COUNT(DISTINCT game_id) as games_explored
        FROM recombination_attempts
        GROUP BY agent_id
        ORDER BY successful DESC, total_attempts DESC
        LIMIT 10
    """)
    
    if top_agents:
        print(f"{'Agent':<20} {'Attempts':<10} {'Success':<10} {'Games':<8} {'Rate'}")
        print("-" * 60)
        for row in top_agents:
            rate = (row['successful'] / row['total_attempts'] * 100) if row['total_attempts'] > 0 else 0
            print(f"{row['agent_id'][:16]:<20} {row['total_attempts']:<10} "
                  f"{row['successful']:<10} {row['games_explored']:<8} {rate:.1f}%")
    else:
        print("No agent recombination data.")
    
    # 4. Sequence dependencies (the chains!)
    print("\n" + "=" * 80)
    print("[4/7] SEQUENCE DEPENDENCY CHAINS")
    print("=" * 80)
    
    dependencies = db.execute_query("""
        SELECT 
            COUNT(*) as total_dependencies,
            COUNT(DISTINCT parent_sequence_id) as unique_parents,
            COUNT(DISTINCT child_sequence_id) as unique_children,
            COUNT(DISTINCT discovery_agent_id) as discoverers,
            AVG(combined_efficiency) as avg_efficiency
        FROM sequence_dependencies
    """)
    
    if dependencies and dependencies[0]['total_dependencies'] > 0:
        dep = dependencies[0]
        print(f"Total Dependencies: {dep['total_dependencies']}")
        print(f"Unique Parent Sequences: {dep['unique_parents']}")
        print(f"Unique Child Sequences: {dep['unique_children']}")
        print(f"Agents Creating Chains: {dep['discoverers']}")
        print(f"Average Combined Efficiency: {dep['avg_efficiency']:.4f}")
    else:
        print("❌ No sequence dependencies found!")
        print("   Successful recombinations create dependencies.")
    
    # 5. Most foundational sequences
    print("\n" + "=" * 80)
    print("[5/7] MOST FOUNDATIONAL SEQUENCES")
    print("=" * 80)
    
    foundational = db.execute_query("""
        SELECT 
            sd.parent_sequence_id,
            ws.game_id,
            ws.level_number,
            ws.agent_id,
            COUNT(DISTINCT sd.child_sequence_id) as children_count,
            COUNT(DISTINCT sd.discovery_agent_id) as reused_by_agents,
            ws.efficiency_score as parent_efficiency
        FROM sequence_dependencies sd
        JOIN winning_sequences ws ON sd.parent_sequence_id = ws.sequence_id
        GROUP BY sd.parent_sequence_id
        ORDER BY children_count DESC, reused_by_agents DESC
        LIMIT 10
    """)
    
    if foundational:
        print(f"{'Sequence':<18} {'Game':<18} {'Lvl':<5} {'Children':<10} {'Agents':<8} {'Efficiency'}")
        print("-" * 80)
        for row in foundational:
            print(f"{row['parent_sequence_id'][:16]:<18} {row['game_id'][:16]:<18} "
                  f"{row['level_number']:<5} {row['children_count']:<10} "
                  f"{row['reused_by_agents']:<8} {row['parent_efficiency']:.4f}")
    else:
        print("No foundational sequences yet (need successful chains first).")
    
    # 6. Recent successful chains
    print("\n" + "=" * 80)
    print("[6/7] RECENT SUCCESSFUL CHAINS")
    print("=" * 80)
    
    recent_chains = db.execute_query("""
        SELECT 
            sd.child_sequence_id,
            sd.parent_sequence_id,
            sd.discovery_agent_id,
            sd.combined_efficiency,
            sd.improvement_over_parent,
            sd.discovery_timestamp,
            ws.game_id
        FROM sequence_dependencies sd
        JOIN winning_sequences ws ON sd.child_sequence_id = ws.sequence_id
        ORDER BY sd.discovery_timestamp DESC
        LIMIT 10
    """)
    
    if recent_chains:
        print(f"{'Chain ID':<18} {'Parent':<18} {'Game':<18} {'Efficiency':<12} {'Created'}")
        print("-" * 80)
        for row in recent_chains:
            print(f"{row['child_sequence_id'][:16]:<18} {row['parent_sequence_id'][:16]:<18} "
                  f"{row['game_id'][:16]:<18} {row['combined_efficiency']:<12.4f} "
                  f"{row['discovery_timestamp'][:19]}")
    else:
        print("No successful chains created yet.")
    
    # 7. Agent recombination stats from agents table
    print("\n" + "=" * 80)
    print("[7/7] AGENT RECOMBINATION STATS (from agents table)")
    print("=" * 80)
    
    agent_stats = db.execute_query("""
        SELECT 
            agent_id,
            recombination_discoveries,
            successful_recombinations,
            recombination_success_rate
        FROM agents
        WHERE recombination_discoveries > 0
        ORDER BY successful_recombinations DESC
        LIMIT 10
    """)
    
    if agent_stats:
        print(f"{'Agent':<20} {'Discoveries':<14} {'Successful':<14} {'Rate'}")
        print("-" * 65)
        for row in agent_stats:
            rate_display = f"{row['recombination_success_rate']:.1%}" if row['recombination_success_rate'] else "0.0%"
            print(f"{row['agent_id'][:16]:<20} {row['recombination_discoveries']:<14} "
                  f"{row['successful_recombinations']:<14} {rate_display}")
    else:
        print("No agents have recombination stats yet.")
    
    # Summary and recommendations
    print("\n" + "=" * 80)
    print("SUMMARY & NEXT STEPS")
    print("=" * 80)
    
    if attempts_stats and attempts_stats[0]['total_attempts'] > 0:
        total = attempts_stats[0]['total_attempts']
        successful = attempts_stats[0]['successful']
        success_rate = (successful / total) * 100
        
        print(f"\n✅ Recombination system is ACTIVE!")
        print(f"   - {total} attempts made")
        print(f"   - {successful} successful ({success_rate:.1f}% success rate)")
        
        if dependencies and dependencies[0]['total_dependencies'] > 0:
            dep_count = dependencies[0]['total_dependencies']
            print(f"   - {dep_count} dependency chains created")
            print(f"\n🧬 VIRAL KNOWLEDGE ACCELERATION is working!")
            print(f"\n   Phase 2.5 is COMPLETE and FUNCTIONAL!")
        else:
            print(f"\n⚠️  Attempts made but NO CHAINS stored yet.")
            print(f"   This is normal if success rate is very low.")
        
        if success_rate < 5:
            print(f"\n💡 Low success rate ({success_rate:.1f}%) is EXPECTED:")
            print(f"   - Most random combinations don't work")
            print(f"   - Successful ones will spread virally")
            print(f"   - Network learns which combinations are valuable")
        elif success_rate > 20:
            print(f"\n🎯 High success rate ({success_rate:.1f}%)!")
            print(f"   - Agents finding good combination patterns")
            print(f"   - Exponential knowledge growth happening")
        
    else:
        print("\n⚠️  No recombination attempts yet.")
        print("\nPossible reasons:")
        print("1. Games didn't complete (check game_results table)")
        print("2. Not enough sequences exist (<2 per game/level)")
        print("3. Agents don't have agent_id during gameplay")
        
        # Check if sequences exist
        seq_count = db.execute_query("""
            SELECT COUNT(*) as count FROM winning_sequences
        """)
        if seq_count and seq_count[0]['count'] > 0:
            print(f"\n   {seq_count[0]['count']} sequences exist - should be enough")
        else:
            print(f"\n   ❌ No sequences exist - need to play games first")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    analyze_recombination()
