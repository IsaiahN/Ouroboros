"""
Network Health Monitor for Phase 0 Observation Period
Monitors network intelligence snapshots during evolution.
"""

import os
import time
from datetime import datetime
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface
from network_intelligence_engine import display_network_intelligence_dashboard


def monitor_network_health(check_interval_seconds=60, duration_minutes=30):
    """
    Monitor network health snapshots during evolution.
    
    Args:
        check_interval_seconds: How often to check for new snapshots
        duration_minutes: How long to monitor
    """
    db = DatabaseInterface()
    start_time = datetime.now()
    from datetime import timedelta
    end_time = start_time + timedelta(minutes=duration_minutes)
    
    last_generation_seen = None
    snapshot_count = 0
    
    print("\n" + "="*80)
    print("NETWORK HEALTH MONITORING - PHASE 0 OBSERVATION PERIOD")
    print("="*80)
    print(f"Start Time: {start_time}")
    print(f"Duration: {duration_minutes} minutes")
    print(f"Check Interval: {check_interval_seconds} seconds")
    print(f"Monitoring for network snapshots...")
    print("="*80 + "\n")
    
    try:
        while datetime.now() < end_time:
            # Check for latest snapshot
            snapshots = db.execute_query("""
                SELECT generation, health_status, health_score, 
                       total_sequences, active_agents, knowledge_diversity_index,
                       snapshot_timestamp
                FROM ecosystem_health_snapshots
                ORDER BY generation DESC
                LIMIT 1
            """)
            
            if snapshots:
                current_gen = snapshots[0]['generation']
                
                # New snapshot detected
                if last_generation_seen is None or current_gen > last_generation_seen:
                    snapshot_count += 1
                    print(f"\n{'='*80}")
                    print(f"NEW SNAPSHOT DETECTED - Generation {current_gen}")
                    print(f"{'='*80}")
                    print(f"Time: {snapshots[0]['snapshot_timestamp']}")
                    print(f"Health: {snapshots[0]['health_status']} (score: {snapshots[0]['health_score']:.3f})")
                    print(f"Knowledge: {snapshots[0]['total_sequences']} sequences, diversity: {snapshots[0]['knowledge_diversity_index']:.3f}")
                    print(f"Population: {snapshots[0]['active_agents']} agents")
                    
                    # Show full dashboard
                    print("\n" + "-"*80)
                    display_network_intelligence_dashboard(current_gen)
                    print("-"*80)
                    
                    last_generation_seen = current_gen
                    
                    # Check if we have 5 generations
                    if snapshot_count >= 5:
                        print("\n" + "="*80)
                        print("OBSERVATION PERIOD COMPLETE - 5 GENERATIONS OBSERVED")
                        print("="*80)
                        show_health_trends(db)
                        return True
            
            # Wait before next check
            time.sleep(check_interval_seconds)
            
            # Show progress indicator
            elapsed = (datetime.now() - start_time).total_seconds()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Monitoring... (elapsed: {elapsed/60:.1f} min, snapshots: {snapshot_count})")
    
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Monitoring stopped by user")
    
    print("\n" + "="*80)
    print("MONITORING SUMMARY")
    print("="*80)
    print(f"Total Snapshots Captured: {snapshot_count}")
    print(f"Last Generation Seen: {last_generation_seen if last_generation_seen else 'None'}")
    
    if snapshot_count > 0:
        show_health_trends(db)
    
    return snapshot_count >= 5


