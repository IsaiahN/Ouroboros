"""
Compact the database using VACUUM INTO (requires only 1x space, not 2x like regular VACUUM).
This creates a new compacted file, then swaps it with the original.
"""
import os
import shutil
import sqlite3
import time

DB_PATH = 'core_data.db'
COMPACT_PATH = 'core_data_compacted.db'
BACKUP_PATH = 'core_data_old.db'

def compact_database(force=False):
    # Check current sizes
    old_size = os.path.getsize(DB_PATH) / 1024 / 1024
    print(f"Current database size: {old_size:.1f} MB")

    # Check free pages and auto_vacuum status
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('PRAGMA freelist_count')
    free_pages = cursor.fetchone()[0]
    cursor.execute('PRAGMA page_size')
    page_size = cursor.fetchone()[0]
    cursor.execute('PRAGMA auto_vacuum')
    auto_vacuum = cursor.fetchone()[0]
    reclaimable = free_pages * page_size / 1024 / 1024
    print(f"Reclaimable space: {reclaimable:.1f} MB")
    print(f"auto_vacuum: {auto_vacuum} (0=NONE, 1=FULL, 2=INCREMENTAL)")

    # Force if auto_vacuum not enabled
    if auto_vacuum == 0 and not force:
        print("auto_vacuum not enabled - forcing rebuild to enable it")
        force = True

    if reclaimable < 10 and not force:
        print("Less than 10 MB reclaimable - skipping compaction")
        conn.close()
        return

    # Remove old compacted file if exists
    if os.path.exists(COMPACT_PATH):
        os.remove(COMPACT_PATH)

    print(f"\nCreating compacted copy...")
    start = time.time()

    # VACUUM INTO creates a new compacted database
    cursor.execute(f"VACUUM INTO '{COMPACT_PATH}'")
    conn.close()

    elapsed = time.time() - start
    new_size = os.path.getsize(COMPACT_PATH) / 1024 / 1024
    saved = old_size - new_size

    print(f"Compaction completed in {elapsed:.1f}s")
    print(f"New size: {new_size:.1f} MB")
    print(f"Saved: {saved:.1f} MB ({saved/old_size*100:.1f}%)")

    # Swap files FIRST to free up space for vacuum
    print(f"\nSwapping files...")

    # Remove old backup if exists
    if os.path.exists(BACKUP_PATH):
        os.remove(BACKUP_PATH)

    # Rename original to backup (we'll delete it to free space)
    os.rename(DB_PATH, BACKUP_PATH)

    # Rename compacted to original
    os.rename(COMPACT_PATH, DB_PATH)

    # Delete old backup to free space for vacuum
    print(f"Deleting old database to free space...")
    os.remove(BACKUP_PATH)

    # Now enable auto_vacuum on the new database with space available
    print("Enabling auto_vacuum=INCREMENTAL...")
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA auto_vacuum = INCREMENTAL')
    # Since this is a fresh copy with no free pages, vacuum should be quick
    conn.execute('VACUUM')
    conn.close()

    print(f"Done!")

    # Verify new database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM game_results")
    count = cursor.fetchone()[0]
    print(f"\nVerification: game_results has {count:,} rows")
    conn.close()

if __name__ == '__main__':
    compact_database()
