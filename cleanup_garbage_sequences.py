"""
Clean up garbage sequences (< 5 actions) from the database.
These are likely from interrupted games, graceful shutdowns, or crashes.
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface

db = DatabaseInterface()

print("\n" + "="*80)
print("CLEANING UP GARBAGE SEQUENCES")
print("="*80)

# Find sequences with < 5 actions
garbage_seqs = db.execute_query("""
    SELECT sequence_id, game_id, level_number, total_actions, total_score
    FROM winning_sequences
    WHERE total_actions < 5
    AND is_active = 1
""")

if garbage_seqs:
    print(f"\n⚠️  Found {len(garbage_seqs)} garbage sequences (< 5 actions):")
    print("-" * 80)
    
    for s in garbage_seqs:
        print(f"  {s['sequence_id'][:16]} | {s['game_id']:25s} | L{s['level_number']} | "
              f"{s['total_actions']} actions | Score {s['total_score']}")
    
    print("\n" + "-" * 80)
    print(f"\nThese are likely from:")
    print("  • Graceful shutdowns during gameplay")
    print("  • VSCode closures/failures")
    print("  • Interrupted game sessions")
    print("\nThey should be removed from the database.")
    
    # Deactivate (soft delete) these sequences
    print("\n" + "="*80)
    print("DEACTIVATING GARBAGE SEQUENCES...")
    print("="*80)
    
    for s in garbage_seqs:
        db.execute_query("""
            UPDATE winning_sequences
            SET is_active = 0
            WHERE sequence_id = ?
        """, (s['sequence_id'],))
    
    print(f"\n✓ Deactivated {len(garbage_seqs)} garbage sequences")
    print("  (Set is_active = 0, can be reactivated if needed)")
    
    # Verify cleanup
    remaining = db.execute_query("""
        SELECT COUNT(*) as count
        FROM winning_sequences
        WHERE total_actions < 5
        AND is_active = 1
    """)
    
    if remaining and remaining[0]['count'] == 0:
        print("✓ Cleanup verified - no garbage sequences remain active")
    else:
        print(f"⚠️  {remaining[0]['count']} garbage sequences still active")
else:
    print("\n✓ No garbage sequences found (database is clean)")

# Show summary of remaining sequences
print("\n" + "="*80)
print("REMAINING ACTIVE SEQUENCES")
print("="*80)

summary = db.execute_query("""
    SELECT 
        COUNT(*) as total,
        MIN(total_actions) as min_actions,
        MAX(total_actions) as max_actions,
        AVG(total_actions) as avg_actions,
        COUNT(DISTINCT game_id) as unique_games
    FROM winning_sequences
    WHERE is_active = 1
""")

if summary:
    s = summary[0]
    print(f"\nTotal active sequences: {s['total']}")
    print(f"Action range: {s['min_actions']} - {s['max_actions']}")
    print(f"Average actions: {s['avg_actions']:.1f}")
    print(f"Unique games: {s['unique_games']}")

print("\n" + "="*80 + "\n")

db.close()
