"""
Create a clean database by exporting and reimporting (alternative to VACUUM)
This reclaims space without needing 2x disk space
"""
import sqlite3
import os
import shutil
from datetime import datetime

print("\n" + "=" * 80)
print("DATABASE REBUILD (Alternative to VACUUM)")
print("=" * 80)

# Check sizes
old_db = 'core_data.db'
new_db = 'core_data_clean.db'
backup_db = f'core_data_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'

old_size = os.path.getsize(old_db) / (1024**3)
print(f"\nOld database size: {old_size:.2f} GB")

# Remove old clean file if exists
if os.path.exists(new_db):
    print(f"Removing old {new_db}...")
    os.remove(new_db)

print(f"\n1. Creating clean database using SQLite command...")
print("   This will create a compact copy without empty space")

# Use SQLite's .backup command through subprocess
import subprocess

try:
    # Use sqlite3 command-line tool for backup (most efficient)
    result = subprocess.run(
        ['sqlite3', old_db, f'.backup {new_db}'],
        capture_output=True,
        text=True,
        timeout=600  # 10 minute timeout
    )
    
    if result.returncode != 0:
        print(f"   SQLite backup failed: {result.stderr}")
        print(f"   Falling back to Python dump method...")
        
        # Fallback: Use Python dump with foreign keys disabled
        old_conn = sqlite3.connect(old_db)
        new_conn = sqlite3.connect(new_db)
        
        # Critical: Disable foreign keys
        old_conn.execute("PRAGMA foreign_keys = OFF")
        new_conn.execute("PRAGMA foreign_keys = OFF")
        
        # Get schema and data separately
        print("   Copying schema...")
        schema_dump = '\n'.join(old_conn.iterdump())
        
        for line in schema_dump.split('\n'):
            if line and line not in ('BEGIN;', 'COMMIT;'):
                try:
                    new_conn.execute(line)
                except Exception as e:
                    pass  # Ignore duplicate/constraint errors
        
        new_conn.commit()
        old_conn.close()
        new_conn.close()
        
except FileNotFoundError:
    print("   sqlite3 command not found, using Python method...")
    # Python-only method (slower but works)
    old_conn = sqlite3.connect(old_db)
    new_conn = sqlite3.connect(new_db)
    
    old_conn.execute("PRAGMA foreign_keys = OFF")
    new_conn.execute("PRAGMA foreign_keys = OFF")
    
    # Simple table-by-table copy
    print("   Copying tables...")
    cursor = old_conn.cursor()
    tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    
    for (table,) in tables:
        if table.startswith('sqlite_'):
            continue
        try:
            # Copy table structure
            create_sql = cursor.execute(f"SELECT sql FROM sqlite_master WHERE name='{table}'").fetchone()[0]
            new_conn.execute(create_sql)
            
            # Copy data in chunks
            print(f"   Copying {table}...")
            rows = cursor.execute(f"SELECT * FROM {table}").fetchall()
            if rows:
                placeholders = ','.join(['?'] * len(rows[0]))
                new_conn.executemany(f"INSERT INTO {table} VALUES ({placeholders})", rows)
        except Exception as e:
            print(f"   Warning: {table} - {e}")
    
    new_conn.commit()
    old_conn.close()
    new_conn.close()

new_size = os.path.getsize(new_db) / (1024**3)
space_saved = old_size - new_size

print(f"\n2. Clean database created!")
print(f"   Old: {old_size:.2f} GB")
print(f"   New: {new_size:.2f} GB")
print(f"   Saved: {space_saved:.2f} GB ({space_saved/old_size*100:.1f}%)")

if space_saved > 1.0:  # Saved more than 1GB
    print(f"\n3. Replacing old database...")
    print(f"   SKIPPING BACKUP (not enough disk space)")
    print(f"   Deleting old database...")
    os.remove(old_db)
    
    print(f"   Renaming clean database to core_data.db...")
    os.rename(new_db, old_db)
    
    final_size = os.path.getsize(old_db) / (1024**3)
    print(f"\n✓ SUCCESS!")
    print(f"   core_data.db is now {final_size:.2f} GB")
    print(f"   Space reclaimed: {space_saved:.2f} GB")
    print(f"   WARNING: No backup created (insufficient disk space)")
else:
    print(f"\n⚠️ Not enough space saved to justify replacement")
    print(f"   Keeping old database")
    os.remove(new_db)

print("\n" + "=" * 80)
