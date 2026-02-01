"""Reactivate best sequences and investigate deactivation sources."""
from database_interface import DatabaseInterface

db = DatabaseInterface()

print("=" * 60)
print("REACTIVATING BEST SEQUENCES")
print("=" * 60)

# as66 Level 4 - find best candidate to reactivate
print("\n--- as66 Level 4 Candidates ---")
r1 = db.execute_query("""
    SELECT sequence_id, is_active, success_rate_when_reused, times_referenced,
           consecutive_failures, flag_reason, total_actions
    FROM winning_sequences
    WHERE game_type = 'as66' AND level_number = 4
    ORDER BY success_rate_when_reused DESC, times_referenced DESC
    LIMIT 5
""")
best_seq_id = None
for row in r1:
    print(f"  {row['sequence_id'][:30]}... active={row['is_active']}, "
          f"success_rate={row['success_rate_when_reused']}, refs={row['times_referenced']}, "
          f"actions={row['total_actions']}, reason={row['flag_reason']}")
    if row['success_rate_when_reused'] and row['success_rate_when_reused'] > 0.5:
        if not best_seq_id:
            best_seq_id = row['sequence_id']

# Reactivate best as66 L4 sequence
if best_seq_id:
    print(f"\n>>> Reactivating: {best_seq_id[:40]}...")
    db.execute_query("""
        UPDATE winning_sequences
        SET is_active = 1, flag_reason = 'manually_reactivated'
        WHERE sequence_id = ?
    """, (best_seq_id,))
    print("    Done!")
else:
    # Find the one with most references
    r1b = db.execute_query("""
        SELECT sequence_id, success_rate_when_reused, times_referenced
        FROM winning_sequences
        WHERE game_type = 'as66' AND level_number = 4
        ORDER BY times_referenced DESC
        LIMIT 1
    """)
    if r1b:
        best_seq_id = r1b[0]['sequence_id']
        print(f"\n>>> Reactivating highest-referenced: {best_seq_id[:40]}...")
        db.execute_query("""
            UPDATE winning_sequences
            SET is_active = 1, flag_reason = 'manually_reactivated'
            WHERE sequence_id = ?
        """, (best_seq_id,))
        print("    Done!")

# ls20 - find best L1 sequence to reactivate (since all are inactive)
print("\n--- ls20 Level 1 Candidates ---")
r2 = db.execute_query("""
    SELECT sequence_id, is_active, success_rate_when_reused, times_referenced,
           consecutive_failures, flag_reason, total_actions
    FROM winning_sequences
    WHERE game_type = 'ls20' AND level_number = 1
    ORDER BY success_rate_when_reused DESC, times_referenced DESC
    LIMIT 5
""")
best_ls20_seq = None
for row in r2:
    print(f"  {row['sequence_id'][:30]}... active={row['is_active']}, "
          f"success_rate={row['success_rate_when_reused']}, refs={row['times_referenced']}, "
          f"actions={row['total_actions']}, reason={row['flag_reason']}")
    if row['success_rate_when_reused'] and row['success_rate_when_reused'] > 0:
        if not best_ls20_seq:
            best_ls20_seq = row['sequence_id']

if best_ls20_seq:
    print(f"\n>>> Reactivating: {best_ls20_seq[:40]}...")
    db.execute_query("""
        UPDATE winning_sequences
        SET is_active = 1, flag_reason = 'manually_reactivated'
        WHERE sequence_id = ?
    """, (best_ls20_seq,))
    print("    Done!")

# Verify
print("\n--- Verification ---")
r3 = db.execute_query("""
    SELECT game_type, level_number, COUNT(*) as active_count
    FROM winning_sequences
    WHERE is_active = 1 AND game_type IN ('ls20', 'as66')
    GROUP BY game_type, level_number
    ORDER BY game_type, level_number
""")
for row in r3:
    print(f"  {row['game_type']} L{row['level_number']}: {row['active_count']} active")
