"""Cleanup current population explosion - deactivate unevaluated agents"""
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface

db = DatabaseInterface()

print("\n" + "="*70)
print("POPULATION CLEANUP - Deactivating Unevaluated Agents")
print("="*70)

# Check current state
before = db.execute_query("""
    SELECT 
        SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active,
        SUM(CASE WHEN is_active = 0 THEN 1 ELSE 0 END) as inactive
    FROM agents
""")

print(f"\n[BEFORE CLEANUP]")
print(f"  Active agents: {before[0]['active']}")
print(f"  Inactive agents: {before[0]['inactive']}")

# Strategy: Keep only Gen 0-4 agents (they have some evaluation)
# Deactivate Gen 5-11 (unevaluated)
print(f"\n[CLEANUP STRATEGY]")
print("  • Keep Gen 0-4 agents (have game data)")
print("  • Deactivate Gen 5-11 agents (never evaluated)")
print("  • This will reduce population from 11,387 to ~364 agents")

response = input("\nProceed with cleanup? (yes/no): ").strip().lower()

if response == 'yes':
    # Deactivate Gen 5-11
    with db._get_connection() as conn:
        cursor = conn.execute("""
            UPDATE agents
            SET is_active = 0
            WHERE generation >= 5
        """)
        rows_affected = cursor.rowcount
        conn.commit()
    
    print(f"\n[CLEANUP COMPLETE]")
    print(f"  Deactivated {rows_affected} agents")
    
    # Check after state
    after = db.execute_query("""
        SELECT 
            SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active,
            SUM(CASE WHEN is_active = 0 THEN 1 ELSE 0 END) as inactive
        FROM agents
    """)
    
    print(f"\n[AFTER CLEANUP]")
    print(f"  Active agents: {after[0]['active']}")
    print(f"  Inactive agents: {after[0]['inactive']}")
    
    # Show generation breakdown
    gen_counts = db.execute_query("""
        SELECT 
            generation,
            SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active,
            AVG(total_games_played) as avg_games
        FROM agents
        WHERE is_active = 1
        GROUP BY generation
        ORDER BY generation
    """)
    
    print(f"\n[ACTIVE GENERATIONS]")
    for g in gen_counts:
        print(f"  Gen {g['generation']}: {g['active']} agents, {g['avg_games']:.1f} avg games")
    
    print(f"\n[NEXT STEPS]")
    print("  1. Population size now controlled (364 active agents)")
    print("  2. Next evolution cycle will properly cull to 50-200 agents")
    print("  3. Fixes applied to evolutionary_engine.py will prevent re-explosion")
    print("  4. Run evolution with: python run_evolution.py --specialist")
    
else:
    print("\n[CANCELLED] No changes made")

print("\n" + "="*70 + "\n")
