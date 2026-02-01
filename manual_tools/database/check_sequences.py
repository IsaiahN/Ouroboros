"""Check sequence status for ls20 and as66."""
from database_interface import DatabaseInterface

db = DatabaseInterface()

print("=" * 60)
print("SEQUENCE STATUS CHECK")
print("=" * 60)

# First check table schema
print("\n--- winning_sequences schema ---")
schema = db.execute_query("PRAGMA table_info(winning_sequences)")
for col in schema:
    print(f"  {col['name']}: {col['type']}")

# Check ls20 sequences
print("\n--- ls20 Sequences ---")
r1 = db.execute_query("""
    SELECT sequence_id, level_number, is_active, discovered_at, 
           success_rate_when_reused, times_referenced, consecutive_failures,
           flag_reason, LENGTH(action_sequence) as seq_len
    FROM winning_sequences
    WHERE game_type = 'ls20'
    ORDER BY level_number
""")
for row in r1:
    status = "ACTIVE" if row['is_active'] else f"INACTIVE ({row.get('flag_reason', 'unknown')})"
    print(f"  Level {row['level_number']}: seq_len={row['seq_len']}, {status}, "
          f"success_rate={row.get('success_rate_when_reused', 'N/A')}, refs={row.get('times_referenced', 0)}, "
          f"consec_fails={row.get('consecutive_failures', 0)}")

# Check as66 sequences  
print("\n--- as66 Sequences ---")
r2 = db.execute_query("""
    SELECT sequence_id, level_number, is_active, discovered_at,
           success_rate_when_reused, times_referenced, consecutive_failures,
           flag_reason, LENGTH(action_sequence) as seq_len
    FROM winning_sequences
    WHERE game_type = 'as66'
    ORDER BY level_number
""")
for row in r2:
    status = "ACTIVE" if row['is_active'] else f"INACTIVE ({row.get('flag_reason', 'unknown')})"
    print(f"  Level {row['level_number']}: seq_len={row['seq_len']}, {status}, "
          f"success_rate={row.get('success_rate_when_reused', 'N/A')}, refs={row.get('times_referenced', 0)}, "
          f"consec_fails={row.get('consecutive_failures', 0)}")

# Summary of all inactive sequences
print("\n--- All Inactive Sequences (by game_type) ---")
r3 = db.execute_query("""
    SELECT game_type, level_number, COUNT(*) as cnt, 
           GROUP_CONCAT(DISTINCT deactivation_reason) as reasons
    FROM winning_sequences
    WHERE is_active = 0
    GROUP BY game_type, level_number
    ORDER BY game_type, level_number
""")
for row in r3:
    print(f"  {row['game_type']} L{row['level_number']}: {row['cnt']} inactive, reasons: {row['reasons']}")

# Check what's causing deactivations - look at recent deactivations
print("\n--- Recent Deactivations (last 7 days) ---")
r4 = db.execute_query("""
    SELECT game_type, level_number, deactivation_reason, 
           validation_attempts, validation_failures,
           updated_at
    FROM winning_sequences
    WHERE is_active = 0 
    AND updated_at >= datetime('now', '-7 days')
    ORDER BY updated_at DESC
    LIMIT 20
""")
for row in r4:
    print(f"  {row['game_type']} L{row['level_number']}: {row['deactivation_reason']} "
          f"(attempts={row.get('validation_attempts')}, failures={row.get('validation_failures')}, {row.get('updated_at', 'N/A')})")
