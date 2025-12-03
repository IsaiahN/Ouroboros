#!/usr/bin/env python3
"""
Backfill viral packages from existing winning sequences
One-time script to bootstrap Phase 3 from historical data
"""

from database_interface import DatabaseInterface
from viral_package_engine import ViralPackageEngine
import random

def main():
    db = DatabaseInterface()
    viral_engine = ViralPackageEngine(db)
    
    print("\n" + "=" * 80)
    print("BACKFILL VIRAL PACKAGES FROM EXISTING WINNING SEQUENCES")
    print("=" * 80)
    
    # Get existing winning sequences
    sequences = db.execute_query("""
        SELECT sequence_id, game_id, agent_id, generation_discovered
        FROM winning_sequences
        ORDER BY generation_discovered DESC
        LIMIT 20
    """)
    
    print(f"\nFound {len(sequences)} recent winning sequences to convert")
    
    packages_created = 0
    infections_created = 0
    
    for seq in sequences:
        try:
            # Create viral package from sequence
            package_id = viral_engine.create_viral_package_from_sequence(
                sequence_id=seq['sequence_id'],
                agent_id=seq['agent_id'],
                generation=seq['generation_discovered']
            )
            
            if package_id:
                packages_created += 1
                print(f"  ✓ Created package from sequence {seq['sequence_id'][:8]}...")
                
                # Spread to 3 random agents
                agents = db.execute_query("""
                    SELECT agent_id FROM agents 
                    WHERE is_active = TRUE 
                    AND agent_id != ?
                    ORDER BY RANDOM() 
                    LIMIT 3
                """, (seq['agent_id'],))
                
                for agent in agents:
                    success = viral_engine.spread_viral_package(
                        package_id=package_id,
                        from_agent_id=seq['agent_id'],
                        to_agent_id=agent['agent_id'],
                        generation=seq['generation_discovered']
                    )
                    if success:
                        infections_created += 1
                        
        except Exception as e:
            print(f"  ✗ Error with sequence {seq['sequence_id'][:8]}: {e}")
    
    print(f"\n" + "=" * 80)
    print(f"BACKFILL COMPLETE")
    print(f"=" * 80)
    print(f"[PKG] Viral packages created: {packages_created}")
    print(f"[VIRAL] Infections spread: {infections_created}")
    print("=" * 80 + "\n")
    
    # Show dashboard
    print("\nDisplaying viral ecosystem dashboard...\n")
    from viral_package_engine import display_viral_ecosystem_dashboard
    display_viral_ecosystem_dashboard(db, generation=87)

if __name__ == '__main__':
    main()
