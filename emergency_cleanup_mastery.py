"""
EMERGENCY: Delete failed mastery sessions and free up disk space
ONLY deletes sessions with ZERO level completions (no progress at all)
"""
import sqlite3
import os
from datetime import datetime, timedelta

conn = sqlite3.connect('core_data.db')
cursor = conn.cursor()

print("\n" + "=" * 80)
print("EMERGENCY CLEANUP - MASTERY MODE FAILURES")
print("=" * 80)

# 1. Find mastery sessions with ZERO level completions
print("\n1. IDENTIFYING FAILED MASTERY SESSIONS (ZERO LEVELS COMPLETED):")
print("-" * 80)

recent_time = (datetime.now() - timedelta(days=7)).isoformat()

# Get sessions for as66 where agent completed ZERO levels (no progress)
# Check game_results for sessions with level_completions = 0 or NULL
failed_sessions = cursor.execute("""
    SELECT DISTINCT gr.session_id, gr.final_score, gr.level_completions, gr.total_actions
    FROM game_results gr
    WHERE gr.game_id = 'as66-821a4dcad9c2'
    AND (gr.level_completions = 0 OR gr.level_completions IS NULL)
    AND gr.final_score = 0
    ORDER BY gr.session_id DESC
""").fetchall()

print(f"Found {len(failed_sessions)} failed mastery sessions (ZERO level completions)")

if len(failed_sessions) > 0:
    # Show sample of what will be deleted
    print("\nSample sessions to delete:")
    for sess in failed_sessions[:10]:
        print(f"  Session: {sess[0][:16]}..., Score: {sess[1]}, Levels: {sess[2]}, Actions: {sess[3]}")
    
    if len(failed_sessions) > 10:
        print(f"  ... and {len(failed_sessions) - 10} more")
    
    session_ids = [s[0] for s in failed_sessions]
    
    # Count data to delete
    print("\n2. DATA TO DELETE:")
    print("-" * 80)
    
    # Action traces
    placeholders = ','.join('?' * len(session_ids))
    action_count = cursor.execute(f"""
        SELECT COUNT(*) FROM action_traces 
        WHERE session_id IN ({placeholders})
        AND game_id = 'as66-821a4dcad9c2'
    """, session_ids).fetchone()[0]
    # Start deletion
    print("\n3. DELETING FAILED MASTERY DATA:")
    print("-" * 80)
    
    # Delete system logs (massive space saver)
    print("Deleting system logs...")
    cursor.execute(f"""
        DELETE FROM system_logs 
        WHERE session_id IN ({placeholders})
    """, session_ids)
    print(f"  ✓ Deleted {cursor.rowcount:,} system logs")
    
    # Delete action traces
    print("Deleting action traces...")
    cursor.execute(f"""
        DELETE FROM action_traces 
        WHERE session_id IN ({placeholders})
        AND game_id = 'as66-821a4dcad9c2'
    """, session_ids)
    print(f"  ✓ Deleted {cursor.rowcount:,} action traces")
    
    # Delete game results
    print("Deleting game results...")
    cursor.execute(f"""
        DELETE FROM game_results 
        WHERE session_id IN ({placeholders})
        AND game_id = 'as66-821a4dcad9c2'
    """, session_ids)
    print(f"  ✓ Deleted {cursor.rowcount:,} game results")
    
    # Note: navigation_state_history and sensation_learning_events don't have session_id
    # They're tied to agents, not sessions, so skip them
    
    conn.commit()
    print("\n✓ Deletion complete")
    print("Deleting action traces...")
    cursor.execute(f"""
        DELETE FROM action_traces 
        WHERE session_id IN ({placeholders})
    """, session_ids)
    print(f"  ✓ Deleted {cursor.rowcount:,} action traces")
    
    # Delete game results
    print("Deleting game results...")
    cursor.execute(f"""
        DELETE FROM game_results 
        WHERE session_id IN ({placeholders})
    """, session_ids)
    print(f"  ✓ Deleted {cursor.rowcount:,} game results")
    
    conn.commit()
    print("\n✓ Deletion complete")
    
    # Vacuum database to reclaim space
    print("\n4. VACUUMING DATABASE:")
    print("-" * 80)
    print("This will reclaim disk space (may take several minutes)...")
    
    # Get size before
    db_size_before = os.path.getsize('core_data.db') / (1024**3)
    print(f"Database size before: {db_size_before:.2f} GB")
    
    cursor.execute("VACUUM")
    conn.commit()
    
    # Get size after
    db_size_after = os.path.getsize('core_data.db') / (1024**3)
    print(f"Database size after: {db_size_after:.2f} GB")
    print(f"Space reclaimed: {db_size_before - db_size_after:.2f} GB")

else:
    print("No failed sessions found (unexpected)")

conn.close()

print("\n" + "=" * 80)
print("CLEANUP COMPLETE")
print("=" * 80)