def show_health_trends(db: DatabaseInterface):
    """Show health trends over all captured snapshots."""
    
    print("\n" + "="*80)
    print("NETWORK HEALTH TRENDS ANALYSIS")
    print("="*80)
    
    snapshots = db.execute_query("""
        SELECT generation, health_status, health_score,
               total_sequences, total_patterns, total_learned_rules,
               knowledge_diversity_index, active_agents,
               validation_rate, innovation_vs_exploitation,
               network_growth_rate, snapshot_timestamp
        FROM ecosystem_health_snapshots
        ORDER BY generation ASC
    """)
    
    if not snapshots:
        print("No snapshots available for trend analysis.")
        return
    
    print(f"\nTotal Snapshots: {len(snapshots)}")
    print(f"Generation Range: {snapshots[0]['generation']} - {snapshots[-1]['generation']}")
    print()
    
    # Health score trend
    print("HEALTH SCORE TREND:")
    for s in snapshots:
        bar_length = int(s['health_score'] * 50)
        bar = "█" * bar_length + "░" * (50 - bar_length)
        print(f"  Gen {s['generation']:2d}: {bar} {s['health_score']:.3f} - {s['health_status']}")
    
    # Calculate trends
    if len(snapshots) >= 2:
        first = snapshots[0]
        last = snapshots[-1]
        
        health_change = last['health_score'] - first['health_score']
        knowledge_change = (last['total_sequences'] + last['total_patterns'] + last['total_learned_rules']) - \
                          (first['total_sequences'] + first['total_patterns'] + first['total_learned_rules'])
        diversity_change = last['knowledge_diversity_index'] - first['knowledge_diversity_index']
        agent_change = last['active_agents'] - first['active_agents']
        
        print("\n" + "-"*80)
        print("TREND SUMMARY:")
        print(f"  Health Score: {first['health_score']:.3f} → {last['health_score']:.3f} ({'+' if health_change > 0 else ''}{health_change:.3f})")
        print(f"  Total Knowledge: {first['total_sequences'] + first['total_patterns'] + first['total_learned_rules']} → {last['total_sequences'] + last['total_patterns'] + last['total_learned_rules']} ({'+' if knowledge_change > 0 else ''}{knowledge_change})")
        print(f"  Diversity Index: {first['knowledge_diversity_index']:.3f} → {last['knowledge_diversity_index']:.3f} ({'+' if diversity_change > 0 else ''}{diversity_change:.3f})")
        print(f"  Active Agents: {first['active_agents']} → {last['active_agents']} ({'+' if agent_change > 0 else ''}{agent_change})")
        
        print("\n" + "-"*80)
        print("KEY OBSERVATIONS:")
        
        if health_change > 0.05:
            print("  ✓ Network health is IMPROVING - ecosystem becoming healthier")
        elif health_change < -0.05:
            print("  ⚠ Network health is DECLINING - may need intervention")
        else:
            print("  → Network health is STABLE")
        
        if diversity_change > 0.5:
            print("  ✓ Knowledge diversity is INCREASING - good for resilience")
        elif diversity_change < -0.5:
            print("  ⚠ Knowledge diversity is DECREASING - risk of overfitting")
        else:
            print("  → Knowledge diversity is STABLE")
        
        if knowledge_change > 10:
            print("  ✓ Knowledge base is GROWING rapidly")
        elif knowledge_change > 0:
            print("  → Knowledge base is growing slowly")
        else:
            print("  ⚠ Knowledge base is STAGNANT - no new learning")
        
        avg_validation = sum(s['validation_rate'] for s in snapshots) / len(snapshots)
        if avg_validation > 0.5:
            print(f"  ✓ High validation success rate ({avg_validation:.1%}) - knowledge is reliable")
        elif avg_validation > 0.2:
            print(f"  → Moderate validation rate ({avg_validation:.1%}) - some knowledge is useful")
        else:
            print(f"  ⚠ Low validation rate ({avg_validation:.1%}) - knowledge may not be reusable")
    
    print("="*80)
    
    # Phase 0 completion check
    if len(snapshots) >= 5:
        print("\n✓ PHASE 0 OBSERVATION PERIOD COMPLETE")
        print("  - 5+ generations observed with network health tracking")
        print("  - Network-centric metrics captured successfully")
        print("  - Paradigm shift to 'How is the NETWORK doing?' achieved")
        print("\n  Ready to proceed to Phase 1 (Prestige System) if desired.")
        print("  However, consider observing longer for better baseline data.")
    else:
        print(f"\n⏳ PHASE 0 OBSERVATION IN PROGRESS")
        print(f"  - {len(snapshots)}/5 generations observed")
        print(f"  - Continue running evolution until 5 snapshots captured")
    
    print("="*80)


if __name__ == "__main__":
    import sys
    
    # Parse arguments
    check_interval = 60  # Check every minute
    duration = 120       # Monitor for 2 hours
    
    if len(sys.argv) > 1:
        check_interval = int(sys.argv[1])
    if len(sys.argv) > 2:
        duration = int(sys.argv[2])
    
    print("\n[MONITOR] Starting network health monitoring...")
    print(f"  Check Interval: {check_interval} seconds")
    print(f"  Duration: {duration} minutes")
    
    success = monitor_network_health(check_interval, duration)
    
    if success:
        print("\n[SUCCESS] Observation period complete!")
        sys.exit(0)
    else:
        print("\n[INCOMPLETE] Observation period not yet complete")
        sys.exit(1)
