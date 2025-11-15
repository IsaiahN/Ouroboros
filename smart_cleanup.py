"""
PROPER cleanup - only deactivate sequences that FAILED validation.
Short sequences that were never tried should stay active (might work!).
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface

db = DatabaseInterface()

print("\n" + "="*80)
print("SMART SEQUENCE CLEANUP - Only Deactivate Proven Failures")
print("="*80)

# First, REACTIVATE all sequences we just deactivated
print("\nStep 1: Reactivating all sequences...")
print("-" * 80)

reactivate = db.execute_query("""
    UPDATE winning_sequences
    SET is_active = 1
    WHERE is_active = 0
""")

print("✓ All sequences reactivated")

# Now find sequences that ACTUALLY failed validation
failed_seqs = db.execute_query("""
    SELECT 
        ws.sequence_id,
        ws.game_id,
        ws.level_number,
        ws.total_actions,
        ws.total_score,
        sr.total_validation_attempts,
        sr.successful_validations,
        sr.failed_validations,
        sr.reliability_score
    FROM winning_sequences ws
    JOIN sequence_reputation sr ON ws.sequence_id = sr.sequence_id
    WHERE sr.total_validation_attempts > 0
      AND sr.successful_validations = 0
      AND sr.failed_validations > 0
      AND ws.is_active = 1
""")

if failed_seqs:
    print(f"\nStep 2: Found {len(failed_seqs)} sequences that FAILED validation:")
    print("-" * 80)
    
    for s in failed_seqs:
        print(f"  {s['sequence_id'][:16]} | {s['game_id']:25s} | L{s['level_number']} | "
              f"{s['total_actions']:5d} actions | "
              f"Attempts: {s['total_validation_attempts']} | "
              f"Success: {s['successful_validations']} | Failed: {s['failed_validations']} | "
              f"Reliability: {s['reliability_score']:.3f}")
    
    print("\n" + "-" * 80)
    print("These sequences were tried by agents and FAILED every time.")
    print("Deactivating proven-failed sequences...")
    
    for s in failed_seqs:
        db.execute_query("""
            UPDATE winning_sequences
            SET is_active = 0
            WHERE sequence_id = ?
        """, (s['sequence_id'],))
    
    print(f"✓ Deactivated {len(failed_seqs)} proven-failed sequences")
else:
    print("\nStep 2: No proven-failed sequences found")

# Check untested short sequences (these stay ACTIVE)
print("\n" + "="*80)
print("UNTESTED SHORT SEQUENCES (< 5 actions) - Staying ACTIVE:")
print("-" * 80)

short_untested = db.execute_query("""
    SELECT 
        ws.sequence_id,
        ws.game_id,
        ws.level_number,
        ws.total_actions,
        COALESCE(sr.total_validation_attempts, 0) as attempts
    FROM winning_sequences ws
    LEFT JOIN sequence_reputation sr ON ws.sequence_id = sr.sequence_id
    WHERE ws.total_actions < 5
      AND ws.is_active = 1
      AND COALESCE(sr.total_validation_attempts, 0) = 0
""")

if short_untested:
    print(f"Found {len(short_untested)} untested short sequences (keeping ACTIVE):")
    for s in short_untested:
        print(f"  {s['game_id']:25s} | L{s['level_number']} | {s['total_actions']} actions | "
              f"Never validated - might work!")
else:
    print("No untested short sequences")

# Final summary
print("\n" + "="*80)
print("FINAL SUMMARY:")
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

# Show breakdown by validation status
print("\nBreakdown by validation status:")
validated = db.execute_query("""
    SELECT 
        CASE 
            WHEN COALESCE(sr.successful_validations, 0) > 0 THEN 'PROVEN'
            WHEN COALESCE(sr.total_validation_attempts, 0) = 0 THEN 'UNTESTED'
            ELSE 'FAILED'
        END as status,
        COUNT(*) as count
    FROM winning_sequences ws
    LEFT JOIN sequence_reputation sr ON ws.sequence_id = sr.sequence_id
    WHERE ws.is_active = 1
    GROUP BY status
""")

if validated:
    for v in validated:
        print(f"  {v['status']:10s}: {v['count']:3d} sequences")

print("\n" + "="*80)
print("\nPHILOSOPHY:")
print("✓ PROVEN sequences (successful_validations > 0) - Keep active")
print("✓ UNTESTED sequences (never tried) - Keep active (might work!)")
print("✗ FAILED sequences (tried but all failed) - Deactivate (proven broken)")
print("\n" + "="*80 + "\n")

db.close()
