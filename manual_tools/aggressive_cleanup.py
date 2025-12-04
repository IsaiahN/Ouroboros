"""
AGGRESSIVE CLEANUP: Delete large tables to free space WITHOUT vacuum
"""
import sqlite3
import os

conn = sqlite3.connect('core_data.db')
cursor = conn.cursor()

print("\n" + "=" * 80)
print("AGGRESSIVE DISK SPACE CLEANUP")
print("=" * 80)

# Get current size
db_size_before = os.path.getsize('core_data.db') / (1024**3)
print(f"\nDatabase size: {db_size_before:.2f} GB")
print(f"Problem: VACUUM needs 2x space (~54 GB) but only 10 GB free")
print(f"Solution: Delete bulk data WITHOUT vacuum, let SQLite auto-reclaim")

# Delete system_logs (2.1M rows - massive!)
print("\n1. DELETING SYSTEM_LOGS (2.1M+ rows):")
print("-" * 80)
count_before = cursor.execute("SELECT COUNT(*) FROM system_logs").fetchone()[0]
print(f"Before: {count_before:,} rows")

# Keep only last 10,000 rows
cursor.execute("""
    DELETE FROM system_logs 
    WHERE id NOT IN (
        SELECT id FROM system_logs 
        ORDER BY timestamp DESC 
        LIMIT 10000
    )
""")
print(f"Deleted: {cursor.rowcount:,} rows")
conn.commit()

count_after = cursor.execute("SELECT COUNT(*) FROM system_logs").fetchone()[0]
print(f"After: {count_after:,} rows")

# Delete sensation_learning_events (12M rows!)
print("\n2. DELETING OLD SENSATION_LEARNING_EVENTS (12M+ rows):")
print("-" * 80)
count_before = cursor.execute("SELECT COUNT(*) FROM sensation_learning_events").fetchone()[0]
print(f"Before: {count_before:,} rows")

# Keep only last 100,000 rows
cursor.execute("""
    DELETE FROM sensation_learning_events
    WHERE event_id NOT IN (
        SELECT event_id FROM sensation_learning_events
        ORDER BY event_timestamp DESC
        LIMIT 100000
    )
""")
print(f"Deleted: {cursor.rowcount:,} rows")
conn.commit()

count_after = cursor.execute("SELECT COUNT(*) FROM sensation_learning_events").fetchone()[0]
print(f"After: {count_after:,} rows")

# Delete navigation_state_history (3.2M rows!)
print("\n3. DELETING OLD NAVIGATION_STATE_HISTORY (3.2M+ rows):")
print("-" * 80)
count_before = cursor.execute("SELECT COUNT(*) FROM navigation_state_history").fetchone()[0]
print(f"Before: {count_before:,} rows")

# Keep only last 50,000 rows
cursor.execute("""
    DELETE FROM navigation_state_history
    WHERE history_id NOT IN (
        SELECT history_id FROM navigation_state_history
        ORDER BY state_timestamp DESC
        LIMIT 50000
    )
""")
print(f"Deleted: {cursor.rowcount:,} rows")
conn.commit()

count_after = cursor.execute("SELECT COUNT(*) FROM navigation_state_history").fetchone()[0]
print(f"After: {count_after:,} rows")

# Delete old action traces (keep last 100k)
print("\n4. DELETING OLD ACTION_TRACES:")
print("-" * 80)
count_before = cursor.execute("SELECT COUNT(*) FROM action_traces").fetchone()[0]
print(f"Before: {count_before:,} rows")

# Keep only last 100,000 rows
cursor.execute("""
    DELETE FROM action_traces
    WHERE id NOT IN (
        SELECT id FROM action_traces
        ORDER BY timestamp DESC
        LIMIT 100000
    )
""")
print(f"Deleted: {cursor.rowcount:,} rows")
conn.commit()

count_after = cursor.execute("SELECT COUNT(*) FROM action_traces").fetchone()[0]
print(f"After: {count_after:,} rows")

conn.close()

print("\n" + "=" * 80)
print("CLEANUP COMPLETE")
print("=" * 80)
print("\nNote: Space won't be reclaimed until VACUUM runs")
print("But deleted data is marked as free, allowing new inserts")
print("\nOnce you have ~30+ GB free, run: sqlite3 core_data.db 'VACUUM;'")
